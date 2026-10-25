from collections import defaultdict, deque
import asyncio
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class PortalSubmissionRateLimitMiddleware(BaseHTTPMiddleware):
    """Process-local guardrail; the upstream edge must also enforce global limits."""

    def __init__(self, app, limit: int | None = None, window_seconds: int = 900):
        super().__init__(app)
        from ..config import settings
        default_limit = getattr(settings, "PORTAL_RATE_LIMIT", 100)
        self.limit = limit if limit is not None else default_limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/api/portal/submit":
            client = request.client.host if request.client else "unknown"
            now = time.monotonic()
            async with self.lock:
                if len(self.requests) > 10_000:
                    expired_clients = [
                        key for key, timestamps in self.requests.items()
                        if not timestamps or now - timestamps[-1] >= self.window_seconds
                    ]
                    for key in expired_clients:
                        self.requests.pop(key, None)
                    if len(self.requests) > 10_000:
                        oldest = sorted(self.requests, key=lambda key: self.requests[key][-1] if self.requests[key] else 0)
                        for key in oldest[: len(self.requests) - 8_000]:
                            self.requests.pop(key, None)
                recent = self.requests[client]
                while recent and now - recent[0] >= self.window_seconds:
                    recent.popleft()
                if len(recent) >= self.limit:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many submissions. Please try again later."},
                        headers={"Retry-After": str(max(1, int(self.window_seconds - (now - recent[0]))))},
                    )
                recent.append(now)
        return await call_next(request)
