from . import get_val
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule

@register_rule(
    name="Proportionate Deduction Rule",
    description="Validates if proportionate deduction was correctly applied.",
    tier=1,
    regulatory_citation="Policy Schedule - Proportionate Deduction Clause (per IRDAI Master Circular restrictions)",
    modifies_categories=["ROOM", "NURSING", "CONSULTATION", "LAB", "OT"]
)
def check_proportionate_deduction(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    try:
        policy_room_limit = get_val(policy, 'room_rent_limit_per_day', None)
        if policy_room_limit is None:
            return RuleVerdict(
                status="NOT_APPLICABLE",
                rule_name="Proportionate Deduction Rule",
                rule_description="Validates if proportionate deduction was correctly applied.",
                confidence=1.0,
                finding="No room rent limit in policy. Proportionate deduction not applicable."
            )
        
        actual_room_rate = get_val(bill, 'room_charges_per_day', None)
        length_of_stay = get_val(bill, 'length_of_stay', None)
        
        if actual_room_rate is None or length_of_stay is None or length_of_stay <= 0:
             return RuleVerdict(
                status="SKIPPED",
                rule_name="Proportionate Deduction Rule",
                rule_description="Validates if proportionate deduction was correctly applied.",
                confidence=1.0,
                finding="Missing room rate or length of stay in hospital bill."
            )

        from ..engine.calculator import FinancialMath as fmath

        actual_room_rate_f = fmath.extract(actual_room_rate)
        policy_room_limit_f = fmath.extract(policy_room_limit)
        
        # 1. Calculate Room Excess
        room_excess_per_day = max(0.0, actual_room_rate_f - policy_room_limit_f)
        total_room_excess = room_excess_per_day * fmath.extract(length_of_stay)
        
        # 2. Check Proportionate Deduction Trigger
        trigger_threshold = policy_room_limit_f
        threshold_pct = 100.0
        
        prop_rule = get_val(policy, 'proportionate_deduction_rule', None)
        if prop_rule:
            threshold_val = float(get_val(prop_rule, 'threshold_value', 1.0))
            # If the value is like 1.15, treat it as ratio. If it's 115, treat as percentage.
            if threshold_val < 5.0:
                threshold_pct = threshold_val * 100.0
            else:
                threshold_pct = threshold_val
            trigger_threshold = policy_room_limit_f * (threshold_pct / 100.0)
            
        is_triggered = actual_room_rate_f > trigger_threshold
        
        room_linked_items = []
        room_linked_codes = []
        
        for i, item in enumerate(get_val(bill, 'line_items', [])):
            cat = get_val(item, 'category', '').upper()
            is_linked = get_val(item, 'is_room_linked', False)
            
            code = get_val(item, 'item_code', None)
            if code is None: code = f"ITEM_{i}"
            if hasattr(code, 'value'): code = code.value
            
            if cat in ['OT', 'CATH_LAB', 'CATH LAB', 'ICU', 'ICC', 'PHARMACY', 'CONSUMABLES']:
                is_linked = False
                
            if is_linked or cat in ['NURSING', 'CONSULTATION']:
                room_linked_items.append(item)
                room_linked_codes.append(str(code))
                
        if state:
            room_linked_sum = sum(state.get_balance(code) for code in room_linked_codes)
        else:
            room_linked_sum = sum(fmath.extract(get_val(item, 'amount', 0.0)) for item in room_linked_items)
        
        proportionate_reduction = 0.0
        trigger_msg = ""
        if is_triggered:
            deduction_percentage = 1.0 - (policy_room_limit_f / actual_room_rate_f)
            proportionate_reduction = room_linked_sum * deduction_percentage
            trigger_msg = f"Ratio {actual_room_rate_f/policy_room_limit_f:.2f} exceeds {threshold_pct/100.0:.2f} threshold. Proportionate reduction applies."
            
            if state and proportionate_reduction > 0:
                state.apply_deduction(
                    rule_id="Proportionate Deduction Rule",
                    target_item_codes=room_linked_codes,
                    deduction_amount=proportionate_reduction,
                    formula=f"({room_linked_sum} * {deduction_percentage})",
                    policy_clause="Proportionate Deduction Clause"
                )
        else:
            trigger_msg = f"Ratio {actual_room_rate_f/policy_room_limit_f:.2f} does NOT exceed {threshold_pct/100.0:.2f}. Proportionate reduction is ZERO."

        insurer_deduction = fmath.extract(get_val(rejection, 'total_deducted', 0.0))
        misc_deductions = sum(fmath.extract(get_val(item, 'amount', 0.0)) for item in get_val(bill, 'line_items', []) if get_val(item, 'category', '').upper() == 'MISCELLANEOUS')
        expected_total_deduction = total_room_excess + proportionate_reduction + misc_deductions
        
        is_fail = insurer_deduction > (expected_total_deduction + 100.0)
        
        finding = (f"Actual Rate: Rs. {actual_room_rate_f}/day. Eligible: Rs. {policy_room_limit_f}/day. "
                   f"Room Excess: Rs. {total_room_excess:.2f}. "
                   f"Trigger Check: {trigger_msg} "
                   f"Expected Proportionate Reduction: Rs. {proportionate_reduction:.2f}. "
                   f"Total Legitimate Deduction (including non-medical): Rs. {expected_total_deduction:.2f}. "
                   f"Insurer Deducted: Rs. {insurer_deduction:.2f}. ")
                   
        appeal_rec = None
        if is_fail:
            if is_triggered:
                appeal_rec = "Proportionate deduction was unlawfully applied to the entire bill instead of only room-linked items (IRDAI Master Circular May 2024)."
            else:
                appeal_rec = "Recompute proportionate deduction as the eligible room limit was not exceeded."

        evidence_entry = None
        if state is not None and getattr(state, 'ledger', None) is not None:
            evidence_entry = state.ledger.record_calculation(
                rule_id="Proportionate Deduction Rule",
                formula=f"expected_total_deduction ({expected_total_deduction}) vs insurer_deduction ({insurer_deduction})",
                calculation_inputs={"actual_room_rate": actual_room_rate_f, "policy_room_limit": policy_room_limit_f, "room_linked_sum": room_linked_sum},
                final_output=expected_total_deduction,
                confidence=1.0
            )

        return RuleVerdict(
            status="FAIL" if is_fail else "PASS", 
            rule_name="Proportionate Deduction Rule",
            rule_description="Validates if proportionate deduction was correctly applied.",
            confidence=1.0,
            finding=finding,
            insurer_calculation=insurer_deduction,
            correct_calculation=expected_total_deduction,
            expected_admissible_amount=expected_total_deduction,
            monetary_impact=insurer_deduction - expected_total_deduction if is_fail else 0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024",
            appeal_recommendation=appeal_rec,
            evidence_entries=[evidence_entry] if evidence_entry else []
        )

    except Exception as e:
        return RuleVerdict(status="SKIPPED", rule_name="Proportionate Deduction Rule", rule_description="", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
