import os
import re

backend_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend"

# Map for finding types based on filename or rule context
FINDING_TYPES = {
    'identity_gate.py': 'IDENTITY_CONFLICT',
    'clinical_firewall.py': 'CLINICAL_REJECTION',
    'authenticity_check.py': 'FRAUD_SIGNAL',
    'document_integrity.py': 'DOCUMENT_INCONSISTENCY',
    'mental_health_parity.py': 'REGULATORY_CONFLICT',
    'clause_timeline.py': 'REGULATORY_CONFLICT',
    'proportionate_deduction.py': 'REGULATORY_CONFLICT',
    'waiting_period.py': 'REGULATORY_CONFLICT',
    'copay_rule.py': 'FINANCIAL_DISCREPANCY',
    'deductible_rule.py': 'FINANCIAL_DISCREPANCY',
    'cross_document_adjudication.py': 'DOCUMENT_INCONSISTENCY',
    'engine.py': 'FINANCIAL_DISCREPANCY',
    'policy_applicability.py': 'POLICY_MISMATCH'
}

def update_rule_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(path)
    default_type = FINDING_TYPES.get(filename, 'NEEDS_REVIEW')

    # Replace RuleVerdict(
    # by parsing the arguments and adding finding_type.
    # We can do this with a simpler approach: replace `finding=...` with `finding=..., finding_type=...`
    # However, sometimes finding=... is not at the end.
    
    # Let's just find `RuleVerdict(` and inject finding_type based on status if possible.
    # Actually, we can use regex to find `finding=...` up to the next parameter or closing bracket, but it's risky with multiline.
    # Simpler: regex search for `RuleVerdict(` and replace it with a wrapper or append finding_type if not present.
    # Since finding_type has default None, we can just leave it for PASS, but we need it for all findings per Point 12: "Explicitly classify every finding".
    
    # Let's replace 'RuleVerdict(' with a custom function or just append finding_type inside if not present.
    # Even simpler: we just regex replace 'RuleVerdict(' with `RuleVerdict(finding_type="{}", `. Wait, RuleVerdict is a pydantic model, keyword args are usually used, but positional might be used.
    
    # We will use regex to inject `finding_type="<type>", ` right after `RuleVerdict(`.
    if "finding_type=" not in content:
        content = content.replace("RuleVerdict(", f'RuleVerdict(finding_type="{default_type}", ')
        
    # Replace "Violation" with "Conflict"
    content = content.replace("Violation", "Conflict").replace("violation", "conflict").replace("VIOLATION", "CONFLICT")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(os.path.join(backend_dir, "app", "rules")):
    for f in files:
        if f.endswith('.py') and f != '__init__.py' and f != 'rule_registry.py':
            update_rule_file(os.path.join(root, f))
            
# Also replace in tests
for root, _, files in os.walk(os.path.join(backend_dir, "tests")):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                c = file.read()
            c = c.replace("Violation", "Conflict").replace("violation", "conflict").replace("VIOLATION", "CONFLICT")
            with open(os.path.join(root, f), 'w', encoding='utf-8') as file:
                file.write(c)

# Also update appeal_evaluator schemas and references
schemas_dir = os.path.join(backend_dir, "app", "schemas")
for f in os.listdir(schemas_dir):
    if f.endswith('.py'):
        path = os.path.join(schemas_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            c = file.read()
        c = c.replace("statutory_violations_detected", "statutory_conflicts_detected")
        with open(path, 'w', encoding='utf-8') as file:
            file.write(c)

print("Done replacing in rules, tests, and schemas.")
