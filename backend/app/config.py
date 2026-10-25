from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urlparse

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./claimguard.db"
    SECRET_KEY: str = "default_unsafe_secret_key_for_dev_only"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    VLM_PROVIDER: str = "anthropic"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_SUBMISSION_SIZE_MB: int = 50
    MAX_PENDING_ANALYSIS_JOBS: int = 50
    MAX_ANALYSIS_WORKERS: int = 4
    PORTAL_RATE_LIMIT: int = 100
    MAX_DOCUMENT_PAGES: int = 30
    MAX_DOCUMENT_TOTAL_PIXELS: int = 40_000_000
    DEBUG: bool = False
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:4173,http://localhost:5174"
    STAFF_PROXY_SHARED_SECRET: Optional[str] = None
    STAFF_REQUIRED_GROUP: str = "claimguard-staff"
    STAFF_AUTH_DISABLED: bool = False
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()


def validate_production_settings(config: Settings = settings) -> None:
    """Reject production configurations that would bypass required controls."""
    if config.APP_ENV.strip().lower() != "production":
        return

    errors = []
    if config.DEBUG:
        errors.append("DEBUG must be false in production")
    if config.STAFF_AUTH_DISABLED:
        errors.append("STAFF_AUTH_DISABLED must be false in production")
    if not config.STAFF_PROXY_SHARED_SECRET or len(config.STAFF_PROXY_SHARED_SECRET) < 32:
        errors.append("STAFF_PROXY_SHARED_SECRET must contain at least 32 characters")
    if config.SECRET_KEY == "default_unsafe_secret_key_for_dev_only" or len(config.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be replaced with a random value of at least 32 characters")
    if config.DATABASE_URL.startswith("sqlite"):
        errors.append("DATABASE_URL must use a persistent production database")
    origins = [origin.strip() for origin in config.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
    if not origins or "*" in origins:
        errors.append("CORS_ALLOWED_ORIGINS must list one or more explicit origins")
    if any(urlparse(origin).scheme != "https" or not urlparse(origin).netloc for origin in origins):
        errors.append("CORS_ALLOWED_ORIGINS must contain only explicit HTTPS origins in production")
    if any(urlparse(origin).path not in ("", "/") or urlparse(origin).query or urlparse(origin).fragment for origin in origins):
        errors.append("CORS_ALLOWED_ORIGINS entries must be origins without paths or query strings")
    if not config.UPLOAD_DIR.startswith("/var/data/"):
        errors.append("UPLOAD_DIR must point to the persistent Render disk mounted under /var/data")
    if config.MAX_UPLOAD_SIZE_MB < 1 or config.MAX_SUBMISSION_SIZE_MB < 1 or config.MAX_PENDING_ANALYSIS_JOBS < 1 or not 1 <= config.MAX_DOCUMENT_PAGES <= 100:
        errors.append("Upload and document page limits must be set within supported production bounds")
    if not 1_000_000 <= config.MAX_DOCUMENT_TOTAL_PIXELS <= 200_000_000:
        errors.append("MAX_DOCUMENT_TOTAL_PIXELS must be between 1,000,000 and 200,000,000")
    provider = config.VLM_PROVIDER.strip().lower()
    key = {
        "openai": config.OPENAI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "gemini": config.GEMINI_API_KEY,
    }.get(provider)
    if not key or any(marker in key.strip().lower() for marker in ("replace-with", "your-api-key", "changeme", "placeholder")):
        errors.append(f"A valid API key must be configured for VLM_PROVIDER={provider}")

    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


def get_cors_origins(config: Settings = settings) -> list[str]:
    """Return configured origins without whitespace or wildcard fallback."""
    origins = [origin.strip().rstrip("/") for origin in config.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS must list one or more explicit origins")
    return origins
