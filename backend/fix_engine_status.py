path = 'app/rules/engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_block = '        has_fail = any(v.status == "FAIL" for v in verdicts)\n        has_review = any(v.status == "NEEDS_REVIEW" for v in verdicts)\n        \n        if has_fail:\n            overall_status = "MISMATCH_DETECTED"\n        elif has_review:\n            overall_status = "REVIEW_RECOMMENDED"\n        else:\n            overall_status = "NO_MISMATCH_FOUND"\n            \n        fail_count = sum(1 for v in verdicts if v.status == "FAIL")\n        review_count = sum(1 for v in verdicts if v.status == "NEEDS_REVIEW")\n        summary = f"Rule engine completed. {fail_count} failures, {review_count} needs review."'

new_block = '        has_blocked = any(v.status == "BLOCKED" for v in verdicts)\n        has_fail = any(v.status == "FAIL" for v in verdicts)\n        has_review = any(v.status == "NEEDS_REVIEW" for v in verdicts)\n        \n        if has_blocked:\n            overall_status = "BLOCKED"\n        elif has_fail:\n            overall_status = "MISMATCH_DETECTED"\n        elif has_review:\n            overall_status = "REVIEW_RECOMMENDED"\n        else:\n            overall_status = "NO_MISMATCH_FOUND"\n            \n        fail_count = sum(1 for v in verdicts if v.status == "FAIL")\n        review_count = sum(1 for v in verdicts if v.status == "NEEDS_REVIEW")\n        \n        if has_blocked:\n            blocked_rule = next(v.rule_name for v in verdicts if v.status == "BLOCKED")\n            summary = f"ACTION = FINANCIAL_ENGINE_NOT_EXECUTED. Blocked by Tier 0 rule: {blocked_rule}."\n        else:\n            summary = f"Rule engine completed. {fail_count} failures, {review_count} needs review."'

content = content.replace(old_block, new_block)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
