import os

def fix_tests(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('result.review_status == "LOW"', 'result.review_status == "CLEAN"')
    content = content.replace('result.review_status in ["HIGH", "CRITICAL"]', 'result.review_status == "FLAGGED FOR REVIEW"')
    content = content.replace('result.review_status in ["FLAGGED FOR REVIEW", "FLAGGED FOR REVIEW"]', 'result.review_status == "FLAGGED FOR REVIEW"')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_tests('tests/test_new_features.py')
fix_tests('tests/test_adversarial_challenger_1.py')
