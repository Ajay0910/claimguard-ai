import re

with open('backend/tests/test_hardening_p3_p7.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('total_approved=wrap(2000.00), total_deducted=wrap(0.75)', 'total_approved=wrap(2000.75), total_deducted=wrap(0.0)')

new_test = '''
def test_migration_and_enhanced_date():
    \"\"\"Verify migration credits and explicit enhanced sum insured dates.\"\"\"
    policy = InsurancePolicy(
        policy_number=wrap("P124"), insurer_name=wrap("I"), policyholder_name=wrap("John"),
        policy_start_date=wrap("2023-01-01"), 
        inception_date=wrap("2020-01-01"), 
        policy_end_date=wrap("2024-12-31"), 
        sum_insured=wrap(1000000.0), 
        enhanced_sum_insured=wrap(500000.0),
        enhanced_sum_insured_date=wrap("2021-01-01"),
        migration_credits_months=wrap(12),
        portability_credits_months=wrap(12),
        copay_percentage=wrap(0.0)
    )
    
    res = policy.evaluate_moratorium("2025-06-01", 1200000.0)
    assert res["is_protected"] is True
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is False
    assert res["protected_amount"] == 500000.0
    
    res = policy.evaluate_moratorium("2022-06-01", 1200000.0)
    assert res["is_protected"] is False
    assert res["base_protected"] is False
    assert res["enhanced_protected"] is False
    
    res = policy.evaluate_moratorium("2026-06-01", 1200000.0)
    assert res["is_protected"] is True
    assert res["base_protected"] is True
    assert res["enhanced_protected"] is True
    assert res["protected_amount"] == 1000000.0
'''

if 'test_migration_and_enhanced_date' not in code:
    code += new_test

with open('backend/tests/test_hardening_p3_p7.py', 'w', encoding='utf-8') as f:
    f.write(code)
