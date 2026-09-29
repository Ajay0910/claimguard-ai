import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Set
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles
import os

from ..database import get_db
from ..models.claim import Claim, Document, AnalysisRun
from ..config import settings

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


# ── WebSocket Endpoint ────────────────────────────────────────────────
@router.websocket("/ws/claim/{claim_id}")
async def claim_websocket(websocket: WebSocket, claim_id: str, db: AsyncSession = Depends(get_db)):
    """Real-time status updates for a specific claim."""
    # Validate claim exists
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        await websocket.close(code=4004)
        return

    await manager.connect(claim_id, websocket)
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
async def portal_submit(
    patient_name: str = Form(...),
    patient_email: str = Form(...),
    patient_phone: str = Form(""),
    hospital_bill: Optional[UploadFile] = File(None),
    insurance_policy: Optional[UploadFile] = File(None),
    rejection_letter: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Single-call patient portal submission.
    Creates claim, saves documents, and triggers AI analysis pipeline.
    Returns claim_id for tracking.
    """
    if not hospital_bill and not insurance_policy and not rejection_letter:
        raise HTTPException(status_code=400, detail="At least one document must be uploaded.")

    # Create claim
    claim_id = str(uuid.uuid4())
    portal_token = str(uuid.uuid4())

    claim = Claim(
        id=claim_id,
        patient_name=patient_name,
        patient_email=patient_email,
        patient_phone=patient_phone,
        portal_token=portal_token,
        status="PENDING",
    )
    db.add(claim)
    await db.flush()

    # Save uploaded documents
    upload_dir = os.path.join(settings.UPLOAD_DIR, claim_id)
    os.makedirs(upload_dir, exist_ok=True)

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
            raise HTTPException(status_code=400, detail=f"Invalid file type for {doc_type}: {upload_file.content_type}")

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(upload_file.filename or "file.pdf")[1] or ".pdf"
        filename = f"{file_id}{ext}"
        file_path = os.path.join(upload_dir, filename)

        content = await upload_file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{doc_type} exceeds 25MB limit.")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        from ..utils.file_handler import compute_sha256_bytes
        from ..utils.audit_trail import AuditTrail

        doc_hash = compute_sha256_bytes(content)

        doc = Document(
            id=file_id,
            claim_id=claim_id,
            document_type=doc_type,
            filename=filename,
            original_filename=upload_file.filename,
            file_path=file_path,
            content_type=upload_file.content_type,
            file_size_bytes=len(content),
            document_hash=doc_hash,
        )
        db.add(doc)

        await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
            "document_id": file_id,
            "filename": upload_file.filename,
            "document_type": doc_type,
            "document_hash": doc_hash,
            "file_size_bytes": len(content)
        })

    analysis_run_id = str(uuid.uuid4())
    analysis_run = AnalysisRun(
        id=analysis_run_id,
        claim_id=claim_id,
        status="PENDING",
        started_at=datetime.utcnow(),
    )
    db.add(analysis_run)

    await db.commit()

    # Trigger analysis pipeline in background
    import asyncio
    asyncio.create_task(_trigger_analysis(claim_id, analysis_run_id))

    return {
        "claim_id": claim_id,
        "portal_token": portal_token,
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
async def portal_claim_status(claim_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns claim status + friendly results summary for the patient portal.
    """
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
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
        "EXTRACTING": {"label": "Reading Documents", "step": 1, "description": "Our AI is reading and extracting data from your documents."},
        "ANALYZING": {"label": "Checking Your Claim", "step": 2, "description": "We are verifying your claim against insurance regulations."},
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
    if analysis_run and claim.status == "COMPLETED":
        result_data = analysis_run.result_data or {}
        verdicts = result_data.get("verdicts") or result_data.get("rule_verdicts", [])
        violations = [v for v in verdicts if v.get("status") in ("FAIL", "NEEDS_REVIEW")]
        monetary = analysis_run.total_monetary_impact or 0

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
                    "recoverable": v.get("monetary_impact", 0),
                    "citation": v.get("regulatory_citation", ""),
                }
                for v in violations
            ],
        }

    return response


def _generate_plain_summary(overall_status: str, recoverable: float, violations: int) -> str:
    """Generate a plain-language summary for the patient."""
    if overall_status == "CLAIM_SUPPORTED":
        if recoverable > 0:
            lakhs = recoverable / 100000
            return (
                f"Good news! Your claim analysis found that your insurer may have incorrectly "
                f"deducted ₹{lakhs:.1f} Lakh from your settlement. You have a strong basis to "
                f"appeal and recover this amount."
            )
        return "Your claim appears to be settled correctly. No major violations were found."
    elif overall_status in ("PARTIAL_DISPUTE", "NEEDS_REVIEW"):
        return (
            f"We found {violations} potential issue(s) with your claim that may be worth disputing. "
            f"Review the details below and consider filing a formal appeal."
        )
    elif overall_status == "CLAIM_DISPUTED":
        return (
            f"Your claim has significant violations. We found {violations} regulatory breach(es). "
            f"We strongly recommend filing a formal appeal using the letter generated below."
        )
    return "Your claim has been analyzed. Please review the detailed findings below."
