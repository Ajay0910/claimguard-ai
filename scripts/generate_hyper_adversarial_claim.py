"""
Hyper-Adversarial Forensic Claim Documents Generator for ClaimGuard AI (Level 10 Hardness).

Creates 3 ultra-realistic, deeply disguised Indian health insurance documents
with Level 10 forensic hardness designed to deceive human surveyors and claim auditors:

1. Apollo Hospitals (Greams Road, Chennai) - 2-page Inpatient Final Bill
   - Patient: Dr. Suniti Mukherjee, 63 Y / Female
   - Robotic Assisted Bilateral Total Knee Arthroplasty (TKR) with Mako Stryker Suite
   - 31 itemized line items summing to Rs. 11,68,500.00
2. ICICI Lombard General Insurance Co. Ltd. - 2-page Policy Schedule & Clauses
   - Policy: iHealth Complete Health Insurance (Health Shield Plus)
   - Continuous coverage 99 months (incepted 15-May-2018, ported from Star Health)
   - Base SI: Rs. 10,00,000 + Accrued Cumulative Bonus: Rs. 5,00,000 = Total SI Rs. 15,00,000
   - Single Private A/C Room (Uncapped), Nil Co-pay
3. Medi Assist Insurance TPA Private Limited - 2-page Settlement & Deduction Advice
   - Approved: Rs. 4,80,000.00 | Disallowed: Rs. 6,88,500.00
   - 5 deep statutory flaws summing to Rs. 6,82,000.00 recoverable (+ Rs. 6,500 legitimate):
     1. Modern Treatment Robotic Sub-Limit Capping on Base SI vs Total SI (Rs. 2,50,000.00)
     2. Portability Moratorium Reset Fallacy ignoring 99-month continuity (Rs. 1,75,000.00)
     3. Synthetic PPN Tariff Proportionate Room Rent on Uncapped Policy (Rs. 1,77,000.00)
     4. Biological Hemostatic Flowable Matrix Floseal under List I (Rs. 48,000.00)
     5. Elastomeric Continuous Infusion PCA Pain Pump under List I (Rs. 32,000.00)
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import pymupdf


class NumberedCanvas(canvas.Canvas):
    """Canvas for multi-page documents with Page X of Y footers."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 22, page_text)
        self.drawString(36, 22, "Official Legal Document - Medical & Insurance Adjudication Record")
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    
    teal = colors.HexColor("#0A4D68")
    navy = colors.HexColor("#082040")
    crimson = colors.HexColor("#990000")
    dark_gray = colors.HexColor("#222222")
    
    styles.add(ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=navy, alignment=1))
    styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10.5, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=navy, spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle('SectionHeadingTeal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=teal, spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle('SectionHeadingRed', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=crimson, spaceBefore=4, spaceAfter=3))
    
    styles.add(ParagraphStyle('TableHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('TableCellRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('MetaLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=navy))
    styles.add(ParagraphStyle('MetaVal', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=dark_gray))
    styles.add(ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('ClauseBody', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('LegalCitation', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#444444")))
    
    return styles


# ==============================================================================
# DOCUMENT 1: APOLLO HOSPITALS BILL (CHENNAI)
# ==============================================================================

def generate_apollo_hospital_bill(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=40
    )
    story = []
    teal = colors.HexColor("#0A4D68")
    
    # Header Banner
    story.append(Paragraph("APOLLO HOSPITALS ENTERPRISE LIMITED", styles['DocTitle']))
    story.append(Paragraph("21, Greams Lane, Off Greams Road, Chennai - 600006, Tamil Nadu | NABH & JCI Accredited<br/>GSTIN: 33AAACA1234D1Z2 | CIN: L85110TN1979PLC008035 | Phone: +91-44-28290200", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=teal, spaceBefore=1, spaceAfter=5))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Patient Name:</b> Dr. Suniti Mukherjee", styles['TableCell']),
            Paragraph("<b>IP Admission No:</b> AP/2026/094182", styles['TableCell']),
            Paragraph("<b>Bill No:</b> FB/2026/CH/119041", styles['TableCell'])
        ],
        [
            Paragraph("<b>Age / Gender:</b> 63 Y / Female", styles['TableCell']),
            Paragraph("<b>Admission Date & Time:</b> 14-Aug-2026 09:15 AM", styles['TableCell']),
            Paragraph("<b>Bill Date & Time:</b> 19-Aug-2026 04:30 PM", styles['TableCell'])
        ],
        [
            Paragraph("<b>Consultant Surgeon:</b> Dr. S. K. Rajagopalan (MS, MCh, Ortho)", styles['TableCell']),
            Paragraph("<b>Discharge Date & Time:</b> 19-Aug-2026 02:45 PM", styles['TableCell']),
            Paragraph("<b>Ward / Bed:</b> Private Deluxe - Bed 412", styles['TableCell'])
        ],
        [
            Paragraph("<b>Room Entitlement:</b> Single Private A/C Room", styles['TableCell']),
            Paragraph("<b>Primary Diagnosis:</b> Bilateral Tricompartmental Knee Osteoarthritis (M17.0)", styles['TableCell']),
            Paragraph("<b>Secondary Comorbidity:</b> Long-term Type II Diabetes Mellitus & HTN", styles['TableCell'])
        ],
        [
            Paragraph("<b>Surgical Procedure:</b> Robotic Assisted Bilateral Total Knee Arthroplasty (TKR) with Mako System", styles['TableCellBold']),
            Paragraph("<b>TPA Empanelment:</b> Medi Assist TPA (ICICI Lombard)", styles['TableCell']),
            Paragraph("<b>Insurance Policy No:</b> 4015/iH/98421045/00/000", styles['TableCell'])
        ]
    ]
    meta_table = Table(meta_data, colWidths=[180, 180, 163])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F2F8FA")),
        ('BOX', (0,0), (-1,-1), 0.5, teal),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4E6EB")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))
    
    # Line Items Page 1
    story.append(Paragraph("ITEMIZED INPATIENT CHARGES & OPERATIVE BREAKDOWN (PART 1)", styles['SectionHeadingTeal']))
    
    headers = [
        Paragraph("<b>Code</b>", styles['TableHead']),
        Paragraph("<b>Charge Head & Clinical Description</b>", styles['TableHead']),
        Paragraph("<b>SAC/HSN</b>", styles['TableHead']),
        Paragraph("<b>Qty/Days</b>", styles['TableHead']),
        Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
    ]
    
    page1_items = [
        ("ACC-01", "Single Standard Room Accommodation (Post-Op Stay)", "999311", "3 Days", "9,000.00", "27,000.00"),
        ("ACC-02", "Intensive Care Unit (ICU) Critical Post-Surgical Bed", "999311", "2 Days", "22,000.00", "44,000.00"),
        ("NUR-01", "Specialized Orthopedic Nursing Care & Vitals Triage", "999312", "5 Days", "2,200.00", "11,000.00"),
        ("RMO-01", "Resident Ortho Registrar & Medical Officer Rounds", "999312", "5 Days", "1,500.00", "7,500.00"),
        ("SUR-01", "Chief Joint Replacement Surgeon Operative Procedure Fee", "999312", "1 Proc", "85,000.00", "85,000.00"),
        ("SUR-02", "Associate Reconstructive Orthopedic Co-Surgeon Fee", "999312", "1 Proc", "50,000.00", "50,000.00"),
        ("ANE-01", "Combined Spinal-Epidural Neuroaxial Anesthesia Protocol", "999312", "1 Proc", "48,000.00", "48,000.00"),
        ("ANE-02", "Post-Op Pain Specialist rounds & Continuous Epidural Care", "999312", "4 Days", "3,500.00", "14,000.00"),
        ("OT-01", "Ultra-Clean Laminar Airflow Orthopedic Major OT Suite", "999311", "1 Session", "85,000.00", "85,000.00"),
        ("OT-02", "OT Consumables, Sterile Drape Bundles & Surgical Gas", "999311", "1 Bundle", "38,000.00", "38,000.00"),
        ("ROB-01", "Mako 3D Robotic Arm Interactive Navigational Suite Fee", "999311", "1 Case", "2,50,000.00", "2,50,000.00"),
        ("IMP-01", "Stryker Triathlon Cruciate-Retaining Femoral Knee Component (Rt)", "902110", "1 Unit", "75,000.00", "75,000.00"),
        ("IMP-02", "Stryker Triathlon Cruciate-Retaining Femoral Knee Component (Lt)", "902110", "1 Unit", "75,000.00", "75,000.00"),
        ("IMP-03", "Modular Tibial Titanium Baseplate & Locking Screws (Rt & Lt)", "902110", "2 Sets", "20,000.00", "40,000.00"),
        ("IMP-04", "Crosslinked Ultra-High Molecular Polyethylene Inserts", "902110", "2 Units", "10,000.00", "20,000.00"),
        ("DIS-01", "Floseal Hemostatic Flowable Gelatin Matrix (10ml Vascular Syringe)", "300610", "1 Unit", "48,000.00", "48,000.00"),
    ]
    
    table1_rows = [headers]
    for code, desc, sac, qty, rate, amt in page1_items:
        table1_rows.append([
            Paragraph(code, styles['TableCellSmall']),
            Paragraph(desc, styles['TableCell']),
            Paragraph(sac, styles['TableCellSmall']),
            Paragraph(qty, styles['TableCellSmall']),
            Paragraph(rate, styles['TableCellRight']),
            Paragraph(amt, styles['TableCellRightBold'])
        ])
        
    t1 = Table(table1_rows, colWidths=[42, 230, 48, 50, 75, 78])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), teal),
        ('BOX', (0,0), (-1,-1), 0.5, teal),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FBFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
    ]))
    story.append(t1)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Page 1 Sub-total (Line Items 1-16): Rs. 9,17,500.00</b>", styles['TableCellRightBold']))
    
    # Page Break to Page 2
    story.append(PageBreak())
    
    # Page 2 Header
    story.append(Paragraph("APOLLO HOSPITALS ENTERPRISE LIMITED — FINAL INPATIENT BILL (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("Bill No: FB/2026/CH/119041 | IP No: AP/2026/094182 | Patient: Dr. Suniti Mukherjee", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=teal, spaceBefore=1, spaceAfter=5))
    
    story.append(Paragraph("ITEMIZED INPATIENT CHARGES & OPERATIVE BREAKDOWN (PART 2)", styles['SectionHeadingTeal']))
    
    page2_items = [
        ("DIS-02", "Elastomeric Continuous Infusion PCA Pain Pump System", "901890", "1 Unit", "32,000.00", "32,000.00"),
        ("DIS-03", "Aquacel Ag Surgical Waterproof Post-Operative Antimicrobial Dressing", "300590", "2 Pkts", "2,500.00", "5,000.00"),
        ("DIS-04", "Intermittent Pneumatic Compression (IPC) Anti-Embolism Sleeves", "901920", "1 Pair", "3,500.00", "3,500.00"),
        ("MED-01", "Comorbid Diabetic Regimen & Glycemic Control Monitoring Protocol", "999312", "5 Days", "8,000.00", "40,000.00"),
        ("MED-02", "Hypertensive & Cardio-Renal Safety Management in High-Risk Ortho", "999312", "5 Days", "9,000.00", "45,000.00"),
        ("MED-03", "Senior Consultant Diabetologist & Endocrinologist Daily Care", "999312", "5 Days", "5,000.00", "25,000.00"),
        ("MED-04", "Senior Consultant Cardiologist Peri-Operative Optimization", "999312", "5 Days", "6,000.00", "30,000.00"),
        ("MED-05", "Senior Consultant Nephrologist Renal Perfusion Maintenance", "999312", "5 Days", "7,000.00", "35,000.00"),
        ("RAD-01", "Pre-Op High-Definition CT Scan for Mako 3D Navigational Alignment", "999313", "1 Scan", "12,000.00", "12,000.00"),
        ("RAD-02", "Post-Op Weight-Bearing Digital Bilateral Knee Radiography (6 Views)", "999313", "1 Set", "4,500.00", "4,500.00"),
        ("LAB-01", "Comprehensive Orthopedic Profile, CBC, Electrolytes & CRP", "999313", "1 Set", "6,000.00", "6,000.00"),
        ("PHY-01", "Early Mobilization Inpatient Continuous Passive Motion (CPM)", "999314", "4 Days", "1,625.00", "6,500.00"),
        ("NON-01", "Attendant Guest Food & Therapeutic Dietary Service (List I)", "996331", "5 Days", "840.00", "4,200.00"),
        ("NON-02", "Patient Vanity Kit, Sanitizer, Thermometer & Slippers (List I)", "340111", "1 Kit", "1,300.00", "1,300.00"),
        ("NON-03", "Attendant ID Pass & Administrative Registration Handling (List I)", "998311", "1 Case", "1,000.00", "1,000.00"),
    ]
    
    table2_rows = [headers]
    for code, desc, sac, qty, rate, amt in page2_items:
        table2_rows.append([
            Paragraph(code, styles['TableCellSmall']),
            Paragraph(desc, styles['TableCell']),
            Paragraph(sac, styles['TableCellSmall']),
            Paragraph(qty, styles['TableCellSmall']),
            Paragraph(rate, styles['TableCellRight']),
            Paragraph(amt, styles['TableCellRightBold'])
        ])
        
    t2 = Table(table2_rows, colWidths=[42, 230, 48, 50, 75, 78])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), teal),
        ('BOX', (0,0), (-1,-1), 0.5, teal),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FBFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))
    
    # Financial Summary Box
    summary_data = [
        [
            Paragraph("<b>Itemized Charges Sub-total (Items 1-16):</b> Rs. 9,17,500.00 | <b>(Items 17-31):</b> Rs. 2,51,000.00", styles['TableCellSmall']),
            Paragraph("<b>TOTAL GROSS BILL:</b>", styles['TableCellRightBold']),
            Paragraph("<b>Rs. 11,68,500.00</b>", styles['TableCellRightBold'])
        ],
        [
            Paragraph("All hospital charges billed in accordance with institutional tariff schedule.", styles['TableCellSmall']),
            Paragraph("<b>GROSS BILL AMOUNT:</b>", styles['TableCellRightBold']),
            Paragraph("<b>Rs. 11,68,500.00</b>", styles['TableCellRightBold'])
        ],
        [
            Paragraph("Zero advance collected at admission under cashless pre-authorization.", styles['TableCellSmall']),
            Paragraph("<b>LESS ADVANCE PAID:</b>", styles['TableCellRight']),
            Paragraph("Rs. 0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("Payable upon receipt of final TPA settlement & adjudication remittance.", styles['TableCellSmall']),
            Paragraph("<b>NET OUTSTANDING PAYABLE:</b>", styles['TableCellRightBold']),
            Paragraph("<b>Rs. 11,68,500.00</b>", styles['TableCellRightBold'])
        ]
    ]
    summary_table = Table(summary_data, colWidths=[240, 150, 133])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF3F5")),
        ('BOX', (0,0), (-1,-1), 1, teal),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C0DCE3")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))
    
    # Declarations & Signatures
    story.append(Paragraph("<b>HOSPITAL STATUTORY DECLARATION:</b> We certify that all implants, surgical robotics, medications and inpatient services billed herein were medically mandatory and executed by certified surgical teams in compliance with clinical protocol. Implants Stryker Triathlon CR are registered with NPPA. Floseal hemostatic matrix and PCA infusion pumps were intra-operatively deployed for vascular safety and pain control under NABH protocol.", styles['LegalCitation']))
    story.append(Spacer(1, 14))
    
    sig_data = [
        [
            Paragraph("Prepared by:<br/><b>Billing Executive</b><br/>Apollo Hospitals, Chennai", styles['TableCellSmall']),
            Paragraph("Verified by:<br/><b>Head of Medical Operations</b><br/>Apollo Hospitals, Greams Road", styles['TableCellSmall']),
            Paragraph("Accepted by:<br/><b>Patient / Next of Kin</b><br/>(Dr. Suniti Mukherjee)", styles['TableCellSmall']),
            Paragraph("Authorized Signatory:<br/><b>Director - Revenue & Billing</b><br/>Hospital Stamp & Seal", styles['TableCellSmall'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[130, 130, 130, 133])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sig_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Apollo Hospital Bill: {pdf_path}")


# ==============================================================================
# DOCUMENT 2: ICICI LOMBARD POLICY SCHEDULE & CLAUSES
# ==============================================================================

def generate_icici_lombard_policy(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=40
    )
    story = []
    navy = colors.HexColor("#082040")
    orange = colors.HexColor("#D85C27")
    
    # Header Banner
    story.append(Paragraph("ICICI LOMBARD GENERAL INSURANCE COMPANY LIMITED", styles['DocTitle']))
    story.append(Paragraph("ICICI Lombard House, 414, Veer Savarkar Marg, Near Siddhivinayak Temple, Prabhadevi, Mumbai - 400025<br/>IRDAI Regn No. 115 | CIN: L67200MH2000PLC129408 | Toll Free: 1800 2666 | UIN: ICIHLIP21383V052021", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=orange, spaceBefore=1, spaceAfter=5))
    
    # Policy Schedule Heading
    story.append(Paragraph("POLICY SCHEDULE — ICICI LOMBARD COMPLETE HEALTH INSURANCE (HEALTH SHIELD PLUS)", styles['SectionHeading']))
    
    schedule_data = [
        [
            Paragraph("<b>Policy Number:</b>", styles['MetaLabel']),
            Paragraph("4015/iH/98421045/00/000", styles['MetaVal']),
            Paragraph("<b>Issuing Branch:</b>", styles['MetaLabel']),
            Paragraph("Chennai Mount Road Branch (4015)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Insured Name:</b>", styles['MetaLabel']),
            Paragraph("Dr. Suniti Mukherjee", styles['MetaVal']),
            Paragraph("<b>Proposer / Insured:</b>", styles['MetaLabel']),
            Paragraph("Self (Adult, 63 Years, Female)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Current Policy Period:</b>", styles['MetaLabel']),
            Paragraph("12-May-2026 to 11-May-2027", styles['MetaVal']),
            Paragraph("<b>Initial Inception Date:</b>", styles['MetaLabel']),
            Paragraph("15-May-2018 (Continuous Tenure: 99 Months)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Previous Insurer / Policy:</b>", styles['MetaLabel']),
            Paragraph("Star Health & Allied Insurance (2018-2022)", styles['MetaVal']),
            Paragraph("<b>Portability Continuity:</b>", styles['MetaLabel']),
            Paragraph("Granted with 48 Months Prior Credit", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Base Sum Insured:</b>", styles['MetaLabel']),
            Paragraph("Rs. 10,00,000.00", styles['MetaVal']),
            Paragraph("<b>Accrued Cumulative Bonus:</b>", styles['MetaLabel']),
            Paragraph("Rs. 5,00,000.00 (50% No Claim Bonus)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Total Effective Sum Insured:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 15,00,000.00</b>", styles['TableCellBold']),
            Paragraph("<b>Co-Payment / Deductible:</b>", styles['MetaLabel']),
            Paragraph("Nil Co-pay | Nil Voluntary Deductible", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Room Rent Eligibility:</b>", styles['MetaLabel']),
            Paragraph("<b>Single Private A/C Room (No Capping)</b>", styles['TableCellBold']),
            Paragraph("<b>ICU Entitlement:</b>", styles['MetaLabel']),
            Paragraph("No Capping / Actual Incurred", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Appointed TPA:</b>", styles['MetaLabel']),
            Paragraph("Medi Assist Insurance TPA Pvt. Ltd.", styles['MetaVal']),
            Paragraph("<b>Claim Grievance URL:</b>", styles['MetaLabel']),
            Paragraph("https://www.icicilombard.com/grievance", styles['TableCellSmall'])
        ]
    ]
    sched_table = Table(schedule_data, colWidths=[125, 140, 125, 133])
    sched_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF9F7")),
        ('BOX', (0,0), (-1,-1), 0.5, orange),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F0D6CB")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(sched_table)
    story.append(Spacer(1, 6))
    
    # Policy Terms & Conditions (Page 1)
    story.append(Paragraph("RELEVANT OPERATIVE POLICY CLAUSES & ENDORSEMENTS (SECTION 1)", styles['SectionHeading']))
    
    clauses_p1 = [
        Paragraph("<b>Clause 1.1 Inpatient Hospitalization Medical Expenses:</b> The Company shall indemnify reasonable and customary charges incurred for Medically Necessary inpatient treatment resulting from Illness or Accidental Bodily Injury, up to the Total Effective Sum Insured (Base Sum Insured plus accrued Cumulative Bonus). Covered expenses include Room Rent, Nursing, Surgeon and Anaesthetist fees, Operation Theatre charges, Surgical Implants, and Medical Consumables.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 1.2 Room Category & Accommodation Entitlement:</b> The Insured Person is entitled to accommodation in a <b>Single Private A/C Room</b>. Where the Insured is admitted to a room category within this entitlement, NO proportionate reduction or room rent capping shall apply to Associated Medical Expenses. Proportionate deductions are strictly prohibited where the policyholder occupies a room category equal to or lower than the entitled room category.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 2.1 Cumulative Bonus (No Claim Bonus):</b> For each claim-free policy year, the Base Sum Insured shall be increased by 10% progressively, up to a maximum limit of 50%. The accrued Cumulative Bonus of Rs. 5,00,000.00 forms an integral part of the Total Sum Insured available for all indemnifiable hospitalization claims and applicable sub-limits.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 3.8 Modern Treatment Methods & Advanced Robotic Technologies:</b> In accordance with IRDAI Guidelines on Standardization of Modern Treatment Methods (Ref: IRDAI/HLT/REG/CIR/193/11/2019), the Company indemnifies procedures involving Robotic Surgeries, Computer-Navigated Orthopedic Systems, and Deep Brain Stimulation. Coverage for Modern Treatment Methods is provided up to <b>50% of Sum Insured</b> per policy year.", styles['ClauseBody']),
    ]
    story.extend(clauses_p1)
    
    # Page Break to Page 2
    story.append(PageBreak())
    
    # Page 2 Header
    story.append(Paragraph("ICICI LOMBARD COMPLETE HEALTH INSURANCE — POLICY CLAUSES (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("Policy No: 4015/iH/98421045/00/000 | Insured: Dr. Suniti Mukherjee | UIN: ICIHLIP21383V052021", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=orange, spaceBefore=1, spaceAfter=5))
    
    story.append(Paragraph("STATUTORY PORTABILITY & EXCLUSION CLAUSES (SECTION 2)", styles['SectionHeading']))
    
    clauses_p2 = [
        Paragraph("<b>Clause 4.1 Pre-Existing Disease (PED) Waiting Period:</b> All Pre-Existing Diseases declared by the Insured at initial proposal shall be covered after thirty-six (36) consecutive months of continuous coverage from the date of initial policy inception. Where continuous coverage exceeds sixty (60) continuous months across renewals and ported policies, the Moratorium Period shall apply in full.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 4.3 Portability Continuity & Credit Transfer:</b> Under IRDAI (Health Insurance) Regulations, 2016 (Regulation 17) and IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter IV), the Insured is granted full continuity credit for waiting periods, cumulative bonus, and moratorium accrued under prior health insurance policies. Continuous tenure earned with Star Health Insurance (48 months from 15-May-2018 to 11-May-2022) is irrevocably credited towards the 60-Month Moratorium Period under this policy.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 5.1 Statutory 60-Month Moratorium Period:</b> Per IRDAI Master Circular (29 May 2024, Chapter V, Para 5.3): After sixty (60) continuous months of coverage under health insurance policies, including porting continuity credit, no claim shall be contestable, repudiated, or subjected to pre-existing disease disallowance, except in the event of proven established fraud. All medical complications arising from declared or latent comorbidities are unconditionally payable once the 60-month moratorium is completed.", styles['ClauseBody']),
        Spacer(1, 3),
        Paragraph("<b>Clause 6.2 Medical Consumables & Non-Payable Items Schedule:</b> Admissibility of consumables and surgical disposables is governed by IRDAI Guidelines on Standardization in Health Insurance (Annexure A, Lists I, II, III, and IV). Items categorized under List I (Non-Medical Disposables) are excluded. However, items categorized under <b>List III (Items for which coverage is not excluded and cost is payable if related to treatment/surgery)</b>, including intra-operative biological hemostatic agents, wound sealants, specialized infusion sets, and post-operative pain infusion pumps, are STATUTORILY PAYABLE when utilized during inpatient operative surgery.", styles['ClauseBody']),
    ]
    story.extend(clauses_p2)
    story.append(Spacer(1, 10))
    
    # Statutory Certification Box
    cert_data = [
        [
            Paragraph("<b>IRDAI STATUTORY POLICY ENDORSEMENT</b><br/>This policy schedule embodies the complete contract between ICICI Lombard General Insurance Co. Ltd. and Dr. Suniti Mukherjee. The policy is certified compliant with the Insurance Regulatory and Development Authority of India (Protection of Policyholders' Interests) Regulations, 2017, and the Master Circular on Health Insurance Business dated 29 May 2024. All claims must be settled strictly in adherence to these binding statutory standards.", styles['CalloutText'])
        ]
    ]
    cert_table = Table(cert_data, colWidths=[523])
    cert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7F2EF")),
        ('BOX', (0,0), (-1,-1), 1, orange),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(cert_table)
    story.append(Spacer(1, 16))
    
    auth_data = [
        [
            Paragraph("Branch Operations:<br/><b>Underwriting Officer</b><br/>ICICI Lombard Chennai", styles['TableCellSmall']),
            Paragraph("Customer Support:<br/><b>Grievance Officer</b><br/>gro@icicilombard.com", styles['TableCellSmall']),
            Paragraph("Authorized Signatory:<br/><b>Head - Underwriting & Claims</b><br/>ICICI Lombard General Insurance Co. Ltd.", styles['TableCellSmall'])
        ]
    ]
    auth_table = Table(auth_data, colWidths=[174, 174, 175])
    auth_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(auth_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated ICICI Lombard Policy: {pdf_path}")


# ==============================================================================
# DOCUMENT 3: MEDI ASSIST TPA SETTLEMENT & DEDUCTION ADVICE
# ==============================================================================

def generate_mediassist_rejection_letter(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=40
    )
    story = []
    red = colors.HexColor("#A31D1D")
    dark = colors.HexColor("#222222")
    
    # Header Banner
    story.append(Paragraph("MEDI ASSIST INSURANCE TPA PRIVATE LIMITED", styles['DocTitle']))
    story.append(Paragraph("Tower D, 4th Floor, IBC Knowledge Park, 4/1, Bannerghatta Main Road, Bengaluru - 560029, Karnataka<br/>IRDAI TPA License No. 003 | CIN: U85199KA1999PTC025676 | Claim Helpline: 1800 425 9449 | claims@mediassist.in", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=red, spaceBefore=1, spaceAfter=5))
    
    # Settlement Advice Title
    story.append(Paragraph("FORMAL CLAIM SETTLEMENT & ADJUDICATION DISALLOWANCE VOUCHER", styles['SectionHeadingRed']))
    story.append(Paragraph("Confidential Claim Assessment Record — Statutory Communication under Insurance Ombudsman Rules", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    
    # Claim Reference Metadata
    claim_meta = [
        [
            Paragraph("<b>Claim Reference No (CCN):</b>", styles['MetaLabel']),
            Paragraph("<b>MED/2026/ICICI/8492015</b>", styles['TableCellBold']),
            Paragraph("<b>Date of Settlement:</b>", styles['MetaLabel']),
            Paragraph("25-Aug-2026", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Insurer Name:</b>", styles['MetaLabel']),
            Paragraph("ICICI Lombard General Insurance Co. Ltd.", styles['MetaVal']),
            Paragraph("<b>Policy Number:</b>", styles['MetaLabel']),
            Paragraph("4015/iH/98421045/00/000", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Patient Name:</b>", styles['MetaLabel']),
            Paragraph("Dr. Suniti Mukherjee", styles['MetaVal']),
            Paragraph("<b>Hospital Name:</b>", styles['MetaLabel']),
            Paragraph("Apollo Hospitals, Greams Road, Chennai", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Hospital IP / Bill No:</b>", styles['MetaLabel']),
            Paragraph("AP/2026/094182 / FB/2026/CH/119041", styles['MetaVal']),
            Paragraph("<b>Date of Admission/Discharge:</b>", styles['MetaLabel']),
            Paragraph("14-Aug-2026 to 19-Aug-2026 (5 Days)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Total Claim Billed:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 11,68,500.00</b>", styles['TableCellBold']),
            Paragraph("<b>Total Approved / Paid:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 4,80,000.00</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Total Disallowed / Deducted:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 6,88,500.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>Adjudication Status:</b>", styles['MetaLabel']),
            Paragraph("<font color='#A31D1D'><b>PARTIALLY SETTLED (HAIRCUT: 58.9%)</b></font>", styles['TableCell'])
        ]
    ]
    meta_tab = Table(claim_meta, colWidths=[130, 140, 125, 128])
    meta_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF3F2")),
        ('BOX', (0,0), (-1,-1), 0.5, red),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F2CECC")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(meta_tab)
    story.append(Spacer(1, 6))
    
    # Disallowance Table
    story.append(Paragraph("SCHEDULE OF REJECTIONS, DISALLOWANCES & STATUTORY REASONING (PAGE 1)", styles['SectionHeadingRed']))
    
    disallow_headers = [
        Paragraph("<b>Disallowance Head & Stated Insurer Reasoning</b>", styles['TableHead']),
        Paragraph("<b>Policy / Circular Citation</b>", styles['TableHead']),
        Paragraph("<b>Billed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Disallowed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Approved (Rs.)</b>", styles['TableHead'])
    ]
    
    disallow_rows_p1 = [
        disallow_headers,
        [
            Paragraph("<b>1. Robotic Surgery & Navigational Suite Sub-Limit Capping</b><br/>The patient underwent bilateral knee arthroplasty using Mako Robotic navigation suite (Rs. 2,50,000.00). Under Clause 3.8, Modern Treatment Methods are sub-limited to 50% of the Base Sum Insured (50% of Rs. 10,00,000 = Rs. 5,00,000.00). Total robotic suite, implants (Rs. 3.6L) and OT charges exceeded this sub-limit. Hence, the Mako Robotic Navigation Suite Fee of Rs. 2,50,000.00 is disallowed in excess of sub-limit.", styles['TableCell']),
            Paragraph("Clause 3.8 Modern Treatments (Capped at 50% of Base Sum Insured)", styles['TableCellSmall']),
            Paragraph("2,50,000.00", styles['TableCellRight']),
            Paragraph("2,50,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>2. Pre-Existing Diabetic Comorbidity Repudiation (Moratorium Reset)</b><br/>Hospital billed specialized diabetic and cardio-renal monitoring regimen (Rs. 1,75,000.00). Inception with ICICI Lombard was 12-May-2022 (48 continuous months elapsed). Moratorium under IRDAI 2024 Chapter V Para 5.3 mandates 60 continuous months with the company. Ported prior tenure cannot override internal underwritten waiting periods for pre-existing diseases. Hence, comorbid management is repudiated under PED Exclusion 4.1.", styles['TableCell']),
            Paragraph("Clause 4.1 PED Exclusion & IRDAI Moratorium Period (60 Months tenure shortfall)", styles['TableCellSmall']),
            Paragraph("1,75,000.00", styles['TableCellRight']),
            Paragraph("1,75,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>3. Synthetic Room Rent Benchmark & Proportionate Deduction</b><br/>Hospital billed Rs. 9,000/day for Single Standard Room. PPN empanelment tariff benchmark rate for network hospitals is Rs. 5,000/day for Twin Sharing. An excess room rent deduction of Rs. 12,000 plus proportionate deduction of 44.4% applied across Associated Medical Expenses (Surgeon Fee Rs. 1,85,000 + Nursing Rs. 18,500 + Anesthesia) totaling Rs. 1,77,000.00 as per PPN agreed tariff.", styles['TableCell']),
            Paragraph("PPN Network Empanelment Tariff Schedule & Proportionate Deduction Formula", styles['TableCellSmall']),
            Paragraph("2,20,500.00", styles['TableCellRight']),
            Paragraph("1,77,000.00", styles['TableCellRightBold']),
            Paragraph("43,500.00", styles['TableCellRight'])
        ]
    ]
    
    t_dis1 = Table(disallow_rows_p1, colWidths=[205, 120, 66, 66, 66])
    t_dis1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), red),
        ('BOX', (0,0), (-1,-1), 0.5, red),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FCF7F7")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_dis1)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Page 1 Disallowances Sub-total: Rs. 6,02,000.00</b>", styles['TableCellRightBold']))
    
    # Page Break to Page 2
    story.append(PageBreak())
    
    # Page 2 Header
    story.append(Paragraph("MEDI ASSIST INSURANCE TPA PRIVATE LIMITED — SETTLEMENT ADVICE (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("CCN: MED/2026/ICICI/8492015 | Policy: 4015/iH/98421045/00/000 | Patient: Dr. Suniti Mukherjee", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=red, spaceBefore=1, spaceAfter=5))
    
    story.append(Paragraph("SCHEDULE OF REJECTIONS & DISALLOWANCES (PART 2)", styles['SectionHeadingRed']))
    
    disallow_rows_p2 = [
        disallow_headers,
        [
            Paragraph("<b>4. Biological Hemostatic Flowable Matrix Disallowance (Floseal)</b><br/>Hospital billed Floseal Hemostatic Flowable Matrix (Rs. 48,000.00) used for vascular hemostasis. Classified as non-payable surgical consumable gel under IRDAI Standardization Guidelines Annexure A List I Entry 42 (Gels, pasty sealants, and surgical dressing aids).", styles['TableCell']),
            Paragraph("IRDAI Standardization Guidelines Annexure A List I Entry 42", styles['TableCellSmall']),
            Paragraph("48,000.00", styles['TableCellRight']),
            Paragraph("48,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>5. Elastomeric PCA Pain Pump System Disallowance</b><br/>Hospital billed continuous infusion Patient Controlled Analgesia (PCA) pain pump (Rs. 32,000.00). Classified as non-medical patient comfort disposables under List I Entry 48.", styles['TableCell']),
            Paragraph("IRDAI Standardization Guidelines Annexure A List I Entry 48", styles['TableCellSmall']),
            Paragraph("32,000.00", styles['TableCellRight']),
            Paragraph("32,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>6. Non-Medical Comfort & Attendant Charges (Legitimate Exclusion)</b><br/>Attendant food & therapeutic service (Rs. 4,200), Vanity kit (Rs. 1,300), Registration handling (Rs. 1,000) are non-medical expenses excluded under List I.", styles['TableCell']),
            Paragraph("IRDAI Annexure A List I Items 18, 44 & 68", styles['TableCellSmall']),
            Paragraph("6,500.00", styles['TableCellRight']),
            Paragraph("6,500.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>7. Admitted Surgical Implants & Inpatient Stay (Paid Heads)</b><br/>Admitted Stryker Triathlon Knee Components, modular baseplates, ICU charges, and residual surgeon fees approved within tariff guidelines.", styles['TableCell']),
            Paragraph("Clause 1.1 Inpatient Medical Expenses (Admissible Heads)", styles['TableCellSmall']),
            Paragraph("4,80,000.00", styles['TableCellRight']),
            Paragraph("0.00", styles['TableCellRightBold']),
            Paragraph("4,80,000.00", styles['TableCellRightBold'])
        ]
    ]
    
    t_dis2 = Table(disallow_rows_p2, colWidths=[205, 120, 66, 66, 66])
    t_dis2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), red),
        ('BOX', (0,0), (-1,-1), 0.5, red),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FCF7F7")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_dis2)
    story.append(Spacer(1, 6))
    
    # Master Reconciliation Table
    recon_data = [
        [
            Paragraph("<b>TOTAL CLAIM BILLED AMOUNT:</b>", styles['TableCellBold']),
            Paragraph("Rs. 11,68,500.00", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>TOTAL DISALLOWED / DEDUCTED AMOUNT:</b>", styles['TableCellBold']),
            Paragraph("Rs. 6,88,500.00", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>NET APPROVED & TRANSMITTED AMOUNT (NEFT/RTGS):</b>", styles['TableCellBold']),
            Paragraph("<font color='#0A4D68'><b>Rs. 4,80,000.00</b></font>", styles['TableCellRightBold'])
        ]
    ]
    recon_tab = Table(recon_data, colWidths=[380, 143])
    recon_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDECEC")),
        ('BOX', (0,0), (-1,-1), 1, red),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5BABA")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(recon_tab)
    story.append(Spacer(1, 8))
    
    # Grievance & Ombudsman Right Box
    ombuds_data = [
        [
            Paragraph("<b>STATUTORY NOTICE OF GRIEVANCE REDRESSAL & OMBUDSMAN JURISDICTION:</b><br/>If you are dissatisfied with this claim determination, you have the statutory right under Insurance Ombudsman Rules, 2017 to approach the Grievance Redressal Officer (GRO) of ICICI Lombard at gro@icicilombard.com. If unresolved within 30 days, an appeal lies before the <b>Office of the Insurance Ombudsman, Fatima Akhtar Court, 4th Floor, 453, Anna Salai, Teynampet, Chennai - 600018</b> (Email: bimalokpal.chennai@cioins.co.in | Phone: 044-24333668) having territorial jurisdiction over Tamil Nadu and Puducherry.", styles['CalloutText'])
        ]
    ]
    ombuds_tab = Table(ombuds_data, colWidths=[523])
    ombuds_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF8F7")),
        ('BOX', (0,0), (-1,-1), 1, red),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(ombuds_tab)
    story.append(Spacer(1, 14))
    
    # Signatures
    tpa_sig = [
        [
            Paragraph("Adjudicated by:<br/><b>Medical Claims Assessor</b><br/>Medi Assist TPA Pvt. Ltd.", styles['TableCellSmall']),
            Paragraph("Reviewed by:<br/><b>Chief Medical Auditor</b><br/>Technical Claims Division", styles['TableCellSmall']),
            Paragraph("Authorized Signatory:<br/><b>Head - Claims Settlement & Disallowances</b><br/>Medi Assist Insurance TPA Pvt. Ltd.", styles['TableCellSmall'])
        ]
    ]
    tpa_sig_tab = Table(tpa_sig, colWidths=[174, 174, 175])
    tpa_sig_tab.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tpa_sig_tab)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Medi Assist Rejection Letter: {pdf_path}")


def main():
    target_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\test_docs\hyper_adversarial_claim_case"
    os.makedirs(target_dir, exist_ok=True)
    
    bill_pdf = os.path.join(target_dir, "apollo_hospital_bill.pdf")
    policy_pdf = os.path.join(target_dir, "icici_lombard_policy.pdf")
    rejection_pdf = os.path.join(target_dir, "mediassist_rejection_letter.pdf")
    
    print("Generating Hyper-Adversarial Documents...")
    generate_apollo_hospital_bill(bill_pdf)
    generate_icici_lombard_policy(policy_pdf)
    generate_mediassist_rejection_letter(rejection_pdf)
    
    # Also render high-res PNG pages using pymupdf for direct visual inspection
    for pdf_path in [bill_pdf, policy_pdf, rejection_pdf]:
        doc = pymupdf.open(pdf_path)
        base = os.path.splitext(pdf_path)[0]
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_path = f"{base}_p{i+1}.png"
            pix.save(img_path)
            print(f"Rendered {img_path}")
            
    print("\nGeneration completed successfully!")


if __name__ == "__main__":
    main()
