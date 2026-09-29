from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import os
from datetime import datetime

from ..database import get_db
from ..models.claim import Claim, Document
from ..utils.file_handler import save_upload
from ..utils.audit_trail import AuditTrail
from ..config import settings

router = APIRouter(prefix='/api', tags=['upload'])

@router.post('/upload')
async def upload_document(
    file: UploadFile,
    document_type: str = Form(...),
    claim_id: Optional[str] = Form(None),
    patient_email: Optional[str] = Form(None),
    patient_phone: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
) -> dict:
    valid_types = ['HOSPITAL_BILL', 'INSURANCE_POLICY', 'REJECTION_LETTER']
    if document_type not in valid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document_type")
        
    valid_mime_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
    if file.content_type not in valid_mime_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    # Simple email and phone validation if provided
    if patient_email and '@' not in patient_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
    if patient_phone and not patient_phone.replace('+', '').isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number format")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 25 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 25MB)")
    
    if not claim_id:
        claim_id = str(uuid.uuid4())
        new_claim = Claim(
            id=claim_id,
            patient_name="Unknown", # Will be extracted later
            patient_email=patient_email,
            patient_phone=patient_phone,
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_claim)
        await db.flush()
    else:
        result = await db.execute(select(Claim).where(Claim.id == claim_id))
        claim = result.scalar_one_or_none()
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    upload_dir = settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else os.path.join("data", "uploads")
    file_path, mime_type, size_bytes, doc_hash = await save_upload(file, upload_dir)

    document_id = str(uuid.uuid4())
    new_doc = Document(
        id=document_id,
        claim_id=claim_id,
        document_type=document_type,
        filename=file.filename or "unknown",
        file_path=file_path,
        content_type=mime_type,
        file_size_bytes=size_bytes,
        document_hash=doc_hash,
        created_at=datetime.utcnow()
    )
    db.add(new_doc)
    
    await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
        "filename": file.filename, 
        "document_type": document_type,
        "document_hash": doc_hash,
        "file_size_bytes": size_bytes
    })
    
    await db.commit()
    
    return {
        "claim_id": claim_id,
        "document_id": document_id,
        "filename": file.filename,
        "document_hash": doc_hash,
        "status": "success"
    }

@router.get('/claims/{claim_id}/documents')
async def list_documents(claim_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Claim not found")

    result = await db.execute(select(Document).where(Document.claim_id == claim_id))
    documents = result.scalars().all()
    
    return [
        {
            "id": doc.id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "document_hash": doc.document_hash,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "extracted_data": doc.extracted_data
        }
        for doc in documents
    ]

@router.get('/claims')
async def list_claims(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Claim))
    claims = result.scalars().all()
    return [
        {
            "id": claim.id,
            "patient_name": claim.patient_name,
            "patient_email": claim.patient_email,
            "patient_phone": claim.patient_phone,
            "policy_number": claim.policy_number,
            "claim_number": claim.claim_number,
            "status": claim.status,
            "updated_at": claim.updated_at.isoformat() if claim.updated_at else None
        }
        for claim in claims
    ]

@router.get('/stats')
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    from sqlalchemy import func
    from ..models.claim import AnalysisRun
    
    result = await db.execute(select(func.count(Claim.id)))
    total_claims = result.scalar() or 0
    
    result = await db.execute(select(func.count(Claim.id)).where(Claim.status.in_(['PENDING', 'ANALYZING'])))
    pending_analysis = result.scalar() or 0
    
    result = await db.execute(select(func.count(AnalysisRun.id)).where(AnalysisRun.overall_status == 'FAIL'))
    mismatches_found = result.scalar() or 0
    
    result = await db.execute(select(func.sum(AnalysisRun.total_monetary_impact)))
    total_recovered_amount = float(result.scalar() or 0.0)
    
    return {
        "total_claims": total_claims,
        "pending_analysis": pending_analysis,
        "mismatches_found": mismatches_found,
        "total_recovered_amount": total_recovered_amount
    }
