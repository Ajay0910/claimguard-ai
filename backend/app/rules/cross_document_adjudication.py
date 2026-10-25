from typing import Dict, Any, List
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from ..schemas.evidence_ledger import EvidenceLedgerEntry
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
            
    from ..engine.calculator import FinancialMath
    diff_dec = FinancialMath.sub(
        FinancialMath.to_decimal(expected_liability),
        FinancialMath.to_decimal(total_approved),
        formula="expected_liability - total_approved",
        quantize=True
    )
    difference = FinancialMath.to_float(diff_dec)

    pat_name = get_val(bill, "patient_name") or get_val(policy, "policyholder_name") or "Patient"
    hosp_name = get_val(bill, "hospital_name") or "Hospital"
    bill_id = get_val(bill, "bill_id") or "Bill"
    insurer_name = get_val(policy, "insurer_name") or get_val(rejection, "insurer_name") or "Insurer"
    pol_num = get_val(policy, "policy_number") or "Policy"
    claim_num = get_val(rejection, "claim_number") or "Claim"
    sum_ins = float(get_val(policy, "sum_insured", 0.0) or 0.0)
    
    # Determine actual_claim_fact
    actual_claim_fact = f"Patient billed {total_billed}, but insurer approved only {total_approved}."
    
    # Identify applicable policy rules based on rejection reasons (human-readable and category-preserving)
    category_map = {
        "PRE_EXISTING": "PRE_EXISTING: Pre-Existing Disease Moratorium Protection (IRDAI Master Circular 2024 Chapter V Para 5.3)",
        "WAITING_PERIOD": "WAITING_PERIOD: Portability Continuity & Specific Illness Waiting Period Provisions",
        "PROPORTIONATE_DEDUCTION": "PROPORTIONATE_DEDUCTION: Uncapped Room Rent Entitlement & Mandatory Proportionate Protection (IRDAI 2024 Para 5.4)",
        "NON-MEDICAL": "Non-Medical: Statutory Non-Payable Items Schedule (IRDAI Annexure A Lists I & III)",
        "OTHER": "OTHER: Inpatient Surgical Instrumentation & Modern Treatment Procedural Protections"
    }
    readable_rules = []
    seen = set()
    rejection_reasons = get_val(rejection, "rejection_reasons", []) or get_val(rejection, "reasons", []) or []
    for reason in rejection_reasons:
        cat = str(get_val(reason, "category", "")).strip()
        cat_upper = cat.upper()
        rule_desc = category_map.get(cat_upper, f"{cat}: Surviving Valid Policy Terms")
        if rule_desc and rule_desc not in seen:
            seen.add(rule_desc)
            readable_rules.append(rule_desc)
    applicable_policy_rule = "; ".join(readable_rules) if readable_rules else "IRDAI Master Circular 2024 & Policy Schedule Admissible Coverage Terms"
    
    # Insurer applied action
    insurer_applied_action = (
        f"Insurer {insurer_name} deducted {total_deducted} (Rs. {total_deducted:,.2f}) across disputed heads "
        f"({applicable_policy_rule}) under Claim {claim_num}."
    )
    
    # Expected action
    expected_action = (
        f"Expected approval of {expected_liability} (Rs. {expected_liability:,.2f}) based on surviving valid policy terms "
        f"under {pol_num} (Sum Insured Rs. {sum_ins:,.2f}). Unjustified disallowance of Rs. {difference:,.2f} must be restored."
    )
    
    evidence = (
        f"Reconciled across {hosp_name} Hospital Bill ({bill_id}: Rs. {total_billed:,.2f}), "
        f"{insurer_name} Policy Schedule ({pol_num}: Sum Insured Rs. {sum_ins:,.2f}), and "
        f"Rejection/Settlement Advice ({claim_num}: Approved Rs. {total_approved:,.2f}, Deducted Rs. {total_deducted:,.2f})."
    )
    
    evidence_entry = None
    if state is not None and getattr(state, 'ledger', None) is not None:
        evidence_entry = state.ledger.record_calculation(
            rule_id="Cross-Document Adjudication",
            formula=f"expected_liability - total_approved ({expected_liability} - {total_approved})",
            calculation_inputs={"expected_liability": expected_liability, "total_approved": total_approved},
            final_output=difference,
            confidence=1.0
        )
    else:
        evidence_entry = EvidenceLedgerEntry(
            claim_id=str(get_val(bill, "bill_id", "CLAIM")),
            document_id="CALCULATED",
            document_hash="SYSTEM_DETERMINISTIC",
            rule_id="Cross-Document Adjudication",
            formula=f"expected_liability - total_approved ({expected_liability} - {total_approved})",
            calculation_inputs={"expected_liability": expected_liability, "total_approved": total_approved},
            final_output=difference,
            calculation_output=difference,
            value=difference,
            normalized_value=difference,
            extracted_value=difference,
            source_text=f"Hospital Bill ({total_billed}) - Approved ({total_approved}) = Difference ({difference})",
            confidence=1.0
        )
    
    status = "NEEDS_REVIEW" if difference > 0 else "PASS"
    legal_track = "TRACK_A_ARITHMETIC_BREACH" if difference > 0 else "NOT_APPLICABLE"
    
    return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
        status=status,
        rule_name="Cross-Document Adjudication",
        rule_description="Explicitly connects Hospital Bill, Insurance Policy, and Rejection Letter.",
        finding=f"Cross-document logic calculated difference: {difference}",
        legal_track=legal_track,
        monetary_impact=difference,
        actual_claim_fact=actual_claim_fact,
        applicable_policy_rule=applicable_policy_rule,
        insurer_applied_action=insurer_applied_action,
        expected_action=expected_action,
        difference=difference,
        evidence=evidence,
        evidence_entries=[evidence_entry] if evidence_entry else []
    )
