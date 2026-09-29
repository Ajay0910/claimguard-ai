import pytest
import os
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command
from app.database import Base
from app.models import claim  # Import models so Base.metadata is populated

ALEMBIC_INI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")

def run_alembic_upgrade(db_path: str):
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(ALEMBIC_INI_PATH), "alembic"))
    url = f"sqlite+aiosqlite:///{db_path}"
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")

@pytest.mark.asyncio
async def test_migration_preserves_data():
    """
    Test that upgrading a database works and we can insert/read data.
    If we simulate an existing DB, we ensure data remains readable.
    """
    db_path = "test_migration_preserves.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    sync_url = f"sqlite:///{db_path}"
    engine = sa.create_engine(sync_url)
    
    # 1. Simulate legacy DB creation via metadata.create_all
    Base.metadata.create_all(engine)
    
    # 2. Insert data into legacy schema
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO claims (id, patient_name, status, portal_token) VALUES (:id, :name, :status, :token)"
        ), {"id": "claim_mig_1", "name": "Test Patient", "status": "PENDING", "token": "token123"})
        
    engine.dispose()
    
    # 3. Run Alembic upgrade head (should be a no-op for creation if tables exist, but might add alembic_version)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    await asyncio.to_thread(run_alembic_upgrade, db_path)
    
    # 4. Verify data survived
    engine = sa.create_engine(sync_url)
    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT id, patient_name FROM claims WHERE id = 'claim_mig_1'")).fetchone()
        assert result is not None
        assert result[0] == "claim_mig_1"
        assert result[1] == "Test Patient"
        
        # Verify alembic_version exists
        alembic_version = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchone()
        assert alembic_version is not None
        
    engine.dispose()
    
    if os.path.exists(db_path):
        os.remove(db_path)
