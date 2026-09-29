path = 'app/extraction/pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = '''if expected_type == 'HOSPITAL_BILL':
                    doc_type = 'bill'
                elif expected_type == 'INSURANCE_POLICY':
                    doc_type = 'policy'
                elif expected_type == 'REJECTION_LETTER':
                    doc_type = 'rejection'
                else:
                    doc_type = self.vlm_extractor.classify_document(image_bytes, mime_type)'''

content = content.replace("doc_type = self.vlm_extractor.classify_document(image_bytes, mime_type)", new_logic)

content = content.replace("results['bill'] = self.process_document(bill_path)", "results['bill'] = self.process_document(bill_path, 'HOSPITAL_BILL')")
content = content.replace("results['policy'] = self.process_document(policy_path)", "results['policy'] = self.process_document(policy_path, 'INSURANCE_POLICY')")
content = content.replace("results['rejection'] = self.process_document(rejection_path)", "results['rejection'] = self.process_document(rejection_path, 'REJECTION_LETTER')")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
