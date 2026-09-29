from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from datetime import datetime

def _parse_date(d_str: str):
    if not d_str:
        return None
    try:
        return datetime.fromisoformat(str(d_str).replace('Z', '+00:00')).date()
    except ValueError:
        try:
            return datetime.strptime(str(d_str), '%d/%m/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(str(d_str), '%d-%m-%Y').date()
            except ValueError:
                return None

def is_date_in_range(target_date_str, start_date_str, end_date_str):
    if not target_date_str or not start_date_str: return True
    t = _parse_date(target_date_str)
    s = _parse_date(start_date_str)
    e = _parse_date(end_date_str) if end_date_str else None
    
    if t is None or s is None:
        return True
        
    if e: return s <= t <= e
    else: return s <= t

def _is_valid(val):
    return val and str(val).upper() not in ["UNKNOWN", "NONE", "N/A", ""]

@register_rule(
    name="Policy Applicability Gate",
    description="Pre-execution gate to verify if the policy actually applies to the claim context.",
    tier=0,
    regulatory_citation="IRDAI KYC & Claims Processing Guidelines"
)
def check_policy_applicability(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        conflicts = []
        
        # 1. Identity Check
        rejection_policy_no = get_val(rejection, 'policy_number')
        policy_no = get_val(policy, 'policy_number')
        if _is_valid(rejection_policy_no) and _is_valid(policy_no):
            if str(rejection_policy_no).strip() != str(policy_no).strip():
                conflicts.append(f"Identity Conflict: Rejection policy number ({rejection_policy_no}) does not match Policy Document ({policy_no}).")
                
        # 2. Effective Dates & Coverage Period
        pol_start = get_val(policy, 'policy_start_date', getattr(policy, 'inception_date', None))
        pol_end = get_val(policy, 'policy_end_date', None)
        
        admit_dt = get_val(bill, 'admission_date', None)
        discharge_dt = get_val(bill, 'discharge_date', None)
        claim_dt = get_val(rejection, 'claim_date', None)
        
        # Hospitalization start date is the most relevant for policy applicability
        target_dt = admit_dt if _is_valid(admit_dt) else (discharge_dt if _is_valid(discharge_dt) else claim_dt)
            
        if _is_valid(pol_start) and _is_valid(target_dt):
            if not is_date_in_range(target_dt, pol_start, pol_end):
                conflicts.append(f"Coverage Date Conflict: Event Date {target_dt} outside active policy period {pol_start} to {pol_end}.")
                
        # 3. Benefit Category Check
        if hasattr(bill, 'line_items') and bill.line_items:
            uncovered = False
            for item in bill.line_items:
                cat = get_val(item, 'category', "MISCELLANEOUS")
                cat_str = str(cat).strip().upper()
                
                # If policy has exclusions
                if hasattr(policy, 'exclusions') and policy.exclusions:
                    for excl_item in policy.exclusions:
                        excl_val = excl_item.value if hasattr(excl_item, 'value') else excl_item
                        excl_str = str(excl_val).strip().upper()
                        # Allow comma separated exact matches (no simple substring matching which is brittle)
                        exclusions_list = [e.strip() for e in excl_str.split(',')]
                        if cat_str in exclusions_list:
                            conflicts.append(f"Exclusion Conflict: Claim contains excluded category {cat}.")
                            uncovered = True
                            break
                if uncovered:
                    break

        if len(conflicts) > 0:
            finding_text = (
                "STATUS = BLOCKED\n"
                "BLOCK_REASON = POLICY_MISMATCH\n"
                "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED\n"
                "DETAILS:\n" + "\n".join(conflicts)
            )
            return RuleVerdict(status="BLOCKED", rule_name="Policy Applicability Gate", finding=finding_text, finding_type="POLICY_MISMATCH")
            
        return RuleVerdict(
            status="PASS",
            rule_name="Policy Applicability Gate",
            finding="STATUS = MATCH. Policy is applicable to this claim context.",
            finding_type="NO_ISSUE",
            monetary_impact=None
        )

    except Exception as e:
        return RuleVerdict(status="SKIPPED", rule_name="Policy Applicability Gate", finding=f"Error evaluating rule: {str(e)}", finding_type="EXTRACTION_CONFLICT")
