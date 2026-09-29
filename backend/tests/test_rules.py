import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, WaitingPeriodConfig, ProportionateDeductionRuleConfig
from app.schemas.provenance import Provenance
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.clause_timeline import check_clause_timeline
from app.rules.mental_health_parity import check_mental_health_parity
from app.rules.waiting_period import check_waiting_period
from app.rules.engine import RuleEngine

def get_base_bill():
    return HospitalBill(
        hospital_name="Test Hospital",
        patient_name="John Doe",
        admission_date="2025-09-01",
        discharge_date="2025-09-02",
        line_items=[],
        subtotal=0,
        net_payable=0
    )

def get_base_policy():
    return InsurancePolicy(
        policy_number="POL-123",
        insurer_name="Test Insurer",
        policyholder_name="John Doe",
        policy_start_date="2020-01-01",
        policy_end_date="2021-01-01",
        sum_insured=500000,
        waiting_periods=[],
        sub_limits=[],
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=Provenance(value=1.0, source_type="POLICY"),
            threshold_operator=Provenance(value=">", source_type="POLICY"),
            threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
        )
    )

def get_base_rejection():
    return RejectionLetter(
        reference_number="REF-123",
        insurer_name="Test Insurer",
        policyholder_name="John Doe",
        policy_number="POL-123",
        claim_number="CLM-123",
        claim_date="2025-09-01",
        total_claimed=10000.0,
        total_approved=0.0,
        total_deducted=10000.0,
        rejection_reasons=[],
        settlement_type="FULL_REJECTION"
    )

def test_proportionate_deduction_no_cap():
    bill = get_base_bill()
    bill.line_items = [
        BillLineItem(description="Room", category="ROOM", quantity=1, unit_rate=5000, amount=5000, is_room_linked=True)
    ]
    policy = get_base_policy()
    policy.room_rent_limit_per_day = None
    rejection = get_base_rejection()
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status in ["PASS", "NOT_APPLICABLE"]

def test_proportionate_deduction_within_limit():
    bill = get_base_bill()
    bill.line_items = [
        BillLineItem(description="Room", category="ROOM", quantity=1, unit_rate=4000, amount=4000, is_room_linked=True)
    ]
    policy = get_base_policy()
    policy.room_rent_limit_per_day = 5000
    rejection = get_base_rejection()
    rejection.total_deducted = 0.0
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"

def test_proportionate_deduction_mismatch():
    bill = get_base_bill()
    bill.line_items = [
        BillLineItem(description="Room", category="ROOM", quantity=1, unit_rate=6000, amount=6000, is_room_linked=True),
        BillLineItem(description="Surgery", category="OT", quantity=1, unit_rate=10000, amount=10000, is_room_linked=False)
    ]
    policy = get_base_policy()
    policy.room_rent_limit_per_day = 4000
    rejection = get_base_rejection()
    rejection.total_deducted = 18000.0
    
    # Correct payable calculation:
    # Room deduction factor: 4000 / 6000 = 2/3
    # Room linked (6000) * 2/3 = 4000
    # Fixed charges (10000) = 10000
    # Total correct payable = 14000
    # Insurer approved = 0
    # Difference = 14000
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert abs(verdict.monetary_impact - 14000.0) < 0.1

def test_proportionate_deduction_correct_deduction():
    bill = get_base_bill()
    bill.line_items = [
        BillLineItem(description="Room", category="ROOM", quantity=1, unit_rate=6000, amount=6000, is_room_linked=True),
        BillLineItem(description="Surgery", category="OT", quantity=1, unit_rate=10000, amount=10000, is_room_linked=False)
    ]
    policy = get_base_policy()
    policy.room_rent_limit_per_day = 4000
    rejection = get_base_rejection()
    rejection.total_approved = 12000.0
    rejection.total_deducted = 4000.0
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_clause_timeline_moratorium_expired():
    bill = get_base_bill()
    policy = get_base_policy()
    policy.policy_start_date = "2020-01-01"
    # Actually the rule uses inception_date, let's mock it
    policy.inception_date = "2020-01-01"
    policy.moratorium_period_months = 60
    
    rejection = get_base_rejection()
    rejection.claim_date = "2025-09-01"
    rejection.rejection_reasons = [RejectionReason(code="PRE01", description="Pre-existing", category="PRE_EXISTING")]
    rejection.reasons = rejection.rejection_reasons
    
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"

def test_clause_timeline_moratorium_active():
    bill = get_base_bill()
    policy = get_base_policy()
    policy.inception_date = "2024-01-01"
    policy.moratorium_period_months = 60
    
    rejection = get_base_rejection()
    rejection.claim_date = "2025-09-01"
    rejection.rejection_reasons = [RejectionReason(code="PRE01", description="Pre-existing", category="PRE_EXISTING")]
    rejection.reasons = rejection.rejection_reasons
    
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "PASS"

def test_mental_health_rejected():
    bill = get_base_bill()
    bill.diagnosis = "depression"
    policy = get_base_policy()
    policy.covers_mental_health = True
    
    rejection = get_base_rejection()
    rejection.total_claimed = 50000.0
    rejection.total_approved = 0.0
    rejection.rejection_reasons = [RejectionReason(code="MH01", description="Mental Health", category="MENTAL_HEALTH")]
    rejection.reasons = rejection.rejection_reasons
    
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"

def test_mental_health_not_applicable():
    bill = get_base_bill()
    bill.diagnosis = "appendectomy"
    policy = get_base_policy()
    rejection = get_base_rejection()
    
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "SKIPPED"

def test_waiting_period_expired():
    bill = get_base_bill()
    policy = get_base_policy()
    policy.inception_date = "2023-01-01"
    rejection = get_base_rejection()
    rejection.claim_date = "2025-09-01"
    rejection.rejection_reasons = [RejectionReason(code="WP01", description="Specific Disease", category="WAITING_PERIOD")]
    rejection.reasons = rejection.rejection_reasons
    
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "FAIL"

def test_waiting_period_active():
    bill = get_base_bill()
    policy = get_base_policy()
    policy.inception_date = "2025-09-01"
    rejection = get_base_rejection()
    rejection.claim_date = "2025-09-15"
    reason = RejectionReason(code="WP01", description="Initial 30 days", category="WAITING_PERIOD")
    # Setting details attribute as expected by the rule code
    reason.details = "initial"
    rejection.rejection_reasons = [reason]
    rejection.reasons = rejection.rejection_reasons
    
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "PASS"

def test_rule_engine_integration():
    bill = get_base_bill()
    policy = get_base_policy()
    rejection = get_base_rejection()
    
    engine = RuleEngine()
    result = engine.run_all_rules(bill, policy, rejection)
    
    assert hasattr(result, "overall_status")
    assert isinstance(result.rule_verdicts, list)
    assert len(result.rule_verdicts) >= 0
