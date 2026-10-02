import pytest

from app.utils.audit_trail import AuditTrail


@pytest.mark.asyncio
async def test_empty_audit_history_is_not_reported_as_verified(async_test_db):
    assert await AuditTrail.verify_chain(async_test_db, "claim-with-no-events") is False
