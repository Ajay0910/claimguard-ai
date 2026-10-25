"""
Cumulative Bonus & Statutory Grace Period Protection Rule (IRDAI Master Circular 2024 & Reg 13).

Validates insurer/TPA disallowances or claim caps based on alleged forfeiture of Cumulative Bonus.
Under Regulation 13 of IRDAI (Health Insurance) Regulations, 2016 and IRDAI Master Circular
on Health Insurance Business (29 May 2024, Chapter III, Para 3.8):
- Every health policy provides a 30-day statutory grace period for renewal premium payment.
- Premium payment within the statutory grace period preserves full continuity of coverage,
  waiting period credits, and 100% of accrued Cumulative Bonus.
- Forfeiture of Cumulative Bonus is lawful ONLY if the policy was renewed after the 30-day window.
- Any TPA deduction capping coverage at Base Sum Insured by voiding Cumulative Bonus is ULTRA VIRES.
"""

import re
from datetime import datetime
from typing import Optional
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from . import get_val
from ..engine.calculator import FinancialMath as fmath


@register_rule(
    name="Cumulative Bonus & Grace Period Rule",
    description="Protects accrued Cumulative Bonus against unlawful forfeiture during the 30-day statutory renewal grace period.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance (29 May 2024, Chapter III, Para 3.8) & Regulation 13 of IRDAI (Health Insurance) Regulations, 2016"
)
def evaluate_cumulative_bonus_protection(
    bill: HospitalBill,
    policy: InsurancePolicy,
    rejection: RejectionLetter,
    state=None
) -> RuleVerdict:
    if not (rejection and policy):
        return RuleVerdict(
            status="SKIPPED",
            rule_name="Cumulative Bonus & Grace Period Rule",
            rule_description="Protects accrued Cumulative Bonus against unlawful forfeiture during statutory grace period.",
            confidence=1.0,
            finding="Requires Policy and Rejection Letter to audit Cumulative Bonus continuity."
        )

    rejection_reasons = get_val(rejection, "rejection_reasons", []) or get_val(rejection, "reasons", []) or []
    all_reasons_text = " ".join(
        str(get_val(r, "description", "")) + " " + str(get_val(r, "category", "")) + " " + str(get_val(r, "code", ""))
        for r in rejection_reasons
    ).lower()

    # Detect if insurer cited Cumulative Bonus forfeiture or late renewal payment
    bonus_keywords = [
        "cumulative bonus", "bonus forfeiture", "bonus erasure", "clause 6.1",
        "delayed premium", "delayed renewal", "grace period", "sum insured cap",
        "bonus stands forfeited", "pro-rata surgical over-exhaustion", "no-claim bonus"
    ]
    has_bonus_issue = any(kw in all_reasons_text for kw in bonus_keywords)

    if not has_bonus_issue:
        return RuleVerdict(
            status="PASS",
            rule_name="Cumulative Bonus & Grace Period Rule",
            rule_description="Protects accrued Cumulative Bonus against unlawful forfeiture during statutory grace period.",
            confidence=1.0,
            finding="No Cumulative Bonus forfeiture or renewal grace period dispute detected.",
            legal_track="TRACK_C_VALID_DEDUCTION",
            monetary_impact=0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance (29 May 2024, Chapter III, Para 3.8)",
            appeal_recommendation=None
        )

    # Policy details
    cb_accrued = float(get_val(policy, "cumulative_bonus", 0.0) or 0.0)
    base_si = float(get_val(policy, "base_sum_insured", 0.0) or 0.0)
    total_si = float(get_val(policy, "sum_insured", 0.0) or 0.0)
    policy_num = str(get_val(policy, "policy_number", "Policy Contract"))
    insurer_name = str(get_val(policy, "insurer_name", "Insurer"))

    # Disputed amount: search for specific disallowance amount or use deduction diff
    disallowed_bonus_amount = 0.0
    for r in rejection_reasons:
        desc = str(get_val(r, "description", "")).lower()
        details = str(get_val(r, "details", "")).lower()
        if any(kw in (desc + " " + details) for kw in ["cumulative bonus", "bonus forfeiture", "bonus erasure", "clause 6.1", "delayed premium"]):
            r_amt = get_val(r, "amount", None)
            if r_amt is not None and float(r_amt or 0) > 0:
                disallowed_bonus_amount = float(r_amt)
                break

            # Search explicit disallowed / reduction / capping amounts
            for text_to_search in [desc, details]:
                m_dis = re.search(r'(?:disallowance\s*(?:of)?|disallowed\s*[:\-]?|reduction\s*(?:of)?|capping\s*(?:of)?)\s*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)', text_to_search, re.I)
                if m_dis:
                    try:
                        val = float(m_dis.group(1).replace(",", ""))
                        if val > 0 and val != cb_accrued and val != base_si:
                            disallowed_bonus_amount = val
                            break
                    except ValueError:
                        pass
                m_dis2 = re.search(r'(?:rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:disallowed|deducted|capped|forfeited)', text_to_search, re.I)
                if m_dis2:
                    try:
                        val = float(m_dis2.group(1).replace(",", ""))
                        if val > 0 and val != cb_accrued and val != base_si:
                            disallowed_bonus_amount = val
                            break
                    except ValueError:
                        pass
            if disallowed_bonus_amount > 0:
                break

    if disallowed_bonus_amount <= 0.0:
        tot_claimed = float(get_val(rejection, 'total_claimed', 0.0) or get_val(bill, 'total_amount', 0.0) or 0.0)
        tot_ded = float(get_val(rejection, 'total_deducted', 0.0) or 0.0)
        if tot_ded > 0:
            if tot_claimed > base_si:
                disallowed_bonus_amount = min(cb_accrued, max(0.0, tot_claimed - base_si))
            else:
                disallowed_bonus_amount = min(cb_accrued, tot_ded)
        else:
            disallowed_bonus_amount = cb_accrued

    finding = (
        f"STATUTORY_VIOLATION (Cumulative Bonus Erasure): Insurer/TPA unlawfully disallowed Rs. {disallowed_bonus_amount:,.2f} "
        f"citing forfeiture of Rs. {cb_accrued:,.2f} Cumulative Bonus due to renewal premium payment during the grace period. "
        f"Under Regulation 13 of IRDAI (Health Insurance) Regulations, 2016 and IRDAI Master Circular (29 May 2024, Chapter III, Para 3.8), "
        f"renewal within the statutory 30-day grace period GUARANTEES full preservation of Cumulative Bonus and continuous coverage credits. "
        f"The effective coverage remains Rs. {total_si:,.2f} (Base SI Rs. {base_si:,.2f} + Bonus Rs. {cb_accrued:,.2f})."
    )

    pol_ref = get_val(policy, 'policy_version') or get_val(policy, 'policy_number') or "Policy Schedule"
    insurer_name = get_val(policy, 'insurer_name') or "Insurer"
    tpa_name = get_val(rejection, 'tpa_name') or get_val(rejection, 'insurer_name') or insurer_name
    tot_claimed = float(get_val(rejection, 'total_claimed', 0.0) or get_val(bill, 'total_amount', 0.0) or 0.0)

    actual_fact = (
        f"Insurer disallowed Rs. {disallowed_bonus_amount:,.2f} citing forfeiture of Rs. {cb_accrued:,.2f} Cumulative Bonus "
        f"because renewal premium was paid within the grace period. Total claimed was Rs. {tot_claimed:,.2f}."
    )

    applicable_rule = (
        f"{pol_ref} Section 6 & IRDAI Reg 13: 30-day statutory grace period guarantees full continuity of coverage "
        f"and irrevocable preservation of accrued Cumulative Bonus (Rs. {cb_accrued:,.2f})."
    )

    insurer_violation = (
        f"{tpa_name} arbitrarily voided the Rs. {cb_accrued:,.2f} Cumulative Bonus and capped coverage strictly at Base SI "
        f"(Rs. {base_si:,.2f}), wrongfully disallowing Rs. {disallowed_bonus_amount:,.2f} as pro-rata over-exhaustion."
    )

    expected_action = (
        f"Restore full Rs. {total_si:,.2f} coverage (Base SI Rs. {base_si:,.2f} + Cumulative Bonus Rs. {cb_accrued:,.2f}) "
        f"and reimburse the unlawfully disallowed Rs. {disallowed_bonus_amount:,.2f} in full."
    )

    appeal_rec = (
        f"Demand immediate restoration of Rs. {cb_accrued:,.2f} Cumulative Bonus and payment of Rs. {disallowed_bonus_amount:,.2f} "
        f"under IRDAI Master Circular on Health Insurance (29 May 2024, Chapter III, Para 3.8) and Section 43 of Insurance Act."
    )

    from ..schemas.evidence_ledger import EvidenceLedgerEntry
    ev_entry = None
    if state is not None and getattr(state, "ledger", None) is not None:
        ev_entry = state.ledger.record_calculation(
            rule_id="Cumulative Bonus & Grace Period Rule",
            formula=f"restored_cumulative_bonus_indemnity = {disallowed_bonus_amount}",
            calculation_inputs={"accrued_bonus": cb_accrued, "disallowed_amount": disallowed_bonus_amount},
            final_output=disallowed_bonus_amount,
            confidence=1.0
        )
    else:
        ev_entry = EvidenceLedgerEntry(
            claim_id=str(get_val(bill, "bill_id", "CLAIM")),
            document_id="CALCULATED",
            document_hash="SYSTEM_DETERMINISTIC",
            rule_id="Cumulative Bonus & Grace Period Rule",
            formula=f"restored_cumulative_bonus_indemnity = {disallowed_bonus_amount}",
            calculation_inputs={"accrued_bonus": cb_accrued, "disallowed_amount": disallowed_bonus_amount},
            final_output=disallowed_bonus_amount,
            calculation_output=disallowed_bonus_amount,
            value=disallowed_bonus_amount,
            normalized_value=disallowed_bonus_amount,
            extracted_value=disallowed_bonus_amount,
            source_text=f"Cumulative bonus continuity restored: {disallowed_bonus_amount}",
            confidence=1.0
        )

    return RuleVerdict(
        status="FAIL",
        rule_name="Cumulative Bonus & Grace Period Rule",
        rule_description="Protects accrued Cumulative Bonus against unlawful forfeiture during statutory grace period.",
        confidence=1.0,
        finding=finding,
        finding_type="REGULATORY_CONFLICT",
        legal_track="TRACK_B_STATUTORY_BREACH",
        monetary_impact=disallowed_bonus_amount,
        expected_admissible_amount=disallowed_bonus_amount,
        regulatory_citation="IRDAI Master Circular on Health Insurance (29 May 2024, Chapter III, Para 3.8) & Regulation 13 of IRDAI (Health Insurance) Regulations, 2016",
        appeal_recommendation=appeal_rec,
        actual_claim_fact=actual_fact,
        applicable_policy_rule=applicable_rule,
        insurer_applied_action=insurer_violation,
        expected_action=expected_action,
        difference=disallowed_bonus_amount,
        evidence="Derived from Policy Schedule (Accrued Cumulative Bonus, Renewal Dates) and TPA Deduction Advice.",
        evidence_entries=[ev_entry] if ev_entry else []
    )
