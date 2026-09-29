import pytest
from backend.app.engine.adjudication_state import AdjudicationState, LineItemState
from backend.app.engine.calculator import SafeDecimal

class DummyLedger:
    def record_calculation(self, **kwargs):
        print(kwargs)

def test_ledger_bug():
    state = AdjudicationState(
        claim_id="TEST_BUG",
        line_items={
            "ITEM1": LineItemState(
                item_code="ITEM1",
                category="ROOM",
                original_amount=1000.0,
                remaining_balance=1000.0
            )
        },
        ledger=DummyLedger()
    )
    state.apply_deduction(
        rule_id="RULE_BUG",
        target_item_codes=["ITEM1"],
        deduction_amount=200.0,
        formula="Rule BUG"
    )
    print("Success!")

test_ledger_bug()
