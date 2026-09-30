import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, ProportionateDeductionRuleConfig
from app.schemas.rejection_letter import RejectionLetter
from app.rules.engine import RuleEngine
from app.schemas.provenance import Provenance

def wrap(val):
    return Provenance(value=val)

def test_rule_dependency_and_double_deduction():
    # Setup test data with Deductible + Co-Pay + Proportionate Deduction
    # Policy: Room limit 5000. Deductible 10000. Copay 10%.
    bill = HospitalBill(
        bill_id=wrap("B123"),
        hospital_name=wrap("Test Hospital"),
        patient_name=wrap("John Doe"),
        admission_date=wrap("2024-01-01"),
        discharge_date=wrap("2024-01-05"),
        length_of_stay=wrap(4),
        room_charges_per_day=wrap(10000.0), # Excess of 5000 per day. 4 days = 20000 excess. Ratio: 10000/5000 = 2.0 (>1.15)
        subtotal=wrap(100000.0),
        net_payable=wrap(100000.0),
        total_amount=wrap(100000.0),
        line_items=[
            BillLineItem(description=wrap("Room"), category=wrap("ROOM"), quantity=wrap(4), unit_rate=wrap(10000.0), amount=wrap(40000.0), is_room_linked=True),
            BillLineItem(description=wrap("Nursing"), category=wrap("NURSING"), quantity=wrap(4), unit_rate=wrap(5000.0), amount=wrap(20000.0), is_room_linked=True),
            BillLineItem(description=wrap("Surgery"), category=wrap("OT"), quantity=wrap(1), unit_rate=wrap(40000.0), amount=wrap(40000.0), is_room_linked=False)
        ]
    )
    
    policy = InsurancePolicy(
        policy_number=wrap("P123"),
        insurer_name=wrap("Test Insurer"),
        policyholder_name=wrap("John Doe"),
        policy_start_date=wrap("2023-01-01"),
        policy_end_date=wrap("2024-12-31"),
        sum_insured=wrap(500000.0),
        room_rent_limit_per_day=wrap(5000.0),
        deductible=wrap(10000.0),
        copay_percentage=wrap(10.0),
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=Provenance(value=1.15, source_type="POLICY"),
            threshold_operator=Provenance(value=">", source_type="POLICY"),
            threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
        )
    )
    
    rejection = RejectionLetter(
        reference_number=wrap("R123"),
        insurer_name=wrap("Test Insurer"),
        policyholder_name=wrap("John Doe"),
        settlement_type=wrap("FULL_REJECTION"),
        claim_number=wrap("C123"),
        policy_number=wrap("P123"),
        patient_name=wrap("John Doe"),
        claim_date=wrap("2024-01-10"),
        total_claimed=wrap(100000.0),
        total_approved=wrap(0.0),
        total_deducted=wrap(100000.0),
        deductions=[]
    )
    
    engine = RuleEngine()
    result = engine.run_all_rules(bill, policy, rejection)
    
    # Let's verify the execution graph ran perfectly without cycle errors
    assert "Rule Engine aborted due to Dependency Graph Conflict" not in result.summary
    
    # We expect these three rules to have run
    prop_verdict = next((v for v in result.rule_verdicts if v.rule_name == "Proportionate Deduction Rule"), None)
    deduct_verdict = next((v for v in result.rule_verdicts if v.rule_name == "Deductible Rule"), None)
    copay_verdict = next((v for v in result.rule_verdicts if v.rule_name == "Co-Pay Rule"), None)
    
    assert prop_verdict is not None
    assert deduct_verdict is not None
    assert copay_verdict is not None
    
    # Independent verification of the math:
    # 1. Room Excess is deducted first (40000 - 20000) = 20000 remaining for room.
    # Total room linked sum = 20000 (Room) + 20000 (Nursing) = 40000.
    # Actual rate 10000, limit 5000. Ratio = 2.0. Deduction % = 1.0 - (5000/10000) = 50%.
    # Prop Deduction = 50% of 40000 = 20000.
    assert "Expected Proportionate Reduction: Rs. 20000" in prop_verdict.finding or "Rs. 20000.00" in prop_verdict.finding
    
    # 2. Deductible Rule applies to remaining balance (100000 - 20000 excess - 20000 prop = 60000). Deductible = 10000.
    # Remaining = 50000.
    assert "Applied deductible of Rs. 10000.0" in deduct_verdict.finding
    
    # 3. Copay Rule (10%) applies to remaining balance AFTER deductibles and prop deductions.
    # So 10% of 50000 = 5000.
    assert "Applied 10.0% co-pay (Rs. 5000.0" in copay_verdict.finding
    
    # This test asserts that the rules dynamically ordered themselves, applied correct math, 
    # and prevented double deduction by using the shared AdjudicationState.
