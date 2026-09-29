path = 'app/rules/proportionate_deduction.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("category', '') == 'CONSUMABLES'", "category', '') == 'MISCELLANEOUS'")
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
