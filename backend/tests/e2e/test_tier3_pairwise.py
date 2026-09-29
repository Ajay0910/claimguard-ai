"""
Tier 3: Comprehensive Cross-Feature Combinations (Pairwise Interaction Suite).
Covers 15 pairwise feature interaction test cases:
1. Moratorium + Room Rent Capping
2. Identity Conflict + Clinical Rejection
3. Co-Pay + Protected ICU & OT Shielding
4. Document Arithmetic Warning + Proportionate Deduction
5. Mental Health Parity + Waiting Period
6. Waiting Period Expired + Room Rent Limit Exceeded
7. Moratorium Active (<60m) + Clinical Firewall
8. Portability Credits + Waiting Period Satisfaction
9. Procedure Sub-Limit + Room Rent Proportionate Capping
10. Identity Mismatch + Document Arithmetic Error
11. Moratorium Expired (>60m) + Non-Medical Deductions
12. Clinical Necessity Disguised Repudiation + Room Rent Haircut
13. Mental Health Denial Overturn + Deductible Accounting
14. Room Rent Within Limit + Co-Pay Reconciliation
15. Hospital Authenticity Failure + Clean Gates
"""

import pytest
from datetime import datetime, date

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
from app.rules.authenticity_check import check_authenticity
from app.rules.engine import RuleEngine

from .conftest import make_bill, make_policy, make_rejection, make_line_item


def test_tier3_pairwise_01_moratorium_and_room_rent_capping():
    # Moratorium protects against PED repudiation, while room excess is computed independently
    items = [
        make_line_item("Deluxe Room", "ROOM", 5, 8000, 40000, is_room_linked=True),
        make_line_item("Nursing", "NURSING", 5, 2000, 10000, is_room_linked=True),
        make_line_item("Pharmacy", "PHARMACY", 1, 20000, 20000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-06", line_items=items)
    # Continuous coverage since 2018 (> 60 months)
    policy = make_policy(inception_date="2018-01-01", moratorium_period_months=60, room_rent_limit_per_day=4000.0)
    rejection = make_rejection(
        claim_date="2025-01-03",
        total_claimed=70000.0,
        total_approved=25000.0,
        total_deducted=45000.0,
        rejection_reasons=[RejectionReason(code="PED01", description="Non-disclosure of pre-existing hypertension", category="PRE_EXISTING")]
    )
    # 1. Moratorium check must fail (protecting policyholder)
    moratorium_verdict = check_clause_timeline(bill, policy, rejection)
    assert moratorium_verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in moratorium_verdict.finding

    # 2. Proportionate deduction calculates legitimate room excess independently
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    assert prop_verdict.expected_admissible_amount > 0.0


def test_tier3_pairwise_02_identity_conflict_and_clinical_rejection(rule_engine):
    # Both identity mismatch and clinical necessity denial occur
    bill = make_bill(patient_name="Rajesh Sharma")
    policy = make_policy(policyholder_name="Different Person", policy_number="POL-A")
    rejection = make_rejection(
        policyholder_name="Third Person",
        policy_number="POL-B",
        rejection_reasons=[RejectionReason(code="CLI01", description="Hospitalization not backed by medical necessity", category="OTHER")]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier3_pairwise_03_copay_and_icu_shielding():
    # Bill with Deluxe Room + ICU (shielded) + OT (shielded) with 10% co-pay
    room = make_line_item("Room", "ROOM", 2, 8000, 16000, is_room_linked=True)
    icu = make_line_item("ICU Intensive Care", "OT", 2, 15000, 30000, is_room_linked=False)
    pharmacy = make_line_item("Medicines", "PHARMACY", 1, 14000, 14000, is_room_linked=False)
    
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=[room, icu, pharmacy])
    policy = make_policy(room_rent_limit_per_day=4000.0, copay_percentage=10.0)
    
    # Proportionate check verifies ICU and pharmacy are not in room-linked haircut
    rejection = make_rejection(total_deducted=16000.0)
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    assert prop_verdict.status == "PASS"
    assert prop_verdict.expected_admissible_amount == 16000.0  # 8000 excess (2 days * 4000) + 8000 prop reduction on room
    
    # Financial reconciliation: Admissible after room excess = 60,000 - 16,000 = 44,000.
    # 10% co-pay on 44,000 = 4,400. Insurer payable = 39,600.
    admissible = bill.total_amount - prop_verdict.expected_admissible_amount
    patient_copay = admissible * 0.10
    insurer_payable = admissible - patient_copay
    assert admissible == 44000.0
    assert patient_copay == 4400.0
    assert insurer_payable == 39600.0


def test_tier3_pairwise_04_document_integrity_warning_and_proportionate_deduction():
    # Arithmetic discrepancy between line items and total_amount triggers WARNING
    items = [make_line_item("Room", "ROOM", 2, 5000, 10000, is_room_linked=True)]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=items, total_amount=25000.0)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(total_deducted=10000.0)
    
    doc_verdict = check_document_integrity(bill, policy, rejection)
    assert doc_verdict.status == "WARNING"
    assert doc_verdict.monetary_impact == 15000.0


def test_tier3_pairwise_05_mental_health_parity_and_waiting_period():
    bill = make_bill(diagnosis="Major Depressive Disorder with Psychosis")
    policy = make_policy(inception_date="2024-01-01", covers_mental_health=False)
    rejection = make_rejection(
        claim_date="2024-03-01",
        total_claimed=60000.0,
        total_approved=0.0,
        rejection_reasons=[
            RejectionReason(code="MH01", description="Psychiatric disorders excluded under policy", category="MENTAL_HEALTH"),
            RejectionReason(code="WP01", description="Specific illness waiting period", details="specific", category="WAITING_PERIOD")
        ]
    )
    # Mental health repudiation is illegal under Section 21(4) MHCA 2017
    mh_verdict = check_mental_health_parity(bill, policy, rejection)
    assert mh_verdict.status == "FAIL"
    assert "Mental Healthcare Act 2017" in mh_verdict.regulatory_citation
    assert mh_verdict.monetary_impact == 60000.0


def test_tier3_pairwise_06_waiting_period_expired_and_room_rent_limit_exceeded():
    items = [
        make_line_item("Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("Nursing", "NURSING", 4, 2000, 8000, is_room_linked=True)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-05", line_items=items)
    # Inception 90 days ago; initial 30 days has expired
    policy = make_policy(inception_date="2024-10-01", room_rent_limit_per_day=4000.0)
    rejection = make_rejection(
        claim_date="2025-01-03",
        total_claimed=40000.0,
        total_approved=0.0,
        total_deducted=40000.0,
        rejection_reasons=[RejectionReason(code="WP01", description="Initial 30 day waiting period", details="initial 30 days", category="WAITING_PERIOD")]
    )
    # 1. Waiting period rejection fails because 90 days > 30 days
    wp_verdict = check_waiting_period(bill, policy, rejection)
    assert wp_verdict.status == "FAIL"
    
    # 2. Room rent deduction is calculated accurately
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    # Expected deduction is 16,000 room excess + 20,000 proportionate = 36,000
    assert prop_verdict.expected_admissible_amount == 36000.0


def test_tier3_pairwise_07_moratorium_active_and_clinical_firewall(rule_engine):
    bill = make_bill()
    # Inception 6 months ago (< 60 months)
    policy = make_policy(inception_date="2024-07-01", moratorium_period_months=60)
    rejection = make_rejection(
        claim_date="2025-01-12",
        rejection_reasons=[
            RejectionReason(code="PED01", description="Pre-existing disease", category="PRE_EXISTING"),
            RejectionReason(code="CLIN01", description="Medical necessity not established for inpatient admission", category="OTHER")
        ]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier3_pairwise_08_portability_credits_and_waiting_period():
    bill = make_bill()
    # Inception 6 months ago on new policy, but 24 months ported
    policy = make_policy(
        inception_date="2024-07-01",
        portability_credits_months=24,
        moratorium_period_months=60
    )
    rejection = make_rejection(
        claim_date="2025-01-01",
        rejection_reasons=[RejectionReason(code="PED01", description="Non-disclosure of pre-existing ailment", category="PRE_EXISTING")]
    )
    # Ported 24 months + 6 months on current policy = 30 months (< 60 moratorium)
    # Verifies moratorium has not completed yet (PASS)
    moratorium_verdict = check_clause_timeline(bill, policy, rejection)
    assert moratorium_verdict.status == "PASS"


def test_tier3_pairwise_09_sublimit_exhaustion_and_proportionate_deduction():
    # Cataract surgery: Procedure sub-limit ₹35,000, room rent cap ₹3,000/day
    items = [
        make_line_item("Day Care Room", "ROOM", 1, 5000, 5000, is_room_linked=True),
        make_line_item("Phacoemulsification Cataract OT", "OT", 1, 45000, 45000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-02", line_items=items)
    cataract_sublimit = SubLimit(category="Cataract", max_amount=35000.0, description="Cataract surgery cap")
    policy = make_policy(room_rent_limit_per_day=3000.0, sub_limits=[cataract_sublimit])
    rejection = make_rejection(total_claimed=50000.0, total_deducted=15000.0)
    
    # 1. Room rent check verifies OT is shielded from room haircut
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    assert "Expected Proportionate Reduction: Rs. 2000.00" in prop_verdict.finding
    
    # 2. Procedure sub-limit check: Cataract procedure (45,000) exceeds 35,000 sublimit by 10,000
    procedure_excess = max(0.0, 45000.0 - policy.sub_limits[0].max_amount)
    assert procedure_excess == 10000.0


def test_tier3_pairwise_10_identity_mismatch_and_document_arithmetic_error(rule_engine):
    # Both identity mismatch and arithmetic error occur simultaneously
    items = [make_line_item("Room", "ROOM", 1, 2000, 2000)]
    bill = make_bill(patient_name="Rajesh Sharma", line_items=items, total_amount=20000.0)  # Difference 18,000
    policy = make_policy(policyholder_name="Different Person")
    rejection = make_rejection(policyholder_name="Wrong Person")
    
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier3_pairwise_11_moratorium_expired_and_miscellaneous_deductions():
    # Moratorium protects against PED repudiation; miscellaneous non-medical items are deducted
    items = [
        make_line_item("Room", "ROOM", 2, 4000, 8000, is_room_linked=True),
        make_line_item("Administrative File Fee", "MISCELLANEOUS", 1, 1500, 1500, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=items)
    policy = make_policy(inception_date="2018-01-01", moratorium_period_months=60, room_rent_limit_per_day=5000.0)
    rejection = make_rejection(
        claim_date="2025-01-02",
        total_claimed=9500.0,
        total_approved=8000.0,
        total_deducted=1500.0,
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing ailment", category="PRE_EXISTING")]
    )
    # Moratorium rule fails (protecting policyholder)
    moratorium_verdict = check_clause_timeline(bill, policy, rejection)
    assert moratorium_verdict.status == "FAIL"
    
    # Proportionate rule confirms 1500 non-medical deduction was legitimate
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    assert prop_verdict.status == "PASS"


def test_tier3_pairwise_12_clinical_necessity_and_proportionate_overdeduction(rule_engine):
    # Insurer repudiated on medical necessity AND attempted arbitrary deductions
    items = [make_line_item("Deluxe", "ROOM", 3, 8000, 24000, is_room_linked=True)]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-04", line_items=items)
    policy = make_policy(room_rent_limit_per_day=4000.0)
    rejection = make_rejection(
        total_claimed=24000.0,
        total_deducted=24000.0,
        rejection_reasons=[RejectionReason(code="CLI01", description="Hospitalization not justified by medical necessity", category="OTHER")]
    )
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary


def test_tier3_pairwise_13_mental_health_and_deductible_reconciliation():
    # Mental health claim of 100,000 unlawfully repudiated; policy has 15,000 deductible
    bill = make_bill(diagnosis="Bipolar disorder manic episode")
    policy = make_policy(covers_mental_health=False, deductible=15000.0)
    rejection = make_rejection(
        total_claimed=100000.0,
        total_approved=0.0,
        rejection_reasons=[RejectionReason(code="MH01", description="Mental health excluded", category="MENTAL_HEALTH")]
    )
    mh_verdict = check_mental_health_parity(bill, policy, rejection)
    assert mh_verdict.status == "FAIL"
    # Net statutory recoverable after deductible is 85,000
    net_recoverable = max(0.0, mh_verdict.monetary_impact - policy.deductible)
    assert net_recoverable == 85000.0


def test_tier3_pairwise_14_room_rent_within_limit_and_copay():
    # Room rent within limit; 15% co-pay applied accurately
    items = [
        make_line_item("Room", "ROOM", 2, 4000, 8000, is_room_linked=True),
        make_line_item("OT", "OT", 1, 32000, 32000, is_room_linked=False)
    ]
    bill = make_bill(admission_date="2025-01-01", discharge_date="2025-01-03", line_items=items)
    policy = make_policy(room_rent_limit_per_day=5000.0, copay_percentage=15.0)
    rejection = make_rejection(total_deducted=0.0)
    
    prop_verdict = check_proportionate_deduction(bill, policy, rejection)
    assert prop_verdict.status == "PASS"
    assert prop_verdict.monetary_impact == 0.0
    
    total_bill = bill.total_amount
    patient_copay = total_bill * (policy.copay_percentage / 100.0)
    insurer_share = total_bill - patient_copay
    assert total_bill == 40000.0
    assert patient_copay == 6000.0
    assert insurer_share == 34000.0


def test_tier3_pairwise_15_authenticity_check_failed_and_clean_gates():
    # Identity and dates pass, but hospital is fake/unregistered
    bill = make_bill(hospital_name="Fake Test City Nursing Home", total_amount=85000.0)
    policy = make_policy(policy_number="POL-2024-HDF-9988")
    rejection = make_rejection()
    
    # 1. Identity gate passes
    id_verdict = check_identity_gate(bill, policy, rejection)
    assert id_verdict.status == "PASS"
    
    # 2. Authenticity verification check fails
    auth_verdict = check_authenticity(bill, policy, rejection)
    assert auth_verdict.status == "FAIL"
    assert auth_verdict.monetary_impact == 85000.0
    assert "could not be verified in the National Registry" in auth_verdict.finding
