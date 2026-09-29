import re

path = 'app/rules/proportionate_deduction.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_str = "sum(item.amount for item in getattr(bill, 'line_items', []) if getattr(item, 'is_non_medical', False))"
new_str = "sum(item.amount for item in getattr(bill, 'line_items', []) if getattr(item, 'category', '') == 'CONSUMABLES')"

content = content.replace(old_str, new_str)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
