import os
import json
import random
from datetime import datetime
from fpdf import FPDF

PATIENTS = [f"Patient_{i}" for i in range(1, 41)]
INSURERS = ["Star Health", "HDFC Ergo", "ICICI Lombard", "Bajaj Allianz", "New India Assurance"]

def generate_rejections():
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "synthetic_rejections"))
    os.makedirs(out_dir, exist_ok=True)
    manifest = []

    random.seed(999)
    for i in range(30):
        patient = "Rajesh Gupta"
        insurer = random.choice(INSURERS)
        policy_no = f"POL-{1000+i}"
        claim_no = f"CLM-{5000+i}"
        
        if i < 10:
            cat = "Proportionate deduction error"
            claimed, approved = 100000.0, 60000.0
            reason = "Room rent limit exceeded. Applied deduction proportionately on ALL charges (Error)."
        elif i < 15:
            cat = "Waiting period misapplication"
            claimed, approved = 80000.0, 0.0
            reason = "Claim rejected under 2-year specific disease waiting period (Incorrect, expired)."
        elif i < 20:
            cat = "Mental health illegal rejection"
            claimed, approved = 45000.0, 0.0
            reason = "Psychiatric treatment is permanently excluded (Illegal per MHCA 2017)."
        elif i < 25:
            cat = "Legitimate rejection"
            claimed, approved = 50000.0, 0.0
            reason = "Claim rejected: Admission within initial 30-day waiting period."
        else:
            cat = "Pre-existing disease moratorium errors"
            claimed, approved = 120000.0, 0.0
            reason = "PED exclusion applied (Error: policy is >60 months old, moratorium applies)."

        deducted = claimed - approved

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

        filename = f"rejection_{i:03d}_{cat.replace(' ', '_')}.pdf"
        filepath = os.path.join(out_dir, filename)
        pdf.output(filepath)

        manifest.append({
            "filename": filename,
            "patient": patient,
            "policy_no": policy_no,
            "claim_no": claim_no,
            "category": cat,
            "claimed_amount": claimed,
            "approved_amount": approved,
            "deducted_amount": deducted
        })

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Generated 30 rejections in {out_dir}")

if __name__ == "__main__":
    generate_rejections()
