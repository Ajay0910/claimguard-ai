import requests
from fpdf import FPDF
import time

def make_pdf(filename, text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.cell(200, 10, txt=line, ln=1)
    pdf.output(filename)

make_pdf("fail_bill.pdf", "INVOICE\nAmount: 5000\nTotal: 5000")
make_pdf("fail_policy.pdf", "POLICY\nCover: 500000")
make_pdf("fail_rejection.pdf", "REJECTION\nSorry.")

url_upload = "http://localhost:8000/api/upload"

resp = requests.post(url_upload, files={'file': ('bill.pdf', open('fail_bill.pdf', 'rb'), 'application/pdf')}, data={'document_type': 'HOSPITAL_BILL', 'patient_name': 'Unknown'})
claim_id = resp.json()['claim_id']
requests.post(url_upload, files={'file': ('policy.pdf', open('fail_policy.pdf', 'rb'), 'application/pdf')}, data={'document_type': 'INSURANCE_POLICY', 'claim_id': claim_id})
requests.post(url_upload, files={'file': ('rejection.pdf', open('fail_rejection.pdf', 'rb'), 'application/pdf')}, data={'document_type': 'REJECTION_LETTER', 'claim_id': claim_id})

requests.post(f"http://localhost:8000/api/analyze/{claim_id}")

while True:
    status_resp = requests.get(f"http://localhost:8000/api/analyze/{claim_id}/status").json()
    if status_resp.get('status') in ['COMPLETED', 'FAILED', 'ERROR']:
        break
    time.sleep(2)

print("Overall Status:", requests.get(f"http://localhost:8000/api/analyze/{claim_id}/result").json()['result']['overall_status'])
import sqlite3
import json
conn = sqlite3.connect('backend/claimguard.db')
c = conn.cursor()
c.execute('SELECT document_type, extracted_data FROM documents WHERE claim_id = ?', (claim_id,))
for r in c.fetchall():
    print(r[0])
    data = json.loads(r[1]) if r[1] else {}
    print(data.get('patient_name'))
