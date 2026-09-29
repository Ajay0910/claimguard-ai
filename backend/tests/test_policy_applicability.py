import pytest
from app.schemas.analysis_result import RuleVerdict
from app.rules.policy_applicability import check_policy_applicability

class MockItem:
    def __init__(self, category):
        self.category = category

class MockBill:
    def __init__(self, admission_date=None, discharge_date=None, bill_date=None, line_items=None):
        self.admission_date = admission_date
        self.discharge_date = discharge_date
        self.bill_date = bill_date
        self.line_items = line_items or []

class MockPolicy:
    def __init__(self, start, end, exclusions=None, policy_number=None):
        self.policy_start_date = start
        self.policy_end_date = end
        self.exclusions = exclusions or []
        self.policy_number = policy_number

class MockRejection:
    def __init__(self, claim_date, policy_number=None):
        self.claim_date = claim_date
        self.policy_number = policy_number

def test_policy_applicability_pass():
    bill = MockBill(admission_date="2025-05-10", discharge_date="2025-05-15")
    policy = MockPolicy(start="2025-01-01", end="2025-12-31", policy_number="POL123")
    rejection = MockRejection(claim_date="2025-05-15", policy_number="POL123")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"

def test_policy_applicability_date_conflict():
    bill = MockBill(admission_date="2024-05-10")
    policy = MockPolicy(start="2025-01-01", end="2025-12-31")
    rejection = MockRejection(claim_date="2024-05-15")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert verdict.finding_type == "POLICY_MISMATCH"
    assert "Coverage Date Conflict" in verdict.finding

def test_policy_applicability_identity_conflict():
    bill = MockBill(admission_date="2025-05-10")
    policy = MockPolicy(start="2025-01-01", end="2025-12-31", policy_number="POL123")
    rejection = MockRejection(claim_date="2025-05-15", policy_number="POL999")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert verdict.finding_type == "POLICY_MISMATCH"
    assert "Identity Conflict" in verdict.finding

def test_policy_applicability_exclusion_conflict():
    bill = MockBill(admission_date="2025-05-10", line_items=[MockItem(category="COSMETIC")])
    policy = MockPolicy(start="2025-01-01", end="2025-12-31", exclusions=["COSMETIC"])
    rejection = MockRejection(claim_date="2025-05-15")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "BLOCKED"
    assert verdict.finding_type == "POLICY_MISMATCH"
    assert "Exclusion Conflict" in verdict.finding

def test_policy_applicability_exclusion_no_substring_conflict():
    bill = MockBill(admission_date="2025-05-10", line_items=[MockItem(category="ROOM")])
    policy = MockPolicy(start="2025-01-01", end="2025-12-31", exclusions=["MUSHROOM"])
    rejection = MockRejection(claim_date="2025-05-15")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"

def test_policy_applicability_straddling_dates():
    # Admitted during active policy, discharged after expiry
    # Event date should be admission_date, which is within policy
    bill = MockBill(admission_date="2025-12-30", discharge_date="2026-01-05")
    policy = MockPolicy(start="2025-01-01", end="2025-12-31")
    # Claim filed way after policy ends
    rejection = MockRejection(claim_date="2026-01-10")
    
    verdict = check_policy_applicability(bill, policy, rejection)
    assert verdict.status == "PASS"
    assert verdict.finding_type == "NO_ISSUE"
