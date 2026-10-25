"""
Comprehensive Test Suite for the Universal 3-Stage ClaimGuard Architecture:
- MODEL 1: Universal Forensic Extractor (Dynamic PyMuPDF layout tables, Levenshtein identity matching, arithmetic reconciliation)
- MODEL 2: IRDAI Statutory Policy Auditor (Master Circular 2024, Annexure A Lists I-IV, Moratorium, Grace Period, Mental Health)
- MODEL 3: Cross-Document Adjudicator & Reconciler (FinancialMath paisa precision, 5 forensic pillars)
"""

import os
import pytest
from app.extraction.pdf_parser_fallback import (
    parse_hospital_bill_pdf,
    parse_insurance_policy_pdf,
    parse_rejection_letter_pdf,
    _is_room_linked,
    _normalize_category,
)
from app.utils.text_matching import (
    strip_honorifics,
    levenshtein_distance,
    levenshtein_similarity,
    match_names,
)
from app.extraction.pipeline import ExtractionPipeline
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import (
    InsurancePolicy,
    ProportionateDeductionRuleConfig,
)
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.statutory_policy_auditor import audit_statutory_policy_compliance
from app.rules.cross_document_adjudication import evaluate_cross_document_adjudication
from app.rules.proportionate_deduction import evaluate_proportionate_deduction
from app.rules.engine import RuleEngine


def prov(val):
    return Provenance(value=val)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
COMPLEX_DIR = os.path.join(PROJECT_ROOT, "test_docs", "complex_claim_case")
ULTRA_DIR = os.path.join(PROJECT_ROOT, "test_docs", "ultra_hard_claim_case")
BENCH_DIR = os.path.join(BASE_DIR, "tests", "benchmark", "benchmark_dataset")


# =============================================================================
# MODEL 1: Dynamic Layout Table Parser Tests
# =============================================================================

def test_dynamic_parser_apollo_hospital_bill():
    pdf_path = os.path.join(COMPLEX_DIR, "apollo_hospital_bill.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Apollo hospital bill PDF not found")

    bill = parse_hospital_bill_pdf(pdf_path)
    assert bill is not None
    assert "Vikramaditya" in bill.patient_name.value
    assert "APOLLO" in bill.hospital_name.value.upper()
    assert bill.total_amount.value == 548750.0
    assert bill.arithmetic_verified is True
    assert len(bill.line_items) == 28

    # ICU charges must NEVER be room-linked
    sicu_items = [i for i in bill.line_items if any(w in i.description.value.upper() for w in ["SICU", "ICU"])]
    assert len(sicu_items) >= 2
    for item in sicu_items:
        assert item.is_room_linked is False

    # Ward bed accommodation charges must be room-linked
    ward_items = [i for i in bill.line_items if "AC ROOM" in i.description.value.upper()]
    assert len(ward_items) >= 1
    for item in ward_items:
        assert item.is_room_linked is True


def test_dynamic_parser_max_hospital_bill():
    pdf_path = os.path.join(ULTRA_DIR, "max_hospital_bill.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Max hospital bill PDF not found")

    bill = parse_hospital_bill_pdf(pdf_path)
    assert bill is not None
    assert "Rajeshwari" in bill.patient_name.value
    assert "MAX" in bill.hospital_name.value.upper()
    assert bill.total_amount.value == 785600.0
    assert bill.arithmetic_verified is True
    assert len(bill.line_items) == 32

    # SICU/ICU charges must not be room-linked
    sicu_items = [i for i in bill.line_items if any(w in i.description.value.upper() for w in ["SICU", "ICU"])]
    assert len(sicu_items) >= 2
    for item in sicu_items:
        assert item.is_room_linked is False


def test_dynamic_parser_benchmark_case_1():
    pdf_path = os.path.join(BENCH_DIR, "case_001_baseline_correct", "hospital_bill.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Benchmark case 1 PDF not found")

    bill = parse_hospital_bill_pdf(pdf_path)
    assert bill is not None
    assert "John Doe" in bill.patient_name.value
    assert bill.total_amount.value == 50000.0
    assert bill.arithmetic_verified is True
    assert len(bill.line_items) >= 1


def test_dynamic_parser_policies():
    star_pdf = os.path.join(COMPLEX_DIR, "star_comprehensive_policy.pdf")
    if os.path.exists(star_pdf):
        p1 = parse_insurance_policy_pdf(star_pdf)
        assert p1 is not None
        assert "Vikramaditya" in p1.policyholder_name.value
        assert p1.sum_insured.value == 1250000.0
        assert p1.room_rent_limit_per_day.value == 6000.0
        assert p1.moratorium_period_months.value == 60

    care_pdf = os.path.join(ULTRA_DIR, "care_supreme_policy.pdf")
    if os.path.exists(care_pdf):
        p2 = parse_insurance_policy_pdf(care_pdf)
        assert p2 is not None
        assert "Rajeshwari" in p2.policyholder_name.value
        assert p2.sum_insured.value == 1200000.0
        assert p2.cumulative_bonus.value == 400000.0


def test_dynamic_parser_rejections():
    medi_pdf = os.path.join(COMPLEX_DIR, "mediassist_rejection_letter.pdf")
    if os.path.exists(medi_pdf):
        r1 = parse_rejection_letter_pdf(medi_pdf)
        assert r1 is not None
        assert "Vikramaditya" in r1.policyholder_name.value
        assert r1.total_claimed.value == 548750.0
        assert r1.total_approved.value == 216200.0
        assert r1.total_deducted.value == 332550.0
        assert len(r1.rejection_reasons) > 0

    vidal_pdf = os.path.join(ULTRA_DIR, "vidal_rejection_letter.pdf")
    if os.path.exists(vidal_pdf):
        r2 = parse_rejection_letter_pdf(vidal_pdf)
        assert r2 is not None
        assert "Rajeshwari" in r2.policyholder_name.value
        assert r2.total_claimed.value == 785600.0
        assert r2.total_approved.value == 338100.0
        assert r2.total_deducted.value == 447500.0
        assert len(r2.rejection_reasons) > 0


# =============================================================================
# MODEL 1: Levenshtein Matching & Identity Normalization
# =============================================================================

def test_honorific_stripping():
    assert strip_honorifics("Mr. Vikramaditya Singhania") == "Vikramaditya Singhania"
    assert strip_honorifics("Mrs. Rajeshwari Sundaram") == "Rajeshwari Sundaram"
    assert strip_honorifics("Dr. Rajesh Sharma") == "Rajesh Sharma"
    assert strip_honorifics("Shri Amit Patel") == "Amit Patel"
    assert strip_honorifics("Smt. Kamala Devi") == "Kamala Devi"


def test_levenshtein_similarity():
    sim = levenshtein_similarity("Vikramaditya", "Vikramaditiya")
    assert sim >= 0.90
    sim_diff = levenshtein_similarity("Vikramaditya", "Anita")
    assert sim_diff < 0.50


def test_fuzzy_name_matching():
    # Exact with different honorifics
    assert match_names("Mr. Vikramaditya Singhania", "Vikramaditya Singhania") is True
    assert match_names("Mrs. Rajeshwari Sundaram", "Rajeshwari Sundaram") is True
    # Minor OCR/spelling variation
    assert match_names("Vikramaditya Singhania", "Vikramadityaa Singhania") is True
    # Distinct names must not match
    assert match_names("Rajesh Sharma", "Anita Desai") is False


def test_pipeline_arithmetic_reconciliation():
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "dummy"})

    # Matching sum
    good_bill = HospitalBill(
        bill_id=prov("B1"),
        total_amount=prov(1000.0),
        subtotal=prov(1000.0),
        line_items=[
            BillLineItem(item_code=prov("I1"), description=prov("Ward"), category=prov("ROOM"), quantity=prov(1.0), unit_rate=prov(600.0), amount=prov(600.0)),
            BillLineItem(item_code=prov("I2"), description=prov("Meds"), category=prov("PHARMACY"), quantity=prov(1.0), unit_rate=prov(400.0), amount=prov(400.0)),
        ]
    )
    status, issues = pipeline._validate_extraction("bill", good_bill)
    assert status == "SUCCESS"
    assert "ARITHMETIC_MISMATCH" not in issues
    assert good_bill.arithmetic_verified is True

    # Mismatched sum
    bad_bill = HospitalBill(
        bill_id=prov("B2"),
        total_amount=prov(1500.0),
        subtotal=prov(1500.0),
        line_items=[
            BillLineItem(item_code=prov("I1"), description=prov("Ward"), category=prov("ROOM"), quantity=prov(1.0), unit_rate=prov(600.0), amount=prov(600.0)),
        ]
    )
    status, issues = pipeline._validate_extraction("bill", bad_bill)
    assert status == "NEEDS_REVIEW"
    assert "ARITHMETIC_MISMATCH" in issues
    assert bad_bill.arithmetic_verified is False


# =============================================================================
# MODEL 2: IRDAI Statutory Policy Auditor Tests
# =============================================================================

def test_statutory_auditor_compliant_policy():
    policy = InsurancePolicy(
        policy_number=prov("POL-VALID-01"),
        sum_insured=prov(1000000.0),
        moratorium_period_months=prov(60),
        covers_mental_health=prov(True)
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"
    assert verdict.actual_claim_fact is not None
    assert verdict.applicable_policy_rule is not None
    assert verdict.insurer_applied_action is not None
    assert verdict.expected_action is not None
    assert verdict.evidence is not None


def test_statutory_auditor_ultra_vires_proportionate_deduction():
    rule_config = ProportionateDeductionRuleConfig(
        threshold_value=prov(1.0),
        threshold_operator=prov(">"),
        threshold_source_type=prov("POLICY_WORDING"),
        policy_clause=prov("Clause 4.1"),
        source_text=prov("Room rent ratio applies to entire bill including ICU, OT, pharmacy, and implants without exception")
    )
    policy = InsurancePolicy(
        policy_number=prov("POL-BREACH-01"),
        sum_insured=prov(1000000.0),
        proportionate_deduction_rule=rule_config
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "ULTRA VIRES" in verdict.finding
    assert "Para 5.4" in verdict.finding


def test_statutory_auditor_ultra_vires_moratorium():
    policy = InsurancePolicy(
        policy_number=prov("POL-BREACH-02"),
        sum_insured=prov(1000000.0),
        moratorium_period_months=prov(84) # 84 months exceeds 60-month cap
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "84 months vs statutory 60 months" in verdict.finding


def test_statutory_auditor_ultra_vires_bonus_forfeiture():
    policy = InsurancePolicy(
        policy_number=prov("POL-BREACH-03"),
        sum_insured=prov(1000000.0),
        deduction_order_clause=prov("Clause 6: Delayed premium payment forfeits bonus even if paid in grace period")
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "Regulation 13" in verdict.finding


def test_statutory_auditor_ultra_vires_mental_health():
    policy = InsurancePolicy(
        policy_number=prov("POL-BREACH-04"),
        sum_insured=prov(1000000.0),
        covers_mental_health=prov(False)
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "Mental Health Exclusion" in verdict.finding


# =============================================================================
# MODEL 3: Cross-Document Adjudicator & Reconciler Tests
# =============================================================================

def test_cross_document_adjudication_forensic_pillars():
    bill = HospitalBill(
        bill_id=prov("B100"),
        total_amount=prov(20000.0),
        subtotal=prov(20000.0),
        line_items=[
            BillLineItem(item_code=prov("I1"), description=prov("Ward Room"), category=prov("ROOM"), quantity=prov(2.0), unit_rate=prov(10000.0), amount=prov(20000.0))
        ]
    )
    policy = InsurancePolicy(
        policy_number=prov("POL100"),
        sum_insured=prov(500000.0)
    )
    rejection = RejectionLetter(
        policy_number=prov("POL100"),
        claim_number=prov("CLM100"),
        total_claimed=prov(20000.0),
        total_approved=prov(12000.0),
        total_deducted=prov(8000.0),
        rejection_reasons=[
            RejectionReason(code=prov("PROP-01"), category=prov("PROPORTIONATE_DEDUCTION"), description=prov("Proportionate cut on room charges"))
        ]
    )

    verdict = evaluate_cross_document_adjudication(bill, policy, rejection)
    assert verdict.status == "NEEDS_REVIEW"
    assert verdict.difference == 8000.0
    assert verdict.monetary_impact == 8000.0
    assert "20000.0" in verdict.actual_claim_fact
    assert "12000.0" in verdict.actual_claim_fact
    assert "PROPORTIONATE_DEDUCTION" in verdict.applicable_policy_rule
    assert "8000.0" in verdict.insurer_applied_action
    assert "Expected approval" in verdict.expected_action
    assert verdict.evidence is not None
    assert len(verdict.evidence_entries) >= 1


def test_pipeline_levenshtein_identity_reconciliation():
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "dummy"})

    # Matching names with honorific differences
    bill_match = HospitalBill(bill_id=prov("B1"), patient_name=prov("Mr. Amitabh Verma"), total_amount=prov(1000.0))
    pol_match = InsurancePolicy(policy_number=prov("P1"), policyholder_name=prov("Amitabh Verma"), sum_insured=prov(500000.0))
    rej_match = RejectionLetter(claim_number=prov("C1"), policyholder_name=prov("Amitabh Verma"), total_claimed=prov(1000.0), total_approved=prov(1000.0))

    recon = pipeline.reconcile_identities(bill_match, pol_match, rej_match)
    assert recon["is_verified"] is True
    assert len(recon["conflicts"]) == 0
    assert recon["similarities"]["bill_patient_vs_rejection"] >= 0.99
    assert recon["normalized_names"]["bill_patient"] == "Amitabh Verma"

    # Conflicting names (<80% similarity)
    bill_mismatch = HospitalBill(bill_id=prov("B2"), patient_name=prov("Dr. Ramesh Gupta"), total_amount=prov(2000.0))
    recon_bad = pipeline.reconcile_identities(bill_mismatch, pol_match, rej_match)
    assert recon_bad["is_verified"] is False
    assert len(recon_bad["conflicts"]) >= 1
    assert "Ramesh Gupta" in recon_bad["conflicts"][0]
    assert recon_bad["similarities"]["bill_patient_vs_rejection"] < 0.80


def test_proportionate_deduction_forensic_pillars():
    bill = HospitalBill(
        bill_id=prov("B-DELUXE-01"),
        hospital_name=prov("Fortis Memorial Research Institute"),
        total_amount=prov(100000.0),
        subtotal=prov(100000.0),
        line_items=[
            BillLineItem(item_code=prov("I1"), description=prov("Deluxe Room"), category=prov("ROOM"), quantity=prov(5.0), unit_rate=prov(10000.0), amount=prov(50000.0), is_room_linked=True),
            BillLineItem(item_code=prov("I2"), description=prov("Nursing"), category=prov("NURSING"), quantity=prov(5.0), unit_rate=prov(2000.0), amount=prov(10000.0), is_room_linked=True),
            BillLineItem(item_code=prov("I3"), description=prov("Pharmacy"), category=prov("PHARMACY"), quantity=prov(1.0), unit_rate=prov(40000.0), amount=prov(40000.0), is_room_linked=False),
        ]
    )
    policy = InsurancePolicy(
        policy_number=prov("POL-FORTIS-01"),
        insurer_name=prov("HDFC ERGO General Insurance"),
        sum_insured=prov(1000000.0),
        room_rent_limit_per_day=prov(5000.0),
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=prov(1.0),
            threshold_operator=prov(">"),
            threshold_source_type=prov("POLICY_WORDING"),
            policy_clause=prov("Clause 3.1")
        )
    )
    rejection = RejectionLetter(
        policy_number=prov("POL-FORTIS-01"),
        claim_number=prov("CLM-FORTIS-01"),
        total_claimed=prov(100000.0),
        total_approved=prov(40000.0),
        total_deducted=prov(60000.0) # Insurer deducted 60,000 (applying ratio across entire bill)
    )

    verdict = evaluate_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.actual_claim_fact is not None
    assert "Fortis Memorial" in verdict.actual_claim_fact or "Fortis Memorial" in verdict.evidence
    assert verdict.applicable_policy_rule is not None
    assert "Master Circular" in verdict.applicable_policy_rule
    assert verdict.insurer_applied_action is not None
    assert verdict.expected_action is not None
    assert verdict.evidence is not None


def test_statutory_auditor_mental_health_exclusion_text():
    policy = InsurancePolicy(
        policy_number=prov("POL-MH-EXCL"),
        sum_insured=prov(1000000.0),
        exclusions=[prov("Exclusion 14: Mental illness, psychiatric conditions and disorders are excluded")]
    )
    verdict = audit_statutory_policy_compliance(None, policy, None)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "Mental Health Exclusion" in verdict.finding

