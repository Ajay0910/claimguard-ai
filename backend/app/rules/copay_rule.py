from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Co-Pay Rule",
    description="Applies co-payment percentage. Must be applied AFTER deductibles and proportionate deductions per IRDAI standards.",
    tier=1,
    depends_on=["Deductible Rule", "Proportionate Deduction Rule"], # Explicit Rule Dependency
    regulatory_citation="Policy Schedule - Co-Pay Clause"
)
def check_copay(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    try:
        from ..engine.calculator import FinancialMath as fmath
        
        copay_pct = fmath.extract(get_val(policy, 'copay_percentage', 0.0))
        if copay_pct <= 0:
            return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="NOT_APPLICABLE",
                rule_name="Co-Pay Rule",
                finding="No co-pay applies to this policy."
            )
            
        if state:
            # Co-pay applies to the remaining balance AFTER deductibles and sub-limits
            all_codes = [code for code, item in state.line_items.items() if item.remaining_balance > 0]
            total_remaining = sum(state.get_balance(code) for code in all_codes)
            
            if total_remaining <= 0:
                return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                    status="NOT_APPLICABLE",
                    rule_name="Co-Pay Rule",
                    finding="No remaining balance to apply co-pay."
                )
                
            copay_amount = total_remaining * (copay_pct / 100.0)
            
            adj = state.apply_deduction(
                rule_id="Co-Pay Rule",
                target_item_codes=all_codes,
                deduction_amount=copay_amount,
                formula=f"({total_remaining} * {copay_pct}%)",
                policy_clause="Co-Pay Clause",
                dependencies=["Deductible Rule", "Proportionate Deduction Rule"]
            )
            
            return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="PASS",
                rule_name="Co-Pay Rule",
                finding=f"Applied {copay_pct}% co-pay (Rs. {copay_amount:.2f}) against remaining eligible amount of Rs. {total_remaining:.2f}."
            )
                
        return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
            status="SKIPPED",
            rule_name="Co-Pay Rule",
            finding="No AdjudicationState provided to apply co-pay."
        )

    except Exception as e:
        return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", status="SKIPPED", rule_name="Co-Pay Rule", finding=f"Error evaluating rule: {str(e)}")
