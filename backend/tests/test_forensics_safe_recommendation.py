from app.forensics.engine import ForensicsEngine
from app.schemas.forensics_result import MetadataFlag


def test_high_anomaly_signals_route_to_human_review_without_fraud_verdict(monkeypatch, tmp_path):
    engine = ForensicsEngine()
    document_path = tmp_path / "document.txt"
    document_path.write_text("test document", encoding="utf-8")
    monkeypatch.setattr(engine.metadata_checker, "analyze", lambda _path: [MetadataFlag(
        flag_type="METADATA_CHANGE",
        field_name="Producer",
        actual_value="Unknown",
        severity="HIGH",
        description="The PDF metadata is incomplete.",
    )])

    result = engine.run_all_checks(str(document_path), bill=None)

    assert result.overall_risk == "HIGH"
    assert "human verification" in result.recommendation.lower()
    assert "reject" not in result.recommendation.lower()
    assert "fraud" not in result.recommendation.lower()
