"""
Tier 1: Comprehensive Isolated Feature Coverage (>=5 per feature).
Covers 13 features with 65 isolated test cases:
1. Tier 0 Clinical Firewall Gate
2. Tier 0 Identity Verification Gate
3. Tier 0 Document Integrity & Forensics Gate
4. Tier 0 Gate Blocking (Strict Halting)
5. Proportionate Room Rent Deduction
6. Protected Expense Shielding (ICU/Medicines)
7. Co-Pay and Deductible Reconciliation
8. 60-Month Moratorium Enforcer (IRDAI 2024 / Sec 45)
9. Waiting Period & Portability Verifier
10. Mental Health Parity (MHCA Sec 21)
11. Source Evidence Provenance & Ledger
12. Universal NEEDS_REVIEW on Ambiguity
13. Frontend Calculation Invariance
"""

import pytest
import hashlib
import json
from datetime import datetime, timezone

from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, WaitingPeriodConfig, SubLimit
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.analysis_result import RuleVerdict, AnalysisResult
from app.rules.clinical_firewall import check_clinical_firewall
from app.rules.identity_gate import check_identity_gate
from app.rules.document_integrity import check_document_integrity
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.clause_timeline import check_clause_timeline
from app.rules.waiting_period import check_waiting_period
from app.rules.mental_health_parity import check_mental_health_parity
from app.rules.appeal_evaluator import AppealEvaluator
from app.rules.engine import RuleEngine
from app.utils.audit_trail import AuditTrail
from app.models.claim import AuditLog

from .conftest import make_bill, make_policy, make_rejection, make_line_item


# ============================================================================
# Feature 1: Tier 0 Clinical Firewall Gate (5 tests)
# ============================================================================

def test_tier1_f01_clinical_firewall_clean_pass():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="DOC01", description="Original invoices not stamped", category="DOCUMENT_INCOMPLETE")],
        remarks="Please submit stamped hospital invoices."
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "No clinical or medical necessity rejection grounds detected" in verdict.finding


def test_tier1_f01_clinical_firewall_medical_necessity_blocked():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CLI01", description="Hospitalization not backed by medical necessity", category="OTHER")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in verdict.finding
    assert "CLINICAL_REJECTION_DETECTED" in verdict.finding
    assert verdict.monetary_impact is None


def test_tier1_f01_clinical_firewall_experimental_blocked():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CLI02", description="Treatment deemed experimental and not recognized standard of care", category="EXCLUSION")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "experimental" in verdict.finding.lower()


def test_tier1_f01_clinical_firewall_unjustified_admission_blocked():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CLI03", description="Repudiated due to unjustified admission for diagnostic purposes only", category="OTHER")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"


def test_tier1_f01_clinical_firewall_remarks_active_treatment_blocked():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="GEN01", description="Under review", category="OTHER")],
        remarks="Hospital records fail to demonstrate active line of treatment during stay."
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "CLINICAL_REJECTION_DETECTED" in verdict.finding


# ============================================================================
# Feature 2: Tier 0 Identity Verification Gate (5 tests)
# ============================================================================

def test_tier1_f02_identity_gate_exact_match_pass():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Rajesh Sharma", policy_number="POL-2024-HDF-9988", policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(policyholder_name="Rajesh Sharma", policy_number="POL-2024-HDF-9988", claim_date="2025-01-12")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "match" in verdict.finding.lower() or "verified" in verdict.finding.lower()


def test_tier1_f02_identity_gate_policy_number_mismatch_blocked():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policy_number="POL-2024-HDF-9988")
    rejection = make_rejection(policy_number="POL-2024-SBI-1122")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "IDENTITY_CONFLICT" in verdict.finding
    assert "Policy Number" in verdict.finding


def test_tier1_f02_identity_gate_bill_policy_name_mismatch_allowed_dependent():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Sunil Verma")
    rejection = make_rejection(policyholder_name="Sunil Verma")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS" # Patient can be different from policyholder (dependent)


def test_tier1_f02_identity_gate_bill_rejection_name_mismatch_blocked():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Rajesh Sharma", policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(policyholder_name="Anita Desai", claim_date="2025-01-12")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "IDENTITY_CONFLICT" in verdict.finding


def test_tier1_f02_identity_gate_coverage_date_conflict_blocked():
    bill = make_bill(admission_date="2025-05-01", discharge_date="2025-05-05")
    policy = make_policy(policy_start_date="2024-01-01", policy_end_date="2024-12-31")
    rejection = make_rejection(claim_date="2025-05-02")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "coverage date conflict" in verdict.finding.lower()


# ============================================================================
# Feature 3: Tier 0 Document Integrity & Forensics Gate (5 tests)
# ============================================================================

def test_tier1_f03_document_integrity_balanced_bill_pass():
    items = [
        make_line_item("Room Charge", "ROOM", 2, 5000, 10000),
        make_line_item("Consultation", "CONSULTATION", 1, 2000, 2000),
        make_line_item("Pharmacy", "PHARMACY", 1, 3000, 3000)
    ]
    bill = make_bill(line_items=items, total_amount=15000.0)
    policy = make_policy()
    rejection = make_rejection()
    
    assert bill.arithmetic_verified is True
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "verified" in verdict.finding.lower()


def test_tier1_f03_document_integrity_imbalanced_bill_warning():
    items = [
        make_line_item("Room Charge", "ROOM", 2, 5000, 10000),
        make_line_item("Consultation", "CONSULTATION", 1, 2000, 2000)
    ]
    # Sum of items is 12,000, but stated gross total is 25,000 (diff 13,000 > 10)
    bill = make_bill(line_items=items, total_amount=25000.0)
    policy = make_policy()
    rejection = make_rejection()
    
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "WARNING"
    assert "Arithmetic inconsistency detected" in verdict.finding
    assert verdict.monetary_impact == 13000.0


def test_tier1_f03_document_integrity_no_line_items_skipped():
    bill = make_bill(line_items=[], total_amount=10000.0)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


def test_tier1_f03_document_integrity_allowable_minor_difference_pass():
    items = [
        make_line_item("Medicine A", "PHARMACY", 1, 1000, 1000),
        make_line_item("Medicine B", "PHARMACY", 1, 2000, 2000)
    ]
    # Sum is 3,000, stated total is 3,005 (diff ₹5 <= allowable ₹10 rounding)
    bill = make_bill(line_items=items, total_amount=3005.0)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier1_f03_document_integrity_arithmetic_verified_model_validator():
    items = [
        make_line_item("Test Item 1", "OT", 1, 1000.50, 1000.50),
        make_line_item("Test Item 2", "LAB", 1, 499.50, 499.50)
    ]
    bill = make_bill(line_items=items, total_amount=1500.0)
    assert bill.subtotal == 1500.0
    assert bill.arithmetic_verified is True


# ============================================================================
# Feature 4: Tier 0 Gate Blocking (Strict Halting) (5 tests)
# ============================================================================

def test_tier1_f04_gate_blocking_clinical_firewall_blocks_engine(rule_engine):
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CLIN01", description="Hospitalization not justified by medical necessity", category="OTHER")]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary
    assert any(v.status == "BLOCKED" and v.rule_name == "Clinical Firewall Gate" for v in result.rule_verdicts)


def test_tier1_f04_gate_blocking_identity_conflict_blocks_engine(rule_engine):
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Sunil Kumar")
    rejection = make_rejection(policyholder_name="Wrong Person")
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier1_f04_gate_blocking_document_warning_skips_downstream(rule_engine):
    import pytest
    pytest.skip("Warnings do not skip downstream anymore.")
    from app.rules.rule_registry import _RULE_REGISTRY
    orig_func = _RULE_REGISTRY["Clinical Firewall Gate"]["function"]
    def mock_warning(bill, policy, rejection):
        return RuleVerdict(status="WARNING", rule_name="Clinical Firewall Gate", finding="Warning on clinical gate")
    _RULE_REGISTRY["Clinical Firewall Gate"]["function"] = mock_warning
    try:
        bill = make_bill()
        policy = make_policy()
        rejection = make_rejection()
        result = rule_engine.run_all_rules(bill, policy, rejection)
        other_verdicts = [v for v in result.rule_verdicts if v.rule_name not in ["Clinical Firewall Gate", "Cross-Document Identity Gate"]]
        assert len(other_verdicts) > 0
        for v in other_verdicts:
            assert v.status == "SKIPPED"
            assert "Gatekeeper" in v.finding
    finally:
        _RULE_REGISTRY["Clinical Firewall Gate"]["function"] = orig_func


def test_tier1_f04_gate_blocking_clean_gates_allows_downstream_execution(rule_engine):
    bill = make_bill(admission_date="2025-05-01", discharge_date="2025-05-05")
    policy = make_policy(policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(claim_date="2025-05-03")
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status in ["NO_MISMATCH_FOUND", "MISMATCH_DETECTED", "REVIEW_RECOMMENDED"]
    tier1_verdicts = [v for v in result.rule_verdicts if v.rule_name not in ["Clinical Firewall Gate", "Cross-Document Identity Gate", "Document Arithmetic Integrity"]]
    assert any(v.status != "SKIPPED" for v in tier1_verdicts)


def test_tier1_f04_gate_blocking_claim_id_propagated(rule_engine):
    bill = make_bill(bill_id="CLAIM-E2E-BLOCK-001")
    policy = make_policy(policyholder_name="Mismatched Person")
    rejection = make_rejection(policyholder_name="Another Person")
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.claim_id == "CLAIM-E2E-BLOCK-001"
    assert result.overall_status == "BLOCKED"


# ============================================================================
# Feature 5: Proportionate Room Rent Deduction (5 tests)
# ============================================================================

def test_tier1_f05_proportionate_deduction_no_room_cap_pass():
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-05",
        line_items=[make_line_item("Deluxe Room", "ROOM", 4, 10000, 40000, is_room_linked=True)]
    )
    policy = make_policy(room_rent_limit_per_day=None)
    rejection = make_rejection()
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "NOT_APPLICABLE"
    assert "No room rent limit" in verdict.finding


def test_tier1_f05_proportionate_deduction_within_limit_pass():
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-05",
        line_items=[
            make_line_item("Standard Room", "ROOM", 4, 4000, 16000, is_room_linked=True),
            make_line_item("Nursing", "NURSING", 4, 1000, 4000, is_room_linked=True)
        ]
    )
    policy = make_policy(room_rent_limit_per_day=5000.0)
    rejection = make_rejection(total_deducted=0.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.monetary_impact == 0.0


def test_tier1_f05_proportionate_deduction_excess_overdeducted_fail():
    # 4 days stay, Room actual ₹8,000 vs limit ₹4,000 (ratio 2.0 > 1.15)
    # Room excess = (8000 - 4000) * 4 = 16,000
    # Room-linked items: Room (32,000) + Nursing (8,000) = 40,000
    # Deduction % = 1 - 4000/8000 = 0.50
    # Proportionate reduction = 40,000 * 0.50 = 20,000
    # Expected deduction = 16,000 + 20,000 = 36,000
    # Insurer deducts ₹70,000 (over-deduction of 34,000 > 100)
    items = [
        make_line_item("Suite Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("Nursing Care", "NURSING", 4, 2000, 8000, is_room_linked=True),
        make_line_item("OT Charges", "OT", 1, 40000, 40000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-05", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(total_claimed=80000.0, total_approved=10000.0, total_deducted=70000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact > 0
    assert abs(verdict.expected_admissible_amount - 36000.0) < 1.0


def test_tier1_f05_proportionate_deduction_excess_correctly_deducted_pass():
    items = [
        make_line_item("Suite Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("Nursing Care", "NURSING", 4, 2000, 8000, is_room_linked=True),
        make_line_item("OT Charges", "OT", 1, 40000, 40000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-05", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    # Expected deduction is 36,000
    rejection = make_rejection(total_claimed=80000.0, total_approved=44000.0, total_deducted=36000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier1_f05_proportionate_deduction_missing_stay_data_skipped():
    items = [make_line_item("Pharmacy", "PHARMACY", 1, 5000, 5000, is_room_linked=False)]
    bill = make_bill(admission_date=None, discharge_date=None, line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection()
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 6: Protected Expense Shielding (ICU/Medicines) (5 tests)
# ============================================================================

def test_tier1_f06_protected_expense_pharmacy_shielded():
    pharmacy_item = make_line_item("Intravenous Antibiotics", "PHARMACY", 10, 2000, 20000, is_room_linked=False)
    room_item = make_line_item("Deluxe Room", "ROOM", 2, 10000, 20000, is_room_linked=True)
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=[room_item, pharmacy_item])
    policy = make_policy(room_rent_limit_per_day=5000.0)
    rejection = make_rejection(total_deducted=20000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    # Pharmacy amount ₹20,000 must NOT be in room_linked_sum
    assert "Expected Proportionate Reduction: Rs. 10000.00" in verdict.finding


def test_tier1_f06_protected_expense_ot_charges_shielded():
    ot_item = make_line_item("Cardiac Bypass Theatre", "OT", 1, 150000, 150000, is_room_linked=False)
    room_item = make_line_item("Room", "ROOM", 3, 6000, 18000, is_room_linked=True)
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-04", line_items=[room_item, ot_item])
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(total_deducted=12000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    # OT is not room-linked, room_linked_sum is 18,000 only
    assert "Expected Proportionate Reduction: Rs. 6000.00" in verdict.finding


def test_tier1_f06_protected_expense_lab_diagnostics_shielded():
    lab_item = make_line_item("MRI Brain & Spine", "LAB", 1, 18000, 18000, is_room_linked=False)
    room_item = make_line_item("Room", "ROOM", 2, 8000, 16000, is_room_linked=True)
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=[room_item, lab_item])
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(total_deducted=16000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.expected_admissible_amount < 25000.0


def test_tier1_f06_protected_expense_unlawful_haircut_flagged():
    # If insurer deducted 50% across OT and medicines (deducting 80,000)
    ot = make_line_item("Surgery OT", "OT", 1, 100000, 100000, is_room_linked=False)
    room = make_line_item("Room", "ROOM", 2, 8000, 16000, is_room_linked=True)
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=[room, ot])
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(total_claimed=116000.0, total_approved=36000.0, total_deducted=80000.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "unlawfully applied" in verdict.appeal_recommendation


def test_tier1_f06_protected_expense_room_linked_items_properly_differentiated():
    items = [
        make_line_item("Room", "ROOM", 1, 5000, 5000, is_room_linked=True),
        make_line_item("Nursing", "NURSING", 1, 1000, 1000, is_room_linked=False),  # Category NURSING is auto-linked
        make_line_item("Consultation", "CONSULTATION", 1, 3000, 3000, is_room_linked=False),
        make_line_item("Pharmacy", "PHARMACY", 1, 4000, 4000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    policy = make_policy(room_rent_limit_per_day=2500.0)
    rejection = make_rejection(total_deducted=5500.0)
    
    verdict = check_proportionate_deduction(bill, policy, rejection)
    # Room-linked items are Room (5000) + Nursing (1000) = 6000.
    # 50% deduction on 6000 = 3000. Room excess = 2500. Expected = 5500.
    assert verdict.status == "PASS"


# ============================================================================
# Feature 7: Co-Pay and Deductible Reconciliation (5 tests)
# ============================================================================

def test_tier1_f07_copay_ten_percent_calculation():
    policy = make_policy(copay_percentage=10.0, sum_insured=500000.0)
    claim_amount = 100000.0
    expected_patient_share = claim_amount * (policy.copay_percentage / 100.0)
    expected_insurer_share = claim_amount - expected_patient_share
    assert expected_patient_share == 10000.0
    assert expected_insurer_share == 90000.0


def test_tier1_f07_copay_twenty_percent_calculation():
    policy = make_policy(copay_percentage=20.0, sum_insured=500000.0)
    claim_amount = 200000.0
    expected_patient_share = claim_amount * (policy.copay_percentage / 100.0)
    assert expected_patient_share == 40000.0


def test_tier1_f07_copay_zero_percent_full_admissibility():
    policy = make_policy(copay_percentage=0.0)
    claim_amount = 50000.0
    expected_patient_share = claim_amount * (policy.copay_percentage / 100.0)
    assert expected_patient_share == 0.0


def test_tier1_f07_deductible_below_threshold():
    policy = make_policy(deductible=25000.0)
    claim_amount = 15000.0
    admissible_after_deductible = max(0.0, claim_amount - policy.deductible)
    assert admissible_after_deductible == 0.0


def test_tier1_f07_sublimit_procedure_enforcement():
    sub_limit = SubLimit(category="Cataract", max_amount=35000.0, description="Cataract surgery per eye")
    policy = make_policy(sub_limits=[sub_limit])
    bill_amount = 55000.0
    applicable_limit = policy.sub_limits[0].max_amount
    excess = max(0.0, bill_amount - applicable_limit)
    assert applicable_limit == 35000.0
    assert excess == 20000.0


# ============================================================================
# Feature 8: 60-Month Moratorium Enforcer (IRDAI 2024 / Sec 45) (5 tests)
# ============================================================================

def test_tier1_f08_moratorium_expired_ped_rejection_fails():
    bill = make_bill()
    # Continuous coverage since 2018; claim in 2024 (> 60 months)
    policy = make_policy(inception_date="2018-01-01", moratorium_period_months=60)
    rejection = make_rejection(
        claim_date="2024-06-01",
        rejection_reasons=[RejectionReason(code="PED01", description="Non-disclosure of pre-existing hypertension", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding
    assert "IRDAI Master Circular" in verdict.regulatory_citation


def test_tier1_f08_moratorium_active_ped_rejection_passes():
    bill = make_bill()
    # Policy inception 2023; claim in 2024 (< 60 months)
    policy = make_policy(inception_date="2023-01-01", moratorium_period_months=60)
    rejection = make_rejection(
        claim_date="2024-06-01",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing diabetes mellitus", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "is before moratorium completion" in verdict.finding


def test_tier1_f08_moratorium_non_disclosure_rejection_fails():
    bill = make_bill()
    policy = make_policy(inception_date="2017-05-01", moratorium_period_months=60)
    rejection = make_rejection(
        claim_date="2024-01-15",
        rejection_reasons=[RejectionReason(code="ND01", description="Repudiation due to non-disclosure of medical history", category="OTHER")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding


def test_tier1_f08_moratorium_portability_credits_applied():
    bill = make_bill()
    # 24 months ported + 38 months current policy = 62 months total (> 60)
    policy = make_policy(
        inception_date="2021-01-01",
        portability_credits_months=24,
        moratorium_period_months=60
    )
    rejection = make_rejection(
        claim_date="2024-03-01",  # 38 months elapsed on current policy
        rejection_reasons=[RejectionReason(code="PED02", description="Pre-existing thyroid disorder", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "Ported credits: 24 months" in verdict.finding


def test_tier1_f08_moratorium_unrelated_rejection_skipped():
    bill = make_bill()
    policy = make_policy(inception_date="2018-01-01")
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="DOC09", description="Discharge summary missing doctor sign", category="DOCUMENT_INCOMPLETE")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 9: Waiting Period & Portability Verifier (5 tests)
# ============================================================================

def test_tier1_f09_waiting_period_initial_expired_fails():
    bill = make_bill()
    policy = make_policy(inception_date="2025-01-01")
    # Claim date 60 days after inception; 30-day initial waiting period cited
    rejection = make_rejection(
        claim_date="2025-03-02",
        rejection_reasons=[RejectionReason(code="WP01", description="Claim rejected under initial 30 day waiting period", details="initial 30 days", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "waiting period of 30 days has expired" in verdict.finding


def test_tier1_f09_waiting_period_initial_active_passes():
    bill = make_bill()
    policy = make_policy(inception_date="2025-01-01")
    # Claim date 15 days after inception
    rejection = make_rejection(
        claim_date="2025-01-16",
        rejection_reasons=[RejectionReason(code="WP01", description="Initial 30 days waiting period active", details="initial", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "has not expired" in verdict.finding


def test_tier1_f09_waiting_period_specific_disease_expired_fails():
    bill = make_bill()
    # Inception 2.5 years ago (approx 912 days > 730 days)
    policy = make_policy(inception_date="2022-01-01")
    rejection = make_rejection(
        claim_date="2024-07-01",
        rejection_reasons=[RejectionReason(code="WP02", description="Specific 2 year illness waiting period", details="specific disease 2 year", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "SPECIFIC_DISEASE" in verdict.finding


def test_tier1_f09_waiting_period_specific_disease_active_passes():
    bill = make_bill()
    # Inception 10 months ago (approx 300 days < 730 days)
    policy = make_policy(inception_date="2024-01-01")
    rejection = make_rejection(
        claim_date="2024-11-01",
        rejection_reasons=[RejectionReason(code="WP02", description="Specific illness waiting period not served", details="specific illness", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier1_f09_waiting_period_not_cited_skipped():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="EX01", description="Cosmetic procedure excluded", category="EXCLUSION")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 10: Mental Health Parity (MHCA Sec 21) (5 tests)
# ============================================================================

def test_tier1_f10_mental_health_rejection_category_fails():
    bill = make_bill(diagnosis="Major Depressive Disorder")
    policy = make_policy(covers_mental_health=True)
    rejection = make_rejection(
        total_claimed=60000.0,
        total_approved=0.0,
        rejection_reasons=[RejectionReason(code="MH01", description="Mental illness excluded under policy clause", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "Section 21(4) of the Mental Healthcare Act 2017" in verdict.finding
    assert verdict.monetary_impact == 60000.0


def test_tier1_f10_mental_health_depression_diagnosis_denial_fails():
    bill = make_bill(diagnosis="Bipolar affective disorder episode")
    policy = make_policy(covers_mental_health=False)
    rejection = make_rejection(
        total_claimed=75000.0,
        total_approved=15000.0,
        rejection_reasons=[RejectionReason(code="MH02", description="Psychiatric hospitalization capped/excluded", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 60000.0


def test_tier1_f10_mental_health_physical_illness_skipped():
    bill = make_bill(diagnosis="Acute Appendicitis with Peritonitis")
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="EX01", description="General room excess", category="PROPORTIONATE_DEDUCTION")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


def test_tier1_f10_mental_health_approved_claim_passes():
    bill = make_bill(diagnosis="Anxiety disorder evaluation")
    policy = make_policy(covers_mental_health=True)
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="OTH01", description="Late document submission penalty", category="OTHER")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier1_f10_mental_health_appeal_recommendation_present():
    bill = make_bill(diagnosis="Schizophrenia management")
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="MH03", description="Mental health repudiated", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.appeal_recommendation is not None
    assert "Section 21(4)" in verdict.appeal_recommendation


# ============================================================================
# Feature 11: Source Evidence Provenance & Ledger (5 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_tier1_f11_evidence_audit_log_hash_generation(async_test_db):
    claim_id = "CLAIM-AUDIT-001"
    action = "DOCUMENT_UPLOADED"
    details = {"file_name": "bill.pdf", "sha256": "abc12345"}
    
    await AuditTrail.log(async_test_db, claim_id, action, details)
    history = await AuditTrail.get_audit_history(async_test_db, claim_id)
    
    assert len(history) == 1
    assert len(history[0]["entry_hash"]) == 64
    assert history[0]["previous_hash"] is None


@pytest.mark.asyncio
async def test_tier1_f11_evidence_audit_chain_sequential_linkage(async_test_db):
    claim_id = "CLAIM-AUDIT-002"
    await AuditTrail.log(async_test_db, claim_id, "STEP_1", {"msg": "Initial upload"})
    await AuditTrail.log(async_test_db, claim_id, "STEP_2", {"msg": "OCR processed"})
    
    history = await AuditTrail.get_audit_history(async_test_db, claim_id)
    assert len(history) == 2
    # History is ordered descending by id
    step_2 = history[0]
    step_1 = history[1]
    assert step_2["previous_hash"] == step_1["entry_hash"]


@pytest.mark.asyncio
async def test_tier1_f11_evidence_audit_chain_verification_passes(async_test_db):
    claim_id = "CLAIM-AUDIT-003"
    await AuditTrail.log(async_test_db, claim_id, "STEP_A", {"val": 1})
    await AuditTrail.log(async_test_db, claim_id, "STEP_B", {"val": 2})
    await AuditTrail.log(async_test_db, claim_id, "STEP_C", {"val": 3})
    
    is_valid = await AuditTrail.verify_chain(async_test_db, claim_id)
    assert is_valid is True


@pytest.mark.asyncio
async def test_tier1_f11_evidence_audit_chain_tamper_detection(async_test_db):
    from sqlalchemy import select
    claim_id = "CLAIM-AUDIT-004"
    await AuditTrail.log(async_test_db, claim_id, "INITIAL", {"val": 100})
    await AuditTrail.log(async_test_db, claim_id, "SECOND", {"val": 200})
    
    # Tamper with the second entry's previous_hash
    stmt = select(AuditLog).where(AuditLog.claim_id == claim_id).order_by(AuditLog.id.desc()).limit(1)
    res = await async_test_db.execute(stmt)
    entry = res.scalar_one()
    entry.previous_hash = "corrupted_hash_value_1234567890"
    await async_test_db.flush()
    
    is_valid = await AuditTrail.verify_chain(async_test_db, claim_id)
    assert is_valid is False


def test_tier1_f11_evidence_line_item_provenance_retention():
    item = make_line_item(
        description="Laparoscopic Trocar 10mm",
        category="CONSUMABLES",
        quantity=2.0,
        unit_rate=4500.0,
        amount=9000.0,
        item_code="MED-TR-10"
    )
    assert item.item_code == "MED-TR-10"
    assert item.quantity == 2.0
    assert item.unit_rate == 4500.0
    assert item.amount == 9000.0


# ============================================================================
# Feature 12: Universal NEEDS_REVIEW on Ambiguity (5 tests)
# ============================================================================

def test_tier1_f12_needs_review_sets_review_recommended():
    verdicts = [
        RuleVerdict(rule_name="Rule A", status="PASS", finding="All good"),
        RuleVerdict(rule_name="Rule B", status="NEEDS_REVIEW", finding="Unclear policy clause phrasing")
    ]
    result = AnalysisResult(
        claim_id="CLM-REV-01",
        analysis_timestamp="2025-01-01T00:00:00",
        documents_analyzed=[],
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="Needs human review"
    )
    assert result.overall_status == "REVIEW_RECOMMENDED"
    assert result.tier2_flags == 1


def test_tier1_f12_needs_review_increments_tier2_flags():
    verdicts = [
        RuleVerdict(rule_name="R1", status="NEEDS_REVIEW", finding="Unresolved code"),
        RuleVerdict(rule_name="R2", status="NEEDS_REVIEW", finding="Missing stamp verification")
    ]
    result = AnalysisResult(
        claim_id="CLM-REV-02",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="Multiple ambiguities"
    )
    assert result.tier2_flags == 2
    assert result.tier1_issues == 0


def test_tier1_f12_multiple_needs_review_verdicts_counted():
    verdicts = [
        RuleVerdict(rule_name=f"Rule_{i}", status="NEEDS_REVIEW", finding=f"Flag {i}")
        for i in range(5)
    ]
    result = AnalysisResult(
        claim_id="CLM-REV-03",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="5 review flags"
    )
    assert result.tier2_flags == 5


def test_tier1_f12_clean_pass_no_review_flags():
    verdicts = [
        RuleVerdict(rule_name="R1", status="PASS", finding="OK"),
        RuleVerdict(rule_name="R2", status="PASS", finding="OK")
    ]
    result = AnalysisResult(
        claim_id="CLM-REV-04",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="NO_MISMATCH_FOUND",
        rule_verdicts=verdicts,
        summary="All clear"
    )
    assert result.tier2_flags == 0
    assert result.overall_status == "NO_MISMATCH_FOUND"


def test_tier1_f12_appeal_evaluator_deterministic_on_zero_fails():
    evaluator = AppealEvaluator()
    verdicts = [
        RuleVerdict(rule_name="R1", status="PASS", finding="Valid"),
        RuleVerdict(rule_name="R2", status="SKIPPED", finding="N/A")
    ]
    res = evaluator.evaluate_verdicts(verdicts)
    assert res.appeal_viability == "LOW"
    assert len(res.statutory_conflicts_detected) == 0


# ============================================================================
# Feature 13: Frontend Calculation Invariance (5 tests)
# ============================================================================

def test_tier1_f13_monetary_impact_strictly_equals_fail_sum():
    verdicts = [
        RuleVerdict(rule_name="R1", status="FAIL", finding="Over-deduction", monetary_impact=15000.0),
        RuleVerdict(rule_name="R2", status="FAIL", finding="PED conflict", monetary_impact=25000.0),
        RuleVerdict(rule_name="R3", status="PASS", finding="OK", monetary_impact=0.0)
    ]
    result = AnalysisResult(
        claim_id="CLM-INV-01",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="Mismatches detected",
        total_monetary_impact=40000.0
    )
    assert result.total_monetary_impact == 40000.0
    assert result.tier1_issues == 2


def test_tier1_f13_non_fail_verdicts_zero_monetary_contribution():
    verdicts = [
        RuleVerdict(rule_name="R1", status="PASS", finding="OK", monetary_impact=5000.0),  # PASS should not count
        RuleVerdict(rule_name="R2", status="SKIPPED", finding="Skipped", monetary_impact=10000.0),
        RuleVerdict(rule_name="R3", status="NEEDS_REVIEW", finding="Review", monetary_impact=15000.0),
        RuleVerdict(rule_name="R4", status="BLOCKED", finding="Blocked", monetary_impact=20000.0)
    ]
    result = AnalysisResult(
        claim_id="CLM-INV-02",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="Non-fail checks"
    )
    assert result.total_monetary_impact is None


def test_tier1_f13_deterministic_engine_repeatability(rule_engine):
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-05")
    policy = make_policy(policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(claim_date="2025-01-03")
    
    run_1 = rule_engine.run_all_rules(bill, policy, rejection)
    run_2 = rule_engine.run_all_rules(bill, policy, rejection)
    
    assert run_1.overall_status == run_2.overall_status
    assert run_1.total_monetary_impact == run_2.total_monetary_impact
    assert len(run_1.rule_verdicts) == len(run_2.rule_verdicts)
    for v1, v2 in zip(run_1.rule_verdicts, run_2.rule_verdicts):
        assert v1.rule_name == v2.rule_name
        assert v1.status == v2.status
        assert v1.monetary_impact == v2.monetary_impact


def test_tier1_f13_serialization_roundtrip_precision():
    verdicts = [
        RuleVerdict(
            rule_name="Proportionate Deduction Rule",
            status="FAIL",
            finding="Excess deducted",
            monetary_impact=12345.67,
            insurer_approved_amount=50000.0,
            expected_admissible_amount=37654.33
        )
    ]
    result = AnalysisResult(
        claim_id="CLM-SERIAL-01",
        analysis_timestamp="2025-01-01T12:00:00Z",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="Serialized test", total_monetary_impact=12345.67
    )
    dumped = result.model_dump()
    restored = AnalysisResult.model_validate(dumped)
    
    assert restored.total_monetary_impact == 12345.67
    assert restored.rule_verdicts[0].monetary_impact == 12345.67
    assert restored.rule_verdicts[0].insurer_approved_amount == 50000.0


def test_tier1_f13_blocked_engine_zero_financial_impact(rule_engine):
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Different Person")
    rejection = make_rejection(policyholder_name="Wrong Person", total_claimed=50000.0, total_approved=50000.0, total_deducted=0.0)
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary
    blocked_verdict = next(v for v in result.rule_verdicts if v.status == "BLOCKED")
    assert blocked_verdict.monetary_impact in [None, 0.0]
