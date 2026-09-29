import pytest
from app.engine.adjudication_state import AdjudicationState, LineItemState, CalculationBase
from app.engine.calculator import SafeDecimal

def test_double_deduction_bug():
    state = AdjudicationState(
        claim_id="TEST_BUG",
        line_items={
            "ITEM1": LineItemState(
                item_code="ITEM1",
                category="ROOM",
                original_amount=100.0,
                remaining_balance=100.0
            ),
            "ITEM2": LineItemState(
                item_code="ITEM2",
                category="ROOM",
                original_amount=100.0,
                remaining_balance=100.0
            )
        }
    )
    
    # First deduction: Rule A targets both, wants to deduct 100.
    adj1 = state.apply_deduction(
        rule_id="RULE_A",
        target_item_codes=["ITEM1", "ITEM2"],
        deduction_amount=100.0,
        formula="Rule A 100",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    assert adj1 is not None
    assert state.get_balance("ITEM1") == SafeDecimal('0.00')
    assert state.get_balance("ITEM2") == SafeDecimal('100.00')
    
    # Second deduction: Same rule accidentally applied again
    adj2 = state.apply_deduction(
        rule_id="RULE_A",
        target_item_codes=["ITEM1", "ITEM2"],
        deduction_amount=100.0,
        formula="Rule A 100 Again",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    # This should be NONE (blocked) to prevent double deduction.
    # But because ITEM2 didn't get RULE_A in its applied_rules, it will process!
    assert adj2 is None, f"Double deduction occurred! ITEM2 balance is {state.get_balance('ITEM2')}"
