from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_db
from ..security.auth import require_staff_access
from ..models.claim import Claim, AuditLog, AnalysisRun
from ..utils.audit_trail import AuditTrail

router = APIRouter(prefix='/api', tags=['reports'], dependencies=[Depends(require_staff_access)])

@router.get('/reports/{claim_id}')
async def get_report(claim_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.claim_id == claim_id)
        .order_by(AnalysisRun.started_at.desc())
    )
    run = result.scalars().first()
    
    if not run or run.status != "COMPLETED":
        raise HTTPException(status_code=404, detail="Completed analysis not found")
        
    return {
        "claim_id": claim_id,
        "analysis_run_id": run.id,
        "report_data": run.result_data,
        "overall_status": run.overall_status,
        "total_monetary_impact": run.total_monetary_impact
    }

@router.get('/reports/{claim_id}/appeal')
async def get_appeal_draft(claim_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from ..models.claim import Document
    result = await db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.claim_id == claim_id)
        .order_by(AnalysisRun.started_at.desc())
    )
    run = result.scalars().first()
    
    if not run or run.status != "COMPLETED":
        raise HTTPException(status_code=404, detail="Completed analysis not found")
        
    doc_result = await db.execute(select(Document).where(Document.claim_id == claim_id))
    documents = doc_result.scalars().all()
    
    from ..schemas.hospital_bill import HospitalBill
    from ..schemas.insurance_policy import InsurancePolicy
    from ..schemas.rejection_letter import RejectionLetter
    from ..schemas.analysis_result import AnalysisResult
    
    bill, policy, rejection = None, None, None
    for doc in documents:
        if doc.document_type == 'HOSPITAL_BILL' and doc.extracted_data:
            bill = HospitalBill(**doc.extracted_data)
        elif doc.document_type == 'INSURANCE_POLICY' and doc.extracted_data:
            policy = InsurancePolicy(**doc.extracted_data)
        elif doc.document_type == 'REJECTION_LETTER' and doc.extracted_data:
            rejection = RejectionLetter(**doc.extracted_data)
            
    # Allow extra fields just in case
    run_res_data = run.result_data or {}
    analysis_res = AnalysisResult.model_validate(run_res_data) if hasattr(AnalysisResult, 'model_validate') else AnalysisResult(**run_res_data)
    
    from ..reports.generator import ReportGenerator
    generator = ReportGenerator()
    appeal_text = generator.generate_appeal_letter(analysis_res, bill, policy, rejection)
    
    return {
        "appeal_text": appeal_text,
        "regulatory_citations": run_res_data.get('regulatory_citations', []),
        "monetary_impact": run.total_monetary_impact
    }

@router.get('/reports/{claim_id}/audit-trail')
async def get_audit_trail(claim_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    # Use AuditTrail to get history and verify chain
    is_verified = await AuditTrail.verify_chain(db, claim_id)
    history = await AuditTrail.get_audit_history(db, claim_id)
    
    return {
        "claim_id": claim_id,
        "verified": is_verified,
        "audit_logs": history
    }
