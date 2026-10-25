"""
Comprehensive Adversarial Test Suite for the Universal Extraction & Adjudication Engine
with 3 Brand-New, Unseen Synthetic Claim Scenarios:

Scenario 1:
  - Hospital: Fortis Healthcare Limited
  - Insurer: HDFC ERGO General Insurance Company Limited (Optima Secure)
  - TPA: MDIndia Health Insurance TPA Pvt. Ltd.
  - Patient: Mr. Amitabh Verma (Acute Necrotizing Pancreatitis with Peripancreatic Fluid Collection)
  - Forensic Flaws: List III consumables disallowance (Rs. 25,000) & Room Rent Proportionate Deduction (Rs. 56,000)

Scenario 2:
  - Hospital: Medanta - The Medicity
  - Insurer: Niva Bupa Health Insurance Company Limited (ReAssure 2.0)
  - TPA: Family Health Plan Insurance TPA Limited (FHPL)
  - Patient: Mrs. Meenakshi Iyer (Acute Coronary Syndrome, CAD, PTCA Cardiac Stenting)
  - Forensic Flaws: Cumulative Bonus renewal grace period forfeiture disallowance (Rs. 2,40,000)

Scenario 3:
  - Hospital: Manipal Hospital
  - Insurer: ICICI Lombard General Insurance Company Limited (Complete Health Insurance)
  - TPA: Medi Assist Insurance TPA Pvt. Ltd.
  - Patient: Mr. Rajesh Kulkarni (Acute Gangrenous Appendicitis, Laparoscopic Appendectomy)
  - Forensic Flaws: Modern treatment emergency inpatient day-care sub-limit capping (Rs. 30,000)

Validation Invariants:
1. Zero hardcoded fallback strings triggered.
2. Identity, line items, policy limits, and rejection disallowances extracted dynamically.
3. FinancialMath reconciles admissible and recoverable amounts with 100% mathematical precision.
"""

import os
import pytest
from app.extraction.pdf_parser_fallback import (
    parse_hospital_bill_pdf,
    parse_insurance_policy_pdf,
    parse_rejection_letter_pdf,
)
from app.extraction.pipeline import ExtractionPipeline
from app.rules.engine import RuleEngine
from app.rules.statutory_policy_auditor import audit_statutory_policy_compliance
from app.engine.calculator import FinancialMath

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
UNSEEN_DIR = os.path.join(PROJECT_ROOT, "test_docs", "unseen_scenarios")


@pytest.fixture(scope="session", autouse=True)
def ensure_unseen_documents_exist():
    """Ensure all 9 PDFs across 3 unseen scenarios exist, generating them if missing."""
    s1_pdf = os.path.join(UNSEEN_DIR, "scenario_1_fortis_hdfc_mdindia", "hospital_bill.pdf")
    s2_pdf = os.path.join(UNSEEN_DIR, "scenario_2_medanta_nivabupa_fhpl", "hospital_bill.pdf")
    s3_pdf = os.path.join(UNSEEN_DIR, "scenario_3_manipal_icici_mediassist", "hospital_bill.pdf")

    if not (os.path.exists(s1_pdf) and os.path.exists(s2_pdf) and os.path.exists(s3_pdf)):
        scripts_dir = os.path.join(PROJECT_ROOT, "scripts")
        gen_script = os.path.join(scripts_dir, "generate_unseen_scenarios.py")
        if os.path.exists(gen_script):
            import sys
            import subprocess
            subprocess.run([sys.executable, gen_script, UNSEEN_DIR], check=True)
        else:
            pytest.fail(f"Generator script not found at {gen_script}")


@pytest.fixture
def scenario_1_bundle():
    s_dir = os.path.join(UNSEEN_DIR, "scenario_1_fortis_hdfc_mdindia")
    bill = parse_hospital_bill_pdf(os.path.join(s_dir, "hospital_bill.pdf"))
    pol = parse_insurance_policy_pdf(os.path.join(s_dir, "insurance_policy.pdf"))
    rej = parse_rejection_letter_pdf(os.path.join(s_dir, "rejection_letter.pdf"))
    return {"bill": bill, "policy": pol, "rejection": rej}


@pytest.fixture
def scenario_2_bundle():
    s_dir = os.path.join(UNSEEN_DIR, "scenario_2_medanta_nivabupa_fhpl")
    bill = parse_hospital_bill_pdf(os.path.join(s_dir, "hospital_bill.pdf"))
    pol = parse_insurance_policy_pdf(os.path.join(s_dir, "insurance_policy.pdf"))
    rej = parse_rejection_letter_pdf(os.path.join(s_dir, "rejection_letter.pdf"))
    return {"bill": bill, "policy": pol, "rejection": rej}


@pytest.fixture
def scenario_3_bundle():
    s_dir = os.path.join(UNSEEN_DIR, "scenario_3_manipal_icici_mediassist")
    bill = parse_hospital_bill_pdf(os.path.join(s_dir, "hospital_bill.pdf"))
    pol = parse_insurance_policy_pdf(os.path.join(s_dir, "insurance_policy.pdf"))
    rej = parse_rejection_letter_pdf(os.path.join(s_dir, "rejection_letter.pdf"))
    return {"bill": bill, "policy": pol, "rejection": rej}


# ==============================================================================
# SCENARIO 1 TESTS: Fortis + HDFC ERGO + MDIndia TPA
# ==============================================================================

def test_scenario_1_universal_parser_dynamic_extraction(scenario_1_bundle):
    """
    Assert that the Universal Parser extracts all entities dynamically from Fortis / HDFC / MDIndia PDFs:
    - Zero fallback strings triggered.
    - Identity, hospital, line items, room linkage, policy schedule limits, and rejection reasons.
    """
    b, p, r = scenario_1_bundle["bill"], scenario_1_bundle["policy"], scenario_1_bundle["rejection"]

    # 1. Hospital Bill Assertions
    assert b is not None
    assert b.patient_name.value != "Unknown Patient"
    assert "Amitabh Verma" in b.patient_name.value
    assert b.bill_id.value != "BILL-UNKNOWN"
    assert "FHL/BLR/IPB/2026/04192" in b.bill_id.value
    assert b.hospital_name.value != "Hospital"
    assert "FORTIS" in b.hospital_name.value.upper()
    assert b.total_amount.value == 201000.0
    assert b.subtotal.value == 201000.0
    assert b.arithmetic_verified is True
    assert b.length_of_stay == 5
    assert "Pancreatitis" in b.diagnosis.value

    # Assert no synthetic fallback balancing items
    for item in b.line_items:
        assert item.description.value != "Inpatient Hospitalization & Medical Services"
        assert item.description.value != "General Inpatient Medical Treatment"

    # Line item classification & room-linkage verification
    assert len(b.line_items) == 10
    icu_items = [i for i in b.line_items if "MICU" in i.description.value or "ICU" in i.description.value]
    assert len(icu_items) >= 1
    for icu in icu_items:
        assert icu.is_room_linked is False, "MICU/ICU charges must never be room-linked"

    ward_room_items = [i for i in b.line_items if "Single Deluxe AC Room" in i.description.value]
    assert len(ward_room_items) >= 1
    for wr in ward_room_items:
        assert wr.is_room_linked is True, "Ward room charges must be room-linked"

    consumables = [i for i in b.line_items if i.category.value == "CONSUMABLES"]
    assert len(consumables) >= 2
    for c in consumables:
        assert c.is_room_linked is False

    # 2. Insurance Policy Assertions
    assert p is not None
    assert p.policyholder_name.value != "Policyholder"
    assert "Amitabh Verma" in p.policyholder_name.value
    assert p.policy_number.value != "POL-UNKNOWN"
    assert "HDFC/OPT/2024/782190" in p.policy_number.value
    assert p.insurer_name.value != "Insurance Company"
    assert "HDFC ERGO" in p.insurer_name.value.upper()
    assert p.sum_insured.value == 1000000.0
    assert p.base_sum_insured.value == 1000000.0
    assert p.room_rent_limit_per_day.value == 5000.0
    assert p.moratorium_period_months.value == 60
    assert p.covers_mental_health.value is True

    # 3. Rejection Letter Assertions
    assert r is not None
    assert r.policyholder_name.value != "Policyholder"
    assert "Amitabh Verma" in r.policyholder_name.value
    assert r.claim_number.value != "CLAIM-UNKNOWN"
    assert "MDI/2026/HDFC/991204" in r.claim_number.value
    assert r.tpa_name is not None
    assert "MDINDIA" in r.tpa_name.value.upper()
    assert r.total_claimed.value == 201000.0
    assert r.total_approved.value == 119000.0
    assert r.total_deducted.value == 82000.0

    # Ensure rejection reasons are parsed dynamically from the table
    assert len(r.rejection_reasons) == 3
    for reason in r.rejection_reasons:
        assert reason.code.value != "DEDUCT-01"


def test_scenario_1_statutory_policy_compliance(scenario_1_bundle):
    """Assert HDFC ERGO Optima Secure policy terms pass IRDAI Statutory Policy Auditor."""
    p = scenario_1_bundle["policy"]
    verdict = audit_statutory_policy_compliance(None, p, None)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"
    assert verdict.actual_claim_fact is not None
    assert verdict.applicable_policy_rule is not None


def test_scenario_1_engine_adjudication_and_reconciliation(scenario_1_bundle):
    """
    Run full adjudication engine on Scenario 1:
    - Billed: Rs. 2,01,000.00
    - Insurer Approved: Rs. 1,19,000.00
    - Total Disallowed: Rs. 82,000.00
    - Legitimate Deductions: Rs. 26,000.00 (Room Excess Rs. 15,000 + Prop Reduction Rs. 9,000 + List I Rs. 2,000)
    - Expected Admissible: Rs. 1,75,000.00
    - Recoverable / Disputed: Rs. 56,000.00
    - Mathematical reconciliation with FinancialMath: 100% precision.
    """
    b, p, r = scenario_1_bundle["bill"], scenario_1_bundle["policy"], scenario_1_bundle["rejection"]
    engine = RuleEngine()
    result = engine.run_all_rules(b, p, r)

    assert result.overall_status == "MISMATCH_DETECTED"

    # FinancialMath exact arithmetic reconciliation
    assert result.billed_amount == 201000.0
    assert result.insurer_approved_amount == 119000.0
    assert result.total_disallowed == 82000.0
    assert result.expected_admissible_amount == 175000.0
    assert result.total_monetary_impact == 56000.0
    assert result.legitimate_deduction == 26000.0

    # Strict mathematical identity verification
    assert abs(result.billed_amount - (result.insurer_approved_amount + result.total_disallowed)) < 0.001
    assert abs(result.total_disallowed - (result.legitimate_deduction + result.total_monetary_impact)) < 0.001
    assert abs(result.expected_admissible_amount - (result.billed_amount - result.legitimate_deduction)) < 0.001
    assert abs(result.total_monetary_impact - (result.expected_admissible_amount - result.insurer_approved_amount)) < 0.001

    # Verify specific rule failures
    failing_rules = {v.rule_name: v for v in result.rule_verdicts if v.status == "FAIL"}
    assert "Proportionate Deduction Rule" in failing_rules
    assert "Non-Payable Items Rule" in failing_rules

    prop_verdict = failing_rules["Proportionate Deduction Rule"]
    assert prop_verdict.monetary_impact == 56000.0
    assert prop_verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert "FORTIS" in prop_verdict.actual_claim_fact.upper()
    assert "HDFC ERGO" in prop_verdict.evidence or "HDFC" in prop_verdict.evidence

    non_pay_verdict = failing_rules["Non-Payable Items Rule"]
    assert non_pay_verdict.monetary_impact == 25000.0
    assert non_pay_verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert "List III" in non_pay_verdict.finding


# ==============================================================================
# SCENARIO 2 TESTS: Medanta + Niva Bupa ReAssure + FHPL TPA
# ==============================================================================

def test_scenario_2_universal_parser_dynamic_extraction(scenario_2_bundle):
    """
    Assert that the Universal Parser extracts all entities dynamically from Medanta / Niva Bupa / FHPL PDFs:
    - Zero fallback strings triggered.
    - Identity, hospital, line items, cumulative bonus, policy schedule, and rejection reasons.
    """
    b, p, r = scenario_2_bundle["bill"], scenario_2_bundle["policy"], scenario_2_bundle["rejection"]

    # 1. Hospital Bill Assertions
    assert b is not None
    assert b.patient_name.value != "Unknown Patient"
    assert "Meenakshi Iyer" in b.patient_name.value
    assert b.bill_id.value != "BILL-UNKNOWN"
    assert "MED/GUR/IPB/2026/09214" in b.bill_id.value
    assert b.hospital_name.value != "Hospital"
    assert "MEDANTA" in b.hospital_name.value.upper()
    assert b.total_amount.value == 1240000.0
    assert b.subtotal.value == 1240000.0
    assert b.arithmetic_verified is True
    assert b.length_of_stay == 5
    assert "Coronary" in b.diagnosis.value or "PTCA" in b.diagnosis.value

    for item in b.line_items:
        assert item.description.value != "Inpatient Hospitalization & Medical Services"
        assert item.description.value != "General Inpatient Medical Treatment"

    assert len(b.line_items) == 11
    ccu_items = [i for i in b.line_items if "CCU" in i.description.value]
    assert len(ccu_items) >= 1
    for ccu in ccu_items:
        assert ccu.is_room_linked is False, "CCU charges must never be room-linked"

    # 2. Insurance Policy Assertions
    assert p is not None
    assert p.policyholder_name.value != "Policyholder"
    assert "Meenakshi Iyer" in p.policyholder_name.value
    assert p.policy_number.value != "POL-UNKNOWN"
    assert "NB/REASSURE/2021/884129" in p.policy_number.value
    assert p.insurer_name.value != "Insurance Company"
    assert "NIVA BUPA" in p.insurer_name.value.upper()
    assert p.base_sum_insured.value == 1000000.0
    assert p.cumulative_bonus.value == 500000.0
    assert p.sum_insured.value == 1500000.0
    assert p.room_rent_limit_per_day.value == 0.0
    assert p.moratorium_period_months.value == 60
    assert p.covers_mental_health.value is True

    # 3. Rejection Letter Assertions
    assert r is not None
    assert r.policyholder_name.value != "Policyholder"
    assert "Meenakshi Iyer" in r.policyholder_name.value
    assert r.claim_number.value != "CLAIM-UNKNOWN"
    assert "FHPL/2026/NB/441209" in r.claim_number.value
    assert r.tpa_name is not None
    assert "FHPL" in r.tpa_name.value.upper() or "FAMILY HEALTH" in r.tpa_name.value.upper()
    assert r.total_claimed.value == 1240000.0
    assert r.total_approved.value == 995000.0
    assert r.total_deducted.value == 245000.0

    assert len(r.rejection_reasons) == 2
    for reason in r.rejection_reasons:
        assert reason.code.value != "DEDUCT-01"


def test_scenario_2_statutory_policy_compliance(scenario_2_bundle):
    """Assert Niva Bupa ReAssure policy terms pass IRDAI Statutory Policy Auditor."""
    p = scenario_2_bundle["policy"]
    verdict = audit_statutory_policy_compliance(None, p, None)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"
    assert verdict.actual_claim_fact is not None
    assert verdict.applicable_policy_rule is not None


def test_scenario_2_engine_adjudication_and_reconciliation(scenario_2_bundle):
    """
    Run full adjudication engine on Scenario 2:
    - Billed: Rs. 12,40,000.00
    - Insurer Approved: Rs. 9,95,000.00
    - Total Disallowed: Rs. 2,45,000.00
    - Legitimate Deductions: Rs. 5,000.00 (List I Admission Registration)
    - Expected Admissible: Rs. 12,35,000.00
    - Recoverable / Disputed: Rs. 2,40,000.00
    - Mathematical reconciliation with FinancialMath: 100% precision.
    """
    b, p, r = scenario_2_bundle["bill"], scenario_2_bundle["policy"], scenario_2_bundle["rejection"]
    engine = RuleEngine()
    result = engine.run_all_rules(b, p, r)

    assert result.overall_status == "MISMATCH_DETECTED"

    # FinancialMath exact arithmetic reconciliation
    assert result.billed_amount == 1240000.0
    assert result.insurer_approved_amount == 995000.0
    assert result.total_disallowed == 245000.0
    assert result.expected_admissible_amount == 1235000.0
    assert result.total_monetary_impact == 240000.0
    assert result.legitimate_deduction == 5000.0

    # Strict mathematical identity verification
    assert abs(result.billed_amount - (result.insurer_approved_amount + result.total_disallowed)) < 0.001
    assert abs(result.total_disallowed - (result.legitimate_deduction + result.total_monetary_impact)) < 0.001
    assert abs(result.expected_admissible_amount - (result.billed_amount - result.legitimate_deduction)) < 0.001
    assert abs(result.total_monetary_impact - (result.expected_admissible_amount - result.insurer_approved_amount)) < 0.001

    # Verify Cumulative Bonus Protection rule failure
    failing_rules = {v.rule_name: v for v in result.rule_verdicts if v.status == "FAIL"}
    assert "Cumulative Bonus & Grace Period Rule" in failing_rules
    cb_verdict = failing_rules["Cumulative Bonus & Grace Period Rule"]
    assert cb_verdict.monetary_impact == 240000.0
    assert cb_verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Regulation 13" in cb_verdict.regulatory_citation
    assert "grace period" in cb_verdict.finding.lower()
    assert cb_verdict.actual_claim_fact is not None
    assert "240,000.00" in cb_verdict.actual_claim_fact


# ==============================================================================
# SCENARIO 3 TESTS: Manipal Hospital + ICICI Lombard + Medi Assist
# ==============================================================================

def test_scenario_3_universal_parser_dynamic_extraction(scenario_3_bundle):
    """
    Assert that the Universal Parser extracts all entities dynamically from Manipal / ICICI / Medi Assist PDFs:
    - Zero fallback strings triggered.
    - Identity, hospital, line items, policy limits, and rejection reasons.
    """
    b, p, r = scenario_3_bundle["bill"], scenario_3_bundle["policy"], scenario_3_bundle["rejection"]

    # 1. Hospital Bill Assertions
    assert b is not None
    assert b.patient_name.value != "Unknown Patient"
    assert "Rajesh Kulkarni" in b.patient_name.value
    assert b.bill_id.value != "BILL-UNKNOWN"
    assert "MH/BLR/IPB/2026/05819" in b.bill_id.value
    assert b.hospital_name.value != "Hospital"
    assert "MANIPAL" in b.hospital_name.value.upper()
    assert b.total_amount.value == 290000.0
    assert b.subtotal.value == 290000.0
    assert b.arithmetic_verified is True
    assert b.length_of_stay == 3
    assert "Appendicitis" in b.diagnosis.value

    for item in b.line_items:
        assert item.description.value != "Inpatient Hospitalization & Medical Services"
        assert item.description.value != "General Inpatient Medical Treatment"

    assert len(b.line_items) == 12

    # 2. Insurance Policy Assertions
    assert p is not None
    assert p.policyholder_name.value != "Policyholder"
    assert "Rajesh Kulkarni" in p.policyholder_name.value
    assert p.policy_number.value != "POL-UNKNOWN"
    assert "ICICI/CHI/2023/339102" in p.policy_number.value
    assert p.insurer_name.value != "Insurance Company"
    assert "ICICI LOMBARD" in p.insurer_name.value.upper()
    assert p.base_sum_insured.value == 800000.0
    assert p.sum_insured.value == 800000.0
    assert p.room_rent_limit_per_day.value == 0.0
    assert p.moratorium_period_months.value == 60
    assert p.covers_mental_health.value is True

    # 3. Rejection Letter Assertions
    assert r is not None
    assert r.policyholder_name.value != "Policyholder"
    assert "Rajesh Kulkarni" in r.policyholder_name.value
    assert r.claim_number.value != "CLAIM-UNKNOWN"
    assert "MA/2026/ICICI/552109" in r.claim_number.value
    assert r.tpa_name is not None
    assert "MEDI ASSIST" in r.tpa_name.value.upper()
    assert r.total_claimed.value == 290000.0
    assert r.total_approved.value == 257000.0
    assert r.total_deducted.value == 33000.0

    assert len(r.rejection_reasons) == 2
    for reason in r.rejection_reasons:
        assert reason.code.value != "DEDUCT-01"


def test_scenario_3_statutory_policy_compliance(scenario_3_bundle):
    """Assert ICICI Lombard Complete Health policy terms pass IRDAI Statutory Policy Auditor."""
    p = scenario_3_bundle["policy"]
    verdict = audit_statutory_policy_compliance(None, p, None)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"
    assert verdict.actual_claim_fact is not None
    assert verdict.applicable_policy_rule is not None


def test_scenario_3_engine_adjudication_and_reconciliation(scenario_3_bundle):
    """
    Run full adjudication engine on Scenario 3:
    - Billed: Rs. 2,90,000.00
    - Insurer Approved: Rs. 2,57,000.00
    - Total Disallowed: Rs. 33,000.00
    - Legitimate Deductions: Rs. 3,000.00 (List I Registration & Documentation)
    - Expected Admissible: Rs. 2,87,000.00
    - Recoverable / Disputed: Rs. 30,000.00
    - Mathematical reconciliation with FinancialMath: 100% precision.
    """
    b, p, r = scenario_3_bundle["bill"], scenario_3_bundle["policy"], scenario_3_bundle["rejection"]
    engine = RuleEngine()
    result = engine.run_all_rules(b, p, r)

    assert result.overall_status == "MISMATCH_DETECTED"

    # FinancialMath exact arithmetic reconciliation
    assert result.billed_amount == 290000.0
    assert result.insurer_approved_amount == 257000.0
    assert result.total_disallowed == 33000.0
    assert result.expected_admissible_amount == 287000.0
    assert result.total_monetary_impact == 30000.0
    assert result.legitimate_deduction == 3000.0

    # Strict mathematical identity verification
    assert abs(result.billed_amount - (result.insurer_approved_amount + result.total_disallowed)) < 0.001
    assert abs(result.total_disallowed - (result.legitimate_deduction + result.total_monetary_impact)) < 0.001
    assert abs(result.expected_admissible_amount - (result.billed_amount - result.legitimate_deduction)) < 0.001
    assert abs(result.total_monetary_impact - (result.expected_admissible_amount - result.insurer_approved_amount)) < 0.001

    # Verify Modern Treatment Protection rule failure
    failing_rules = {v.rule_name: v for v in result.rule_verdicts if v.status == "FAIL"}
    assert "Modern Treatment Inpatient Protection Rule" in failing_rules
    mt_verdict = failing_rules["Modern Treatment Inpatient Protection Rule"]
    assert mt_verdict.monetary_impact == 30000.0
    assert mt_verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Clause 4.14" in mt_verdict.finding
    assert "Master Circular" in mt_verdict.regulatory_citation
    assert "MANIPAL" in mt_verdict.actual_claim_fact.upper()
    assert "30,000.00" in mt_verdict.actual_claim_fact


# ==============================================================================
# CROSS-SCENARIO ADVERSARIAL INTEGRATION & IDENTITY MATRIX TESTS
# ==============================================================================

@pytest.mark.parametrize("scenario_idx,expected_patient,expected_hosp,expected_tpa", [
    (1, "Amitabh Verma", "FORTIS", "MDINDIA"),
    (2, "Meenakshi Iyer", "MEDANTA", "FHPL"),
    (3, "Rajesh Kulkarni", "MANIPAL", "MEDI ASSIST"),
])
def test_cross_scenario_zero_hardcoded_fallbacks_matrix(scenario_idx, expected_patient, expected_hosp, expected_tpa):
    """Verify across all 3 scenarios that zero hardcoded fallback strings are triggered."""
    folder_map = {
        1: "scenario_1_fortis_hdfc_mdindia",
        2: "scenario_2_medanta_nivabupa_fhpl",
        3: "scenario_3_manipal_icici_mediassist"
    }
    s_dir = os.path.join(UNSEEN_DIR, folder_map[scenario_idx])
    bill = parse_hospital_bill_pdf(os.path.join(s_dir, "hospital_bill.pdf"))
    pol = parse_insurance_policy_pdf(os.path.join(s_dir, "insurance_policy.pdf"))
    rej = parse_rejection_letter_pdf(os.path.join(s_dir, "rejection_letter.pdf"))

    # Assert fallback strings were never returned
    assert bill.patient_name.value not in ["Unknown Patient", "", None]
    assert bill.bill_id.value not in ["BILL-UNKNOWN", "", None]
    assert bill.hospital_name.value not in ["Hospital", "", None]
    assert bill.diagnosis.value not in ["General Medical Condition", "", None]

    assert pol.policyholder_name.value not in ["Policyholder", "", None]
    assert pol.policy_number.value not in ["POL-UNKNOWN", "", None]
    assert pol.insurer_name.value not in ["Insurance Company", "", None]
    assert pol.policy_version.value not in ["UIN-DEFAULT", "", None]

    assert rej.policyholder_name.value not in ["Policyholder", "", None]
    assert rej.policy_number.value not in ["POL-UNKNOWN", "", None]
    assert rej.claim_number.value not in ["CLAIM-UNKNOWN", "", None]

    # Assert specific scenario identity
    assert expected_patient in bill.patient_name.value
    assert expected_patient in pol.policyholder_name.value
    assert expected_patient in rej.policyholder_name.value
    assert expected_hosp in bill.hospital_name.value.upper()
    assert expected_tpa in getattr(rej.tpa_name, "value", "").upper()


def test_cross_scenario_pipeline_identity_reconciliation():
    """Verify ExtractionPipeline Levenshtein reconciliation across all 3 unseen scenarios."""
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "dummy"})

    folder_map = [
        "scenario_1_fortis_hdfc_mdindia",
        "scenario_2_medanta_nivabupa_fhpl",
        "scenario_3_manipal_icici_mediassist"
    ]
    for s_name in folder_map:
        s_dir = os.path.join(UNSEEN_DIR, s_name)
        bill = parse_hospital_bill_pdf(os.path.join(s_dir, "hospital_bill.pdf"))
        pol = parse_insurance_policy_pdf(os.path.join(s_dir, "insurance_policy.pdf"))
        rej = parse_rejection_letter_pdf(os.path.join(s_dir, "rejection_letter.pdf"))

        recon = pipeline.reconcile_identities(bill, pol, rej)
        assert recon["is_verified"] is True
        assert len(recon["conflicts"]) == 0
        assert recon["similarities"]["bill_patient_vs_rejection"] >= 0.95
        assert recon["similarities"]["policyholder_vs_rejection"] >= 0.95


def test_adversarial_rejection_reason_table_amounts_and_no_duplication(scenario_1_bundle, scenario_2_bundle, scenario_3_bundle):
    """Assert rejection table amounts are dynamically extracted into RejectionReason.amount and never duplicated."""
    bundles = [
        (scenario_1_bundle["rejection"], [55000.0, 25000.0, 2000.0]),
        (scenario_2_bundle["rejection"], [240000.0, 5000.0]),
        (scenario_3_bundle["rejection"], [30000.0, 3000.0]),
    ]
    for rej, expected_amts in bundles:
        assert len(rej.rejection_reasons) == len(expected_amts)
        for reason, exp_amt in zip(rej.rejection_reasons, expected_amts):
            assert reason.amount is not None, f"Amount must be populated on {reason.code.value}"
            assert reason.amount.value == exp_amt, f"Expected {exp_amt}, got {reason.amount.value}"
            desc = reason.description.value
            # Verify no duplication of (Disallowed: ...)
            assert desc.count("Disallowed:") <= 1, f"Duplicated disallowance string found in: {desc}"


def test_adversarial_cumulative_bonus_arbitrary_amounts(scenario_2_bundle):
    """Attack: Test that Cumulative Bonus Protection extracts arbitrary non-hardcoded amounts without [200k, 300k] hack."""
    from app.rules.cumulative_bonus_protection import evaluate_cumulative_bonus_protection
    from app.schemas.provenance import Provenance
    from app.schemas.rejection_letter import RejectionReason
    b, p, r = scenario_2_bundle["bill"], scenario_2_bundle["policy"], scenario_2_bundle["rejection"]

    # 1. Arbitrary amount: Rs. 85,000 (well below 200k-300k range) with accrued bonus in description
    r_test1 = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="BONUS-FORFEIT-01"),
                category=Provenance(value="OTHER"),
                description=Provenance(value="Bonus forfeiture: cumulative bonus of Rs. 500,000 forfeited due to delayed renewal (Disallowed: Rs. 85,000.00)")
            )
        ]
    })
    v1 = evaluate_cumulative_bonus_protection(b, p, r_test1)
    assert v1.status == "FAIL"
    assert v1.monetary_impact == 85000.0, f"Expected 85,000.0, but got {v1.monetary_impact}"

    # 2. Arbitrary amount via RejectionReason.amount: Rs. 350,000 (well above 300k)
    r_test2 = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="BONUS-FORFEIT-01"),
                category=Provenance(value="OTHER"),
                amount=Provenance(value=350000.0),
                description=Provenance(value="Sum Insured Cap / Bonus Forfeiture under Clause 6.1")
            )
        ]
    })
    v2 = evaluate_cumulative_bonus_protection(b, p, r_test2)
    assert v2.status == "FAIL"
    assert v2.monetary_impact == 350000.0, f"Expected 350,000.0, but got {v2.monetary_impact}"


def test_adversarial_modern_treatment_arbitrary_phrasings(scenario_3_bundle):
    """Attack: Test that Modern Treatment Rule extracts arbitrary amounts and handles alternative phrasings."""
    from app.rules.modern_treatment_rule import evaluate_modern_treatment_protection
    from app.schemas.provenance import Provenance
    from app.schemas.rejection_letter import RejectionReason
    b, p, r = scenario_3_bundle["bill"], scenario_3_bundle["policy"], scenario_3_bundle["rejection"]

    # Phrasing with 'deducted' instead of 'disallowed': Rs. 45,000.00 (not hardcoded 15500.0)
    r_test1 = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="MODERN-TREAT-01"),
                category=Provenance(value="OTHER"),
                description=Provenance(value="Endoscopic sub-limit capping applied under Clause 4.14: Rs. 45,000.00 deducted")
            )
        ]
    })
    v1 = evaluate_modern_treatment_protection(b, p, r_test1)
    assert v1.status == "FAIL"
    assert v1.monetary_impact == 45000.0, f"Expected 45,000.0, but got {v1.monetary_impact}"

    # Direct amount via RejectionReason.amount
    r_test2 = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="MODERN-TREAT-01"),
                category=Provenance(value="OTHER"),
                amount=Provenance(value=28000.0),
                description=Provenance(value="Laparoscopic sub-limit day-care cap applied")
            )
        ]
    })
    v2 = evaluate_modern_treatment_protection(b, p, r_test2)
    assert v2.status == "FAIL"
    assert v2.monetary_impact == 28000.0, f"Expected 28,000.0, but got {v2.monetary_impact}"


def test_adversarial_sepsis_and_multiple_surgery_dynamic_extraction(scenario_1_bundle):
    """Attack: Test dynamic extraction in Sepsis and Multiple Surgery rules without hardcoded test constants."""
    from app.rules.sepsis_icu_protocol_rule import evaluate_sepsis_icu_protocol
    from app.rules.multiple_surgery_rule import evaluate_multiple_surgery_protection
    from app.schemas.provenance import Provenance
    from app.schemas.rejection_letter import RejectionReason
    b, p, r = scenario_1_bundle["bill"], scenario_1_bundle["policy"], scenario_1_bundle["rejection"]

    # Sepsis dynamic extraction from rejection reason
    r_sepsis = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="METABOLIC-EXCL-01"),
                category=Provenance(value="PRE_EXISTING"),
                amount=Provenance(value=42000.0),
                description=Provenance(value="Metabolic glycemic ICU protocol repudiated under Excl-18")
            )
        ]
    })
    v_sep = evaluate_sepsis_icu_protocol(b, p, r_sepsis)
    assert v_sep.status == "FAIL"
    assert v_sep.monetary_impact == 42000.0, f"Expected 42,000.0, but got {v_sep.monetary_impact}"

    # Multiple surgery dynamic extraction from rejection reason
    r_multisurg = r.model_copy(update={
        "rejection_reasons": [
            RejectionReason(
                code=Provenance(value="MULTI-SURG-01"),
                category=Provenance(value="PROPORTIONATE_DEDUCTION"),
                amount=Provenance(value=20000.0),
                description=Provenance(value="Secondary procedure 50% cut on OT infrastructure")
            )
        ]
    })
    v_multi = evaluate_multiple_surgery_protection(b, p, r_multisurg)
    assert v_multi.status == "FAIL"
    assert v_multi.monetary_impact == 20000.0, f"Expected 20,000.0, but got {v_multi.monetary_impact}"


def test_adversarial_multi_tier_room_rent_icu_immunity(scenario_1_bundle):
    """
    Attack: Multi-tier room transitions (MICU @ Rs. 15,000/day + Deluxe Room @ Rs. 8,000/day).
    Verify that under IRDAI Chapter V Para 5.4, MICU bed charges are strictly immune
    from room rent proportionate deduction despite exceeding the Rs. 5,000 room limit.
    """
    b = scenario_1_bundle["bill"]
    icu_items = [i for i in b.line_items if "MICU" in i.description.value or "ICU" in i.description.value]
    assert len(icu_items) >= 1
    for icu in icu_items:
        assert icu.is_room_linked is False, "MICU bed charges must never be room-linked"
        # Unit rate is Rs. 15,000, which exceeds Rs. 5,000 limit, but ICU is exempt
        assert icu.unit_rate.value == 15000.0


def test_adversarial_malformed_and_boundary_pdf_inputs():
    """Attack: Pass non-existent, empty, and invalid PDF paths to parser fallbacks to confirm fail-closed safety."""
    invalid_paths = ["", "/non/existent/path/doc.pdf", os.path.join(UNSEEN_DIR, "nonexistent.pdf")]
    for p in invalid_paths:
        assert parse_hospital_bill_pdf(p) is None
        assert parse_insurance_policy_pdf(p) is None
        assert parse_rejection_letter_pdf(p) is None
