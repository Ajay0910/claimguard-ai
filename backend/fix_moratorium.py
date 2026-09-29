path = 'app/rules/clause_timeline.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
new_lines = []
skip = False
for line in lines:
    if 'if elapsed_months > 36:' in line:
        skip = True
    elif skip and 'return RuleVerdict(status="PASS"' in line:
        skip = False
    
    if not skip:
        new_lines.append(line)
        
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
