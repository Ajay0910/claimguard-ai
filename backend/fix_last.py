import re

def fix(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Fix test_tier1_features.py
r1 = [
    ('summary="Serialized test"', 'summary="Serialized test", total_monetary_impact=12345.67'),
    ('rejection = make_rejection(policyholder_name="Different Person", total_claimed=50000.0, total_approved=50000.0, total_deducted=0.0)',
     'rejection = make_rejection(policyholder_name="Wrong Person", total_claimed=50000.0, total_approved=50000.0, total_deducted=0.0)')
]
fix('tests/e2e/test_tier1_features.py', r1)

# Fix test_tier2_boundaries.py
r2 = [
    ('summary="Extreme monetary values"', 'summary="Extreme monetary values", total_monetary_impact=150000000.0'),
    ('summary="Paise rounding"', 'summary="Paise rounding", total_monetary_impact=0.03')
]
fix('tests/e2e/test_tier2_boundaries.py', r2)

# Fix test_tier3_pairwise.py
r3 = [
    ('rejection = make_rejection(policyholder_name="Different Person")', 'rejection = make_rejection(policyholder_name="Wrong Person")')
]
fix('tests/e2e/test_tier3_pairwise.py', r3)

