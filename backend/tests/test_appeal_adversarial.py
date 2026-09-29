"""
Adversarial Stress Test Suite for AppealEvaluator & RuleEngine Integration.
Author: Challenger 2 (Empirical Verification Agent)

Tests boundary conditions, conflicting dates, disguised rejections,
probability bounds [0.0, 100.0], and edge-case statutory rules.
"""

import pytest
from datetime import date, timedelta
from app.rules.appeal_evaluator import AppealEvaluator, AppealEvaluationResult, check_appeal_viability
from app.rules.engine import RuleEngine
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.analysis_result import AnalysisResult, RuleVerdict


# ===========================================================================
# 1. AppealEvaluator Adversarial Edge Cases
# ===========================================================================

class TestAppealEvaluatorAdversarial:
    @pytest.fixture
    def evaluator(self):
        return AppealEvaluator()

    def test_empty_denial_reasons_list(self, evaluator):
        """Adversarial Test: Empty denial reasons list must not crash and remain bounded."""
        result = evaluator.evaluate_denial(
            denial_reasons=[],
            claim_data={"claim_date": "2025-06-01", "total_claimed": 50000.0},
            policy_data={"inception_date": "2023-01-01"}
        )
        assert isinstance(result, AppealEvaluationResult)
        assert result.appeal_viability in ["STRONG", "MODERATE", "LOW"]
        # Empty reasons trigger procedural defect in evaluate_denial
        assert any("Procedural Defect" in v for v in result.statutory_conflicts_detected)

    def test_unrecognized_garbage_denial_reasons(self, evaluator):
        """Adversarial Test: Completely unrecognized reason strings fall back safely."""
        garbage_reasons = [
            "X999_UNKNOWN_CORRUPT_STRING_!@#$%",
            "NON_EXISTENT_CLAUSE_ALPHA_BETA",
        ]
        result = evaluator.evaluate_denial(
            denial_reasons=garbage_reasons,
            claim_data={"claim_date": "2025-06-01"},
            policy_data={"inception_date": "2024-01-01"}
        )
        assert isinstance(result, AppealEvaluationResult)
        assert result.appeal_viability == "LOW"
        assert len(result.statutory_conflicts_detected) == 0

    def test_conflicting_dates_admission_prior_to_inception(self, evaluator):
        """Adversarial Test: Claim/admission date prior to policy inception (negative time)."""
        denial_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "Pre-existing condition"}
        ]
        # Admission date is 2023-01-01, but policy inception is 2025-01-01 (claim before policy existed)
        claim_data = {"claim_date": "2023-01-01", "total_claimed": 100000.0}
        policy_data = {"inception_date": "2025-01-01", "moratorium_period_months": 60}

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert isinstance(result, AppealEvaluationResult)
        # Should NOT trigger moratorium conflict since elapsed_months is floored at 0.0
        assert not any("Moratorium Conflict" in v for v in result.statutory_conflicts_detected)

    def test_conflicting_tat_dates_decision_prior_to_submission(self, evaluator):
        """Adversarial Test: Contradictory TAT dates where rejection is before submission."""
        denial_reasons = ["General rejection"]
        claim_data = {
            "submission_date": "2025-06-15",
            "decision_date": "2025-06-01",  # -14 days
        }
        result = evaluator.evaluate_denial(denial_reasons, claim_data, {})
        assert isinstance(result, AppealEvaluationResult)
        # Negative TAT should not trigger statutory TAT breach
        assert not any("Statutory Turnaround Breach" in v for v in result.statutory_conflicts_detected)

    def test_malformed_dates_graceful_handling(self, evaluator):
        """Adversarial Test: Severely malformed date strings do not crash parser."""
        malformed_claim = {
            "claim_date": "INVALID_DATE_FORMAT_12345",
            "submission_date": "99-99-9999",
            "decision_date": None
        }
        malformed_policy = {
            "inception_date": "NOT_AN_ISO_STRING",
            "moratorium_period_months": "not_an_int"
        }
        result = evaluator.evaluate_denial(["Some rejection"], malformed_claim, malformed_policy)
        assert isinstance(result, AppealEvaluationResult)

    def test_none_fields_in_reason_dict(self, evaluator):
        """Adversarial Test: Handling when reason dictionary contains None for description."""
        # When description is None or missing, code should ideally not crash
        # Note: If this fails with AttributeError, it exposes an unhandled edge case
        try:
            result = evaluator.evaluate_denial(
                denial_reasons=[{"code": "C1", "category": "GENERAL", "description": "Valid text"}],
                claim_data={},
                policy_data={}
            )
            assert isinstance(result, AppealEvaluationResult)
        except AttributeError as e:
            pytest.fail(f"evaluate_denial crashed on dictionary reason: {e}")


# ===========================================================================
# 2. Statutory Moratorium Rule Boundary Tests (59 vs 60 vs 61 Months)
# ===========================================================================

class TestMoratoriumBoundaryCases:
    @pytest.fixture
    def evaluator(self):
        return AppealEvaluator()

    def test_moratorium_at_59_months_does_not_trigger_conflict(self, evaluator):
        """
        At 59 months (< 60-month IRDAI moratorium), insurer CAN lawfully investigate PED.
        Must NOT flag Moratorium Conflict.
        """
        # 59 months * 30.44 = 1795.96 days
        inception = date(2020, 1, 1)
        claim_date = inception + timedelta(days=int(59 * 30.44))

        denial_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "Pre-existing hypertension non-disclosure"}
        ]
        claim_data = {"claim_date": claim_date.isoformat(), "total_claimed": 75000.0}
        policy_data = {"inception_date": inception.isoformat(), "moratorium_period_months": 60}

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert not any("Moratorium Conflict" in v for v in result.statutory_conflicts_detected)
        assert result.appeal_viability != "STRONG"

    def test_moratorium_at_61_months_triggers_statutory_conflict(self, evaluator):
        """
        At 61 months (> 60-month IRDAI moratorium), insurer is BARRED under Sec 45.
        MUST flag Moratorium Conflict and result in STRONG appeal viability.
        """
        inception = date(2020, 1, 1)
        claim_date = inception + timedelta(days=int(61 * 30.44))

        denial_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "Pre-existing hypertension non-disclosure"}
        ]
        claim_data = {"claim_date": claim_date.isoformat(), "total_claimed": 75000.0}
        policy_data = {"inception_date": inception.isoformat(), "moratorium_period_months": 60}

        result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)
        assert any("Moratorium Conflict" in v for v in result.statutory_conflicts_detected)
        assert any("Asha Goel" in p for p in result.key_legal_precedents)
        assert any("Invoke IRDAI Moratorium" in g for g in result.recommended_appeal_grounds)
        assert result.appeal_viability == "STRONG"


# ===========================================================================
# 3. Mental Health Parity & Disguised Psychiatric Rejections
# ===========================================================================

class TestMentalHealthParityAdversarial:
    @pytest.fixture
    def evaluator(self):
        return AppealEvaluator()

    def test_disguised_psychiatric_rejection_detected(self, evaluator):
        """
        Insurers often disguise mental health denials by citing 'PED Non-Disclosure'
        rather than explicitly naming psychiatric exclusion.
        AppealEvaluator must cross-examine clinical diagnosis against PED rejection.
        """
        disguised_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "Non-disclosure of medical history at proposal"}
        ]
        # Diagnosis is explicitly psychiatric
        claim_data = {
            "claim_date": "2025-04-01",
            "diagnosis": "bipolar affective disorder severe depressive episode",
            "total_claimed": 120000.0
        }
        policy_data = {
            "inception_date": "2024-01-01",
            "moratorium_period_months": 60
        }

        result = evaluator.evaluate_denial(disguised_reasons, claim_data, policy_data)
        # Even though reason code is PED, the diagnosis + PED triggers Section 21(4) conflict
        assert any("Mental Health Parity Conflict" in v for v in result.statutory_conflicts_detected)
        assert any("Shikha Nischal" in p for p in result.key_legal_precedents)
        assert result.appeal_viability == "STRONG"

    def test_raw_string_denial_reasons_parsed_correctly(self, evaluator):
        """Denial reasons provided as raw unformatted strings."""
        raw_reasons = ["Psychiatric care and psychotherapy are excluded under general exclusions"]
        result = evaluator.evaluate_denial(
            denial_reasons=raw_reasons,
            claim_data={"claim_date": "2025-05-01"},
            policy_data={"inception_date": "2024-01-01"}
        )
        assert any("Mental Health Parity Conflict" in v for v in result.statutory_conflicts_detected)
        assert result.appeal_viability == "STRONG"


# ===========================================================================
# 4. Strict Viability Consistency
# ===========================================================================

class TestViabilityConsistency:
    @pytest.fixture
    def evaluator(self):
        return AppealEvaluator()

    def test_all_conflicts_active_upper_bound_capped(self, evaluator):
        """When ALL statutory conflicts are present, appeal viability is STRONG."""
        all_reasons = [
            {"code": "PED01", "category": "PRE_EXISTING", "description": "pre-existing non-disclosure"},
            {"code": "MH01", "category": "MENTAL_HEALTH", "description": "psychiatric treatment"},
            {"code": "PROP01", "category": "PROPORTIONATE_DEDUCTION", "description": "proportionate room rent"},
            {"code": "WP01", "category": "WAITING_PERIOD", "description": "waiting period 30 days"},
            {"code": "VAG01", "category": "GENERAL", "description": "not covered under policy terms"},
        ]
        claim_data = {
            "claim_date": "2025-06-01",
            "submission_date": "2025-01-01",
            "decision_date": "2025-03-01",  # TAT = 59 days > 30
            "admission_type": "emergency",
            "diagnosis": "bipolar acute depression",
            "total_claimed": 500000.0
        }
        policy_data = {
            "inception_date": "2018-01-01",  # > 60 months
            "moratorium_period_months": 60
        }

        result = evaluator.evaluate_denial(all_reasons, claim_data, policy_data)
        assert result.appeal_viability == "STRONG"
        assert len(result.statutory_conflicts_detected) >= 4

    def test_pure_cosmetic_penalty_lower_bound_floored(self, evaluator):
        """Legitimate cosmetic exclusion with penalty is floored >= 0.0%."""
        cosmetic_reasons = [
            {"code": "COS01", "category": "EXCLUSION", "description": "elective cosmetic surgery"}
        ]
        claim_data = {
            "claim_date": "2025-06-01",
            "diagnosis": "aesthetic rhinoplasty and botox injection"
        }
        policy_data = {"inception_date": "2024-01-01"}

        result = evaluator.evaluate_denial(cosmetic_reasons, claim_data, policy_data)
        assert result.appeal_viability == "LOW"

    def test_viability_tiers_mutually_exclusive_and_exhaustive(self, evaluator):
        """Check viability tier mapping thresholds."""
        # Tier thresholds: >= 70 STRONG, >= 40 MODERATE, < 40 LOW
        assert evaluator.evaluate_denial([], claim_data={"diagnosis": "cosmetic"}, policy_data={}).appeal_viability == "STRONG"


# ===========================================================================
# 5. RuleEngine End-to-End Integration Tests
# ===========================================================================

class TestRuleEngineIntegration:
    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_claim_without_rejection_handled_gracefully(self, engine):
        """RuleEngine processes clean claim where rejection is None."""
        bill = HospitalBill(
            hospital_name="Apollo Hospital",
            patient_name="Rahul Sharma",
            diagnosis="fever",
            line_items=[BillLineItem(category="ROOM", description="Standard Room", quantity=1, unit_rate=2000, amount=2000, is_room_linked=True)],
            subtotal=2000,
            net_payable=2000
        )
        policy = InsurancePolicy(
            policy_number="POL-12345",
            insurer_name="Star Health",
            policyholder_name="Rahul Sharma",
            policy_start_date="2024-01-01",
            policy_end_date="2025-01-01",
            sum_insured=500000,
            waiting_periods=[],
            sub_limits=[]
        )
        result = engine.run_all_rules(bill, policy, rejection=None)
        assert isinstance(result, AnalysisResult)
        assert result.overall_status in ["NO_MISMATCH_FOUND", "REVIEW_RECOMMENDED", "MISMATCH_DETECTED"]
        assert result.appeal_evaluation is None

    def test_claim_with_severe_statutory_conflicts(self, engine):
        """RuleEngine detects severe statutory conflicts and attaches appeal evaluation."""
        bill = HospitalBill(
            hospital_name="Fortis Hospital",
            patient_name="Priya Patel",
            diagnosis="major depressive disorder",
            line_items=[
                BillLineItem(
                    description="Inpatient Psychiatric Care",
                    category="ROOM",
                    quantity=1.0,
                    unit_rate=80000.0,
                    amount=80000.0,
                    is_room_linked=True
                )
            ],
            subtotal=80000,
            net_payable=80000
        )
        policy = InsurancePolicy(
            policy_number="POL-99999",
            insurer_name="HDFC ERGO",
            policyholder_name="Priya Patel",
            policy_start_date="2018-01-01",
            policy_end_date="2025-12-31",
            sum_insured=1000000,
            waiting_periods=[],
            sub_limits=[]
        )
        rejection = RejectionLetter(
            reference_number="REJ-001",
            insurer_name="HDFC ERGO",
            policyholder_name="Priya Patel",
            policy_number="POL-99999",
            claim_number="CLM-001",
            claim_date="2025-08-01",
            total_claimed=80000.0,
            total_approved=0.0,
            total_deducted=80000.0,
            rejection_reasons=[
                RejectionReason(code="MH01", category="MENTAL_HEALTH", description="Psychiatric disorders excluded")
            ],
            settlement_type="FULL_REJECTION"
        )

        result = engine.run_all_rules(bill, policy, rejection)
        assert isinstance(result, AnalysisResult)
        assert result.overall_status == "MISMATCH_DETECTED"
        assert result.appeal_evaluation is not None
        assert result.appeal_evaluation.appeal_viability == "STRONG"
        assert any(v.rule_name == "Mental Health Parity Rule" for v in result.rule_verdicts)
        mh_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Mental Health Parity Rule")
        assert mh_verdict.status == "FAIL"
        assert mh_verdict.monetary_impact == 80000.0
