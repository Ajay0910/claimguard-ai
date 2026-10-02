import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import database as database_module
from app.api import analysis as analysis_module
from app.database import Base
from app.models.claim import AnalysisRun, Claim, Document


@pytest.mark.asyncio
async def test_incomplete_extraction_bypasses_rules_and_preserves_failure_result(monkeypatch, tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'analysis.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    claim_id = "claim-incomplete-extraction"
    run_id = "run-incomplete-extraction"
    async with sessions() as db:
        db.add(Claim(id=claim_id, patient_name="Test Patient", status="ANALYZING"))
        db.add(AnalysisRun(id=run_id, claim_id=claim_id, status="PENDING"))
        for kind in ("HOSPITAL_BILL", "INSURANCE_POLICY", "REJECTION_LETTER"):
            db.add(Document(
                id=f"doc-{kind}",
                claim_id=claim_id,
                document_type=kind,
                filename=f"{kind}.pdf",
                file_path=str(tmp_path / f"{kind}.pdf"),
                content_type="application/pdf",
                file_size_bytes=1,
                document_hash="a" * 64,
            ))
        await db.commit()

    class FailedExtraction:
        def __init__(self, **_kwargs):
            pass

        def process_document(self, _path, _document_type):
            return {
                "source": "none",
                "data": None,
                "status": "INSUFFICIENT_EVIDENCE",
                "issues": ["NO_STRUCTURED_EXTRACTION"],
            }

    rule_engine_called = False

    class RuleEngineMustNotRun:
        def __init__(self):
            pass

        def run_all_rules(self, **_kwargs):
            nonlocal rule_engine_called
            rule_engine_called = True
            raise AssertionError("financial rules ran without extracted documents")

    monkeypatch.setattr(database_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(analysis_module, "ExtractionPipeline", FailedExtraction)
    monkeypatch.setattr(analysis_module, "RuleEngine", RuleEngineMustNotRun)

    await analysis_module.run_analysis_pipeline(claim_id, run_id)

    async with sessions() as db:
        run = await db.get(AnalysisRun, run_id)
        claim = await db.get(Claim, claim_id)

    assert rule_engine_called is False
    assert run.overall_status == "EXTRACTION_FAILED"
    assert run.result_data["overall_status"] == "EXTRACTION_FAILED"
    assert run.result_data["total_monetary_impact"] is None
    assert run.result_data["expected_admissible_amount"] is None
    assert claim.status == "REVIEW_RECOMMENDED"

    await engine.dispose()
