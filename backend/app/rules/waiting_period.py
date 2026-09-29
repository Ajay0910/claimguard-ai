from . import get_val
from datetime import datetime
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Waiting Period Rule",
    description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024 — Waiting Period provisions"
)
def check_waiting_period(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        reasons_list = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
        wp_reasons = [r for r in reasons_list if get_val(r, 'category', '') == "WAITING_PERIOD"]
        if not wp_reasons:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding="No WAITING_PERIOD reason cited.")
            
        policy_start = get_val(policy, 'inception_date', None) or get_val(policy, 'original_inception_date', None) or get_val(policy, 'policy_start_date', None)
        claim_date = get_val(rejection, 'claim_date', None)
        
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
        claim_date = parse_date(claim_date) if isinstance(claim_date, str) else claim_date
        
        if not policy_start or not claim_date:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding="Invalid or missing policy inception or claim date.")
            
        delta_days = (claim_date - policy_start).days
        
        wp_required_days = get_val(policy, 'ped_waiting_period_months', 48) * 30.44
        category_name = "PED"
        
        wp_details = f"{get_val(wp_reasons[0], 'details', '') or ''} {get_val(wp_reasons[0], 'description', '') or ''}"
        
        if "initial" in wp_details.lower() or "30 day" in wp_details.lower():
            wp_required_days = get_val(policy, 'initial_waiting_period_days', 30)
            category_name = "INITIAL"
        elif "specific" in wp_details.lower() or "2 year" in wp_details.lower():
            wp_required_days = get_val(policy, 'specific_illness_waiting_period_months', 24) * 30.44
            category_name = "SPECIFIC_DISEASE"
            
        if delta_days > wp_required_days:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="FAIL",
                rule_name="Waiting Period Rule",
                rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
                confidence=1.0,
                finding=f"The {category_name} waiting period of {wp_required_days:.0f} days has expired. Days elapsed: {delta_days}. The insurer's rejection is incorrect.",
                regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024 — Waiting Period provisions",
                appeal_recommendation=f"The insurer has wrongfully rejected the claim citing a {category_name} waiting period, which has already expired."
            )
            
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
            status="PASS", 
            rule_name="Waiting Period Rule", 
            rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
            confidence=1.0,
            finding=f"Rejection is valid, {category_name} waiting period has not expired. Days elapsed: {delta_days}."
        )
        
    except Exception as e:
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
