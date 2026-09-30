from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from ..utils.text_matching import match_ids, match_names
from datetime import datetime

def is_date_in_range(target_date_str, start_date_str, end_date_str):
    if not target_date_str or not start_date_str: return True
    try:
        t = datetime.fromisoformat(target_date_str[:10]).date()
        s = datetime.fromisoformat(start_date_str[:10]).date()
        e = datetime.fromisoformat(end_date_str[:10]).date() if end_date_str else None
        
        if e: return s <= t <= e
        else: return s <= t
    except ValueError:
        return True

def _is_valid(val):
    return val and str(val).upper() not in ["UNKNOWN", "NONE", "N/A", ""]

@register_rule(
    name="Cross-Document Identity Gate",
    description="Role-aware identity gate. Weights deterministic IDs heavily. Distinguishes patient from policyholder.",
    tier=0,
    regulatory_citation="IRDAI KYC & Claims Processing Guidelines"
)
def check_identity_gate(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        evidence_points = 0
        conflicts = []
        
        # 1. Deterministic Identifier: Policy Number (High Weight)
        pol_num_policy = get_val(policy, 'policy_number', None)
        pol_num_rejection = get_val(rejection, 'policy_number', None)
        
        if _is_valid(pol_num_policy) and _is_valid(pol_num_rejection):
            if match_ids(pol_num_policy, pol_num_rejection):
                evidence_points += 3 # High weight for exact ID match
            else:
                conflicts.append(f"Policy Number CONFLICT: Policy({pol_num_policy}) vs Rejection({pol_num_rejection})")
                
        # 2. Deterministic Identifier: Claim Number
        claim_num_bill = get_val(bill, 'bill_id', None) # or claim_id
        claim_num_rej = get_val(rejection, 'claim_number', None)
        if _is_valid(claim_num_bill) and _is_valid(claim_num_rej):
            if match_ids(claim_num_bill, claim_num_rej):
                evidence_points += 2
            # Not necessarily a conflict if bill ID != insurer claim ID, so we just add evidence if they match.
            
        # 3. Role-Aware Names: Patient vs Patient
        patient_bill = get_val(bill, 'patient_name', None)
        patient_rej = get_val(rejection, 'patient_name', None)
        
        if _is_valid(patient_bill) and _is_valid(patient_rej):
            if match_names(patient_bill, patient_rej, threshold=0.75):
                evidence_points += 2
            else:
                conflicts.append(f"Patient Name CONFLICT: Bill({patient_bill}) vs Rejection({patient_rej})")

        # 4. Role-Aware Names: Proposer/Policyholder vs Proposer/Policyholder
        policyholder_pol = get_val(policy, 'policyholder_name', getattr(policy, 'policy_holder_name', None))
        policyholder_rej = get_val(rejection, 'policyholder_name', None)
        
        if _is_valid(policyholder_pol) and _is_valid(policyholder_rej):
            if match_names(policyholder_pol, policyholder_rej, threshold=0.75):
                evidence_points += 2
            else:
                conflicts.append(f"Policyholder Name CONFLICT: Policy({policyholder_pol}) vs Rejection({policyholder_rej})")

        # Note: We purposely DO NOT block if patient_bill != policyholder_pol, as they can be legitimately different people (e.g. dependent child).

        # 5. Coverage Dates
        pol_start = get_val(policy, 'policy_start_date', getattr(policy, 'inception_date', None))
        pol_end = get_val(policy, 'policy_end_date', None)
        claim_dt = get_val(rejection, 'claim_date', None)
        
        if _is_valid(pol_start) and _is_valid(claim_dt):
            if not is_date_in_range(claim_dt, pol_start, pol_end):
                conflicts.append(f"Coverage Date CONFLICT: Claim Date {claim_dt} outside {pol_start} to {pol_end}")
            else:
                evidence_points += 1
                
        # Resolve State
        if len(conflicts) > 0:
            finding_text = (
                "STATUS = BLOCKED\n"
                "ACTION = STOP_ADJUDICATION\n"
                "DETAILS:\nIDENTITY_CONFLICT\n" + "\n".join(conflicts)
            )
            return RuleVerdict(finding_type="IDENTITY_CONFLICT", status="BLOCKED", rule_name="Cross-Document Identity Gate", finding=finding_text)
            
        elif evidence_points == 0:
             return RuleVerdict(finding_type="IDENTITY_CONFLICT", 
                status="NEEDS_REVIEW",
                rule_name="Cross-Document Identity Gate",
                finding="STATUS = INSUFFICIENT_EVIDENCE\nACTION = NEEDS_HUMAN_REVIEW\nNo strong matching identifiers (Policy No, Claim No, Patient Name) found across documents to establish identity continuity."
            )
        else:
             return RuleVerdict(finding_type="IDENTITY_CONFLICT", 
                status="PASS",
                rule_name="Cross-Document Identity Gate",
                confidence=min(1.0, evidence_points / 5.0),
                finding=f"STATUS = MATCH\nStrong evidence points: {evidence_points}. Identities and dates verified.",
                monetary_impact=None
            )

    except Exception as e:
        return RuleVerdict(finding_type="IDENTITY_CONFLICT", status="SKIPPED", rule_name="Cross-Document Identity Gate", finding=f"Error evaluating rule: {str(e)}")
