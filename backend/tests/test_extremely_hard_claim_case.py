"""
Test Suite: Extremely Hard Flaws Claim Case Adjudication.
Patient: Prof. Swaminathan Venkataraman (61 Y / Male)
Hospital: Sir Ganga Ram Hospital, Rajinder Nagar, New Delhi
Underwriter: Bajaj Allianz General Insurance Co. Ltd. (Health Guard Platinum)
TPA: Heritage Health Insurance TPA Pvt. Ltd.

Validates the detection and forensic adjudication of all 5 disguised flaws:
1. Co-Surgeon / Dual Neuro-Interventionist Microvascular Fee (IRDAI Master Circular 2024 Para 5.4 & NHA Standards): Rs. 2,20,000.00
2. Adult-Manifested Congenital Aneurysmal Repudiation under 90-Month Moratorium (Chapter V Para 5.3 & Reg 17): Rs. 2,75,000.00
3. Modern Treatment Stent Capping on Base SI vs Total Effective SI (IRDAI Master Circular 2024 Para 5.4): Rs. 1,50,000.00
4. Synthetic PPN Tariff Proportionate Room Rent Haircut on Uncapped Policy (Standardization Guidelines): Rs. 1,18,000.00
5. Microvascular Embolic Introducer & Surgiflo Hemostat Disallowed under List I (Annexure A List III): Rs. 92,000.00

Mathematical Conservation:
- Billed: Rs. 14,85,000.00
- Insurer Approved: Rs. 6,22,000.00
- Insurer Disallowed: Rs. 8,63,000.00
- Legitimate List I Deductions (Attendant Meals, Hygiene Kit, Registration): Rs. 8,000.00
- Expected Admissible: Rs. 14,77,000.00
- Recoverable Yield: Rs. 8,55,000.00 (100% of all 5 statutory flaws)
"""

import os
import pytest
from app.extraction.pdf_parser_fallback import (
    parse_hospital_bill_pdf,
    parse_insurance_policy_pdf,
    parse_rejection_letter_pdf
)
from app.rules.engine import RuleEngine

TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_docs", "extremely_hard_flaws_claim_case")
BILL_PDF = os.path.join(TEST_DIR, "gangaram_hospital_bill.pdf")
POLICY_PDF = os.path.join(TEST_DIR, "bajaj_allianz_policy.pdf")
REJECTION_PDF = os.path.join(TEST_DIR, "heritage_rejection_letter.pdf")


def test_extremely_hard_claim_pdf_fixtures_exist():
    """Verify that all 3 generated PDF documents and page renders exist on disk."""
    assert os.path.exists(BILL_PDF), f"Missing {BILL_PDF}"
    assert os.path.exists(POLICY_PDF), f"Missing {POLICY_PDF}"
    assert os.path.exists(REJECTION_PDF), f"Missing {REJECTION_PDF}"


def test_extremely_hard_claim_extraction():
    """Verify 100% extraction fidelity across hospital bill, insurance policy, and rejection letter."""
    bill = parse_hospital_bill_pdf(BILL_PDF)
    assert bill is not None
    assert "GANGA RAM" in bill.hospital_name.value.upper()
    assert "SWAMINATHAN" in bill.patient_name.value.upper()
    assert bill.bill_id.value == "SGRH/FB/2026/09218"
    assert bill.total_amount.value == 1485000.0
    assert len(bill.line_items) == 32

    policy = parse_insurance_policy_pdf(POLICY_PDF)
    assert policy is not None
    assert "BAJAJ ALLIANZ" in policy.insurer_name.value.upper()
    assert policy.policy_number.value == "OG-27-1801-8401-00094182"
    assert policy.base_sum_insured.value == 1000000.0
    assert policy.cumulative_bonus.value == 500000.0
    assert policy.sum_insured.value == 1500000.0
    assert policy.portability_credits_months.value == 48
    assert policy.moratorium_period_months.value == 60
    assert policy.room_category_entitled.value == "SINGLE_PRIVATE_AC_ROOM"
    assert policy.room_rent_limit_per_day.value == 0.0

    rejection = parse_rejection_letter_pdf(REJECTION_PDF)
    assert rejection is not None
    assert "HERITAGE" in rejection.tpa_name.value.upper()
    assert rejection.claim_number.value == "HER/2026/BAJAJ/8910452"
    assert rejection.total_claimed.value == 1485000.0
    assert rejection.total_approved.value == 622000.0
    assert rejection.total_deducted.value == 863000.0
    assert len(rejection.rejection_reasons) == 6


def test_extremely_hard_claim_rule_engine_reconciliation():
    """
    End-to-end full engine test asserting:
    1. Overall status = MISMATCH_DETECTED
    2. Exactly 5 failing rules firing independently
    3. Recoverable yield = exactly Rs. 8,55,000.00
    4. Expected admissible = Rs. 14,77,000.00
    5. Complete 5 Forensic Pillars on every single card
    """
    bill = parse_hospital_bill_pdf(BILL_PDF)
    policy = parse_insurance_policy_pdf(POLICY_PDF)
    rejection = parse_rejection_letter_pdf(REJECTION_PDF)

    engine = RuleEngine()
    result = engine.run_all_rules(bill, policy, rejection)

    assert result.overall_status == "MISMATCH_DETECTED"
    assert result.billed_amount == 1485000.0
    assert result.insurer_approved_amount == 622000.0
    assert result.total_disallowed == 863000.0
    assert result.expected_admissible_amount == 1477000.0
    assert result.total_monetary_impact == 855000.0

    failing_verdicts = [v for v in result.rule_verdicts if v.status == "FAIL"]
    assert len(failing_verdicts) == 5

    failing_rule_names = {v.rule_name: v for v in failing_verdicts}
    assert "Co-Surgeon & Multi-Specialist Operative Protection Rule" in failing_rule_names
    assert "Clause Timeline Rule" in failing_rule_names
    assert "Modern Treatment Inpatient Protection Rule" in failing_rule_names
    assert "Proportionate Deduction Rule" in failing_rule_names
    assert "Non-Payable Items Rule" in failing_rule_names

    # Check specific monetary impacts per flaw
    assert failing_rule_names["Co-Surgeon & Multi-Specialist Operative Protection Rule"].monetary_impact == 220000.0
    assert failing_rule_names["Clause Timeline Rule"].monetary_impact == 275000.0
    assert failing_rule_names["Modern Treatment Inpatient Protection Rule"].monetary_impact == 150000.0
    assert failing_rule_names["Proportionate Deduction Rule"].monetary_impact == 118000.0
    assert failing_rule_names["Non-Payable Items Rule"].monetary_impact == 92000.0

    # Assert 5 Forensic Pillars on every actionable card
    for v in failing_verdicts:
        assert v.actual_claim_fact is not None, f"Missing actual_claim_fact in {v.rule_name}"
        assert v.applicable_policy_rule is not None, f"Missing applicable_policy_rule in {v.rule_name}"
        assert v.insurer_applied_action is not None, f"Missing insurer_applied_action in {v.rule_name}"
        assert v.expected_action is not None, f"Missing expected_action in {v.rule_name}"
        assert v.regulatory_citation is not None, f"Missing regulatory_citation in {v.rule_name}"
        assert "Governed by insurance policy terms" not in str(v.applicable_policy_rule)
        assert v.monetary_impact is not None and v.monetary_impact > 0
