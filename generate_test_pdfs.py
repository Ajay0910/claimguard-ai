import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_pdf(path, text_lines):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()

os.makedirs('C:/Users/Ajay/.gemini/antigravity/scratch/claimguard-ai/test_docs', exist_ok=True)

# 1. Hospital Bill
bill_lines = [
    "APOLLO SPECIALITY HOSPITAL",
    "Patient Name: Rajesh Gupta",
    "Bill ID: BILL-2026-999",
    "Admission Date: 2026-05-10",
    "Discharge Date: 2026-05-15",
    "Length of Stay: 5 days",
    "Diagnosis: Acute Appendicitis",
    "",
    "LINE ITEMS:",
    "1. Standard Private Room (5 days @ 4500) = 22500 (Room)",
    "2. Nursing Charges (5 days @ 1000) = 5000 (Nursing)",
    "3. Surgical Consultation = 15000 (Consultation)",
    "4. Operation Theatre Charges = 35000 (OT)",
    "5. Cath Lab Charges = 25000 (Cath_Lab)",
    "6. Pharmacy = 15000 (Pharmacy)",
    "7. Miscellaneous = 10000 (Miscellaneous)",
    "",
    "TOTAL AMOUNT: 127500"
]
create_pdf('C:/Users/Ajay/.gemini/antigravity/scratch/claimguard-ai/test_docs/hard_test_hospital_bill.pdf', bill_lines)

# 2. Insurance Policy
policy_lines = [
    "STAR HEALTH INSURANCE POLICY",
    "Policyholder Name: Rajesh Gupta",
    "Policy Number: POL-555-888",
    "Original Inception Date: 2021-01-01",
    "Current Policy Start Date: 2026-01-01",
    "Current Policy End Date: 2026-12-31",
    "Sum Insured: 500000",
    "Base Sum Insured: 300000",
    "Enhanced Sum Insured: 200000",
    "",
    "CLAUSES:",
    "- Room Rent Limit: 4000 per day",
    "- Proportionate Deduction Clause: Applies if room rent exceeds limit by > 15%",
    "- Deductible: 10000",
    "- Co-pay: 10% on remaining balance",
    "- Moratorium Period: 60 months (Portability credits apply)"
]
create_pdf('C:/Users/Ajay/.gemini/antigravity/scratch/claimguard-ai/test_docs/hard_test_insurance_policy.pdf', policy_lines)

# 3. Rejection / Settlement Letter
rejection_lines = [
    "CLAIM SETTLEMENT LETTER",
    "Insurer: Star Health Insurance",
    "Policy Number: POL-555-888",
    "Claim Number: CL-2026-ABC",
    "Patient Name: Suresh Gupta", # Identity mismatch boundary!
    "",
    "Total Claimed: 127500",
    "Total Approved: 70000", # Intentionally wrong to test reconciliation
    "Total Deducted: 57500",
    "",
    "DEDUCTION REASONS:",
    "1. Patient name mismatch (Suresh vs Rajesh) - Warning",
    "2. Room rent limit exceeded - Proportionate deduction applied to entire bill.",
    "3. Disease within waiting period - Rejected under pre-existing conditions."
]
create_pdf('C:/Users/Ajay/.gemini/antigravity/scratch/claimguard-ai/test_docs/hard_test_rejection_letter.pdf', rejection_lines)

print("PDFs created.")
