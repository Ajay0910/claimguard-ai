import fitz
doc = fitz.open('test_docs/hard_test_insurance_policy.pdf')
for page in doc:
    print(page.get_text())
