import pytest
from app.rules.engine import RuleEngine
from app.schemas.hospital_bill import HospitalBill
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
import app.rules.engine as engine_mod

def test_engine_aborts_on_dependency_cycle(monkeypatch):
    engine = RuleEngine()
    
    # Mock get_all_rules to return a circular dependency
    def mock_get_all_rules():
        return [
            {
                "name": "Gatekeeper",
                "tier": 0,
                "function": lambda b, p, r: engine_mod.RuleVerdict(
                    status="PASS", rule_name="Gatekeeper", rule_description="", finding=""
                )
            },
            {
                "name": "RuleA",
                "tier": 1,
                "depends_on": ["RuleB"],
                "function": lambda b, p, r, state: None
            },
            {
                "name": "RuleB",
                "tier": 1,
                "depends_on": ["RuleA"],
                "function": lambda b, p, r, state: None
            }
        ]
        
    monkeypatch.setattr(engine_mod, "get_all_rules", mock_get_all_rules)
    
    from unittest.mock import MagicMock
    
    bill = MagicMock(spec=HospitalBill)
    bill.bill_id = "B1"
    bill.line_items = []
    
    policy = MagicMock(spec=InsurancePolicy)
    policy.evaluate_moratorium.return_value = {"is_protected": False}
    
    rejection = MagicMock(spec=RejectionLetter)
    rejection.total_approved = 1000.0
    rejection.claim_date = "2023-01-01"
    
    result = engine.run_all_rules(bill, policy, rejection)
    
    assert result.overall_status == "REVIEW_RECOMMENDED"
    assert "Dependency Graph Conflict: Cyclic dependency detected" in result.summary
