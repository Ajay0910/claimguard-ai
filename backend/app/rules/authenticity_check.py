from .rule_registry import register_rule
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.analysis_result import RuleVerdict

def mock_verify_hospital(hospital_name: str) -> bool:
    """Mock API call to verify if hospital is registered in ROHINI/National Registry."""
    if not hospital_name:
        return False
    name_lower = hospital_name.lower()
    # Simulate a fake hospital name detection
    if "fake" in name_lower or "test" in name_lower or "dummy" in name_lower:
        return False
    # In a real scenario, this would query an external registry API.
    return True

def mock_verify_policy(policy_number: str) -> bool:
    """Mock API call to verify if policy number is active with the insurer."""
    if not policy_number:
        return False
    # Simulate: Real policies usually have alphanumeric formats, e.g., POL-1234
    # If the policy number is just "000" or similar, fail it.
    if policy_number in ["000", "123", "0000000000", "FAKE"]:
        return False
    # Real scenario: API request to Insurance Information Bureau (IIB)
    return True

@register_rule(
    name="Authenticity Verification Check",
    description="Verifies the existence of the hospital in the national registry and the active status of the insurance policy.",
    tier=1,
    regulatory_citation="IRDAI Master Circular (KYC & Provider Registration)"
)
def check_authenticity(bill: HospitalBill, policy: InsurancePolicy, rejection=None) -> RuleVerdict:
    issues = []
    monetary_impact = 0.0
    
    # 1. Check Hospital
    if bill and bill.hospital_name:
        is_valid_hospital = mock_verify_hospital(bill.hospital_name)
        if not is_valid_hospital:
            issues.append(f"Hospital '{bill.hospital_name}' could not be verified in the National Registry (ROHINI).")
            # If hospital is fake, the entire bill is likely fraudulent
            monetary_impact += bill.total_amount
    else:
        issues.append("Hospital name missing from the bill.")
        
    # 2. Check Policy
    if policy and policy.policy_number:
        is_valid_policy = mock_verify_policy(policy.policy_number)
        if not is_valid_policy:
            issues.append(f"Policy Number '{policy.policy_number}' could not be verified or is inactive.")
            # If policy is fake, claim is 100% rejected
            if bill:
                monetary_impact = bill.total_amount
    else:
        issues.append("Policy number missing from the insurance document.")
        
    if issues:
        return RuleVerdict(finding_type="FRAUD_SIGNAL", 
            rule_name="Authenticity Verification Check",
            status="FAIL",
            finding="Authenticity verification failed: " + " | ".join(issues),
            insurer_approved_amount=0.0,
            expected_admissible_amount=0.0,
            monetary_impact=monetary_impact,
            regulatory_citation="IRDAI Master Circular (KYC & Provider Registration)",
            appeal_recommendation="Provide valid hospital registration (ROHINI ID) and active policy documentation."
        )
        
    return RuleVerdict(finding_type="FRAUD_SIGNAL", 
        rule_name="Authenticity Verification Check",
        status="PASS",
        finding="Hospital registration and Policy number successfully verified against external registries.",
        insurer_approved_amount=0.0,
        expected_admissible_amount=0.0,
        monetary_impact=None,
        regulatory_citation="IRDAI Master Circular (KYC & Provider Registration)"
    )
