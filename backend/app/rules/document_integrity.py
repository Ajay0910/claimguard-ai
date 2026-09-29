from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Extraction Confidence Gate",
    description="Validates critical fields for low extraction confidence or conflicting candidates.",
    tier=0,
    regulatory_citation=None
)
def check_extraction_confidence(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    conflicts = []
    
    # 1. Gross Bill
    gross_bill = getattr(bill, 'total_amount', None)
    if gross_bill and hasattr(gross_bill, 'extraction_confidence') and gross_bill.extraction_confidence < 0.85:
        conflicts.append(f"Gross Bill amount has low extraction confidence ({gross_bill.extraction_confidence}).")
        
    # 2. Room Rate
    room_rate = getattr(policy, 'room_rent_limit_per_day', None)
    if room_rate and hasattr(room_rate, 'extraction_confidence') and room_rate.extraction_confidence < 0.85:
        conflicts.append(f"Policy Room Rent Limit has low extraction confidence ({room_rate.extraction_confidence}).")
        
    if bill and hasattr(bill, 'line_items'):
        for i, item in enumerate(bill.line_items):
            amt = getattr(item, 'amount', None)
            if amt and hasattr(amt, 'extraction_confidence') and amt.extraction_confidence < 0.85:
                conflicts.append(f"Line Item '{getattr(item, 'item_code', i)}' amount has low confidence ({amt.extraction_confidence}).")
                
    # 3. Approved Amount
    approved = getattr(rejection, 'total_approved', None)
    if approved and hasattr(approved, 'extraction_confidence') and approved.extraction_confidence < 0.85:
        conflicts.append(f"Insurer Approved Amount has low extraction confidence ({approved.extraction_confidence}).")
        
    if conflicts:
        return RuleVerdict(
            finding_type="DOCUMENT_INCONSISTENCY", 
            status="NEEDS_REVIEW",
            rule_name="Extraction Confidence Gate",
            rule_description="Halts if critical fields have low extraction confidence.",
            confidence=1.0,
            finding="CRITICAL FIELD EXTRACTION LOW CONFIDENCE:\n" + "\n".join(conflicts)
        )
        
    return RuleVerdict(
        finding_type="DOCUMENT_INCONSISTENCY", 
        status="PASS",
        rule_name="Extraction Confidence Gate",
        rule_description="Halts if critical fields have low extraction confidence.",
        confidence=1.0,
        finding="Critical fields extraction confidence is acceptable."
    )

@register_rule(
    name="Document Arithmetic Integrity",
    description="Validates if the sum of itemized hospital bill line items matches the stated gross bill total.",
    tier=1,
    regulatory_citation=None
)
def check_document_integrity(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        gross_total = get_val(bill, 'total_amount', 0.0)
        line_items = get_val(bill, 'line_items', [])
        
        if not line_items:
             return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", 
                status="SKIPPED",
                rule_name="Document Arithmetic Integrity",
                rule_description="Validates bill totals.",
                confidence=1.0,
                finding="No line items extracted to verify against gross total."
            )

        sum_items = sum(get_val(item, 'amount', 0.0) for item in line_items)
        difference = abs(gross_total - sum_items)
        
        if difference > 10.0:  # Allow small rounding
            return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", 
                status="WARNING",
                rule_name="Document Arithmetic Integrity",
                rule_description="Validates bill totals.",
                confidence=1.0,
                finding=f"Arithmetic inconsistency detected. Sum of line items (Rs. {sum_items:.2f}) does not match stated gross bill (Rs. {gross_total:.2f}). Difference: Rs. {difference:.2f}.",
                monetary_impact=difference
            )
            
        return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", 
            status="PASS",
            rule_name="Document Arithmetic Integrity",
            rule_description="Validates bill totals.",
            confidence=1.0,
            finding=f"Arithmetic integrity verified. Sum of items (Rs. {sum_items:.2f}) matches gross bill.",
            monetary_impact=0.0
        )

    except Exception as e:
        return RuleVerdict(finding_type="DOCUMENT_INCONSISTENCY", status="SKIPPED", rule_name="Document Arithmetic Integrity", rule_description="", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
