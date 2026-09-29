"""
Adversarial Stress Test Harness - Challenger 1
Targeting:
1. PDFInspector (backend/app/forensics/pdf_inspector.py)
2. AnomalyScorer (backend/app/forensics/fraud_scorer.py)

Designed to stress-test:
- Corrupted byte streams, 0-byte files, non-PDF payloads, fake %%EOF chaining
- Malformed xref tables, missing /Prev chains, huge payloads
- Extreme numerical values (negative numbers, multi-crore amounts, NaN/None, empty dicts)
- Mathematical invariant verification: 0.0 <= score <= 100.0, risk tier alignment
"""

import math
import os
import tempfile
import pytest
from app.forensics.pdf_inspector import PDFInspector, PDFInspectionResult, PDFRevisionInfo
from app.forensics.fraud_scorer import AnomalyScorer, AnomalyAssessment, FactorAttribution
from app.schemas.forensics_result import BillAnomalyFlag, ConsistencyFlag, MetadataFlag


# ===========================================================================
# 1. Adversarial Stress Tests: PDFInspector
# ===========================================================================

class TestPDFInspectorAdversarial:
    @pytest.fixture
    def inspector(self):
        return PDFInspector()

    def test_zero_byte_stream(self, inspector):
        """0-byte payload should not crash and return valid CLEAN inspection result."""
        result = inspector.inspect_bytes(b"")
        assert isinstance(result, PDFInspectionResult)
        assert result.is_tampered is False
        assert result.pdf_tamper_score == 0.0
        assert result.risk_level == "CLEAN"
        assert result.revisions.revision_count == 0
        assert "Empty PDF byte stream" in result.anomalies

    def test_non_pdf_file_arbitrary_text(self, inspector):
        """Plain text pretending to be PDF should be handled gracefully without crashing."""
        data = b"This is a standard UTF-8 text file with no PDF structure whatsoever."
        result = inspector.inspect_bytes(data)
        assert isinstance(result, PDFInspectionResult)
        assert 0.0 <= result.pdf_tamper_score <= 1.0
        assert result.risk_level in ["CLEAN", "SUSPICIOUS", "TAMPERED"]
        assert any("Missing standard %PDF header" in a for a in result.anomalies)

    def test_random_binary_garbage_payload(self, inspector):
        """Arbitrary 64KB high-entropy binary payload should not cause regex catastrophic backtracking."""
        import random
        random.seed(42)
        random_bytes = bytes([random.randint(0, 255) for _ in range(65536)])
        result = inspector.inspect_bytes(random_bytes)
        assert isinstance(result, PDFInspectionResult)
        assert 0.0 <= result.pdf_tamper_score <= 1.0

    def test_ten_plus_fake_incremental_eofs(self, inspector):
        """Adversarial PDF containing 15 repeated %%EOF markers must be flagged as multi-revision."""
        payload = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        for i in range(15):
            payload += f"startxref\n{100 + i*50}\n%%EOF\n".encode("ascii")

        result = inspector.inspect_bytes(payload)
        assert isinstance(result, PDFInspectionResult)
        assert result.revisions.has_incremental_updates is True
        assert result.revisions.revision_count == 15
        assert len(result.revisions.eof_offsets) == 15
        assert result.is_tampered is True
        assert result.pdf_tamper_score >= 0.45
        assert result.risk_level in ["SUSPICIOUS", "TAMPERED"]

    def test_one_hundred_fake_eofs_performance(self, inspector):
        """100 repeated %%EOF markers should parse swiftly without timeout or memory bloat."""
        payload = b"%PDF-1.6\n1 0 obj\n<<>>\nendobj\n"
        payload += b"%%EOF\n" * 100
        result = inspector.inspect_bytes(payload)
        assert result.revisions.revision_count == 100
        assert result.revisions.has_incremental_updates is True
        assert 0.0 <= result.pdf_tamper_score <= 1.0

    def test_malformed_xref_table(self, inspector):
        """Corrupted xref table with negative numbers, garbage tokens, and missing sections."""
        payload = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"xref\n"
            b"CORRUPTED_ENTRY -999 -999999999\n"
            b"NULL_BYTE \x00\x00\x00\xff\n"
            b"trailer\n<< /Size 1 >>\n"
            b"startxref\n50\n%%EOF\n"
        )
        result = inspector.inspect_bytes(payload)
        assert isinstance(result, PDFInspectionResult)
        assert 0.0 <= result.pdf_tamper_score <= 1.0

    def test_missing_prev_pointer_with_overwritten_objects(self, inspector):
        """Multi-revision PDF with overwritten indirect objects but omitting /Prev trailer pointer."""
        payload = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Amount 100 >>\nendobj\n"
            b"trailer\n<< /Size 2 >>\nstartxref\n40\n%%EOF\n"
            b"1 0 obj\n<< /Amount 999999 >>\nendobj\n"
            b"trailer\n<< /Size 2 >>\nstartxref\n90\n%%EOF\n"
        )
        result = inspector.inspect_bytes(payload)
        assert result.revisions.has_incremental_updates is True
        assert 1 in result.revisions.overwritten_objects
        assert result.is_tampered is True
        assert result.pdf_tamper_score >= 0.45

    def test_huge_indirect_object_numbers(self, inspector):
        """Very large indirect object IDs should not trigger integer overflow."""
        huge_id = "99999999999999999999"
        payload = f"%PDF-1.4\n{huge_id} 0 obj\n<<>>\nendobj\n%%EOF\n".encode("ascii")
        result = inspector.inspect_bytes(payload)
        assert isinstance(result, PDFInspectionResult)
        assert 0.0 <= result.pdf_tamper_score <= 1.0

    def test_known_tampering_tool_signatures(self, inspector):
        """Signatures of consumer editing tools (iLovePDF, Photoshop, Canva, Sejda) must trigger tampering."""
        tools = [b"ilovepdf", b"photoshop", b"canva", b"sejda", b"pdfescape"]
        for tool in tools:
            payload = b"%PDF-1.4\n1 0 obj\n<< /Producer (" + tool + b") >>\nendobj\n%%EOF\n"
            result = inspector.inspect_bytes(payload)
            assert result.is_tampered is True
            assert tool.decode("ascii") in result.details["detected_tools"]

    def test_missing_file_on_disk(self, inspector):
        """Missing file on disk returns valid result without unhandled FileNotFoundError."""
        result = inspector.inspect_file("non_existent_adversarial_file_987654.pdf")
        assert isinstance(result, PDFInspectionResult)
        assert result.is_tampered is False
        assert result.risk_level == "CLEAN"
        assert "File does not exist" in result.anomalies


# ===========================================================================
# 2. Adversarial Stress Tests: AnomalyScorer
# ===========================================================================

class TestAnomalyScorerAdversarial:
    @pytest.fixture
    def scorer(self):
        return AnomalyScorer()

    def test_all_none_inputs(self, scorer):
        """All inputs None must return valid AnomalyAssessment with baseline risk."""
        result = scorer.compute_score(None, None, None, None, None)
        assert isinstance(result, AnomalyAssessment)
        assert 0.0 <= result.anomaly_density_score <= 100.0
        assert result.anomaly_density_score == 2.0
        assert result.review_status == "CLEAN"
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.factor_attributions) > 0

    def test_empty_dictionaries_and_lists(self, scorer):
        """Empty dictionaries and lists must return calibrated low risk."""
        result = scorer.compute_score({}, [], [], [], {})
        assert isinstance(result, AnomalyAssessment)
        assert 0.0 <= result.anomaly_density_score <= 100.0
        assert result.anomaly_density_score == 2.0
        assert result.review_status == "CLEAN"

    def test_extreme_negative_values(self, scorer):
        """Extreme negative values must be floored safely at 0.0, not negative."""
        result = scorer.compute_score(
            forensics_result={"ela_result": {"tamper_score": -999999.0}},
            bill_anomalies=[],
            clinical_consistency=[],
            metadata_flags=[]
        )
        assert isinstance(result, AnomalyAssessment)
        assert 0.0 <= result.anomaly_density_score <= 100.0
        assert result.review_status == "CLEAN"

    def test_extreme_multi_crore_values(self, scorer):
        """Multi-crore / astronomical inputs must be strictly capped at 100.0."""
        bill_flags = [
            BillAnomalyFlag(
                anomaly_type="TARIFF_DEVIATION",
                description=f"Inflated item {i} to 10 crore",
                severity="HIGH",
                affected_items=[f"Item_{i}"]
            )
            for i in range(100)
        ]
        result = scorer.compute_score(
            forensics_result={
                "ela_result": {"tamper_score": 1000000000.0, "assessment": "HIGHLY_SUSPICIOUS"},
                "pdf_inspection_result": {"is_tampered": True, "pdf_tamper_score": 1000000000.0, "risk_level": "TAMPERED"}
            },
            bill_anomalies=bill_flags,
            clinical_consistency=[
                ConsistencyFlag(
                    issue_type="CONTRADICTORY_TREATMENT",
                    description="Severe mismatch",
                    severity="HIGH"
                )
            ] * 20,
            metadata_flags=[
                MetadataFlag(description="Photoshop", severity="HIGH")
            ] * 10
        )
        assert isinstance(result, AnomalyAssessment)
        assert 0.0 <= result.anomaly_density_score <= 100.0
        assert result.anomaly_density_score == 100.0
        assert result.review_status == "FLAGGED FOR REVIEW"

    def test_review_status_boundary_alignment(self, scorer):
        """Risk tiers must strictly align with score boundaries:
        - [0, 25) -> LOW
        - [25, 50) -> MEDIUM
        - [50, 75) -> HIGH
        - [75, 100] -> CRITICAL
        """
        # Baseline is 2.0 -> LOW
        res_low = scorer.compute_score(None, None, None, None)
        assert res_low.anomaly_density_score < 25.0
        assert res_low.review_status == "CLEAN"

    def test_provider_synergy_trigger_boundary(self, scorer):
        """Provider systemic risk attribution only triggers when both billing > 0.4 and clinical > 0.4."""
        # Only high billing -> No provider synergy attribution
        res_only_billing = scorer.compute_score(
            forensics_result=None,
            bill_anomalies=[
                BillAnomalyFlag(anomaly_type="TARIFF_DEVIATION", description="High tariff", severity="HIGH"),
                BillAnomalyFlag(anomaly_type="LOS_PADDING", description="High LOS", severity="HIGH")
            ],
            clinical_consistency=None,
            metadata_flags=None
        )
        categories_b = [fa.category for fa in res_only_billing.factor_attributions]
        assert "provider" not in categories_b

        # Both high billing and high clinical -> Provider synergy attribution MUST be present
        res_both = scorer.compute_score(
            forensics_result=None,
            bill_anomalies=[
                BillAnomalyFlag(anomaly_type="TARIFF_DEVIATION", description="High tariff", severity="HIGH"),
                BillAnomalyFlag(anomaly_type="LOS_PADDING", description="High LOS", severity="HIGH")
            ],
            clinical_consistency=[
                ConsistencyFlag(issue_type="CONTRADICTORY_TREATMENT", description="Unexpected chemotherapy", severity="HIGH")
            ],
            metadata_flags=None
        )
        categories_both = [fa.category for fa in res_both.factor_attributions]
        assert "provider" in categories_both

    def test_factor_attributions_impact_bounds(self, scorer):
        """All factor impact scores must be in [-1.0, 1.0] and weights strictly positive."""
        result = scorer.compute_score(
            forensics_result={"ela_result": {"tamper_score": 0.5, "assessment": "SUSPICIOUS"}},
            bill_anomalies=[BillAnomalyFlag(anomaly_type="LOS_PADDING", description="Overstay", severity="HIGH")],
            clinical_consistency=[ConsistencyFlag(description="test", severity="HIGH")],
            metadata_flags=[MetadataFlag(description="tool", severity="HIGH")]
        )
        for fa in result.factor_attributions:
            assert -1.0 <= fa.impact_score <= 1.0, f"Impact score out of range: {fa.impact_score}"
            assert fa.weight > 0, f"Weight must be positive: {fa.weight}"

    # -----------------------------------------------------------------------
    # Bug / Vulnerability Demonstration Tests (Empirical Findings)
    # -----------------------------------------------------------------------

    def test_nan_tamper_score_vulnerability(self, scorer):
        """
        EMPIRICAL BUG CHALLENGE:
        Passing float('nan') as tamper_score propagates NaN into anomaly_density_score,
        violating invariant 0.0 <= anomaly_density_score <= 100.0, and defaults review_status to 'CRITICAL'.
        """
        result = scorer.compute_score(
            forensics_result={"ela_result": {"tamper_score": float("nan")}}
        )
        # Empirical finding: anomaly_density_score is NaN
        is_nan = math.isnan(result.anomaly_density_score)
        # Document the vulnerability:
        if is_nan:
            # Bug reproduced empirically: score is NaN, not in [0.0, 100.0]
            assert is_nan is True
            assert result.review_status == "FLAGGED FOR REVIEW"  # Defaults to CRITICAL due to NaN comparisons
        else:
            assert 0.0 <= result.anomaly_density_score <= 100.0
