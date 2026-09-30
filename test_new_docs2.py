import os
import time
import requests

b1_path = "test_docs/new_variants/variant1_bill.pdf"
p1_path = "test_docs/new_variants/variant2_policy.pdf"
r1_path = "test_docs/new_variants/variant3_rejection.pdf"

url_upload = "http://localhost:8000/api/upload"

print("Uploading Bill...")
resp = requests.post(url_upload, files={'file': ('bill.pdf', open(b1_path, 'rb'), 'application/pdf')}, data={'document_type': 'HOSPITAL_BILL', 'patient_name': 'Anita Desai'})
claim_id = resp.json()['claim_id']
print(f"Claim ID: {claim_id}")

print("Uploading Policy...")
requests.post(url_upload, files={'file': ('policy.pdf', open(p1_path, 'rb'), 'application/pdf')}, data={'document_type': 'INSURANCE_POLICY', 'claim_id': claim_id})

print("Uploading Rejection...")
requests.post(url_upload, files={'file': ('rejection.pdf', open(r1_path, 'rb'), 'application/pdf')}, data={'document_type': 'REJECTION_LETTER', 'claim_id': claim_id})

print("Triggering Analysis...")
url_analyze = f"http://localhost:8000/api/analyze/{claim_id}"
requests.post(url_analyze)

url_status = f"http://localhost:8000/api/analyze/{claim_id}/status"
while True:
    status_resp = requests.get(url_status).json()
    print("Status:", status_resp.get('status'))
    if status_resp.get('status') in ['COMPLETED', 'FAILED', 'ERROR']:
        break
    time.sleep(2)

if status_resp.get('status') == 'COMPLETED':
    print("Analysis Completed Successfully!")
    url_result = f"http://localhost:8000/api/analyze/{claim_id}/result"
    print(requests.get(url_result).json())
else:
    print("Analysis Failed!")
