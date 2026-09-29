path = 'app/rules/proportionate_deduction.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_logic = """        # Calculate reductions
        room_linked_items = [item for item in getattr(bill, 'line_items', []) if getattr(item, 'is_room_linked', False)]
        room_linked_sum = sum(getattr(item, 'amount', 0.0) for item in room_linked_items)
        
        if is_triggered:
            # Applies to room-linked items
            deduction_percentage = 1.0 - (policy_room_limit / actual_room_rate)
            proportionate_reduction = room_linked_sum * deduction_percentage
            trigger_msg = f"Ratio {actual_room_rate/policy_room_limit:.2f} strictly exceeds 1.15 threshold. Proportionate reduction applies."
        else:
            proportionate_reduction = 0.0
            trigger_msg = f"Ratio {actual_room_rate/policy_room_limit:.2f} does NOT strictly exceed 1.15 threshold. Proportionate reduction is ZERO."

        # Compare with insurer deduction
        insurer_deduction = getattr(rejection, 'total_deducted', 0.0)
        
        finding = (f"Actual Rate: ₹{actual_room_rate}/day. Eligible: ₹{policy_room_limit}/day. "
                   f"Room Excess: ₹{total_room_excess:.2f}. "
                   f"Trigger Check: {trigger_msg} "
                   f"Expected Proportionate Reduction: ₹{proportionate_reduction:.2f}. ")
                   
        # We will let engine.py handle the final expected admissible math. 
        # But this rule returns whether the insurer unlawfully applied proportionate deduction.
        # It fails if proportionate_reduction is 0 but insurer deducted a massive amount, etc.
        # For simplicity, we just pass the calculated values in `correct_calculation` for engine.py.

        return RuleVerdict(
            status="FAIL" if not is_triggered and insurer_deduction > (total_room_excess + 1000) else "PASS", 
            rule_name="Proportionate Deduction Rule",
            rule_description="Validates if proportionate deduction was correctly applied.",
            confidence=1.0,
            finding=finding,
            insurer_calculation=insurer_deduction,
            correct_calculation=proportionate_reduction,
            monetary_impact=insurer_deduction - (total_room_excess + sum(item.amount for item in getattr(bill, 'line_items', []) if getattr(item, 'category', '') == 'MISCELLANEOUS')), # Total policy-supported deduction from room limits
            regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024",
            appeal_recommendation="Recompute proportionate deduction as the 115% threshold was not strictly exceeded." if not is_triggered else None
        )"""

new_logic = """        # Calculate reductions
        room_linked_items = []
        for item in getattr(bill, 'line_items', []):
            cat = getattr(item, 'category', '').upper()
            is_linked = getattr(item, 'is_room_linked', False)
            if is_linked or cat in ['ROOM', 'NURSING']:
                room_linked_items.append(item)
                
        room_linked_sum = sum(getattr(item, 'amount', 0.0) for item in room_linked_items)
        
        if is_triggered:
            # Applies to room-linked items
            deduction_percentage = 1.0 - (policy_room_limit / actual_room_rate)
            proportionate_reduction = room_linked_sum * deduction_percentage
            trigger_msg = f"Ratio {actual_room_rate/policy_room_limit:.2f} strictly exceeds 1.15 threshold. Proportionate reduction applies."
        else:
            proportionate_reduction = 0.0
            trigger_msg = f"Ratio {actual_room_rate/policy_room_limit:.2f} does NOT strictly exceed 1.15 threshold. Proportionate reduction is ZERO."

        # Compare with insurer deduction
        insurer_deduction = getattr(rejection, 'total_deducted', 0.0)
        
        # Calculate exactly what the total legitimate deductions should be
        misc_deductions = sum(getattr(item, 'amount', 0.0) for item in getattr(bill, 'line_items', []) if getattr(item, 'category', '').upper() == 'MISCELLANEOUS')
        expected_total_deduction = total_room_excess + proportionate_reduction + misc_deductions
        
        # If the insurer deduced substantially more than the legitimate total deduction
        is_fail = insurer_deduction > (expected_total_deduction + 100.0) # Margin of error
        
        finding = (f"Actual Rate: ₹{actual_room_rate}/day. Eligible: ₹{policy_room_limit}/day. "
                   f"Room Excess: ₹{total_room_excess:.2f}. "
                   f"Trigger Check: {trigger_msg} "
                   f"Expected Proportionate Reduction: ₹{proportionate_reduction:.2f}. "
                   f"Total Legitimate Deduction (including non-medical): ₹{expected_total_deduction:.2f}. "
                   f"Insurer Deducted: ₹{insurer_deduction:.2f}. ")
                   
        appeal_rec = None
        if is_fail:
            if is_triggered:
                appeal_rec = "Proportionate deduction was unlawfully applied to the entire bill instead of only room-linked items."
            else:
                appeal_rec = "Recompute proportionate deduction as the 115% threshold was not strictly exceeded."

        return RuleVerdict(
            status="FAIL" if is_fail else "PASS", 
            rule_name="Proportionate Deduction Rule",
            rule_description="Validates if proportionate deduction was correctly applied.",
            confidence=1.0,
            finding=finding,
            insurer_calculation=insurer_deduction,
            correct_calculation=expected_total_deduction,
            monetary_impact=insurer_deduction - expected_total_deduction if is_fail else 0.0,
            regulatory_citation="IRDAI Master Circular on Health Insurance, May 2024",
            appeal_recommendation=appeal_rec
        )"""

# using a simpler replace strategy to avoid encoding issues with the INR symbol in python string replace
content = re.sub(r'# Calculate reductions.*return RuleVerdict\([^\)]*\)', new_logic, content, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
