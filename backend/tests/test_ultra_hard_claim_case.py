"""
Test Suite: Ultra-Hard Claim Adjudication (Mrs. Rajeshwari Sundaram / Max Super Speciality / Care Supreme / Vidal Health TPA).

Validates that ClaimGuard catches all 5 distinct, deeply disguised flaws:
1. Cumulative Bonus Forfeiture under grace period (IRDAI Master Circular 2024 Para 3.8 & Reg 13): Rs. 2,35,000.00
2. Advanced Energy Devices repudiated under List I Entry 42 knives (IRDAI Annexure A List III & Para 5.4): Rs. 86,000.00
3. Sepsis ICU Glycemic Protocol repudiated under lifestyle Excl-18 (Surviving Sepsis Standards & Para 5.4): Rs. 58,000.00
4. Secondary Surgery 50% Multi-Cut applied to OT & Consumables (Clause 3.4 & Para 5.4): Rs. 33,000.00
5. Emergency Inpatient Modern Treatment Day-Care Sub-Limit Cap (Clause 4.14 & Para 5.4): Rs. 15,500.00

Total Recoverable Ground Truth: Rs. 4,26,500.00 (~Rs. 4.27 Lakhs)
Legitimate Deductions: List I Admin Registration (Rs. 3,500.00) + 50% 2nd procedure surgeon discount (Rs. 17,500.00) = Rs. 21,000.00
"""

import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, ProportionateDeductionRuleConfig
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.engine import RuleEngine
from app.rules.cumulative_bonus_protection import evaluate_cumulative_bonus_protection
from app.rules.multiple_surgery_rule import evaluate_multiple_surgery_protection
from app.rules.non_payable_items import check_non_payable_items
from app.rules.sepsis_icu_protocol_rule import evaluate_sepsis_icu_protocol
from app.rules.modern_treatment_rule import evaluate_modern_treatment_protection


def prov(val):
    return Provenance(value=val)


def make_item(desc, cat, qty, rate, amt, is_room_linked=False, item_code=None):
    return BillLineItem(
        description=prov(desc),
        category=prov(cat),
        quantity=prov(float(qty)),
        unit_rate=prov(float(rate)),
        amount=prov(float(amt)),
        is_room_linked=is_room_linked,
        item_code=prov(item_code) if item_code else None
    )


@pytest.fixture
def ultra_hard_bundle():
    # 32 Line items totaling exactly Rs. 7,85,600.00
    items = [
        make_item("Surgical ICU Bed Charges", "ROOM", 3, 16000.0, 48000.0, False, "ITEM_0"),
        make_item("SICU Dedicated Critical Care Nursing Care", "NURSING", 3, 4500.0, 13500.0, False, "ITEM_1"),
        make_item("Single Private Deluxe A/C Room Bed Charges", "ROOM", 4, 9000.0, 36000.0, True, "ITEM_2"),
        make_item("Inpatient Ward General Nursing", "NURSING", 4, 2500.0, 10000.0, True, "ITEM_3"),
        make_item("Therapeutic ERCP Operative Fee", "CONSULTATION", 1, 35000.0, 35000.0, True, "ITEM_4"),
        make_item("Advanced Endoscopy / Fluoroscopy Suite", "OT", 1, 22000.0, 22000.0, False, "ITEM_5"),
        make_item("Digital C-Arm Fluoroscopy Real-Time X-Ray", "OT", 1, 12000.0, 12000.0, False, "ITEM_6"),
        make_item("Dormia Stone Extraction Basket", "CONSUMABLES", 1, 32000.0, 32000.0, False, "ITEM_7"),
        make_item("Chief Surgeon Operative Fee", "CONSULTATION", 1, 94500.0, 94500.0, True, "ITEM_8"),
        make_item("Senior Co-Surgeon / Assistant GI Surgeon", "CONSULTATION", 1, 30000.0, 30000.0, True, "ITEM_9"),
        make_item("Senior Consultant Anaesthesiologist Charge", "CONSULTATION", 1, 38000.0, 38000.0, True, "ITEM_10"),
        make_item("Major Ultra-Clean Laminar Flow OT Complex", "OT", 1, 55000.0, 55000.0, False, "ITEM_11"),
        make_item("Advanced Anaesthesia Workstation", "OT", 1, 20000.0, 20000.0, False, "ITEM_12"),
        make_item("Ethicon Harmonic ACE+ 36cm Ultrasonic", "CONSUMABLES", 1, 48000.0, 48000.0, False, "ITEM_13"),
        make_item("LigaSure Blunt Tip Laparoscopic", "CONSUMABLES", 1, 38000.0, 38000.0, False, "ITEM_14"),
        make_item("Silicone T-Tube Biliary Decompression", "CONSUMABLES", 1, 14500.0, 14500.0, False, "ITEM_15"),
        make_item("Laparotomy Major Surgical Sterile Drape Pack", "CONSUMABLES", 1, 9500.0, 9500.0, False, "ITEM_16"),
        make_item("Sterile Powder-Free Latex Surgical Gloves", "CONSUMABLES", 14, 350.0, 4900.0, False, "ITEM_17"),
        make_item("Abdominal Yankauer Suction Cannula", "CONSUMABLES", 1, 4200.0, 4200.0, False, "ITEM_18"),
        make_item("Antibacterial Monocryl & PDS Loop Suture", "CONSUMABLES", 1, 11000.0, 11000.0, False, "ITEM_19"),
        make_item("Senior Consultant Endocrinologist ICU Management", "CONSULTATION", 3, 6000.0, 18000.0, False, "ITEM_20"),
        make_item("Continuous IV Regular Insulin Infusion Protocol", "PHARMACY", 3, 4500.0, 13500.0, False, "ITEM_21"),
        make_item("Intensive Point-of-Care Arterial Blood Gas", "LAB", 6, 2400.0, 14400.0, False, "ITEM_22"),
        make_item("Continuous Glycemic Glucose Strips & Biosensor", "CONSUMABLES", 1, 12100.0, 12100.0, False, "ITEM_23"),
        make_item("IV Meropenem 1g Infusion", "PHARMACY", 21, 2600.0, 54600.0, False, "ITEM_24"),
        make_item("IV Human Albumin 20% 100ml Infusion", "PHARMACY", 4, 4900.0, 19600.0, False, "ITEM_25"),
        make_item("IV Analgesics, Antiemetics, Pantoprazole", "PHARMACY", 1, 14800.0, 14800.0, False, "ITEM_26"),
        make_item("Total Parenteral Nutrition", "PHARMACY", 3, 4200.0, 12600.0, False, "ITEM_27"),
        make_item("Emergency Contrast Triple-Phase CT Abdomen", "RADIOLOGY", 1, 22500.0, 22500.0, False, "ITEM_28"),
        make_item("Surgical Pathology - Gallbladder Resection", "LAB", 1, 9500.0, 9500.0, False, "ITEM_29"),
        make_item("Comprehensive Liver Function, Amylase, Lipase", "LAB", 1, 14400.0, 14400.0, False, "ITEM_30"),
        make_item("Inpatient Admission Registration, ID Wristband", "MISCELLANEOUS", 1, 3500.0, 3500.0, False, "ITEM_31"),
    ]
    bill = HospitalBill(
        bill_id=prov("MAX/SKT/IPB/2026/10492"),
        patient_name=prov("Mrs. Rajeshwari Sundaram"),
        hospital_name=prov("Max Super Speciality Hospital, Saket, New Delhi"),
        total_amount=prov(785600.0),
        subtotal=prov(785600.0),
        admission_date=prov("2026-03-04"),
        discharge_date=prov("2026-03-11"),
        length_of_stay=prov(7),
        diagnosis=prov("Acute Gangrenous Cholecystitis with Choledocholithiasis, Biliary Pancreatitis & Severe Sepsis"),
        line_items=items,
        arithmetic_verified=True
    )

    prop_rule = ProportionateDeductionRuleConfig(
        threshold_value=prov(1.0),
        threshold_operator=prov(">"),
        threshold_source_type=prov("POLICY_WORDING"),
        policy_clause=prov("Clause 2.3")
    )
    policy = InsurancePolicy(
        policy_number=prov("11/2020/CARE/998231"),
        insurer_name=prov("Care Health Insurance Limited"),
        policyholder_name=prov("Mrs. Rajeshwari Sundaram"),
        policy_version=prov("CHIHLIP23089V032223"),
        inception_date=prov("2020-01-15"),
        policy_start_date=prov("2026-01-28"),
        policy_end_date=prov("2027-01-27"),
        sum_insured=prov(1200000.0),
        base_sum_insured=prov(800000.0),
        cumulative_bonus=prov(400000.0),
        room_category_entitled=prov("SINGLE_PRIVATE_AC_ROOM"),
        room_rent_limit_per_day=prov(0.0),
        copay_percentage=prov(0.0),
        deductible=prov(0.0),
        moratorium_period_months=prov(60),
        waiting_periods=[],
        proportionate_deduction_rule=prop_rule,
        covers_mental_health=prov(True)
    )

    rejection_reasons = [
        RejectionReason(
            code=prov("BONUS-FORFEIT-01"),
            category=prov("OTHER"),
            amount=prov(235000.0),
            description=prov("Sum Insured Cap / Bonus Forfeiture (Cumulative Bonus Erasure of Rs. 4,00,000 citing renewal on 28-Jan-2026, 13 days past anniversary) (Disallowed: Rs. 235,000.00)")
        ),
        RejectionReason(
            code=prov("ENERGY-DEV-01"),
            category=prov("Non-Medical"),
            amount=prov(86000.0),
            description=prov("Advanced Energy Devices (Harmonic & LigaSure Shears) disallowed under Entry 42 (Disallowed: Rs. 86,000.00)")
        ),
        RejectionReason(
            code=prov("METABOLIC-EXCL-01"),
            category=prov("PRE_EXISTING"),
            amount=prov(58000.0),
            description=prov("Metabolic & Glycemic Protocol (Endocrine, Insulin, ABG Series) disallowed under Excl-18 (Disallowed: Rs. 58,000.00)")
        ),
        RejectionReason(
            code=prov("MULTI-SURG-01"),
            category=prov("PROPORTIONATE_DEDUCTION"),
            amount=prov(50500.0),
            description=prov("Secondary Procedure Multi-Cut (50% Cut on ERCP OT & Consumables) under Clause 3.4 (Disallowed: Rs. 50,500.00)")
        ),
        RejectionReason(
            code=prov("MODERN-TREAT-01"),
            category=prov("OTHER"),
            amount=prov(15500.0),
            description=prov("Modern Treatment Capping (Endoscopic Sub-Limit Exhaustion) under Clause 4.14 (Disallowed: Rs. 15,500.00)")
        ),
        RejectionReason(
            code=prov("NON-MED-ADMIN-01"),
            category=prov("Non-Medical"),
            amount=prov(2500.0),
            description=prov("List I Non-Medical Overheads (Registration & ID Wristband) disallowed (Disallowed: Rs. 2,500.00)")
        )
    ]
    rejection = RejectionLetter(
        claim_number=prov("VID/2026/CARE/7719024"),
        policy_number=prov("11/2020/CARE/998231"),
        policyholder_name=prov("Mrs. Rajeshwari Sundaram"),
        claim_date=prov("2026-03-22"),
        total_claimed=prov(785600.0),
        total_approved=prov(338100.0),
        approved_amount=prov(338100.0),
        total_deducted=prov(447500.0),
        rejection_reasons=rejection_reasons,
        reasons=rejection_reasons,
        settlement_type=prov("PARTIAL_SETTLEMENT"),
        remarks=prov("Adjudicated by Vidal Health TPA for Care Health Insurance")
    )
    return {"bill": bill, "policy": policy, "rejection": rejection}


def test_ultra_hard_cumulative_bonus_protection(ultra_hard_bundle):
    """Flaw 1: Vidal arbitrarily erased Rs. 4L bonus for a 13-day renewal within the 30-day statutory grace period."""
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    verdict = evaluate_cumulative_bonus_protection(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 235000.0
    assert verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Regulation 13" in verdict.regulatory_citation
    assert "grace period" in verdict.finding.lower()
    assert verdict.actual_claim_fact is not None
    assert verdict.applicable_policy_rule is not None


def test_ultra_hard_non_payable_items_energy_devices(ultra_hard_bundle):
    """Flaw 2: Vidal disallowed Harmonic ACE+ and LigaSure under List I Entry 42 razor blades."""
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    verdict = check_non_payable_items(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 86000.0
    assert verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Harmonic" in verdict.finding or "Energy" in verdict.finding
    assert "List III" in verdict.regulatory_citation or "Para 5.4" in verdict.regulatory_citation


def test_ultra_hard_sepsis_icu_protocol(ultra_hard_bundle):
    """Flaw 3: Vidal repudiated ICU glycemic insulin management under lifestyle Excl-18."""
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    verdict = evaluate_sepsis_icu_protocol(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 58000.0
    assert verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Exclusion 18" in verdict.finding or "sepsis" in verdict.finding.lower()


def test_ultra_hard_multiple_surgery_rule(ultra_hard_bundle):
    """Flaw 4: Vidal slashed 50% across OT suite and consumables instead of restricting to surgeon fee."""
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    verdict = evaluate_multiple_surgery_protection(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 33000.0
    assert verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Clause 3.4" in verdict.applicable_policy_rule


def test_ultra_hard_modern_treatment_sublimit(ultra_hard_bundle):
    """Flaw 5: Vidal imposed a Rs. 50k elective day-care cap on emergency inpatient ERCP."""
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    verdict = evaluate_modern_treatment_protection(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 15500.0
    assert verdict.legal_track == "TRACK_B_STATUTORY_BREACH"
    assert "Clause 4.14" in verdict.finding


def test_ultra_hard_end_to_end_engine_reconciliation(ultra_hard_bundle):
    """
    End-to-end full engine test:
    Total claimed: Rs. 7,85,600.00
    Insurer approved: Rs. 3,38,100.00
    Insurer disallowed: Rs. 4,47,500.00
    Legitimate deductions: Rs. 21,000.00 (List I Admin Rs. 3,500 + 50% ERCP surgeon Rs. 17,500)
    Expected admissible: Rs. 7,64,600.00
    Disputed / Recoverable: exactly Rs. 4,26,500.00 (~Rs. 4.27 Lakhs)
    """
    b, p, r = ultra_hard_bundle["bill"], ultra_hard_bundle["policy"], ultra_hard_bundle["rejection"]
    engine = RuleEngine()
    result = engine.run_all_rules(b, p, r)

    assert result.overall_status == "MISMATCH_DETECTED"
    assert result.billed_amount == 785600.0
    assert result.insurer_approved_amount == 338100.0
    assert result.total_disallowed == 447500.0
    assert result.expected_admissible_amount == 764600.0
    assert result.total_monetary_impact == 426500.0

    # Ensure all 5 failing rules are captured with non-generic forensic pillars
    rule_names = {v.rule_name for v in result.rule_verdicts if v.status == "FAIL"}
    assert "Cumulative Bonus & Grace Period Rule" in rule_names
    assert "Non-Payable Items Rule" in rule_names
    assert "Sepsis Glycemic & ICU Protocol Protection Rule" in rule_names
    assert "Multiple Surgery Infrastructure Protection Rule" in rule_names
    assert "Modern Treatment Inpatient Protection Rule" in rule_names

    for v in result.rule_verdicts:
        if v.status == "FAIL":
            assert v.actual_claim_fact is not None, f"Missing actual_claim_fact in {v.rule_name}"
            assert v.applicable_policy_rule is not None, f"Missing applicable_policy_rule in {v.rule_name}"
            assert v.insurer_applied_action is not None, f"Missing insurer_applied_action in {v.rule_name}"
            assert v.expected_action is not None, f"Missing expected_action in {v.rule_name}"
            assert "Governed by insurance policy terms" not in str(v.applicable_policy_rule)
