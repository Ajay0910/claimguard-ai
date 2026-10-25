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
        from ..engine.calculator import FinancialMath as fmath

        policy_room_limit = get_val(policy, 'room_rent_limit_per_day', None)
        policy_room_limit_f = fmath.extract(policy_room_limit) if policy_room_limit is not None else 0.0
        if policy_room_limit is None or policy_room_limit_f <= 0.0:
            # Check if rejection letter applied an unauthorized proportionate room rent deduction anyway
            rejection_reasons = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
            unauthorized_deduction = 0.0
            unauthorized_details = []
            for r in rejection_reasons:
                cat = str(get_val(r, 'category', '')).upper()
                desc = str(get_val(r, 'description', ''))
                details = str(get_val(r, 'details', ''))
                clause = str(get_val(r, 'clause_cited', ''))
                combined_r = (desc + " " + details + " " + cat + " " + clause).lower()
                if (
                    cat == "PROPORTIONATE_DEDUCTION"
                    or any(kw in combined_r for kw in [
                        "proportionate", "room ratio", "room rent deduction",
                        "benchmark twin", "benchmark empanelment", "empanelment guidelines",
                        "room rent surcharge", "proportionate room"
                    ])
                ):
                    amt = fmath.extract(get_val(r, 'amount', 0.0))
                    if amt <= 0.0:
                        import re
                        m = re.search(r"(?:Disallowed|Deducted|Rs\.?|₹)\s*[:\-]?\s*Rs\.?\s*([\d,]+(?:\.\d{2})?)", combined_r, re.IGNORECASE)
                        if m:
                            try:
                                amt = float(m.group(1).replace(",", ""))
                            except ValueError:
                                pass
                    if amt > 0.0:
                        unauthorized_deduction += amt
                        unauthorized_details.append(desc or details or cat)

            if unauthorized_deduction > 0.0:
                hosp_name = get_val(bill, 'hospital_name') or "Hospital"
                pol_num = get_val(policy, 'policy_number') or "Policy Schedule"
                claim_num = get_val(rejection, 'claim_number') or "Claim"
                insurer_name = get_val(policy, 'insurer_name') or get_val(rejection, 'insurer_name') or "Insurer"
                tpa_name = get_val(rejection, 'tpa_name') or insurer_name
                room_entitled = get_val(policy, 'room_category_entitled', 'Single Private Room') or 'Single Private Room'
                if hasattr(room_entitled, 'value'):
                    room_entitled = room_entitled.value
                room_entitled_str = str(room_entitled).replace('_', ' ').title()

                finding = (
                    f"STATUTORY_VIOLATION (Unauthorized Proportionate Deduction on Uncapped Policy): "
                    f"Policy schedule ({pol_num}) grants uncapped room entitlement ({room_entitled_str} with no room rent cap), "
                    f"but {tpa_name} unlawfully applied a proportionate room rent deduction of Rs. {unauthorized_deduction:,.2f} "
                    f"citing benchmark empanelment rates or tariff capping. Under IRDAI Standardization Guidelines & GIPSA PPN Rules, "
                    f"uncapped rooms strictly prohibit proportionate reduction. Insurers and TPAs cannot enforce synthetic room caps "
                    f"where the policy contract provides uncapped room eligibility."
                )
                actual_claim_fact = (
                    f"Patient availed room accommodation under uncapped policy entitlement ({room_entitled_str}). "
                    f"{tpa_name} executed an unauthorized proportionate room rent deduction of Rs. {unauthorized_deduction:,.2f}."
                )
                applicable_policy_rule = (
                    "IRDAI Standardization Guidelines & GIPSA PPN Rules (uncapped rooms strictly prohibit proportionate reduction): "
                    "When policy schedule provides uncapped room entitlement or no room rent capping, TPAs are legally prohibited "
                    "from applying pro-rata proportionate deductions or benchmark empanelment rates."
                )
                insurer_applied_action = (
                    f"{tpa_name} unlawfully executed proportionate room rent deduction of Rs. {unauthorized_deduction:,.2f} "
                    f"citing benchmark empanelment rates on an uncapped room policy."
                )
                expected_action = (
                    f"Restore Rs. {unauthorized_deduction:,.2f} in full to the claimant as proportionate reduction is strictly prohibited on uncapped policies."
                )
                evidence_str = (
                    f"{insurer_name} Policy Schedule ({pol_num}) Room Entitlement ({room_entitled_str}) vs "
                    f"{tpa_name} Settlement Advice ({claim_num}) Disallowance."
                )
                evidence_entry = None
                if state is not None and getattr(state, 'ledger', None) is not None:
                    evidence_entry = state.ledger.record_calculation(
                        rule_id="Proportionate Deduction Rule",
                        formula=f"Unauthorized proportionate deduction on uncapped room entitlement = {unauthorized_deduction}",
                        calculation_inputs={"policy_room_limit": 0.0, "unauthorized_deduction": unauthorized_deduction},
                        final_output=unauthorized_deduction,
                        confidence=1.0
                    )
                return RuleVerdict(
                    status="FAIL",
                    rule_name="Proportionate Deduction Rule",
                    rule_description="Validates if proportionate deduction was correctly applied.",
                    confidence=1.0,
                    finding=finding,
                    finding_type="REGULATORY_CONFLICT",
                    legal_track="TRACK_B_STATUTORY_BREACH",
                    insurer_calculation=unauthorized_deduction,
                    correct_calculation=0.0,
                    expected_admissible_amount=unauthorized_deduction,
                    monetary_impact=unauthorized_deduction,
                    difference=unauthorized_deduction,
                    regulatory_citation="IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4) & IRDAI Standardization Guidelines (Uncapped Room Entitlement Bars Proportionate Deduction)",
                    appeal_recommendation=(
                        f"Demand immediate refund of Rs. {unauthorized_deduction:,.2f}. Proportionate deduction cannot be applied "
                        "when the policy schedule grants uncapped room entitlement per IRDAI Master Circular 2024 and Standardization Guidelines."
                    ),
                    actual_claim_fact=actual_claim_fact,
                    applicable_policy_rule=applicable_policy_rule,
                    insurer_applied_action=insurer_applied_action,
                    expected_action=expected_action,
                    evidence=evidence_str,
                    evidence_entries=[evidence_entry] if evidence_entry else []
                )

            return RuleVerdict(
                status="NOT_APPLICABLE",
                rule_name="Proportionate Deduction Rule",
                rule_description="Validates if proportionate deduction was correctly applied.",
                confidence=1.0,
                finding="No room rent limit in policy. Proportionate deduction not applicable.",
                legal_track="NOT_APPLICABLE"
            )
        
        actual_room_rate = get_val(bill, 'room_charges_per_day', None)
        length_of_stay = get_val(bill, 'length_of_stay', None)

        if actual_room_rate is None or length_of_stay is None or float(length_of_stay or 0) <= 0:
            for itm in get_val(bill, 'line_items', []):
                itm_cat = str(get_val(itm, 'category', '')).upper()
                itm_desc = str(get_val(itm, 'description', '')).upper()
                if itm_cat == 'ROOM' or 'ROOM' in itm_desc or 'BED' in itm_desc:
                    rate = get_val(itm, 'unit_rate', 0.0)
                    qty = get_val(itm, 'quantity', 0.0)
                    if (actual_room_rate is None or float(actual_room_rate or 0) <= 0) and rate and float(rate) > 0:
                        actual_room_rate = rate
                    if (length_of_stay is None or float(length_of_stay or 0) <= 0) and qty and float(qty) > 0:
                        length_of_stay = qty
                    if actual_room_rate and length_of_stay and float(length_of_stay) > 0:
                        break
        
        if actual_room_rate is None or length_of_stay is None or float(length_of_stay or 0) <= 0:
             return RuleVerdict(
                status="SKIPPED",
                rule_name="Proportionate Deduction Rule",
                rule_description="Validates if proportionate deduction was correctly applied.",
                confidence=1.0,
                finding="Missing room rate or length of stay in hospital bill.",
                legal_track="NOT_APPLICABLE"
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
        room_only_codes = []
        misc_codes = []
        misc_total = 0.0
        
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
                
            if cat == 'ROOM':
                room_only_codes.append(str(code))
                
            if cat == 'MISCELLANEOUS':
                misc_codes.append(str(code))
                misc_total += fmath.extract(get_val(item, 'amount', 0.0))
                
        if state and total_room_excess > 0 and room_only_codes:
            state.apply_deduction(
                rule_id="Proportionate Deduction Rule",
                target_item_codes=room_only_codes,
                deduction_amount=total_room_excess,
                formula=f"Room Excess: (Actual - Limit) * Days",
                policy_clause="Room Rent Limit Clause"
            )
            
        if state and misc_total > 0 and misc_codes:
            state.apply_deduction(
                rule_id="Proportionate Deduction Rule",
                target_item_codes=misc_codes,
                deduction_amount=misc_total,
                formula="Sum of MISCELLANEOUS items",
                policy_clause="Non-Medical Expenses Clause"
            )
                
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
        
        # Clause inspection for Track B (Ultra Vires clause attempting to override IRDAI protected heads)
        prop_rule = get_val(policy, 'proportionate_deduction_rule', None)
        clause_texts = []
        if prop_rule:
            for attr in ['policy_clause', 'source_text', 'applicability_conditions', 'description']:
                val = get_val(prop_rule, attr, '')
                if val: clause_texts.append(str(val))
        for attr in ['deduction_order_clause', 'exclusions']:
            val = get_val(policy, attr, '')
            if isinstance(val, list): clause_texts.extend(str(x) for x in val)
            elif val: clause_texts.append(str(val))
        combined_clause_text = " ".join(clause_texts).lower()

        is_ultra_vires_clause = any(
            phrase in combined_clause_text for phrase in [
                "all charges", "entire bill", "all expenses", "including ot", 
                "including pharmacy", "including medicines", "including consumables", 
                "including icu", "notwithstanding irdai", "all medical expenses",
                "overrides irdai", "ultra vires", "without exception"
            ]
        )

        stat_audit = getattr(policy, 'statutory_clause_audit', {}) or {}
        if stat_audit.get("proportionate_deduction", {}).get("status") == "ULTRA_VIRES":
            is_ultra_vires_clause = True

        is_fail = insurer_deduction > (expected_total_deduction + 100.0)
        
        finding = (f"Actual Rate: Rs. {actual_room_rate_f}/day. Eligible: Rs. {policy_room_limit_f}/day. "
                   f"Room Excess: Rs. {total_room_excess:.2f}. "
                   f"Trigger Check: {trigger_msg} "
                   f"Expected Proportionate Reduction: Rs. {proportionate_reduction:.2f}. "
                   f"Total Legitimate Deduction (including non-medical): Rs. {expected_total_deduction:.2f}. "
                   f"Insurer Deducted: Rs. {insurer_deduction:.2f}. ")
                   
        appeal_rec = None
        if is_fail:
            if is_ultra_vires_clause:
                legal_track = "TRACK_B_ULTRA_VIRES_CLAUSE"
                finding += " [TRACK B: ULTRA VIRES CLAUSE - Policy clause unlawfully attempts to subject statutory protected heads to proportionate deduction contrary to IRDAI Master Circular 2024.]"
                appeal_rec = "Policy clause purporting to apply proportionate deduction to protected heads is ultra vires IRDAI Master Circular May 2024. Demand full restoration."
            else:
                legal_track = "TRACK_A_ARITHMETIC_BREACH"
                finding += " [TRACK A: ARITHMETIC BREACH - Proportionate deduction ratio applied beyond permissible room-linked charges to protected categories.]"
                if is_triggered:
                    appeal_rec = "Proportionate deduction was unlawfully applied to the entire bill instead of only room-linked items (IRDAI Master Circular May 2024)."
                else:
                    appeal_rec = "Recompute proportionate deduction as the eligible room limit was not exceeded."
        else:
            legal_track = "TRACK_C_VALID_DEDUCTION"
            finding += " Insurer calculation is contractually and regulatorily valid. No underpayment."
            appeal_rec = None

        hosp_name = get_val(bill, 'hospital_name') or "Hospital"
        pol_num = get_val(policy, 'policy_number') or "Policy"
        claim_num = get_val(rejection, 'claim_number') or "Claim"
        insurer_name = get_val(policy, 'insurer_name') or get_val(rejection, 'insurer_name') or "Insurer"
        tpa_name = get_val(rejection, 'tpa_name') or insurer_name
        diff_amt = max(0.0, insurer_deduction - expected_total_deduction) if is_fail else 0.0
        room_days = int(float(length_of_stay or 1))

        if is_fail:
            actual_claim_fact = (
                f"Patient was admitted at {hosp_name} for {room_days} day(s) in a room at Rs. {actual_room_rate_f:,.2f}/day "
                f"against an eligible policy room rent limit of Rs. {policy_room_limit_f:,.2f}/day. "
                f"Total bill amount: Rs. {float(get_val(bill, 'total_amount', 0.0)):,.2f}. Insurer deducted Rs. {insurer_deduction:,.2f}."
            )
            applicable_policy_rule = (
                "IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.4): "
                "Proportionate deduction is strictly limited to room-linked charges (nursing and room rent). "
                "ICU, OT infrastructure, medicines/pharmacy, implants, and diagnostics are statutory protected heads immune from proportionate cuts."
            )
            insurer_applied_action = (
                f"{tpa_name} executed proportionate deduction of Rs. {insurer_deduction:,.2f} by applying room rent "
                "pro-rata reductions across non-associated medical categories and protected heads."
            )
            expected_action = (
                f"Limit legitimate deduction strictly to Rs. {expected_total_deduction:,.2f} (room excess Rs. {total_room_excess:,.2f} "
                f"+ room-linked proportionate reduction Rs. {proportionate_reduction:,.2f} + non-medical Rs. {misc_deductions:,.2f}) "
                f"and restore Rs. {diff_amt:,.2f} in full to the claimant."
            )
            evidence_str = (
                f"{hosp_name} Hospital Bill Room Charges (Rs. {actual_room_rate_f:,.2f}/day) vs "
                f"{insurer_name} Policy Schedule ({pol_num}) Room Rent Limit (Rs. {policy_room_limit_f:,.2f}/day) "
                f"and Settlement Advice ({claim_num})."
            )
        else:
            actual_claim_fact = (
                f"Hospital room rate of Rs. {actual_room_rate_f:,.2f}/day evaluated against eligible limit "
                f"of Rs. {policy_room_limit_f:,.2f}/day. Insurer deducted Rs. {insurer_deduction:,.2f}."
            )
            applicable_policy_rule = "IRDAI Master Circular 2024 Para 5.4: Proportionate deduction applied within legitimate contractual limits."
            insurer_applied_action = f"Insurer deducted Rs. {insurer_deduction:,.2f} in accordance with policy terms."
            expected_action = "Maintain standard settlement as deductions are contractually and regulatorily valid."
            evidence_str = f"{hosp_name} Bill and {pol_num} Policy Schedule terms verified."

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
            legal_track=legal_track,
            insurer_calculation=insurer_deduction,
            correct_calculation=expected_total_deduction,
            expected_admissible_amount=expected_total_deduction,
            monetary_impact=insurer_deduction - expected_total_deduction if is_fail else 0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024",
            appeal_recommendation=appeal_rec,
            actual_claim_fact=actual_claim_fact,
            applicable_policy_rule=applicable_policy_rule,
            insurer_applied_action=insurer_applied_action,
            expected_action=expected_action,
            difference=diff_amt,
            evidence=evidence_str,
            evidence_entries=[evidence_entry] if evidence_entry else []
        )

    except Exception as e:
        return RuleVerdict(status="SKIPPED", rule_name="Proportionate Deduction Rule", rule_description="", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")


evaluate_proportionate_deduction = check_proportionate_deduction
