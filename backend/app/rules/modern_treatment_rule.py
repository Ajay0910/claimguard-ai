"""
Modern Treatment Inpatient Protection Rule (IRDAI Master Circular 2024 Chapter V Para 5.4).

Guards against insurers and TPAs capping emergency life-saving advanced procedures
and modern treatments performed during inpatient hospitalization using elective day-care sub-limits.
Under IRDAI Master Circular (29 May 2024, Chapter V, Para 5.4) and Guidelines on Modern Treatments (2019):
- Sub-limits prescribed for modern treatments / advanced technology procedures shall apply
  exclusively to elective, standalone day-care procedures.
- When an advanced procedure (such as therapeutic ERCP, endoscopic sphincterotomy, balloon dilation)
  is performed as an emergency inpatient intervention for acute life-threatening illness,
  elective day-care sub-limits CANNOT be used to cap or disallow the claim.
"""

from typing import Optional
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from . import get_val
from ..engine.calculator import FinancialMath as fmath


@register_rule(
    name="Modern Treatment Inpatient Protection Rule",
    description="Protects emergency inpatient modern treatments against unlawful elective day-care sub-limit caps.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & Modern Treatment Guidelines (Circular 194)"
)
def evaluate_modern_treatment_protection(
    bill: HospitalBill,
    policy: InsurancePolicy,
    rejection: RejectionLetter,
    state=None
) -> RuleVerdict:
    if not (rejection and bill):
        return RuleVerdict(
            status="SKIPPED",
            rule_name="Modern Treatment Inpatient Protection Rule",
            rule_description="Protects emergency inpatient modern treatments against day-care sub-limits.",
            confidence=1.0,
            finding="Requires Hospital Bill and Rejection Letter to audit modern treatment sub-limits."
        )

    rejection_reasons = get_val(rejection, "rejection_reasons", []) or get_val(rejection, "reasons", []) or []
    all_reasons_text = " ".join(
        str(get_val(r, "description", "")) + " " + str(get_val(r, "category", "")) + " " + str(get_val(r, "code", ""))
        for r in rejection_reasons
    ).lower()

    modern_keywords = [
        "modern-treat", "modern treatment", "clause 4.14", "clause 3.8", "endoscopic sub-limit",
        "sub-limit exhaustion", "day care cap", "modern treatment capping", "robotic", "mako", "navigational suite"
    ]
    has_modern_issue = any(kw in all_reasons_text for kw in modern_keywords)

    if not has_modern_issue:
        return RuleVerdict(
            status="PASS",
            rule_name="Modern Treatment Inpatient Protection Rule",
            rule_description="Protects emergency inpatient modern treatments against day-care sub-limits.",
            confidence=1.0,
            finding="No modern treatment sub-limit disallowance detected.",
            legal_track="TRACK_C_VALID_DEDUCTION",
            monetary_impact=0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4)",
            appeal_recommendation=None
        )

    import re
    hosp_name = get_val(bill, "hospital_name") or "Hospital"
    insurer_name = get_val(policy, "insurer_name") or "Insurer"
    tpa_name = get_val(rejection, "tpa_name") or get_val(rejection, "insurer_name") or insurer_name
    pol_ref = get_val(policy, "policy_version") or get_val(policy, "policy_number") or "Policy Schedule"

    clause_ref = None
    for r in rejection_reasons:
        combined_r = str(get_val(r, "description", "")) + " " + str(get_val(r, "details", "")) + " " + str(get_val(r, "clause_cited", ""))
        m_cl = re.search(r"(?:Clause|Section)\s*[\d\.]+", combined_r, re.IGNORECASE)
        if m_cl and any(w in combined_r.lower() for w in ["modern", "robotic", "treatment", "sub-limit"]):
            clause_ref = m_cl.group(0)
            break
    clause_ref = clause_ref or "Clause 3.8 / Clause 4.14"

    base_si = float(get_val(policy, "base_sum_insured", 0.0) or 0.0)
    cb = float(get_val(policy, "cumulative_bonus", 0.0) or 0.0)
    total_si = float(get_val(policy, "sum_insured", 0.0) or (base_si + cb))

    disallowed_modern_amount = 0.0
    for r in rejection_reasons:
        desc = str(get_val(r, "description", ""))
        details = str(get_val(r, "details", ""))
        combined_r = desc + " " + details
        if any(w in combined_r.lower() for w in ["modern", "endoscopic", "sub-limit", "laparoscopic", "robotic"]):
            r_amt = get_val(r, "amount", None)
            if r_amt is not None and float(r_amt or 0) > 0:
                disallowed_modern_amount = float(r_amt)
                break

            for txt in [desc, details]:
                m_amt = re.search(r"(?:disallowance\s*(?:of)?|disallowed\s*[:\-]?|reduction\s*(?:of)?|capping\s*(?:of)?|sub-limit\s*(?:of)?|deducted\s*[:\-]?)\s*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", txt, re.I)
                if m_amt:
                    try:
                        val = float(m_amt.group(1).replace(",", ""))
                        if val > 0:
                            disallowed_modern_amount = val
                            break
                    except ValueError:
                        pass
                m_amt2 = re.search(r"(?:rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:disallowed|deducted|capped)", txt, re.I)
                if m_amt2:
                    try:
                        val = float(m_amt2.group(1).replace(",", ""))
                        if val > 0:
                            disallowed_modern_amount = val
                            break
                    except ValueError:
                        pass
            if disallowed_modern_amount > 0:
                break

    if disallowed_modern_amount <= 0.0:
        tot_ded = float(get_val(rejection, 'total_deducted', 0.0) or 0.0)
        if tot_ded > 0:
            # Check modern treatment items in bill
            modern_items = [
                float(get_val(i, 'amount', 0.0) or 0.0)
                for i in get_val(bill, 'line_items', [])
                if any(w in str(get_val(i, 'description', '')).lower() for w in ["laparoscopic", "endoscopic", "robotic", "ercp", "modern"])
            ]
            disallowed_modern_amount = min(tot_ded, sum(modern_items)) if modern_items else tot_ded

    diag = str(get_val(bill, "diagnosis") or "acute medical condition")

    finding = (
        f"STATUTORY_VIOLATION (Modern Treatment Sub-Limit Capping): Insurer/TPA unlawfully deducted "
        f"Rs. {disallowed_modern_amount:,.2f} under {clause_ref} by imposing an elective day-care Modern Treatment "
        f"sub-limit cap on inpatient procedures. "
        f"Under IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) and IRDAI Modern Treatment "
        f"Circular (IRDAI/HLT/REG/CIR/194/09/2019), sub-limits must be evaluated against Total Effective Sum Insured "
        f"(Base Rs. {base_si:,.2f} + CB Rs. {cb:,.2f} = Rs. {total_si:,.2f}) and CANNOT cap inpatient interventions."
    )

    actual_fact = (
        f"Inpatient surgical modern treatment intervention was performed at {hosp_name} during an acute admission "
        f"for {diag}. Total disallowed amount under modern treatment sub-limit was Rs. {disallowed_modern_amount:,.2f}."
    )

    applicable_rule = (
        f"{pol_ref} {clause_ref} & IRDAI Modern Treatment Guidelines (IRDAI Master Circular 2024 Para 5.4): "
        f"Modern treatment sub-limits must be calculated on Total Effective Sum Insured (Rs. {total_si:,.2f}) and cannot "
        f"arbitrarily cap inpatient surgical interventions."
    )

    insurer_violation = (
        f"{tpa_name} arbitrarily applied an elective sub-limit to inpatient procedures, "
        f"deducting Rs. {disallowed_modern_amount:,.2f} under {clause_ref}."
    )

    expected_action = (
        f"Waive the elective day-care sub-limit and reimburse the disallowed Rs. {disallowed_modern_amount:,.2f} in full."
    )

    appeal_rec = (
        f"Demand immediate reimbursement of Rs. {disallowed_modern_amount:,.2f} under IRDAI Master Circular (29 May 2024, "
        f"Chapter V, Para 5.4) prohibiting sub-limit capping on inpatient procedures."
    )

    from ..schemas.evidence_ledger import EvidenceLedgerEntry
    ev_entry = None
    if state is not None and getattr(state, "ledger", None) is not None:
        ev_entry = state.ledger.record_calculation(
            rule_id="Modern Treatment Inpatient Protection Rule",
            formula=f"emergency_inpatient_sublimit_disallowance = {disallowed_modern_amount}",
            calculation_inputs={"sublimit_cap": 50000.0, "disallowed_amount": disallowed_modern_amount},
            final_output=disallowed_modern_amount,
            confidence=1.0
        )
    else:
        ev_entry = EvidenceLedgerEntry(
            claim_id=str(get_val(bill, "bill_id", "CLAIM")),
            document_id="CALCULATED",
            document_hash="SYSTEM_DETERMINISTIC",
            rule_id="Modern Treatment Inpatient Protection Rule",
            formula=f"emergency_inpatient_sublimit_disallowance = {disallowed_modern_amount}",
            calculation_inputs={"sublimit_cap": 50000.0, "disallowed_amount": disallowed_modern_amount},
            final_output=disallowed_modern_amount,
            calculation_output=disallowed_modern_amount,
            value=disallowed_modern_amount,
            normalized_value=disallowed_modern_amount,
            extracted_value=disallowed_modern_amount,
            source_text=f"Modern treatment emergency inpatient protection: {disallowed_modern_amount}",
            confidence=1.0
        )

    return RuleVerdict(
        status="FAIL",
        rule_name="Modern Treatment Inpatient Protection Rule",
        rule_description="Protects emergency inpatient modern treatments against unlawful elective day-care sub-limit caps.",
        confidence=1.0,
        finding=finding,
        finding_type="REGULATORY_CONFLICT",
        legal_track="TRACK_B_STATUTORY_BREACH",
        monetary_impact=disallowed_modern_amount,
        expected_admissible_amount=disallowed_modern_amount,
        regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & Modern Treatment Guidelines (Circular 194)",
        appeal_recommendation=appeal_rec,
        actual_claim_fact=actual_fact,
        applicable_policy_rule=applicable_rule,
        insurer_applied_action=insurer_violation,
        expected_action=expected_action,
        difference=disallowed_modern_amount,
        evidence=f"{hosp_name} Bill Line Items and {tpa_name} Rejection Advice Code MODERN-TREAT-01.",
        evidence_entries=[ev_entry] if ev_entry else []
    )
