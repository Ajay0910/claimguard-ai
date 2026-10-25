from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update
from typing import Optional
import asyncio
import uuid
from datetime import datetime

from ..database import AsyncSessionLocal, get_db
from ..models.claim import Claim, Document, AnalysisRun, RuleVerdictRecord, EvidenceLedgerRecord
from ..extraction.pipeline import ExtractionPipeline
from ..rules.engine import RuleEngine
from ..utils.audit_trail import AuditTrail
from ..schemas.analysis_result import AnalysisResult
from ..security.auth import require_staff_access
from ..utils.analysis_jobs import ensure_analysis_capacity, serialize_analysis_admission, limit_analysis_workers
from ..config import settings

router = APIRouter(prefix='/api', tags=['analysis'], dependencies=[Depends(require_staff_access)])

_active_pipeline_tasks: set = set()


async def _broadcast_claim_status(claim_id: str, status_value: str) -> None:
    from .portal import manager
    await manager.broadcast(claim_id, {
        "type": "STATUS_UPDATE",
        "claim_id": claim_id,
        "status": status_value,
        "timestamp": datetime.utcnow().isoformat(),
    })


def suppress_financial_conclusion_when_review_needed(analysis_result: AnalysisResult) -> None:
    if analysis_result.overall_status == "EXTRACTION_FAILED":
        return
    has_actionable_findings = any(v.status == "FAIL" for v in analysis_result.rule_verdicts)
    unresolved = any(
        verdict.status in {"NEEDS_REVIEW", "CONFLICT", "BLOCKED", "INSUFFICIENT_EVIDENCE"}
        and (verdict.rule_name != "Cross-Document Adjudication" or not has_actionable_findings)
        for verdict in analysis_result.rule_verdicts
    )
    if not unresolved:
        return

    analysis_result.overall_status = "BLOCKED" if any(
        verdict.status == "BLOCKED" for verdict in analysis_result.rule_verdicts
    ) else "REVIEW_RECOMMENDED"
    analysis_result.summary = "One or more rule checks require human review. Financial conclusions are withheld until the evidence is verified."
    for field_name in (
        "total_monetary_impact", "expected_admissible_amount", "insurer_approved_amount",
        "billed_amount", "total_disallowed", "legitimate_deduction", "approved_pct",
        "recoverable_pct", "legitimate_pct", "recovery_yield",
    ):
        setattr(analysis_result, field_name, None)
    for verdict in analysis_result.rule_verdicts:
        verdict.insurer_approved_amount = None
        verdict.expected_admissible_amount = None
        verdict.monetary_impact = None
        verdict.insurer_calculation = None
        verdict.correct_calculation = None
        verdict.difference = None

@limit_analysis_workers
async def run_analysis_pipeline(claim_id: str, analysis_run_id: str):
    async with AsyncSessionLocal() as db:
        try:
            # Claim the durable queued job exactly once before doing provider work.
            acquired = await db.execute(
                update(AnalysisRun)
                .where(AnalysisRun.id == analysis_run_id, AnalysisRun.claim_id == claim_id, AnalysisRun.status == "PENDING")
                .values(status="RUNNING", started_at=datetime.utcnow())
            )
            if acquired.rowcount != 1:
                await db.rollback()
                return
            claim_result = await db.execute(select(Claim).where(Claim.id == claim_id))
            claim = claim_result.scalar_one_or_none()
            if claim:
                claim.status = "EXTRACTING"
            await db.commit()
            await _broadcast_claim_status(claim_id, "EXTRACTING")

            # 1. Get all documents for claim
            result = await db.execute(select(Document).where(Document.claim_id == claim_id))
            documents = result.scalars().all()
            
            # 2. Extract
            from ..config import settings
            vlm_api_key = settings.OPENAI_API_KEY if settings.VLM_PROVIDER == "openai" else (settings.GEMINI_API_KEY if settings.VLM_PROVIDER == "gemini" else settings.ANTHROPIC_API_KEY)
            pipeline = ExtractionPipeline(config={
                "vlm_provider": settings.VLM_PROVIDER,
                "vlm_api_key": vlm_api_key,
                "vlm_model": settings.GEMINI_MODEL if settings.VLM_PROVIDER == "gemini" else None,
                "max_document_pages": settings.MAX_DOCUMENT_PAGES,
                "max_document_total_pixels": settings.MAX_DOCUMENT_TOTAL_PIXELS,
            })
            extracted_bill = None
            extracted_policy = None
            extracted_rejection = None
            extraction_verdicts = []
            present_document_types = set()
            from ..schemas.evidence_ledger import EvidenceLedger
            from ..utils.evidence_capture import validate_and_record_financial_evidence
            evidence_ledger = EvidenceLedger(claim_id=claim_id)
            import asyncio
            for doc in documents:
                present_document_types.add(doc.document_type)
                extracted = await asyncio.to_thread(pipeline.process_document, doc.file_path, doc.document_type)
                data = extracted.get("data")
                status = extracted.get("status", "SUCCESS")
                issues = extracted.get("issues", [])

                if data is not None:
                    evidence_issues = validate_and_record_financial_evidence(
                        data, doc, extracted.get("ocr_pages", extracted.get("ocr_fallback_text", "")), evidence_ledger
                    )
                    if evidence_issues:
                        status = "INSUFFICIENT_EVIDENCE"
                        issues = [*issues, *evidence_issues]
                
                if status != "SUCCESS" or data is None:
                    from ..schemas.analysis_result import RuleVerdict
                    extraction_verdicts.append(RuleVerdict(
                        rule_name=f"{doc.document_type} Extraction Validation",
                        rule_description="Validates that critical fields are present and confident.",
                        status="INSUFFICIENT_EVIDENCE",
                        confidence=0.0,
                        finding=f"Structured extraction unavailable (status: {status}). Issues: {', '.join(issues) or 'No structured data returned.'}"
                    ))
                    
                if data:
                    doc.extracted_data = data.model_dump(mode='json') if hasattr(data, "model_dump") else (data.dict() if hasattr(data, "dict") else data)
                else:
                    doc.extracted_data = extracted
                
                if doc.document_type == 'HOSPITAL_BILL':
                    extracted_bill = data
                elif doc.document_type == 'INSURANCE_POLICY':
                    extracted_policy = data
                elif doc.document_type == 'REJECTION_LETTER':
                    extracted_rejection = data
                    
            await AuditTrail.log(db, claim_id, "EXTRACTION_COMPLETED", {"documents_processed": len(documents)})
            
            required_document_types = {"HOSPITAL_BILL", "INSURANCE_POLICY", "REJECTION_LETTER"}
            for missing_type in sorted(required_document_types - present_document_types):
                from ..schemas.analysis_result import RuleVerdict
                extraction_verdicts.append(RuleVerdict(
                    rule_name=f"{missing_type} Extraction Validation",
                    rule_description="A bill, policy, and insurer settlement/rejection document are required for cross-document verification.",
                    status="INSUFFICIENT_EVIDENCE",
                    confidence=0.0,
                    finding="Required document was not uploaded. Financial adjudication was not run."
                ))

            # Missing, failed, or low-confidence extraction must never be
            # interpreted as zero-valued financial inputs by the rule engine.
            extraction_failed = bool(extraction_verdicts)
            if extraction_failed:
                analysis_result = AnalysisResult(
                    claim_id=claim_id,
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    documents_analyzed=sorted(present_document_types),
                    overall_status="EXTRACTION_FAILED",
                    summary="Financial adjudication was skipped because one or more required documents could not be extracted with sufficient evidence.",
                    rule_verdicts=extraction_verdicts,
                    total_monetary_impact=None,
                    expected_admissible_amount=None,
                    insurer_approved_amount=None,
                    billed_amount=None,
                    evidence_ledger=evidence_ledger,
                )
            else:
                claim.status = "ANALYZING"
                await db.commit()
                await _broadcast_claim_status(claim_id, "ANALYZING")
                # 3. Rule engine
                engine = RuleEngine()
                analysis_result = await asyncio.to_thread(
                    engine.run_all_rules,
                    bill=extracted_bill,
                    policy=extracted_policy,
                    rejection=extracted_rejection,
                    ledger=evidence_ledger
                )
                analysis_result.evidence_ledger = evidence_ledger
            
            # Post-process to enforce Point 14 (Downgrade status if evidence is missing or confidence < 0.8)
            for verdict in analysis_result.rule_verdicts:
                if verdict.status in ["BLOCKED", "SKIPPED", "NOT_APPLICABLE"]:
                    continue
                if verdict.confidence < 0.8:
                    if verdict.status not in ["NEEDS_REVIEW", "CONFLICT", "INSUFFICIENT_EVIDENCE"]:
                        verdict.status = "INSUFFICIENT_EVIDENCE"
            
            if extraction_verdicts and not extraction_failed:
                analysis_result.rule_verdicts.extend(extraction_verdicts)
                analysis_result.overall_status = "REVIEW_RECOMMENDED"
                analysis_result.compute_aggregates()

            suppress_financial_conclusion_when_review_needed(analysis_result)
            
            # Run Forensics Engine
            from ..forensics.engine import ForensicsEngine
            forensics_engine = ForensicsEngine()
            forensics_res = await asyncio.to_thread(forensics_engine.run, documents, bill=extracted_bill)
            forensics_dict = forensics_res.model_dump(mode='json') if hasattr(forensics_res, "model_dump") else (forensics_res.dict() if hasattr(forensics_res, "dict") else forensics_res)
            
            # 4. Store results
            result_query = await db.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_run_id))
            analysis_run = result_query.scalar_one()
            analysis_run.status = "COMPLETED"
            analysis_run.completed_at = datetime.utcnow()
            
            result_dict = analysis_result.model_dump(mode='json') if hasattr(analysis_result, "model_dump") else analysis_result.dict()
            result_dict["forensics"] = forensics_dict
            analysis_run.result_data = result_dict
            
            analysis_run.overall_status = analysis_result.overall_status if hasattr(analysis_result, 'overall_status') else 'UNKNOWN'
            analysis_run.total_monetary_impact = analysis_result.total_monetary_impact
            
            # Create rule verdicts
            for verdict in analysis_result.rule_verdicts:
                db.add(RuleVerdictRecord(
                    id=str(uuid.uuid4()),
                    analysis_run_id=analysis_run.id,
                    rule_name=verdict.rule_name,
                    status=verdict.status,
                    confidence=verdict.confidence if hasattr(verdict, "confidence") and verdict.confidence is not None else 1.0,
                    finding=verdict.finding,
                    monetary_impact=verdict.monetary_impact if hasattr(verdict, "monetary_impact") else 0.0,
                    regulatory_citation=verdict.regulatory_citation if hasattr(verdict, "regulatory_citation") else None,
                    appeal_recommendation=verdict.appeal_recommendation if hasattr(verdict, "appeal_recommendation") else None,
                    actual_claim_fact=verdict.actual_claim_fact if hasattr(verdict, "actual_claim_fact") else None,
                    applicable_policy_rule=verdict.applicable_policy_rule if hasattr(verdict, "applicable_policy_rule") else None,
                    insurer_applied_action=verdict.insurer_applied_action if hasattr(verdict, "insurer_applied_action") else None,
                    expected_action=verdict.expected_action if hasattr(verdict, "expected_action") else None,
                    difference=verdict.difference if hasattr(verdict, "difference") else None,
                    evidence=verdict.evidence if hasattr(verdict, "evidence") else None
                ))
            
            # 5. Update claim status
            claim_query = await db.execute(select(Claim).where(Claim.id == claim_id))
            claim = claim_query.scalar_one()
            claim.status = "REVIEW_RECOMMENDED" if analysis_result.overall_status in {"EXTRACTION_FAILED", "REVIEW_RECOMMENDED", "INSUFFICIENT_EVIDENCE", "BLOCKED"} else "COMPLETED"
            claim.updated_at = datetime.utcnow()
            
            await AuditTrail.log(db, claim_id, "ANALYSIS_COMPLETED", {"status": analysis_run.status})
            await db.commit()
            await _broadcast_claim_status(claim_id, claim.status)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Analysis pipeline failed for claim %s (%s: %s)", claim_id, type(e).__name__, getattr(e, "name", ""))
            try:
                await db.rollback()
            except Exception:
                pass
            # Mark as failed in a new transaction (retry up to 3 times on transient DB lock)
            for attempt in range(3):
                try:
                    async with AsyncSessionLocal() as session2:
                        result_query = await session2.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_run_id))
                        analysis_run = result_query.scalar_one_or_none()
                        if analysis_run:
                            analysis_run.status = "FAILED"
                            analysis_run.completed_at = datetime.utcnow()
                            session2.add(analysis_run)
                        
                        claim_query = await session2.execute(select(Claim).where(Claim.id == claim_id))
                        claim = claim_query.scalar_one_or_none()
                        if claim:
                            claim.status = "FAILED"
                            session2.add(claim)
                            
                        await AuditTrail.log(session2, claim_id, "ANALYSIS_FAILED", {"error_type": type(e).__name__})
                        await session2.commit()
                        await _broadcast_claim_status(claim_id, "FAILED")
                        break
                except Exception as commit_exc:
                    if attempt == 2:
                        raise commit_exc
                    await asyncio.sleep(0.1 * (attempt + 1))

@router.post('/analyze/{claim_id}')
@serialize_analysis_admission
async def trigger_analysis(
    claim_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    doc_result = await db.execute(select(Document).where(Document.claim_id == claim_id))
    documents = doc_result.scalars().all()
    if not documents:
        raise HTTPException(status_code=400, detail="Claim has no documents")

    active_result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.claim_id == claim_id, AnalysisRun.status.in_(["PENDING", "RUNNING"]))
        .order_by(AnalysisRun.started_at.desc())
    )
    active_run = active_result.scalars().first()
    if active_run:
        return {"analysis_run_id": active_run.id, "status": active_run.status}

    await ensure_analysis_capacity(db, settings)

    # A compare-and-set on the claim prevents two concurrent callers from creating
    # separate runs after both observed an empty active-run query.
    claim_gate = await db.execute(
        update(Claim)
        .where(Claim.id == claim_id, Claim.status.not_in(["QUEUED", "EXTRACTING", "ANALYZING"]))
        .values(status="QUEUED")
    )
    if claim_gate.rowcount != 1:
        await db.rollback()
        retry_result = await db.execute(
            select(AnalysisRun).where(AnalysisRun.claim_id == claim_id, AnalysisRun.status.in_(["PENDING", "RUNNING"]))
            .order_by(AnalysisRun.started_at.desc())
        )
        retry_run = retry_result.scalars().first()
        if retry_run:
            return {"analysis_run_id": retry_run.id, "status": retry_run.status}
        raise HTTPException(status_code=409, detail="Claim analysis is already being prepared.")
        
    analysis_run_id = str(uuid.uuid4())
    run = AnalysisRun(
        id=analysis_run_id,
        claim_id=claim_id,
        status="PENDING",
        total_monetary_impact=0.0,
        started_at=datetime.utcnow()
    )
    db.add(run)
    claim.status = "QUEUED"
    
    await AuditTrail.log(db, claim_id, "ANALYSIS_STARTED", {"analysis_run_id": analysis_run_id})
    await db.commit()
    
    background_tasks.add_task(run_analysis_pipeline, claim_id, analysis_run_id)
    
    return {
        "analysis_run_id": analysis_run_id,
        "status": "PENDING"
    }


async def resume_analysis_jobs():
    """Requeue interrupted jobs at single-instance startup and start pending work."""
    async with AsyncSessionLocal() as db:
        interrupted_result = await db.execute(select(AnalysisRun.id).where(AnalysisRun.status == "RUNNING"))
        interrupted_ids = list(interrupted_result.scalars().all())
        if interrupted_ids:
            await db.execute(
                update(AnalysisRun)
                .where(AnalysisRun.id.in_(interrupted_ids))
                .values(
                    status="PENDING",
                    result_data=None,
                    forensics_data=None,
                    overall_status=None,
                    total_monetary_impact=None,
                    completed_at=None,
                )
            )
            await db.execute(delete(EvidenceLedgerRecord).where(EvidenceLedgerRecord.analysis_run_id.in_(interrupted_ids)))
            await db.execute(delete(RuleVerdictRecord).where(RuleVerdictRecord.analysis_run_id.in_(interrupted_ids)))
        pending = await db.execute(select(AnalysisRun.id, AnalysisRun.claim_id).where(AnalysisRun.status == "PENDING"))
        jobs = pending.all()
        if interrupted_ids:
            await db.execute(update(Claim).where(Claim.status.in_(["ANALYZING", "EXTRACTING"])).values(status="QUEUED"))
        await db.commit()
    import asyncio
    for run_id, claim_id in jobs:
        task = asyncio.create_task(run_analysis_pipeline(claim_id, run_id))
        _active_pipeline_tasks.add(task)
        task.add_done_callback(_active_pipeline_tasks.discard)

@router.get('/analyze/{claim_id}/status')
async def get_analysis_status(claim_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.claim_id == claim_id)
        .order_by(AnalysisRun.started_at.desc())
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="No analysis run found for this claim")
        
    return {
        "analysis_run_id": run.id,
        "status": run.status,
        "overall_status": run.overall_status,
        "started_at": run.started_at,
        "completed_at": run.completed_at
    }

@router.get('/analyze/{claim_id}/result')
async def get_analysis_result(claim_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.claim_id == claim_id)
        .order_by(AnalysisRun.started_at.desc())
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="No analysis run found")
        
    return {
        "analysis_run_id": run.id,
        "status": run.status,
        "result": run.result_data
    }
