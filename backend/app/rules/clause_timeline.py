from . import get_val
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Clause Timeline Rule",
    description="Validates if the rejection violates the moratorium period for pre-existing conditions based on continuous coverage.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024, Para 5.3 – Moratorium Period of 60 months"
)
def check_clause_timeline(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        reasons_list = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
        
        # Check if rejection is related to non-disclosure or pre-existing
        is_non_disclosure = any(
            get_val(reason, 'category', '') == "PRE_EXISTING" or 
            "non-disclosure" in str(get_val(reason, 'description', '')).lower() or
            "pre-existing" in str(get_val(reason, 'description', '')).lower()
            for reason in reasons_list
        )
        
        if not is_non_disclosure:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Rejection does not cite non-disclosure or pre-existing conditions."
            )
            
        policy_start = get_val(policy, 'inception_date', None) or get_val(policy, 'original_inception_date', None) or get_val(policy, 'policy_start_date', None)
        claim_date = get_val(rejection, 'claim_date', None)
        claim_amount = get_val(rejection, 'total_claimed', 0.0)
        
        if not policy_start or not claim_date:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Missing policy inception or claim date for moratorium evaluation."
            )
            
        from dateutil.parser import parse
        def parse_date(d_str):
            if not d_str or str(d_str).strip().upper() == "N/A": return None
            try:
                return datetime.fromisoformat(str(d_str)[:10]).date()
            except ValueError:
                try:
                    return parse(str(d_str)).date()
                except Exception:
                    return None

        policy_start = parse_date(policy_start)
        claim_date_obj = parse_date(claim_date) if isinstance(claim_date, str) else claim_date
        
        if not policy_start or not claim_date_obj:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Invalid or missing policy inception or claim date for moratorium evaluation."
            )
            
        portability_months = get_val(policy, 'portability_credits_months', 0) or 0
        migration_months = get_val(policy, 'migration_credits_months', 0) or 0
        moratorium_months = get_val(policy, 'moratorium_period_months', 60) or 60
        
        months_needed_on_current = moratorium_months - portability_months - migration_months
        moratorium_completion_date = policy_start + relativedelta(months=months_needed_on_current)
        
        if hasattr(policy, "evaluate_moratorium"):
            moratorium_status = policy.evaluate_moratorium(claim_date, claim_amount)
            
            if moratorium_status.get("is_protected", False) and claim_date_obj > moratorium_completion_date:
                finding_text = (
                    f"MORATORIUM_RULE_CONFLICT: Rejection cites non-disclosure/pre-existing after the {moratorium_months}-month moratorium.\n"
                    f"Continuous coverage required: {moratorium_months} months.\n"
                    f"Ported credits: {portability_months} months.\n"
                    f"Coverage start: {policy_start}\n"
                    f"Moratorium completion: {moratorium_completion_date}\n"
                    f"Claim date: {claim_date_obj}\n"
                    "Inconsistency: Claim occurred after moratorium completion. Unless established fraud applies, the claim cannot be contested on these grounds."
                )
                return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                    status="FAIL",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=finding_text,
                    regulatory_citation="IRDAI Master Circular on Health Insurance, 29 May 2024 (60-Month Moratorium)",
                    appeal_recommendation="Appeal citing IRDAI Master Circular 2024: 60-month continuous coverage moratorium prohibits contestation on non-disclosure."
                )
            else:
                return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                    status="PASS",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=f"Claim date ({claim_date_obj}) is before moratorium completion ({moratorium_completion_date}). Rejection is temporally valid."
                )
        else:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Policy object does not support moratorium evaluation."
            )
        
    except Exception as e:
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Clause Timeline Rule", finding=f"Error evaluating rule: {str(e)}")
