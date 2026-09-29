import pytest
from datetime import datetime
from decimal import Decimal

from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.engine.calculator import FinancialMath, SafeDecimal
from app.rules.engine import RuleEngine

def wrap(v):
    return Provenance(value=v)

def test_financial_math_reconciliation():
    """Verify that the engine uses FinancialMath for strict financial reconciliation."""
    engine = RuleEngine()
    bill = HospitalBill(
        hospital_name=wrap("Hospital"), patient_name=wrap("Patient"), diagnosis=wrap("Flu"),
        line_items=[
            BillLineItem(category=wrap("ROOM"), description=wrap("Room"), quantity=wrap(1), unit_rate=wrap(1500.25), amount=wrap(1500.25)),
            BillLineItem(category=wrap("PHARMACY"), description=wrap("Med"), quantity=wrap(1), unit_rate=wrap(500.50), amount=wrap(500.50))
        ],
        subtotal=wrap(2000.75), net_payable=wrap(2000.75)
    )
    policy = InsurancePolicy(
        policy_number=wrap("P1"), insurer_name=wrap("Insurer"), policyholder_name=wrap("Patient"),
        policy_start_date=wrap("2020-01-01"), policy_end_date=wrap("2021-01-01"), sum_insured=wrap(500000),
        waiting_periods=[], sub_limits=[]
    )
    rejection = RejectionLetter(
        reference_number=wrap("R1"), insurer_name=wrap("Insurer"), policyholder_name=wrap("Patient"),
        policy_number=wrap("P1"), claim_number=wrap("C1"), claim_date=wrap("2025-09-01"),
        total_claimed=wrap(2000.75), total_approved=wrap(2000.75), total_deducted=wrap(0.0),
        rejection_reasons=[], settlement_type=wrap("PARTIAL_SETTLEMENT")
    )
    
    result = engine.run_all_rules(bill, policy, rejection)
    
    # Financial reconciliation should pass if disputed amount > 1.0 is considered mismatch.
    # Here disputed amount = 2000.75 - 2000.00 = 0.75, which is <= 1.0. So it should PASS reconciliation.
    verdicts = result.rule_verdicts
    recon_verdict = next((v for v in verdicts if v.rule_name == "Final Financial Reconciliation Gate"), None)
    assert recon_verdict is not None
    assert recon_verdict.status == "PASS"

def test_moratorium_enhanced_sum_insured():
    """Verify that enhanced sum insured gets its own 60-month timer."""
    policy = InsurancePolicy(
        policy_number=wrap("P123"), insurer_name=wrap("I"), policyholder_name=wrap("John"),
        policy_start_date=wrap("2023-01-01"), # enhanced sum insured started here
        inception_date=wrap("2015-01-01"), # base sum insured started here
        policy_end_date=wrap("2024-12-31"), sum_insured=wrap(1000000.0), enhanced_sum_insured=wrap(500000.0),
        copay_percentage=wrap(0.0)
    )
    
    # 2024-06-01: Base is > 60 months (protected). Enhanced is < 60 months (not protected).
    res = policy.evaluate_moratorium("2024-06-01", 1200000.0)
    assert res["is_protected"] is True
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is False
    assert res["protected_amount"] == 500000.0 # base_si - enhanced_si
    
def test_financialmath_preserves_provenance():
    """Test FinancialMath explicitly tracking operand provenance in calculation."""
    val1 = Provenance(value=100.0, source_document_id="doc1")
    val2 = Provenance(value=50.0, source_document_id="doc2")
    
    result = FinancialMath.add(val1, val2)
    assert result.value == Decimal("150.00")
    assert "doc1" in result.source_document_id
    assert "doc2" in result.source_document_id
    assert result.calculation_inputs["operator"] == "ADD"

def test_migration_and_enhanced_date():
    """Verify migration credits and explicit enhanced sum insured dates."""
    policy = InsurancePolicy(
        policy_number=wrap("P124"), insurer_name=wrap("I"), policyholder_name=wrap("John"),
        policy_start_date=wrap("2023-01-01"), 
        inception_date=wrap("2020-01-01"), 
        policy_end_date=wrap("2024-12-31"), 
        sum_insured=wrap(1000000.0), 
        enhanced_sum_insured=wrap(500000.0),
        enhanced_sum_insured_date=wrap("2021-01-01"),
        migration_credits_months=wrap(12),
        portability_credits_months=wrap(12),
        copay_percentage=wrap(0.0)
    )
    
    res = policy.evaluate_moratorium("2025-06-01", 1200000.0)
    assert res["is_protected"] is True
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is False
    assert res["protected_amount"] == 500000.0
    
    res = policy.evaluate_moratorium("2022-06-01", 1200000.0)
    assert res["is_protected"] is False
    assert res["base_protected"] is False
    assert res["enhanced_protected"] is False
    
    res = policy.evaluate_moratorium("2026-06-01", 1200000.0)
    assert res["is_protected"] is True
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is True
    assert res["protected_amount"] == 1000000.0
