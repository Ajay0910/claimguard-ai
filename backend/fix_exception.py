path = 'app/rules/proportionate_deduction.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content += """
    except Exception as e:
        return RuleVerdict(status="SKIPPED", rule_name="Proportionate Deduction Rule", rule_description="", confidence=1.0, finding=f"Error evaluating rule: {str(e)}")
"""
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
