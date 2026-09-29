from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
from datetime import datetime

from ..database import AsyncSessionLocal, get_db
from ..models.claim import Claim, Document, AnalysisRun, RuleVerdictRecord
from ..extraction.pipeline import ExtractionPipeline
from ..rules.engine import RuleEngine
from ..utils.audit_trail import AuditTrail
from ..schemas.analysis_result import AnalysisResult

router = APIRouter(prefix='/api', tags=['analysis'])

async def run_analysis_pipeline(claim_id: str, analysis_run_id: str):
    async with AsyncSessionLocal() as db:
        try:
            # 1. Get all documents for claim
            result = await db.execute(select(Document).where(Document.claim_id == claim_id))
            documents = result.scalars().all()
            
            # 2. Extract
            from ..config import settings
            vlm_api_key = settings.OPENAI_API_KEY if settings.VLM_PROVIDER == "openai" else (settings.GEMINI_API_KEY if settings.VLM_PROVIDER == "gemini" else settings.ANTHROPIC_API_KEY)
            pipeline = ExtractionPipeline(config={"vlm_provider": settings.VLM_PROVIDER, "vlm_api_key": vlm_api_key})
            extracted_bill = None
            extracted_policy = None
            extracted_rejection = None
            
            extraction_verdicts = []
            for doc in documents:
                extracted = pipeline.process_document(doc.file_path, expected_type=doc.document_type)
                data = extracted.get("data")
                status = extracted.get("status", "SUCCESS")
                issues = extracted.get("issues", [])
                
                if status in ["NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"]:
                    from ..schemas.analysis_result import RuleVerdict
                    extraction_verdicts.append(RuleVerdict(
                        rule_name=f"{doc.document_type} Extraction Validation",
                        rule_description="Validates that critical fields are present and confident.",
                        status=status,
                        confidence=0.0 if status == "INSUFFICIENT_EVIDENCE" else 1.0,
                        finding=f"Extraction issues found: {', '.join(issues)}"
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
            
            from ..schemas.evidence_ledger import EvidenceLedger
            evidence_ledger = EvidenceLedger(claim_id=claim_id)
            
            # 3. Rule engine
            engine = RuleEngine()
            analysis_result = engine.run_all_rules(
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
            
            if extraction_verdicts:
                analysis_result.rule_verdicts.extend(extraction_verdicts)
                analysis_result.overall_status = "REVIEW_RECOMMENDED"
                analysis_result.compute_aggregates()
            
            # Run Forensics Engine
            from ..forensics.engine import ForensicsEngine
            forensics_engine = ForensicsEngine()
            forensics_res = forensics_engine.run(documents, bill=extracted_bill)
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
            analysis_run.total_monetary_impact = analysis_result.total_monetary_impact if hasattr(analysis_result, 'total_monetary_impact') else 0.0
            
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
            claim.status = "COMPLETED"
            claim.updated_at = datetime.utcnow()
            
            await AuditTrail.log(db, claim_id, "ANALYSIS_COMPLETED", {"status": analysis_run.status})
            await db.commit()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"PIPELINE CRASHED: {str(e)}")
            await db.rollback()
            # Mark as failed in a new transaction
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
                    
                await AuditTrail.log(session2, claim_id, "ANALYSIS_FAILED", {"error": str(e)})
                await session2.commit()

@router.post('/analyze/{claim_id}')
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
        
    analysis_run_id = str(uuid.uuid4())
    run = AnalysisRun(
        id=analysis_run_id,
        claim_id=claim_id,
        status="RUNNING",
        started_at=datetime.utcnow()
    )
    db.add(run)
    claim.status = "ANALYZING"
    
    await AuditTrail.log(db, claim_id, "ANALYSIS_STARTED", {"analysis_run_id": analysis_run_id})
    await db.commit()
    
    background_tasks.add_task(run_analysis_pipeline, claim_id, analysis_run_id)
    
    return {
        "analysis_run_id": analysis_run_id,
        "status": "RUNNING"
    }

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
