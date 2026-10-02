import asyncio
import sys
from types import ModuleType

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import database as database_module
from app.api import analysis as analysis_module
from app.database import Base
from app.models.claim import AnalysisRun, Claim, Document, EvidenceLedgerRecord, RuleVerdictRecord
from app.database import get_db
from app.security.auth import require_staff_access


@pytest.mark.asyncio
async def test_restart_recovery_clears_partial_result_before_requeue(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery.db'}")
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA foreign_keys=ON"))
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(database_module, "engine", engine)

    async with sessions() as db:
        claim = Claim(id="interrupted-claim", patient_name="Patient", status="ANALYZING")
        run = AnalysisRun(
            id="interrupted-run", claim_id=claim.id, status="RUNNING",
            result_data={"overall_status": "MISMATCH_DETECTED", "total_monetary_impact": 500},
            overall_status="MISMATCH_DETECTED", total_monetary_impact=500,
        )
        db.add_all([claim, run])
        db.add(RuleVerdictRecord(
            id="partial-verdict", analysis_run_id=run.id, rule_name="partial",
            status="FAIL", confidence=1, finding="partial result", monetary_impact=500,
        ))
        db.add(EvidenceLedgerRecord(
            id="partial-evidence", claim_id=claim.id, analysis_run_id=run.id,
            rule_verdict_id="partial-verdict", document_hash="a" * 64,
            page_number=1, source_text="partial evidence", confidence=1,
        ))
        await db.commit()

    async def no_op_pipeline(*_args):
        return None

    monkeypatch.setattr(analysis_module, "run_analysis_pipeline", no_op_pipeline)
    await analysis_module.resume_analysis_jobs()
    await asyncio.sleep(0)

    async with sessions() as db:
        run = await db.get(AnalysisRun, "interrupted-run")
        claim = await db.get(Claim, "interrupted-claim")
        verdicts = (await db.execute(select(RuleVerdictRecord))).scalars().all()
        evidence = (await db.execute(select(EvidenceLedgerRecord))).scalars().all()
        assert run.status == "PENDING"
        assert run.result_data is None
        assert run.overall_status is None
        assert run.total_monetary_impact is None
        assert verdicts == []
        assert evidence == []
        assert claim.status == "QUEUED"

    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_workers_claim_one_run_and_write_verdicts_once(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'concurrent.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(analysis_module, "_broadcast_claim_status", lambda *_args: asyncio.sleep(0))
    monkeypatch.setattr(analysis_module, "ExtractionPipeline", lambda **_kwargs: object())

    class Forensics:
        def run(self, *_args, **_kwargs):
            return SimpleForensicsResult()

    class SimpleForensicsResult:
        def model_dump(self, **_kwargs):
            return {}

    fake_forensics_module = ModuleType("app.forensics.engine")
    fake_forensics_module.ForensicsEngine = Forensics
    monkeypatch.setitem(sys.modules, "app.forensics.engine", fake_forensics_module)

    async with sessions() as db:
        db.add(Claim(id="shared-claim", patient_name="Patient", status="QUEUED"))
        db.add(AnalysisRun(id="shared-run", claim_id="shared-claim", status="PENDING"))
        await db.commit()

    await asyncio.gather(
        analysis_module.run_analysis_pipeline("shared-claim", "shared-run"),
        analysis_module.run_analysis_pipeline("shared-claim", "shared-run"),
    )

    async with sessions() as db:
        run = await db.get(AnalysisRun, "shared-run")
        verdicts = (await db.execute(select(RuleVerdictRecord).where(RuleVerdictRecord.analysis_run_id == run.id))).scalars().all()
        assert run.status == "COMPLETED"
        assert run.overall_status == "EXTRACTION_FAILED"
        assert run.total_monetary_impact is None
        assert len(verdicts) == 3

    await engine.dispose()


@pytest.mark.asyncio
async def test_provider_failure_marks_job_failed_without_financial_result(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'provider-failure.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(analysis_module, "_broadcast_claim_status", lambda *_args: asyncio.sleep(0))

    class ProviderUnavailable:
        def __init__(self, **_kwargs):
            pass

        def process_document(self, *_args):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(analysis_module, "ExtractionPipeline", ProviderUnavailable)
    async with sessions() as db:
        claim = Claim(id="provider-claim", patient_name="Patient", status="QUEUED")
        db.add_all([
            claim,
            AnalysisRun(id="provider-run", claim_id=claim.id, status="PENDING"),
            Document(
                id="provider-document", claim_id=claim.id, document_type="HOSPITAL_BILL",
                filename="bill.pdf", file_path="/missing/bill.pdf", content_type="application/pdf",
                file_size_bytes=10,
            ),
        ])
        await db.commit()

    await analysis_module.run_analysis_pipeline("provider-claim", "provider-run")

    async with sessions() as db:
        run = await db.get(AnalysisRun, "provider-run")
        claim = await db.get(Claim, "provider-claim")
        assert run.status == "FAILED"
        assert run.result_data is None
        assert run.total_monetary_impact is None
        assert claim.status == "FAILED"

    await engine.dispose()


@pytest.mark.asyncio
async def test_transient_result_commit_failure_rolls_back_and_marks_job_failed(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'db-commit-failure.db'}")

    class FailFinalCommitSession(AsyncSession):
        def __init__(self, *args, **kwargs):
            self.commit_count = 0
            super().__init__(*args, **kwargs)

        async def commit(self):
            self.commit_count += 1
            if self.commit_count == 2:
                raise RuntimeError("injected transient result commit failure")
            await super().commit()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=FailFinalCommitSession, expire_on_commit=False)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(analysis_module, "_broadcast_claim_status", lambda *_args: asyncio.sleep(0))
    monkeypatch.setattr(analysis_module, "ExtractionPipeline", lambda **_kwargs: object())

    class ForensicsResult:
        def model_dump(self, **_kwargs):
            return {}

    class Forensics:
        def run(self, *_args, **_kwargs):
            return ForensicsResult()

    fake_forensics_module = ModuleType("app.forensics.engine")
    fake_forensics_module.ForensicsEngine = Forensics
    monkeypatch.setitem(sys.modules, "app.forensics.engine", fake_forensics_module)

    async with sessions() as db:
        claim = Claim(id="db-failure-claim", patient_name="Patient", status="QUEUED")
        db.add_all([claim, AnalysisRun(id="db-failure-run", claim_id=claim.id, status="PENDING")])
        await db.commit()

    await analysis_module.run_analysis_pipeline("db-failure-claim", "db-failure-run")

    async with sessions() as db:
        run = await db.get(AnalysisRun, "db-failure-run")
        claim = await db.get(Claim, "db-failure-claim")
        verdicts = (await db.execute(select(RuleVerdictRecord))).scalars().all()
        assert run.status == "FAILED"
        assert run.result_data is None
        assert run.total_monetary_impact is None
        assert claim.status == "FAILED"
        assert verdicts == []

    await engine.dispose()


def test_staff_analysis_trigger_uses_same_global_queue_cap(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from types import SimpleNamespace

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'staff-cap.db'}")
    async def initialize():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    asyncio.run(initialize())
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with sessions() as session:
            yield session

    monkeypatch.setattr(analysis_module, "settings", SimpleNamespace(MAX_PENDING_ANALYSIS_JOBS=1))
    app = FastAPI()
    app.include_router(analysis_module.router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_staff_access] = lambda: None

    async def seed():
        async with sessions() as db:
            occupied = Claim(id="occupied-claim", patient_name="One", status="QUEUED")
            target = Claim(id="target-claim", patient_name="Two", status="PENDING")
            db.add_all([occupied, target])
            db.add_all([
                AnalysisRun(id="occupied-run", claim_id=occupied.id, status="PENDING"),
                Document(
                    id="target-document", claim_id=target.id, document_type="HOSPITAL_BILL",
                    filename="bill.pdf", file_path="/tmp/bill.pdf", content_type="application/pdf",
                    file_size_bytes=10,
                ),
            ])
            await db.commit()
    asyncio.run(seed())

    with TestClient(app) as client:
        response = client.post("/api/analyze/target-claim")

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"

    async def verify_no_new_run():
        async with sessions() as db:
            runs = (await db.execute(select(AnalysisRun))).scalars().all()
            assert [run.id for run in runs] == ["occupied-run"]
    asyncio.run(verify_no_new_run())
    asyncio.run(engine.dispose())
