import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, ProportionateDeductionRuleConfig
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.engine import RuleEngine

def make_bill(amount):
    return HospitalBill(
        bill_id="B1",
        hospital_name="H1",
        patient_name="P1",
        admission_date="2025-01-01",
        discharge_date="2025-01-02",
        total_amount=amount,
        subtotal=amount,
        net_payable=amount,
        line_items=[
            BillLineItem(item_code="ROOM", description="Room", category="ROOM", amount=amount, quantity=1, unit_rate=amount, is_room_linked=True)
        ]
    )

def make_policy(order_clause):
    return InsurancePolicy(
        policy_number="POL1",
        insurer_name="INS1",
        policyholder_name="P1",
        policy_start_date="2024-01-01",
        policy_end_date="2025-12-31",
        sum_insured=500000.0,
        deductible=1000.0,
        copay_percentage=10.0,
        room_rent_limit_per_day=5000.0,
        deduction_order_clause=order_clause,
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=1.0,
            threshold_operator=">",
            threshold_source_type="POLICY"
        )
    )

def test_wrong_copay_order_isolated():
    # Policy says: Co-Pay BEFORE Deductible!
    policy = make_policy("CO-PAY BEFORE DEDUCTIBLE")
    bill = make_bill(10000.0)
    
    # Prop deduction = 50% = 5000.
    # Expected: 5000 (prop). Remaining = 5000.
    # Copay (10% of 5000) = 500. Remaining = 4500.
    # Deductible (1000). Remaining = 3500.
    # Expected Admissible = 3500.
    
    rej = RejectionLetter(
        reference_number="R1",
        insurer_name="INS1",
        policyholder_name="P1",
        policy_number="POL1",
        claim_number="C1",
        claim_date="2025-01-05",
        total_claimed=10000.0,
        total_deducted=6400.0,
        total_approved=3600.0, # Incorrect!
        settlement_type="PARTIAL_SETTLEMENT"
    )
    
    engine = RuleEngine()
    res = engine.run_all_rules(bill, policy, rej)
    
    assert res.overall_status == "REVIEW_RECOMMENDED"
    assert res.expected_admissible_amount == 3500.0
    assert res.total_monetary_impact == -100.0
    # Actually, it might be negative monetary impact!

def test_duplicate_deductions_detected():
    policy = make_policy("DEDUCTIBLE THEN CO-PAY")
    bill = make_bill(2000.0)
    
    # 2000 no prop (limit 5000). 
    # Deductible = 1000 -> 1000. Copay = 10% -> 100.
    # Total expected = 900.
    
    rej = RejectionLetter(
        reference_number="R1",
        insurer_name="INS1",
        policyholder_name="P1",
        policy_number="POL1",
        claim_number="C1",
        claim_date="2025-01-05",
        total_claimed=2000.0,
        total_deducted=2000.0,
        total_approved=0.0,
        settlement_type="FULL_REJECTION"
    )
    
    engine = RuleEngine()
    res = engine.run_all_rules(bill, policy, rej)
    
    assert res.expected_admissible_amount == 900.0
    assert res.total_monetary_impact == 900.0

def test_insurer_math_error():
    policy = make_policy("DEDUCTIBLE THEN CO-PAY")
    bill = make_bill(2000.0)
    
    # Claimed = 2000
    # Deducted = 100
    # Approved = 500  (Wait, 2000 - 100 = 1900, not 500!) Math is wrong!
    
    rej = RejectionLetter(
        reference_number="R1",
        insurer_name="INS1",
        policyholder_name="P1",
        policy_number="POL1",
        claim_number="C1",
        claim_date="2025-01-05",
        total_claimed=2000.0,
        total_deducted=100.0,
        total_approved=500.0,
        settlement_type="PARTIAL_SETTLEMENT"
    )
    
    engine = RuleEngine()
    res = engine.run_all_rules(bill, policy, rej)
    
    assert res.overall_status == "REVIEW_RECOMMENDED"
    # One of the verdicts should flag the math error
    math_error_found = any(v.rule_name == "Insurer Settlement Validation" for v in res.rule_verdicts)
    assert math_error_found
