import re
path = 'app/extraction/pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the RejectionReason initialization
old_str = '''                    RejectionReason(
                        category="PROPORTIONATE_DEDUCTION",
                        description="Proportionate Deduction Applied as per Clause 4.2 (37.5%)",
                        deduction_amount=67500.0,
                        policy_clause_reference="Clause 4.2"
                    )'''
new_str = '''                    RejectionReason(
                        code="PD01",
                        category="PROPORTIONATE_DEDUCTION",
                        description="Proportionate Deduction Applied as per Clause 4.2 (37.5%)",
                        clause_cited="Clause 4.2"
                    )'''
content = content.replace(old_str, new_str)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
