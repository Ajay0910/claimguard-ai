import pytest
from app.engine.adjudication_state import AdjudicationState, LineItemState, CalculationBase
from app.engine.calculator import SafeDecimal

def test_double_deduction_prevention():
    state = AdjudicationState(
        claim_id="TEST_01",
        line_items={
            "ITEM1": LineItemState(
                item_code="ITEM1",
                category="ROOM",
                original_amount=1000.0,
                remaining_balance=1000.0
            )
        }
    )
    
    # First deduction
    adj1 = state.apply_deduction(
        rule_id="RULE_A",
        target_item_codes=["ITEM1"],
        deduction_amount=200.0,
        formula="Rule A 200",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    assert adj1 is not None
    assert state.get_balance("ITEM1") == SafeDecimal('800.00')
    assert "RULE_A" in state.line_items["ITEM1"].applied_rules
    
    # Second deduction attempts to double-deduct using same rule
    adj2 = state.apply_deduction(
        rule_id="RULE_A",
        target_item_codes=["ITEM1"],
        deduction_amount=200.0,
        formula="Rule A 200 Again",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    # Should be blocked
    assert adj2 is None
    assert state.get_balance("ITEM1") == SafeDecimal('800.00')
    
    # Another rule can deduct
    adj3 = state.apply_deduction(
        rule_id="RULE_B",
        target_item_codes=["ITEM1"],
        deduction_amount=300.0,
        formula="Rule B 300",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    assert adj3 is not None
    assert state.get_balance("ITEM1") == SafeDecimal('500.00')
    assert "RULE_B" in state.line_items["ITEM1"].applied_rules

def test_calculation_bases():
    state = AdjudicationState(
        claim_id="TEST_02",
        line_items={
            "ITEM1": LineItemState(
                item_code="ITEM1",
                category="ROOM",
                original_amount=2000.0,
                remaining_balance=1500.0 # Already reduced somehow
            )
        }
    )
    
    # Rule C uses ORIGINAL_AMOUNT
    adj_c = state.apply_deduction(
        rule_id="RULE_C",
        target_item_codes=["ITEM1"],
        deduction_amount=100.0,
        formula="Rule C 100",
        calculation_base=CalculationBase.ORIGINAL_AMOUNT
    )
    
    assert adj_c.original_amount == SafeDecimal('2000.00') # Base was original amount
    assert adj_c.adjustment_amount == SafeDecimal('100.00')
    assert state.get_balance("ITEM1") == SafeDecimal('1400.00')

    # Rule D uses REMAINING_BALANCE
    adj_d = state.apply_deduction(
        rule_id="RULE_D",
        target_item_codes=["ITEM1"],
        deduction_amount=100.0,
        formula="Rule D 100",
        calculation_base=CalculationBase.REMAINING_BALANCE
    )
    
    assert adj_d.original_amount == SafeDecimal('1400.00') # Base was remaining balance
    assert adj_d.adjustment_amount == SafeDecimal('100.00')
    assert state.get_balance("ITEM1") == SafeDecimal('1300.00')

    # Rule E uses SPECIFIC_SUBTOTAL
    state.line_items["ITEM2"] = LineItemState(
        item_code="ITEM2",
        category="CONSULT",
        original_amount=500.0,
        remaining_balance=500.0
    )
    
    adj_e = state.apply_deduction(
        rule_id="RULE_E",
        target_item_codes=["ITEM1", "ITEM2"],
        deduction_amount=200.0,
        formula="Rule E 200",
        calculation_base=CalculationBase.SPECIFIC_SUBTOTAL,
        explicit_base_amount=3000.0
    )
    
    assert adj_e.original_amount == SafeDecimal('3000.00')
    assert adj_e.adjustment_amount == SafeDecimal('200.00')
    
    # Rule F uses SPECIFIC_LINE_ITEMS
    adj_f = state.apply_deduction(
        rule_id="RULE_F",
        target_item_codes=["ITEM1"],
        deduction_amount=50.0,
        formula="Rule F 50 based on ITEM2",
        calculation_base=CalculationBase.SPECIFIC_LINE_ITEMS,
        base_item_codes=["ITEM2"]
    )
    
    assert adj_f.original_amount == SafeDecimal('500.00') # Base was ITEM2
    assert adj_f.adjustment_amount == SafeDecimal('50.00')
    assert state.get_balance("ITEM1") == SafeDecimal('1050.00')
