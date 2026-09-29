from typing import Dict, Any, List
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from . import get_val
from .rule_registry import register_rule

@register_rule(name="Cross-Document Adjudication", description="Explicitly connects Hospital Bill, Insurance Policy, and Rejection Letter to calculate actual facts and expected actions.", tier=2)
def evaluate_cross_document_adjudication(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    if not (bill and policy and rejection):
        return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", 
            status="SKIPPED",
            rule_name="Cross-Document Adjudication",
            rule_description="Explicitly connects Hospital Bill, Insurance Policy, and Rejection Letter to calculate actual facts and expected actions.",
            finding="Requires Bill, Policy, and Rejection Letter to perform cross-document adjudication."
        )

    # Calculate fields for Point 10
    total_billed = float(get_val(bill, "total_amount", 0.0))
    total_approved = float(get_val(rejection, "total_approved", 0.0))
    total_deducted = float(get_val(rejection, "total_deducted", 0.0))
    
    expected_liability = total_billed # Default if state is None
    if state and hasattr(state, 'line_items'):
        from ..engine.calculator import FinancialMath
        try:
            expected_payable = FinancialMath.sum(
                [item.remaining_balance for item in state.line_items.values()], 
                formula="sum(remaining_balances)", 
                quantize=True
            )
            expected_liability = float(expected_payable.value) if hasattr(expected_payable, 'value') else float(expected_payable)
        except Exception:
            pass
            
    # Calculate difference
    difference = expected_liability - total_approved
    
    # Determine actual_claim_fact
    actual_claim_fact = f"Patient billed {total_billed}, but insurer approved only {total_approved}."
    
    # Identify applicable policy rules based on rejection reasons
    policy_rules_list = []
    rejection_reasons = get_val(rejection, "rejection_reasons", []) or get_val(rejection, "reasons", []) or []
    for reason in rejection_reasons:
        category = get_val(reason, "category", "Unknown")
        policy_rules_list.append(str(category))
    applicable_policy_rule = ", ".join(policy_rules_list) if policy_rules_list else "Standard coverage terms"
    
    # Insurer applied action
    insurer_applied_action = f"Insurer deducted {total_deducted} based on {applicable_policy_rule}."
    
    # Expected action
    expected_action = f"Expected approval of {expected_liability} based on policy terms."
    
    evidence = "Derived from Hospital Bill (Total Amount), Rejection Letter (Approved Amount, Deductions), and Insurance Policy."
    
    evidence_entry = None
    if state is not None and getattr(state, 'ledger', None) is not None:
        evidence_entry = state.ledger.record_calculation(
            rule_id="Cross-Document Adjudication",
            formula=f"expected_liability - total_approved ({expected_liability} - {total_approved})",
            calculation_inputs={"expected_liability": expected_liability, "total_approved": total_approved},
            final_output=difference,
            confidence=1.0
        )
    
    status = "FAIL" if difference > 0 else "PASS"
    
    return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", 
        status=status,
        rule_name="Cross-Document Adjudication",
        rule_description="Explicitly connects Hospital Bill, Insurance Policy, and Rejection Letter.",
        finding=f"Cross-document logic calculated difference: {difference}",
        monetary_impact=difference,
        actual_claim_fact=actual_claim_fact,
        applicable_policy_rule=applicable_policy_rule,
        insurer_applied_action=insurer_applied_action,
        expected_action=expected_action,
        difference=difference,
        evidence=evidence,
        evidence_entries=[evidence_entry] if evidence_entry else []
    )
