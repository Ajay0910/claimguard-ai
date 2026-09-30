import os
import requests
from fpdf import FPDF
import uuid

os.makedirs("test_docs/new_variants", exist_ok=True)

def make_pdf(filename, text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Write each line
    for line in text_content.split('\n'):
        pdf.cell(200, 10, txt=line, ln=1)
    
    path = f"test_docs/new_variants/{filename}"
    pdf.output(path)
    return path

# Variant 1: Completely different hospital bill layout (No "Hospital Bill" title, different field names)
b1_text = """
MEDICAL INVOICE
Invoice No: INV-778899
Date of Service: 2025-02-10 to 2025-02-15
Facility: Apollo Cradle, Bengaluru
Patient: Anita Desai

Services Rendered:
- Accommodation (Deluxe)    5 days @ 5000/day = 25000.00
- Pharmacy Items            15000.00
- Doctor Visits             4000.00

Grand Total: INR 44000.00
"""
b1_path = make_pdf("variant1_bill.pdf", b1_text)

# Variant 2: Policy with different wording
p1_text = """
HEALTH COVERAGE CERTIFICATE
Certificate No: HC-999-APOLLO
Member Name: Anita Desai
Coverage Start: 2020-05-01
Coverage End: 2025-04-30
Maximum Sum Assured: 500000.00

Terms & Conditions:
1. Room Rent Capping: Covered up to 1% of Sum Assured per day.
2. Waiting Period: Pre-existing conditions covered after 48 months.
"""
p1_path = make_pdf("variant2_policy.pdf", p1_text)

# Variant 3: Rejection/Settlement Letter with different layout
r1_text = """
CLAIM DECISION SUMMARY
Claim Reference: CLM-APO-4455
Beneficiary: Anita Desai
Certificate: HC-999-APOLLO

We have reviewed your recent medical claim for INR 44000.00.
Approved Amount: INR 39000.00
Deducted Amount: INR 5000.00
Reason for Deduction: Room rent exceeded the 1% cap (5000/day instead of 4000/day).

Status: Settled.
"""
r1_path = make_pdf("variant3_rejection.pdf", r1_text)

print("Generated new document variants.")

# Now test via API
def test_pipeline(bill_path, policy_path, rej_path):
    url = "http://localhost:8000/api/claims/analyze"
    files = [
        ('files', ('bill.pdf', open(bill_path, 'rb'), 'application/pdf')),
        ('files', ('policy.pdf', open(policy_path, 'rb'), 'application/pdf')),
        ('files', ('rejection.pdf', open(rej_path, 'rb'), 'application/pdf'))
    ]
    data = {
        'patient_name': 'Anita Desai',
        'patient_email': 'anita@example.com',
        'patient_phone': '9999999999'
    }
    
    print(f"Sending request for {bill_path}, {policy_path}, {rej_path}...")
    try:
        resp = requests.post(url, files=files, data=data)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print("Error:", resp.text)
        else:
            json_resp = resp.json()
            print("Success!")
            print(json_resp)
    except Exception as e:
        print("Request failed:", e)

test_pipeline(b1_path, p1_path, r1_path)
