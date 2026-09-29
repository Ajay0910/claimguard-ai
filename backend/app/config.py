from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./claimguard.db"
    SECRET_KEY: str = "default_unsafe_secret_key_for_dev_only"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    VLM_PROVIDER: str = "anthropic"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    DEBUG: bool = False
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
