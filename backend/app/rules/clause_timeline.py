from . import get_val
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Clause Timeline Rule",
    description="Validates if the rejection violates the moratorium period for pre-existing conditions based on continuous coverage.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024, Para 5.3 – Moratorium Period of 60 months"
)
def check_clause_timeline(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    try:
        reasons_list = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
        
        # Check if rejection is related to non-disclosure or pre-existing
        is_non_disclosure = any(
            get_val(reason, 'category', '') == "PRE_EXISTING" or 
            "non-disclosure" in str(get_val(reason, 'description', '')).lower() or
            "pre-existing" in str(get_val(reason, 'description', '')).lower()
            for reason in reasons_list
        )
        
        if not is_non_disclosure:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Rejection does not cite non-disclosure or pre-existing conditions."
            )
            
        policy_start = get_val(policy, 'inception_date', None) or get_val(policy, 'original_inception_date', None) or get_val(policy, 'policy_start_date', None)
        claim_date = get_val(rejection, 'claim_date', None)
        claim_amount = get_val(rejection, 'total_claimed', 0.0)
        
        if not policy_start or not claim_date:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Missing policy inception or claim date for moratorium evaluation."
            )
            
        from dateutil.parser import parse
        def parse_date(d_str):
            if not d_str or str(d_str).strip().upper() == "N/A": return None
            try:
                return datetime.fromisoformat(str(d_str)[:10]).date()
            except ValueError:
                try:
                    return parse(str(d_str)).date()
                except Exception:
                    return None

        policy_start = parse_date(policy_start)
        claim_date_obj = parse_date(claim_date) if isinstance(claim_date, str) else claim_date
        
        if not policy_start or not claim_date_obj:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="SKIPPED",
                rule_name="Clause Timeline Rule",
                confidence=1.0,
                finding="Invalid or missing policy inception or claim date for moratorium evaluation."
            )
            
        portability_months = get_val(policy, 'portability_credits_months', 0) or 0
        migration_months = get_val(policy, 'migration_credits_months', 0) or 0
        moratorium_months = get_val(policy, 'moratorium_period_months', 60) or 60
        
        months_needed_on_current = moratorium_months - portability_months - migration_months
        moratorium_completion_date = policy_start + relativedelta(months=months_needed_on_current)
        
        if hasattr(policy, "evaluate_moratorium"):
            moratorium_status = policy.evaluate_moratorium(str(claim_date_obj), claim_amount)
            is_protected = moratorium_status.get("is_protected", False) and claim_date_obj > moratorium_completion_date
        else:
            elapsed_rel = relativedelta(claim_date_obj, policy_start)
            total_months_active = elapsed_rel.years * 12 + elapsed_rel.months + (elapsed_rel.days / 30.44) + (portability_months + migration_months)
            is_protected = total_months_active >= moratorium_months and claim_date_obj > moratorium_completion_date
            
        if is_protected:
            finding_text = (
                f"MORATORIUM_RULE_CONFLICT: Rejection cites non-disclosure/pre-existing after the {moratorium_months}-month moratorium.\n"
                f"Continuous coverage required: {moratorium_months} months.\n"
                f"Ported credits: {portability_months} months.\n"
                f"Coverage start: {policy_start}\n"
                f"Moratorium completion: {moratorium_completion_date}\n"
                f"Claim date: {claim_date_obj}\n"
                "Inconsistency: Claim occurred after moratorium completion. Unless established fraud applies, the claim cannot be contested on these grounds."
            )
            from ..engine.calculator import FinancialMath as fmath
            ped_disallowance = 0.0
            ped_reasons = [
                r for r in reasons_list
                if str(get_val(r, 'category', '')).upper() == "PRE_EXISTING"
                or any(kw in str(get_val(r, 'description', '')).lower() for kw in ["pre-existing", "non-disclosure", "moratorium"])
                or any(kw in str(get_val(r, 'details', '')).lower() for kw in ["pre-existing", "non-disclosure", "moratorium"])
            ]
            for pr in ped_reasons:
                pr_amt = fmath.extract(get_val(pr, 'amount', 0.0))
                if pr_amt <= 0.0:
                    import re
                    m_pr = re.search(r"(?:Disallowed|Deducted|Rs\.?|₹)\s*[:\-]?\s*Rs\.?\s*([\d,]+(?:\.\d{2})?)", str(get_val(pr, 'description', '')) + " " + str(get_val(pr, 'details', '')), re.IGNORECASE)
                    if m_pr:
                        try:
                            pr_amt = float(m_pr.group(1).replace(",", ""))
                        except ValueError:
                            pass
                if pr_amt > 0.0:
                    ped_disallowance += pr_amt

            total_approved = fmath.extract(get_val(rejection, 'total_approved', None) or get_val(rejection, 'approved_amount', 0.0))
            if ped_disallowance > 0.0:
                diff_amount = ped_disallowance
            elif total_approved == 0.0 and claim_amount > 0.0:
                diff_amount = claim_amount
            else:
                diff_amount = claim_amount if isinstance(claim_amount, (int, float)) and claim_amount > 0 else None

            from ..schemas.evidence_ledger import EvidenceLedgerEntry
            ev_entry = None
            if state is not None and getattr(state, "ledger", None) is not None:
                ev_entry = state.ledger.record_calculation(
                    rule_id="Clause Timeline Rule",
                    formula=f"claim_date ({claim_date_obj}) >= moratorium_completion ({moratorium_completion_date})",
                    calculation_inputs={"coverage_start": str(policy_start), "claim_date": str(claim_date_obj), "moratorium_months": moratorium_months, "disputed_amount": diff_amount},
                    final_output=float(diff_amount or 0.0),
                    confidence=1.0
                )
            else:
                ev_entry = EvidenceLedgerEntry(
                    claim_id=str(get_val(bill, "bill_id", "CLAIM")),
                    document_id="CALCULATED",
                    document_hash="SYSTEM_DETERMINISTIC",
                    rule_id="Clause Timeline Rule",
                    formula=f"claim_date ({claim_date_obj}) >= moratorium_completion ({moratorium_completion_date})",
                    calculation_inputs={"coverage_start": str(policy_start), "claim_date": str(claim_date_obj), "moratorium_months": moratorium_months, "disputed_amount": diff_amount},
                    final_output=float(diff_amount or 0.0),
                    calculation_output=float(diff_amount or 0.0),
                    value=float(diff_amount or 0.0),
                    normalized_value=float(diff_amount or 0.0),
                    extracted_value=float(diff_amount or 0.0),
                    source_text=f"Moratorium active: {policy_start} to {moratorium_completion_date}",
                    confidence=1.0
                )
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="FAIL",
                rule_name="Clause Timeline Rule",
                rule_description="Validates continuous coverage moratorium rules.",
                confidence=1.0,
                finding=finding_text,
                legal_track="TRACK_B_STATUTORY_BREACH",
                monetary_impact=diff_amount,
                regulatory_citation="IRDAI Master Circular on Health Insurance, 29 May 2024 (Chapter V, Para 5.3) & Regulation 17 of IRDAI (Health Insurance) Regulations 2016 (Portability Continuity)",
                appeal_recommendation="Appeal citing IRDAI Master Circular 2024 & Regulation 17: 60-month continuous coverage moratorium with portability credit prohibits contestation on non-disclosure.",
                actual_claim_fact=f"Claim incurred on {claim_date_obj} after continuous coverage active since policy inception on {policy_start}.",
                applicable_policy_rule=f"IRDAI Master Circular (29 May 2024, Chapter V, Para 5.3): All pre-existing disease exclusions expire irrevocably after 60 continuous months of coverage (completed on {moratorium_completion_date}).",
                insurer_applied_action="Insurer/TPA repudiated coverage citing pre-existing condition exclusions after completion of statutory moratorium period.",
                expected_action="Admit and process claim under full statutory moratorium protection without contestation.",
                difference=diff_amount,
                evidence=f"Policy Schedule Inception Date ({policy_start}), Moratorium Completion Date ({moratorium_completion_date}), and Claim Date ({claim_date_obj}).",
                evidence_entries=[ev_entry] if ev_entry else []
            )
        else:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="PASS",
                rule_name="Clause Timeline Rule",
                rule_description="Validates continuous coverage moratorium rules.",
                confidence=1.0,
                finding=f"Claim date ({claim_date_obj}) is before moratorium completion ({moratorium_completion_date}). Rejection is temporally valid."
            )
        
    except Exception as e:
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Clause Timeline Rule", finding=f"Error evaluating rule: {str(e)}")
