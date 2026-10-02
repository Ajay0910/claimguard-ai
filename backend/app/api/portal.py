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
from ..security.auth import generate_portal_secret, hash_portal_secret, verify_portal_secret
from ..utils.file_handler import save_upload
from ..utils.analysis_jobs import ensure_analysis_capacity, serialize_analysis_admission

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


# Singleton manager — imported by analysis.py to broadcast
manager = ClaimConnectionManager()


def _cleanup_files(paths: list[str]) -> None:
    for path in paths:
        try:
            os.remove(path)
        except OSError:
            pass


# ── WebSocket Endpoint ────────────────────────────────────────────────
@router.websocket("/ws/claim/{claim_id}")
async def claim_websocket(websocket: WebSocket, claim_id: str, db: AsyncSession = Depends(get_db)):
    """Require the one-time claim secret as the first WebSocket message."""
    origin = websocket.headers.get("origin")
    if (origin and origin.rstrip("/") not in get_cors_origins()) or (
        settings.APP_ENV.strip().lower() == "production" and not origin
    ):
        await websocket.close(code=4403)
        return
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    await websocket.accept()
    try:
        secret = await asyncio.wait_for(websocket.receive_text(), timeout=10)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await websocket.close(code=4401)
        return
    if not claim or not verify_portal_secret(secret, claim.portal_token):
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
            "status": claim.status,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep connection alive, waiting for broadcasts
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "PING"})
    except WebSocketDisconnect:
        manager.disconnect(claim_id, websocket)


# ── Portal Submit Endpoint ────────────────────────────────────────────
@router.post("/submit")
@serialize_analysis_admission
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
    portal_token = supplied_portal_secret or generate_portal_secret()
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
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
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

    # Save uploaded documents
    upload_dir = os.path.join(settings.UPLOAD_DIR, claim_id)
    os.makedirs(upload_dir, exist_ok=True)
    saved_paths: list[str] = []

    doc_map = {
        "HOSPITAL_BILL": hospital_bill,
        "INSURANCE_POLICY": insurance_policy,
        "REJECTION_LETTER": rejection_letter,
    }

    for doc_type, upload_file in doc_map.items():
        if not upload_file:
            continue
        # Validate MIME type
        allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
        if upload_file.content_type not in allowed_types:
            await db.rollback()
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
            await db.rollback()
            _cleanup_files(saved_paths)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            try:
                await db.rollback()
            finally:
                _cleanup_files(saved_paths)
            raise
        saved_paths.append(file_path)
        if sniffed_type != upload_file.content_type:
            await db.rollback()
            _cleanup_files(saved_paths)
            raise HTTPException(status_code=400, detail="File content does not match its declared type.")

        from ..utils.audit_trail import AuditTrail

        doc = Document(
            id=file_id,
            claim_id=claim_id,
            document_type=doc_type,
            filename=os.path.basename(file_path),
            original_filename=upload_file.filename,
            file_path=file_path,
            content_type=upload_file.content_type,
            file_size_bytes=file_size,
            document_hash=doc_hash,
        )
        db.add(doc)

        try:
            await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
                "document_id": file_id,
                "filename": upload_file.filename,
                "document_type": doc_type,
                "document_hash": doc_hash,
                "file_size_bytes": file_size
            })
        except Exception:
            await db.rollback()
            _cleanup_files(saved_paths)
            raise

    analysis_run_id = str(uuid.uuid4())
    analysis_run = AnalysisRun(
        id=analysis_run_id,
        claim_id=claim_id,
        status="PENDING",
        started_at=datetime.utcnow(),
    )
    db.add(analysis_run)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        _cleanup_files(saved_paths)
        raise

    # Trigger analysis pipeline in background
    import asyncio
    asyncio.create_task(_trigger_analysis(claim_id, analysis_run_id))

    return {
        "claim_id": claim_id,
        "portal_secret": portal_token,
        "status": "PENDING",
        "message": "Your documents have been submitted. Analysis is starting now.",
        "tracking_url": f"/track/{claim_id}",
    }


async def _trigger_analysis(claim_id: str, analysis_run_id: str):
    """Background task to trigger the AI analysis pipeline."""
    from ..api.analysis import run_analysis_pipeline
    await run_analysis_pipeline(claim_id, analysis_run_id)


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

        response["result"] = {
            "overall_status": analysis_run.overall_status,
            "recoverable_amount": monetary,
            "violations_found": len(violations),
            "total_rules_checked": len(verdicts),
            "plain_summary": _generate_plain_summary(analysis_run.overall_status, monetary, len(violations)),
            "violations": [
                {
                    "rule": v.get("rule_name", ""),
                    "finding": v.get("finding", ""),
                    "recoverable": v.get("monetary_impact") if evidence_sufficient else None,
                    "citation": v.get("regulatory_citation", ""),
                }
                for v in violations
            ],
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


def _generate_plain_summary(overall_status: str, recoverable: float, violations: int) -> str:
    """Generate a plain-language summary for the patient."""
    if overall_status in ("EXTRACTION_FAILED", "INSUFFICIENT_EVIDENCE", "BLOCKED"):
        return "We could not verify enough information in the submitted documents. A reviewer must check them before any financial conclusion is available."
    if overall_status == "NO_MISMATCH_FOUND":
        return "The automated checks did not find a mismatch. This is not a final insurer or legal decision."
    if overall_status == "MISMATCH_DETECTED":
        return f"The automated checks found {violations} potential discrepancy(s). A reviewer should verify the evidence before taking action."
    if overall_status == "REVIEW_RECOMMENDED":
        return "The documents or checks need human review before a reliable financial conclusion can be made."
    return "Your claim has been analyzed. Please review the detailed findings below."
