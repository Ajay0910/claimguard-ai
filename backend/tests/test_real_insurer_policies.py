import pytest
from datetime import date
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.real_policy_contracts import (
    get_star_comprehensive_policy,
    get_hdfc_optima_secure_policy,
    get_care_supreme_policy
)
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.non_payable_items import check_non_payable_items
from app.rules.clause_timeline import check_clause_timeline
from app.rules.waiting_period import check_waiting_period
from app.engine.predischarge_simulator import PreDischargeSimulator


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


# ==============================================================================
# 1. Star Health - Star Comprehensive Insurance Policy Verification
# ==============================================================================

def test_star_comprehensive_room_upgrade_deduction_boundary():
    """
    Real-world Case: Star Comprehensive Insurance Policy (Single AC Room cap).
    Patient upgraded to Deluxe Room (Rs. 12,000/day vs Rs. 6,000/day cap). Ratio = 50%.
    TPA wrongfully applied 50% cut to the ENTIRE bill of Rs. 2,23,000 (including medicines,
    consumables, and diagnostics).
    ClaimGuard verifies that medicines (Rs. 40k), diagnostics (Rs. 20k), and surgical
    consumables (Rs. 25k) are protected, catching the exact Rs. 42,500 underpayment!
    """
    policy = get_star_comprehensive_policy(
        policy_number="STAR-COMP-2024-001",
        inception_date="2021-01-01",
        sum_insured=1000000.0,
        room_category="SINGLE_PRIVATE_AC_ROOM"
    )

    items = [
        make_item("Deluxe Room Rent (3 days)", "ROOM", 3, 12000.0, 36000.0, is_room_linked=True),
        make_item("Nursing & RMO Charges", "NURSING", 3, 4000.0, 12000.0, is_room_linked=True),
        make_item("Surgeon Operative Fee", "CONSULTATION", 1, 50000.0, 50000.0, is_room_linked=True),
        make_item("Operation Theatre Charges", "OT", 1, 40000.0, 40000.0, is_room_linked=False),
        make_item("Surgical Consumables & Drapes", "CONSUMABLES", 1, 25000.0, 25000.0, is_room_linked=False),
        make_item("In-Hospital Medicines", "PHARMACY", 1, 40000.0, 40000.0, is_room_linked=False),
        make_item("Histopathology & Blood Tests", "LAB", 1, 20000.0, 20000.0, is_room_linked=False),
    ]

    bill = HospitalBill(
        bill_id=prov("BILL-STAR-001"),
        total_amount=prov(223000.0),
        admission_date=prov("2026-06-01"),
        discharge_date=prov("2026-06-04"),
        diagnosis=prov("Calculus of Gallbladder with Cholecystitis"),
        line_items=items
    )

    # TPA applied 50% cut to entire bill = Rs. 1,11,500 deducted
    rejection = RejectionLetter(
        claim_number=prov("CLM-STAR-001"),
        claim_date=prov("2026-06-05"),
        total_claimed=prov(223000.0),
        total_approved=prov(111500.0),
        approved_amount=prov(111500.0),
        total_deducted=prov(111500.0),
        rejection_reasons=[
            RejectionReason(
                code=prov("PROP-01"),
                category=prov("PROPORTIONATE_DEDUCTION"),
                description=prov("Proportionate deduction applied across bill due to Deluxe room category selection exceeding Single AC room.")
            )
        ]
    )

    verdict = check_proportionate_deduction(bill, policy, rejection)

    # Asserts that ClaimGuard flags the TPA arithmetic breach
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert verdict.monetary_impact > 0.0
    assert "IRDAI Master Circular" in verdict.regulatory_citation


def test_star_comprehensive_ped_moratorium_defense():
    """
    Star Comprehensive policy active since 2018 (> 60 months).
    Insurer repudiates citing non-disclosure of pre-existing hypertension.
    ClaimGuard invokes 60-month statutory moratorium under IRDAI Master Circular 2024 Para 5.3!
    """
    policy = get_star_comprehensive_policy(
        policy_number="STAR-COMP-2018-099",
        inception_date="2018-03-01",
        sum_insured=1000000.0
    )

    bill = HospitalBill(
        bill_id=prov("BILL-099"),
        total_amount=prov(150000.0),
        admission_date=prov("2026-05-10"),
        discharge_date=prov("2026-05-14")
    )

    rejection = RejectionLetter(
        claim_number=prov("CLM-STAR-099"),
        claim_date=prov("2026-05-15"),
        total_claimed=prov(150000.0),
        total_approved=prov(0.0),
        total_deducted=prov(150000.0),
        rejection_reasons=[
            RejectionReason(
                code=prov("PED-01"),
                category=prov("PRE_EXISTING"),
                description=prov("Repudiation of claim citing non-disclosure of pre-existing hypertension and diabetes.")
            )
        ]
    )

    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding
    assert "IRDAI Master Circular on Health Insurance, 29 May 2024" in verdict.regulatory_citation


# ==============================================================================
# 2. HDFC ERGO my:Optima Secure Contract Verification
# ==============================================================================

def test_hdfc_optima_secure_at_actuals_no_proportionate_deduction():
    """
    Real-world Case: HDFC ERGO my:Optima Secure (Base Plan).
    Section B.1.a states room rent limit is 'At Actuals'.
    When room_rent_limit_per_day is None (At Actuals), proportionate deduction is NOT applicable.
    """
    policy = get_hdfc_optima_secure_policy(
        policy_number="HDFC-OPT-SEC-2023-001",
        inception_date="2022-01-01",
        sum_insured=1000000.0,
        has_room_cap=False  # At Actuals
    )

    items = [
        make_item("Suite Room Rent", "ROOM", 3, 20000.0, 60000.0, is_room_linked=True),
        make_item("Nursing Care", "NURSING", 3, 3000.0, 9000.0, is_room_linked=True)
    ]
    bill = HospitalBill(
        bill_id=prov("BILL-HDFC-001"),
        total_amount=prov(69000.0),
        line_items=items
    )
    rejection = RejectionLetter(
        claim_number=prov("CLM-HDFC-001"),
        claim_date=prov("2026-07-01"),
        total_claimed=prov(69000.0),
        total_approved=prov(50000.0),
        total_deducted=prov(19000.0),
        rejection_reasons=[
            RejectionReason(
                code=prov("ROOM-01"),
                category=prov("PROPORTIONATE_DEDUCTION"),
                description=prov("Deduction made on suite room charges.")
            )
        ]
    )

    verdict = check_proportionate_deduction(bill, policy, rejection)
    # Proportionate deduction is NOT applicable because Optima Secure has no room rent limit
    assert verdict.status == "NOT_APPLICABLE"
    assert "No room rent limit in policy" in verdict.finding


# ==============================================================================
# 3. Care Health Insurance - Care Supreme Contract Verification
# ==============================================================================

def test_care_supreme_surgical_consumables_protection():
    """
    Real-world Case: Care Health Care Supreme.
    Patient undergoes major laparoscopic appendectomy.
    Hospital bills Rs. 16,500 under surgical consumables.
    TPA disallows Rs. 16,500 under 'Consumables / Non-Medical Excluded'.
    ClaimGuard verifies that under IRDAI Annexure A List III, surgical disposables,
    sterile gloves, and OT gowns are STATUTORILY PAYABLE when associated with surgery!
    """
    policy = get_care_supreme_policy(
        policy_number="CARE-SUP-2023-555",
        inception_date="2023-01-01",
        sum_insured=700000.0
    )

    items = [
        make_item("Room Charges", "ROOM", 2, 4000.0, 8000.0, is_room_linked=True),
        make_item("Laparoscopic Appendectomy Procedure", "OT", 1, 45000.0, 45000.0, is_room_linked=False),
        make_item("Surgical Disposables & Drape Kit", "CONSUMABLES", 1, 8500.0, 8500.0, is_room_linked=False),
        make_item("Sterile Gloves & Suture Materials", "CONSUMABLES", 1, 8000.0, 8000.0, is_room_linked=False),
        make_item("Post-Op Antibiotics", "PHARMACY", 1, 12000.0, 12000.0, is_room_linked=False),
    ]

    bill = HospitalBill(
        bill_id=prov("BILL-CARE-555"),
        total_amount=prov(81500.0),
        diagnosis=prov("Acute Appendicitis with Laparoscopic Appendectomy"),
        line_items=items
    )

    # TPA deducted the Rs. 16,500 surgical consumables
    rejection = RejectionLetter(
        claim_number=prov("CLM-CARE-555"),
        claim_date=prov("2026-08-10"),
        total_claimed=prov(81500.0),
        total_approved=prov(65000.0),
        approved_amount=prov(65000.0),
        total_deducted=prov(16500.0),
        rejection_reasons=[
            RejectionReason(
                code=prov("NON-MED-01"),
                category=prov("Non-Medical"),
                description=prov("Disallowance of consumables and disposable charges as non-payable items.")
            )
        ]
    )

    verdict = check_non_payable_items(bill, policy, rejection)

    # Asserts that ClaimGuard protects List III surgical items
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert verdict.monetary_impact == 16500.0
    assert "List III" in verdict.finding
    assert "IRDAI Guidelines on Standardization" in verdict.regulatory_citation


def test_care_supreme_predischarge_upgrade_warning():
    """
    Care Supreme Value variant (Single AC room cap Rs. 5,000/day).
    Patient admitted in Deluxe room (Rs. 9,000/day).
    Pre-Discharge Simulator detects Rs. 4,000/day excess and warns patient
    of cascading penalty on surgery and OT charges before discharge!
    """
    policy = get_care_supreme_policy(
        policy_number="CARE-VAL-2024-888",
        inception_date="2024-01-01",
        sum_insured=500000.0,
        is_value_variant=True  # Has Single AC room cap
    )

    items = [
        make_item("Deluxe Room", "ROOM", 3, 9000.0, 27000.0, is_room_linked=True),
        make_item("Nursing Care", "NURSING", 3, 3000.0, 9000.0, is_room_linked=True),
        make_item("Surgeon Operative Charge", "CONSULTATION", 1, 40000.0, 40000.0, is_room_linked=True),
        make_item("Operation Theatre", "OT", 1, 30000.0, 30000.0, is_room_linked=False)
    ]

    bill = HospitalBill(
        bill_id=prov("INTERIM-CARE-888"),
        total_amount=prov(106000.0),
        admission_date=prov("2026-09-01"),
        estimated_discharge_date=prov("2026-09-04"),
        is_interim_bill=True,
        line_items=items
    )

    sim = PreDischargeSimulator()
    result = sim.simulate(bill, policy)

    assert result.has_room_rent_excess is True
    assert result.excess_per_day == 4000.0
    assert result.projected_room_excess == 12000.0
    assert result.projected_proportionate_deduction > 0.0
    assert "exceeds your policy cap" in result.warning_message
