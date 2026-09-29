import re

with open('backend/app/rules/clause_timeline.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
'''        if hasattr(policy, "evaluate_moratorium"):
            moratorium_status = policy.evaluate_moratorium(claim_date, claim_amount)
            
            if moratorium_status.get("is_protected", False):
                finding_text = (
                    f"MORATORIUM_RULE_CONFLICT: Rejection cites non-disclosure/pre-existing despite moratorium protection.\\n"
                    f"Details: {moratorium_status.get('reason')}\\n"
                    f"Claim date: {claim_date_obj}\\n"
                    "Inconsistency: Claim is protected. Unless established fraud applies, the claim cannot be contested on these grounds."
                )
                return RuleVerdict(
                    status="FAIL",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=finding_text,
                    regulatory_citation="IRDAI Master Circular on Health Insurance, 29 May 2024 (60-Month Moratorium)",
                    appeal_recommendation="Appeal citing IRDAI Master Circular 2024: 60-month continuous coverage moratorium prohibits contestation on non-disclosure."
                )
            else:
                return RuleVerdict(
                    status="PASS",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=f"Moratorium check passed: {moratorium_status.get('reason')}"
                )''',
'''        portability_months = get_val(policy, 'portability_credits_months', 0) or 0
        migration_months = get_val(policy, 'migration_credits_months', 0) or 0
        moratorium_months = get_val(policy, 'moratorium_period_months', 60) or 60
        
        months_needed_on_current = moratorium_months - portability_months - migration_months
        moratorium_completion_date = policy_start + relativedelta(months=months_needed_on_current)
        
        if hasattr(policy, "evaluate_moratorium"):
            moratorium_status = policy.evaluate_moratorium(claim_date, claim_amount)
            
            if moratorium_status.get("is_protected", False) and claim_date_obj > moratorium_completion_date:
                finding_text = (
                    f"MORATORIUM_RULE_CONFLICT: Rejection cites non-disclosure/pre-existing after the {moratorium_months}-month moratorium.\\n"
                    f"Continuous coverage required: {moratorium_months} months.\\n"
                    f"Ported credits: {portability_months} months.\\n"
                    f"Coverage start: {policy_start}\\n"
                    f"Moratorium completion: {moratorium_completion_date}\\n"
                    f"Claim date: {claim_date_obj}\\n"
                    "Inconsistency: Claim occurred after moratorium completion. Unless established fraud applies, the claim cannot be contested on these grounds."
                )
                return RuleVerdict(
                    status="FAIL",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=finding_text,
                    regulatory_citation="IRDAI Master Circular on Health Insurance, 29 May 2024 (60-Month Moratorium)",
                    appeal_recommendation="Appeal citing IRDAI Master Circular 2024: 60-month continuous coverage moratorium prohibits contestation on non-disclosure."
                )
            else:
                return RuleVerdict(
                    status="PASS",
                    rule_name="Clause Timeline Rule",
                    rule_description="Validates continuous coverage moratorium rules.",
                    confidence=1.0,
                    finding=f"Claim date ({claim_date_obj}) is before moratorium completion ({moratorium_completion_date}). Rejection is temporally valid."
                )'''
)

with open('backend/app/rules/clause_timeline.py', 'w', encoding='utf-8') as f:
    f.write(code)
