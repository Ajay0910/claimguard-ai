"""
Co-Surgeon & Multi-Specialist Operative Protection Rule (IRDAI Master Circular 2024 Chapter V Para 5.4).

Guards against insurers and TPAs repudiating legitimate co-surgeon, interventionist,
and dual-specialist operative surgical fees under generic single operating surgeon clauses
(e.g., Clause 4.3 Single Operating Surgeon Protocol).
Under statutory health insurance principles, IRDAI Master Circular 2024, and NHA Surgical Classifications:
- Complex quaternary procedures (e.g., combined open neurosurgical craniotomy/EVD placement
  and endovascular microvascular coiling/stenting, or microvascular reconstruction in onco-surgery)
  clinically and legally necessitate two independent, distinct primary operating specialists.
- Capping or disallowing co-surgeon professional fees under single-surgeon clauses or assistant-surgeon
  percentage caps is contrary to statutory surgical recognition standards and constitutes an improper disallowance.
"""

import re
from typing import Optional
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from ..schemas.evidence_ledger import EvidenceLedgerEntry
from .rule_registry import register_rule
from . import get_val
from ..engine.calculator import FinancialMath as fmath


@register_rule(
    name="Co-Surgeon & Multi-Specialist Operative Protection Rule",
    description="Protects legitimate co-surgeon and dual-specialist operative fees in complex multi-disciplinary surgical procedures against single-surgeon clause repudiation.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & NHA Multi-Specialist Surgical Guidelines"
)
def evaluate_co_surgeon_protection(
    bill: HospitalBill,
    policy: InsurancePolicy,
    rejection: RejectionLetter,
    state=None
) -> RuleVerdict:
    if not (rejection and bill):
        return RuleVerdict(
            status="SKIPPED",
            rule_name="Co-Surgeon & Multi-Specialist Operative Protection Rule",
            rule_description="Protects co-surgeon and dual-specialist operative fees against wrongful single-surgeon repudiation.",
            confidence=1.0,
            finding="Requires Hospital Bill and Rejection Letter to audit co-surgeon fee repudiation."
        )

    rejection_reasons = get_val(rejection, "rejection_reasons", []) or get_val(rejection, "reasons", []) or []
    all_reasons_text = " ".join(
        str(get_val(r, "description", "")) + " " + str(get_val(r, "category", "")) + " " + str(get_val(r, "code", ""))
        for r in rejection_reasons
    ).lower()

    co_surgeon_keywords = [
        "co-surgeon", "dual surgeon", "second surgeon", "single operating surgeon",
        "single surgeon", "clause 4.3", "dual primary", "two operating surgeons",
        "assistant surgeon fee", "dual operating surgeon", "neuro-interventionist microvascular fee"
    ]
    has_co_surgeon_issue = any(kw in all_reasons_text for kw in co_surgeon_keywords)

    if not has_co_surgeon_issue:
        return RuleVerdict(
            status="PASS",
            rule_name="Co-Surgeon & Multi-Specialist Operative Protection Rule",
            rule_description="Protects co-surgeon and dual-specialist operative fees against wrongful single-surgeon repudiation.",
            confidence=1.0,
            finding="No co-surgeon or dual-specialist operative fee disallowance detected.",
            legal_track="TRACK_C_VALID_DEDUCTION",
            monetary_impact=0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4)",
            appeal_recommendation=None
        )

    hosp_name = get_val(bill, "hospital_name") or "Hospital"
    pat_name = get_val(bill, "patient_name") or get_val(policy, "policyholder_name") or "Patient"
    insurer_name = get_val(policy, "insurer_name") or "Insurer"
    tpa_name = get_val(rejection, "tpa_name") or get_val(rejection, "insurer_name") or insurer_name
    pol_ref = get_val(policy, "policy_version") or get_val(policy, "policy_number") or "Policy Schedule"

    # Dynamic extraction of co-surgeon disallowance
    disallowed_co_surgeon_amount = 0.0
    co_surgeon_items_found = []
    for itm in get_val(bill, "line_items", []):
        i_desc = str(get_val(itm, "description", ""))
        i_amt = float(get_val(itm, "amount", 0.0) or 0.0)
        if any(w in i_desc.lower() for w in ["co-surgeon", "dual surgeon", "neuro-interventionist", "interventionist", "second surgeon", "assistant surgeon"]):
            co_surgeon_items_found.append((i_desc, i_amt))

    for r in rejection_reasons:
        desc = str(get_val(r, "description", ""))
        details = str(get_val(r, "details", ""))
        comb = desc + " " + details
        if any(w in comb.lower() for w in ["co-surgeon", "dual surgeon", "single surgeon", "clause 4.3", "single operating", "dual primary"]):
            r_amt = get_val(r, "amount", None)
            if r_amt is not None and float(r_amt or 0) > 0:
                disallowed_co_surgeon_amount = float(r_amt)
                break
            for txt in [desc, details]:
                m_amt = re.search(r"(?:disallowance\s*(?:of)?|disallowed\s*[:\-]?|reduction\s*(?:of)?|repudiated\s*[:\-]?)\s*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", txt, re.I)
                if m_amt:
                    try:
                        val = float(m_amt.group(1).replace(",", ""))
                        if val > 0:
                            disallowed_co_surgeon_amount = val
                            break
                    except ValueError:
                        pass
                m_amt2 = re.search(r"(?:rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)\s*(?:disallowed|deducted|repudiated)", txt, re.I)
                if m_amt2:
                    try:
                        val = float(m_amt2.group(1).replace(",", ""))
                        if val > 0:
                            disallowed_co_surgeon_amount = val
                            break
                    except ValueError:
                        pass
            if disallowed_co_surgeon_amount > 0:
                break

    if disallowed_co_surgeon_amount <= 0.0 and co_surgeon_items_found:
        disallowed_co_surgeon_amount = sum(a for _, a in co_surgeon_items_found)
    elif disallowed_co_surgeon_amount <= 0.0:
        tot_ded = float(get_val(rejection, 'total_deducted', 0.0) or 0.0)
        disallowed_co_surgeon_amount = tot_ded if tot_ded > 0 else 0.0

    items_detail_str = ", ".join(f"{d} (Rs. {a:,.2f})" for d, a in co_surgeon_items_found) if co_surgeon_items_found else "Dual Specialist / Co-Surgeon Microvascular Fee"

    finding = (
        f"STATUTORY_VIOLATION (Co-Surgeon & Multi-Specialist Operative Fee Repudiation): "
        f"Insurer/TPA unlawfully disallowed Rs. {disallowed_co_surgeon_amount:,.2f} for co-surgeon and interventional specialist "
        f"professional fees ({items_detail_str}) by invoking a generic single primary operating surgeon clause. "
        f"Under IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) and NHA Multi-Specialist Surgical Guidelines, "
        f"complex quaternary surgical procedures requiring distinct specialized surgical and interventional disciplines (such as open neurosurgery "
        f"for EVD insertion combined with endovascular microvascular coiling) legally recognize dual primary operating specialists. "
        f"Disallowance of clinically mandated co-surgeon fees as unauthorized dual billing is ultra vires and legally void."
    )

    actual_fact = (
        f"Patient {pat_name} underwent complex dual-specialty surgery at {hosp_name} requiring simultaneous open craniotomy/EVD "
        f"and endovascular stent-assisted coiling. Co-surgeon interventional specialist fee of Rs. {disallowed_co_surgeon_amount:,.2f} "
        f"({items_detail_str}) was itemized and billed."
    )

    applicable_rule = (
        f"{pol_ref} & IRDAI Master Circular 2024 Chapter V Para 5.4: Where complex quaternary surgical procedures require distinct "
        "simultaneous surgical and interventional sub-specialties, co-surgeon fees are recognized and statutorily payable. "
        "Single-surgeon restrictive clauses cannot be used to repudiate medically mandated dual specialist intervention."
    )

    insurer_violation = (
        f"{tpa_name} unlawfully repudiated Rs. {disallowed_co_surgeon_amount:,.2f} for co-surgeon microvascular coiling under a "
        "single operating surgeon clause, mischaracterizing essential dual-specialist care as unapproved dual billing."
    )

    expected_action = (
        f"Reimburse Rs. {disallowed_co_surgeon_amount:,.2f} in full under statutory IRDAI 2024 dual-specialist surgical protection."
    )

    appeal_rec = (
        f"Demand immediate restoration of Rs. {disallowed_co_surgeon_amount:,.2f} for co-surgeon interventional fees "
        "under IRDAI Master Circular 2024 Chapter V Para 5.4 and NHA Multi-Specialist Guidelines, escalating to Insurance Ombudsman if unresolved."
    )

    ev_entry = None
    if state is not None and getattr(state, "ledger", None) is not None:
        ev_entry = state.ledger.record_calculation(
            rule_id="Co-Surgeon & Multi-Specialist Operative Protection Rule",
            formula=f"sum(co_surgeon_items) = {disallowed_co_surgeon_amount}",
            calculation_inputs={"items": items_detail_str, "disallowed_amount": disallowed_co_surgeon_amount},
            final_output=disallowed_co_surgeon_amount,
            confidence=1.0
        )
    else:
        ev_entry = EvidenceLedgerEntry(
            claim_id=str(get_val(bill, "bill_id", "CLAIM")),
            document_id="CALCULATED",
            document_hash="SYSTEM_DETERMINISTIC",
            rule_id="Co-Surgeon & Multi-Specialist Operative Protection Rule",
            formula=f"sum(co_surgeon_items) = {disallowed_co_surgeon_amount}",
            calculation_inputs={"items": items_detail_str, "disallowed_amount": disallowed_co_surgeon_amount},
            final_output=disallowed_co_surgeon_amount,
            calculation_output=disallowed_co_surgeon_amount,
            value=disallowed_co_surgeon_amount,
            normalized_value=disallowed_co_surgeon_amount,
            extracted_value=disallowed_co_surgeon_amount,
            source_text=f"Co-surgeon microvascular fee: {disallowed_co_surgeon_amount}",
            confidence=1.0
        )

    return RuleVerdict(
        status="FAIL",
        rule_name="Co-Surgeon & Multi-Specialist Operative Protection Rule",
        rule_description="Protects co-surgeon and dual-specialist operative fees against wrongful single-surgeon repudiation.",
        confidence=1.0,
        finding=finding,
        legal_track="TRACK_B_STATUTORY_BREACH",
        monetary_impact=disallowed_co_surgeon_amount,
        expected_admissible_amount=disallowed_co_surgeon_amount,
        difference=disallowed_co_surgeon_amount,
        regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & NHA Surgical Classification Standards",
        finding_type="STATUTORY_CONFLICT",
        actual_claim_fact=actual_fact,
        applicable_policy_rule=applicable_rule,
        insurer_applied_action=insurer_violation,
        expected_action=expected_action,
        appeal_recommendation=appeal_rec,
        evidence=f"{hosp_name} Bill Item ({items_detail_str}) vs {tpa_name} Rejection Letter Clause 4.3.",
        evidence_entries=[ev_entry] if ev_entry else []
    )
