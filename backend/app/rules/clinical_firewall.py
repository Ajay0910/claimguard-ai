from . import get_val
import re
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Clinical Firewall Gate",
    description="Halts financial verification if rejection is based on medical necessity or clinical grounds.",
    tier=0, 
    regulatory_citation=None
)
def check_clinical_firewall(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        clinical_triggers = [
            r"medical necessity",
            r"clinically justified",
            r"unjustified admission",
            r"experimental",
            r"investigational",
            r"active line of treatment",
            r"not medically necessary",
            r"clinical grounds",
            r"treatment protocol",
            r"standard of care",
            r"unwarranted hospitalization"
        ]
        
        reasons_list = get_val(rejection, 'rejection_reasons', []) or get_val(rejection, 'reasons', []) or []
        remarks = get_val(rejection, 'remarks', "") or ""
        
        # Only scan rejection specific texts, avoiding policy definition matches
        texts_to_check = [str(get_val(r, 'description', r)) for r in reasons_list] + [remarks]
        
        for text_fragment in texts_to_check:
            text_fragment = str(text_fragment).lower()
            for trigger in clinical_triggers:
                if re.search(r'\b' + trigger + r'\b', text_fragment):
                    finding_text = (
                        "STATUS = BLOCKED\n"
                        "BLOCK_REASON = CLINICAL_REJECTION_DETECTED\n"
                        "DOCUMENT_A = Rejection Letter\n"
                        "DOCUMENT_B = N/A\n"
                        "FIELD = Rejection Reason\n"
                        f"VALUE_A = {text_fragment[:50]}...\n"
                        "VALUE_B = N/A\n"
                        "ACTION = FINANCIAL_ENGINE_NOT_EXECUTED - Human medical review and physician counter-letter required."
                    )
                    return RuleVerdict(finding_type="CLINICAL_REJECTION", 
                        status="BLOCKED",
                        rule_name="Clinical Firewall Gate",
                        rule_description="Halts verification on clinical rejections.",
                        confidence=1.0,
                        finding=finding_text,
                        monetary_impact=None
                    )
                
        return RuleVerdict(finding_type="CLINICAL_REJECTION", 
            status="PASS",
            rule_name="Clinical Firewall Gate",
            rule_description="Halts verification on clinical rejections.",
            confidence=1.0,
            finding="No clinical or medical necessity rejection grounds detected. Proceeding.",
            monetary_impact=None
        )
        
    except Exception as e:
        return RuleVerdict(finding_type="CLINICAL_REJECTION", status="SKIPPED", rule_name="Clinical Firewall Gate", finding=f"Error evaluating rule: {str(e)}")
