path = 'app/rules/document_integrity.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('status="CONFLICT"', 'status="WARNING"')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

path2 = 'app/rules/appeal_evaluator.py'
with open(path2, 'r', encoding='utf-8') as f:
    content2 = f.read()
content2 = content2.replace('status == "CONFLICT"', 'status == "WARNING"')
with open(path2, 'w', encoding='utf-8') as f:
    f.write(content2)
