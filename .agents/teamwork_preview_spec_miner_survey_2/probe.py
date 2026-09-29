import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend")

from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.clause_timeline import check_clause_timeline
from app.rules.waiting_period import check_waiting_period
from app.rules.identity_gate import check_identity_gate
from app.rules.clinical_firewall import check_clinical_firewall
from app.rules.document_integrity import check_document_integrity
from app.rules.authenticity_check import check_authenticity
from app.rules.mental_health_parity import check_mental_health_parity
from app.rules.engine import RuleEngine

print("=== PROBE 1: Proportionate Deduction with Room Item in Room-Linked ===")
bill = HospitalBill(
    hospital_name="Test Hospital",
    patient_name="John Doe",
    line_items=[
        BillLineItem(description="Room Charges", category="ROOM", quantity=2, unit_rate=6000.0, amount=12000.0, is_room_linked=True),
        BillLineItem(description="Nursing Charges", category="NURSING", quantity=2, unit_rate=1000.0, amount=2000.0, is_room_linked=True),
        BillLineItem(description="Doctor Fees", category="CONSULTATION", quantity=2, unit_rate=1500.0, amount=3000.0, is_room_linked=False),
    ],
    subtotal=17000.0,
    net_payable=17000.0,
    admission_date="2025-01-01",
    discharge_date="2025-01-03"
)
policy = InsurancePolicy(
    policy_number="POL-123",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_start_date="2024-01-01",
    policy_end_date="2025-01-01",
    sum_insured=500000.0,
    room_rent_limit_per_day=5000.0
)
rejection = RejectionLetter(
    reference_number="REF-1",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-1",
    claim_date="2025-01-02",
    total_claimed=17000.0,
    total_approved=14666.67,
    total_deducted=2333.33,
    rejection_reasons=[RejectionReason(code="PROP01", description="Proportionate deduction applied", category="PROPORTIONATE_DEDUCTION")],
    settlement_type="PARTIAL_SETTLEMENT"
)

# 1. Trigger threshold check: 5000 * 1.15 = 5750. Actual = 6000 > 5750 -> triggered!
v1 = check_proportionate_deduction(bill, policy, rejection)
print(f"Triggered: status={v1.status}")
print(f"Finding: {v1.finding}")
print(f"Expected Legitimate Deduction: {v1.correct_calculation}")
print(f"Insurer Deducted: {v1.insurer_calculation}")
print(f"Monetary impact: {v1.monetary_impact}")

print("\n=== PROBE 2: Proportionate Deduction when Actual Rate is 1.10x (below 1.15x) ===")
# If actual room rate is 5500 (10% over 5000 limit, but <= 1.15 limit 5750)
bill2 = HospitalBill(
    hospital_name="Test Hospital",
    patient_name="John Doe",
    line_items=[
        BillLineItem(description="Room Charges", category="ROOM", quantity=2, unit_rate=5500.0, amount=11000.0, is_room_linked=True)
    ],
    subtotal=11000.0,
    net_payable=11000.0,
    admission_date="2025-01-01",
    discharge_date="2025-01-03"
)
rejection2 = RejectionLetter(
    reference_number="REF-2",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-2",
    claim_date="2025-01-02",
    total_claimed=11000.0,
    total_approved=10000.0,
    total_deducted=1000.0, # Insurer deducted the room excess (500*2 = 1000)
    rejection_reasons=[RejectionReason(code="ROOM01", description="Room rent excess deducted", category="PROPORTIONATE_DEDUCTION")],
    settlement_type="PARTIAL_SETTLEMENT"
)
v2 = check_proportionate_deduction(bill2, policy, rejection2)
print(f"Below 1.15: status={v2.status}")
print(f"Finding: {v2.finding}")
print(f"Expected Legitimate Deduction: {v2.correct_calculation}")

print("\n=== PROBE 3: Clause Timeline Moratorium Boundary (Exact 60 Months) ===")
policy3 = InsurancePolicy(
    policy_number="POL-123",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_start_date="2020-01-01",
    inception_date="2020-01-01",
    policy_end_date="2025-01-01",
    sum_insured=500000.0,
    moratorium_period_months=60
)
# Claim exactly at 60 months: 2025-01-01
rejection3 = RejectionLetter(
    reference_number="REF-3",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-3",
    claim_date="2025-01-01",
    total_claimed=50000.0,
    total_approved=0.0,
    total_deducted=50000.0,
    rejection_reasons=[RejectionReason(code="PED01", description="Claim rejected for pre-existing non-disclosure", category="PRE_EXISTING")],
    settlement_type="FULL_REJECTION"
)
v3 = check_clause_timeline(bill, policy3, rejection3)
print(f"Exact 60 months date: status={v3.status}")
print(f"Finding: {v3.finding}")

# Claim at 60 months + 1 day: 2025-01-02
rejection3_plus1 = RejectionLetter(
    reference_number="REF-3B",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-3B",
    claim_date="2025-01-02",
    total_claimed=50000.0,
    total_approved=0.0,
    total_deducted=50000.0,
    rejection_reasons=[RejectionReason(code="PED01", description="Claim rejected for pre-existing non-disclosure", category="PRE_EXISTING")],
    settlement_type="FULL_REJECTION"
)
v3_plus1 = check_clause_timeline(bill, policy3, rejection3_plus1)
print(f"60 months + 1 day: status={v3_plus1.status}")

# Disguised wording: "Suppression of material medical facts"
rejection3_disguised = RejectionLetter(
    reference_number="REF-3C",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-3C",
    claim_date="2025-06-01",
    total_claimed=50000.0,
    total_approved=0.0,
    total_deducted=50000.0,
    rejection_reasons=[RejectionReason(code="MISREP01", description="Suppression of material medical facts regarding hypertension", category="EXCLUSION")],
    settlement_type="FULL_REJECTION"
)
v3_disguised = check_clause_timeline(bill, policy3, rejection3_disguised)
print(f"Disguised suppression wording: status={v3_disguised.status}, finding={v3_disguised.finding}")

print("\n=== PROBE 4: Waiting Period with 30.44 days vs calendar calculation ===")
# Policy start 2024-01-01, claim on 2024-01-31 (day 30)
rejection4 = RejectionLetter(
    reference_number="REF-4",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_number="POL-123",
    claim_number="CLM-4",
    claim_date="2024-01-31",
    total_claimed=30000.0,
    total_approved=0.0,
    total_deducted=30000.0,
    rejection_reasons=[RejectionReason(code="WP01", description="Initial 30 day waiting period applies", category="WAITING_PERIOD")],
    settlement_type="FULL_REJECTION"
)
policy4 = InsurancePolicy(
    policy_number="POL-123",
    insurer_name="Test Insurer",
    policyholder_name="John Doe",
    policy_start_date="2024-01-01",
    policy_end_date="2025-01-01",
    sum_insured=500000.0,
    initial_waiting_period_days=30
)
v4 = check_waiting_period(bill, policy4, rejection4)
print(f"Day 30 initial WP: status={v4.status}, finding={v4.finding}")

print("\n=== PROBE 5: Tier 0 Identity Gate BLOCKED execution in RuleEngine ===")
policy_mismatch = InsurancePolicy(
    policy_number="POL-999-WRONG",
    insurer_name="Test Insurer",
    policyholder_name="Jane Doe",
    policy_start_date="2024-01-01",
    policy_end_date="2025-01-01",
    sum_insured=500000.0
)
engine = RuleEngine()
analysis_res = engine.run_all_rules(bill, policy_mismatch, rejection)
print(f"Overall status: {analysis_res.overall_status}")
print(f"Summary: {analysis_res.summary}")
print("Verdicts generated:")
for v in analysis_res.rule_verdicts:
    print(f"  - {v.rule_name} (tier ?): status={v.status}, finding={v.finding[:60]}...")
