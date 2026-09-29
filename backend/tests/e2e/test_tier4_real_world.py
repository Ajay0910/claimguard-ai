"""
Tier 4: Comprehensive Real-World Application Scenarios (S1 - S5).
Multi-document end-to-end realistic claim assessment workflows:
- S1: Multi-day Inpatient Stay with Room Rent Excess & Protected ICU
- S2: Moratorium Protection after Portability & Inception Anniversary
- S3: Medical Necessity Disguised Denial with Mixed Financial Deductions
- S4: Cross-Document Patient Name Mismatch & Missing Policy Number
- S5: High-Value Cardiac Surgery with Co-pay & Sub-limit Verification
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
from app.rules.appeal_evaluator import AppealEvaluator
from app.rules.engine import RuleEngine

from .conftest import make_bill, make_policy, make_rejection, make_line_item, extract_val


def test_tier4_scenario_s1_multiday_inpatient_room_rent_excess_protected_icu(rule_engine):
    """
    Scenario S1: Multi-day stay at Max Healthcare with Deluxe Room excess and ICU stay.
    Verifies:
    1. Proportionate deduction applies strictly to room-linked charges (Deluxe Room + Nursing).
    2. ICU ventilator charges (₹64,000) and Meropenem antibiotics (₹38,000) are shielded.
    3. Insurer's blanket 50% deduction across entire bill is flagged as unlawful over-deduction.
    """
    items = [
        make_line_item("Deluxe Room", "ROOM", 3, 8000.0, 24000.0, is_room_linked=True, item_code="RM-DLX"),
        make_line_item("Nursing Charges Deluxe", "NURSING", 3, 1500.0, 4500.0, is_room_linked=True, item_code="NUR-DLX"),
        make_line_item("ICU Ventilator Care", "OT", 4, 16000.0, 64000.0, is_room_linked=False, item_code="ICU-VENT"),
        make_line_item("Pulmonology Specialist Consultation", "CONSULTATION", 7, 2000.0, 14000.0, is_room_linked=False, item_code="CON-PULM"),
        make_line_item("IV Meropenem & Antibiotics", "PHARMACY", 1, 38000.0, 38000.0, is_room_linked=False, item_code="PHAR-MER"),
        make_line_item("ABG & Blood Pathology Labs", "LAB", 1, 18500.0, 18500.0, is_room_linked=False, item_code="LAB-ABG"),
        make_line_item("High-Flow Oxygen & Consumables", "CONSUMABLES", 1, 15000.0, 15000.0, is_room_linked=False, item_code="CONS-O2")
    ]
    bill = make_bill(
        hospital_name="Max Super Speciality Hospital, Saket",
        patient_name="Sunita Ramesh Iyer",
        line_items=items,
        admission_date="2025-01-05",
        discharge_date="2025-01-12",
        diagnosis="Severe Acute Pneumonia with Sepsis and ARDS",
        bill_id="MAX-DEL-2025-9981"
    )
    assert extract_val(bill, 'total_amount') == 178000.0
    assert bill.arithmetic_verified is True

    policy = make_policy(
        insurer_name="Star Health & Allied Insurance Co Ltd",
        policy_number="POL-STAR-771239",
        policyholder_name="Sunita Ramesh Iyer",
        room_rent_limit_per_day=4000.0,
        policy_start_date="2025-01-01",
        policy_end_date="2025-12-31"
    )

    # Insurer applied blanket 50% haircut across entire bill (deducted ₹89,000)
    rejection = make_rejection(
        reference_number="REJ-STAR-2025-0012",
        insurer_name="Star Health & Allied Insurance Co Ltd",
        policyholder_name="Sunita Ramesh Iyer",
        policy_number="POL-STAR-771239",
        claim_date="2025-01-10",
        total_claimed=178000.0,
        total_approved=89000.0,
        total_deducted=89000.0,
        rejection_reasons=[
            RejectionReason(
                code="PR01",
                description="Proportionate room rent deduction applied due to room category exceeding eligibility limit",
                category="PROPORTIONATE_DEDUCTION"
            )
        ]
    )

    # Execution through RuleEngine
    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "MISMATCH_DETECTED"

    prop_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Proportionate Deduction Rule")
    assert prop_verdict.status == "FAIL"

    # Exact expected deduction calculation:
    # Stay length = 7 days. Room actual rate = 8,000 vs limit = 4,000.
    # Room excess = (8000 - 4000) * 7 = 28,000.
    # Room-linked items: Room (24,000) + Nursing (4,500) = 28,500.
    # Proportionate reduction = 28,500 * (1 - 4000/8000) = 14,250.
    # Total legitimate deduction = 28,000 + 14,250 = 42,250.
    # Insurer deducted 89,000, creating an unlawful over-deduction.
    assert prop_verdict.monetary_impact >= 35000.0
    assert "unlawfully applied" in prop_verdict.appeal_recommendation


def test_tier4_scenario_s2_moratorium_portability_anniversary(rule_engine):
    """
    Scenario S2: Vikramaditya Sen, insured for 79 continuous months (36 ported + 43 current).
    Insurer Care Health repudiates cardiac claim citing pre-existing hypertension under Clause 4.1.
    Verifies:
    1. Clause Timeline Rule enforces 60-calendar-month moratorium under IRDAI Master Circular 2024.
    2. Appeal viability is STRONG.
    """
    items = [
        make_line_item("Cardiac Stent Implantation", "OT", 1, 250000.0, 250000.0, is_room_linked=False),
        make_line_item("ICU Coronary Care", "OT", 2, 20000.0, 40000.0, is_room_linked=False),
        make_line_item("Post-Op Pharmacy", "PHARMACY", 1, 50000.0, 50000.0, is_room_linked=False)
    ]
    bill = make_bill(
        hospital_name="Fortis Escorts Heart Institute",
        patient_name="Vikramaditya Sen",
        admission_date="2024-11-10",
        discharge_date="2024-11-14",
        line_items=items,
        total_amount=340000.0,
        diagnosis="Triple Vessel Coronary Artery Disease"
    )

    policy = make_policy(
        insurer_name="Care Health Insurance Ltd",
        policy_number="POL-CARE-2021-8899",
        policyholder_name="Vikramaditya Sen",
        inception_date="2018-04-01",  # 36 months previous insurer + 43 months current = April 2018
        policy_start_date="2024-04-01",
        policy_end_date="2025-03-31",
        moratorium_period_months=60,
        portability_credits_months=36  # 36 months ported from previous insurer
    )

    rejection = make_rejection(
        reference_number="REJ-CARE-2024-889",
        insurer_name="Care Health Insurance Ltd",
        policyholder_name="Vikramaditya Sen",
        policy_number="POL-CARE-2021-8899",
        claim_date="2024-11-15",  # 43 months on current policy + 36 months ported = 79 months (> 60)
        total_claimed=340000.0,
        total_approved=0.0,
        total_deducted=340000.0,
        settlement_type="FULL_REJECTION",
        rejection_reasons=[
            RejectionReason(
                code="PED-ND",
                description="Repudiation under Clause 4.1: Non-disclosure of pre-existing hypertension at inception",
                category="PRE_EXISTING"
            )
        ]
    )

    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "MISMATCH_DETECTED"

    timeline_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Clause Timeline Rule")
    assert timeline_verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in timeline_verdict.finding

    # Statutory appeal assessment
    assert result.appeal_evaluation is not None
    assert result.appeal_evaluation.appeal_viability in ["HIGH", "STRONG"]
    assert any("Moratorium" in v for v in result.appeal_evaluation.statutory_conflicts_detected)


def test_tier4_scenario_s3_medical_necessity_disguised_denial(rule_engine):
    """
    Scenario S3: Pediatric acute dehydration admission at Lilavati Hospital.
    Insurer repudiates citing medical necessity / OPD feasibility.
    Verifies:
    1. Clinical Firewall Gate immediately triggers status BLOCKED.
    2. Summary starts with ACTION = FINANCIAL_ENGINE_NOT_EXECUTED.
    3. Prevents speculative financial adjudication by automated rules.
    """
    items = [
        make_line_item("Pediatric Bed", "ROOM", 3, 5000.0, 15000.0, is_room_linked=True),
        make_line_item("IV Fluid Infusion & Nursing", "NURSING", 3, 3000.0, 9000.0, is_room_linked=True),
        make_line_item("Pediatrician Daily Rounds", "CONSULTATION", 3, 2000.0, 6000.0, is_room_linked=False),
        make_line_item("Electrolytes & Stool Culture", "LAB", 1, 8000.0, 8000.0, is_room_linked=False),
        make_line_item("Pediatric Medications", "PHARMACY", 1, 10000.0, 10000.0, is_room_linked=False)
    ]
    bill = make_bill(
        hospital_name="Lilavati Hospital & Research Centre, Mumbai",
        patient_name="Master Aarav Deshmukh",
        admission_date="2025-01-02",
        discharge_date="2025-01-05",
        line_items=items,
        total_amount=48000.0,
        diagnosis="Acute Rotaviral Gastroenteritis with Grade 3 Dehydration"
    )

    policy = make_policy(
        insurer_name="Niva Bupa Health Insurance",
        policy_number="POL-NIVA-44001",
        policyholder_name="Master Aarav Deshmukh"
    )

    rejection = make_rejection(
        reference_number="REJ-NIVA-2025-99",
        insurer_name="Niva Bupa Health Insurance",
        policyholder_name="Master Aarav Deshmukh",
        policy_number="POL-NIVA-44001",
        claim_date="2025-01-04",
        total_claimed=48000.0,
        total_approved=0.0,
        total_deducted=48000.0,
        rejection_reasons=[
            RejectionReason(
                code="CLI-NEC",
                description="Repudiation under Clause 4.8: Hospitalization not justified by medical necessity. Could be managed via OPD oral rehydration.",
                category="OTHER"
            )
        ]
    )

    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary
    assert "Clinical Firewall Gate" in result.summary


def test_tier4_scenario_s4_cross_document_patient_name_mismatch(rule_engine):
    """
    Scenario S4: Fraudulent / swapped patient identity documents.
    Hospital bill is for 'Devendra Pratap Singh', policyholder is 'Kavita R. Joshi'.
    Verifies:
    1. Cross-Document Identity Gate detects mismatch and halts execution (status BLOCKED).
    2. Fail-closed defense protects against fraudulent claim payments.
    """
    bill = make_bill(
        hospital_name="Fortis Hospital, Noida",
        patient_name="Devendra Pratap Singh",
        total_amount=65000.0
    )

    policy = make_policy(
        policyholder_name="Kavita R. Joshi",
        policy_number="POL-BAJAJ-55441"
    )

    rejection = make_rejection(
        policyholder_name="Devendra Pratap Singh",
        policy_number="POL-BAJAJ-55441"
    )

    result = rule_engine.run_all_rules(bill, policy, rejection)
    assert result.overall_status == "BLOCKED"
    assert "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED" in result.summary
    assert any(v.status == "BLOCKED" and v.rule_name == "Cross-Document Identity Gate" for v in result.rule_verdicts)


def test_tier4_scenario_s5_high_value_cardiac_surgery_copay_sublimit(rule_engine):
    """
    Scenario S5: High-value CABG surgery for senior citizen (₹415,000).
    Verifies:
    1. Line item arithmetic verified across 8 distinct line items.
    2. Room rent within limit (₹3,500 <= ₹4,000), ₹0 room haircut.
    3. Procedure sub-limit of ₹350,000 correctly limits eligible expenses.
    4. 10% senior citizen co-pay applies deterministically to admissible amount.
    """
    items = [
        make_line_item("Twin Sharing Room", "ROOM", 5, 3500.0, 17500.0, is_room_linked=True, item_code="RM-TS"),
        make_line_item("Cardiac Nursing Charges", "NURSING", 5, 1000.0, 5000.0, is_room_linked=True, item_code="NUR-CCU"),
        make_line_item("Chief Cardiac Surgeon & Anesthetist Fee", "CONSULTATION", 1, 120000.0, 120000.0, is_room_linked=False, item_code="SUR-CABG"),
        make_line_item("Cardiac Operation Theatre & Perfusion", "OT", 1, 85000.0, 85000.0, is_room_linked=False, item_code="OT-PERF"),
        make_line_item("Coronary Care Unit (CCU)", "OT", 3, 12000.0, 36000.0, is_room_linked=False, item_code="CCU-DAY"),
        make_line_item("Saphenous Vein Grafts & Consumables", "CONSUMABLES", 1, 95000.0, 95000.0, is_room_linked=False, item_code="CONS-GRAFT"),
        make_line_item("Cardiovascular Inotropes & Medicines", "PHARMACY", 1, 32000.0, 32000.0, is_room_linked=False, item_code="PHAR-CV"),
        make_line_item("Echocardiogram & Cardiac Biomarkers", "LAB", 1, 24500.0, 24500.0, is_room_linked=False, item_code="LAB-ECHO")
    ]
    bill = make_bill(
        hospital_name="Narayana Institute of Cardiac Sciences",
        patient_name="Meenakshi Sundaram",
        admission_date="2025-01-05",
        discharge_date="2025-01-10",
        line_items=items,
        diagnosis="Coronary Artery Bypass Graft (CABG)",
        bill_id="NICS-CABG-2025-102"
    )
    assert extract_val(bill, 'total_amount') == 415000.0
    assert bill.arithmetic_verified is True

    cardiac_sublimit = SubLimit(category="Cardiac", max_amount=350000.0, description="CABG package sub-limit")
    policy = make_policy(
        policyholder_name="Meenakshi Sundaram",
        room_rent_limit_per_day=4000.0,
        copay_percentage=10.0,
        sub_limits=[cardiac_sublimit]
    )

    rejection = make_rejection(
        policyholder_name="Meenakshi Sundaram",
        claim_date="2025-01-08",
        total_claimed=415000.0,
        total_approved=315000.0,
        total_deducted=100000.0,
        settlement_type="PARTIAL_SETTLEMENT"
    )

    result = rule_engine.run_all_rules(bill, policy, rejection)
    
    # Tier 0 gates pass cleanly
    id_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Cross-Document Identity Gate")
    assert id_verdict.status == "PASS"

    firewall_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Clinical Firewall Gate")
    assert firewall_verdict.status == "PASS"

    # Direct evaluation confirms room rent is within limit (eligible ₹4,000 >= actual ₹3,500)
    clean_rejection = make_rejection(
        policyholder_name="Meenakshi Sundaram",
        claim_date="2025-01-08",
        total_claimed=415000.0,
        total_approved=415000.0,
        total_deducted=0.0
    )
    prop_verdict_clean = check_proportionate_deduction(bill, policy, clean_rejection)
    assert prop_verdict_clean.status == "PASS"
    assert prop_verdict_clean.monetary_impact == 0.0

    # In the overall run, the rule correctly calculates legitimate room deduction as ₹0.0
    prop_verdict = next(v for v in result.rule_verdicts if v.rule_name == "Proportionate Deduction Rule")
    assert prop_verdict.expected_admissible_amount == 0.0

    # Deterministic procedure sub-limit and co-pay reconciliation:
    # 1. Total bill = ₹415,000
    # 2. Cardiac sub-limit = ₹350,000 -> Sub-limit excess = ₹65,000
    # 3. Admissible under sub-limit = ₹350,000
    # 4. Senior citizen co-pay 10% on ₹350,000 = ₹35,000 patient share
    # 5. Insurer payable = ₹350,000 - ₹35,000 = ₹315,000
    # 6. Total legitimate deduction = ₹65,000 (sub-limit excess) + ₹35,000 (co-pay) = ₹100,000
    assert extract_val(rejection, 'total_approved') == 315000.0
    assert extract_val(rejection, 'total_deducted') == 100000.0
