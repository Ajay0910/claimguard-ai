import json
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

def main():
    base_dir = r'C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend\tests\benchmark'
    json_path = os.path.join(base_dir, 'benchmark_cases.json')
    dataset_dir = os.path.join(base_dir, 'benchmark_dataset')
    
    os.makedirs(dataset_dir, exist_ok=True)
    
    with open(json_path, 'r') as f:
        cases = json.load(f)
        
    for case in cases:
        case_id = case['case_id']
        case_dir = os.path.join(dataset_dir, case_id)
        os.makedirs(case_dir, exist_ok=True)
        
        create_pdf(os.path.join(case_dir, 'hospital_bill.pdf'), case['documents']['hospital_bill'])
        create_pdf(os.path.join(case_dir, 'insurance_policy.pdf'), case['documents']['insurance_policy'])
        create_pdf(os.path.join(case_dir, 'rejection_letter.pdf'), case['documents']['rejection_letter'])
        
    print(f"Successfully generated PDFs for {len(cases)} benchmark cases in {dataset_dir}")

if __name__ == '__main__':
    main()
