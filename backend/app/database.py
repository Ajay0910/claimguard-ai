from sqlalchemy import event, text
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

connect_args = {}
pool_kwargs = {}
if "sqlite" in ASYNC_DATABASE_URL:
    connect_args["timeout"] = 60.0
    connect_args["check_same_thread"] = False
    if ":memory:" not in ASYNC_DATABASE_URL:
        from sqlalchemy.pool import AsyncAdaptedQueuePool
        pool_kwargs["poolclass"] = AsyncAdaptedQueuePool
        pool_kwargs["pool_size"] = 25
        pool_kwargs["max_overflow"] = 25
        pool_kwargs["pool_timeout"] = 60.0

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
    **pool_kwargs,
)

if "sqlite" in ASYNC_DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def init_db():
    import app.models.claim
    async with engine.begin() as conn:
        if "sqlite" in ASYNC_DATABASE_URL:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
            await conn.execute(text("PRAGMA busy_timeout=60000"))
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.execute(text("PRAGMA cache_size=-64000"))
        # Removed create_all to stop wiping/relying on auto-create. Use Alembic instead.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
