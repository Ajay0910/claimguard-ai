"""
Comprehensive Test Suite for the 3 Research-Backed Core Features:
1. Explainable Composite Fraud Risk Scorer (Paper 9: Wang et al., Nature Sci Rep 2025)
2. PDF Multi-Revision & Incremental Update Forensic Inspector (Paper 14: Grobler et al., SAICSIT 2025)
3. Denial Appeal Overturn Predictor & Statutory Ombudsman Risk Engine (Paper 1, 12, 13)
"""

import os
import tempfile
import pytest
from app.forensics.fraud_scorer import AnomalyScorer, AnomalyAssessment, FactorAttribution
from app.forensics.pdf_inspector import PDFInspector, PDFInspectionResult, PDFRevisionInfo
from app.rules.appeal_evaluator import AppealEvaluator, AppealEvaluationResult, check_appeal_viability
from app.forensics.engine import ForensicsEngine
from app.rules.engine import RuleEngine
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.forensics_result import BillAnomalyFlag, ConsistencyFlag, MetadataFlag


# ---------------------------------------------------------------------------
# Feature 1: Explainable Composite Fraud Risk Scorer Tests
# ---------------------------------------------------------------------------

class TestAnomalyScorer:
    @pytest.fixture
    def scorer(self):
        return AnomalyScorer()

    def test_clean_claim_low_fraud_score(self, scorer):
        """Clean bill with no forensic, billing, or clinical flags yields LOW risk."""
        result = scorer.compute_score(
            forensics_result={"ela_result": {"tamper_score": 0.02, "assessment": "CLEAN"}},
            bill_anomalies=[],
            clinical_consistency=[],
            metadata_flags=[]
        )
        assert isinstance(result, AnomalyAssessment)
        assert result.anomaly_density_score < 25.0
        assert result.review_status == "CLEAN"
        assert result.confidence >= 0.90
        assert "CLEAN" in result.summary
        assert len(result.factor_attributions) > 0

    def test_high_fraud_score_multiple_anomalies(self, scorer):
        """High ELA score, tariff inflation, and contradictory medication yield HIGH/CRITICAL risk."""
        forensics_data = {
            "ela_result": {"tamper_score": 0.88, "assessment": "HIGHLY_SUSPICIOUS"},
            "pdf_inspection_result": {"is_tampered": True, "pdf_tamper_score": 0.90, "risk_level": "TAMPERED"}
        }
        bill_anomalies = [
            BillAnomalyFlag(anomaly_type="TARIFF_DEVIATION", description="Surgery >3x CGHS benchmark", severity="HIGH", affected_items=["Surgery"]),
            BillAnomalyFlag(anomaly_type="LOS_PADDING", description="Overstay 10 days vs 2 expected", severity="HIGH", affected_items=[])
        ]
        clinical_flags = [
            ConsistencyFlag(issue_type="CONTRADICTORY_TREATMENT", mismatch_type="DIAGNOSIS_MEDICINE", description="Found unexpected treatment 'chemotherapy' for diagnosis 'cataract'", severity="HIGH")
        ]
        metadata_flags = [
            MetadataFlag(flag_type="SOFTWARE", description="Created with Photoshop CS6", severity="HIGH")
        ]

        result = scorer.compute_score(
            forensics_result=forensics_data,
            bill_anomalies=bill_anomalies,
            clinical_consistency=clinical_flags,
            metadata_flags=metadata_flags
        )

        assert result.anomaly_density_score >= 50.0
        assert result.review_status == "FLAGGED FOR REVIEW"
        assert len(result.top_anomalies) >= 3
        # Ensure factor attributions decompose into all 4 key categories
        categories = {fa.category for fa in result.factor_attributions}
        assert "forensics" in categories
        assert "billing" in categories
        assert "clinical" in categories

    def test_factor_attributions_bounded(self, scorer):
        """Ensure all impact scores are properly bounded in [-1.0, 1.0]."""
        result = scorer.compute_score(
            forensics_result={"ela_result": {"tamper_score": 0.5, "assessment": "SUSPICIOUS"}},
            bill_anomalies=[BillAnomalyFlag(anomaly_type="LOS_PADDING", description="Overstay", severity="MEDIUM")],
            clinical_consistency=[],
            metadata_flags=[]
        )
        for fa in result.factor_attributions:
            assert -1.0 <= fa.impact_score <= 1.0
            assert fa.weight > 0

    def test_empty_inputs_handled_gracefully(self, scorer):
        """Scorer gracefully computes baseline risk on empty/None inputs."""
        result = scorer.compute_score(None, None, None, None)
        assert isinstance(result, AnomalyAssessment)
        assert 0.0 <= result.anomaly_density_score <= 100.0
        assert result.review_status == "CLEAN"


# ---------------------------------------------------------------------------
# Feature 2: PDF Multi-Revision & Incremental Update Forensic Inspector Tests
# ---------------------------------------------------------------------------

class TestPDFInspector:
    @pytest.fixture
    def inspector(self):
        return PDFInspector()

    def test_clean_single_revision_pdf(self, inspector):
        """Synthesized single-revision PDF has 1 %%EOF, 0 overwritten objects, and CLEAN risk."""
        clean_pdf_bytes = (
            b"%PDF-1.5\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n"
            b"0000000010 00000 n \n"
            b"0000000060 00000 n \n"
            b"0000000120 00000 n \n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
            b"startxref\n180\n"
            b"%%EOF\n"
        )
        result = inspector.inspect_bytes(clean_pdf_bytes)
        assert isinstance(result, PDFInspectionResult)
        assert result.is_tampered is False
        assert result.risk_level == "CLEAN"
        assert result.revisions.revision_count == 1
        assert result.revisions.has_incremental_updates is False
        assert len(result.revisions.overwritten_objects) == 0
        assert result.pdf_tamper_score < 0.35

    def test_multi_revision_tampered_pdf_detected(self, inspector):
        """Synthesized incremental update PDF with multiple %%EOF and overwritten objects."""
        tampered_pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Contents 4 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 20 >>\nstream\nBT /F1 12 Tf (Bill: 5000) ET\nendstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000010 00000 n \n"
            b"0000000060 00000 n \n"
            b"0000000120 00000 n \n"
            b"0000000180 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n260\n"
            b"%%EOF\n"
            # Incremental Revision 2: Overwrite object 4 with forged bill amount and iLovePDF trace
            b"4 0 obj\n<< /Length 21 >>\nstream\nBT /F1 12 Tf (Bill: 95000) ET\nendstream\nendobj\n"
            b"trailer\n<< /Size 5 /Root 1 0 R /Prev 260 /Producer (ilovepdf) >>\n"
            b"startxref\n380\n"
            b"%%EOF\n"
        )
        result = inspector.inspect_bytes(tampered_pdf_bytes)
        assert result.is_tampered is True
        assert result.revisions.has_incremental_updates is True
        assert result.revisions.revision_count == 2
        assert 4 in result.revisions.overwritten_objects
        assert result.risk_level in ["SUSPICIOUS", "TAMPERED"]
        assert result.pdf_tamper_score >= 0.50
        assert any("ilovepdf" in s.lower() for s in result.revisions.suspicious_modifications)

    def test_inspect_file_on_disk(self, inspector):
        """Verify inspect_file correctly reads from local filesystem."""
        content = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\nstartxref\n10\n%%EOF\n"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = inspector.inspect_file(temp_path)
            assert result.revisions.revision_count == 1
            assert result.details["pdf_version"] == "1.7"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_missing_file_handled(self, inspector):
        """Inspector returns graceful result for non-existent file path."""
        result = inspector.inspect_file("non_existent_file_path_123.pdf")
        assert result.is_tampered is False
        assert "File does not exist" in result.anomalies


# ---------------------------------------------------------------------------
# Feature 3: Denial Appeal Overturn & Ombudsman Risk Engine Tests
# ---------------------------------------------------------------------------

class TestAppealEvaluator:
    @pytest.fixture
    def evaluator(self):
        return AppealEvaluator()

    def test_moratorium_conflict_strong_appeal(self, evaluator):
        """Claims denied on PED after 60-month moratorium have STRONG appeal viability."""
        denial_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "Pre-existing diabetes non-disclosure"}
        ]
        claim_data = {
            "claim_date": "2025-09-01",
            "total_claimed": 150000.0,
            "total_approved": 0.0,
            "total_deducted": 150000.0,
            "diagnosis": "diabetic ketoacidosis"
        }
        policy_data = {
            "inception_date": "2019-01-01",  # > 60 months elapsed
            "moratorium_period_months": 60
        }

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert isinstance(result, AppealEvaluationResult)
        assert result.appeal_viability == "STRONG"
        assert any("Moratorium Conflict" in v for v in result.statutory_conflicts_detected)
        assert any("Asha Goel" in p for p in result.key_legal_precedents)
        assert len(result.suggested_action_plan) >= 4

    def test_mental_health_parity_conflict(self, evaluator):
        """Mental health claim denial triggers Section 21(4) conflict and STRONG appeal viability."""
        denial_reasons = [
            {"code": "MH01", "category": "MENTAL_HEALTH", "description": "Psychiatric illness excluded"}
        ]
        claim_data = {
            "claim_date": "2025-09-01",
            "diagnosis": "major depressive disorder with psychosis",
            "total_claimed": 85000.0,
            "total_approved": 0.0,
            "total_deducted": 85000.0
        }
        policy_data = {
            "inception_date": "2023-01-01",
            "covers_mental_health": True
        }

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert result.appeal_viability == "STRONG"
        assert any("Mental Health Parity Conflict" in v for v in result.statutory_conflicts_detected)
        assert any("Shikha Nischal" in p for p in result.key_legal_precedents)

    def test_emergency_admission_waiting_period_override(self, evaluator):
        """Acute emergency admission rejected under 30-day waiting period is contestable."""
        denial_reasons = [
            {"code": "WP01", "category": "WAITING_PERIOD", "description": "Hospitalization within 30 days of policy start"}
        ]
        claim_data = {
            "claim_date": "2025-01-10",
            "admission_type": "emergency",
            "diagnosis": "acute appendicitis rupture"
        }
        policy_data = {
            "inception_date": "2025-01-01"
        }

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert result.appeal_viability == "STRONG"
        assert any("Emergency Exception Breach" in v for v in result.statutory_conflicts_detected)

    def test_legitimate_cosmetic_exclusion_low_overturn(self, evaluator):
        """Cosmetic procedure exclusion is legally defensible with LOW appeal viability."""
        denial_reasons = [
            {"code": "EX01", "category": "EXCLUSION", "description": "Cosmetic aesthetic surgery excluded"}
        ]
        claim_data = {
            "claim_date": "2025-05-01",
            "diagnosis": "elective cosmetic rhinoplasty",
            "admission_type": "planned"
        }
        policy_data = {
            "inception_date": "2024-01-01"
        }

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert result.appeal_viability == "LOW"

    def test_rule_registry_check_appeal_viability_integration(self):
        """Verify check_appeal_viability registered rule verdict execution."""
        bill = HospitalBill(hospital_name="Hospital", patient_name="Patient", diagnosis="depression", line_items=[], subtotal=0, net_payable=0)
        policy = InsurancePolicy(policy_number="P1", insurer_name="Insurer", policyholder_name="Patient", policy_start_date="2020-01-01", policy_end_date="2021-01-01", sum_insured=500000, waiting_periods=[], sub_limits=[])
        rejection = RejectionLetter(
            reference_number="R1",
            insurer_name="Insurer",
            policyholder_name="Patient",
            policy_number="P1",
            claim_number="C1",
            claim_date="2025-09-01",
            total_claimed=50000.0,
            total_approved=0.0,
            total_deducted=50000.0,
            rejection_reasons=[RejectionReason(code="MH01", description="Mental health excluded", category="MENTAL_HEALTH")],
            settlement_type="FULL_REJECTION"
        )
        verdict = check_appeal_viability(bill, policy, rejection)
        assert verdict.status == "FAIL"
        assert "statutory conflicts" in verdict.finding.lower()
        assert verdict.regulatory_citation is not None


# ---------------------------------------------------------------------------
# Full System End-to-End Integration Tests
# ---------------------------------------------------------------------------

class TestFullSystemIntegration:
    def test_forensics_engine_with_pdf_and_fraud_scorer(self):
        """ForensicsEngine integrates PDF inspector and computes explainable composite fraud score."""
        engine = ForensicsEngine()
        clean_pdf_bytes = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\ntrailer\n"
            b"<< /Size 3 /Root 1 0 R >>\nstartxref\n80\n%%EOF\n"
        )
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(clean_pdf_bytes)
            pdf_path = f.name

        try:
            bill = HospitalBill(
                hospital_name="Apex Care",
                patient_name="Jane Doe",
                diagnosis="appendectomy",
                line_items=[BillLineItem(category="ROOM", description="Room", quantity=2, unit_rate=3000, amount=6000, is_room_linked=True)],
                subtotal=6000,
                net_payable=6000
            )
            result = engine.run_all_checks(pdf_path, bill=bill)

            assert result.pdf_inspection_result is not None
            assert result.pdf_inspection_result.is_tampered is False
            assert result.anomaly_assessment is not None
            assert result.anomaly_assessment.review_status == "CLEAN"
            assert result.anomaly_assessment.anomaly_density_score < 25.0
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_rule_engine_appeal_evaluation_included(self):
        """RuleEngine.run_all_rules attaches appeal_evaluation in AnalysisResult."""
        engine = RuleEngine()
        bill = HospitalBill(hospital_name="Hospital", patient_name="Patient", diagnosis="depression", line_items=[], subtotal=0, net_payable=0)
        policy = InsurancePolicy(policy_number="P1", insurer_name="Insurer", policyholder_name="Patient", policy_start_date="2020-01-01", policy_end_date="2021-01-01", sum_insured=500000, waiting_periods=[], sub_limits=[])
        rejection = RejectionLetter(
            reference_number="R1",
            insurer_name="Insurer",
            policyholder_name="Patient",
            policy_number="P1",
            claim_number="C1",
            claim_date="2025-09-01",
            total_claimed=50000.0,
            total_approved=0.0,
            total_deducted=50000.0,
            rejection_reasons=[RejectionReason(code="MH01", description="Mental health", category="MENTAL_HEALTH")],
            settlement_type="FULL_REJECTION"
        )
        analysis_res = engine.run_all_rules(bill, policy, rejection)
        assert analysis_res.appeal_evaluation is not None
        assert analysis_res.appeal_evaluation.appeal_viability == "STRONG"
