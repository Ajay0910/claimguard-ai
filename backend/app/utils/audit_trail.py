import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from ..models.claim import AuditLog

class AuditTrail:
    @staticmethod
    async def log(db: AsyncSession, claim_id: str, action: str, details: dict, actor: str = 'system'):
        # 1. Get the last audit entry's hash
        stmt = select(AuditLog).where(AuditLog.claim_id == claim_id).order_by(desc(AuditLog.id)).limit(1)
        result = await db.execute(stmt)
        last_log = result.scalar_one_or_none()
        
        previous_hash = last_log.entry_hash if last_log else None
        
        # 2. Compute new hash
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{previous_hash or ''}{action}{json.dumps(details, sort_keys=True)}{timestamp}"
        entry_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # 3. Create AuditLog entry
        new_log = AuditLog(
            claim_id=claim_id,
            action=action,
            actor=actor,
            details=details,
            previous_hash=previous_hash,
            entry_hash=entry_hash
        )
        
        # 4. Add and flush
        db.add(new_log)
        await db.flush()
    
    @staticmethod
    async def verify_chain(db: AsyncSession, claim_id: str) -> bool:
        stmt = select(AuditLog).where(AuditLog.claim_id == claim_id).order_by(AuditLog.id)
        result = await db.execute(stmt)
        logs = result.scalars().all()

        if not logs:
            return False
        
        expected_prev_hash = None
        for log in logs:
            if log.previous_hash != expected_prev_hash:
                return False
            expected_prev_hash = log.entry_hash
            
        return True
    
    @staticmethod
    async def get_audit_history(db: AsyncSession, claim_id: str) -> list[dict]:
        stmt = select(AuditLog).where(AuditLog.claim_id == claim_id).order_by(desc(AuditLog.id))
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "claim_id": log.claim_id,
                "action": log.action,
                "actor": log.actor,
                "details": log.details,
                "previous_hash": log.previous_hash,
                "entry_hash": log.entry_hash,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
