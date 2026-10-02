"""Process-local admission serialization for the single-instance API service."""
import asyncio
from functools import wraps
import weakref

from fastapi import HTTPException
from sqlalchemy import func, select

from ..models.claim import AnalysisRun
from ..config import settings


_admission_lock = asyncio.Lock()
_worker_semaphores = weakref.WeakKeyDictionary()


def serialize_analysis_admission(endpoint):
    """Prevent concurrent requests from oversubscribing the durable job cap."""
    @wraps(endpoint)
    async def wrapped(*args, **kwargs):
        async with _admission_lock:
            return await endpoint(*args, **kwargs)
    return wrapped


def limit_analysis_workers(endpoint):
    """Keep provider work within the configured worker cap, including recovery."""
    @wraps(endpoint)
    async def wrapped(*args, **kwargs):
        loop = asyncio.get_running_loop()
        limit = max(1, int(settings.MAX_PENDING_ANALYSIS_JOBS))
        per_loop = _worker_semaphores.setdefault(loop, {})
        semaphore = per_loop.setdefault(limit, asyncio.Semaphore(limit))
        async with semaphore:
            return await endpoint(*args, **kwargs)
    return wrapped


async def ensure_analysis_capacity(db, settings) -> None:
    maximum = max(1, int(settings.MAX_PENDING_ANALYSIS_JOBS))
    result = await db.execute(
        select(func.count(AnalysisRun.id)).where(AnalysisRun.status.in_(["PENDING", "RUNNING"]))
    )
    if (result.scalar() or 0) >= maximum:
        raise HTTPException(
            status_code=503,
            detail="Analysis capacity is full. Please retry shortly.",
            headers={"Retry-After": "30"},
        )
