from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Union
from decimal import Decimal
from ..schemas.provenance import Provenance
from .calculator import FinancialMath, SafeDecimal
import uuid
from enum import Enum

class CalculationBase(str, Enum):
    ORIGINAL_AMOUNT = "ORIGINAL_AMOUNT"
    REMAINING_BALANCE = "REMAINING_BALANCE"
    SPECIFIC_SUBTOTAL = "SPECIFIC_SUBTOTAL"
    SPECIFIC_LINE_ITEMS = "SPECIFIC_LINE_ITEMS"

class FinancialAdjustment(BaseModel):
    model_config = ConfigDict(extra='ignore')
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    policy_clause: Optional[str] = None
    affected_line_items: List[str]
    original_amount: Union[SafeDecimal, Decimal, float]
    adjustment_amount: Union[SafeDecimal, Decimal, float]
    remaining_amount: Union[SafeDecimal, Decimal, float]
    calculation_formula: str
    calculation_base: Optional[CalculationBase] = None
    provenance: List[Provenance] = []
    dependency_rules: List[str] = []
    execution_order: int

class LineItemState(BaseModel):
    model_config = ConfigDict(extra='ignore')
    item_code: str
    category: str
    original_amount: Any
    remaining_balance: Any
    applied_adjustments: List[str] = []
    applied_rules: List[str] = []

class AdjudicationState(BaseModel):
    model_config = ConfigDict(extra='ignore')
    claim_id: str
    line_items: Dict[str, LineItemState] = {}
    adjustments: List[FinancialAdjustment] = []
    ledger: Optional[Any] = None  # Optional EvidenceLedger instance
    
    def get_balance(self, item_code: str) -> SafeDecimal:
        if item_code in self.line_items:
            return FinancialMath.to_decimal(self.line_items[item_code].remaining_balance)
        return SafeDecimal('0.00')

    def apply_deduction(
        self, 
        rule_id: str, 
        target_item_codes: List[str], 
        deduction_amount: Union[SafeDecimal, Decimal, float, Provenance], 
        formula: str,
        policy_clause: Optional[str] = None,
        prov: Optional[List[Provenance]] = None,
        dependencies: Optional[List[str]] = None,
        calculation_base: CalculationBase = CalculationBase.REMAINING_BALANCE,
        base_item_codes: Optional[List[str]] = None,
        explicit_base_amount: Optional[Union[SafeDecimal, Decimal, float]] = None
    ) -> Optional[FinancialAdjustment]:
        # Extract SafeDecimal deduction amount
        dec_deduction = FinancialMath.to_decimal(deduction_amount)
        
        # Automatically wrap provenance if deduction_amount was a Provenance instance
        if isinstance(deduction_amount, Provenance) and not prov:
            prov = [deduction_amount]

        # Double-deduction prevention via lineage tracking
        valid_targets = []
        for code in target_item_codes:
            if code in self.line_items:
                if rule_id not in self.line_items[code].applied_rules:
                    valid_targets.append(code)
        
        if not valid_targets:
            return None
            
        target_item_codes = valid_targets

        # Compute calculation base amount for the record
        if calculation_base == CalculationBase.ORIGINAL_AMOUNT:
            total_base_amount = sum(FinancialMath.to_decimal(self.line_items[code].original_amount) for code in target_item_codes)
        elif calculation_base == CalculationBase.SPECIFIC_LINE_ITEMS and base_item_codes:
            total_base_amount = sum(self.get_balance(code) for code in base_item_codes)
        elif calculation_base == CalculationBase.SPECIFIC_SUBTOTAL and explicit_base_amount is not None:
            total_base_amount = FinancialMath.to_decimal(explicit_base_amount)
        else:
            total_base_amount = sum(self.get_balance(code) for code in target_item_codes)
            
        # We can only deduct what is actually remaining, regardless of the calculation base
        total_remaining = sum(self.get_balance(code) for code in target_item_codes)
        actual_deduction = min(dec_deduction, total_remaining)
        
        if actual_deduction <= SafeDecimal('0.00'):
            return None

        adj = FinancialAdjustment(
            rule_id=rule_id,
            policy_clause=policy_clause,
            affected_line_items=target_item_codes,
            original_amount=total_base_amount,  # Recording the base amount used
            adjustment_amount=actual_deduction,
            remaining_amount=total_remaining - actual_deduction,
            calculation_formula=formula,
            calculation_base=calculation_base,
            provenance=prov or [],
            dependency_rules=dependencies or [],
            execution_order=len(self.adjustments) + 1
        )
        self.adjustments.append(adj)
        
        # Deduct from balances in exact paise
        remaining_to_deduct = actual_deduction
        for code in target_item_codes:
            if rule_id not in self.line_items[code].applied_rules:
                self.line_items[code].applied_rules.append(rule_id)
            if adj.adjustment_id not in self.line_items[code].applied_adjustments:
                self.line_items[code].applied_adjustments.append(adj.adjustment_id)
                
            if remaining_to_deduct <= SafeDecimal('0.00'):
                continue
                
            bal = self.get_balance(code)
            if bal > SafeDecimal('0.00'):
                take = min(bal, remaining_to_deduct)
                
                # Point 13: Preserve provenance ledger for the new balance
                self.line_items[code].remaining_balance = FinancialMath.sub(
                    self.line_items[code].remaining_balance, 
                    take,
                    formula=f"balance - deduction",
                    rule_id=rule_id
                )
                remaining_to_deduct = remaining_to_deduct - take
        # If an EvidenceLedger is attached, record adjustment directly
        if self.ledger and hasattr(self.ledger, 'record_calculation'):
            self.ledger.record_calculation(
                rule_id=rule_id,
                formula=formula,
                calculation_inputs={
                    "target_items": target_item_codes,
                    "requested_deduction": str(dec_deduction),
                    "total_available": str(total_remaining),
                    "actual_deduction": str(actual_deduction)
                },
                final_output=str(actual_deduction)
            )

        return adj

    def verify_reconciliation(self) -> bool:
        original_total = sum(FinancialMath.to_decimal(item.original_amount) for item in self.line_items.values())
        final_total = sum(FinancialMath.to_decimal(item.remaining_balance) for item in self.line_items.values())
        total_deducted = sum(FinancialMath.to_decimal(adj.adjustment_amount) for adj in self.adjustments)
        
        return abs(original_total - (final_total + total_deducted)) < SafeDecimal('0.01')
