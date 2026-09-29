import os
import random
from datetime import datetime
from fpdf import FPDF

out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "synthetic_rejections"))
os.makedirs(out_dir, exist_ok=True)

patient = "Rajesh Gupta"
insurer = "Star Health"
policy_no = "POL-9999"
claim_no = "CLM-8888"

claimed = 150000.0
approved = 0.0
deducted = 150000.0
reason = "Claim rejected: Admission was not medically necessary. Treatment could have been done on an outpatient basis."

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(0, 10, insurer, ln=True, align="C")
pdf.set_font("Arial", "B", 12)
pdf.cell(0, 10, "CLAIM SETTLEMENT / REJECTION LETTER", ln=True, align="C")
pdf.ln(10)

pdf.set_font("Arial", "", 10)
pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
pdf.cell(0, 6, f"Ref No: REF-{random.randint(10000, 99999)}", ln=True)
pdf.ln(5)
pdf.cell(0, 6, f"Policyholder: {patient}", ln=True)
pdf.cell(0, 6, f"Policy No: {policy_no}", ln=True)
pdf.cell(0, 6, f"Claim No: {claim_no}", ln=True)
pdf.ln(10)

pdf.set_font("Arial", "B", 10)
pdf.cell(0, 6, "Claim Summary:", ln=True)
pdf.set_font("Arial", "", 10)
pdf.cell(50, 6, "Claimed Amount:")
pdf.cell(0, 6, f"INR {claimed:,.2f}", ln=True)
pdf.cell(50, 6, "Approved Amount:")
pdf.cell(0, 6, f"INR {approved:,.2f}", ln=True)
pdf.cell(50, 6, "Deducted Amount:")
pdf.cell(0, 6, f"INR {deducted:,.2f}", ln=True)
pdf.ln(10)

pdf.set_font("Arial", "B", 10)
pdf.cell(0, 6, "Deduction / Rejection Remarks:", ln=True)
pdf.set_font("Arial", "", 10)
pdf.multi_cell(0, 6, reason)
pdf.ln(10)

pdf.cell(0, 6, "For Grievance Redressal, please contact gro@insurer.com or IRDAI Bima Bharosa.", ln=True)

filename = "rejection_Clinical_Necessity.pdf"
filepath = os.path.join(out_dir, filename)
pdf.output(filepath)

print(f"Generated {filepath}")
