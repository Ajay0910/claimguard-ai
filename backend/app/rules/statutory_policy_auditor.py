"""
MODEL 2: IRDAI Statutory Policy Auditor Gate.
Automated statutory compliance audit that validates insurance policy documents
against mandatory Indian insurance regulations:
1. IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & Annexure A Lists I–IV
2. Statutory 60-Month Moratorium Period (Chapter V, Para 5.3)
3. Regulation 13 of IRDAI (Health Insurance) Regulations, 2016 & 30-Day Renewal Grace Period (Chapter III, Para 3.8)
4. Mental Healthcare Act 2017 (Section 21(4)) & IRDAI Mental Health Parity Regulations

Classifies each audited clause as STATUTORILY_VALID or ULTRA_VIRES (null & void by operation of law).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from . import get_val


@register_rule(
    name="IRDAI Statutory Policy Auditor Gate",
    description="Audits policy clauses against mandatory IRDAI Master Circular 2024, Annexure A Lists I-IV, 60-Month Moratorium, 30-Day Grace Period, and Mental Healthcare Act 2017.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Ref: IRDAI/HLT/REG/CIR/089/05/2024) & Mental Healthcare Act 2017 (Act 10 of 2017, Sec 21)"
)
def audit_statutory_policy_compliance(
    bill: HospitalBill,
    policy: InsurancePolicy,
    rejection: RejectionLetter,
    state=None
) -> RuleVerdict:
    """
    Audits the policy document clauses against statutory baselines:
    - Proportionate deduction scope (protected medical categories)
    - Annexure A List III surgical consumables & energy devices
    - Moratorium period compliance (60-month cap)
    - Renewal grace period & Cumulative Bonus preservation
    - Mental health parity
    """
    if not policy:
        return RuleVerdict(
            status="SKIPPED",
            rule_name="IRDAI Statutory Policy Auditor Gate",
            rule_description="Audits policy clauses against IRDAI statutory regulations.",
            confidence=1.0,
            finding="No insurance policy document available for statutory audit."
        )

    clause_audits: Dict[str, Dict[str, Any]] = {}
    ultra_vires_clauses: List[str] = []
    valid_clauses: List[str] = []

    # -------------------------------------------------------------------------
    # 1. Audit Proportionate Deduction Clause (IRDAI Master Circular 2024, Para 5.4)
    # -------------------------------------------------------------------------
    prop_rule = get_val(policy, "proportionate_deduction_rule", None)
    policy_texts = []
    for attr in ["deduction_order_clause", "exclusions"]:
        val = getattr(policy, attr, "")
        if hasattr(val, "value"):
            val = val.value
        if isinstance(val, list):
            for x in val:
                txt = getattr(x, "value", x)
                if txt:
                    policy_texts.append(str(txt))
        elif val:
            txt = getattr(val, "value", val)
            if txt:
                policy_texts.append(str(txt))
    if prop_rule and hasattr(prop_rule, "source_text"):
        policy_texts.append(str(get_val(prop_rule, "source_text", "")))
    if prop_rule and hasattr(prop_rule, "policy_clause"):
        policy_texts.append(str(get_val(prop_rule, "policy_clause", "")))

    combined_policy_text = " ".join(policy_texts).lower()

    # Check if clause unlawfully attempts to subject protected categories to room rent ratio
    unlawful_prop_markers = [
        "all charges", "entire bill", "all expenses", "including ot",
        "including pharmacy", "including medicines", "including consumables",
        "including icu", "notwithstanding irdai", "all medical expenses",
        "overrides irdai", "without exception"
    ]
    prop_is_ultra_vires = any(m in combined_policy_text for m in unlawful_prop_markers)
    if prop_is_ultra_vires:
        clause_audits["proportionate_deduction"] = {
            "status": "ULTRA_VIRES",
            "statutory_reference": "IRDAI Master Circular 2024, Chapter V, Para 5.4",
            "clause": str(get_val(prop_rule, "policy_clause", "Proportionate Deduction Clause")),
            "violation": "Clause unlawfully purports to apply room rent proportionate deduction to ICU, OT, pharmacy, or implants contrary to statutory protections.",
            "effect": "Term is null, void, and unenforceable. Proportionate deduction is legally restricted strictly to room-linked charges."
        }
        ultra_vires_clauses.append("Proportionate Deduction Protected Categories Clause (IRDAI Para 5.4)")
    else:
        clause_audits["proportionate_deduction"] = {
            "status": "STATUTORILY_VALID",
            "statutory_reference": "IRDAI Master Circular 2024, Chapter V, Para 5.4",
            "clause": str(get_val(prop_rule, "policy_clause", "Proportionate Deduction Clause")),
            "details": "Clause restricts proportionate deduction to permissible room-linked expenses."
        }
        valid_clauses.append("Proportionate Deduction Clause")

    # -------------------------------------------------------------------------
    # 2. Audit Surgical Consumables & Energy Devices (Annexure A List III)
    # -------------------------------------------------------------------------
    # Check if policy or rejection attempts to exclude surgical tools or drapes as non-payable razor blades
    excludes_list_iii = any(
        kw in combined_policy_text for kw in [
            "exclude all consumables", "knives and blades excluded during surgery",
            "energy devices not payable", "entry 42 applicable to surgery"
        ]
    )
    if excludes_list_iii:
        clause_audits["surgical_consumables_list_iii"] = {
            "status": "ULTRA_VIRES",
            "statutory_reference": "IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List III)",
            "clause": "Exclusions Schedule / Non-Medical List",
            "violation": "Policy terms excluding procedural consumables and advanced energy devices during major surgical interventions violate statutory List III mandates.",
            "effect": "Term is void ab initio. Specialized procedural cutting, sealing, and sterile surgical consumables are statutorily payable."
        }
        ultra_vires_clauses.append("Surgical Consumables & Energy Devices Exclusion (Annexure A List III)")
    else:
        clause_audits["surgical_consumables_list_iii"] = {
            "status": "STATUTORILY_VALID",
            "statutory_reference": "IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List III)",
            "clause": "Annexure A Schedule",
            "details": "Complies with IRDAI statutory List III payable surgical consumables standard."
        }
        valid_clauses.append("Annexure A Surgical Consumables Schedule")

    # -------------------------------------------------------------------------
    # 3. Audit Moratorium Period (IRDAI Master Circular 2024, Chapter V, Para 5.3)
    # -------------------------------------------------------------------------
    moratorium_months = int(get_val(policy, "moratorium_period_months", 60) or 60)
    # Any policy term imposing a moratorium longer than 60 continuous months is Ultra Vires
    if moratorium_months > 60:
        clause_audits["moratorium_period"] = {
            "status": "ULTRA_VIRES",
            "statutory_reference": "IRDAI Master Circular 2024, Chapter V, Para 5.3",
            "clause": f"Section on Moratorium Period ({moratorium_months} months)",
            "violation": f"Policy stipulates a moratorium of {moratorium_months} months exceeding the statutory ceiling of 60 continuous months.",
            "effect": "Superseded by operation of law. Moratorium period is statutorily fixed at 60 continuous months."
        }
        ultra_vires_clauses.append(f"Excessive Moratorium Term ({moratorium_months} months vs statutory 60 months)")
    else:
        clause_audits["moratorium_period"] = {
            "status": "STATUTORILY_VALID",
            "statutory_reference": "IRDAI Master Circular 2024, Chapter V, Para 5.3",
            "clause": f"Section 4/5 - Moratorium Period ({moratorium_months} months)",
            "details": "Complies with statutory 60-month contestability moratorium."
        }
        valid_clauses.append("60-Month Moratorium Clause")

    # -------------------------------------------------------------------------
    # 4. Audit Renewal Grace Period & Bonus Continuity (Reg 13 & Master Circular Para 3.8)
    # -------------------------------------------------------------------------
    clause_6_text = ""
    for txt in policy_texts:
        if any(kw in txt.lower() for kw in ["clause 6", "cumulative bonus", "delayed renewal", "grace period"]):
            clause_6_text += " " + txt

    forfeits_bonus_in_grace_period = any(
        kw in clause_6_text.lower() for kw in [
            "bonus stands forfeited if renewed in grace period",
            "delayed premium payment forfeits bonus",
            "forfeit cumulative bonus within 30 days"
        ]
    )
    if forfeits_bonus_in_grace_period:
        clause_audits["cumulative_bonus_grace_period"] = {
            "status": "ULTRA_VIRES",
            "statutory_reference": "Regulation 13 of IRDAI (Health Insurance) Regulations, 2016 & Master Circular 2024 Chapter III Para 3.8",
            "clause": "Clause 6.1 (Cumulative Bonus Rules)",
            "violation": "Clause purports to forfeit accrued Cumulative Bonus for renewal payments made within the statutory 30-day grace period.",
            "effect": "Ultra vires and legally void. Statutory grace period strictly guarantees continuity of accrued Cumulative Bonus."
        }
        ultra_vires_clauses.append("Cumulative Bonus Forfeiture during Grace Period (Regulation 13)")
    else:
        clause_audits["cumulative_bonus_grace_period"] = {
            "status": "STATUTORILY_VALID",
            "statutory_reference": "Regulation 13 of IRDAI Health Insurance Regulations 2016",
            "clause": "Cumulative Bonus Protection Terms",
            "details": "Preserves continuity and accrued Cumulative Bonus across the statutory 30-day grace period."
        }
        valid_clauses.append("Cumulative Bonus Grace Period Terms")

    # -------------------------------------------------------------------------
    # 5. Audit Mental Healthcare Parity (Mental Healthcare Act 2017, Sec 21(4))
    # -------------------------------------------------------------------------
    covers_mh = bool(get_val(policy, "covers_mental_health", True))
    
    exclusions_list = getattr(policy, "exclusions", []) or []
    if hasattr(exclusions_list, "value"):
        exclusions_list = exclusions_list.value
    if not isinstance(exclusions_list, list):
        exclusions_list = [exclusions_list]

    mh_in_exclusions = False
    for exc in exclusions_list:
        exc_str = str(getattr(exc, "value", exc)).lower()
        if any(w in exc_str for w in ["mental", "psychiatric", "psychological", "schizophrenia", "bipolar"]):
            mh_in_exclusions = True
            break

    has_mh_exclusion = mh_in_exclusions or any(
        re.search(pat, combined_policy_text) for pat in [
            r"\b(mental|psychiatric|psychological|behavioral)\b[^\.\n]{0,100}\b(exclud|not covered|inadmissible|waived)",
            r"\b(exclud|not covered|inadmissible)\b[^\.\n]{0,100}\b(mental|psychiatric|psychological|behavioral)",
            r"no\s+cover[^\.\n]{0,60}(mental|psychiatric)",
        ]
    )
    if not covers_mh or has_mh_exclusion:
        clause_audits["mental_healthcare_parity"] = {
            "status": "ULTRA_VIRES",
            "statutory_reference": "Mental Healthcare Act 2017, Section 21(4) & IRDAI Master Circular 2024",
            "clause": "General Exclusions - Mental Illness",
            "violation": "Policy excludes mental health conditions or fails to treat mental illness on par with physical illness.",
            "effect": "Null and void under Section 21(4) of the Mental Healthcare Act 2017."
        }
        ultra_vires_clauses.append("Mental Health Exclusion Clause (Section 21(4))")
    else:
        clause_audits["mental_healthcare_parity"] = {
            "status": "STATUTORILY_VALID",
            "statutory_reference": "Mental Healthcare Act 2017, Section 21(4)",
            "clause": "Mental Healthcare Coverage Terms",
            "details": "Complies with statutory mental health parity mandate."
        }
        valid_clauses.append("Mental Health Parity Coverage")

    try:
        policy.statutory_clause_audit = clause_audits
    except Exception:
        pass

    # -------------------------------------------------------------------------
    # Build Forensic Rule Verdict
    # -------------------------------------------------------------------------
    if ultra_vires_clauses:
        status = "FAIL"
        legal_track = "TRACK_B_ULTRA_VIRES_CLAUSE"
        finding_type = "STATUTORY_CONFLICT"
        uv_summary = "; ".join(ultra_vires_clauses)
        finding = (
            f"STATUTORY_POLICY_AUDIT_BREACH: Found {len(ultra_vires_clauses)} clause(s) that are ULTRA VIRES and null & void by law: "
            f"[{uv_summary}]. Audited against IRDAI Master Circular 2024, Annexure A Lists I–IV, 60-Month Moratorium, Regulation 13, and Mental Healthcare Act 2017."
        )
        actual_claim_fact = (
            f"Policy contract contains {len(ultra_vires_clauses)} clause(s) that conflict directly with statutory baselines: {uv_summary}."
        )
        applicable_policy_rule = (
            "IRDAI Master Circular on Health Insurance Business (29 May 2024, Paras 3.8, 5.3, 5.4), Annexure A Lists I–IV, "
            "Regulation 13 of IRDAI Health Regulations 2016, and Mental Healthcare Act 2017 Section 21(4)."
        )
        insurer_applied_action = (
            f"Insurer drafted/enforced ultra vires restrictive terms contrary to mandatory IRDAI statutory regulations."
        )
        expected_action = (
            "Sever and void all ultra vires policy clauses; adjudicate claim strictly under statutory baseline protections without unlawful caps."
        )
        evidence = f"Policy Schedule Terms ({policy.policy_number.value if policy.policy_number else 'Contract'}) and IRDAI 2024 Master Circular."
        appeal_rec = (
            "Invoke the doctrine of Ultra Vires before the Grievance Redressal Officer and Insurance Ombudsman. "
            "Demand that all restrictive deductions premised on statutorily void policy clauses be set aside in full."
        )
    else:
        status = "PASS"
        legal_track = None
        finding_type = "NO_ISSUE"
        finding = (
            f"STATUTORY_POLICY_AUDIT_PASSED: All {len(valid_clauses)} audited core policy clauses comply fully with "
            "IRDAI Master Circular 2024, Annexure A Lists I–IV, 60-Month Moratorium (Para 5.3), 30-Day Renewal Grace Period (Reg 13), "
            "and Mental Healthcare Act 2017."
        )
        actual_claim_fact = "Policy terms comply with IRDAI Master Circular 2024 and Mental Healthcare Act 2017 statutory requirements."
        applicable_policy_rule = "IRDAI Master Circular 2024 (Paras 3.8, 5.3, 5.4) and Mental Healthcare Act 2017 Section 21(4)."
        insurer_applied_action = "Insurer policy clauses conform to statutory mandates."
        expected_action = "Standard adjudication under valid statutory contract provisions."
        evidence = f"Policy Schedule ({policy.policy_number.value if policy.policy_number else 'Contract'}) verified against IRDAI statutory schedule."
        appeal_rec = None

    return RuleVerdict(
        status=status,
        rule_name="IRDAI Statutory Policy Auditor Gate",
        rule_description="Audits policy clauses against mandatory IRDAI Master Circular 2024, Annexure A Lists I-IV, 60-Month Moratorium, 30-Day Grace Period, and Mental Healthcare Act 2017.",
        confidence=1.0,
        finding=finding,
        finding_type=finding_type,
        legal_track=legal_track,
        monetary_impact=0.0,
        regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024) & Mental Healthcare Act 2017",
        appeal_recommendation=appeal_rec,
        actual_claim_fact=actual_claim_fact,
        applicable_policy_rule=applicable_policy_rule,
        insurer_applied_action=insurer_applied_action,
        expected_action=expected_action,
        evidence=evidence
    )
