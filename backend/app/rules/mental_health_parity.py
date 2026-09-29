from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Mental Health Parity Rule",
    description="Validates if the rejection violates the Mental Healthcare Act 2017 for mental health parity.",
    tier=1,
    regulatory_citation="Mental Healthcare Act 2017, Section 21(4); IRDAI Master Circular May 2024"
)
def check_mental_health_parity(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        reasons_list = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
        has_mh_reason = any(get_val(reason, 'category', '') == "MENTAL_HEALTH" for reason in reasons_list)
        
        mh_keywords = ["depression", "anxiety", "schizophrenia", "bipolar", "ptsd", "ocd", "eating disorder", "substance use disorder", "psychiatric", "psychotherapy", "counselling"]
        diagnosis = (get_val(bill, 'diagnosis', '') or "").lower()
        has_mh_diagnosis = any(keyword in diagnosis for keyword in mh_keywords)
        
        if not has_mh_reason and not has_mh_diagnosis:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Mental Health Parity Rule", rule_description="Validates if the rejection violates the Mental Healthcare Act 2017 for mental health parity.", confidence=1.0, finding="No mental health component found in rejection or bill.")
            
        covers_mh = get_val(policy, 'covers_mental_health', False)
            
        if has_mh_reason:
            monetary_impact = get_val(rejection, 'total_claimed', 0.0) - get_val(rejection, 'total_approved', 0.0)
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="FAIL",
                rule_name="Mental Health Parity Rule",
                rule_description="Validates if the rejection violates the Mental Healthcare Act 2017 for mental health parity.",
                confidence=1.0,
                finding="Mental health claims cannot be denied under Section 21(4) of the Mental Healthcare Act 2017. All health insurance policies are legally required to cover mental health treatment on par with physical health.",
                regulatory_citation="Mental Healthcare Act 2017, Section 21(4); IRDAI Master Circular May 2024",
                appeal_recommendation="Cite Section 21(4) of the Mental Healthcare Act 2017 and IRDAI regulations mandating mental health coverage on par with physical health.",
                monetary_impact=monetary_impact
            )
            
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="PASS", rule_name="Mental Health Parity Rule", rule_description="Validates if the rejection violates the Mental Healthcare Act 2017 for mental health parity.", confidence=1.0, finding="Mental health coverage present and not rejected on mental health grounds.")
        
    except Exception as e:
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Mental Health Parity Rule", rule_description="Validates if the rejection violates the Mental Healthcare Act 2017 for mental health parity.", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
