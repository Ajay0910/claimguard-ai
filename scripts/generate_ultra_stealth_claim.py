"""
Ultra-Stealth Complex Claim Documents Generator for ClaimGuard AI.

Creates 3 ultra-realistic, deeply disguised Indian health insurance documents:
1. Kokilaben Dhirubhai Ambani Hospital (Mumbai) - 2-page Inpatient Final Bill
   - Severe Acute Necrotizing Retrosternal Mediastinitis & Complex Incisional Hernia with Incarcerated Omentum
   - 34 itemized line items exactly summing to Rs. 9,45,800.00
2. Tata AIG General Insurance Company Limited (MediCare Premier Gold) - 2-page Policy Schedule & Clauses
   - Policy Inception: 12-May-2018 (95 continuous months / ~8 years continuous coverage, ported from National Insurance)
   - Base SI: Rs. 10,00,000 + Accrued Cumulative Bonus: Rs. 5,00,000 = Total Rs. 15,00,000
   - Single Private A/C Room (No Room Rent Capping), Nil Co-pay, Nil Deductible
   - Statutory 60-Month Moratorium Period (Section 5)
3. Paramount Health Services & Insurance TPA Private Limited - 2-page Deduction & Settlement Advice Letter
   - Approved: Rs. 4,28,300.00 | Disallowed: Rs. 5,17,500.00
   - 5 ultra-stealth flaws that deceive humans, seasoned insurance doctors, and TPA auditors:
     1. Malicious Clinical Cross-Mapping: Conflating acute post-surgical necrotizing mediastinitis with an ancient OPD note of allergic rhinitis under Exclusion 01 (Rs. 1,85,000.00)
     2. Portability Continuity Credit Erasure: Imposing 24-month waiting period on enhanced sum insured while ignoring 95-month continuous coverage and ported bonus slab exhaustion order (Rs. 1,42,000.00)
     3. Proportionate Room Rent Surcharge on Single Deluxe Room despite policy having Single Private Room with No Capping (Rs. 88,000.00)
     4. Specialized Cordless Ultrasonic Dissector & Vessel Sealer (Sonicision) disallowed as List I Entry 42 non-payable razor blade (Rs. 52,000.00)
     5. Robotic CapSure Absorbable Mesh Internal Fixation Cartridge disallowed as disposable suture dressing under List I Entry 48 rather than prosthetic implant (Rs. 44,000.00)
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
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('TableCellRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('MetaLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=navy))
    styles.add(ParagraphStyle('MetaVal', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=dark_gray))
    styles.add(ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('ClauseBody', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    
    return styles


# ==============================================================================
# DOCUMENT 1: KOKILABEN DHIRUBHAI AMBANI HOSPITAL BILL
# ==============================================================================

def generate_kokilaben_hospital_bill(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    
    elements = []
    
    # Header Banner
    header_data = [
        [
            Paragraph("<b>KOKILABEN DHIRUBHAI AMBANI HOSPITAL & MEDICAL RESEARCH INSTITUTE</b>", styles['DocTitle']),
        ],
        [
            Paragraph("Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri (West), Mumbai - 400053<br/>"
                      "JCI & NABH Accredited Tertiary Quaternary Care | GSTIN: 27AABCK4819Q1ZT | Tel: +91-22-4269-6969<br/>"
                      "<b>INPATIENT FINAL TAX INVOICE & CONSOLIDATED ADJUDICATION LEDGER</b>", styles['DocSubtitle'])
        ]
    ]
    t_header = Table(header_data, colWidths=[523])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 6))
    
    # Patient & Admission Metadata
    meta_data = [
        [
            Paragraph("<b>Patient Name:</b> Dr. Arisudan Sengupta", styles['MetaVal']),
            Paragraph("<b>UHID / MRN:</b> KDAH-MUM-2026-11849", styles['MetaVal']),
            Paragraph("<b>Age / Sex:</b> 63 Y / Male", styles['MetaVal']),
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP/2026/088219", styles['MetaVal']),
            Paragraph("<b>Admission Date:</b> 14-Apr-2026 01:45 AM (Emergency ER)", styles['MetaVal']),
            Paragraph("<b>Discharge Date:</b> 20-Apr-2026 15:30 PM", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Primary Consultant:</b> Dr. Rajeshwar Deshmukh, MS, MCh (GI Surgery)", styles['MetaVal']),
            Paragraph("<b>Anaesthesiologist:</b> Dr. Sunita Kulkarni, MD, DNB", styles['MetaVal']),
            Paragraph("<b>Room Category:</b> Single Deluxe A/C Room", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Clinical Diagnosis:</b> Severe Acute Necrotizing Retrosternal Mediastinitis & Complex Recurrent Incisional Hernia with Incarcerated Omentum; Severe Septic Response", styles['MetaVal']),
            "", ""
        ],
        [
            Paragraph("<b>Insurer / TPA:</b> Tata AIG General Insurance / Paramount Health Services TPA", styles['MetaVal']),
            Paragraph("<b>TPA Pre-Auth ID:</b> PAR/2026/MUM/882190", styles['MetaVal']),
            Paragraph("<b>Bill No:</b> KDAH/IPB/2026/09941", styles['MetaVal']),
        ]
    ]
    t_meta = Table(meta_data, colWidths=[185, 175, 163])
    t_meta.setStyle(TableStyle([
        ('SPAN', (0, 3), (2, 3)),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5EBF2")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 6))
    
    # Line Items Header
    col_widths = [20, 235, 78, 25, 60, 45, 60]
    
    # 34 Line Items across 2 pages summing exactly to Rs. 9,45,800.00
    items_page_1 = [
        ("1", "Intensive Surgical Critical Care Unit (SICU Bed Charges)", "ROOM", "2", "18,000.00", "999311", "36,000.00"),
        ("2", "SICU Advanced Hemodynamic & Critical Care Nursing", "NURSING", "2", "5,000.00", "999311", "10,000.00"),
        ("3", "Single Private Deluxe A/C Room Accommodation Charges", "ROOM", "4", "12,000.00", "999311", "48,000.00"),
        ("4", "Single Deluxe Inpatient General Ward Nursing Care", "NURSING", "4", "3,000.00", "999311", "12,000.00"),
        ("5", "Emergency Exploratory Laparotomy & Omentectomy Operative Fee", "CONSULTATION", "1", "85,000.00", "999312", "85,000.00"),
        ("6", "Robotic Transversus Abdominis Release (TAR) Reconstruction Fee", "CONSULTATION", "1", "63,000.00", "999312", "63,000.00"),
        ("7", "Senior Consultant Co-Surgeon Operative Assistance", "CONSULTATION", "1", "35,000.00", "999312", "35,000.00"),
        ("8", "Senior Consultant Anaesthesiologist Comprehensive Fee", "CONSULTATION", "1", "42,000.00", "999312", "42,000.00"),
        ("9", "Critical Care Intensivist SICU Management Rounds", "CONSULTATION", "2", "9,000.00", "999312", "18,000.00"),
        ("10", "Major Robotic Ultra-Clean Laminar Flow OT Suite", "OT", "1", "68,000.00", "999313", "68,000.00"),
        ("11", "Advanced Closed-Circuit Anaesthesia Workstation", "OT", "1", "24,000.00", "999313", "24,000.00"),
        ("12", "High-Definition 3D Laparoscopy Video Imaging Tower", "OT", "1", "22,000.00", "999313", "22,000.00"),
        ("13", "Covidien Sonicision Cordless Ultrasonic Dissector & Vessel Sealer", "CONSUMABLES", "1", "52,000.00", "999314", "52,000.00"),
        ("14", "Bard Ventralight ST Composite Bio-Resorbable Barrier Mesh (20x25cm)", "CONSUMABLES", "1", "72,000.00", "999314", "72,000.00"),
        ("15", "Robotic CapSure Absorbable Mesh Fixation Internal Device (30 Fasteners)", "CONSUMABLES", "1", "44,000.00", "999314", "44,000.00"),
        ("16", "Endo-GIA Ultra Articulating Vascular Bowel Stapler Handle", "CONSUMABLES", "1", "38,000.00", "999314", "38,000.00"),
    ]
    
    table_p1_data = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Item Description / Particulars</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>SAC Code</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead']),
        ]
    ]
    for row in items_page_1:
        table_p1_data.append([
            Paragraph(row[0], styles['TableCellSmall']),
            Paragraph(row[1], styles['TableCellBold']),
            Paragraph(row[2], styles['TableCellSmall']),
            Paragraph(row[3], styles['TableCellSmall']),
            Paragraph(row[4], styles['TableCellRight']),
            Paragraph(row[5], styles['TableCellSmall']),
            Paragraph(row[6], styles['TableCellRightBold']),
        ])
        
    t_p1 = Table(table_p1_data, colWidths=col_widths)
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#082040")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FBFD")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_p1)
    
    # Page Break to Page 2
    elements.append(PageBreak())
    
    # Page 2 Header Banner
    p2_header = Table([
        [
            Paragraph("<b>KOKILABEN DHIRUBHAI AMBANI HOSPITAL & MEDICAL RESEARCH INSTITUTE</b>", styles['DocTitle']),
        ],
        [
            Paragraph("INPATIENT FINAL TAX INVOICE (CONTINUATION SHEET) | Patient: Dr. Arisudan Sengupta | IP: IP/2026/088219", styles['DocSubtitle'])
        ]
    ], colWidths=[523])
    p2_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(p2_header)
    elements.append(Spacer(1, 5))
    
    items_page_2 = [
        ("17", "Endo-GIA Tri-Staple Reinforced Cartridges (60mm Purple)", "CONSUMABLES", "2", "14,500.00", "999314", "29,000.00"),
        ("18", "Laparotomy Sterile Impermeable Fluid Barrier Drape Kit", "CONSUMABLES", "1", "9,500.00", "999314", "9,500.00"),
        ("19", "Micro-Porose Surgical Drains & Closed Vacuum Suction Set", "CONSUMABLES", "2", "4,200.00", "999314", "8,400.00"),
        ("20", "Polypropylene Suture Loops & Hemostatic Clips", "CONSUMABLES", "1", "11,500.00", "999314", "11,500.00"),
        ("21", "Sterile Surgical Barrier Gloves & Scrub Accessories", "CONSUMABLES", "16", "450.00", "999314", "7,200.00"),
        ("22", "High-Vacuum Suction Irrigation Cannula Set", "CONSUMABLES", "1", "4,800.00", "999314", "4,800.00"),
        ("23", "Emergency Mediastinal Sepsis Antimicrobial: IV Polymyxin B (500k IU)", "PHARMACY", "8", "4,500.00", "999315", "36,000.00"),
        ("24", "Broad-Spectrum Antibiotic: IV Meropenem 1g Infusions", "PHARMACY", "18", "2,600.00", "999315", "46,800.00"),
        ("25", "Supportive Volume Expander: IV Human Albumin 20% (100ml)", "PHARMACY", "4", "4,900.00", "999315", "19,600.00"),
        ("26", "Total Parenteral Nutrition: Olimel Peri IV Infusion 1500ml", "PHARMACY", "4", "3,800.00", "999315", "15,200.00"),
        ("27", "SICU Emergency Sedation, Analgesia & Vasopressor Infusions", "PHARMACY", "1", "16,400.00", "999315", "16,400.00"),
        ("28", "Emergency Contrast CT Thorax & Abdomen (Triple Phase)", "RADIOLOGY", "1", "17,500.00", "999316", "17,500.00"),
        ("29", "Digital Portable Chest Radiography Series (SICU Follow-up)", "RADIOLOGY", "5", "2,100.00", "999316", "10,500.00"),
        ("30", "Surgical Tissue Histopathology & Bacterial Aerobic/Anaerobic Cultures", "LAB", "1", "12,500.00", "999317", "12,500.00"),
        ("31", "Serial Arterial Blood Gas (ABG), Serum Lactate & Procalcitonin Kinetics", "LAB", "1", "14,000.00", "999317", "14,000.00"),
        ("32", "Inpatient Administrative Admission & Digital Registration", "MISCELLANEOUS", "1", "3,000.00", "999319", "3,000.00"),
        ("33", "Personal Grooming & Sanitation Amenities Pack", "MISCELLANEOUS", "1", "3,500.00", "999319", "3,500.00"),
        ("34", "CBIC Statutory GST on Room Charges (5% on Room Rent > Rs. 5,000/day)", "MISCELLANEOUS", "1", "11,400.00", "999319", "11,400.00"),
    ]
    
    table_p2_data = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Item Description / Particulars</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>SAC Code</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead']),
        ]
    ]
    for row in items_page_2:
        table_p2_data.append([
            Paragraph(row[0], styles['TableCellSmall']),
            Paragraph(row[1], styles['TableCellBold']),
            Paragraph(row[2], styles['TableCellSmall']),
            Paragraph(row[3], styles['TableCellSmall']),
            Paragraph(row[4], styles['TableCellRight']),
            Paragraph(row[5], styles['TableCellSmall']),
            Paragraph(row[6], styles['TableCellRightBold']),
        ])
        
    t_p2 = Table(table_p2_data, colWidths=col_widths)
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#082040")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FBFD")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_p2)
    elements.append(Spacer(1, 6))
    
    # Financial Summary Table
    fin_summary_data = [
        [
            Paragraph("<b>SUB-TOTAL (PAGE 1 CHARGES):</b>", styles['TableCellBold']),
            Paragraph("Rs. 6,69,000.00", styles['TableCellRightBold']),
            Paragraph("<b>GROSS BILL AMOUNT:</b>", styles['TableCellBold']),
            Paragraph("<b>Rs. 9,45,800.00</b>", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>SUB-TOTAL (PAGE 2 CHARGES):</b>", styles['TableCellBold']),
            Paragraph("Rs. 2,76,800.00", styles['TableCellRightBold']),
            Paragraph("<b>DISCOUNT / REBATE:</b>", styles['TableCellBold']),
            Paragraph("Rs. 0.00", styles['TableCellRight'])
        ],
        [
            Paragraph("<b>HOSPITAL GST REGISTRATION:</b>", styles['TableCellBold']),
            Paragraph("27AABCK4819Q1ZT", styles['TableCell']),
            Paragraph("<b>NET INVOICE TOTAL PAYABLE:</b>", styles['TableCellBold']),
            Paragraph("<b>Rs. 9,45,800.00</b>", styles['TableCellRightBold'])
        ],
    ]
    t_fin = Table(fin_summary_data, colWidths=[150, 100, 160, 113])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#082040")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 10))
    
    # Hospital Declarations & Signatures
    sign_data = [
        [
            Paragraph("<b>Billing Officer:</b> R. K. Saxena<br/>Emp ID: KDAH-FIN-881", styles['TableCellSmall']),
            Paragraph("<b>Medical Superintendent:</b> Dr. Hemant V. Joshi, MS, MHA<br/>Reg No: MMC-2001/04/1042", styles['TableCellSmall']),
            Paragraph("<b>For Kokilaben Dhirubhai Ambani Hospital</b><br/><i>[Authorized Digital Signatory]</i>", styles['TableCellSmall'])
        ]
    ]
    t_sign = Table(sign_data, colWidths=[174, 174, 175])
    t_sign.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sign)
    
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Generated Kokilaben Hospital Bill: {pdf_path}")


# ==============================================================================
# DOCUMENT 2: TATA AIG MEDICARE PREMIER POLICY DOCUMENT
# ==============================================================================

def generate_tata_aig_medicare_policy(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    
    elements = []
    
    # Header Banner
    header_data = [
        [
            Paragraph("<b>TATA AIG GENERAL INSURANCE COMPANY LIMITED</b>", styles['DocTitle']),
        ],
        [
            Paragraph("Peninsula Business Park, Tower A, 15th Floor, G.K. Marg, Lower Parel, Mumbai - 400013<br/>"
                      "IRDAI Reg. No. 108 | CIN: U85110MH2000PLC128425 | UIN: TATHLIP21200V032021<br/>"
                      "<b>TATA AIG MEDICARE PREMIER (GOLD EDITION) - POLICY SCHEDULE & BENEFIT SPECIFICATION</b>", styles['DocSubtitle'])
        ]
    ]
    t_header = Table(header_data, colWidths=[523])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 6))
    
    # Policy Schedule Table (Key Parameters)
    sched_data = [
        [
            Paragraph("<b>Policyholder / Primary Insured:</b>", styles['MetaLabel']),
            Paragraph("Dr. Arisudan Sengupta (Self, Age: 63)", styles['MetaVal']),
            Paragraph("<b>Policy Number:</b>", styles['MetaLabel']),
            Paragraph("0238914022/TATAAIG/2026", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Policy Product & Plan:</b>", styles['MetaLabel']),
            Paragraph("Tata AIG MediCare Premier (Gold Edition)", styles['MetaVal']),
            Paragraph("<b>Intermediary / Agent:</b>", styles['MetaLabel']),
            Paragraph("Direct Corporate Online / Mumbai Branch", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Original Policy Inception Date:</b>", styles['MetaLabel']),
            Paragraph("<b>12-May-2018</b> (Ported Continuous)", styles['MetaVal']),
            Paragraph("<b>Current Policy Period:</b>", styles['MetaLabel']),
            Paragraph("<b>12-May-2025 to 11-May-2026</b>", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Portability History & Credit:</b>", styles['MetaLabel']),
            Paragraph("Ported from National Insurance (48 months credit) on 12-May-2022. Total continuous coverage: <b>95 months (~8 years)</b>", styles['MetaVal']),
            Paragraph("<b>Enhancement Date:</b>", styles['MetaLabel']),
            Paragraph("12-May-2024 (Enhanced to Rs. 15L)", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Base Sum Insured:</b>", styles['MetaLabel']),
            Paragraph("Rs. 10,00,000.00", styles['MetaVal']),
            Paragraph("<b>Accrued Cumulative Bonus:</b>", styles['MetaLabel']),
            Paragraph("Rs. 5,00,000.00 (50% No-Claim Bonus)", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Total Effective Coverage:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 15,00,000.00</b>", styles['TableCellBold']),
            Paragraph("<b>Co-Payment / Deductible:</b>", styles['MetaLabel']),
            Paragraph("<b>Nil (0% across all treatments / Nil Deductible)</b>", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Room Entitlement & Capping:</b>", styles['MetaLabel']),
            Paragraph("<b>Single Private A/C Room (No Sub-limit / No Capping)</b>", styles['MetaVal']),
            Paragraph("<b>ICU / HDU Entitlement:</b>", styles['MetaLabel']),
            Paragraph("Actuals / No Capping or Restrictions", styles['MetaVal']),
        ],
    ]
    t_sched = Table(sched_data, colWidths=[140, 150, 110, 123])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5EBF2")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_sched)
    elements.append(Spacer(1, 8))
    
    # Section 1 & 2 Clauses
    elements.append(Paragraph("SECTION 1 - INPATIENT HOSPITALIZATION BENEFITS", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 1.1 - Room, Boarding and Nursing Charges:</b> The Company will cover room boarding and nursing expenses up to "
        "<b>Single Private A/C Room category with NO CAPPING or monetary ceiling</b>. If the insured person is admitted to a room category "
        "equal to or lower than Single Private Room, no proportionate deduction shall apply. Proportionate deduction on Associated Medical "
        "Expenses shall be triggered ONLY if the insured voluntarily occupies a suite or room higher than Single Private Room, strictly limited "
        "to proportional differential room rent in non-PPN hospitals, as mandated under IRDAI Master Circular 2024 Chapter V Para 5.4.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<b>Clause 1.2 - Intensive Care Unit (ICU / HDU) Expenses:</b> Expenses incurred for Intensive Care Unit (ICU), Surgical Intensive Care "
        "Unit (SICU), or High Dependency Unit (HDU) admissions shall be covered at <b>ACTUALS</b> without any monetary sub-limit. ICU bed "
        "charges, monitoring equipment, and critical care intensivist consultations shall NEVER be linked to or impacted by room rent ratios.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<b>Clause 1.3 - Surgical Implants & Internal Fixation Devices:</b> Medical and surgical implants including bio-absorbable composite mesh, "
        "helical titanium anchors, vascular stapler cartridges, and internal fixation devices permanently deployed within the human body during "
        "operative surgery are 100% admissible under Inpatient Hospitalization (Section 1).",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("SECTION 2 - ADVANCED PROCEDURAL & ENERGY DEVICES", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 2.1 - Specialized Surgical Energy Devices:</b> High-frequency electrosurgical cutting shears, ultrasonic dissection units "
        "(including Sonicision, Harmonic ACE, LigaSure, and Thunderbeat), and laparoscopic energy handpieces utilized during major open or "
        "minimally invasive surgical procedures are procedural surgical instruments categorized under IRDAI Annexure A List III and shall be "
        "admitted in full as medically necessary procedural expenses.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 6))
    
    # Page Break to Page 2
    elements.append(PageBreak())
    
    # Page 2 Header Banner
    p2_header = Table([
        [
            Paragraph("<b>TATA AIG GENERAL INSURANCE COMPANY LIMITED</b>", styles['DocTitle']),
        ],
        [
            Paragraph("TATA AIG MEDICARE PREMIER - POLICY TERMS & STATUTORY CONDITIONS (PAGE 2 OF 2)", styles['DocSubtitle'])
        ]
    ], colWidths=[523])
    p2_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(p2_header)
    elements.append(Spacer(1, 6))
    
    # Section 3, 4, 5 Clauses
    elements.append(Paragraph("SECTION 3 - PORTABILITY CONTINUITY & WAITING PERIOD PROVISIONS", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 3.1 - Portability & Continuity Benefit (IRDAI Health Regulations 2016, Regulation 15):</b> When an insured person migrates "
        "or ports from another registered insurer, all continuous coverage years accrued with the previous insurer shall be <b>credited in full</b> "
        "against initial waiting periods, specific illness waiting periods, and pre-existing disease waiting periods on the previous sum insured "
        "plus accrued cumulative bonus. For Dr. Arisudan Sengupta, 48 continuous months ported from National Insurance combined with 47 continuous "
        "months with Tata AIG yields <b>95 months of uninterrupted continuous coverage</b>.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<b>Clause 3.2 - Waiting Period on Enhanced Sum Insured & Exhaustion Sequence:</b> In the event of sum insured enhancement, specific illness "
        "waiting periods shall apply strictly to the incremental enhanced portion (Rs. 5,00,000.00). Claims shall be adjudicated in priority against "
        "the <b>original ported base sum insured (Rs. 5,00,000.00) and accrued cumulative bonus (Rs. 5,00,000.00)</b>, which have fully completed all "
        "statutory waiting periods. The enhanced portion shall be tapped only after exhaustion of the protected base slab.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("SECTION 4 - STATUTORY 60-MONTH MORATORIUM PERIOD (IRDAI MANDATE)", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 4.1 - Moratorium Period (IRDAI Master Circular 2024 Chapter V Para 5.3):</b> After completion of <b>sixty (60) continuous months</b> "
        "of coverage with any registered Indian insurer(s), no policy or claim shall be contestable on grounds of non-disclosure, misrepresentation, "
        "or pre-existing conditions, except in established cases of proven criminal fraud. Inasmuch as Dr. Arisudan Sengupta has maintained continuous "
        "coverage since 12-May-2018 (95 elapsed months), <b>the statutory moratorium period was irrevocably completed on 12-May-2023</b>. "
        "Any repudiation or disallowance grounded in pre-existing conditions or alleged non-disclosure is void ab initio.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("SECTION 5 - CAUSALITY FIREWALL & PRE-EXISTING DISEASE EXCLUSIONS", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 5.1 - Clinical Causality & Medical Nexus Requirement:</b> Exclusion 01 (Pre-Existing Diseases) requires an established, "
        "pathophysiological etiology between the declared or historical illness and the acute hospitalization. Acute infectious, surgical, or "
        "necrotizing emergencies (such as acute necrotizing mediastinitis or strangulated incisional hernia) cannot be repudiated under Exclusion 01 "
        "by arbitrarily cross-mapping them to unrelated benign upper airway conditions (such as allergic rhinitis or seasonal cough).",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("SECTION 6 - CUMULATIVE BONUS PRESERVATION & RENEWAL RULES", styles['SectionHeading']))
    elements.append(Paragraph(
        "<b>Clause 6.1 - Cumulative Bonus Protection:</b> Accrued Cumulative Bonus of Rs. 5,00,000.00 represents a vested financial right. "
        "Under Regulation 13 of IRDAI (Health Insurance) Regulations, 2016, renewal premiums remitted within the 30-day statutory grace period "
        "preserve 100% of accrued cumulative bonus without forfeiture or erasure.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 12))
    
    # Policy Schedule Verification Box
    verif_data = [
        [
            Paragraph("<b>STATUTORY REGULATORY VERIFICATION:</b> This policy contract complies strictly with IRDAI Master Circular on Health Insurance "
                      "Business (29 May 2024), Insurance Regulatory and Development Authority of India (Health Insurance) Regulations 2016, and "
                      "Mental Healthcare Act 2017. Any policy term contrary to statutory circulars is null and void under Section 45 & Section 14.", styles['TableCellSmall']),
            Paragraph("<b>Digitally Certified for Tata AIG General Insurance</b><br/>Authorized Signatory: Rajiv Mehra<br/>Chief Underwriter (Retail Health)", styles['TableCellSmall'])
        ]
    ]
    t_verif = Table(verif_data, colWidths=[380, 143])
    t_verif.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_verif)
    
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Generated Tata AIG Medicare Policy: {pdf_path}")


# ==============================================================================
# DOCUMENT 3: PARAMOUNT TPA DEDUCTION & SETTLEMENT ADVICE LETTER
# ==============================================================================

def generate_paramount_rejection_letter(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    
    elements = []
    
    # Header Banner
    header_data = [
        [
            Paragraph("<b>PARAMOUNT HEALTH SERVICES & INSURANCE TPA PRIVATE LIMITED</b>", styles['DocTitle']),
        ],
        [
            Paragraph("Paramount House, Plot No. A-420, Road No. 28, Wagle Estate, Thane (West) - 400604<br/>"
                      "IRDAI Licensed TPA Reg. No. 006 | CIN: U85190MH2001PTC130424 | Tel: +91-22-6662-0808<br/>"
                      "<b>TECHNICAL CLAIMS AUDIT & PARTIAL SETTLEMENT DISBURSEMENT ADVICE</b>", styles['DocSubtitle'])
        ]
    ]
    t_header = Table(header_data, colWidths=[523])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 6))
    
    # Settlement Reference Metadata
    meta_data = [
        [
            Paragraph("<b>Claim Reference No:</b> PAR/2026/TATAAIG/904128", styles['MetaVal']),
            Paragraph("<b>Settlement Advice Date:</b> 28-Apr-2026", styles['MetaVal']),
            Paragraph("<b>Adjudication:</b> PARTIAL SETTLEMENT", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Policyholder Name:</b> Dr. Arisudan Sengupta", styles['MetaVal']),
            Paragraph("<b>Policy Number:</b> 0238914022/TATAAIG/2026", styles['MetaVal']),
            Paragraph("<b>Underwriting Insurer:</b> Tata AIG General", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Hospital / Provider:</b> Kokilaben Dhirubhai Ambani Hospital", styles['MetaVal']),
            Paragraph("<b>Hospital Bill Ref:</b> KDAH/IPB/2026/09941", styles['MetaVal']),
            Paragraph("<b>Dates:</b> 14-Apr-2026 to 20-Apr-2026", styles['MetaVal']),
        ],
        [
            Paragraph("<b>Claimed Amount:</b> Rs. 9,45,800.00", styles['TableCellBold']),
            Paragraph("<b>Sanctioned / Approved:</b> <font color='#006600'><b>Rs. 4,28,300.00</b></font>", styles['TableCellBold']),
            Paragraph("<b>Total Disallowed:</b> <font color='#990000'><b>Rs. 5,17,500.00</b></font>", styles['TableCellBold']),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[185, 175, 163])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5EBF2")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 8))
    
    # Official Disallowance Table (The 5 Stealth Flaws)
    elements.append(Paragraph("AUDITED DISALLOWANCE SCHEDULE & TECHNICAL ADJUDICATION GROUNDS", styles['SectionHeadingRed']))
    
    col_widths_rej = [20, 115, 60, 248, 80]
    rejection_rows = [
        [
            Paragraph("<b>#</b>", styles['TableHead']),
            Paragraph("<b>Disallowance Head</b>", styles['TableHead']),
            Paragraph("<b>Clause / Ref</b>", styles['TableHead']),
            Paragraph("<b>Paramount TPA Adjudication Reason & Rationale</b>", styles['TableHead']),
            Paragraph("<b>Disallowed (Rs.)</b>", styles['TableHead']),
        ],
        [
            Paragraph("1", styles['TableCellSmall']),
            Paragraph("<b>Pre-Existing Disease Repudiation (Mediastinitis)</b>", styles['TableCellBold']),
            Paragraph("Section 4.1<br/>(Excl-01)", styles['TableCellSmall']),
            Paragraph("Hospitalization for necrotizing thoracic/mediastinal septic response is repudiated under Exclusion 01 (Pre-Existing Disease). Patient's past medical history in 2021 records chronic allergic bronchitis and allergic rhinitis. Chronic airway allergic disease constitutes pre-existing respiratory vulnerability linked to current thoracic sepsis. Claimed Rs. 1,85,000 for Polymyxin B, Meropenem, ICU kinetics and thoracic clearance is inadmissible.", styles['TableCellSmall']),
            Paragraph("Rs. 1,85,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("2", styles['TableCellSmall']),
            Paragraph("<b>Enhancement Waiting Period Disallowance (Hernia TAR)</b>", styles['TableCellBold']),
            Paragraph("Clause 3.2<br/>(Specific Illness)", styles['TableCellSmall']),
            Paragraph("Policy was enhanced from Rs. 7,50,000.00 to Rs. 15,00,000.00 on 12-May-2024. Complex incisional hernia reconstruction and robotic TAR procedure performed on 14-Apr-2026 falls within the 24-month waiting period on the enhanced sum insured slab (23 months elapsed). Disallowed incremental surgical charges beyond initial base threshold of Rs. 7,50,000.", styles['TableCellSmall']),
            Paragraph("Rs. 1,42,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("3", styles['TableCellSmall']),
            Paragraph("<b>Proportionate Room Rent Deduction Surcharge</b>", styles['TableCellBold']),
            Paragraph("Clause 2.1<br/>(Room Ratio)", styles['TableCellSmall']),
            Paragraph("Patient elected to stay in Single Deluxe Room at Rs. 12,000.00/day. Under TPA empanelment guidelines, benchmark twin sharing is capped at Rs. 8,000.00/day. Applied pro-rata proportionate deduction ratio (8000/12000 = 66.67%) across surgeon operative fees, assistant fees, and OT complex charges, resulting in a deduction of Rs. 88,000.00.", styles['TableCellSmall']),
            Paragraph("Rs. 88,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("4", styles['TableCellSmall']),
            Paragraph("<b>Ultrasonic Energy Dissector Disallowance (Sonicision)</b>", styles['TableCellBold']),
            Paragraph("Section 4.8<br/>(List I Entry 42)", styles['TableCellSmall']),
            Paragraph("Covidien Sonicision Cordless Ultrasonic Dissection Handpiece billed at Rs. 52,000.00 is classified under IRDAI Annexure A List I Entry 42 ('Blades and Knives') as non-payable disposable surgical equipment. Handpieces and cutting shears are standard operating theatre overheads.", styles['TableCellSmall']),
            Paragraph("Rs. 52,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("5", styles['TableCellSmall']),
            Paragraph("<b>Robotic CapSure Mesh Internal Fixation Cartridge</b>", styles['TableCellBold']),
            Paragraph("Section 4.8<br/>(List I Entry 48)", styles['TableCellSmall']),
            Paragraph("Robotic CapSure 30-fastener cartridge billed at Rs. 44,000.00 is disallowed under List I Entry 48 ('Suture Material and Disposables'). Suture clips and fixation tackers are auxiliary surgical accessories not categorized as core prosthetic mesh.", styles['TableCellSmall']),
            Paragraph("Rs. 44,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("6", styles['TableCellSmall']),
            Paragraph("<b>Non-Medical Administrative & Grooming Expenses</b>", styles['TableCellBold']),
            Paragraph("List I Entry 1<br/>List I Entry 22", styles['TableCellSmall']),
            Paragraph("Inpatient administrative admission fee (Rs. 3,000.00) and personal grooming hygiene kit (Rs. 3,500.00) are standard non-payable overheads under IRDAI Annexure A List I schedule.", styles['TableCellSmall']),
            Paragraph("Rs. 6,500.00", styles['TableCellRightBold']),
        ],
    ]
    t_rej = Table(rejection_rows, colWidths=col_widths_rej)
    t_rej.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#990000")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FDF9F9")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_rej)
    elements.append(Spacer(1, 8))
    
    # Financial Settlement Summary Reconciliation Table
    fin_reconcile = [
        [
            Paragraph("<b>GROSS HOSPITAL BILLED AMOUNT:</b>", styles['TableCellBold']),
            Paragraph("Rs. 9,45,800.00", styles['TableCellRightBold']),
            Paragraph("<b>AUTHORIZED TPA APPROVAL:</b>", styles['TableCellBold']),
            Paragraph("<font color='#006600'><b>Rs. 4,28,300.00</b></font>", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>TOTAL AMOUNT DISALLOWED / DEDUCTED:</b>", styles['TableCellBold']),
            Paragraph("<font color='#990000'><b>Rs. 5,17,500.00</b></font>", styles['TableCellRightBold']),
            Paragraph("<b>NET DISBURSED VIA NEFT:</b>", styles['TableCellBold']),
            Paragraph("<b>Rs. 4,28,300.00</b>", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>BANK TRANSACTION REFERENCE:</b>", styles['TableCellBold']),
            Paragraph("UTR: HDFCN26118492019", styles['TableCell']),
            Paragraph("<b>DISBURSEMENT DATE:</b>", styles['TableCellBold']),
            Paragraph("28-Apr-2026", styles['TableCell'])
        ],
    ]
    t_fin_recon = Table(fin_reconcile, colWidths=[160, 100, 160, 103])
    t_fin_recon.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#082040")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_fin_recon)
    
    # Page Break to Page 2
    elements.append(PageBreak())
    
    # Page 2 Header Banner
    p2_header = Table([
        [
            Paragraph("<b>PARAMOUNT HEALTH SERVICES & INSURANCE TPA PRIVATE LIMITED</b>", styles['DocTitle']),
        ],
        [
            Paragraph("STATUTORY GRIEVANCE REDRESSAL MECHANISM & REGULATORY ESCALATION NOTICE (PAGE 2 OF 2)", styles['DocSubtitle'])
        ]
    ], colWidths=[523])
    p2_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F4F8")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(p2_header)
    elements.append(Spacer(1, 8))
    
    # Technical Legal Rationale from TPA Medical Director
    elements.append(Paragraph("CHIEF MEDICAL AUDITOR'S TECHNICAL RATIONALE", styles['SectionHeading']))
    elements.append(Paragraph(
        "This claim audit was executed by the Senior Medical Adjudication Board of Paramount Health Services TPA in accordance with "
        "the policy terms and conditions of Tata AIG MediCare Premier and prevailing TPA underwriting protocols. Deductions under Head 1 "
        "(Pre-Existing Disease) are based on hospital clinical case notes mentioning historical allergic bronchitis. Deductions under Head 2 "
        "(Enhancement Waiting Period) reflect literal calculation of months from 12-May-2024 to 14-Apr-2026. Deductions under Head 3, 4, and 5 "
        "apply standardized hospital tariff capping and non-payable surgical consumable schedules.",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 8))
    
    elements.append(Paragraph("STATUTORY GRIEVANCE REDRESSAL & INSURANCE OMBUDSMAN PROCEDURE", styles['SectionHeading']))
    elements.append(Paragraph(
        "If you are dissatisfied with this adjudication, you are entitled under the Insurance Ombudsman Rules, 2017 to initiate formal grievance "
        "redressal through the following statutory escalation pathway:",
        styles['ClauseBody']
    ))
    elements.append(Spacer(1, 4))
    
    grievance_steps = [
        [
            Paragraph("<b>Level 1: Insurer Internal Grievance Cell (GRO)</b>", styles['TableCellBold']),
            Paragraph("Submit a formal written appeal to the Grievance Redressal Officer, Tata AIG General Insurance Co. Ltd., Peninsula Business Park, "
                      "Tower A, Lower Parel, Mumbai - 400013. Email: gro@tataaig.com | Response turnaround: 15 statutory calendar days.", styles['TableCellSmall'])
        ],
        [
            Paragraph("<b>Level 2: IRDAI Bima Bharosa Portal</b>", styles['TableCellBold']),
            Paragraph("If no resolution is received within 15 days or if the decision remains adverse, lodge an online regulatory complaint through "
                      "the IRDAI Bima Bharosa Consumer Portal (https://bimabharosa.irdai.gov.in) or call Toll-Free Helpline: 155255.", styles['TableCellSmall'])
        ],
        [
            Paragraph("<b>Level 3: Insurance Ombudsman Jurisdiction</b>", styles['TableCellBold']),
            Paragraph("Under Rule 14(3) of Insurance Ombudsman Rules, 2017, you may file a statutory appeal before the Hon'ble Insurance Ombudsman "
                      "(Mumbai Jurisdiction), 3rd Floor, Jeevan Seva Annexe, S. V. Road, Santacruz (West), Mumbai - 400054. Form VI-A must be submitted "
                      "along with all supporting hospital bills, policy schedule, and this settlement advice letter.", styles['TableCellSmall'])
        ],
    ]
    t_griev = Table(grievance_steps, colWidths=[150, 373])
    t_griev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_griev)
    elements.append(Spacer(1, 14))
    
    # Official TPA Signatures
    sig_data = [
        [
            Paragraph("<b>Adjudicating Medical Officer:</b><br/>Dr. Neha M. Parikh, MBBS, DNB<br/>Paramount Health Claims Desk", styles['TableCellSmall']),
            Paragraph("<b>Chief Claims Officer:</b><br/>Vikramaditya S. Nair<br/>Head - Corporate Adjudications", styles['TableCellSmall']),
            Paragraph("<b>For Paramount Health Services TPA</b><br/><i>[Authorized Digital Clearance Signatory]</i>", styles['TableCellSmall'])
        ]
    ]
    t_sig = Table(sig_data, colWidths=[174, 174, 175])
    t_sig.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#082040")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sig)
    
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Generated Paramount Rejection Letter: {pdf_path}")


# ==============================================================================
# RENDER PNG PREVIEWS FOR ARTIFACT EMBEDDING
# ==============================================================================

def render_pdf_to_png(pdf_path, output_dir, prefix):
    doc = pymupdf.open(pdf_path)
    png_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        out_name = f"{prefix}_p{i+1}.png"
        out_path = os.path.join(output_dir, out_name)
        pix.save(out_path)
        png_paths.append(out_path)
        print(f"Rendered PNG page {i+1}: {out_path}")
    return png_paths


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, "test_docs", "ultra_stealth_claim_case")
    os.makedirs(output_dir, exist_ok=True)
    
    # Artifact directory for PNG previews
    artifact_dir = r"C:\Users\Ajay\.gemini\antigravity\brain\ea359e34-0123-41dc-9ead-6e18b81f2263"
    
    bill_pdf = os.path.join(output_dir, "kokilaben_hospital_bill.pdf")
    policy_pdf = os.path.join(output_dir, "tata_aig_medicare_policy.pdf")
    rejection_pdf = os.path.join(output_dir, "paramount_rejection_letter.pdf")
    
    generate_kokilaben_hospital_bill(bill_pdf)
    generate_tata_aig_medicare_policy(policy_pdf)
    generate_paramount_rejection_letter(rejection_pdf)
    
    # Render PNGs into artifact directory
    render_pdf_to_png(bill_pdf, artifact_dir, "kokilaben_hospital_bill")
    render_pdf_to_png(policy_pdf, artifact_dir, "tata_aig_medicare_policy")
    render_pdf_to_png(rejection_pdf, artifact_dir, "paramount_rejection_letter")
    
    # Also render into output_dir
    render_pdf_to_png(bill_pdf, output_dir, "kokilaben_hospital_bill")
    render_pdf_to_png(policy_pdf, output_dir, "tata_aig_medicare_policy")
    render_pdf_to_png(rejection_pdf, output_dir, "paramount_rejection_letter")
    
    print("\n[SUCCESS] Generated all 3 Ultra-Stealth claim documents and rendered PNG previews!")
