from . import get_val
from datetime import datetime
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Waiting Period Rule",
    description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
    tier=1,
    regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024 — Waiting Period provisions"
)
def check_waiting_period(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
    try:
        reasons_list = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
        wp_reasons = [r for r in reasons_list if get_val(r, 'category', '') == "WAITING_PERIOD"]
        if not wp_reasons:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding="No WAITING_PERIOD reason cited.")
            
        policy_start = get_val(policy, 'inception_date', None) or get_val(policy, 'original_inception_date', None) or get_val(policy, 'policy_start_date', None)
        claim_date = get_val(rejection, 'claim_date', None)
        
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
        claim_date = parse_date(claim_date) if isinstance(claim_date, str) else claim_date
        
        if not policy_start or not claim_date:
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding="Invalid or missing policy inception or claim date.")
            
        delta_days = (claim_date - policy_start).days
        
        wp_required_days = get_val(policy, 'ped_waiting_period_months', 48) * 30.44
        category_name = "PED"
        
        wp_details = f"{get_val(wp_reasons[0], 'details', '') or ''} {get_val(wp_reasons[0], 'description', '') or ''}"
        
        if "initial" in wp_details.lower() or "30 day" in wp_details.lower():
            wp_required_days = get_val(policy, 'initial_waiting_period_days', 30)
            category_name = "INITIAL"
        elif "specific" in wp_details.lower() or "2 year" in wp_details.lower():
            wp_required_days = get_val(policy, 'specific_illness_waiting_period_months', 24) * 30.44
            category_name = "SPECIFIC_DISEASE"
            
        if delta_days > wp_required_days:
            from ..schemas.evidence_ledger import EvidenceLedgerEntry
            prov_inc = getattr(policy, "inception_date", None)
            doc_id = getattr(prov_inc, "source_document_id", "POLICY_INCEPTION") if prov_inc else "POLICY_INCEPTION"
            doc_hash = getattr(prov_inc, "source_hash", "POLICY_HASH") if prov_inc else "POLICY_HASH"
            page_no = int(getattr(prov_inc, "page", 1) or 1) if prov_inc else 1
            src_text = getattr(prov_inc, "source_text", None) or f"Policy Inception Date: {policy_start}"
            
            disallowance_amt = None
            if wp_reasons:
                r_amt = getattr(wp_reasons[0], 'amount', None)
                if r_amt is not None:
                    disallowance_amt = getattr(r_amt, 'value', r_amt) if hasattr(r_amt, 'value') else float(r_amt)

            ev_entry = EvidenceLedgerEntry(
                claim_id=str(get_val(bill, "bill_id", "CLAIM")),
                document_id="CALCULATED",
                document_hash="SYSTEM_DETERMINISTIC",
                page_number=page_no,
                bounding_box=[0.0, 0.0, 1.0, 1.0],
                source_document_type="INSURANCE_POLICY",
                model="DETERMINISTIC_RULES",
                transformations=["CALENDAR_DAYS_ELAPSED"],
                rule_id="WAITING_PERIOD_RULE",
                formula="delta_days > wp_required_days",
                calculation_inputs={"delta_days": delta_days, "wp_required_days": wp_required_days},
                final_output=float(disallowance_amt or delta_days),
                calculation_output=float(disallowance_amt or delta_days),
                value=float(disallowance_amt or delta_days),
                normalized_value=float(disallowance_amt or delta_days),
                extracted_value=float(disallowance_amt or delta_days),
                source_text=src_text,
                confidence=1.0
            )

            actual_fact = f"Claim incurred on {claim_date} ({delta_days} days after policy inception on {policy_start}). Required waiting period was {wp_required_days:.0f} days."
            app_rule = f"IRDAI Master Circular on Health Insurance (May 2024, Waiting Period Provisions): Once the contractual/statutory waiting period ({wp_required_days:.0f} days) has expired, claim repudiation on waiting period grounds is legally invalid."
            ins_action = f"Insurer repudiated claim citing expired {category_name} waiting period."
            exp_action = f"Admit and process claim in full as {category_name} waiting period expired {int(delta_days - wp_required_days)} day(s) before hospitalization."
            ev = f"Policy Inception Date ({policy_start}) and Claim Incurred Date ({claim_date}) demonstrating {delta_days} days continuous coverage."
            return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
                status="FAIL",
                rule_name="Waiting Period Rule",
                rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
                confidence=1.0,
                legal_track="TRACK_B_STATUTORY_BREACH",
                monetary_impact=disallowance_amt,
                difference=disallowance_amt,
                finding=f"The {category_name} waiting period of {wp_required_days:.0f} days has expired. Days elapsed: {delta_days}. The insurer's rejection is incorrect.",
                regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024 — Waiting Period provisions",
                appeal_recommendation=f"The insurer has wrongfully rejected the claim citing a {category_name} waiting period, which has already expired.",
                actual_claim_fact=actual_fact,
                applicable_policy_rule=app_rule,
                insurer_applied_action=ins_action,
                expected_action=exp_action,
                evidence=ev,
                evidence_entries=[ev_entry]
            )
            
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", 
            status="PASS", 
            rule_name="Waiting Period Rule", 
            rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.",
            confidence=1.0,
            finding=f"Rejection is valid, {category_name} waiting period has not expired. Days elapsed: {delta_days}."
        )
        
    except Exception as e:
        return RuleVerdict(finding_type="REGULATORY_CONFLICT", status="SKIPPED", rule_name="Waiting Period Rule", rule_description="Validates if the rejection based on waiting period is actually correct based on policy inception.", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
