"""Process-local admission serialization for the single-instance API service."""
import asyncio
from functools import wraps
import weakref

from fastapi import HTTPException
from sqlalchemy import func, select

from ..models.claim import AnalysisRun
from ..config import settings


_admission_locks = weakref.WeakKeyDictionary()
_worker_semaphores = weakref.WeakKeyDictionary()


def get_admission_lock() -> asyncio.Lock:
    """Return the admission lock for the current running loop."""
    loop = asyncio.get_running_loop()
    return _admission_locks.setdefault(loop, asyncio.Lock())


def serialize_analysis_admission(endpoint):
    """Prevent concurrent requests from oversubscribing the durable job cap."""
    @wraps(endpoint)
    async def wrapped(*args, **kwargs):
        async with get_admission_lock():
            return await endpoint(*args, **kwargs)
    return wrapped


def limit_analysis_workers(endpoint):
    """Keep provider work within the configured worker cap, including recovery."""
    @wraps(endpoint)
    async def wrapped(*args, **kwargs):
        loop = asyncio.get_running_loop()
        worker_cap = getattr(settings, "MAX_ANALYSIS_WORKERS", None)
        if worker_cap is None:
            worker_cap = getattr(settings, "MAX_PENDING_ANALYSIS_JOBS", 4)
        limit = max(1, int(worker_cap))
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
