path = 'app/schemas/analysis_result.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('"NEEDS_REVIEW", "WARNING"]', '"NEEDS_REVIEW", "WARNING", "BLOCKED"]')
content = content.replace('"REVIEW_RECOMMENDED", "EXTRACTION_FAILED"]', '"REVIEW_RECOMMENDED", "EXTRACTION_FAILED", "BLOCKED"]')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

path2 = 'app/schemas/insurance_policy.py'
with open(path2, 'r', encoding='utf-8') as f:
    content2 = f.read()

new_fields = """
    covers_maternity: bool = False
    moratorium_period_months: Optional[int] = 60
    portability_credits_months: Optional[int] = 0
    enhanced_sum_insured: Optional[float] = 0.0
    enhanced_sum_insured_date: Optional[str] = None
    exclusions: list[str] = []
"""
import re
content2 = re.sub(r'covers_maternity.*?\n\s*exclusions.*?\[\]\n', new_fields, content2, flags=re.DOTALL)
with open(path2, 'w', encoding='utf-8') as f:
    f.write(content2)
