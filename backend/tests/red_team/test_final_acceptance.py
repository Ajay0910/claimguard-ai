import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
from app.rules.engine import RuleEngine
from app.engine.adjudication_state import AdjudicationState, LineItemState
from app.schemas.provenance import Provenance
from app.rules.rule_registry import register_rule, _RULE_REGISTRY

def wrap(val, conf=1.0):
    return Provenance(value=val, extraction_confidence=conf)

def test_audit_1_double_deduction_prevention():
    """Prove sequential deduction prevents double dipping."""
    state = AdjudicationState(claim_id="C1", line_items={
        "ITEM_1": LineItemState(item_code="ITEM_1", category="ROOM", original_amount=10000.0, remaining_balance=10000.0)
    })
    
    # Rule A attempts to deduct 6000
    adj1 = state.apply_deduction("Rule_A", ["ITEM_1"], 6000.0, "formula 1")
    assert adj1.adjustment_amount == 6000.0
    assert state.line_items["ITEM_1"].remaining_balance == 4000.0
    
    # Rule B attempts to deduct 6000 from the SAME item
    adj2 = state.apply_deduction("Rule_B", ["ITEM_1"], 6000.0, "formula 2")
    # MUST be capped at the remaining 4000
    assert adj2.adjustment_amount == 4000.0
    assert state.line_items["ITEM_1"].remaining_balance == 0.0

def test_audit_3_moratorium_complex():
    """Verify portability, enhanced sum insured, and exact dates."""
    policy = InsurancePolicy(
        policy_number=wrap("P1"), insurer_name=wrap("I"), policyholder_name=wrap("John"),
        policy_start_date=wrap("2023-01-01"), policy_end_date=wrap("2024-12-31"),
        sum_insured=wrap(1000000.0), enhanced_sum_insured=wrap(200000.0), # 8L base, 2L enhanced
        portability_credits_months=wrap(48), # 4 years of previous coverage
        copay_percentage=wrap(0.0)
    )
    
    # Base SI has 48 months + current policy months. 
    # Claim on 2024-01-01 -> Current policy is 12 months in. Total = 60 months.
    # Base should be protected. Enhanced is only 12 months, NOT protected.
    res = policy.evaluate_moratorium("2024-01-01", 1000.0)
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is False
    assert res["protected_amount"] == 800000.0 # Base only

def test_audit_6_contradictory_policy_mutex():
    """Verify that mutually exclusive clauses halt the engine."""
    original_registry = dict(_RULE_REGISTRY)
    try:
        @register_rule(name="Mutex A", description="A", tier=1, mutually_exclusive_with=["Mutex B"])
        def mutex_a(b, p, r, state=None): pass
        
        @register_rule(name="Mutex B", description="B", tier=1, mutually_exclusive_with=["Mutex A"])
        def mutex_b(b, p, r, state=None): pass
        
        engine = RuleEngine()
        bill = HospitalBill(bill_id=wrap("B1"), hospital_name=wrap("H"), patient_name=wrap("P"), admission_date=wrap("2024-01-01"), discharge_date=wrap("2024-01-05"), length_of_stay=wrap(4), subtotal=wrap(1000), net_payable=wrap(1000), total_amount=wrap(1000.0), line_items=[])
        policy = InsurancePolicy(policy_number=wrap("P1"), insurer_name=wrap("I"), policyholder_name=wrap("P"), policy_start_date=wrap("2023-01-01"), policy_end_date=wrap("2024-12-31"), sum_insured=wrap(100000.0), copay_percentage=wrap(0.0))
        rejection = RejectionLetter(reference_number=wrap("R1"), insurer_name=wrap("I"), policyholder_name=wrap("P"), settlement_type=wrap("FULL_REJECTION"), claim_number=wrap("C1"), policy_number=wrap("P1"), patient_name=wrap("P"), claim_date=wrap("2024-01-10"), total_claimed=wrap(1000.0), total_approved=wrap(0.0), total_deducted=wrap(1000.0), deductions=[])
        
        result = engine.run_all_rules(bill, policy, rejection)
        
        # Must flag REVIEW_RECOMMENDED due to mutex conflict
        assert result.overall_status == "REVIEW_RECOMMENDED"
        assert "Mutually exclusive conflict" in result.summary
    finally:
        _RULE_REGISTRY.clear()
        _RULE_REGISTRY.update(original_registry)

def test_audit_5_extraction_prompt_injection_safety():
    """Simulate prompt injection resulting in corrupted extracted values."""
    # The VLM is tricked into extracting negative numbers or absurd totals.
    # The mathematical layer MUST not crash, and should just process it deterministically,
    # exposing the absurdity in the final audit logic rather than executing arbitrary code.
    
    bill = HospitalBill(
        bill_id=wrap("INJECTED_SQL_DROP_TABLE"), hospital_name=wrap("H"), patient_name=wrap("P"),
        admission_date=wrap("2024-01-01"), discharge_date=wrap("2024-01-05"), length_of_stay=wrap(-999), # Injected negative
        subtotal=wrap(-1000000), net_payable=wrap(-1000000), total_amount=wrap(-1000000.0), # Absurd total
        line_items=[]
    )
    policy = InsurancePolicy(policy_number=wrap("P1"), insurer_name=wrap("I"), policyholder_name=wrap("P"), policy_start_date=wrap("2023-01-01"), policy_end_date=wrap("2024-12-31"), sum_insured=wrap(100000.0), copay_percentage=wrap(0.0))
    rejection = RejectionLetter(reference_number=wrap("R1"), insurer_name=wrap("I"), policyholder_name=wrap("P"), settlement_type=wrap("FULL_REJECTION"), claim_number=wrap("C1"), policy_number=wrap("P1"), patient_name=wrap("P"), claim_date=wrap("2024-01-10"), total_claimed=wrap(-1000000.0), total_approved=wrap(0.0), total_deducted=wrap(0.0), deductions=[])
    
    engine = RuleEngine()
    result = engine.run_all_rules(bill, policy, rejection)
    
    # Financial math should execute flawlessly against the numbers provided.
    # It will not execute code. The prompt injection only affects data values.
    # Because there are no items, deductions, etc., it should just pass/skip safely.
    assert isinstance(result.total_monetary_impact, float)
