"""
Ultra-Hard Complex Claim Documents Generator for ClaimGuard AI.

Creates 3 ultra-realistic, legally deceptive Indian health insurance documents:
1. Max Super Speciality Hospital (Saket, New Delhi) - 2-page Inpatient Final Bill
   - ERCP + Laparoscopic to Open Cholecystectomy Conversion for Gangrenous Acute Cholecystitis & Choledocholithiasis
   - 32 itemized line items exactly summing to Rs. 7,85,600.00
2. Care Health Insurance (Care Supreme / Optima Secure) - 2-page Policy Schedule & Clauses
   - Policy Inception: 15-Jan-2020 (73 continuous months)
   - Base SI: Rs. 8,00,000 + Cumulative Bonus: Rs. 4,00,000 = Total Rs. 12,00,000
   - Grace period renewal on 28-Jan-2025 (13-day delay within 30-day statutory grace window)
   - Clause 3.4 (Multiple Surgeries), Clause 4.14 (Modern Treatment sub-limit), Clause 6.1 (CB rules)
3. Vidal Health TPA - 2-page Deduction & Settlement Advice Letter
   - Approved: Rs. 3,38,100.00 | Disallowed: Rs. 4,47,500.00
   - 5 deeply disguised subtle flaws that deceive humans, TPA auditors, and aggregators:
     1. Multi-Surgery 50% Rule Spillover onto OT, C-Arm Fluoroscopy & Consumables
     2. Inpatient Modern Treatment / Endoscopy Carve-Out Sub-Limit Capping
     3. Grace Period Renewal Cumulative Bonus Arbitrary Erasure (Rs. 4L bonus wiped)
     4. Surgical Sepsis Glycemic Protocol Repudiated as "Routine Lifestyle / Metabolic Maintenance"
     5. Advanced Ultrasonic / Bipolar Vessel Sealing Disallowed as "List I Non-Payable Knives"
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
    
    navy = colors.HexColor("#082040")
    crimson = colors.HexColor("#990000")
    dark_gray = colors.HexColor("#222222")
    
    styles.add(ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=navy, alignment=1))
    styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10.5, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=navy, spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle('SectionHeadingRed', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=crimson, spaceBefore=4, spaceAfter=3))
    
    styles.add(ParagraphStyle('TableHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('TableCellRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    
    styles.add(ParagraphStyle('LegalClauseTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=navy, spaceBefore=3, spaceAfter=1))
    styles.add(ParagraphStyle('LegalClause', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9.5, textColor=dark_gray, spaceBefore=1, spaceAfter=2.5))
    styles.add(ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle('FooterDisclaimer', parent=styles['Normal'], fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#555555")))
    
    return styles


# ==============================================================================
# 1. HOSPITAL BILL GENERATOR (Max Super Speciality Hospital, Saket, New Delhi)
# ==============================================================================

def generate_max_hospital_bill(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    styles = get_custom_styles()
    story = []

    # --- PAGE 1: Header, Demographics, Clinical Summary & Line Items 1-16 ---
    h_text = (
        "<b>MAX SUPER SPECIALITY HOSPITAL</b><br/>"
        "<font size='7'>1, 2, Press Enclave Road, Mandir Marg, Saket, New Delhi - 110017<br/>"
        "NABH & JCI Accredited | GSTIN: 07AAACM3291P1ZX | CIN: U74899DL2001PLC111071<br/>"
        "Phone: +91-11-2651-5050 | Email: billing.saket@maxhealthcare.com</font>"
    )
    inv_text = (
        "<font size='11' color='#082040'><b>INPATIENT FINAL TAX INVOICE</b></font><br/>"
        "<font size='7.5'>Bill No: <b>MAX/SKT/IPB/2026/10492</b><br/>"
        "Invoice Date: <b>11-Mar-2026 15:30</b><br/>"
        "Tariff Type: <b>NABH Corporate / TPA Schedule</b></font>"
    )
    t_head = Table([[Paragraph(h_text, styles['TableCell']), Paragraph(inv_text, styles['TableCellRight'])]], colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#082040")),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))

    pat_data = [
        [
            Paragraph("<b>Patient Name:</b> Mrs. Rajeshwari Sundaram", styles['TableCell']),
            Paragraph("<b>Max MRN / UHID:</b> SKBR.000481920", styles['TableCell']),
            Paragraph("<b>Age / Gender:</b> 58 Y / Female", styles['TableCell']),
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP-SKT-2026-88192", styles['TableCell']),
            Paragraph("<b>Admission:</b> 04-Mar-2026 04:15 AM (Emergency ER)", styles['TableCell']),
            Paragraph("<b>Discharge:</b> 11-Mar-2026 14:00 PM (7 Days)", styles['TableCell']),
        ],
        [
            Paragraph("<b>Chief Consultant:</b> Dr. Pradeep Chowbey, MS, MNAMS (GI Surgery)", styles['TableCell']),
            Paragraph("<b>Consultant Gastroenterologist:</b> Dr. Rajesh Upadhyay, MD, DM", styles['TableCell']),
            Paragraph("<b>Room Entitlement:</b> Single Private A/C Room", styles['TableCell']),
        ],
        [
            Paragraph("<b>Clinical Diagnosis:</b> Acute Gangrenous Cholecystitis with Choledocholithiasis, Biliary Pancreatitis & Severe Sepsis", styles['TableCell']),
            Paragraph("<b>Surgical Procedures Performed:</b> 1. Emergency Therapeutic ERCP + Sphincterotomy + Stone Extraction (04-Mar)<br/>2. Laparoscopic Converted to Open Exploratory Laparotomy, Cholecystectomy & T-Tube Choledochostomy (05-Mar)", styles['TableCell']),
            Paragraph("<b>Insurer / TPA:</b> Care Health Ins. / Vidal Health TPA", styles['TableCell']),
        ]
    ]
    t_pat = Table(pat_data, colWidths=[175, 205, 143])
    t_pat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F6F9FD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#A8C0DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D8E4F2")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_pat)
    story.append(Spacer(1, 4))

    er_cert = [
        [Paragraph("<b>EMERGENCY MULTI-STAGE SURGICAL TRIAGE CERTIFICATE:</b><br/>"
                   "Patient admitted at 04:15 AM in severe septic shock (BP 80/50, Total Bilirubin 8.4 mg/dL, Amylase 1420 U/L) secondary to impacted common bile duct stone. "
                   "Immediate emergent ERCP papillotomy was conducted to decompress the infected biliary tree on 04-Mar-2026. Subsequent persistent fever and peritonism warranted "
                   "emergency cholecystectomy on 05-Mar-2026; due to intense Calot's frozen triangle fibrosis and gangrene, laparoscopic conversion to open laparotomy was performed. "
                   "Both interventions constituted consecutive life-safety emergency steps of an indivisible inpatient admission.", styles['CalloutText'])]
    ]
    t_er = Table(er_cert, colWidths=[523])
    t_er.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF8EE")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2B070")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_er)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN - PART I (PROCEDURES, ICU & ACCOMMODATION)</b>", styles['SectionHeading']))

    items_p1 = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Line Item Description</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>SAC Code</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
        ],
        # 1-3 Accommodation
        [Paragraph("1", styles['TableCellCenter']), Paragraph("Surgical ICU Bed Charges (Intensive Monitoring Bed)", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("16,000.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("48,000.00", styles['TableCellRightBold'])],
        [Paragraph("2", styles['TableCellCenter']), Paragraph("SICU Dedicated Critical Care Nursing Care (1:1 Nurse Ratio)", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("4,500.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("13,500.00", styles['TableCellRightBold'])],
        [Paragraph("3", styles['TableCellCenter']), Paragraph("Single Private Deluxe A/C Room Bed Charges (Bed #508)", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("4", styles['TableCellCenter']), Paragraph("9,000.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("36,000.00", styles['TableCellRightBold'])],
        [Paragraph("4", styles['TableCellCenter']), Paragraph("Inpatient Ward General Nursing & Clinical Monitoring", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("4", styles['TableCellCenter']), Paragraph("2,500.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("10,000.00", styles['TableCellRightBold'])],
        # 5-8 Procedure 1 (ERCP)
        [Paragraph("5", styles['TableCellCenter']), Paragraph("Therapeutic ERCP Operative Fee (Consultant Gastroenterologist)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("35,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("35,000.00", styles['TableCellRightBold'])],
        [Paragraph("6", styles['TableCellCenter']), Paragraph("Advanced Endoscopy / Fluoroscopy Suite Facility Charges", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("22,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("22,000.00", styles['TableCellRightBold'])],
        [Paragraph("7", styles['TableCellCenter']), Paragraph("Digital C-Arm Fluoroscopy Real-Time X-Ray Guidance Suite", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("12,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("12,000.00", styles['TableCellRightBold'])],
        [Paragraph("8", styles['TableCellCenter']), Paragraph("Dormia Stone Extraction Basket & Wire-Guided Sphincterotome Kit", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("32,000.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("32,000.00", styles['TableCellRightBold'])],
        # 9-16 Procedure 2 (Open Laparotomy)
        [Paragraph("9", styles['TableCellCenter']), Paragraph("Chief Surgeon Operative Fee - Laparotomy & Cholecystectomy", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("94,500.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("94,500.00", styles['TableCellRightBold'])],
        [Paragraph("10", styles['TableCellCenter']), Paragraph("Senior Co-Surgeon / Assistant GI Surgeon Professional Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("30,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("30,000.00", styles['TableCellRightBold'])],
        [Paragraph("11", styles['TableCellCenter']), Paragraph("Senior Consultant Anaesthesiologist Charge (Major Laparotomy 5 Hrs)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("38,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("38,000.00", styles['TableCellRightBold'])],
        [Paragraph("12", styles['TableCellCenter']), Paragraph("Major Ultra-Clean Laminar Flow OT Complex Infrastructure", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("55,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("55,000.00", styles['TableCellRightBold'])],
        [Paragraph("13", styles['TableCellCenter']), Paragraph("Advanced Anaesthesia Workstation & BIS Brain State Monitoring", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("20,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("20,000.00", styles['TableCellRightBold'])],
        [Paragraph("14", styles['TableCellCenter']), Paragraph("Ethicon Harmonic ACE+ 36cm Ultrasonic Cutting & Coagulation Shears", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("48,000.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("48,000.00", styles['TableCellRightBold'])],
        [Paragraph("15", styles['TableCellCenter']), Paragraph("LigaSure Blunt Tip Laparoscopic Radiofrequency Vessel Sealing Device", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("38,000.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("38,000.00", styles['TableCellRightBold'])],
        [Paragraph("16", styles['TableCellCenter']), Paragraph("Silicone T-Tube Biliary Decompression Drain System Kit", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("14,500.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("14,500.00", styles['TableCellRightBold'])],
    ]

    t_p1 = Table(items_p1, colWidths=[18, 247, 70, 25, 55, 45, 63])
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#082040")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
    ]))
    for row_idx in range(1, len(items_p1)):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 1 else colors.HexColor("#F8FAFD")
        t_p1.setStyle(TableStyle([('BACKGROUND', (0, row_idx), (-1, row_idx), bg)]))
    story.append(t_p1)

    story.append(PageBreak())

    # --- PAGE 2: Items 17-32, Sepsis Care, Pharmacy, Diagnostics & Summary ---
    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN - PART II (SEPSIS PROTOCOL, PHARMACY & DIAGNOSTICS)</b>", styles['SectionHeading']))

    items_p2 = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Line Item Description</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>SAC Code</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
        ],
        # 17-20 Consumables List III
        [Paragraph("17", styles['TableCellCenter']), Paragraph("Laparotomy Major Surgical Sterile Drape Pack & Gowns (List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("9,500.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("9,500.00", styles['TableCellRightBold'])],
        [Paragraph("18", styles['TableCellCenter']), Paragraph("Sterile Powder-Free Latex Surgical Gloves (Size 7.0/7.5 - List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("14", styles['TableCellCenter']), Paragraph("350.00", styles['TableCellRight']), Paragraph("401511", styles['TableCellCenter']), Paragraph("4,900.00", styles['TableCellRightBold'])],
        [Paragraph("19", styles['TableCellCenter']), Paragraph("Abdominal Yankauer Suction Cannula & Hi-Vacuum Tubing Set", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("4,200.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("4,200.00", styles['TableCellRightBold'])],
        [Paragraph("20", styles['TableCellCenter']), Paragraph("Antibacterial Monocryl & PDS Loop Suture Materials (List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("11,000.00", styles['TableCellRight']), Paragraph("300610", styles['TableCellCenter']), Paragraph("11,000.00", styles['TableCellRightBold'])],
        # 21-24 Glycemic & Sepsis Care Protocol
        [Paragraph("21", styles['TableCellCenter']), Paragraph("Senior Consultant Endocrinologist ICU Management (Sepsis Glycemia)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("6,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRightBold'])],
        [Paragraph("22", styles['TableCellCenter']), Paragraph("Continuous IV Regular Insulin Infusion Protocol & Syringe Driver (3 Days)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("4,500.00", styles['TableCellRight']), Paragraph("300431", styles['TableCellCenter']), Paragraph("13,500.00", styles['TableCellRightBold'])],
        [Paragraph("23", styles['TableCellCenter']), Paragraph("Intensive Point-of-Care Arterial Blood Gas (ABG) & Lactate Series", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("6", styles['TableCellCenter']), Paragraph("2,400.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("14,400.00", styles['TableCellRightBold'])],
        [Paragraph("24", styles['TableCellCenter']), Paragraph("Continuous Glycemic Glucose Strips & Biosensor Electrodes (List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("12,100.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("12,100.00", styles['TableCellRightBold'])],
        # 25-28 Pharmacy (Meropenem, Albumin, Supportive)
        [Paragraph("25", styles['TableCellCenter']), Paragraph("IV Meropenem 1g Infusion (T.I.D. x 7 Days - Biliary Sepsis)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("21", styles['TableCellCenter']), Paragraph("2,600.00", styles['TableCellRight']), Paragraph("300420", styles['TableCellCenter']), Paragraph("54,600.00", styles['TableCellRightBold'])],
        [Paragraph("26", styles['TableCellCenter']), Paragraph("IV Human Albumin 20% 100ml Infusion (Severe Septic Hypoalbuminemia)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("4", styles['TableCellCenter']), Paragraph("4,900.00", styles['TableCellRight']), Paragraph("300212", styles['TableCellCenter']), Paragraph("19,600.00", styles['TableCellRightBold'])],
        [Paragraph("27", styles['TableCellCenter']), Paragraph("IV Analgesics, Antiemetics, Pantoprazole & Heparin Prophylaxis", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("14,800.00", styles['TableCellRight']), Paragraph("300490", styles['TableCellCenter']), Paragraph("14,800.00", styles['TableCellRightBold'])],
        [Paragraph("28", styles['TableCellCenter']), Paragraph("Total Parenteral Nutrition (Kabiven Peri 1440ml Infusion)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("4,200.00", styles['TableCellRight']), Paragraph("300450", styles['TableCellCenter']), Paragraph("12,600.00", styles['TableCellRightBold'])],
        # 29-32 Diagnostics & Admin
        [Paragraph("29", styles['TableCellCenter']), Paragraph("Emergency Contrast Triple-Phase CT Abdomen & MRCP Pelvis", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("22,500.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("22,500.00", styles['TableCellRightBold'])],
        [Paragraph("30", styles['TableCellCenter']), Paragraph("Surgical Pathology - Gallbladder Resection & Liver Bed Biopsy", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("9,500.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("9,500.00", styles['TableCellRightBold'])],
        [Paragraph("31", styles['TableCellCenter']), Paragraph("Comprehensive Liver Function, Amylase, Lipase & Blood Cultures", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("14,400.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("14,400.00", styles['TableCellRightBold'])],
        [Paragraph("32", styles['TableCellCenter']), Paragraph("Inpatient Admission Registration, ID Wristband & Biomedical Handling Fee", styles['TableCell']), Paragraph("NON_MEDICAL", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("3,500.00", styles['TableCellRight']), Paragraph("999319", styles['TableCellCenter']), Paragraph("3,500.00", styles['TableCellRightBold'])],
    ]

    t_p2 = Table(items_p2, colWidths=[18, 247, 70, 25, 55, 45, 63])
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#082040")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
    ]))
    for row_idx in range(1, len(items_p2)):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 1 else colors.HexColor("#F8FAFD")
        t_p2.setStyle(TableStyle([('BACKGROUND', (0, row_idx), (-1, row_idx), bg)]))
    story.append(t_p2)
    story.append(Spacer(1, 6))

    # Bill Summary Ledger Table
    bill_summary = [
        [
            Paragraph("<b>BILL ARITHMETIC RECONCILIATION SUMMARY:</b><br/>"
                      "• Total Hospital Service Units: 32 Items<br/>"
                      "• Bed Category Entitlement: Single Private A/C Room (Rs. 9,000/day)<br/>"
                      "• Subtotal Part I (Procedures & ICU): Rs. 5,46,500.00<br/>"
                      "• Subtotal Part II (Consumables, Sepsis & Drugs): Rs. 2,39,100.00", styles['TableCellSmall']),
            Paragraph("<font size='8'>Total Bill Amount: <b>Rs. 7,85,600.00</b><br/>"
                      "Less Hospital Concession / TPA Discount: <b>Rs. 0.00 (Nil)</b><br/>"
                      "<font size='9' color='#082040'><b>TOTAL GROSS BILL: Rs. 7,85,600.00</b></font><br/>"
                      "Net Amount Due from Payer / TPA: <b>Rs. 7,85,600.00</b></font>", styles['TableCellRightBold'])
        ]
    ]
    t_sum = Table(bill_summary, colWidths=[310, 213])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4FA")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 10))

    b_sig = [
        [
            Paragraph("Prepared By:<br/><b>Sunil Narang</b><br/>Senior Inpatient Billing Officer", styles['TableCell']),
            Paragraph("Verified By:<br/><b>Dr. Anita Sahni, MHA</b><br/>Medical Superintendent", styles['TableCell']),
            Paragraph("For Max Super Speciality Hospital (Saket)<br/><br/><b>Authorized Signatory & Seal</b>", styles['TableCellRight'])
        ]
    ]
    t_bsig = Table(b_sig, colWidths=[174, 174, 175])
    story.append(t_bsig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


# ==============================================================================
# 2. INSURANCE POLICY GENERATOR (Care Health Insurance - Care Supreme Policy)
# ==============================================================================

def generate_care_supreme_policy(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    styles = get_custom_styles()
    story = []

    # --- PAGE 1: Header, Policy Schedule & Key Conditions ---
    p_head = [
        [
            Paragraph("<b>CARE HEALTH INSURANCE LIMITED</b><br/>"
                      "<font size='7'>Regd. Office: 5th Floor, 19 Chawla House, Nehru Place, New Delhi - 110019<br/>"
                      "IRDAI Regn No: 148 | CIN: U66000DL2007PLC161503 | Toll-Free: 1800-102-4488<br/>"
                      "UIN: CHIHLIP23089V032223 | Product Name: <b>CARE SUPREME (POLICY SCHEDULE)</b></font>", styles['TableCell']),
            Paragraph("<font size='11' color='#082040'><b>POLICY CERTIFICATE</b></font><br/>"
                      "<font size='7.5'>Policy No: <b>11/2020/CARE/998231</b><br/>"
                      "Policy Inception Date: <b>15-Jan-2020</b><br/>"
                      "Cumulative Continuity: <b>73 Continuous Months</b></font>", styles['TableCellRight'])
        ]
    ]
    t_head = Table(p_head, colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#082040")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))

    sched_data = [
        [
            Paragraph("<b>Policyholder / Primary Insured:</b> Mrs. Rajeshwari Sundaram", styles['TableCell']),
            Paragraph("<b>Customer ID / UHID:</b> CARE-DEL-889102", styles['TableCell']),
            Paragraph("<b>Age / Gender:</b> 58 Y / Female", styles['TableCell']),
        ],
        [
            Paragraph("<b>Current Policy Period:</b> 28-Jan-2026 to 27-Jan-2027", styles['TableCell']),
            Paragraph("<b>Policy Renewal Due Date:</b> 15-Jan-2026", styles['TableCell']),
            Paragraph("<b>Grace Period Payment Date:</b> 28-Jan-2026 (Section 43)", styles['TableCell']),
        ],
        [
            Paragraph("<b>Base Sum Insured:</b> Rs. 8,00,000.00", styles['TableCell']),
            Paragraph("<b>Accrued Cumulative Bonus:</b> Rs. 4,00,000.00 (50%)", styles['TableCell']),
            Paragraph("<b>Total Effective Coverage:</b> Rs. 12,00,000.00", styles['TableCellBold']),
        ],
        [
            Paragraph("<b>Room Entitlement & Rent Limit:</b> Single Private A/C Room (No Sub-limit / No Capping)", styles['TableCell']),
            Paragraph("<b>Deductible:</b> Nil / Zero", styles['TableCell']),
            Paragraph("<b>Co-Payment:</b> Nil (0% across all ages)", styles['TableCell']),
        ],
        [
            Paragraph("<b>TPA Administration:</b> Vidal Health TPA Pvt. Ltd.", styles['TableCell']),
            Paragraph("<b>Disclosed Medical History:</b> Type 2 Diabetes (Since 2018 - Fully Disclosed)", styles['TableCell']),
            Paragraph("<b>Moratorium Status:</b> <b>Protected (>60 Months Active)</b>", styles['TableCellBold']),
        ]
    ]
    t_sched = Table(sched_data, colWidths=[185, 185, 153])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D8E4F2")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>STATUTORY TERMS, CONDITIONS & ENDORSEMENTS - PART I</b>", styles['SectionHeading']))

    p1_clauses = [
        ("CLAUSE 1.1 - INPATIENT HOSPITALIZATION INDEMNITY",
         "The Company shall indemnify medical expenses reasonably incurred by the Insured Person up to the Sum Insured plus Cumulative Bonus "
         "for Room Rent, Nursing, Surgeon fees, Anaesthetist fees, Operation Theatre, ICU, Medicines, and Specialized Medical Devices."),

        ("CLAUSE 2.3 - ROOM CATEGORY & PROPORTIONATE DEDUCTION APPLICABILITY",
         "The Insured Person is entitled to a <b>Single Private A/C Room with no capping</b>. No proportionate deduction shall apply to any claim "
         "where accommodation is in a Single Private A/C room or lower category. ICU/ICCU charges are indemnified in full with no room-linked restrictions."),

        ("CLAUSE 3.4 - MULTIPLE SURGICAL PROCEDURES IN A SINGLE HOSPITALIZATION",
         "Where two or more distinct surgical procedures are performed during the same hospitalization session, the <b>Surgeon's Professional Operative Fee</b> "
         "for the secondary procedure shall be reimbursed at <b>50% of the Surgeon's tariff</b>. <br/>"
         "<i>Statutory Construction Note:</i> This 50% discount applies solely to the Surgeon's fee and does not apply to hospital infrastructure, "
         "Operation Theatre charges, Anaesthesia charges, Fluoroscopy equipment, or physical single-use consumables."),

        ("CLAUSE 4.14 - MODERN TREATMENT METHODS & ADVANCED TECHNOLOGY",
         "Expenses incurred on modern treatments (including Balloon Sphaeroplasty, Robotic Surgery, and Advanced Endoscopic Interventions) are covered.<br/>"
         "Where modern procedures are performed as part of an emergency inpatient hospitalization for acute life-threatening medical conditions, "
         "they shall be indemnified as standard Inpatient Hospitalization under Clause 1.1 without standalone day-care sub-limit caps.")
    ]

    for title, content in p1_clauses:
        story.append(Paragraph(title, styles['LegalClauseTitle']))
        story.append(Paragraph(content, styles['LegalClause']))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # --- PAGE 2: Moratorium, Grace Period Continuity, Exclusions & Redressal ---
    story.append(Paragraph("<b>STATUTORY TERMS, CONDITIONS & ENDORSEMENTS - PART II</b>", styles['SectionHeading']))

    p2_clauses = [
        ("SECTION 5 - STATUTORY 60-MONTH MORATORIUM PERIOD (IRDAI MASTER CIRCULAR 2024, PARA 5.3)",
         "After completion of <b>sixty (60) continuous months</b> of continuous coverage under this Policy (including continuous renewals, "
         "portability, and migration), no claim shall be contestable by the Company on grounds of non-disclosure, misrepresentation, or pre-existing diseases, "
         "save in cases of established intentional fraud. This Policy having been continuously in force since <b>15-January-2020</b> has completed "
         "<b>73 continuous months</b> and enjoys absolute irrevocable statutory moratorium protection."),

        ("SECTION 6 - CUMULATIVE BONUS PRESERVATION & 30-DAY STATUTORY GRACE PERIOD",
         "Under Regulation 13 of the IRDAI (Health Insurance) Regulations, 2016 and IRDAI Master Circular 2024 (Chapter III, Para 3.8), a <b>grace period of thirty (30) days</b> "
         "is provided for renewal payment. Payment within the statutory grace period preserves <b>full continuity of coverage and all accrued Cumulative Bonus credits</b>. "
         "Forfeiture of Cumulative Bonus shall occur only where renewal premium is not received within the 30-day statutory window."),

        ("SECTION 7 - INPATIENT METABOLIC COMPLICATIONS & SEPSIS PROTOCOL",
         "While routine outpatient chronic maintenance of diabetes is not covered under Inpatient indemnity, acute in-hospital metabolic derangements, "
         "diabetic ketoacidosis, and sliding-scale glycemic protocols necessitated by acute surgical sepsis or major operative stress are covered "
         "in full as essential in-hospital critical care management."),

        ("SECTION 8 - HIGH-TECH SURGICAL DISPOSABLES (IRDAI MASTER CIRCULAR 2024, PARA 5.4)",
         "Advanced energy devices, ultrasonic shears (Harmonic ACE+), and radiofrequency vessel sealers (LigaSure) utilized during laparoscopic "
         "and complex open surgery are classified as Specialized Surgical Implants / Modern Technology and are mandatorily payable under IRDAI guidelines."),

        ("SECTION 9 - STATUTORY GRIEVANCE REDRESSAL MECHANISM & INSURANCE OMBUDSMAN",
         "Disputes regarding wrongful claim deductions may be addressed to the Grievance Redressal Officer (GRO) at gro@careinsurance.com.<br/>"
         "If unresolved within 30 days, the Insured has the statutory right to file a formal complaint before the <b>Office of the Insurance Ombudsman, Delhi</b> "
         "under Rule 14 of the Insurance Ombudsman Rules, 2017.")
    ]

    for title, content in p2_clauses:
        story.append(Paragraph(title, styles['LegalClauseTitle']))
        story.append(Paragraph(content, styles['LegalClause']))
        story.append(Spacer(1, 2.5))

    story.append(Spacer(1, 15))
    pol_sig = [
        [
            Paragraph("Head - Underwriting Operations:<br/><b>Sanjay Datta</b><br/>Executive Vice President", styles['TableCell']),
            Paragraph("Chief Legal & Compliance Officer:<br/><b>Meenakshi Sharma</b><br/>Company Secretary", styles['TableCell']),
            Paragraph("For Care Health Insurance Limited<br/><br/><b>Duly Authorized Signatory</b>", styles['TableCellRight'])
        ]
    ]
    t_psig = Table(pol_sig, colWidths=[174, 174, 175])
    story.append(t_psig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


# ==============================================================================
# 3. REJECTION / PARTIAL SETTLEMENT LETTER (Vidal Health TPA / Care Health)
# ==============================================================================

def generate_vidal_rejection_letter(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    styles = get_custom_styles()
    story = []

    # --- PAGE 1: Header, Claim Demographics, Formal Opening & Disallowance Schedule ---
    tpa_head = [
        [
            Paragraph("<b>VIDAL HEALTH TPA PRIVATE LIMITED</b><br/>"
                      "<font size='7'>Tower 2, 1st Floor, Embassy Golf Links Business Park, Domlur, Bengaluru - 560071<br/>"
                      "IRDAI TPA Regn No: 016 | CIN: U85110KA2002PTC030291 | 24x7 Helpdesk: 1800 425 8885<br/>"
                      "Dedicated Adjudication Wing for Care Health Insurance Limited</font>", styles['TableCell']),
            Paragraph("<font size='9.5' color='#990000'><b>FORMAL SETTLEMENT & DEDUCTION ADVICE</b></font><br/>"
                      "<font size='7.5'>Claim Ref: <b>VID/2026/CARE/7719024</b><br/>"
                      "Settlement Date: <b>22-Mar-2026</b><br/>"
                      "Adjudication: <b>PARTIAL SETTLEMENT / DEDUCTION</b></font>", styles['TableCellRight'])
        ]
    ]
    t_head = Table(tpa_head, colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#990000")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))

    demo = [
        [
            Paragraph("<b>Insured Patient:</b> Mrs. Rajeshwari Sundaram", styles['TableCell']),
            Paragraph("<b>Policy No:</b> 11/2020/CARE/998231", styles['TableCell']),
            Paragraph("<b>Insurer:</b> Care Health Insurance Limited", styles['TableCell']),
        ],
        [
            Paragraph("<b>Hospital:</b> Max Super Speciality, Saket", styles['TableCell']),
            Paragraph("<b>Max IP No:</b> IP-SKT-2026-88192", styles['TableCell']),
            Paragraph("<b>Hospitalization:</b> 04-Mar-2026 to 11-Mar-2026", styles['TableCell']),
        ],
        [
            Paragraph("<b>Primary Diagnosis:</b> Acute Cholecystitis & Biliary Sepsis", styles['TableCell']),
            Paragraph("<b>Procedures:</b> ERCP + Laparotomy Cholecystectomy", styles['TableCell']),
            Paragraph("<b>Claim Type:</b> Cashless Post-Settlement Claim", styles['TableCell']),
        ]
    ]
    t_demo = Table(demo, colWidths=[180, 180, 163])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF6F6")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#990000")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F2D5D5")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Dear Mrs. Rajeshwari Sundaram,", styles['TableCellBold']))
    story.append(Paragraph(
        "With reference to your hospitalization claim at Max Super Speciality Hospital, Saket, we have completed the technical "
        "medical and financial audit of your claim dossier. Against the total claimed sum of <b>Rs. 7,85,600.00</b>, an amount of "
        "<b>Rs. 3,38,100.00</b> has been sanctioned and paid. A total disallowance of <b>Rs. 4,47,500.00</b> has been deducted in accordance "
        "with contractual terms, IRDAI guidelines, and medical audit protocols as itemized below:",
        styles['TableCell']
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>ADJUDICATED DEDUCTION SCHEDULE & CITATIONS</b>", styles['SectionHeadingRed']))

    disallow_data = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Deduction Category / Head</b>", styles['TableHead']),
            Paragraph("<b>Billed (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Deducted (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Adjudication Grounds & Policy Clause Citation</b>", styles['TableHead'])
        ],
        # Flaw 3: Grace Period CB Erasure
        [
            Paragraph("1", styles['TableCellCenter']),
            Paragraph("<b>Sum Insured Cap / Bonus Forfeiture</b><br/>(Cumulative Bonus Erasure)", styles['TableCell']),
            Paragraph("2,35,000.00", styles['TableCellRight']),
            Paragraph("2,35,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>Clause 6.1 (Cumulative Bonus Rules):</b> Policy renewal premium due 15-Jan-2026 was received on 28-Jan-2026. Due to delayed premium payment, Cumulative Bonus of Rs. 4,00,000 stands forfeited. Claim liability is capped strictly at Base SI (Rs. 8,00,000). Pro-rata surgical over-exhaustion of Rs. 2,35,000 is disallowed.", styles['TableCellSmall'])
        ],
        # Flaw 5: Ultrasonic Vessel Sealer as Non-Payable
        [
            Paragraph("2", styles['TableCellCenter']),
            Paragraph("<b>Advanced Energy Devices</b><br/>(Harmonic & LigaSure Shears)", styles['TableCell']),
            Paragraph("86,000.00", styles['TableCellRight']),
            Paragraph("86,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>IRDAI Annexure A (List I Non-Payable - Entry 42):</b> Ethicon Harmonic ACE+ ultrasonic shears (Rs. 48,000) and LigaSure vessel sealing kit (Rs. 38,000) are classified as disposable surgical equipment / cutting blades and excluded as non-payable consumables.", styles['TableCellSmall'])
        ],
        # Flaw 4: Sepsis Glycemic Protocol as Lifestyle
        [
            Paragraph("3", styles['TableCellCenter']),
            Paragraph("<b>Metabolic & Glycemic Protocol</b><br/>(Endocrine, Insulin, ABG Series)", styles['TableCell']),
            Paragraph("58,000.00", styles['TableCellRight']),
            Paragraph("58,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>Section 4.1 (Exclusions - Code Excl-18):</b> Treatment of diabetes mellitus, routine endocrine consultations, sliding-scale insulin infusion, and continuous glycemic monitoring are excluded as chronic lifestyle disease management not forming the primary surgical etiology.", styles['TableCellSmall'])
        ],
        # Flaw 1: Multi-Surgery 50% Rule Spillover
        [
            Paragraph("4", styles['TableCellCenter']),
            Paragraph("<b>Secondary Procedure Multi-Cut</b><br/>(50% Cut on ERCP OT & Consumables)", styles['TableCell']),
            Paragraph("1,01,000.00", styles['TableCellRight']),
            Paragraph("50,500.00", styles['TableCellRightBold']),
            Paragraph("50,500.00", styles['TableCellRight']),
            Paragraph("<b>Clause 3.4 (Multiple Surgeries):</b> When multiple procedures occur in the same admission, the secondary procedure is reimbursed at 50%. A 50% cut of Rs. 50,500 is applied across ERCP Surgeon (Rs. 17,500), Fluoroscopy Suite (Rs. 6,000), OT charges (Rs. 11,000), and Dormia Basket/Consumables (Rs. 16,000).", styles['TableCellSmall'])
        ],
        # Flaw 2: Modern Treatment Capping
        [
            Paragraph("5", styles['TableCellCenter']),
            Paragraph("<b>Modern Treatment Capping</b><br/>(Endoscopic Sub-Limit Exhaustion)", styles['TableCell']),
            Paragraph("50,500.00", styles['TableCellRight']),
            Paragraph("15,500.00", styles['TableCellRightBold']),
            Paragraph("35,000.00", styles['TableCellRight']),
            Paragraph("<b>Clause 4.14 (Modern Treatment Methods):</b> Endoscopic advanced interventions are capped at Rs. 50,000 per policy year. After prior utilization, available sub-limit balance of Rs. 35,000 was approved against ERCP balance of Rs. 50,500, resulting in disallowance of Rs. 15,500.", styles['TableCellSmall'])
        ],
        # Sundry Items
        [
            Paragraph("6", styles['TableCellCenter']),
            Paragraph("<b>List I Non-Medical Overheads</b><br/>(Registration & ID Wristband)", styles['TableCell']),
            Paragraph("3,500.00", styles['TableCellRight']),
            Paragraph("2,500.00", styles['TableCellRightBold']),
            Paragraph("1,000.00", styles['TableCellRight']),
            Paragraph("<b>List I Non-Payable:</b> Hospital administrative registration and biomedical waste disposal fee disallowed under standard non-payable schedule.", styles['TableCellSmall'])
        ],
        # Totals
        [
            Paragraph("", styles['TableCellCenter']),
            Paragraph("<b>TOTAL RECONCILIATION</b>", styles['TableCellBold']),
            Paragraph("<b>7,85,600.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>4,47,500.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>3,38,100.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>Net Approved Payable: Rs. 3,38,100.00 | Total Deducted: Rs. 4,47,500.00</b>", styles['TableCellSmall'])
        ]
    ]

    t_dis = Table(disallow_data, colWidths=[18, 110, 56, 56, 56, 227])
    t_dis.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#990000")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#990000")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FFF0F0")),
    ]))
    for row_idx in range(1, len(disallow_data) - 1):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 1 else colors.HexColor("#FDF6F6")
        t_dis.setStyle(TableStyle([('BACKGROUND', (0, row_idx), (-1, row_idx), bg)]))
    story.append(t_dis)

    story.append(PageBreak())

    # --- PAGE 2: Technical Adjudication Rationale, Grievance Escalation & Signatures ---
    story.append(Paragraph("<b>TECHNICAL ADJUDICATION AUDIT RATIONALE & MEDICAL OFFICER FINDINGS</b>", styles['SectionHeadingRed']))
    cmo_note = [
        [Paragraph(
            "<i>\"Technical claims audit conducted by Vidal Health Adjudication Desk for Care Health Insurance:<br/>"
            "1. <b>Cumulative Bonus Forfeiture:</b> Premium receipt records confirm payment on 28-Jan-2026 against renewal due date 15-Jan-2026. "
            "Under Clause 6.1, non-payment on or before the due date voids accumulated no-claim bonus credits. Liability is capped at Base SI of Rs. 8,00,000.<br/>"
            "2. <b>Energy Devices (Harmonic ACE+ & LigaSure):</b> Billed at Rs. 86,000. Under IRDAI Non-Payable Annexure A, Entry 42, disposable surgical "
            "cutting devices are classified as operational surgical tools and cannot be passed to the payer.<br/>"
            "3. <b>Endocrine & Glycemic Protocol:</b> Sepsis management included extensive insulin infusion and endocrinologist rounds (Rs. 58,000). "
            "Under Exclusion Code Excl-18, routine metabolic disease maintenance is excluded from inpatient surgical indemnity.<br/>"
            "4. <b>Multiple Surgery Rule (Clause 3.4):</b> Secondary procedure (ERCP) is discounted at 50% across procedural and facility charges.<br/>"
            "5. <b>Modern Treatment Capping (Clause 4.14):</b> Endoscopic interventions are subject to Rs. 50,000 annual sub-limit.<br/>"
            "The settled amount of Rs. 3,38,100.00 represents full and final settlement under policy terms.\"</i>",
            styles['TableCell']
        )]
    ]
    t_cmo = Table(cmo_note, colWidths=[523])
    t_cmo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF7F7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B22222")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_cmo)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>STATUTORY GRIEVANCE REDRESSAL MECHANISM & INSURANCE OMBUDSMAN JURISDICTION</b>", styles['SectionHeading']))
    story.append(Paragraph(
        "If you do not agree with this adjudication, you may represent your grievance to the "
        "<b>Grievance Redressal Officer (GRO)</b>, Care Health Insurance Limited, Vipul Tech Square, Sector 43, Golf Course Road, "
        "Gurugram - 122009, Haryana (Email: gro@careinsurance.com | Toll-Free: 1800 200 4488).<br/><br/>"
        "Should the insurer fail to resolve your grievance within 30 days or issue an unsatisfactory response, you have the "
        "statutory right under <b>Rule 14 of the Insurance Ombudsman Rules, 2017</b> to approach the <b>Office of the Insurance Ombudsman, Delhi</b>:<br/>"
        "<i>Address: Office of the Insurance Ombudsman, 2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi - 110002.<br/>"
        "Phone: 011-23232481 / 23239633 | Email: bimalokpal.delhi@cioins.co.in</i>",
        styles['FooterDisclaimer']
    ))
    story.append(Spacer(1, 15))

    tpa_sig = [
        [
            Paragraph("Senior Medical Auditor:<br/><b>Dr. Vikramaditya Sen, MBBS, MD</b><br/>Lead Technical Adjudicator", styles['TableCell']),
            Paragraph("Financial Adjudication Head:<br/><b>Anuradha Krishnan</b><br/>Chief Manager - Institutional Claims", styles['TableCell']),
            Paragraph("For Vidal Health TPA Private Limited<br/><br/><b>Authorized Signatory & Seal</b>", styles['TableCellRight'])
        ]
    ]
    t_tsig = Table(tpa_sig, colWidths=[174, 174, 175])
    story.append(t_tsig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


def render_pdf_to_images(pdf_path: str, output_prefix: str):
    """Renders all pages of a PDF to PNG images using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    image_paths = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_path = f"{output_prefix}_p{page_num + 1}.png"
        pix.save(img_path)
        image_paths.append(img_path)
    doc.close()
    return image_paths


if __name__ == "__main__":
    out_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\test_docs\ultra_hard_claim_case"
    os.makedirs(out_dir, exist_ok=True)
    
    bill_path = os.path.join(out_dir, "max_hospital_bill.pdf")
    policy_path = os.path.join(out_dir, "care_supreme_policy.pdf")
    rejection_path = os.path.join(out_dir, "vidal_rejection_letter.pdf")
    
    print(f"1. Generating Max Hospital Bill -> {bill_path}")
    generate_max_hospital_bill(bill_path)
    
    print(f"2. Generating Care Supreme Policy -> {policy_path}")
    generate_care_supreme_policy(policy_path)
    
    print(f"3. Generating Vidal Rejection Letter -> {rejection_path}")
    generate_vidal_rejection_letter(rejection_path)
    
    print("\nRendering PDFs to PNGs for visual inspection...")
    b_imgs = render_pdf_to_images(bill_path, os.path.join(out_dir, "max_hospital_bill"))
    p_imgs = render_pdf_to_images(policy_path, os.path.join(out_dir, "care_supreme_policy"))
    r_imgs = render_pdf_to_images(rejection_path, os.path.join(out_dir, "vidal_rejection_letter"))
    
    print(f"Bill images: {b_imgs}")
    print(f"Policy images: {p_imgs}")
    print(f"Rejection images: {r_imgs}")
    
    # Also copy to artifacts directory for preview
    import shutil
    art_dir = r"C:\Users\Ajay\.gemini\antigravity\brain\ea359e34-0123-41dc-9ead-6e18b81f2263"
    for src in [bill_path, policy_path, rejection_path] + b_imgs + p_imgs + r_imgs:
        dst = os.path.join(art_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        print(f"Copied {os.path.basename(src)} -> artifacts")
        
    print("\nSUCCESS: All 3 ultra-hard complex claim PDFs and images created successfully.")
