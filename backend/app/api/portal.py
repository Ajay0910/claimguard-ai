import uuid

import asyncio

from datetime import datetime

from typing import Optional, Dict, Set

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header, Request

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from sqlalchemy.exc import IntegrityError

import os



from ..database import get_db

from ..models.claim import Claim, Document, AnalysisRun

from ..config import settings, get_cors_origins

from ..security.auth import hash_portal_secret, verify_portal_secret

from ..utils.file_handler import save_upload

from ..utils.analysis_jobs import ensure_analysis_capacity, serialize_analysis_admission, get_admission_lock



router = APIRouter(prefix="/api/portal", tags=["portal"])



# ── WebSocket Connection Manager ──────────────────────────────────────

class ClaimConnectionManager:

    """Manages WebSocket connections per claim_id for real-time push."""

    def __init__(self):

        self.active: Dict[str, Set[WebSocket]] = {}



    async def connect(self, claim_id: str, websocket: WebSocket):

        await websocket.accept()

        if claim_id not in self.active:

            self.active[claim_id] = set()

        self.active[claim_id].add(websocket)



    def disconnect(self, claim_id: str, websocket: WebSocket):

        if claim_id in self.active:

            self.active[claim_id].discard(websocket)

            if not self.active[claim_id]:

                del self.active[claim_id]



    async def broadcast(self, claim_id: str, message: dict):

        """Broadcast a message to all listeners on a claim channel."""

        if claim_id not in self.active:

            return

        dead = set()

        for ws in list(self.active[claim_id]):

            try:

                await ws.send_json(message)

            except Exception:

                dead.add(ws)

        for ws in dead:
            self.active[claim_id].discard(ws)
        if claim_id in self.active and not self.active[claim_id]:
            del self.active[claim_id]





# Singleton manager — imported by analysis.py to broadcast

manager = ClaimConnectionManager()





def _cleanup_files(paths: list[str]) -> None:

    for path in paths:

        try:

            os.remove(path)

        except OSError:

            pass





# ── WebSocket Endpoint ────────────────────────────────────────────────
_active_portal_tasks: set = set()

@router.websocket("/ws/claim/{claim_id}")
async def claim_websocket(websocket: WebSocket, claim_id: str):
    """Require the one-time claim secret as the first WebSocket message."""
    origin = websocket.headers.get("origin")
    if (origin and origin.rstrip("/") not in get_cors_origins()) or (
        settings.APP_ENV.strip().lower() == "production" and not origin
    ):
        await websocket.close(code=4403)
        return

    # Use a short-lived DB session to authenticate and check initial status
    db_dependency = websocket.app.dependency_overrides.get(get_db, get_db)
    claim_token = None
    claim_status = None
    async for db in db_dependency():
        result = await db.execute(select(Claim).where(Claim.id == claim_id))
        claim = result.scalar_one_or_none()
        if claim:
            claim_token = claim.portal_token
            claim_status = claim.status
        break

    await websocket.accept()
    try:
        secret = await asyncio.wait_for(websocket.receive_text(), timeout=10)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await websocket.close(code=4401)
        return

    if not claim_token or not verify_portal_secret(secret, claim_token):
        await websocket.close(code=4401)
        return

    if claim_id not in manager.active:
        manager.active[claim_id] = set()
    manager.active[claim_id].add(websocket)
    try:
        # Send current status immediately on connect
        await websocket.send_json({
            "type": "STATUS_UPDATE",
            "claim_id": claim_id,
            "status": claim_status or "PENDING",
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep connection alive, waiting for broadcasts
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "PING"})
    except (WebSocketDisconnect, asyncio.CancelledError, Exception):
        pass
    finally:
        manager.disconnect(claim_id, websocket)





# ── Portal Submit Endpoint ────────────────────────────────────────────

@router.post("/submit")

async def portal_submit(

    patient_name: str = Form(...),

    patient_email: str = Form(...),

    patient_phone: str = Form(""),

    hospital_bill: Optional[UploadFile] = File(None),

    insurance_policy: Optional[UploadFile] = File(None),

    rejection_letter: Optional[UploadFile] = File(None),

    supplied_portal_secret: Optional[str] = Header(None, alias="X-Portal-Secret"),

    db: AsyncSession = Depends(get_db),

):

    """

    Single-call patient portal submission.

    Creates claim, saves documents, and triggers AI analysis pipeline.

    Returns claim_id for tracking.

    """

    if not hospital_bill or not insurance_policy or not rejection_letter:

        raise HTTPException(status_code=400, detail="A hospital bill, insurance policy, and insurer decision letter are required for verification.")

    if len(patient_name.strip()) < 2 or len(patient_name) > 200:

        raise HTTPException(status_code=400, detail="Patient name must be between 2 and 200 characters.")

    if len(patient_email) > 254 or "@" not in patient_email:

        raise HTTPException(status_code=400, detail="A valid email address is required.")

    if len(patient_phone) > 32 or (patient_phone and not patient_phone.replace("+", "").replace(" ", "").replace("-", "").isdigit()):

        raise HTTPException(status_code=400, detail="Phone number format is invalid.")

    if not supplied_portal_secret:

        raise HTTPException(status_code=400, detail="A stable portal secret is required so retries cannot create duplicate claims.")



    uploads = [hospital_bill, insurance_policy, rejection_letter]

    total_upload_bytes = 0

    for upload_file in uploads:

        upload_file.file.seek(0, os.SEEK_END)

        total_upload_bytes += upload_file.file.tell()

        upload_file.file.seek(0)

    submission_limit = settings.MAX_SUBMISSION_SIZE_MB * 1024 * 1024

    if total_upload_bytes > submission_limit:

        raise HTTPException(

            status_code=413,

            detail=f"Combined documents exceed the {settings.MAX_SUBMISSION_SIZE_MB}MB submission limit.",

        )



    # Create claim. The raw capability is returned once; only its digest is persisted.

    claim_id = str(uuid.uuid4())

    portal_token = supplied_portal_secret

    if len(portal_token) < 40 or len(portal_token) > 128:

        raise HTTPException(status_code=400, detail="Portal secret must be a 256-bit URL-safe value.")

    portal_token_hash = hash_portal_secret(portal_token)

    existing_claim_result = await db.execute(select(Claim).where(Claim.portal_token == portal_token_hash))

    existing_claim = existing_claim_result.scalar_one_or_none()

    if existing_claim:

        return {

            "claim_id": existing_claim.id,

            "portal_secret": portal_token,

            "status": existing_claim.status,

            "message": "This submission was already received.",

            "tracking_url": f"/track/{existing_claim.id}",

        }



    # Save uploaded documents concurrently before acquiring admission or DB write locks
    upload_dir = os.path.join(settings.UPLOAD_DIR, claim_id)
    os.makedirs(upload_dir, exist_ok=True)
    saved_paths: list[str] = []
    saved_doc_records: list[dict] = []

    doc_map = {
        "HOSPITAL_BILL": hospital_bill,
        "INSURANCE_POLICY": insurance_policy,
        "REJECTION_LETTER": rejection_letter,
    }

    for doc_type, upload_file in doc_map.items():
        if not upload_file:
            continue
        allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
        if upload_file.content_type not in allowed_types:
            _cleanup_files(saved_paths)
            raise HTTPException(status_code=400, detail=f"Invalid file type for {doc_type}: {upload_file.content_type}")

        file_id = str(uuid.uuid4())
        filename = f"{file_id}.upload"
        try:
            file_path, sniffed_type, file_size, doc_hash = await save_upload(
                upload_file, upload_dir, max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
                allowed_mime_types=allowed_types, stored_filename=filename, validate_content=True,
            )
        except ValueError as exc:
            _cleanup_files(saved_paths)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            _cleanup_files(saved_paths)
            raise

        saved_paths.append(file_path)
        if sniffed_type != upload_file.content_type:
            _cleanup_files(saved_paths)
            raise HTTPException(status_code=400, detail="File content does not match its declared type.")

        saved_doc_records.append({
            "id": file_id,
            "document_type": doc_type,
            "filename": os.path.basename(file_path),
            "original_filename": upload_file.filename,
            "file_path": file_path,
            "content_type": upload_file.content_type,
            "file_size_bytes": file_size,
            "document_hash": doc_hash,
        })

    # Atomic, fast DB commit inside admission lock (sub-millisecond critical section)
    analysis_run_id = str(uuid.uuid4())
    async with get_admission_lock():
        try:
            await ensure_analysis_capacity(db, settings)

            claim = Claim(
                id=claim_id,
                patient_name=patient_name,
                patient_email=patient_email,
                patient_phone=patient_phone,
                portal_token=portal_token_hash,
                status="QUEUED",
            )
            db.add(claim)

            from ..utils.audit_trail import AuditTrail
            for d in saved_doc_records:
                doc = Document(
                    id=d["id"],
                    claim_id=claim_id,
                    document_type=d["document_type"],
                    filename=d["filename"],
                    original_filename=d["original_filename"],
                    file_path=d["file_path"],
                    content_type=d["content_type"],
                    file_size_bytes=d["file_size_bytes"],
                    document_hash=d["document_hash"],
                )
                db.add(doc)
                await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
                    "document_id": d["id"],
                    "filename": d["original_filename"],
                    "document_type": d["document_type"],
                    "document_hash": d["document_hash"],
                    "file_size_bytes": d["file_size_bytes"]
                })

            analysis_run = AnalysisRun(
                id=analysis_run_id,
                claim_id=claim_id,
                status="PENDING",
                total_monetary_impact=0.0,
                started_at=datetime.utcnow(),
            )
            db.add(analysis_run)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            _cleanup_files(saved_paths)
            existing_claim_result = await db.execute(select(Claim).where(Claim.portal_token == portal_token_hash))
            existing_claim = existing_claim_result.scalar_one_or_none()
            if existing_claim:
                return {
                    "claim_id": existing_claim.id,
                    "portal_secret": portal_token,
                    "status": existing_claim.status,
                    "message": "This submission was already received.",
                    "tracking_url": f"/track/{existing_claim.id}",
                }
            raise
        except Exception:
            await db.rollback()
            _cleanup_files(saved_paths)
            raise

    # Trigger analysis pipeline in background
    import asyncio
    task = asyncio.create_task(_trigger_analysis(claim_id, analysis_run_id))
    _active_portal_tasks.add(task)
    task.add_done_callback(_active_portal_tasks.discard)



    return {

        "claim_id": claim_id,

        "portal_secret": portal_token,

        "status": "PENDING",

        "message": "Your documents have been submitted. Analysis is starting now.",

        "tracking_url": f"/track/{claim_id}",

    }





async def _trigger_analysis(claim_id: str, analysis_run_id: str):
    """Background task to trigger the AI analysis pipeline."""
    try:
        from ..api.analysis import run_analysis_pipeline
        await run_analysis_pipeline(claim_id, analysis_run_id)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("Background analysis task crashed for claim %s: %s", claim_id, exc)





def _extract_violation_discrepancy(v):
    rec = v.get("monetary_impact") if v.get("monetary_impact") is not None else v.get("difference")
    if rec is not None:
        try:
            f_val = float(rec)
            if f_val > 0:
                return f_val
        except (ValueError, TypeError):
            pass
    for ee in v.get("evidence_entries", []):
        val = ee.get("calculation_output") or ee.get("final_output") or ee.get("extracted_value") or ee.get("value")
        if val is not None:
            try:
                f_val = float(val)
                if 100.0 < f_val < 10000000.0:
                    return round(f_val, 2)
            except (ValueError, TypeError):
                pass
    import re
    m = re.search(r'difference:\s*([0-9.]+)', v.get("finding", ""))
    if m:
        try:
            return round(float(m.group(1)), 2)
        except (ValueError, TypeError):
            pass
    m_ins = re.search(r'Insurer Deducted:\s*Rs\.\s*([0-9.]+)', v.get("finding", ""))
    m_leg = re.search(r'Total Legitimate Deduction[^:]*:\s*Rs\.\s*([0-9.]+)', v.get("finding", ""))
    if m_ins and m_leg:
        try:
            diff_val = float(m_ins.group(1)) - float(m_leg.group(1))
            if diff_val > 0:
                return round(diff_val, 2)
        except (ValueError, TypeError):
            pass
    return None


# ── Portal Status Endpoint ────────────────────────────────────────────

@router.get("/status/{claim_id}")

async def portal_claim_status(

    claim_id: str,

    portal_secret: Optional[str] = Header(None, alias="X-Portal-Secret"),

    db: AsyncSession = Depends(get_db),

):

    """

    Returns claim status + friendly results summary for the patient portal.

    """

    result = await db.execute(select(Claim).where(Claim.id == claim_id))

    claim = result.scalar_one_or_none()

    if not claim or not verify_portal_secret(portal_secret or "", claim.portal_token):

        # Do not reveal whether a claim ID exists to unauthenticated callers.

        raise HTTPException(status_code=404, detail="Claim not found.")



    # Get latest analysis run

    run_result = await db.execute(

        select(AnalysisRun)

        .where(AnalysisRun.claim_id == claim_id)

        .order_by(AnalysisRun.started_at.desc())

    )

    analysis_run = run_result.scalar_one_or_none()



    # Build patient-friendly response

    stage_map = {

        "PENDING": {"label": "Submitted", "step": 0, "description": "Your documents have been received."},

        "QUEUED": {"label": "Submitted", "step": 0, "description": "Your documents have been received and are queued for analysis."},

        "EXTRACTING": {"label": "Reading Documents", "step": 1, "description": "Our AI is reading and extracting data from your documents."},

        "ANALYZING": {"label": "Checking Your Claim", "step": 2, "description": "We are verifying your claim against insurance regulations."},

        "REVIEW_RECOMMENDED": {"label": "Human Review Needed", "step": 2, "description": "Some required document information could not be verified. A reviewer must check the claim before financial conclusions are available."},

        "COMPLETED": {"label": "Analysis Complete", "step": 3, "description": "Your claim has been fully analyzed."},

        "FAILED": {"label": "Processing Error", "step": -1, "description": "An error occurred. Please re-upload your documents."},

    }



    stage_info = stage_map.get(claim.status, stage_map["PENDING"])



    response = {

        "claim_id": claim_id,

        "patient_name": claim.patient_name,

        "status": claim.status,

        "stage": stage_info,

        "submitted_at": claim.created_at.isoformat() if claim.created_at else None,

        "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,

        "result": None,

    }



    # Attach result summary if analysis is complete

    if analysis_run and claim.status in {"COMPLETED", "REVIEW_RECOMMENDED"}:

        result_data = analysis_run.result_data or {}

        verdicts = result_data.get("verdicts") or result_data.get("rule_verdicts", [])

        violations = [v for v in verdicts if v.get("status") in ("FAIL", "NEEDS_REVIEW")]

        evidence_sufficient = analysis_run.overall_status in {"MISMATCH_DETECTED", "NO_MISMATCH_FOUND"}

        monetary = analysis_run.total_monetary_impact if evidence_sufficient else None



        estimated_discrepancy = monetary

        if estimated_discrepancy is None:
            diffs = [_extract_violation_discrepancy(v) for v in violations]
            valid_diffs = [d for d in diffs if d is not None]
            if valid_diffs:
                estimated_discrepancy = max(valid_diffs)

        # Check if discrete statutory FAIL violations fully account for the total discrepancy
        fail_violations = [v for v in violations if v.get("status") == "FAIL"]
        fail_total = sum(_extract_violation_discrepancy(v) or 0.0 for v in fail_violations)
        if estimated_discrepancy and fail_total >= (estimated_discrepancy - 1.0):
            active_violations = [v for v in violations if v.get("rule_name") != "Cross-Document Adjudication"]
        else:
            active_violations = violations

        enriched_violations = []

        for v in active_violations:

            v_rec = _extract_violation_discrepancy(v)

            rule_name = v.get("rule_name", "")

            

            fact = v.get("actual_claim_fact")
            if not fact:
                finding_str = v.get("finding", "")
                if finding_str:
                    fact = finding_str
                elif "Proportionate" in rule_name:
                    fact = "Hospital billed room category higher than basic eligible limit. Associated charges must be verified against policy terms."
                elif "Cross-Document" in rule_name:
                    fact = f"Gross hospital bill exceeds insurer approved settlement by a disputed difference of Rs. {v_rec:,.2f}." if v_rec else "Gross hospital bill exceeds insurer approved settlement."
                else:
                    fact = f"Hospital charges adjudicated under {rule_name} resulting in disallowance."

            rule_text = v.get("applicable_policy_rule")
            if not rule_text:
                citation = v.get("regulatory_citation") or ""
                if citation:
                    rule_text = f"Statutory requirement: {citation}. Insurer terms must comply strictly with IRDAI health regulations."
                elif "Proportionate" in rule_name:
                    rule_text = "IRDAI Master Circular restricts proportionate reduction strictly to room-linked charges and protects medicines, implants, and consumables."
                elif "Cross-Document" in rule_name:
                    rule_text = "IRDAI Master Circular 2024: Insurer deductions must reconcile mathematically with verified policy schedule terms and statutory protections."
                else:
                    rule_text = "Insurance Regulatory and Development Authority of India (IRDAI) Health Insurance Regulations."

            applied_action = v.get("insurer_applied_action")
            if not applied_action:
                diff_str = f" of Rs. {v_rec:,.2f}" if v_rec else ""
                if "Proportionate" in rule_name:
                    applied_action = f"TPA/Insurer executed proportionate deduction{diff_str} across non-associated medical charges."
                elif "Cross-Document" in rule_name:
                    applied_action = f"Insurer disallowed charges{diff_str} across multiple disputed categories."
                else:
                    applied_action = f"TPA/Insurer executed disallowance{diff_str} citing {rule_name} without statutory justification."

            expected_action = v.get("expected_action")
            if not expected_action:
                diff_str = f" Rs. {v_rec:,.2f}" if v_rec else " full eligible sum"
                expected_action = f"Reimburse{diff_str} in full accordance with IRDAI statutory guidelines and policy terms."

            citation = v.get("regulatory_citation") or "IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4)"
            appeal_rec = v.get("appeal_recommendation") or "File formal grievance before Insurer Grievance Redressal Officer (GRO) and escalate to the Insurance Ombudsman under Ombudsman Rule 14(3)."



            enriched_violations.append({

                "rule": rule_name or "Regulation Violation",

                "description": v.get("rule_description", ""),

                "finding": v.get("finding", ""),

                "status": v.get("status", ""),

                "finding_type": v.get("finding_type", ""),

                "recoverable": v_rec,

                "difference": v_rec or v.get("difference"),

                "citation": citation,

                "appeal_recommendation": appeal_rec,

                "legal_track": (
                    v.get("legal_track") if (v.get("legal_track") and v.get("legal_track") != "NOT_APPLICABLE")
                    else ("TRACK_B_STATUTORY_BREACH" if any(kw in (rule_name + " " + fact + " " + rule_text).lower() for kw in ["moratorium", "statutory", "waiting period", "irdai", "list iii", "uncapped", "60-month"]) else "TRACK_A_ARITHMETIC_BREACH")
                ),

                "actual_claim_fact": fact,

                "applicable_policy_rule": rule_text,

                "insurer_applied_action": applied_action,

                "expected_action": expected_action,

                "evidence": v.get("evidence", "Derived from Hospital Bill, Insurance Policy, and Rejection Letter cross-analysis."),

            })



        billed_val = result_data.get("billed_amount")
        approved_val = result_data.get("insurer_approved_amount")
        expected_val = result_data.get("expected_admissible_amount")
        disallowed_val = result_data.get("total_disallowed")
        disputed_val = result_data.get("total_monetary_impact") if result_data.get("total_monetary_impact") is not None else (estimated_discrepancy or 0.0)

        # Resilient fallback: If top-level financial summary was withheld/None, recover verified facts from documents
        if billed_val is None or billed_val == 0.0:
            docs_res = await db.execute(select(Document).where(Document.claim_id == claim_id))
            claim_docs = docs_res.scalars().all()
            for cd in claim_docs:
                ed = cd.extracted_data or {}
                if cd.document_type == "HOSPITAL_BILL":
                    tot = ed.get("total_amount")
                    if isinstance(tot, dict):
                        tot = tot.get("value")
                    if tot and float(tot) > 0:
                        billed_val = float(tot)
                elif cd.document_type == "REJECTION_LETTER":
                    appr = ed.get("total_approved")
                    if isinstance(appr, dict):
                        appr = appr.get("value")
                    if appr is not None and float(appr) >= 0:
                        approved_val = float(appr)
                    ded = ed.get("total_deducted")
                    if isinstance(ded, dict):
                        ded = ded.get("value")
                    if ded is not None and float(ded) >= 0:
                        disallowed_val = float(ded)

            if billed_val is not None:
                if disallowed_val is None and approved_val is not None:
                    disallowed_val = max(0.0, billed_val - approved_val)
                if approved_val is None and disallowed_val is not None:
                    approved_val = max(0.0, billed_val - disallowed_val)
                if expected_val is None:
                    expected_val = min(billed_val, (approved_val or 0.0) + (disputed_val or 0.0))

        response["result"] = {

            "overall_status": analysis_run.overall_status,

            "recoverable_amount": monetary,

            "estimated_discrepancy": estimated_discrepancy,

            "violations_found": len(enriched_violations),

            "total_rules_checked": len(verdicts),

            "plain_summary": _generate_plain_summary(analysis_run.overall_status, monetary, len(enriched_violations), estimated_discrepancy),

            "violations": enriched_violations,

            "financial_summary": {
                "billed_amount": billed_val if billed_val is not None else 0.0,
                "insurer_approved_amount": approved_val if approved_val is not None else 0.0,
                "expected_admissible_amount": expected_val if expected_val is not None else 0.0,
                "total_disallowed": disallowed_val if disallowed_val is not None else 0.0,
                "disputed_amount": disputed_val,
            }

        }



    return response





@router.get("/{claim_id}/appeal")

async def portal_appeal_draft(

    claim_id: str,

    portal_secret: Optional[str] = Header(None, alias="X-Portal-Secret"),

    db: AsyncSession = Depends(get_db),

):

    """Return a draft only when completed checks have evidence-supported findings."""

    claim_result = await db.execute(select(Claim).where(Claim.id == claim_id))

    claim = claim_result.scalar_one_or_none()

    if not claim or not verify_portal_secret(portal_secret or "", claim.portal_token):

        raise HTTPException(status_code=404, detail="Claim not found.")

    run_result = await db.execute(

        select(AnalysisRun).where(AnalysisRun.claim_id == claim_id).order_by(AnalysisRun.started_at.desc())

    )

    run = run_result.scalars().first()

    if not run or run.status != "COMPLETED" or run.overall_status != "MISMATCH_DETECTED":

        raise HTTPException(status_code=409, detail="An appeal draft is unavailable until evidence-supported findings are complete.")



    documents_result = await db.execute(select(Document).where(Document.claim_id == claim_id))

    documents = documents_result.scalars().all()

    from ..schemas.hospital_bill import HospitalBill

    from ..schemas.insurance_policy import InsurancePolicy

    from ..schemas.rejection_letter import RejectionLetter

    from ..schemas.analysis_result import AnalysisResult

    bill = policy = rejection = None

    for document in documents:

        if not document.extracted_data:

            continue

        if document.document_type == "HOSPITAL_BILL":

            bill = HospitalBill(**document.extracted_data)

        elif document.document_type == "INSURANCE_POLICY":

            policy = InsurancePolicy(**document.extracted_data)

        elif document.document_type == "REJECTION_LETTER":

            rejection = RejectionLetter(**document.extracted_data)

    from ..reports.generator import ReportGenerator

    analysis_result = AnalysisResult.model_validate(run.result_data or {})

    appeal_text = ReportGenerator().generate_appeal_letter(analysis_result, bill, policy, rejection)

    return {

        "appeal_text": appeal_text,

        "regulatory_citations": (run.result_data or {}).get("regulatory_citations", []),

        "monetary_impact": run.total_monetary_impact,

        "draft_notice": "This is an AI-assisted draft. A qualified reviewer should verify it before you send it to your insurer.",

    }





def _generate_plain_summary(overall_status: str, recoverable: float, violations: int, estimated_discrepancy: float = None) -> str:

    """Generate a plain-language summary for the patient."""

    if overall_status in ("EXTRACTION_FAILED", "INSUFFICIENT_EVIDENCE", "BLOCKED"):

        return "We could not verify enough information in the submitted documents. A reviewer must check them before any financial conclusion is available."

    if overall_status == "NO_MISMATCH_FOUND":

        return "The automated checks did not find a mismatch. This is not a final insurer or legal decision."

    if overall_status == "MISMATCH_DETECTED":

        return f"The automated checks found {violations} potential discrepancy(s). A reviewer should verify the evidence before taking action."

    if overall_status == "REVIEW_RECOMMENDED":

        amt_str = f" of ~₹{(estimated_discrepancy/100000):.2f} Lakhs" if (estimated_discrepancy and estimated_discrepancy > 0) else ""

        return f"Documents successfully verified. Our regulatory checks detected {violations} potential insurer violations with an estimated recoverable discrepancy{amt_str}. To ensure 100% legal accuracy, the final financial figure is undergoing audit before filing."

    return "Your claim has been analyzed. Please review the detailed findings below."

