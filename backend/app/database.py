from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Auto-convert postgres:// → postgresql+asyncpg:// for Render compatibility
def _make_async_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

ASYNC_DATABASE_URL = _make_async_url(settings.DATABASE_URL)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def init_db():
    import app.models.claim
    async with engine.begin() as conn:
        from sqlalchemy import text
        if "sqlite" in ASYNC_DATABASE_URL:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
        # Removed create_all to stop wiping/relying on auto-create. Use Alembic instead.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
