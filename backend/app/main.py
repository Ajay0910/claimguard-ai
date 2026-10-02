from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from sqlalchemy import text
from .database import engine
from .database import init_db
from .config import settings, get_cors_origins, validate_production_settings
from .security.rate_limit import PortalSubmissionRateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_production_settings()
    await init_db()
    from .api.analysis import resume_analysis_jobs
    await resume_analysis_jobs()
    yield
    # Shutdown

app = FastAPI(
    title="ClaimGuard AI API",
    lifespan=lifespan,
    docs_url=None if settings.APP_ENV.strip().lower() == "production" else "/docs",
    redoc_url=None if settings.APP_ENV.strip().lower() == "production" else "/redoc",
    openapi_url=None if settings.APP_ENV.strip().lower() == "production" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PortalSubmissionRateLimitMiddleware)

from .api import upload, analysis, reports, portal

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(portal.router)

@app.get("/api/health")
async def health_check():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        if not os.access(settings.UPLOAD_DIR, os.W_OK):
            raise OSError("Upload directory is not writable")
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service is not ready")
    return {"status": "ok", "database": "ok", "storage": "ok"}

@app.get("/")
async def root():
    return {
        "project": "ClaimGuard AI",
        "description": "API for processing and analyzing medical claims.",
        "portal": "/api/portal/submit",
        "docs": "/docs" if settings.APP_ENV.strip().lower() != "production" else None,
    }
