import os
import json
import random
from datetime import datetime, timedelta
from fpdf import FPDF

INSURERS = ["Star Health", "HDFC Ergo", "ICICI Lombard", "Bajaj Allianz", "New India Assurance"]
SUMS_INSURED = [300000, 500000, 1000000, 1500000]
ROOM_LIMITS = [3000, 4000, 5000, None]
COPAYS = [0, 10, 20]

class PolicyPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, self.insurer, 0, 1, "C")
        self.set_font("Arial", "I", 12)
        self.cell(0, 8, "Health Insurance Policy Schedule", 0, 1, "C")
        self.line(10, 30, 200, 30)
        self.ln(10)

def generate_policy(policy_idx):
    insurer = random.choice(INSURERS)
    si = random.choice(SUMS_INSURED)
    room_limit = random.choice(ROOM_LIMITS)
    copay = random.choice(COPAYS)
    
    # Random patient names (matching those that might be in bills)
    PATIENTS = [
        "Rahul Sharma", "Priya Patel", "Arun Kumar", "Deepika Reddy", "Suresh Menon",
        "Anita Desai", "Vikram Singh", "Meera Nair", "Rajesh Gupta", "Kavitha Iyer"
    ]
    
    # Assign Rajesh Gupta specifically to the first policy to match the first bill, or random otherwise
    if policy_idx == 1:
        patient_name = "Rajesh Gupta"
    else:
        patient_name = random.choice(PATIENTS)
    
    start_year = random.randint(2020, 2025)
    start_date = f"{start_year}-01-01"
    mental_health = random.choice([True, False])
    
    pdf = PolicyPDF()
    pdf.insurer = insurer
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Policy Details", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 6, f"Policy No: POL{random.randint(100000,999999)}", 0, 1)
    pdf.cell(50, 6, f"Policyholder: {patient_name}", 0, 1)
    pdf.cell(50, 6, f"Start Date: {start_date}", 0, 1)
    pdf.cell(50, 6, f"Sum Insured: INR {si:,.2f}", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Coverage Limits & Copay", 0, 1)
    pdf.set_font("Arial", "", 10)
    
    room_str = f"INR {room_limit}/day" if room_limit else "No Limit (Single Private AC Room)"
    pdf.cell(0, 6, f"Room Rent Limit: {room_str}", 0, 1)
    pdf.cell(0, 6, f"Co-Payment: {copay}% on all claims", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Waiting Periods", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, "- Initial Waiting Period: 30 days", 0, 1)
    pdf.cell(0, 6, "- Specific Illnesses: 24 months", 0, 1)
    pdf.cell(0, 6, "- Pre-existing Diseases: 48 months", 0, 1)
    pdf.cell(0, 6, "- Moratorium Period: 60 months", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Specific Coverages", 0, 1)
    pdf.set_font("Arial", "", 10)
    mh_str = "Covered up to SI" if mental_health else "Not Covered"
    pdf.cell(0, 6, f"- Mental Health Coverage: {mh_str}", 0, 1)
    
    filename = f"policy_{policy_idx:03d}.pdf"
    
    return pdf, filename, {
        "filename": filename,
        "insurer": insurer,
        "patient": patient_name,
        "sum_insured": si,
        "room_rent_limit": room_limit,
        "copay_percent": copay,
        "start_date": start_date,
        "mental_health_covered": mental_health
    }

def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'synthetic_policies')
    os.makedirs(out_dir, exist_ok=True)
    
    manifest = []
    for i in range(1, 31):
        pdf, filename, meta = generate_policy(i)
        pdf.output(os.path.join(out_dir, filename))
        manifest.append(meta)
        
    with open(os.path.join(out_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)

if __name__ == '__main__':
    main()
