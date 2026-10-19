import pytest
import os
import tempfile
from datetime import date, timedelta
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, ProportionateDeductionRuleConfig
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.rules.appeal_evaluator import AppealEvaluator
from app.rules.clause_timeline import check_clause_timeline
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.non_payable_items import check_non_payable_items, classify_line_item
from app.engine.predischarge_simulator import PreDischargeSimulator, simulate_predischarge
from app.reports.ombudsman_form_generator import OmbudsmanFormGenerator, map_pincode_to_ombudsman, OMBUDSMAN_CENTERS
from app.reports.generator import ReportGenerator
from app.rules.engine import RuleEngine


# ==============================================================================
# Helper Factories
# ==============================================================================

def make_prov(val):
    return Provenance(value=val)


def make_line_item(desc, cat, qty, rate, amt, is_room_linked=False):
    return BillLineItem(
        description=make_prov(desc),
        category=make_prov(cat),
        quantity=make_prov(float(qty)),
        unit_rate=make_prov(float(rate)),
        amount=make_prov(float(amt)),
        is_room_linked=is_room_linked
    )


# ==============================================================================
# 1. Appeal Evaluator: Eradication of Section 45 & Citation of IRDAI 2024
# ==============================================================================

def test_appeal_evaluator_no_section_45_reference():
    """Asserts string 'Section 45' does not exist anywhere in generated evaluation findings."""
    evaluator = AppealEvaluator()
    inception = date(2018, 1, 1)
    claim_date = date(2024, 6, 1)  # > 60 months active

    denial_reasons = [
        {"code": "PED01", "category": "PRE_EXISTING", "description": "Repudiation due to pre-existing hypertension non-disclosure"}
    ]
    claim_data = {"claim_date": claim_date.isoformat(), "total_claimed": 100000.0, "total_deducted": 100000.0}
    policy_data = {"inception_date": inception.isoformat(), "moratorium_period_months": 60}

    result = evaluator.evaluate_denial(denial_reasons, claim_data, policy_data)

    all_evaluation_text = " ".join(
        result.statutory_conflicts_detected
        + result.key_legal_precedents
        + result.recommended_appeal_grounds
        + result.suggested_action_plan
    )

    assert "Section 45" not in all_evaluation_text
    assert "Sec 45" not in all_evaluation_text
    assert "IRDAI Master Circular on Health Insurance Business, 29 May 2024 (Chapter V, Para 5.3)" in all_evaluation_text
    assert result.appeal_viability == "STRONG"


def test_appeal_evaluator_valid_deduction_no_grounds():
    """Verifies appeal viability produces NO_GROUNDS when deduction is valid."""
    evaluator = AppealEvaluator()
    result = evaluator.evaluate_denial(
        denial_reasons=[{"description": "Valid room rent excess deduction"}],
        is_valid_deduction=True,
        legal_track="TRACK_C_VALID_DEDUCTION"
    )
    assert result.appeal_viability == "NO_GROUNDS"
    assert len(result.statutory_conflicts_detected) == 0
    assert "no appeal recommended" in result.suggested_action_plan[0].lower()


# ==============================================================================
# 2. Clause Timeline: Exact Calendar Calculation Fallback (relativedelta)
# ==============================================================================

class SimplePolicyWithoutMoratoriumMethod:
    """Mock policy object without evaluate_moratorium method."""
    def __init__(self, inception_date, moratorium_months=60, portability_months=0, migration_months=0):
        self.inception_date = inception_date
        self.moratorium_period_months = moratorium_months
        self.portability_credits_months = portability_months
        self.migration_credits_months = migration_months


def test_clause_timeline_moratorium_fallback():
    """Verifies exact 60-month moratorium calculation when policy lacks evaluate_moratorium."""
    # Policy active for 65 months (Inception: 2018-01-01, Claim: 2023-06-01)
    policy = SimplePolicyWithoutMoratoriumMethod(
        inception_date="2018-01-01",
        moratorium_months=60
    )
    assert not hasattr(policy, "evaluate_moratorium")

    bill = HospitalBill(
        hospital_name=make_prov("Max Healthcare"),
        line_items=[],
        total_amount=make_prov(150000.0)
    )
    rejection = RejectionLetter(
        rejection_id=make_prov("REJ-101"),
        claim_number=make_prov("CLM-101"),
        claim_date=make_prov("2023-06-01"),
        total_claimed=make_prov(150000.0),
        rejection_reasons=[
            RejectionReason(code="PED01", description="Non-disclosure of pre-existing condition", category="PRE_EXISTING")
        ]
    )

    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert "MORATORIUM_RULE_CONFLICT" in verdict.finding
    assert "IRDAI Master Circular on Health Insurance, 29 May 2024" in verdict.regulatory_citation


def test_clause_timeline_moratorium_fallback_before_completion():
    """Verifies that claims before 60 months pass temporally when evaluate_moratorium is absent."""
    # Policy active for only 12 months (Inception: 2023-01-01, Claim: 2024-01-01)
    policy = SimplePolicyWithoutMoratoriumMethod(
        inception_date="2023-01-01",
        moratorium_months=60
    )
    bill = HospitalBill(line_items=[], total_amount=make_prov(50000.0))
    rejection = RejectionLetter(
        claim_date=make_prov("2024-01-01"),
        total_claimed=make_prov(50000.0),
        rejection_reasons=[
            RejectionReason(code="PED01", description="Pre-existing disease", category="PRE_EXISTING")
        ]
    )

    verdict = check_clause_timeline(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert "is before moratorium completion" in verdict.finding


# ==============================================================================
# 3. Proportionate Deduction: Dual-Track (Track A, B, C) Evaluation
# ==============================================================================

def test_proportionate_deduction_track_c_valid():
    """
    Verifies that when an insurer correctly deducts only room-linked charges,
    the engine outputs status="PASS" and flags TRACK_C_VALID_DEDUCTION without
    manufacturing an appeal.
    """
    # 4 days stay: Room actual ₹8,000/day vs limit ₹4,000/day
    # Room excess = (8000 - 4000) * 4 = ₹16,000
    # Room-linked: Room (32,000) + Nursing (8,000) = 40,000
    # Deduction % = 1 - 4000/8000 = 50%
    # Proportionate reduction = 40,000 * 0.50 = ₹20,000
    # Expected total legitimate deduction = 16,000 + 20,000 = ₹36,000
    items = [
        make_line_item("Deluxe Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("Nursing Care", "NURSING", 4, 2000, 8000, is_room_linked=True),
        make_line_item("OT Charges", "OT", 1, 40000, 40000, is_room_linked=False)
    ]
    bill = HospitalBill(
        admission_date=make_prov("2025-01-01"),
        discharge_date=make_prov("2025-01-05"),
        line_items=items,
        total_amount=make_prov(80000.0),
        subtotal=make_prov(80000.0)
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(4000.0))
    rejection = RejectionLetter(
        total_claimed=make_prov(80000.0),
        total_approved=make_prov(44000.0),
        total_deducted=make_prov(36000.0)  # Exactly ₹36,000 legitimate deduction
    )

    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.legal_track == "TRACK_C_VALID_DEDUCTION"
    assert verdict.appeal_recommendation is None
    assert verdict.monetary_impact == 0.0
    assert "Insurer calculation is contractually and regulatorily valid. No underpayment." in verdict.finding


def test_proportionate_deduction_track_a_arithmetic_breach():
    """Verifies that over-deductions touching protected items are classified as Track A."""
    items = [
        make_line_item("Deluxe Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("Nursing Care", "NURSING", 4, 2000, 8000, is_room_linked=True),
        make_line_item("OT Charges", "OT", 1, 40000, 40000, is_room_linked=False)
    ]
    bill = HospitalBill(
        admission_date=make_prov("2025-01-01"),
        discharge_date=make_prov("2025-01-05"),
        line_items=items,
        total_amount=make_prov(80000.0),
        subtotal=make_prov(80000.0)
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(4000.0))
    # Insurer deducts ₹65,000 (expected is ₹36,000; overdeduction of ₹29,000)
    rejection = RejectionLetter(
        total_claimed=make_prov(80000.0),
        total_approved=make_prov(15000.0),
        total_deducted=make_prov(65000.0)
    )

    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_A_ARITHMETIC_BREACH"
    assert "TRACK A: ARITHMETIC BREACH" in verdict.finding
    assert verdict.monetary_impact == 29000.0


def test_proportionate_deduction_track_b_ultra_vires_clause():
    """Verifies that an illegal policy clause overriding IRDAI protected heads triggers Track B."""
    items = [
        make_line_item("Deluxe Room", "ROOM", 4, 8000, 32000, is_room_linked=True),
        make_line_item("OT Charges", "OT", 1, 40000, 40000, is_room_linked=False)
    ]
    bill = HospitalBill(
        admission_date=make_prov("2025-01-01"),
        discharge_date=make_prov("2025-01-05"),
        line_items=items,
        total_amount=make_prov(72000.0),
        subtotal=make_prov(72000.0)
    )
    # Policy clause attempts to apply proportionate deduction to all charges including OT & pharmacy
    ultra_vires_rule = ProportionateDeductionRuleConfig(
        threshold_value=make_prov(1.0),
        threshold_operator=make_prov(">"),
        threshold_source_type=make_prov("POLICY_SCHEDULE"),
        policy_clause=make_prov("Proportionate deduction applies across all charges including OT, ICU, medicines, and entire bill without exception")
    )
    policy = InsurancePolicy(
        room_rent_limit_per_day=make_prov(4000.0),
        proportionate_deduction_rule=ultra_vires_rule
    )
    rejection = RejectionLetter(
        total_claimed=make_prov(72000.0),
        total_approved=make_prov(20000.0),
        total_deducted=make_prov(52000.0)
    )

    verdict = check_proportionate_deduction(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.legal_track == "TRACK_B_ULTRA_VIRES_CLAUSE"
    assert "TRACK B: ULTRA VIRES CLAUSE" in verdict.finding
    assert "ultra vires" in verdict.appeal_recommendation.lower()


# ==============================================================================
# 4. Non-Payable Items Rule: IRDAI Standardization Guidelines (Annexure A)
# ==============================================================================

def test_non_payable_items_surgical_protection():
    """Verifies that List III surgical consumables wrongfully deducted by TPA are caught and quantified."""
    items = [
        make_line_item("General Surgery Laparoscopy", "OT", 1, 50000, 50000),
        make_line_item("Surgical Blades and OT Gowns", "CONSUMABLES", 1, 4500, 4500),
        make_line_item("Sterile Gloves and Drape Sheet", "CONSUMABLES", 1, 3500, 3500),
        make_line_item("Cardiac Monitor Electrodes", "CONSUMABLES", 1, 2000, 2000),
        make_line_item("Room Linen", "ROOM", 1, 1000, 1000)
    ]
    bill = HospitalBill(
        diagnosis=make_prov("Acute appendicitis undergoing laparoscopy appendectomy"),
        line_items=items,
        total_amount=make_prov(61000.0),
        subtotal=make_prov(61000.0)
    )
    policy = InsurancePolicy()
    # TPA deducted all consumables (4500 + 3500 + 2000 = 10,000) citing non-payable schedule
    rejection = RejectionLetter(
        total_claimed=make_prov(61000.0),
        total_approved=make_prov(51000.0),
        total_deducted=make_prov(10000.0),
        rejection_reasons=[
            RejectionReason(code="NP01", description="Non-payable items deducted per schedule / consumables disallowed", category="OTHER")
        ]
    )

    verdict = check_non_payable_items(bill, policy, rejection)
    assert verdict.status == "FAIL"
    assert verdict.monetary_impact == 10000.0
    assert "List III" in verdict.finding
    assert "IRDAI Guidelines on Standardization in Health Insurance" in verdict.regulatory_citation


def test_non_payable_items_list_i_legitimate_deduction():
    """Verifies that purely List I items (toiletries/baby food) pass as legitimate deductions."""
    items = [
        make_line_item("Baby Food and Diapers", "MISCELLANEOUS", 1, 1500, 1500),
        make_line_item("Toothbrush and Slippers", "MISCELLANEOUS", 1, 500, 500)
    ]
    bill = HospitalBill(
        diagnosis=make_prov("Gastroenteritis"),
        line_items=items,
        total_amount=make_prov(2000.0),
        subtotal=make_prov(2000.0)
    )
    policy = InsurancePolicy()
    rejection = RejectionLetter(
        total_claimed=make_prov(2000.0),
        total_approved=make_prov(0.0),
        total_deducted=make_prov(2000.0),
        rejection_reasons=[
            RejectionReason(code="NP01", description="Non-medical items excluded", category="OTHER")
        ]
    )

    verdict = check_non_payable_items(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.monetary_impact == 0.0
    assert "List I non-medical items" in verdict.finding


# ==============================================================================
# 5. Pre-Discharge Simulator: Interim Bill Scrubbing & Room Multiplier Alert
# ==============================================================================

def test_predischarge_room_multiplier_simulation():
    """Verifies the cascading calculation of room rent upgrade warnings on interim bills."""
    # Scenario: Room chosen ₹8,000 vs policy cap ₹5,000 for 3 days
    # Surgeon Fee: ₹45,000, OT: ₹30,000
    # Ratio = 1 - 5000/8000 = 37.5%
    # Projected cut on surgical/OT (45,000 + 30,000 = 75,000) = 37.5% * 75,000 = ₹28,125
    items = [
        make_line_item("Super Deluxe Room", "ROOM", 3, 8000, 24000, is_room_linked=True),
        make_line_item("Senior Surgeon Fee", "CONSULTATION", 1, 45000, 45000, is_room_linked=True),
        make_line_item("Operation Theatre Charges", "OT", 1, 30000, 30000, is_room_linked=True),
        make_line_item("Slippers and Toiletries", "MISCELLANEOUS", 1, 1200, 1200)
    ]
    bill = HospitalBill(
        admission_date=make_prov("2026-03-01"),
        estimated_discharge_date=make_prov("2026-03-04"),
        is_interim_bill=True,
        line_items=items,
        total_amount=make_prov(100200.0),
        subtotal=make_prov(100200.0)
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(5000.0))

    sim = PreDischargeSimulator()
    result = sim.simulate(bill, policy)

    assert result.has_room_rent_excess is True
    assert result.actual_room_rate == 8000.0
    assert result.eligible_room_rate == 5000.0
    assert result.excess_per_day == 3000.0
    assert result.length_of_stay == 3
    assert result.projected_room_excess == 9000.0
    assert abs(result.projected_proportionate_deduction - 28125.0) < 1.0
    assert abs(result.projected_total_out_of_pocket - 37125.0) < 1.0
    assert "₹8,000" in result.warning_message or "8,000" in result.warning_message
    assert "28,125" in result.warning_message
    assert len(result.scrubbed_non_payable_items) == 1
    assert result.scrubbed_non_payable_items[0]["classification"] == "LIST_I_NON_PAYABLE"


# ==============================================================================
# 6. Ombudsman Form VI-A Generator & 17 Territorial Jurisdictions
# ==============================================================================

def test_ombudsman_form_via_jurisdiction_mapping():
    """Verifies pin code mapping across Ombudsman centers and Form VI-A completeness."""
    # Test key regional hubs
    assert map_pincode_to_ombudsman("400001")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("560001")["center"] == "Bengaluru"
    assert map_pincode_to_ombudsman("110001")["center"] == "Delhi"
    assert map_pincode_to_ombudsman("600001")["center"] == "Chennai"
    assert map_pincode_to_ombudsman("700001")["center"] == "Kolkata"
    assert map_pincode_to_ombudsman("500001")["center"] == "Hyderabad"
    assert map_pincode_to_ombudsman("380001")["center"] == "Ahmedabad"
    assert map_pincode_to_ombudsman("302001")["center"] == "Jaipur"
    assert map_pincode_to_ombudsman("682001")["center"] == "Ernakulam"
    assert map_pincode_to_ombudsman("201301")["center"] == "Noida"
    assert map_pincode_to_ombudsman("226001")["center"] == "Lucknow"
    assert map_pincode_to_ombudsman("800001")["center"] == "Patna"
    assert map_pincode_to_ombudsman("411001")["center"] == "Pune"
    assert map_pincode_to_ombudsman("462001")["center"] == "Bhopal"
    assert map_pincode_to_ombudsman("751001")["center"] == "Bhubaneswar"
    assert map_pincode_to_ombudsman("160017")["center"] == "Chandigarh"
    assert map_pincode_to_ombudsman("781001")["center"] == "Guwahati"

    # Test Form VI-A text generation
    generator = OmbudsmanFormGenerator()
    complaint_data = {
        "complainant_name": "Ramesh Kumar Sharma",
        "complainant_address": "Flat 402, Sea Green Apts, Worli, Mumbai",
        "pincode": "400018",
        "phone": "9820123456",
        "email": "ramesh.sharma@example.com",
        "insurer_name": "Star Health and Allied Insurance",
        "insurer_branch": "Mumbai Regional Office",
        "policy_number": "P/101/2024",
        "claim_number": "CIR/2024/0091",
        "repudiation_date": "2024-05-10",
        "gro_representation_date": "2024-05-15",
        "disputed_amount": 28125.0,
        "grounds_summary": "Unlawful proportionate deduction on OT and medicines contrary to IRDAI Master Circular 2024."
    }

    form_text = generator.generate_form_via_text(complaint_data)
    assert "FORM VI-A" in form_text
    assert "RULE 14(3)" in form_text
    assert "Ramesh Kumar Sharma" in form_text
    assert "Mumbai" in form_text
    assert "Rs. 28,125.00" in form_text
    assert "Penal interest @" in form_text
    assert "SOLEMN DECLARATION & VERIFICATION" in form_text


def test_ombudsman_form_pdf_and_report_generator_integration():
    """Verifies ReportGenerator integration with Form VI-A and Pre-Discharge alert."""
    report_gen = ReportGenerator()

    # Test Form VI-A integration
    complaint_data = {
        "complainant_name": "Anita Verma",
        "pincode": "560001",
        "disputed_amount": 45000.0,
        "policy_number": "POL-BLR-01",
        "claim_number": "CLM-BLR-01"
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = os.path.join(tmp_dir, "form_via.pdf")
        res = report_gen.generate_ombudsman_form_via(complaint_data, output_pdf_path=pdf_path)
        assert res["jurisdiction"]["center"] == "Bengaluru"
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

    # Test Pre-Discharge alert integration
    sim_data = {
        "is_interim": True,
        "has_room_rent_excess": True,
        "actual_room_rate": 8000.0,
        "eligible_room_rate": 5000.0,
        "projected_room_excess": 9000.0,
        "projected_proportionate_deduction": 28125.0,
        "projected_total_out_of_pocket": 37125.0,
        "warning_message": "Exceeds cap.",
        "recommended_action": "Request downgrade."
    }
    alert = report_gen.generate_predischarge_alert(sim_data)
    assert alert["has_room_rent_excess"] is True
    assert alert["projected_proportionate_deduction"] == 28125.0


# ==============================================================================
# 7. Edge Cases: Boundary Values, Empty Inputs & Resiliency
# ==============================================================================

def test_predischarge_simulator_boundary_zero_excess():
    """When actual room rate exactly equals or is below policy cap, no excess is flagged."""
    bill = HospitalBill(
        line_items=[make_line_item("Standard Room", "ROOM", 2, 5000, 10000, is_room_linked=True)],
        total_amount=make_prov(10000.0)
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(5000.0))
    res = simulate_predischarge(bill, policy)
    assert res.has_room_rent_excess is False
    assert res.excess_per_day == 0.0
    assert res.projected_proportionate_deduction == 0.0
    assert "within eligible policy limits" in res.warning_message


def test_predischarge_simulator_empty_bill_resilience():
    """Empty bill does not crash simulator."""
    bill = HospitalBill(line_items=[])
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(5000.0))
    res = simulate_predischarge(bill, policy)
    assert res.has_room_rent_excess is False
    assert res.projected_total_out_of_pocket == 0.0


def test_interim_bill_estimated_discharge_date_stay():
    """Interim bill calculates length of stay from admission to estimated_discharge_date."""
    bill = HospitalBill(
        admission_date=make_prov("2026-05-01"),
        estimated_discharge_date=make_prov("2026-05-06"),
        is_interim_bill=True
    )
    assert bill.length_of_stay == 5


def test_ombudsman_pincode_mapper_invalid_fallbacks():
    """Malformed or invalid PIN codes fall back gracefully to default Ombudsman center."""
    assert map_pincode_to_ombudsman("000000")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("ABC123")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("12345")["center"] == "Mumbai"


def test_non_payable_items_empty_line_items_skipped():
    """Empty line items returns SKIPPED status."""
    bill = HospitalBill(line_items=[])
    policy = InsurancePolicy()
    rejection = RejectionLetter(total_deducted=make_prov(5000.0))
    verdict = check_non_payable_items(bill, policy, rejection)
    assert verdict.status == "SKIPPED"


def test_hospital_bill_room_charges_per_day_none_safety():
    """Asserts that HospitalBill with unclassified or unit_rate-less line items does not raise AttributeError."""
    item_none_cat = BillLineItem(description=make_prov("Mystery charge"), amount=make_prov(1000.0))
    item_room_no_rate = BillLineItem(category=make_prov("ROOM"), amount=make_prov(12000.0), quantity=make_prov(2.0))
    bill = HospitalBill(line_items=[item_none_cat, item_room_no_rate])
    
    # Must compute rate safely without raising AttributeError
    assert bill.room_charges_per_day == 6000.0


def test_non_payable_items_no_false_positive_on_room_rent_deduction():
    """Asserts that when insurer solely deducted room rent excess, List III surgical items are NOT flagged as violation."""
    items = [
        make_line_item("Appendectomy Surgery", "OT", 1, 50000, 50000),
        make_line_item("Surgical Blades and OT Gowns", "CONSUMABLES", 1, 5000, 5000),
        make_line_item("Deluxe Room", "ROOM", 3, 8000, 24000, is_room_linked=True)
    ]
    bill = HospitalBill(
        diagnosis=make_prov("Acute appendicitis"),
        line_items=items,
        total_amount=make_prov(79000.0)
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(4000.0))
    # Insurer deducted ₹12,000 solely for room rent limit
    rejection = RejectionLetter(
        total_claimed=make_prov(79000.0),
        total_approved=make_prov(67000.0),
        total_deducted=make_prov(12000.0),
        rejection_reasons=[
            RejectionReason(code="RR01", description="Room rent limit exceeded", category="PROPORTIONATE_DEDUCTION")
        ]
    )

    verdict = check_non_payable_items(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.legal_track == "TRACK_C_VALID_DEDUCTION"
    assert "comply with IRDAI Standardization Guidelines" in verdict.finding


def test_non_payable_items_plural_and_reversed_surgical_disposables():
    """Asserts that plural 'SURGICAL DISPOSABLES' is correctly classified as LIST_III."""
    assert classify_line_item("SURGICAL DISPOSABLES") == "LIST_III"
    assert classify_line_item("Surgical Disposable") == "LIST_III"
    assert classify_line_item("Disposable surgical items") == "LIST_III"
    assert classify_line_item("Disposables") == "LIST_I"


def test_clause_timeline_fallback_exact_boundary_consistency():
    """
    Asserts that both a policy with evaluate_moratorium and a policy without evaluate_moratorium
    produce identical verdicts on the exact 60-month completion day (PASS) and 1 day after (FAIL).
    """
    # Exact 60-month completion date (Inception: 2019-01-01, Completion: 2024-01-01)
    bill = HospitalBill(line_items=[])
    rej_exact = RejectionLetter(
        claim_date=make_prov("2024-01-01"),
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing hypertension", category="PRE_EXISTING")]
    )
    rej_plus_one = RejectionLetter(
        claim_date=make_prov("2024-01-02"),
        rejection_reasons=[RejectionReason(code="PED01", description="Pre-existing hypertension", category="PRE_EXISTING")]
    )

    # Standard policy with evaluate_moratorium
    pol_with_method = InsurancePolicy(inception_date=make_prov("2019-01-01"), moratorium_period_months=make_prov(60))
    # Mock policy without evaluate_moratorium
    pol_without_method = SimplePolicyWithoutMoratoriumMethod(inception_date="2019-01-01", moratorium_months=60)

    # On exact completion day: both PASS
    assert check_clause_timeline(bill, pol_with_method, rej_exact).status == "PASS"
    assert check_clause_timeline(bill, pol_without_method, rej_exact).status == "PASS"

    # One day after: both FAIL (statutory conflict)
    assert check_clause_timeline(bill, pol_with_method, rej_plus_one).status == "FAIL"
    assert check_clause_timeline(bill, pol_without_method, rej_plus_one).status == "FAIL"


def test_predischarge_simulator_line_item_room_rate_fallback():
    """Simulator extracts room rate from line items when room_charges_per_day property is None/0."""
    item = BillLineItem(
        description=make_prov("Deluxe Room"),
        category=make_prov("ROOM"),
        quantity=make_prov(3.0),
        unit_rate=make_prov(7500.0),
        amount=make_prov(22500.0),
        is_room_linked=True
    )
    bill = HospitalBill(
        admission_date=make_prov("2026-04-01"),
        estimated_discharge_date=make_prov("2026-04-04"),
        line_items=[item]
    )
    policy = InsurancePolicy(room_rent_limit_per_day=make_prov(5000.0))

    sim = PreDischargeSimulator()
    res = sim.simulate(bill, policy)
    assert res.has_room_rent_excess is True
    assert res.actual_room_rate == 7500.0
    assert res.excess_per_day == 2500.0
    assert res.projected_room_excess == 7500.0


def test_ombudsman_pincode_mapper_mumbai_goa_coverage():
    """Asserts that all 40xxxx PIN codes (e.g. 403xxx Goa, 404xxx Konkan) map to Mumbai center."""
    assert map_pincode_to_ombudsman("403001")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("404001")["center"] == "Mumbai"
    assert map_pincode_to_ombudsman("400 054")["center"] == "Mumbai"

def test_api_simulate_predischarge_endpoint():
    from app.api.reports import simulate_predischarge
    import asyncio
    payload = {
        "bill": {
            "total_amount": {"value": 150000.0},
            "admission_date": {"value": "2026-05-01"},
            "discharge_date": {"value": "2026-05-04"},
            "line_items": [
                {"category": {"value": "ROOM"}, "unit_rate": {"value": 8000.0}, "quantity": {"value": 3.0}, "amount": {"value": 24000.0}, "is_room_linked": True}
            ]
        },
        "policy": {
            "room_rent_limit_per_day": {"value": 5000.0}
        }
    }
    result = asyncio.run(simulate_predischarge(payload))
    assert result["has_room_rent_excess"] is True
    assert result["actual_room_rate"] == 8000.0
    assert result["eligible_room_rate"] == 5000.0
    assert result["excess_per_day"] == 3000.0
    assert result["projected_room_excess"] == 9000.0
