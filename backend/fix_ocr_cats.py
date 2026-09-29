path = 'app/extraction/pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('category="SURGEON_FEE"', 'category="CONSULTATION"')
content = content.replace('category="OT_CHARGES"', 'category="OT"')
content = content.replace('category="MEDICINE"', 'category="PHARMACY"')
content = content.replace('category="DIAGNOSTICS"', 'category="LAB"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
