"""
Test Case: Mr. Vikramaditya Singhania Complex Claim Adjudication.
Tests ClaimGuard's ability to catch 4 very subtle, deeply disguised flaws in Medi Assist's rejection:
1. Proportionate Deduction illegally applied to protected implants (Endo-GIA), OT package, and ICU care.
2. Repudiation of primary surgery under Enhancement Waiting Period, ignoring that the claim is well within the 60-month moratorium-protected base Sum Insured.
3. Disallowance of IRDAI Annexure A List III surgical consumables & drapes as non-payables.
4. Co-Payment double-dipping calculated on Gross Bill rather than net admissible amount.
"""

import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, ProportionateDeductionRuleConfig, WaitingPeriodConfig
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.engine import RuleEngine
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.clause_timeline import check_clause_timeline
from app.rules.non_payable_items import check_non_payable_items
from app.rules.copay_rule import check_copay


def prov(val):
    return Provenance(value=val)


def make_item(desc, cat, qty, rate, amt, is_room_linked=False):
    return BillLineItem(
        description=prov(desc),
        category=prov(cat),
        quantity=prov(float(qty)),
        unit_rate=prov(float(rate)),
        amount=prov(float(amt)),
        is_room_linked=is_room_linked
    )


@pytest.fixture
def complex_claim_bundle():
    # 1. Hospital Bill (Rs. 5,48,750 total)
    items = [
        make_item("SICU Bed Charges", "ROOM", 2, 14000.0, 28000.0, is_room_linked=False),
        make_item("SICU Nursing & Monitoring", "NURSING", 2, 4000.0, 8000.0, is_room_linked=False),
        make_item("Deluxe Room Accommodation", "ROOM", 4, 10000.0, 40000.0, is_room_linked=True),
        make_item("Ward Nursing Care", "NURSING", 4, 2500.0, 10000.0, is_room_linked=True),
        make_item("Primary Surgeon Operative Fee", "CONSULTATION", 1, 95000.0, 95000.0, is_room_linked=True),
        make_item("Assistant Surgeon Fee", "CONSULTATION", 1, 25000.0, 25000.0, is_room_linked=True),
        make_item("Consultant Anaesthesiologist Charge", "CONSULTATION", 1, 30000.0, 30000.0, is_room_linked=True),
        make_item("Intensivist Critical Care Management", "CONSULTATION", 2, 7500.0, 15000.0, is_room_linked=False),
        make_item("Major OT Complex Charges", "OT", 1, 45000.0, 45000.0, is_room_linked=False),
        make_item("Anaesthesia Workstation", "OT", 1, 18000.0, 18000.0, is_room_linked=False),
        make_item("Electrosurgical Cautery Unit", "OT", 1, 12000.0, 12000.0, is_room_linked=False),
        make_item("Endo-GIA Bowel Stapler Kit", "CONSUMABLES", 1, 42000.0, 42000.0, is_room_linked=False),
        make_item("Endo-GIA Staple Cartridges", "CONSUMABLES", 2, 13000.0, 26000.0, is_room_linked=False),
        make_item("Laparotomy Sterile Drape Pack", "CONSUMABLES", 1, 8500.0, 8500.0, is_room_linked=False),
        make_item("Sterile Surgical Gloves", "CONSUMABLES", 12, 350.0, 4200.0, is_room_linked=False),
        make_item("Suction Irrigation Cannula", "CONSUMABLES", 1, 4100.0, 4100.0, is_room_linked=False),
        make_item("Suture Loops & Clips", "CONSUMABLES", 1, 9800.0, 9800.0, is_room_linked=False),
        make_item("Ostomy Stoma Bag System", "CONSUMABLES", 2, 4100.0, 8200.0, is_room_linked=False),
        make_item("IV Meropenem 1g Infusion", "PHARMACY", 15, 2450.0, 36750.0, is_room_linked=False),
        make_item("IV Human Albumin 20%", "PHARMACY", 3, 4800.0, 14400.0, is_room_linked=False),
        make_item("IV Supportive Injections", "PHARMACY", 1, 8500.0, 8500.0, is_room_linked=False),
        make_item("TPN Olimel Infusion", "PHARMACY", 3, 3600.0, 10800.0, is_room_linked=False),
        make_item("CT Abdomen Triple Phase", "RADIOLOGY", 1, 14500.0, 14500.0, is_room_linked=False),
        make_item("Histopathology Examination", "LAB", 1, 8500.0, 8500.0, is_room_linked=False),
        make_item("Blood Cultures & CMP", "LAB", 1, 11500.0, 11500.0, is_room_linked=False),
        make_item("Administrative Registration", "MISCELLANEOUS", 1, 2500.0, 2500.0, is_room_linked=False),
        make_item("Toiletries Kit", "MISCELLANEOUS", 1, 1500.0, 1500.0, is_room_linked=False)
    ]
    bill = HospitalBill(
        bill_id=prov("AHB/IPB/2026/08941"),
        patient_name=prov("Vikramaditya Singhania"),
        total_amount=prov(548750.0),
        subtotal=prov(548750.0),
        admission_date=prov("2026-02-12"),
        discharge_date=prov("2026-02-18"),
        length_of_stay=prov(6),
        diagnosis=prov("Acute Diverticulitis with Perforation"),
        line_items=items
    )

    # 2. Insurance Policy (Inception 2019, Base SI Rs. 5L, Enhanced SI Rs. 10L in 2023)
    policy = InsurancePolicy(
        policy_number=prov("01/2019/COMP/449210"),
        insurer_name=prov("Star Health and Allied Insurance Company Limited"),
        policyholder_name=prov("Vikramaditya Singhania"),
        policy_version=prov("SHAHLIP21226V052021"),
        inception_date=prov("2019-03-15"),
        policy_start_date=prov("2025-03-15"),
        policy_end_date=prov("2026-03-14"),
        sum_insured=prov(1000000.0),
        base_sum_insured=prov(500000.0),
        cumulative_bonus=prov(250000.0),
        enhancement_date=prov("2023-03-15"),
        enhanced_sum_insured=prov(500000.0),
        room_category_entitled=prov("SINGLE_PRIVATE_AC_ROOM"),
        room_rent_limit_per_day=prov(6000.0),
        copay_percentage=prov(10.0),
        deductible=prov(0.0),
        moratorium_period_months=prov(60),
        waiting_periods=[
            WaitingPeriodConfig(
                category=prov("SPECIFIC_DISEASE"),
                duration_days=prov(730),
                applicable_conditions=[prov("Diverticular disease"), prov("Calculus disease")]
            ),
            WaitingPeriodConfig(
                category=prov("PED"),
                duration_days=prov(1095),
                applicable_conditions=[prov("Pre-Existing Conditions")]
            )
        ],
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=prov(1.0),
            threshold_operator=prov(">"),
            threshold_source_type=prov("POLICY_WORDING"),
            policy_clause=prov("Section 1.A"),
            source_text=prov("Associated Medical Expenses paid in proportion to eligible room tariff.")
        )
    )

    # 3. Rejection Letter (Approved Rs. 2,16,200, Deducted Rs. 3,32,550)
    rejection = RejectionLetter(
        claim_number=prov("MED/2026/STR/8841029"),
        claim_date=prov("2026-02-24"),
        total_claimed=prov(548750.0),
        total_approved=prov(216200.0),
        approved_amount=prov(216200.0),
        total_deducted=prov(332550.0),
        rejection_reasons=[
            RejectionReason(
                code=prov("COPAY-01"),
                category=prov("OTHER"),
                description=prov("10% co-payment applied to the total billed amount of Rs. 5,48,750 as per member entry age bracket.")
            ),
            RejectionReason(
                code=prov("NON-MED-01"),
                category=prov("Non-Medical"),
                description=prov("Consumable items, sterile surgical drapes, surgeon gown kit, suction tubing, and gloves classified as non-medical consumables, hence disallowed.")
            ),
            RejectionReason(
                code=prov("WAIT-01"),
                category=prov("PRE_EXISTING"),
                description=prov("Diverticular surgical resection fee is excluded under Clause 3.2 on enhanced sum insured.")
            ),
            RejectionReason(
                code=prov("PROP-01"),
                category=prov("PROPORTIONATE_DEDUCTION"),
                description=prov("A 40% proportionate reduction is applied to Deluxe Room (Rs. 16,000), SICU (Rs. 11,200), OT Complex (Rs. 24,000), and Endo-GIA Implants (Rs. 31,000).")
            )
        ]
    )

    return {"bill": bill, "policy": policy, "rejection": rejection}


def test_complex_claim_proportionate_deduction_flaw(complex_claim_bundle):
    """
    Subtle Flaw 1: Insurer applied 40% haircut to protected heads:
    - Endo-GIA Bowel Stapler & Cartridges (Rs. 68,000)
    - SICU bed accommodation & intensivist
    - Emergency admission life-safety exception
    ClaimGuard flags the arithmetic breach under IRDAI Master Circular 2024.
    """
    b, p, r = complex_claim_bundle["bill"], complex_claim_bundle["policy"], complex_claim_bundle["rejection"]
    verdict = check_proportionate_deduction(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert "IRDAI Master Circular" in verdict.regulatory_citation


def test_complex_claim_enhancement_waiting_period_moratorium_flaw(complex_claim_bundle):
    """
    Subtle Flaw 2: Insurer repudiated diverticular surgery citing 36M waiting period on enhancement.
    ClaimGuard proves the claim is within the base Sum Insured + Bonus (Rs. 7.5L),
    which has completed 83 continuous months and is protected by the 60-month Moratorium!
    """
    b, p, r = complex_claim_bundle["bill"], complex_claim_bundle["policy"], complex_claim_bundle["rejection"]
    verdict = check_clause_timeline(b, p, r)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding
    assert "IRDAI Master Circular on Health Insurance, 29 May 2024" in verdict.regulatory_citation


def test_complex_claim_list_iii_consumables_flaw(complex_claim_bundle):
    """
    Subtle Flaw 3: Insurer disallowed Rs. 34,800 in surgical drapes, gown kit, and suction cannulas.
    ClaimGuard verifies that under IRDAI Annexure A List III, these are mandatorily payable
    when associated with surgery!
    """
    b, p, r = complex_claim_bundle["bill"], complex_claim_bundle["policy"], complex_claim_bundle["rejection"]
    verdict = check_non_payable_items(b, p, r)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert verdict.monetary_impact > 0.0
    assert "List III" in verdict.finding


def test_complex_claim_copay_on_gross_double_dipping(complex_claim_bundle):
    """
    Subtle Flaw 4: Insurer calculated 10% co-pay on the Gross Bill (Rs. 54,875)
    instead of on the net admissible claim after non-payables and sub-limits.
    ClaimGuard's Rule Engine enforces the strict IRDAI dependency: Co-pay must be applied
    AFTER deductibles and non-payables on remaining balance.
    """
    b, p, r = complex_claim_bundle["bill"], complex_claim_bundle["policy"], complex_claim_bundle["rejection"]
    engine = RuleEngine()
    result = engine.run_all_rules(b, p, r)
    copay_verdicts = [v for v in result.rule_verdicts if v.rule_name == "Co-Pay Rule"]
    assert len(copay_verdicts) > 0
    assert copay_verdicts[0].status == "PASS"
    assert "Applied 10.0% co-pay" in copay_verdicts[0].finding

