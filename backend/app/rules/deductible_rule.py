from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Deductible Rule",
    description="Applies the fixed policy deductible against the total eligible bill.",
    tier=1,
    regulatory_citation="Policy Schedule - Deductible Clause"
)
def check_deductible(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    try:
        from ..engine.calculator import FinancialMath as fmath
        
        deductible = fmath.extract(get_val(policy, 'deductible', 0.0))
        if deductible <= 0:
            return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="NOT_APPLICABLE",
                rule_name="Deductible Rule",
                finding="No deductible applies to this policy."
            )
            
        if state:
            # We apply deductible across all remaining balances, typically distributed proportionally,
            # but for simplicity, we just deduct from the total available balance across all items.
            all_codes = [code for code in state.line_items.keys()]
            adj = state.apply_deduction(
                rule_id="Deductible Rule",
                target_item_codes=all_codes,
                deduction_amount=deductible,
                formula=f"Fixed Deductible ({deductible})",
                policy_clause="Deductible Clause"
            )
            
            if adj:
                return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                    status="PASS",
                    rule_name="Deductible Rule",
                    finding=f"Applied deductible of Rs. {adj.adjustment_amount} against remaining eligible amount of Rs. {adj.original_amount}."
                )
            else:
                return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                    status="NOT_APPLICABLE",
                    rule_name="Deductible Rule",
                    finding="No remaining balance to apply deductible."
                )
                
        return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
            status="SKIPPED",
            rule_name="Deductible Rule",
            finding="No AdjudicationState provided to apply deductible."
        )

    except Exception as e:
        return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", status="SKIPPED", rule_name="Deductible Rule", finding=f"Error evaluating rule: {str(e)}")
