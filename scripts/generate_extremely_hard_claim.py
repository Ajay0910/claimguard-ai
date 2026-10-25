"""
Extremely Hard Flaws Claim Documents Generator for ClaimGuard AI.

Creates 3 ultra-realistic, deeply disguised Indian health insurance documents
with forensic hardness designed to challenge human surveyors and claim auditors:

1. Sir Ganga Ram Hospital (Rajinder Nagar, New Delhi) - 2-page Inpatient Final Bill
   - Patient: Prof. Swaminathan Venkataraman, 61 Y / Male
   - Acute Spontaneous Aneurysmal Subarachnoid Hemorrhage (SAH) & Ruptured ACom Aneurysm
   - Microvascular Endovascular Coiling with Neuroform Atlas Stent Assistance & EVD Placement
   - 32 itemized line items exactly summing to Rs. 14,85,000.00
2. Bajaj Allianz General Insurance Co. Ltd. - 2-page Policy Schedule & Clauses
   - Policy: Health Guard Platinum Individual Policy (BAJHLIP21055V042021)
   - Continuous coverage 90 months (incepted 18-Feb-2019, ported from New India Assurance with 48 months credit)
   - Base SI: Rs. 10,00,000 + Accrued Cumulative Bonus: Rs. 5,00,000 = Total SI Rs. 15,00,000
   - Single Private A/C Room (Uncapped), Nil Co-pay
   - 60-Month Statutory Moratorium Period (Section 1.1 / IRDAI Master Circular 2024 Para 5.3)
3. Heritage Health Insurance TPA Private Limited - 2-page Settlement & Deduction Advice
   - Approved: Rs. 6,22,000.00 | Disallowed: Rs. 8,63,000.00 | Billed: Rs. 14,85,000.00
   - 5 deep statutory flaws summing to Rs. 8,55,000.00 recoverable (+ Rs. 8,000 legitimate List I):
     1. Co-Surgeon / Dual Neuro-Interventionist Microvascular Fee Disallowance (Rs. 2,20,000.00)
     2. Adult-Manifested Congenital Aneurysm Repudiation under 90-Month Moratorium (Rs. 2,75,000.00)
     3. Modern Treatment Stent Reconstruction Sub-Limit on Base SI vs Total SI (Rs. 1,50,000.00)
     4. Synthetic PPN Tariff Proportionate Room Rent Haircut on Uncapped Policy (Rs. 1,18,000.00)
     5. Microvascular Embolic Introducer & Surgiflo Hemostat Disallowed under List I (Rs. 92,000.00)
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
    
    navy = colors.HexColor("#0A2540")
    crimson = colors.HexColor("#A81D24")
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
# DOCUMENT 1: SIR GANGA RAM HOSPITAL FINAL BILL
# ==============================================================================

def generate_gangaram_hospital_bill(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    story = []
    
    story.append(Paragraph("SIR GANGA RAM HOSPITAL", styles['DocTitle']))
    story.append(Paragraph("Rajinder Nagar, New Delhi - 110060 | NABH & NABL Accredited Quaternary Care Institute", styles['DocSubtitle']))
    story.append(Paragraph("Ph: +91-11-25750000 | Web: www.sgrh.com | GSTIN: 07AAATS1042K1ZW", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0A2540"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("FINAL INPATIENT TAX INVOICE & ITEMIZED SUMMARY", styles['SectionHeading']))
    
    meta_data = [
        [
            Paragraph("<b>Patient Name:</b>", styles['MetaLabel']),
            Paragraph("Prof. Swaminathan Venkataraman", styles['MetaVal']),
            Paragraph("<b>Bill No:</b>", styles['MetaLabel']),
            Paragraph("SGRH/FB/2026/09218", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Age / Gender:</b>", styles['MetaLabel']),
            Paragraph("61 Y / Male", styles['MetaVal']),
            Paragraph("<b>UHID / Inpatient ID:</b>", styles['MetaLabel']),
            Paragraph("SGRH/2026/084920 / IPD/2026/19402", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Admission Date:</b>", styles['MetaLabel']),
            Paragraph("04-Sep-2026 03:15 AM (Emergency)", styles['MetaVal']),
            Paragraph("<b>Discharge Date:</b>", styles['MetaLabel']),
            Paragraph("12-Sep-2026 04:30 PM", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Admitted Ward:</b>", styles['MetaLabel']),
            Paragraph("Neuro-ICU (4 Days) / Single Private A/C Room (4 Days)", styles['MetaVal']),
            Paragraph("<b>Primary Consultant:</b>", styles['MetaLabel']),
            Paragraph("Prof. (Dr.) A. K. Sachdev, MCh (Neurosurgery)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Primary Diagnosis:</b>", styles['MetaLabel']),
            Paragraph("Spontaneous Subarachnoid Hemorrhage (Hunt-Hess Gr III, Fisher Gr 3); Ruptured ACom Aneurysm with Acute Hydrocephalus", styles['MetaVal']),
            Paragraph("<b>Procedures:</b>", styles['MetaLabel']),
            Paragraph("Endovascular Microvascular Coiling with Stent Reconstruction; Right Frontal Burr Hole & EVD Insertion", styles['MetaVal'])
        ],
    ]
    meta_tab = Table(meta_data, colWidths=[95, 175, 95, 158])
    meta_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F7FB")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#D8E2ED")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_tab)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("ITEMIZED CLINICAL CHARGES SCHEDULE (PAGE 1 OF 2)", styles['SectionHeading']))
    
    # Exactly calibrated line items for Page 1: Sum = Rs. 12,69,000.00
    page1_items = [
        ("ITEM_0", "Super Speciality Neuro-ICU Bed Charges (Day 1 to 4)", "ROOM", 4, 25000.0, 100000.0),
        ("ITEM_1", "Neuro-Intensive Care Dedicated Nursing & Monitoring", "NURSING", 4, 5000.0, 20000.0),
        ("ITEM_2", "Single Executive Private A/C Room Accommodation (Day 5 to 8)", "ROOM", 4, 14000.0, 56000.0),
        ("ITEM_3", "Inpatient Floor Nursing & Patient Monitoring Care", "NURSING", 4, 2500.0, 10000.0),
        ("ITEM_4", "Emergency Digital Subtraction Angiography (DSA) Biplane Suite", "OT", 1, 40000.0, 40000.0),
        ("ITEM_5", "Chief Neurosurgeon Operative Craniotomy & EVD Insertion Fee", "CONSULTATION", 1, 200000.0, 200000.0),
        ("ITEM_6", "Senior Neuro-Interventionist & Co-Surgeon Microvascular Coiling Fee", "CONSULTATION", 1, 220000.0, 220000.0),
        ("ITEM_7", "Senior Consultant Neuro-Anaesthesiologist Operative Care", "CONSULTATION", 1, 55000.0, 55000.0),
        ("ITEM_8", "Ultra-Clean Laminar Flow Neuro-Surgical Hybrid OT Complex", "OT", 1, 55000.0, 55000.0),
        ("ITEM_9", "Continuous Intra-Operative Neuro-Electrophysiological Monitoring (IONM)", "OT", 1, 30000.0, 30000.0),
        ("ITEM_10", "Medtronic EDM External Ventricular Drainage (EVD) System Kit", "CONSUMABLES", 1, 26000.0, 26000.0),
        ("ITEM_11", "MicroVention Target 3D Detachable Coils - Primary Framing Coil (1)", "IMPLANT", 1, 95000.0, 95000.0),
        ("ITEM_12", "MicroVention Target Helical Detachable Coils - Packing Coils (3)", "IMPLANT", 3, 40000.0, 120000.0),
        ("ITEM_13", "Stryker Neuroform Atlas Self-Expanding Brain Stent System", "IMPLANT", 1, 150000.0, 150000.0),
        ("ITEM_14", "MicroVention Target 3D Detachable Coil Delivery Microcatheter Sheath", "CONSUMABLES", 1, 54000.0, 54000.0),
        ("ITEM_15", "Surgiflo Hemostatic Flowable Gelatin Matrix with Thrombin Kit", "CONSUMABLES", 1, 38000.0, 38000.0),
    ]
    
    t1_data = [[
        Paragraph("<b>Code</b>", styles['TableHead']),
        Paragraph("<b>Item Description</b>", styles['TableHead']),
        Paragraph("<b>Category</b>", styles['TableHead']),
        Paragraph("<b>Qty</b>", styles['TableHead']),
        Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Total (Rs.)</b>", styles['TableHead']),
    ]]
    for code, desc, cat, qty, rate, amt in page1_items:
        t1_data.append([
            Paragraph(code, styles['TableCellSmall']),
            Paragraph(desc, styles['TableCell']),
            Paragraph(cat, styles['TableCellSmall']),
            Paragraph(str(qty), styles['TableCellRight']),
            Paragraph(f"{rate:,.2f}", styles['TableCellRight']),
            Paragraph(f"{amt:,.2f}", styles['TableCellRightBold']),
        ])
    
    p1_subtotal = sum(item[5] for item in page1_items)
    t1_data.append([
        Paragraph("<b>Page 1 Sub-total</b>", styles['TableCellBold']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph(f"<b>Rs. {p1_subtotal:,.2f}</b>", styles['TableCellRightBold']),
    ])
    
    t1 = Table(t1_data, colWidths=[48, 220, 75, 28, 72, 80])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A2540")),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EAEFF5")),
    ]))
    story.append(t1)
    
    story.append(PageBreak())
    
    # PAGE 2 OF HOSPITAL BILL
    story.append(Paragraph("SIR GANGA RAM HOSPITAL — INPATIENT BILL (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("UHID: SGRH/2026/084920 | Bill No: SGRH/FB/2026/09218 | Patient: Prof. Swaminathan Venkataraman", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0A2540"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("ITEMIZED CLINICAL CHARGES SCHEDULE (CONTINUED)", styles['SectionHeading']))
    
    # Exactly calibrated line items for Page 2: Sum = Rs. 2,16,000.00
    page2_items = [
        ("ITEM_16", "Neuro-Interventional Micro-Guidewire Synchro-14 Guidewires (2)", "CONSUMABLES", 2, 12000.0, 24000.0),
        ("ITEM_17", "Diagnostic Neuro-Vascular Angiographic Catheter & Dilator Pack", "CONSUMABLES", 1, 14000.0, 14000.0),
        ("ITEM_18", "Trans-Femoral Arterial Sheath & Perclose ProGlide Vascular Closure", "CONSUMABLES", 1, 18000.0, 18000.0),
        ("ITEM_19", "Intra-Arterial Papaverine & Nimodipine Infusion Spasmolysis", "PHARMACY", 4, 6500.0, 26000.0),
        ("ITEM_20", "IV Nimodipine Continuous Cerebral Perfusion Infusion (8 Days)", "PHARMACY", 8, 3000.0, 24000.0),
        ("ITEM_21", "IV Levetiracetam 1000mg & Neuro-Protective Infusions", "PHARMACY", 8, 1500.0, 12000.0),
        ("ITEM_22", "High-Volume Hyperosmolar Mannitol 20% & 3% NaCl Protocol", "PHARMACY", 12, 750.0, 9000.0),
        ("ITEM_23", "Parenteral Broad-Spectrum Meropenem & Vancomycin Coverage", "PHARMACY", 10, 1800.0, 18000.0),
        ("ITEM_24", "Serial High-Resolution 128-Slice Non-Contrast Brain CT Scans (3)", "RADIOLOGY", 3, 7000.0, 21000.0),
        ("ITEM_25", "Daily Bedside Transcranial Doppler (TCD) Vasospasm Monitoring (6)", "LAB", 6, 3500.0, 21000.0),
        ("ITEM_26", "Comprehensive CSF Cytology, Protein, Culture & Electrolytes (4)", "LAB", 4, 2500.0, 10000.0),
        ("ITEM_27", "Continuous Arterial Line Cannulation & Real-Time Invasive BP Kit", "CONSUMABLES", 1, 6500.0, 6500.0),
        ("ITEM_28", "Central Venous Catheter (Triple Lumen) Insertion Set", "CONSUMABLES", 1, 4500.0, 4500.0),
        ("ITEM_29", "Special Attendant Deluxe Inpatient Meal Plan (Hospital Pantry)", "MISCELLANEOUS", 8, 600.0, 4800.0),
        ("ITEM_30", "Patient Personal Dental, Hygiene & Comfort Kit (Inpatient)", "MISCELLANEOUS", 1, 1700.0, 1700.0),
        ("ITEM_31", "Inpatient Admission Administrative Registration & ID Band", "MISCELLANEOUS", 1, 1500.0, 1500.0),
    ]
    
    t2_data = [[
        Paragraph("<b>Code</b>", styles['TableHead']),
        Paragraph("<b>Item Description</b>", styles['TableHead']),
        Paragraph("<b>Category</b>", styles['TableHead']),
        Paragraph("<b>Qty</b>", styles['TableHead']),
        Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Total (Rs.)</b>", styles['TableHead']),
    ]]
    for code, desc, cat, qty, rate, amt in page2_items:
        t2_data.append([
            Paragraph(code, styles['TableCellSmall']),
            Paragraph(desc, styles['TableCell']),
            Paragraph(cat, styles['TableCellSmall']),
            Paragraph(str(qty), styles['TableCellRight']),
            Paragraph(f"{rate:,.2f}", styles['TableCellRight']),
            Paragraph(f"{amt:,.2f}", styles['TableCellRightBold']),
        ])
        
    p2_subtotal = sum(item[5] for item in page2_items)
    t2_data.append([
        Paragraph("<b>Page 2 Sub-total</b>", styles['TableCellBold']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph("", styles['TableCell']),
        Paragraph(f"<b>Rs. {p2_subtotal:,.2f}</b>", styles['TableCellRightBold']),
    ])
    
    t2 = Table(t2_data, colWidths=[48, 220, 75, 28, 72, 80])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A2540")),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EAEFF5")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))
    
    # Financial Summary Table: Exactly 14,85,000.00
    gross_bill = p1_subtotal + p2_subtotal
    summary_data = [
        [
            Paragraph("<b>Page 1 Sub-Total:</b>", styles['MetaLabel']),
            Paragraph(f"Rs. {p1_subtotal:,.2f}", styles['TableCellRightBold']),
            Paragraph("<b>Net TPA Pre-Auth Sanctioned:</b>", styles['MetaLabel']),
            Paragraph("Rs. 6,22,000.00", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>Page 2 Sub-Total:</b>", styles['MetaLabel']),
            Paragraph(f"Rs. {p2_subtotal:,.2f}", styles['TableCellRightBold']),
            Paragraph("<b>Patient Advance Paid at Discharge:</b>", styles['MetaLabel']),
            Paragraph("Rs. 8,63,000.00", styles['TableCellRightBold'])
        ],
        [
            Paragraph("<b>TOTAL GROSS BILL AMOUNT:</b>", styles['MetaLabel']),
            Paragraph(f"<font color='#0A2540' size='8.5'><b>Rs. {gross_bill:,.2f}</b></font>", styles['TableCellRightBold']),
            Paragraph("<b>NET OUTSTANDING BALANCE:</b>", styles['MetaLabel']),
            Paragraph("<b>Rs. 0.00 (Fully Settled)</b>", styles['TableCellRightBold'])
        ],
    ]
    sum_tab = Table(summary_data, colWidths=[150, 112, 150, 111])
    sum_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0A2540")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#D0D0D0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#E8F0FE")),
    ]))
    story.append(sum_tab)
    story.append(Spacer(1, 10))
    
    # Hospital Declarations & Signatures
    decl_text = (
        "<b>CERTIFICATE & CLINICAL DECLARATION:</b> "
        "Certified that the patient was admitted under emergency conditions with ruptured anterior communicating artery "
        "aneurysm and acute subarachnoid hemorrhage. Simultaneous EVD placement and endovascular coiling with stent assistance "
        "were medically necessary to prevent re-bleeding and cerebral herniation. All procedures and implants are genuine and billed at NABH hospital tariff rates."
    )
    story.append(Paragraph(decl_text, styles['CalloutText']))
    story.append(Spacer(1, 14))
    
    sigs = [
        [
            Paragraph("Prepared by:<br/>Billing Executive (IPD)", styles['TableCell']),
            Paragraph("Verified by:<br/>Medical Superintendent, SGRH", styles['TableCell']),
            Paragraph("Authorized Signatory:<br/>Finance Officer, Patient Accounts", styles['TableCellBold']),
        ]
    ]
    sig_tab = Table(sigs, colWidths=[174, 174, 175])
    sig_tab.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sig_tab)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Sir Ganga Ram Hospital Bill: {pdf_path} (Total: Rs. {gross_bill:,.2f})")


# ==============================================================================
# DOCUMENT 2: BAJAJ ALLIANZ INSURANCE POLICY SCHEDULE & CLAUSES
# ==============================================================================

def generate_bajaj_allianz_policy(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    story = []
    
    # PAGE 1: POLICY SCHEDULE
    story.append(Paragraph("BAJAJ ALLIANZ GENERAL INSURANCE COMPANY LIMITED", styles['DocTitle']))
    story.append(Paragraph("GE Plaza, Airport Road, Yerawada, Pune - 411006 | IRDAI Regn No. 113 | CIN: U66010PN2000PLC015329", styles['DocSubtitle']))
    story.append(Paragraph("Toll Free: 1800-209-5858 | Email: bagichelp@bajajallianz.co.in | Policy UIN: BAJHLIP21055V042021", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0A2540"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("HEALTH GUARD PLATINUM INDIVIDUAL POLICY SCHEDULE", styles['SectionHeading']))
    
    sched_meta = [
        [
            Paragraph("<b>Policyholder / Proposer:</b>", styles['MetaLabel']),
            Paragraph("Prof. Swaminathan Venkataraman", styles['MetaVal']),
            Paragraph("<b>Policy Number:</b>", styles['MetaLabel']),
            Paragraph("OG-27-1801-8401-00094182", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Insured Person Name:</b>", styles['MetaLabel']),
            Paragraph("Prof. Swaminathan Venkataraman (61 Y)", styles['MetaVal']),
            Paragraph("<b>Relationship / Plan:</b>", styles['MetaLabel']),
            Paragraph("Self / Health Guard Platinum", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Current Policy Period:</b>", styles['MetaLabel']),
            Paragraph("18-Feb-2026 to 17-Feb-2027", styles['MetaVal']),
            Paragraph("<b>Original Inception Date:</b>", styles['MetaLabel']),
            Paragraph("18-Feb-2019 (90 Continuous Months)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Base Sum Insured:</b>", styles['MetaLabel']),
            Paragraph("Rs. 10,00,000.00", styles['MetaVal']),
            Paragraph("<b>Accrued Cumulative Bonus:</b>", styles['MetaLabel']),
            Paragraph("Rs. 5,00,000.00 (50% Max Cap)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Total Effective Sum Insured:</b>", styles['MetaLabel']),
            Paragraph("<font color='#006600'><b>Rs. 15,00,000.00</b></font>", styles['MetaVal']),
            Paragraph("<b>Portability Credits / Prior Tenure:</b>", styles['MetaLabel']),
            Paragraph("48 Months (New India Assurance tenure 2019-2023 ported seamlessly)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Room Category Entitlement:</b>", styles['MetaLabel']),
            Paragraph("Single Private A/C Room (No Capping)", styles['MetaVal']),
            Paragraph("<b>Co-Payment / Deductible:</b>", styles['MetaLabel']),
            Paragraph("NIL (0%) Co-pay across all claims", styles['MetaVal'])
        ],
    ]
    sched_tab = Table(sched_meta, colWidths=[120, 150, 120, 133])
    sched_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#D8E2ED")),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sched_tab)
    story.append(Spacer(1, 6))
    
    # Section 1: Moratorium and Continuity
    story.append(Paragraph("SECTION 1: STATUTORY MORATORIUM & WAITING PERIOD PROVISIONS", styles['SectionHeading']))
    sec1_text = (
        "<b>Section 1.1 — 60-Month Moratorium Period (IRDAI Master Circular 2024 Chapter V Para 5.3):</b><br/>"
        "After completion of 60 continuous months of coverage under this policy (including uninterrupted continuity transferred through statutory health portability under "
        "Regulation 17 of IRDAI Regulations 2016), no health insurance claim shall be contestable by the Company on grounds of pre-existing condition, non-disclosure, or "
        "misrepresentation, except for established proven fraud. All waiting periods for pre-existing diseases, internal congenital conditions, or specific treatments expire "
        "irrevocably after 60 continuous months from original inception (18-Feb-2019). The 60-month moratorium was completed on 18-Feb-2024.<br/><br/>"
        "<b>Section 1.2 — Room Rent Entitlement & Proportionate Deduction Bar:</b><br/>"
        "Under the Platinum Plan, the insured is entitled to a Single Private A/C Room without room rent capping. In accordance with IRDAI Standardization Guidelines and "
        "GIPSA PPN Rules, when an insured is entitled to a Single Private Room without financial capping, the Insurer and TPA are strictly prohibited from applying "
        "proportionate deductions or artificial benchmark tariff caps across associated medical expenses (surgeon fees, consultation, nursing, operation theatre, and diagnostic investigations)."
    )
    story.append(Paragraph(sec1_text, styles['ClauseBody']))
    story.append(Spacer(1, 6))
    
    # Section 2: Modern Treatment and Sublimits
    story.append(Paragraph("SECTION 2: MODERN TREATMENT METHODS & SURGICAL PROCEDURES", styles['SectionHeading']))
    sec2_text = (
        "<b>Section 2.1 — Modern Treatment Methods (IRDAI Circular Ref: IRDAI/HLT/REG/CIR/194/09/2019):</b><br/>"
        "The policy covers 12 advanced modern treatment methods including Deep Brain Stimulation, Balloon Sinuplasty, Stereotactic Radio-Surgery, Robotic Surgeries, and "
        "Neuro-Endovascular Interventions. Under IRDAI Master Circular (2024, Chapter V, Para 5.4), sub-limits specified in the policy shall apply against the Total Effective "
        "Sum Insured (Base Sum Insured plus accrued Cumulative Bonus). Where modern treatment methods are performed as medically necessary inpatient procedures for "
        "life-threatening acute cerebrovascular crises, insurers shall not enforce elective day-care sub-limits to deny essential surgical components.<br/><br/>"
        "<b>Section 2.2 — Cumulative Bonus Enhancement:</b><br/>"
        "Cumulative Bonus accrued at 10% per claim-free year enhances the Total Sum Insured up to a maximum of 50%. The accrued Cumulative Bonus of Rs. 5,00,000.00 "
        "is an irrevocable enhancement of coverage and must be exhausted in addition to the base sum insured."
    )
    story.append(Paragraph(sec2_text, styles['ClauseBody']))
    
    story.append(PageBreak())
    
    # PAGE 2: SPECIFIC CLAUSES & EXCLUSIONS
    story.append(Paragraph("BAJAJ ALLIANZ GENERAL INSURANCE — POLICY CLAUSES (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("Policy No: OG-27-1801-8401-00094182 | Insured: Prof. Swaminathan Venkataraman", styles['DocSubtitle']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0A2540"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("SECTION 3: SPECIFIC EXCLUSIONS & TECHNICAL PROVISIONS", styles['SectionHeading']))
    
    clauses_text = (
        "<b>Clause 4.1 — Pre-Existing Disease (PED) Exclusion:</b><br/>"
        "Expenses related to the treatment of a pre-existing disease (PED) and its direct complications shall be excluded until the expiry of 36 months of continuous coverage "
        "after the date of inception. Upon completion of continuous coverage (subject to Section 1.1 moratorium), pre-existing conditions become fully payable.<br/><br/>"
        "<b>Clause 4.2 — Congenital Anomalies Clause:</b><br/>"
        "Congenital external anomalies are excluded. Congenital internal anomalies that manifest symptomatically for the first time in adult life requiring emergency life-saving "
        "neurovascular or cardiovascular surgery shall be indemnified as acute illnesses, and are fully protected under Section 1.1 statutory moratorium provisions.<br/><br/>"
        "<b>Clause 4.3 — Co-Surgeon & Multiple Specialist Operating Rules:</b><br/>"
        "Where complex surgical interventions necessitate simultaneous dual-specialty intervention (e.g. combined open neurosurgery for EVD insertion and endovascular "
        "microvascular coiling by an interventionist), co-surgeon fees are recognized and payable subject to recognized clinical board protocols.<br/><br/>"
        "<b>Clause 4.12 — Modern Treatment Sub-Limit (Technical Schedule):</b><br/>"
        "Neuro-Endovascular Interventions and Stenting: Sub-limited to 50% of Sum Insured. Sub-limits apply to the Total Sum Insured (Base + CB).<br/><br/>"
        "<b>Clause 6.1 — Non-Payable Items & Consumables Schedule:</b><br/>"
        "Expenses excluded under Annexure A List I of IRDAI Standardization Guidelines are non-payable. However, specialized implant delivery catheters, vascular closure "
        "devices, and intra-operative flowable hemostatic matrices used during inpatient neurosurgery are recognized as statutorily payable under Annexure A (List III) "
        "procedural items."
    )
    story.append(Paragraph(clauses_text, styles['ClauseBody']))
    story.append(Spacer(1, 8))
    
    omb_stat = (
        "<b>IMPORTANT STATUTORY NOTICE UNDER IRDAI (PROTECTION OF POLICYHOLDERS' INTERESTS) REGULATIONS:</b><br/>"
        "This policy is subject to the provisions of Insurance Regulatory and Development Authority of India (IRDAI) Act, 1999. In accordance with Chapter V of Master "
        "Circular on Health Insurance Business (29-May-2024), the insurer is bound by statutory moratorium after 60 continuous months, and cannot repudiate adult "
        "emergency manifestations of internal defects."
    )
    story.append(Paragraph(omb_stat, styles['CalloutText']))
    story.append(Spacer(1, 14))
    
    auth = [
        [
            Paragraph("Entered by:<br/>Underwriting Officer, Delhi DO", styles['TableCell']),
            Paragraph("Verified by:<br/>Manager - Technical Underwriting", styles['TableCell']),
            Paragraph("For Bajaj Allianz General Insurance Co. Ltd.<br/><b>Authorized Signatory</b>", styles['TableCellBold']),
        ]
    ]
    auth_tab = Table(auth, colWidths=[174, 174, 175])
    auth_tab.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(auth_tab)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Bajaj Allianz Policy Schedule: {pdf_path}")


# ==============================================================================
# DOCUMENT 3: HERITAGE HEALTH TPA SETTLEMENT & REJECTION ADVICE LETTER
# ==============================================================================

def generate_heritage_rejection_letter(pdf_path):
    styles = get_custom_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    story = []
    
    # PAGE 1: REJECTION & DISALLOWANCE AUDIT
    story.append(Paragraph("HERITAGE HEALTH INSURANCE TPA PRIVATE LIMITED", styles['DocTitle']))
    story.append(Paragraph("Nicco House, 5th Floor, 2 Hare Street, Kolkata - 700001 | Regional Office: New Delhi - 110001", styles['DocSubtitle']))
    story.append(Paragraph("IRDAI TPA Regn No: 008 | CIN: U85199WB1998PTC087998 | Web: www.heritagehealthtpa.com", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#A81D24"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("SETTLEMENT ADVICE & ITEMIZED DISALLOWANCE SCHEDULE", styles['SectionHeadingRed']))
    
    tpa_meta = [
        [
            Paragraph("<b>Claim Reference (CCN):</b>", styles['MetaLabel']),
            Paragraph("HER/2026/BAJAJ/8910452", styles['MetaVal']),
            Paragraph("<b>Settlement Date:</b>", styles['MetaLabel']),
            Paragraph("22-Sep-2026", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Underwriting Insurer:</b>", styles['MetaLabel']),
            Paragraph("Bajaj Allianz General Insurance Co. Ltd.", styles['MetaVal']),
            Paragraph("<b>Policy Number:</b>", styles['MetaLabel']),
            Paragraph("OG-27-1801-8401-00094182", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Patient / Policyholder:</b>", styles['MetaLabel']),
            Paragraph("Prof. Swaminathan Venkataraman", styles['MetaVal']),
            Paragraph("<b>Hospital / Provider:</b>", styles['MetaLabel']),
            Paragraph("Sir Ganga Ram Hospital, New Delhi", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Hospital Bill Ref / IPD No:</b>", styles['MetaLabel']),
            Paragraph("SGRH/FB/2026/09218 / IPD/2026/19402", styles['MetaVal']),
            Paragraph("<b>Dates of Inpatient Stay:</b>", styles['MetaLabel']),
            Paragraph("04-Sep-2026 to 12-Sep-2026 (8 Days)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Total Claim Billed:</b>", styles['MetaLabel']),
            Paragraph("Rs. 14,85,000.00", styles['MetaVal']),
            Paragraph("<b>Total Approved / Paid:</b>", styles['MetaLabel']),
            Paragraph("<font color='#006600'><b>Rs. 6,22,000.00</b></font>", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Total Disallowed / Deducted:</b>", styles['MetaLabel']),
            Paragraph("<font color='#A81D24'><b>Rs. 8,63,000.00</b></font>", styles['MetaVal']),
            Paragraph("<b>Adjudication Status:</b>", styles['MetaLabel']),
            Paragraph("<b>PARTIALLY SETTLED (HAIRCUT: 58.1%)</b>", styles['MetaVal'])
        ],
    ]
    tpa_meta_tab = Table(tpa_meta, colWidths=[120, 150, 120, 133])
    tpa_meta_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#D8E2ED")),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tpa_meta_tab)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("AUDITED DISALLOWANCE SCHEDULE & TECHNICAL ADJUDICATION GROUNDS (PAGE 1)", styles['SectionHeading']))
    
    p1_rejections = [
        (
            "1. Co-Surgeon / Dual Neuro-Interventionist Microvascular Fee Disallowance\n"
            "Hospital billed Chief Neurosurgeon operative fee (Rs. 2,00,000.00) plus Senior Neuro-Interventionist "
            "co-surgeon microvascular coiling fee (Rs. 2,20,000.00). Under Clause 4.3, only one primary operating surgeon "
            "fee is admissible per surgical session; assistant surgeon fees are capped at 15%, and dual primary operating surgeon "
            "billing is repudiated as non-payable dual billing.",
            "Clause 4.3 Single Operating Surgeon Protocol",
            "2,20,000.00",
            "2,20,000.00",
            "0.00"
        ),
        (
            "2. Pre-Existing Congenital Aneurysmal Disallowance (ACom Aneurysm Repudiation)\n"
            "Discharge summary cites ruptured saccular anterior communicating artery aneurysm. Intracranial berry/saccular aneurysms "
            "are congenital arterial wall defects existing from birth. Repudiated under Clause 4.2 (Exclusion of Congenital Internal "
            "Diseases and Vascular Malformations). Inpatient stay charges, hyperosmolar mannitol, and cerebral vasospasm management "
            "linked to congenital aneurysmal defect (Rs. 2,75,000.00) are excluded.",
            "Clause 4.2 Congenital Internal Disease Exclusion & PED Exclusion",
            "2,75,000.00",
            "2,75,000.00",
            "0.00"
        ),
        (
            "3. Modern Treatment Neuro-Stenting Sub-Limit Capping on Base Sum Insured\n"
            "The patient underwent microvascular coiling with Stryker Neuroform Atlas Stent reconstruction (Rs. 1,50,000.00). "
            "Under Clause 4.12, Modern Treatment Methods are sub-limited to 50% of the Base Sum Insured (50% of Rs. 10,00,000 = "
            "Rs. 5,00,000.00). Angiography suite, framing coil and packing coils already consumed Rs. 5,00,000.00. Hence, "
            "Neuroform Atlas stent deployment fee of Rs. 1,50,000.00 is disallowed in excess of sub-limit.",
            "Clause 4.12 Modern Treatments (50% Base SI Capping)",
            "1,50,000.00",
            "1,50,000.00",
            "0.00"
        ),
    ]
    
    t1_data = [[
        Paragraph("<b>Disallowance Head & Stated Insurer Reasoning</b>", styles['TableHead']),
        Paragraph("<b>Policy / Circular Citation</b>", styles['TableHead']),
        Paragraph("<b>Billed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Disallowed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
    ]]
    for head, cit, billed, dis, app in p1_rejections:
        t1_data.append([
            Paragraph(head.replace('\n', '<br/>'), styles['TableCellSmall']),
            Paragraph(cit, styles['TableCellSmall']),
            Paragraph(billed, styles['TableCellRight']),
            Paragraph(dis, styles['TableCellRightBold']),
            Paragraph(app, styles['TableCellRight']),
        ])
        
    t1_data.append([
        Paragraph("<b>Page 1 Sub-total</b>", styles['TableCellBold']),
        Paragraph("", styles['TableCell']),
        Paragraph("6,45,000.00", styles['TableCellRight']),
        Paragraph("<b>Rs. 6,45,000.00</b>", styles['TableCellRightBold']),
        Paragraph("0.00", styles['TableCellRight']),
    ])
    
    t1 = Table(t1_data, colWidths=[205, 110, 68, 75, 65])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A2540")),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EAEFF5")),
    ]))
    story.append(t1)
    
    story.append(PageBreak())
    
    # PAGE 2 OF SETTLEMENT ADVICE
    story.append(Paragraph("HERITAGE HEALTH INSURANCE TPA — SETTLEMENT ADVICE (PAGE 2)", styles['DocTitle']))
    story.append(Paragraph("CCN: HER/2026/BAJAJ/8910452 | Policy: OG-27-1801-8401-00094182 | Patient: Prof. Swaminathan Venkataraman", styles['DocSubtitle']))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0A2540"), spaceBefore=1, spaceAfter=4))
    story.append(Paragraph("AUDITED DISALLOWANCE SCHEDULE (CONTINUED)", styles['SectionHeading']))
    
    p2_rejections = [
        (
            "4. Synthetic Room Rent Benchmark & Proportionate Deduction Haircut\n"
            "Hospital billed Rs. 14,000/day for Single Executive Room (Rs. 56,000 total). PPN empanelment tariff benchmark rate for network hospitals "
            "is Rs. 7,000/day for Twin Sharing. An excess room rent deduction of Rs. 28,000 plus proportionate deduction of 50.0% "
            "applied across Associated Medical Expenses (Chief Surgeon operative care Rs. 60,000 + Nursing Rs. 30,000 + Anaesthesia Rs. 30,000) "
            "totaling Rs. 1,18,000.00 disallowed out of Rs. 1,76,000.00 associated charges.",
            "PPN Network Empanelment Tariff Schedule & Proportionate Deduction Formula",
            "1,76,000.00",
            "1,18,000.00",
            "58,000.00"
        ),
        (
            "5. Biological Hemostatic Flowable Matrix & Embolic Delivery Sheath Disallowance\n"
            "Hospital billed MicroVention Target 3D Detachable Coil delivery microcatheter sheath (Rs. 54,000.00) and Surgiflo "
            "Hemostatic Flowable Gelatin Matrix with Thrombin (Rs. 38,000.00). Classified as non-payable surgical consumable gel "
            "and disposables under IRDAI Standardization Guidelines Annexure A List I Entry 42 and Entry 48 exclusions.",
            "IRDAI Standardization Guidelines Annexure A List I Entry 42 & Entry 48",
            "92,000.00",
            "92,000.00",
            "0.00"
        ),
        (
            "6. Non-Medical Comfort & Attendant Overheads (Legitimate Exclusion)\n"
            "Attendant special pantry meals (Rs. 4,800.00), Patient dental and personal hygiene kit (Rs. 1,700.00), and Inpatient "
            "admission registration handling charge (Rs. 1,500.00) are non-medical expenses excluded under List I.",
            "IRDAI Annexure A List I Items 1, 18 & 44",
            "8,000.00",
            "8,000.00",
            "0.00"
        ),
        (
            "7. Admitted Surgical Implants & Neuro-ICU Stay (Paid Heads)\n"
            "Admitted Stryker Micro-coils, Neuro-ICU monitoring, EVD catheter, IV Nimodipine infusion, CT/MRI neuro-imaging, "
            "and baseline consultation approved within tariff guidelines.",
            "Clause 1.1 Inpatient Medical Expenses (Admissible Heads)",
            "5,64,000.00",
            "0.00",
            "5,64,000.00"
        ),
    ]
    
    t2_data = [[
        Paragraph("<b>Disallowance Head & Stated Insurer Reasoning</b>", styles['TableHead']),
        Paragraph("<b>Policy / Circular Citation</b>", styles['TableHead']),
        Paragraph("<b>Billed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Disallowed (Rs.)</b>", styles['TableHead']),
        Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
    ]]
    for head, cit, billed, dis, app in p2_rejections:
        t2_data.append([
            Paragraph(head.replace('\n', '<br/>'), styles['TableCellSmall']),
            Paragraph(cit, styles['TableCellSmall']),
            Paragraph(billed, styles['TableCellRight']),
            Paragraph(dis, styles['TableCellRightBold']),
            Paragraph(app, styles['TableCellRight']),
        ])
        
    t2_data.append([
        Paragraph("<b>Page 2 Sub-total</b>", styles['TableCellBold']),
        Paragraph("", styles['TableCell']),
        Paragraph("8,40,000.00", styles['TableCellRight']),
        Paragraph("<b>Rs. 2,18,000.00</b>", styles['TableCellRightBold']),
        Paragraph("6,22,000.00", styles['TableCellRight']),
    ])
    
    t2 = Table(t2_data, colWidths=[205, 110, 68, 75, 65])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0A2540")),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EAEFF5")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8))
    
    # Financial Settlement Summary Table
    fin_reconcile = [
        [
            Paragraph("<b>TOTAL CLAIM BILLED AMOUNT:</b>", styles['TableCellBold']),
            Paragraph("<b>Rs. 14,85,000.00</b>", styles['TableCellRightBold']),
        ],
        [
            Paragraph("<b>TOTAL AMOUNT DISALLOWED / DEDUCTED:</b>", styles['TableCellBold']),
            Paragraph("<font color='#A81D24'><b>Rs. 8,63,000.00</b></font>", styles['TableCellRightBold']),
        ],
        [
            Paragraph("<b>NET APPROVED & TRANSMITTED AMOUNT (NEFT/RTGS):</b>", styles['TableCellBold']),
            Paragraph("<font color='#006600'><b>Rs. 6,22,000.00</b></font>", styles['TableCellRightBold']),
        ],
    ]
    fin_tab = Table(fin_reconcile, colWidths=[330, 193])
    fin_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0A2540")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#D0D0D0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#E8F0FE")),
    ]))
    story.append(fin_tab)
    story.append(Spacer(1, 8))
    
    # Ombudsman Escalation Notice
    omb_text = (
        "<b>STATUTORY NOTICE OF GRIEVANCE REDRESSAL & OMBUDSMAN JURISDICTION:</b><br/>"
        "If you are dissatisfied with this adjudication, you have the statutory right under Insurance Ombudsman Rules, 2017 to appeal. "
        "First approach the Grievance Redressal Officer (GRO) of Bajaj Allianz General Insurance Co. Ltd. at gro@bajajallianz.co.in. "
        "If unresolved within 30 days, an appeal lies before the Insurance Ombudsman (Delhi Jurisdiction), 2/2 A, Universal Insurance Building, "
        "Asaf Ali Road, New Delhi - 110002 (Email: bimalokpal.delhi@cioins.co.in | Phone: 011-23232481) having territorial jurisdiction over Delhi."
    )
    story.append(Paragraph(omb_text, styles['CalloutText']))
    story.append(Spacer(1, 12))
    
    # TPA Signatures
    tpa_sig = [
        [
            Paragraph("Adjudicated by:<br/>Medical Claims Assessor, Heritage Health", styles['TableCell']),
            Paragraph("Reviewed by:<br/>Chief Medical Auditor, Technical Claims Division", styles['TableCell']),
            Paragraph("Authorized Signatory:<br/>Head - Claims Settlement & Disallowances", styles['TableCellBold']),
        ]
    ]
    tpa_sig_tab = Table(tpa_sig, colWidths=[174, 174, 175])
    tpa_sig_tab.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#888888")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tpa_sig_tab)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Heritage Health Rejection Letter: {pdf_path}")


def main():
    target_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\test_docs\extremely_hard_flaws_claim_case"
    os.makedirs(target_dir, exist_ok=True)
    
    bill_pdf = os.path.join(target_dir, "gangaram_hospital_bill.pdf")
    policy_pdf = os.path.join(target_dir, "bajaj_allianz_policy.pdf")
    rejection_pdf = os.path.join(target_dir, "heritage_rejection_letter.pdf")
    
    print("Generating Extremely Hard Flaws Claim Documents...")
    generate_gangaram_hospital_bill(bill_pdf)
    generate_bajaj_allianz_policy(policy_pdf)
    generate_heritage_rejection_letter(rejection_pdf)
    
    # Render high-res PNG pages using pymupdf for direct visual inspection
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
