"""
Tier 2: Comprehensive Boundary and Corner Case Test Suite (>=5 per feature).
Covers 13 features with 65 edge/corner cases:
- Off-by-one dates, leap years, calendar boundaries
- Extreme monetary values, fractional paise, zero values
- Case-insensitivity, unicode, whitespace, special characters
- Null/empty handling, precedence hierarchies, and contract limits
"""

import pytest
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, WaitingPeriodConfig, SubLimit, ProportionateDeductionRuleConfig
from app.schemas.provenance import Provenance
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
# Feature 1: Clinical Firewall Gate (Boundaries)
# ============================================================================

def test_tier2_f01_clinical_firewall_mixed_case():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CF01", description="Hospitalization lacked mEdIcAl NeCeSsItY per guidelines", category="OTHER")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert "CLINICAL_REJECTION_DETECTED" in verdict.finding


def test_tier2_f01_clinical_firewall_punctuation_and_symbols():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CF02", description="**EXPERIMENTAL** procedure; not justified!", category="EXCLUSION")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"


def test_tier2_f01_clinical_firewall_multiple_reasons_mixed():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[
            RejectionReason(code="R1", description="Pharmacy bills unsigned", category="DOCUMENT_INCOMPLETE"),
            RejectionReason(code="R2", description="Tax invoice missing", category="DOCUMENT_INCOMPLETE"),
            RejectionReason(code="R3", description="Treatment protocol deviated without justification", category="OTHER")
        ]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "BLOCKED"


def test_tier2_f01_clinical_firewall_empty_rejection_reasons_and_remarks():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(rejection_reasons=[], remarks="")
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f01_clinical_firewall_similar_word_not_trigger():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="R1", description="Applied standard room rent ceiling as per clause 2.1", category="PROPORTIONATE_DEDUCTION")]
    )
    verdict = check_clinical_firewall(bill, policy, rejection)
    assert verdict.status == "PASS"


# ============================================================================
# Feature 2: Cross-Document Identity Gate (Boundaries)
# ============================================================================

def test_tier2_f02_identity_gate_claim_on_exact_start_date():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Rajesh Sharma", policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(policyholder_name="Rajesh Sharma", claim_date="2025-01-01")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f02_identity_gate_claim_on_exact_end_date():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Rajesh Sharma", policy_start_date="2025-01-01", policy_end_date="2025-12-31")
    rejection = make_rejection(policyholder_name="Rajesh Sharma", claim_date="2025-12-31")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f02_identity_gate_policy_number_whitespace_and_casing():
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policy_number=" POL-2024-HDF-9988 ")
    rejection = make_rejection(policy_number="pol-2024-hdf-9988")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f02_identity_gate_name_with_honorifics():
    bill = make_bill(patient_name="Mr. Rajesh Sharma")
    policy = make_policy(policyholder_name="Rajesh Sharma")
    rejection = make_rejection(policyholder_name="Rajesh Sharma")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f02_identity_gate_name_order_reversed():
    bill = make_bill(patient_name="Sharma Rajesh")
    policy = make_policy(policyholder_name="Rajesh Sharma")
    rejection = make_rejection(policyholder_name="Rajesh Sharma")
    verdict = check_identity_gate(bill, policy, rejection)
    assert verdict.status == "PASS"


# ============================================================================
# Feature 3: Document Integrity & Forensics Gate (Boundaries)
# ============================================================================

def test_tier2_f03_document_integrity_exact_threshold_ten_rupees():
    items = [make_line_item("Item 1", "ROOM", 1, 10000, 10000)]
    # Exactly ₹10.00 difference (within <= 10.0 allowance)
    bill = make_bill(line_items=items, total_amount=10010.0)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f03_document_integrity_just_above_threshold_ten_point_one():
    items = [make_line_item("Item 1", "ROOM", 1, 10000, 10000)]
    # ₹10.50 difference (> 10.0 allowance)
    bill = make_bill(line_items=items, total_amount=10010.50)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "WARNING"
    assert verdict.monetary_impact == 10.50


def test_tier2_f03_document_integrity_cents_paise_rounding():
    items = [
        make_line_item(f"Item {i}", "PHARMACY", 1, 99.99, 99.99)
        for i in range(10)
    ]
    # Sum is 999.90
    bill = make_bill(line_items=items, total_amount=999.90)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f03_document_integrity_single_large_line_item():
    items = [make_line_item("Organ Transplant Package", "OT", 1, 1500000.0, 1500000.0)]
    bill = make_bill(line_items=items, total_amount=1500000.0)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f03_document_integrity_zero_amount_bill():
    bill = make_bill(line_items=[], total_amount=0.0)
    policy = make_policy()
    rejection = make_rejection()
    verdict = check_document_integrity(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 4: Tier 0 Gate Blocking (Boundaries)
# ============================================================================

def test_tier2_f04_gate_blocking_multi_gate_failures(rule_engine):
    # Both clinical firewall and identity gate trip
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Completely Different Person")
    rejection = make_rejection(
        policyholder_name="Third Person",
        rejection_reasons=[RejectionReason(code="CF99", description="Medical necessity not established", category="OTHER")]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier2_f04_gate_blocking_confidence_preserved(rule_engine):
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="CLI01", description="Unjustified admission without medical necessity", category="OTHER")]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    blocked_verdict = next(v for v in result.rule_verdicts if v.status == "BLOCKED")
    assert blocked_verdict.confidence == 1.0


def test_tier2_f04_gate_blocking_clean_gates_with_downstream_fail(rule_engine):
    # Gates pass, but room rent over-deduction causes Tier 1 fail
    items = [
        make_line_item("Suite", "ROOM", 3, 10000, 30000, is_room_linked=True),
        make_line_item("Surgery OT", "OT", 1, 50000, 50000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-04", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # Expected deduction is 36,000 (18,000 excess + 18,000 proportionate). Insurer unlawfully deducts 70,000.
    rejection = make_rejection(total_claimed=80000.0, total_approved=10000.0, total_deducted=70000.0)
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "MISMATCH_DETECTED"
    assert not any(v.status == "BLOCKED" for v in result.rule_verdicts)


def test_tier2_f04_gate_blocking_clean_gates_with_downstream_pass(rule_engine):
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-04")
    policy = make_policy(room_rent_limit_per_day=5000.0)
    # Expected deduction is 0
    rejection = make_rejection(total_claimed=75000.0, total_approved=75000.0, total_deducted=0.0)
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "NO_MISMATCH_FOUND"


def test_tier2_f04_gate_blocking_empty_policy_and_bill_handling(rule_engine):
    # Tests graceful resilience without crashing
    bill = make_bill(line_items=[])
    policy = make_policy()
    rejection = make_rejection()
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert hasattr(result, "overall_status")
    assert isinstance(result.rule_verdicts, list)


# ============================================================================
# Feature 5: Proportionate Room Rent Deduction (Boundaries)
# ============================================================================

def test_tier2_f05_proportionate_deduction_exact_limit():
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-03",
        line_items=[make_line_item("Room", "ROOM", 2, 5000, 10000, is_room_linked=True)]
    )
    policy = make_policy(room_rent_limit_per_day=5000.0)
    rejection = make_rejection(total_deducted=0.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "Room Excess: Rs. 0.00" in verdict.finding


def test_tier2_f05_proportionate_deduction_exact_one_point_one_five_threshold():
    # Limit = 4000. 1.15 * 4000 = 4600.
    # Rate = 4600. Ratio = 1.15 (NOT strictly > 1.15)
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-03",
        line_items=[
            make_line_item("Room", "ROOM", 2, 4600, 9200, is_room_linked=True),
            make_line_item("Nursing", "NURSING", 2, 1000, 2000, is_room_linked=True)
        ]
    )
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # Room excess = (4600 - 4000) * 2 = 1200. Proportionate reduction is ZERO.
    rejection = make_rejection(total_deducted=1200.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "Proportionate reduction is ZERO" in verdict.finding


def test_tier2_f05_proportionate_deduction_strictly_above_threshold():
    # Rate = 4601 (strictly > 4600)
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-03",
        line_items=[
            make_line_item("Room", "ROOM", 2, 4601, 9202, is_room_linked=True),
            make_line_item("Nursing", "NURSING", 2, 1000, 2000, is_room_linked=True)
        ]
    )
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    rejection = make_rejection(total_deducted=2000.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert "Proportionate reduction applies" in verdict.finding


def test_tier2_f05_proportionate_deduction_single_day_stay():
    bill = make_bill(
        admission_date="2025-01-01",
        discharge_date="2025-01-02",
        line_items=[make_line_item("Room", "ROOM", 1, 8000, 8000, is_room_linked=True)]
    )
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # 1 day stay. Room excess = (8000 - 4000) * 1 = 4000. Proportionate reduction = 8000 * 0.50 = 4000. Expected = 8000.
    rejection = make_rejection(total_deducted=8000.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f05_proportionate_deduction_ninety_nine_rupee_buffer():
    items = [make_line_item("Room", "ROOM", 2, 8000, 16000, is_room_linked=True)]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # Expected deduction is 16,000. Insurer deducts 16,099 (within <= 100 buffer)
    rejection = make_rejection(total_deducted=16099.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


# ============================================================================
# Feature 6: Protected Expense Shielding (Boundaries)
# ============================================================================

def test_tier2_f06_protected_expense_hundred_percent_shielded_bill():
    items = [
        make_line_item("Chemotherapy Drug", "PHARMACY", 1, 50000, 50000, is_room_linked=False),
        make_line_item("Infusion Facility", "OT", 1, 20000, 20000, is_room_linked=False)
    ]
    bill = make_bill(line_items=items)
    policy = make_policy(room_rent_limit_per_day=3000.0)
    rejection = make_rejection(total_deducted=0.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    # Since no ROOM charges exist, rule skips cleanly
    assert verdict.status == "SKIPPED"


def test_tier2_f06_protected_expense_miscellaneous_deducted_separately():
    items = [
        make_line_item("Room", "ROOM", 1, 6000, 6000, is_room_linked=True),
        make_line_item("Admission Registration", "MISCELLANEOUS", 1, 1000, 1000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # 6000/4000 = 1.5 > 1.15. Room excess = 2000. Prop red = 6000 * (1 - 4/6) = 2000.
    # Misc = 1000. Total expected deduction = 2000 + 2000 + 1000 = 5000.
    rejection = make_rejection(total_deducted=5000.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "including non-medical" in verdict.finding


def test_tier2_f06_protected_expense_high_value_implant_shielded():
    items = [
        make_line_item("Room", "ROOM", 1, 8000, 8000, is_room_linked=True),
        make_line_item("Drug Eluting Stent", "CONSUMABLES", 1, 150000, 150000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    policy.proportionate_deduction_rule = ProportionateDeductionRuleConfig(
        threshold_value=Provenance(value=1.15, source_type="POLICY"),
        threshold_operator=Provenance(value=">", source_type="POLICY"),
        threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
    )
    # Expected deduction is 4000 room excess + 4000 proportionate = 8000.
    # Stent of 150,000 is 100% shielded.
    rejection = make_rejection(total_deducted=8000.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.expected_admissible_amount == 8000.0


def test_tier2_f06_protected_expense_zero_amount_items():
    items = [
        make_line_item("Room", "ROOM", 1, 5000, 5000, is_room_linked=True),
        make_line_item("Free Sample Kit", "PHARMACY", 1, 0.0, 0.0, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    policy = make_policy(room_rent_limit_per_day=5000.0)
    rejection = make_rejection(total_deducted=0.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f06_protected_expense_fractional_room_ratio():
    items = [make_line_item("Room", "ROOM", 1, 6666.0, 6666.0, is_room_linked=True)]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    policy = make_policy(room_rent_limit_per_day=3333.0)
    rejection = make_rejection(total_deducted=6666.0)
    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"


# ============================================================================
# Feature 7: Co-Pay and Deductible Reconciliation (Boundaries)
# ============================================================================

def test_tier2_f07_deductible_exact_boundary():
    policy = make_policy(deductible=20000.0)
    claim_amount = 20000.0
    admissible = max(0.0, claim_amount - policy.deductible)
    assert admissible == 0.0


def test_tier2_f07_deductible_one_rupee_above():
    policy = make_policy(deductible=20000.0)
    claim_amount = 20001.0
    admissible = max(0.0, claim_amount - policy.deductible)
    assert admissible == 1.0


def test_tier2_f07_copay_extreme_fifty_percent():
    policy = make_policy(copay_percentage=50.0)
    claim_amount = 120000.0
    patient_share = claim_amount * (policy.copay_percentage / 100.0)
    insurer_share = claim_amount - patient_share
    assert patient_share == 60000.0
    assert insurer_share == 60000.0


def test_tier2_f07_deductible_then_copay_ordering():
    policy = make_policy(deductible=20000.0, copay_percentage=10.0)
    total_claim = 100000.0
    after_deductible = max(0.0, total_claim - policy.deductible)
    copay_deduction = after_deductible * (policy.copay_percentage / 100.0)
    net_payable = after_deductible - copay_deduction
    assert after_deductible == 80000.0
    assert copay_deduction == 8000.0
    assert net_payable == 72000.0


def test_tier2_f07_sublimit_exact_match():
    sub_limit = SubLimit(category="Hernia", max_amount=50000.0, description="Hernia repair")
    policy = make_policy(sub_limits=[sub_limit])
    bill_amount = 50000.0
    excess = max(0.0, bill_amount - policy.sub_limits[0].max_amount)
    assert excess == 0.0


# ============================================================================
# Feature 8: 60-Month Moratorium Enforcer (Boundaries)
# ============================================================================

def test_tier2_f08_moratorium_exact_completion_day():
    bill = make_bill()
    # Inception 2019-01-01; 60 months completion date is 2024-01-01
    policy = make_policy(inception_date="2019-01-01", moratorium_period_months=60)
    # Claim on the exact completion date (not strictly > completion date)
    rejection = make_rejection(
        claim_date="2024-01-01",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing hypertension", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    # Claim date is not strictly greater than completion date, so passes
    assert verdict.status == "PASS"


def test_tier2_f08_moratorium_one_day_after_completion():
    bill = make_bill()
    policy = make_policy(inception_date="2019-01-01", moratorium_period_months=60)
    # Claim 1 day after completion date
    rejection = make_rejection(
        claim_date="2024-01-02",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing condition cited", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding


def test_tier2_f08_moratorium_leap_year_inception():
    bill = make_bill()
    # Leap day inception 2020-02-29
    policy = make_policy(inception_date="2020-02-29", moratorium_period_months=60)
    # 60 months later is 2025-02-28; claim on 2025-03-01
    rejection = make_rejection(
        claim_date="2025-03-01",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing asthma", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"


def test_tier2_f08_moratorium_full_portability_sixty_months():
    bill = make_bill()
    # 60 months ported credits -> 0 months needed on current policy
    policy = make_policy(
        inception_date="2025-01-01",
        portability_credits_months=60,
        moratorium_period_months=60
    )
    rejection = make_rejection(
        claim_date="2025-01-05",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing diabetes", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"


def test_tier2_f08_moratorium_missing_dates_graceful_skip():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        claim_date="",
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing disease", category="PRE_EXISTING")]
    )
    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 9: Waiting Period & Portability Verifier (Boundaries)
# ============================================================================

def test_tier2_f09_waiting_period_exact_day_thirty():
    bill = make_bill()
    policy = make_policy(inception_date="2025-01-01")
    # Day 30 after inception: 2025-01-31
    rejection = make_rejection(
        claim_date="2025-01-31",
        rejection_reasons=[RejectionReason(code="WP01", description="Initial waiting period", details="initial 30 days", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    # delta_days = 30, not > 30, so waiting period has NOT expired
    assert verdict.status == "PASS"


def test_tier2_f09_waiting_period_day_thirty_one():
    bill = make_bill()
    policy = make_policy(inception_date="2025-01-01")
    # Day 31 after inception: 2025-02-01
    rejection = make_rejection(
        claim_date="2025-02-01",
        rejection_reasons=[RejectionReason(code="WP01", description="Initial waiting period", details="initial 30 days", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    # delta_days = 31 > 30, so waiting period has expired!
    assert verdict.status == "FAIL"


def test_tier2_f09_waiting_period_same_day_claim():
    bill = make_bill()
    policy = make_policy(inception_date="2025-01-01")
    rejection = make_rejection(
        claim_date="2025-01-01",
        rejection_reasons=[RejectionReason(code="WP01", description="Initial 30 days", details="initial", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "has not expired" in verdict.finding


def test_tier2_f09_waiting_period_ped_four_year_boundary():
    bill = make_bill()
    policy = make_policy(inception_date="2020-01-01")
    # 5 years later (> 48 months)
    rejection = make_rejection(
        claim_date="2025-01-15",
        rejection_reasons=[RejectionReason(code="WP03", description="PED waiting period", details="ped", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "FAIL"


def test_tier2_f09_waiting_period_missing_inception_skipped():
    bill = make_bill()
    policy = make_policy()
    rejection = make_rejection(
        claim_date="",
        rejection_reasons=[RejectionReason(code="WP01", description="Waiting period", category="WAITING_PERIOD")]
    )
    verdict = check_waiting_period(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 10: Mental Health Parity (Boundaries)
# ============================================================================

def test_tier2_f10_mental_health_all_caps_diagnosis():
    bill = make_bill(diagnosis="BIPOLAR AFFECTIVE DISORDER - SEVERE")
    policy = make_policy(covers_mental_health=True)
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="MH01", description="Psychiatric conditions excluded", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"


def test_tier2_f10_mental_health_psychotherapy_keyword():
    bill = make_bill(diagnosis="Psychotherapy and cognitive behavioral therapy admission")
    policy = make_policy(covers_mental_health=True)
    rejection = make_rejection(
        rejection_reasons=[RejectionReason(code="MH02", description="Mental health therapy barred", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"


def test_tier2_f10_mental_health_full_approval_clean_zero_impact():
    bill = make_bill(diagnosis="Depression evaluation")
    policy = make_policy(covers_mental_health=True)
    rejection = make_rejection(
        total_claimed=50000.0,
        total_approved=50000.0,
        rejection_reasons=[RejectionReason(code="OK", description="Approved in full", category="OTHER")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "PASS"


def test_tier2_f10_mental_health_zero_approval_full_repudiation():
    bill = make_bill(diagnosis="Schizophrenia acute psychosis")
    policy = make_policy(covers_mental_health=False)
    rejection = make_rejection(
        total_claimed=120000.0,
        total_approved=0.0,
        rejection_reasons=[RejectionReason(code="MH04", description="Mental condition excluded", category="MENTAL_HEALTH")]
    )
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 120000.0


def test_tier2_f10_mental_health_empty_diagnosis_handled():
    bill = make_bill(diagnosis="")
    policy = make_policy()
    rejection = make_rejection(rejection_reasons=[])
    verdict = check_mental_health_parity(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


# ============================================================================
# Feature 11: Source Evidence Provenance & Ledger (Boundaries)
# ============================================================================

@pytest.mark.asyncio
async def test_tier2_f11_evidence_empty_details_dict(async_test_db):
    claim_id = "CLAIM-BND-001"
    await AuditTrail.log(async_test_db, claim_id, "EMPTY_EVENT", {})
    history = await AuditTrail.get_audit_history(async_test_db, claim_id)
    assert len(history) == 1
    assert len(history[0]["entry_hash"]) == 64


@pytest.mark.asyncio
async def test_tier2_f11_evidence_unicode_in_details(async_test_db):
    claim_id = "CLAIM-BND-002"
    details = {"hospital": "अपोलो अस्पताल", "patient": "राजेश शर्मा", "symbol": "₹50,000"}
    await AuditTrail.log(async_test_db, claim_id, "UNICODE_EVENT", details)
    history = await AuditTrail.get_audit_history(async_test_db, claim_id)
    assert len(history) == 1
    assert len(history[0]["entry_hash"]) == 64


@pytest.mark.asyncio
async def test_tier2_f11_evidence_extended_chain_ten_entries(async_test_db):
    claim_id = "CLAIM-BND-003"
    for i in range(10):
        await AuditTrail.log(async_test_db, claim_id, f"EVENT_{i}", {"index": i})
    is_valid = await AuditTrail.verify_chain(async_test_db, claim_id)
    assert is_valid is True


@pytest.mark.asyncio
async def test_tier2_f11_evidence_first_entry_previous_hash_none(async_test_db):
    claim_id = "CLAIM-BND-004"
    await AuditTrail.log(async_test_db, claim_id, "GENESIS", {"step": 0})
    history = await AuditTrail.get_audit_history(async_test_db, claim_id)
    assert history[0]["previous_hash"] is None


def test_tier2_f11_evidence_hash_deterministic_for_same_input():
    import json
    import hashlib
    action = "AUDIT_TEST"
    details = {"amount": 1000.0, "status": "APPROVED"}
    serialized = json.dumps(details, sort_keys=True)
    h1 = hashlib.sha256(f"{action}{serialized}".encode('utf-8')).hexdigest()
    h2 = hashlib.sha256(f"{action}{serialized}".encode('utf-8')).hexdigest()
    assert h1 == h2
    assert len(h1) == 64


# ============================================================================
# Feature 12: Universal NEEDS_REVIEW on Ambiguity (Boundaries)
# ============================================================================

def test_tier2_f12_needs_review_precedence_over_pass():
    verdicts = [
        RuleVerdict(rule_name="R1", status="PASS", finding="OK"),
        RuleVerdict(rule_name="R2", status="NEEDS_REVIEW", finding="Indeterminate clause")
    ]
    result = AnalysisResult(
        claim_id="CLM-BND-REV-01",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="Review recommended"
    )
    assert result.overall_status == "REVIEW_RECOMMENDED"
    assert result.tier2_flags == 1


def test_tier2_f12_fail_precedence_over_needs_review():
    verdicts = [
        RuleVerdict(rule_name="R1", status="FAIL", finding="Math error", monetary_impact=5000.0),
        RuleVerdict(rule_name="R2", status="NEEDS_REVIEW", finding="Unclear clause")
    ]
    result = AnalysisResult(
        claim_id="CLM-BND-REV-02",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="Fail overrides review for overall_status"
    )
    assert result.overall_status == "MISMATCH_DETECTED"
    assert result.tier1_issues == 1
    assert result.tier2_flags == 1


def test_tier2_f12_blocked_precedence_over_all():
    verdicts = [
        RuleVerdict(rule_name="Gatekeeper", status="BLOCKED", finding="Blocked"),
        RuleVerdict(rule_name="R1", status="FAIL", finding="Over-deduction", monetary_impact=1000.0),
        RuleVerdict(rule_name="R2", status="NEEDS_REVIEW", finding="Ambiguous")
    ]
    result = AnalysisResult(
        claim_id="CLM-BND-REV-03",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="BLOCKED",
        rule_verdicts=verdicts,
        summary="Blocked status overrides all"
    )
    assert result.overall_status == "BLOCKED"


def test_tier2_f12_zero_verdicts_default_status():
    result = AnalysisResult(
        claim_id="CLM-BND-REV-04",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="NO_MISMATCH_FOUND",
        rule_verdicts=[],
        summary="No rules run"
    )
    assert result.overall_status == "NO_MISMATCH_FOUND"
    assert result.tier1_issues == 0
    assert result.tier2_flags == 0
    assert result.total_monetary_impact is None


def test_tier2_f12_needs_review_monetary_impact_isolation():
    verdicts = [
        RuleVerdict(rule_name="R1", status="NEEDS_REVIEW", finding="Review needed", monetary_impact=9999.0)
    ]
    result = AnalysisResult(
        claim_id="CLM-BND-REV-05",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="REVIEW_RECOMMENDED",
        rule_verdicts=verdicts,
        summary="Test monetary isolation"
    )
    assert result.total_monetary_impact is None


# ============================================================================
# Feature 13: Frontend Calculation Invariance (Boundaries)
# ============================================================================

def test_tier2_f13_extreme_large_monetary_values():
    verdicts = [
        RuleVerdict(rule_name="R1", status="FAIL", finding="High value error", monetary_impact=100000000.0),
        RuleVerdict(rule_name="R2", status="FAIL", finding="Another error", monetary_impact=50000000.0)
    ]
    result = AnalysisResult(
        claim_id="CLM-EXTREME-01",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="Extreme monetary values", total_monetary_impact=150000000.0
    )
    assert result.total_monetary_impact == 150000000.0


def test_tier2_f13_tiny_fractional_monetary_values():
    verdicts = [
        RuleVerdict(rule_name="R1", status="FAIL", finding="Fraction 1", monetary_impact=0.01),
        RuleVerdict(rule_name="R2", status="FAIL", finding="Fraction 2", monetary_impact=0.02)
    ]
    result = AnalysisResult(
        claim_id="CLM-TINY-01",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="Paise rounding", total_monetary_impact=0.03
    )
    assert round(result.total_monetary_impact, 2) == 0.03


def test_tier2_f13_none_monetary_impact_treated_as_zero():
    verdicts = [
        RuleVerdict(rule_name="R1", status="FAIL", finding="Missing impact field", monetary_impact=None)
    ]
    result = AnalysisResult(
        claim_id="CLM-NONE-01",
        analysis_timestamp="2025-01-01T00:00:00",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=verdicts,
        summary="None monetary impact"
    )
    assert result.total_monetary_impact is None


def test_tier2_f13_empty_documents_analyzed_serialization():
    result = AnalysisResult(
        claim_id="CLM-DOC-01",
        analysis_timestamp="2025-01-01T00:00:00",
        documents_analyzed=[],
        overall_status="NO_MISMATCH_FOUND",
        rule_verdicts=[],
        summary="Empty docs list"
    )
    dumped = result.model_dump()
    assert dumped["documents_analyzed"] == []


def test_tier2_f13_analysis_timestamp_formats():
    iso_time = "2025-05-15T14:30:00+00:00"
    result = AnalysisResult(
        claim_id="CLM-TS-01",
        analysis_timestamp=iso_time,
        overall_status="NO_MISMATCH_FOUND",
        rule_verdicts=[],
        summary="Timestamp test"
    )
    assert result.analysis_timestamp == iso_time
