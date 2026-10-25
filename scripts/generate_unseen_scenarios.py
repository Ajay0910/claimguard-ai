"""
Procedural PDF Generator for 3 Unseen Universal Claim Scenarios:
- Scenario 1: Fortis Healthcare + HDFC ERGO Optima Secure + MDIndia TPA
  (Patient: Amitabh Verma, acute pancreatitis, List III consumables disallowance, room rent deduction)
- Scenario 2: Medanta The Medicity + Niva Bupa ReAssure + FHPL TPA
  (Patient: Meenakshi Iyer, cardiac stenting, cumulative bonus renewal lapse disallowance)
- Scenario 3: Manipal Hospital + ICICI Lombard Complete Health + Medi Assist
  (Patient: Rajesh Kulkarni, laparoscopic surgery, modern treatment day-care sub-limit capping)
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


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
        self.drawString(36, 22, "Official Healthcare & Insurance Record - ClaimGuard Universal Evaluation")
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#0B2545")
    dark_gray = colors.HexColor("#222222")

    styles.add(ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=navy, alignment=1))
    styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10.5, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11.5, textColor=navy, spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle('TableHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('TableCellRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle('ClauseHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=navy, spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyle('ClauseBody', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=dark_gray, spaceBefore=1, spaceAfter=2))
    return styles


# ==============================================================================
# SCENARIO 1: Fortis Healthcare + HDFC ERGO Optima Secure + MDIndia TPA
# ==============================================================================

def generate_scenario_1(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    styles = get_custom_styles()

    # 1. Hospital Bill (Fortis Healthcare)
    bill_path = os.path.join(output_dir, "hospital_bill.pdf")
    doc = SimpleDocTemplate(bill_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story = []

    h_text = (
        "<b>FORTIS HEALTHCARE LIMITED</b><br/>"
        "<font size='7'>Fortis Hospital, 154/9, Bannerghatta Road, Opp IIM-B, Bengaluru - 560076<br/>"
        "NABH & JCI Accredited | GSTIN: 29AAACF1092P1Z5 | Phone: +91-80-6621-4444</font>"
    )
    inv_text = (
        "<font size='11' color='#0B2545'><b>INPATIENT FINAL TAX INVOICE</b></font><br/>"
        "<font size='7.5'>Bill No: <b>FHL/BLR/IPB/2026/04192</b><br/>"
        "Date: <b>17-Feb-2026</b> | Tariff: <b>NABH Corporate / TPA</b></font>"
    )
    story.append(Table([[Paragraph(h_text, styles['TableCell']), Paragraph(inv_text, styles['TableCellRight'])]], colWidths=[330, 193]))
    story.append(Spacer(1, 4))

    pat_info = [
        [
            Paragraph("<b>Patient Name:</b> Mr. Amitabh Verma", styles['TableCell']),
            Paragraph("<b>UHID:</b> FH-2026-88192", styles['TableCell']),
            Paragraph("<b>Age/Sex:</b> 46 Y / Male", styles['TableCell'])
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP-2026-1049", styles['TableCell']),
            Paragraph("<b>Admission:</b> 12-Feb-2026", styles['TableCell']),
            Paragraph("<b>Discharge:</b> 17-Feb-2026", styles['TableCell'])
        ],
        [
            Paragraph("<b>Length of Stay:</b> 5 Days", styles['TableCell']),
            Paragraph("<b>Primary Consultant:</b> Dr. S. K. Sharma (Gastroenterology)", styles['TableCell']),
            Paragraph("<b>Ward:</b> Deluxe AC Room & MICU", styles['TableCell'])
        ],
        [
            Paragraph("<b>Diagnosis:</b> Acute Necrotizing Pancreatitis with Peripancreatic Fluid Collection", styles['TableCell']),
            Paragraph("<b>Procedure:</b> ICU Stabilization, High-Flow Resuscitation & Medical Management", styles['TableCell']),
            Paragraph("<b>Payer / TPA:</b> MDIndia TPA / HDFC ERGO", styles['TableCell'])
        ]
    ]
    t_pat = Table(pat_info, colWidths=[180, 200, 143])
    t_pat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_pat)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN</b>", styles['SectionHeading']))
    items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Description of Service / Procedure</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
        ],
        [Paragraph("1", styles['TableCellCenter']), Paragraph("Single Deluxe AC Room Bed Charges", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("8,000.00", styles['TableCellRight']), Paragraph("24,000.00", styles['TableCellRightBold'])],
        [Paragraph("2", styles['TableCellCenter']), Paragraph("Medical Intensive Care Unit (MICU) Bed Charges", styles['TableCell']), Paragraph("ICU", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("15,000.00", styles['TableCellRight']), Paragraph("30,000.00", styles['TableCellRightBold'])],
        [Paragraph("3", styles['TableCellCenter']), Paragraph("Inpatient Ward General Nursing Care & Monitoring", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("2,000.00", styles['TableCellRight']), Paragraph("6,000.00", styles['TableCellRightBold'])],
        [Paragraph("4", styles['TableCellCenter']), Paragraph("Senior Consultant Gastroenterologist Daily Rounds", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("3,000.00", styles['TableCellRight']), Paragraph("9,000.00", styles['TableCellRightBold'])],
        [Paragraph("5", styles['TableCellCenter']), Paragraph("IV Meropenem & Pancreatitis Infusion Medications", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("75,000.00", styles['TableCellRight']), Paragraph("75,000.00", styles['TableCellRightBold'])],
        [Paragraph("6", styles['TableCellCenter']), Paragraph("Triple Phase Contrast CT Abdomen Pancreatic Protocol", styles['TableCell']), Paragraph("RADIOLOGY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRight']), Paragraph("18,000.00", styles['TableCellRightBold'])],
        [Paragraph("7", styles['TableCellCenter']), Paragraph("Serum Amylase, Lipase & Arterial Blood Gas Series", styles['TableCell']), Paragraph("LAB", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("12,000.00", styles['TableCellRight']), Paragraph("12,000.00", styles['TableCellRightBold'])],
        [Paragraph("8", styles['TableCellCenter']), Paragraph("Sterile Infusion Cannula & Central Line Catheter Kit", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("15,000.00", styles['TableCellRight']), Paragraph("15,000.00", styles['TableCellRightBold'])],
        [Paragraph("9", styles['TableCellCenter']), Paragraph("Major Sterile Surgical Dressing & Sterile Gloves Pack", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("10,000.00", styles['TableCellRight']), Paragraph("10,000.00", styles['TableCellRightBold'])],
        [Paragraph("10", styles['TableCellCenter']), Paragraph("Inpatient Admission Registration & Documentation", styles['TableCell']), Paragraph("MISCELLANEOUS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("2,000.00", styles['TableCellRight']), Paragraph("2,000.00", styles['TableCellRightBold'])],
    ]
    t_items = Table(items, colWidths=[20, 263, 80, 30, 65, 65])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 6))

    tot_table = Table([
        [Paragraph("<b>TOTAL GROSS BILL: Rs. 201,000.00</b>", styles['TableCellRightBold'])]
    ], colWidths=[523])
    tot_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EAEFF8")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tot_table)
    doc.build(story, canvasmaker=NumberedCanvas)

    # 2. Insurance Policy (HDFC ERGO Optima Secure)
    pol_path = os.path.join(output_dir, "insurance_policy.pdf")
    doc_pol = SimpleDocTemplate(pol_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_pol = []

    pol_h = (
        "<b>HDFC ERGO GENERAL INSURANCE COMPANY LIMITED</b><br/>"
        "<font size='7'>1st Floor, HDFC House, 165-166 Backbay Reclamation, H. T. Parekh Marg, Churchgate, Mumbai - 400020<br/>"
        "IRDAI Reg. No. 146 | CIN: U66030MH2007PLC177117 | Policy Schedule & Product Wording</font>"
    )
    story_pol.append(Paragraph(pol_h, styles['TableCell']))
    story_pol.append(Spacer(1, 6))
    story_pol.append(Paragraph("<b>HEALTH INSURANCE POLICY SCHEDULE - OPTIMA SECURE</b>", styles['DocTitle']))
    story_pol.append(Spacer(1, 6))

    sched_rows = [
        [Paragraph("<b>Policy Number:</b> HDFC/OPT/2024/782190", styles['TableCell']), Paragraph("<b>Product UIN:</b> HDFHLIP21054V022021", styles['TableCell'])],
        [Paragraph("<b>Policyholder Name:</b> Mr. Amitabh Verma", styles['TableCell']), Paragraph("<b>Insured Member:</b> Mr. Amitabh Verma (Self, Age 46)", styles['TableCell'])],
        [Paragraph("<b>Original Inception Date:</b> 15-Mar-2021", styles['TableCell']), Paragraph("<b>Current Policy Period:</b> 15-Mar-2025 to 14-Mar-2026", styles['TableCell'])],
        [Paragraph("<b>Base Sum Insured:</b> Rs. 1,000,000.00", styles['TableCell']), Paragraph("<b>Accrued Cumulative Bonus:</b> Rs. 0.00", styles['TableCell'])],
        [Paragraph("<b>Total Sum Insured:</b> Rs. 1,000,000.00", styles['TableCell']), Paragraph("<b>Room Rent Limit:</b> Rs. 5,000 / day", styles['TableCell'])],
        [Paragraph("<b>Co-Payment:</b> 0% (Nil)", styles['TableCell']), Paragraph("<b>Deductible:</b> Rs. 0.00 (Nil)", styles['TableCell'])],
        [Paragraph("<b>Moratorium Period:</b> 60 months", styles['TableCell']), Paragraph("<b>Mental Health Coverage:</b> Covered in full under Mental Healthcare Act", styles['TableCell'])],
    ]
    t_sched = Table(sched_rows, colWidths=[261, 262])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_pol.append(t_sched)
    story_pol.append(Spacer(1, 8))

    story_pol.append(Paragraph("<b>POLICY CLAUSES & TERMS OF COVERAGE</b>", styles['SectionHeading']))
    story_pol.append(Paragraph("<b>Section 1.A: Room Rent Limit & Proportionate Deduction</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "Room rent entitlement under this policy schedule is capped at Rs. 5,000 per day for normal hospital rooms. "
        "If the insured person occupies a room with a tariff higher than the eligible room rent limit of Rs. 5,000 per day, "
        "proportionate deduction shall apply to associated medical charges (nursing care and doctor visits) in the ratio "
        "of eligible room limit to actual room rent charged. ICU charges, medicines, diagnostics and medical procedures "
        "are exempt from proportionate deduction in accordance with IRDAI Master Circular guidelines.",
        styles['ClauseBody']
    ))
    story_pol.append(Paragraph("<b>Section 2.B: Statutory Moratorium & Continuous Coverage</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "After completion of 60 months of continuous coverage under the policy, no policy or claim shall be contestable on grounds "
        "of non-disclosure or misrepresentation, except for proven fraud. Policy moratorium period is strictly 60 months.",
        styles['ClauseBody']
    ))
    doc_pol.build(story_pol, canvasmaker=NumberedCanvas)

    # 3. Rejection / Settlement Letter (MDIndia TPA)
    rej_path = os.path.join(output_dir, "rejection_letter.pdf")
    doc_rej = SimpleDocTemplate(rej_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_rej = []

    tpa_h = (
        "<b>MDINDIA HEALTH INSURANCE TPA PVT. LTD.</b><br/>"
        "<font size='7'>S. No. 46/1, E-Space, A-2 Building, Pune-Nagar Road, Vadgaon Sheri, Pune - 411014<br/>"
        "IRDAI Licensed TPA Reg. No. 005 | Email: claims@mdindia.com | Phone: 1800-233-1166</font>"
    )
    story_rej.append(Paragraph(tpa_h, styles['TableCell']))
    story_rej.append(Spacer(1, 6))
    story_rej.append(Paragraph("<b>CLAIM SETTLEMENT & DEDUCTION ADVICE LETTER</b>", styles['DocTitle']))
    story_rej.append(Spacer(1, 6))

    rej_info = [
        [Paragraph("<b>Claim Ref:</b> MDI/2026/HDFC/991204", styles['TableCell']), Paragraph("<b>Policy No:</b> HDFC/OPT/2024/782190", styles['TableCell'])],
        [Paragraph("<b>Insured Patient:</b> Mr. Amitabh Verma", styles['TableCell']), Paragraph("<b>Hospital:</b> Fortis Hospital, Bannerghatta Road", styles['TableCell'])],
        [Paragraph("<b>Claim Date:</b> 25-Feb-2026", styles['TableCell']), Paragraph("<b>Settlement Type:</b> PARTIAL_SETTLEMENT", styles['TableCell'])],
        [Paragraph("<b>Total Claimed:</b> Rs. 201,000.00", styles['TableCell']), Paragraph("<b>Approved Amount:</b> Rs. 119,000.00", styles['TableCell'])],
        [Paragraph("<b>Total Deducted:</b> Rs. 82,000.00", styles['TableCellBold']), Paragraph("<b>Net Payable:</b> Rs. 119,000.00", styles['TableCellBold'])],
    ]
    t_rej = Table(rej_info, colWidths=[261, 262])
    t_rej.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF9F7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#DEB0B0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F5E0E0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_rej.append(t_rej)
    story_rej.append(Spacer(1, 8))

    story_rej.append(Paragraph("<b>SCHEDULE OF DEDUCTIONS & DISALLOWANCES</b>", styles['SectionHeading']))
    ded_items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Deduction Head / Service</b>", styles['TableHead']),
            Paragraph("<b>Grounds / Citation</b>", styles['TableHead']),
            Paragraph("<b>Claimed (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Deducted (Rs.)</b>", styles['TableHead']),
        ],
        [
            Paragraph("1", styles['TableCellCenter']),
            Paragraph("Room Rent & Proportionate Deduction", styles['TableCell']),
            Paragraph("Room rent exceeded eligible Rs. 5,000/day limit; proportionate deduction applied across hospital bill (Disallowed: Rs. 55,000.00)", styles['TableCell']),
            Paragraph("201,000.00", styles['TableCellRight']),
            Paragraph("146,000.00", styles['TableCellRight']),
            Paragraph("55,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("2", styles['TableCellCenter']),
            Paragraph("Surgical Consumables & Drapes", styles['TableCell']),
            Paragraph("Annexure A Consumables (Cannula, drapes, sterile gloves) disallowed under policy terms (Disallowed: Rs. 25,000.00)", styles['TableCell']),
            Paragraph("25,000.00", styles['TableCellRight']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("25,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("3", styles['TableCellCenter']),
            Paragraph("List I Non-Medical Admin Fee", styles['TableCell']),
            Paragraph("Inpatient admission registration and documentation disallowed under IRDAI Annexure A List I (Disallowed: Rs. 2,000.00)", styles['TableCell']),
            Paragraph("2,000.00", styles['TableCellRight']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("2,000.00", styles['TableCellRightBold']),
        ],
    ]
    t_ded = Table(ded_items, colWidths=[20, 130, 213, 55, 50, 55])
    t_ded.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story_rej.append(t_ded)
    doc_rej.build(story_rej, canvasmaker=NumberedCanvas)


# ==============================================================================
# SCENARIO 2: Medanta The Medicity + Niva Bupa ReAssure + FHPL TPA
# ==============================================================================

def generate_scenario_2(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    styles = get_custom_styles()

    # 1. Hospital Bill (Medanta The Medicity)
    bill_path = os.path.join(output_dir, "hospital_bill.pdf")
    doc = SimpleDocTemplate(bill_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story = []

    h_text = (
        "<b>MEDANTA - THE MEDICITY HOSPITAL</b><br/>"
        "<font size='7'>CH Bakhtawar Singh Road, Sector 38, Gurugram, Haryana - 122001<br/>"
        "NABH & JCI Accredited | GSTIN: 06AAACM4918Q1Z1 | Phone: +91-124-414-1414</font>"
    )
    inv_text = (
        "<font size='11' color='#0B2545'><b>INPATIENT FINAL TAX INVOICE</b></font><br/>"
        "<font size='7.5'>Bill No: <b>MED/GUR/IPB/2026/09214</b><br/>"
        "Date: <b>15-Feb-2026</b> | Tariff: <b>NABH Corporate / TPA</b></font>"
    )
    story.append(Table([[Paragraph(h_text, styles['TableCell']), Paragraph(inv_text, styles['TableCellRight'])]], colWidths=[330, 193]))
    story.append(Spacer(1, 4))

    pat_info = [
        [
            Paragraph("<b>Patient Name:</b> Mrs. Meenakshi Iyer", styles['TableCell']),
            Paragraph("<b>UHID:</b> MED-2026-44910", styles['TableCell']),
            Paragraph("<b>Age/Sex:</b> 58 Y / Female", styles['TableCell'])
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP-2026-8841", styles['TableCell']),
            Paragraph("<b>Admission:</b> 10-Feb-2026", styles['TableCell']),
            Paragraph("<b>Discharge:</b> 15-Feb-2026", styles['TableCell'])
        ],
        [
            Paragraph("<b>Length of Stay:</b> 5 Days", styles['TableCell']),
            Paragraph("<b>Primary Consultant:</b> Dr. Naresh Trehan (Cardiology)", styles['TableCell']),
            Paragraph("<b>Ward:</b> CCU & Single Deluxe Room", styles['TableCell'])
        ],
        [
            Paragraph("<b>Diagnosis:</b> Acute Coronary Syndrome, CAD, PTCA Cardiac Stenting", styles['TableCell']),
            Paragraph("<b>Procedure:</b> Emergency Percutaneous Transluminal Coronary Angioplasty (PTCA)", styles['TableCell']),
            Paragraph("<b>Payer / TPA:</b> FHPL TPA / Niva Bupa Insurance", styles['TableCell'])
        ]
    ]
    t_pat = Table(pat_info, colWidths=[180, 200, 143])
    t_pat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_pat)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN</b>", styles['SectionHeading']))
    items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Description of Service / Procedure</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
        ],
        [Paragraph("1", styles['TableCellCenter']), Paragraph("Coronary Care Unit (CCU) Intensive Bed Charges", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("25,000.00", styles['TableCellRight']), Paragraph("50,000.00", styles['TableCellRightBold'])],
        [Paragraph("2", styles['TableCellCenter']), Paragraph("Single Private AC Room Bed Charges", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("10,000.00", styles['TableCellRight']), Paragraph("30,000.00", styles['TableCellRightBold'])],
        [Paragraph("3", styles['TableCellCenter']), Paragraph("Cardiac Cath Lab Infrastructure & Procedural Charges", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("120,000.00", styles['TableCellRight']), Paragraph("120,000.00", styles['TableCellRightBold'])],
        [Paragraph("4", styles['TableCellCenter']), Paragraph("Chief Interventional Cardiologist Operative Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("150,000.00", styles['TableCellRight']), Paragraph("150,000.00", styles['TableCellRightBold'])],
        [Paragraph("5", styles['TableCellCenter']), Paragraph("Consultant Cardiac Anaesthesiologist Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("35,000.00", styles['TableCellRight']), Paragraph("35,000.00", styles['TableCellRightBold'])],
        [Paragraph("6", styles['TableCellCenter']), Paragraph("Drug-Eluting Coronary Stents (DES Implants)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("140,000.00", styles['TableCellRight']), Paragraph("280,000.00", styles['TableCellRightBold'])],
        [Paragraph("7", styles['TableCellCenter']), Paragraph("PTCA Coronary Balloon Catheter & Guide Wires", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("85,000.00", styles['TableCellRight']), Paragraph("85,000.00", styles['TableCellRightBold'])],
        [Paragraph("8", styles['TableCellCenter']), Paragraph("Coronary Angiography Diagnostic Cine-Loop", styles['TableCell']), Paragraph("RADIOLOGY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("30,000.00", styles['TableCellRight']), Paragraph("30,000.00", styles['TableCellRightBold'])],
        [Paragraph("9", styles['TableCellCenter']), Paragraph("IV Heparin, Glycoprotein Inhibitors & Cardiac Infusion Pharmacy", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("285,000.00", styles['TableCellRight']), Paragraph("285,000.00", styles['TableCellRightBold'])],
        [Paragraph("10", styles['TableCellCenter']), Paragraph("2D Echocardiography, Cardiac Biomarkers & ABG Series", styles['TableCell']), Paragraph("LAB", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("170,000.00", styles['TableCellRight']), Paragraph("170,000.00", styles['TableCellRightBold'])],
        [Paragraph("11", styles['TableCellCenter']), Paragraph("Inpatient Admission Registration & Documentation", styles['TableCell']), Paragraph("MISCELLANEOUS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("5,000.00", styles['TableCellRight']), Paragraph("5,000.00", styles['TableCellRightBold'])],
    ]
    t_items = Table(items, colWidths=[20, 263, 80, 30, 65, 65])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 6))

    tot_table = Table([
        [Paragraph("<b>TOTAL GROSS BILL: Rs. 1,240,000.00</b>", styles['TableCellRightBold'])]
    ], colWidths=[523])
    tot_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EAEFF8")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tot_table)
    doc.build(story, canvasmaker=NumberedCanvas)

    # 2. Insurance Policy (Niva Bupa ReAssure)
    pol_path = os.path.join(output_dir, "insurance_policy.pdf")
    doc_pol = SimpleDocTemplate(pol_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_pol = []

    pol_h = (
        "<b>NIVA BUPA HEALTH INSURANCE COMPANY LIMITED</b><br/>"
        "<font size='7'>Logix Cyber Park, Tower B, Sector 62, Noida, Uttar Pradesh - 201301<br/>"
        "IRDAI Reg. No. 145 | CIN: U66000DL2008PLC182918 | Policy Schedule & Terms</font>"
    )
    story_pol.append(Paragraph(pol_h, styles['TableCell']))
    story_pol.append(Spacer(1, 6))
    story_pol.append(Paragraph("<b>HEALTH INSURANCE POLICY SCHEDULE - REASSURE 2.0</b>", styles['DocTitle']))
    story_pol.append(Spacer(1, 6))

    sched_rows = [
        [Paragraph("<b>Policy Number:</b> NB/REASSURE/2021/884129", styles['TableCell']), Paragraph("<b>Product UIN:</b> NBHHLIP21142V022021", styles['TableCell'])],
        [Paragraph("<b>Policyholder Name:</b> Mrs. Meenakshi Iyer", styles['TableCell']), Paragraph("<b>Insured Member:</b> Mrs. Meenakshi Iyer (Self, Age 58)", styles['TableCell'])],
        [Paragraph("<b>Original Inception Date:</b> 10-Jan-2021", styles['TableCell']), Paragraph("<b>Current Policy Period:</b> 22-Jan-2026 to 21-Jan-2027", styles['TableCell'])],
        [Paragraph("<b>Base Sum Insured:</b> Rs. 1,000,000.00", styles['TableCell']), Paragraph("<b>Accrued Cumulative Bonus:</b> Rs. 500,000.00", styles['TableCell'])],
        [Paragraph("<b>Total Sum Insured:</b> Rs. 1,500,000.00", styles['TableCell']), Paragraph("<b>Room Entitlement:</b> Single Private Room (No Limit)", styles['TableCell'])],
        [Paragraph("<b>Co-Payment:</b> 0% (Nil)", styles['TableCell']), Paragraph("<b>Deductible:</b> Rs. 0.00 (Nil)", styles['TableCell'])],
        [Paragraph("<b>Moratorium Period:</b> 60 months", styles['TableCell']), Paragraph("<b>Mental Health Coverage:</b> Covered in full under Mental Healthcare Act", styles['TableCell'])],
    ]
    t_sched = Table(sched_rows, colWidths=[261, 262])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_pol.append(t_sched)
    story_pol.append(Spacer(1, 8))

    story_pol.append(Paragraph("<b>POLICY CLAUSES & TERMS OF COVERAGE</b>", styles['SectionHeading']))
    story_pol.append(Paragraph("<b>Section 3.1: Room Rent & Accommodation Entitlement</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "The insured person is entitled to Single Private AC Room without any monetary capping or proportionate deduction.",
        styles['ClauseBody']
    ))
    story_pol.append(Paragraph("<b>Section 6.1: Cumulative Bonus & Renewal Grace Period Rules</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "A statutory renewal grace period of 30 days is provided from policy anniversary. Premium payment within the 30-day "
        "statutory grace period preserves full continuity of coverage and accrued cumulative bonus in compliance with Regulation 13 "
        "of IRDAI (Health Insurance) Regulations, 2016 and IRDAI Master Circular (29 May 2024, Chapter III, Para 3.8).",
        styles['ClauseBody']
    ))
    doc_pol.build(story_pol, canvasmaker=NumberedCanvas)

    # 3. Rejection / Settlement Letter (FHPL TPA)
    rej_path = os.path.join(output_dir, "rejection_letter.pdf")
    doc_rej = SimpleDocTemplate(rej_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_rej = []

    tpa_h = (
        "<b>FAMILY HEALTH PLAN INSURANCE TPA LIMITED (FHPL)</b><br/>"
        "<font size='7'>Srinilaya Cyber Spazio, Road No. 2, Banjara Hills, Hyderabad, Telangana - 500034<br/>"
        "IRDAI Licensed TPA Reg. No. 013 | Email: info@fhpl.net | Phone: 1800-425-4033</font>"
    )
    story_rej.append(Paragraph(tpa_h, styles['TableCell']))
    story_rej.append(Spacer(1, 6))
    story_rej.append(Paragraph("<b>CLAIM SETTLEMENT & DEDUCTION ADVICE LETTER</b>", styles['DocTitle']))
    story_rej.append(Spacer(1, 6))

    rej_info = [
        [Paragraph("<b>Claim Ref:</b> FHPL/2026/NB/441209", styles['TableCell']), Paragraph("<b>Policy No:</b> NB/REASSURE/2021/884129", styles['TableCell'])],
        [Paragraph("<b>Insured Patient:</b> Mrs. Meenakshi Iyer", styles['TableCell']), Paragraph("<b>Hospital:</b> Medanta - The Medicity, Gurugram", styles['TableCell'])],
        [Paragraph("<b>Claim Date:</b> 20-Feb-2026", styles['TableCell']), Paragraph("<b>Settlement Type:</b> PARTIAL_SETTLEMENT", styles['TableCell'])],
        [Paragraph("<b>Total Claimed:</b> Rs. 1,240,000.00", styles['TableCell']), Paragraph("<b>Approved Amount:</b> Rs. 995,000.00", styles['TableCell'])],
        [Paragraph("<b>Total Deducted:</b> Rs. 245,000.00", styles['TableCellBold']), Paragraph("<b>Net Payable:</b> Rs. 995,000.00", styles['TableCellBold'])],
    ]
    t_rej = Table(rej_info, colWidths=[261, 262])
    t_rej.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF9F7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#DEB0B0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F5E0E0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_rej.append(t_rej)
    story_rej.append(Spacer(1, 8))

    story_rej.append(Paragraph("<b>SCHEDULE OF DEDUCTIONS & DISALLOWANCES</b>", styles['SectionHeading']))
    ded_items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Deduction Head / Service</b>", styles['TableHead']),
            Paragraph("<b>Grounds / Citation</b>", styles['TableHead']),
            Paragraph("<b>Claimed (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Deducted (Rs.)</b>", styles['TableHead']),
        ],
        [
            Paragraph("1", styles['TableCellCenter']),
            Paragraph("Sum Insured Cap / Bonus Forfeiture", styles['TableCell']),
            Paragraph("Cumulative bonus of Rs. 500,000 stands forfeited due to delayed renewal premium payment on 22-Jan-2026. Coverage capped at Base Sum Insured Rs. 1,000,000 (Disallowed: Rs. 240,000.00)", styles['TableCell']),
            Paragraph("1,240,000.00", styles['TableCellRight']),
            Paragraph("995,000.00", styles['TableCellRight']),
            Paragraph("240,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("2", styles['TableCellCenter']),
            Paragraph("List I Non-Medical Admin Fee", styles['TableCell']),
            Paragraph("Inpatient admission registration and administrative documentation disallowed under IRDAI Annexure A List I (Disallowed: Rs. 5,000.00)", styles['TableCell']),
            Paragraph("5,000.00", styles['TableCellRight']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("5,000.00", styles['TableCellRightBold']),
        ],
    ]
    t_ded = Table(ded_items, colWidths=[20, 130, 213, 55, 50, 55])
    t_ded.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story_rej.append(t_ded)
    doc_rej.build(story_rej, canvasmaker=NumberedCanvas)


# ==============================================================================
# SCENARIO 3: Manipal Hospital + ICICI Lombard Complete Health + Medi Assist
# ==============================================================================

def generate_scenario_3(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    styles = get_custom_styles()

    # 1. Hospital Bill (Manipal Hospital)
    bill_path = os.path.join(output_dir, "hospital_bill.pdf")
    doc = SimpleDocTemplate(bill_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story = []

    h_text = (
        "<b>MANIPAL HOSPITAL</b><br/>"
        "<font size='7'>98, HAL Airport Road, Kodihalli, Bengaluru, Karnataka - 560017<br/>"
        "NABH & JCI Accredited | GSTIN: 29AABCM1890L1Z2 | Phone: +91-80-2502-4444</font>"
    )
    inv_text = (
        "<font size='11' color='#0B2545'><b>INPATIENT FINAL TAX INVOICE</b></font><br/>"
        "<font size='7.5'>Bill No: <b>MH/BLR/IPB/2026/05819</b><br/>"
        "Date: <b>08-Mar-2026</b> | Tariff: <b>NABH Corporate / TPA</b></font>"
    )
    story.append(Table([[Paragraph(h_text, styles['TableCell']), Paragraph(inv_text, styles['TableCellRight'])]], colWidths=[330, 193]))
    story.append(Spacer(1, 4))

    pat_info = [
        [
            Paragraph("<b>Patient Name:</b> Mr. Rajesh Kulkarni", styles['TableCell']),
            Paragraph("<b>UHID:</b> MH-2026-77812", styles['TableCell']),
            Paragraph("<b>Age/Sex:</b> 42 Y / Male", styles['TableCell'])
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP-2026-3391", styles['TableCell']),
            Paragraph("<b>Admission:</b> 05-Mar-2026", styles['TableCell']),
            Paragraph("<b>Discharge:</b> 08-Mar-2026", styles['TableCell'])
        ],
        [
            Paragraph("<b>Length of Stay:</b> 3 Days", styles['TableCell']),
            Paragraph("<b>Primary Consultant:</b> Dr. Sudarshan Ballal (Surgery)", styles['TableCell']),
            Paragraph("<b>Ward:</b> Single Private AC Room", styles['TableCell'])
        ],
        [
            Paragraph("<b>Diagnosis:</b> Acute Gangrenous Appendicitis with Localized Peritonitis", styles['TableCell']),
            Paragraph("<b>Procedure:</b> Emergency Laparoscopic Appendectomy & Peritoneal Lavage", styles['TableCell']),
            Paragraph("<b>Payer / TPA:</b> Medi Assist TPA / ICICI Lombard", styles['TableCell'])
        ]
    ]
    t_pat = Table(pat_info, colWidths=[180, 200, 143])
    t_pat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_pat)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN</b>", styles['SectionHeading']))
    items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Description of Service / Procedure</b>", styles['TableHead']),
            Paragraph("<b>Category</b>", styles['TableHead']),
            Paragraph("<b>Qty</b>", styles['TableHead']),
            Paragraph("<b>Rate (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Total (Rs.)</b>", styles['TableHead'])
        ],
        [Paragraph("1", styles['TableCellCenter']), Paragraph("Single Private AC Room Bed Charges", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("8,000.00", styles['TableCellRight']), Paragraph("24,000.00", styles['TableCellRightBold'])],
        [Paragraph("2", styles['TableCellCenter']), Paragraph("Inpatient Ward Nursing Care & Monitoring", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("2,000.00", styles['TableCellRight']), Paragraph("6,000.00", styles['TableCellRightBold'])],
        [Paragraph("3", styles['TableCellCenter']), Paragraph("Chief Laparoscopic Surgeon Operative Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("45,000.00", styles['TableCellRight']), Paragraph("45,000.00", styles['TableCellRightBold'])],
        [Paragraph("4", styles['TableCellCenter']), Paragraph("Senior Consultant Anaesthesiologist Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRight']), Paragraph("18,000.00", styles['TableCellRightBold'])],
        [Paragraph("5", styles['TableCellCenter']), Paragraph("Major Operation Theatre Complex Infrastructure", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("35,000.00", styles['TableCellRight']), Paragraph("35,000.00", styles['TableCellRightBold'])],
        [Paragraph("6", styles['TableCellCenter']), Paragraph("Advanced Laparoscopic Tower & Insufflator Suite", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("25,000.00", styles['TableCellRight']), Paragraph("25,000.00", styles['TableCellRightBold'])],
        [Paragraph("7", styles['TableCellCenter']), Paragraph("Laparoscopic Ultrasonic Trocar & Port Access Kit", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("22,000.00", styles['TableCellRight']), Paragraph("22,000.00", styles['TableCellRightBold'])],
        [Paragraph("8", styles['TableCellCenter']), Paragraph("Laparoscopic Endo GIA Vascular Staplers & Cartridges", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("38,000.00", styles['TableCellRight']), Paragraph("38,000.00", styles['TableCellRightBold'])],
        [Paragraph("9", styles['TableCellCenter']), Paragraph("IV Ceftriaxone, Metronidazole & Inpatient Pharmacy", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("42,000.00", styles['TableCellRight']), Paragraph("42,000.00", styles['TableCellRightBold'])],
        [Paragraph("10", styles['TableCellCenter']), Paragraph("Contrast Enhanced Abdominal CT & Ultrasound", styles['TableCell']), Paragraph("RADIOLOGY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRight']), Paragraph("18,000.00", styles['TableCellRightBold'])],
        [Paragraph("11", styles['TableCellCenter']), Paragraph("Histopathology & Pre-op Diagnostic Labs", styles['TableCell']), Paragraph("LAB", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("14,000.00", styles['TableCellRight']), Paragraph("14,000.00", styles['TableCellRightBold'])],
        [Paragraph("12", styles['TableCellCenter']), Paragraph("Inpatient Admission Registration & Documentation", styles['TableCell']), Paragraph("MISCELLANEOUS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("3,000.00", styles['TableCellRight']), Paragraph("3,000.00", styles['TableCellRightBold'])],
    ]
    t_items = Table(items, colWidths=[20, 263, 80, 30, 65, 65])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 6))

    tot_table = Table([
        [Paragraph("<b>TOTAL GROSS BILL: Rs. 290,000.00</b>", styles['TableCellRightBold'])]
    ], colWidths=[523])
    tot_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EAEFF8")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tot_table)
    doc.build(story, canvasmaker=NumberedCanvas)

    # 2. Insurance Policy (ICICI Lombard Complete Health)
    pol_path = os.path.join(output_dir, "insurance_policy.pdf")
    doc_pol = SimpleDocTemplate(pol_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_pol = []

    pol_h = (
        "<b>ICICI LOMBARD GENERAL INSURANCE COMPANY LIMITED</b><br/>"
        "<font size='7'>ICICI Lombard House, 414, Veer Savarkar Marg, Near Siddhivinayak Temple, Prabhadevi, Mumbai - 400025<br/>"
        "IRDAI Reg. No. 115 | CIN: L67200MH2000PLC129408 | Policy Schedule & Clauses</font>"
    )
    story_pol.append(Paragraph(pol_h, styles['TableCell']))
    story_pol.append(Spacer(1, 6))
    story_pol.append(Paragraph("<b>COMPLETE HEALTH INSURANCE POLICY SCHEDULE</b>", styles['DocTitle']))
    story_pol.append(Spacer(1, 6))

    sched_rows = [
        [Paragraph("<b>Policy Number:</b> ICICI/CHI/2023/339102", styles['TableCell']), Paragraph("<b>Product UIN:</b> ICIHLIP21383V052021", styles['TableCell'])],
        [Paragraph("<b>Policyholder Name:</b> Mr. Rajesh Kulkarni", styles['TableCell']), Paragraph("<b>Insured Member:</b> Mr. Rajesh Kulkarni (Self, Age 42)", styles['TableCell'])],
        [Paragraph("<b>Original Inception Date:</b> 01-Jan-2022", styles['TableCell']), Paragraph("<b>Current Policy Period:</b> 01-Jan-2026 to 31-Dec-2026", styles['TableCell'])],
        [Paragraph("<b>Base Sum Insured:</b> Rs. 800,000.00", styles['TableCell']), Paragraph("<b>Accrued Cumulative Bonus:</b> Rs. 0.00", styles['TableCell'])],
        [Paragraph("<b>Total Sum Insured:</b> Rs. 800,000.00", styles['TableCell']), Paragraph("<b>Room Entitlement:</b> Single Private AC Room", styles['TableCell'])],
        [Paragraph("<b>Co-Payment:</b> 0% (Nil)", styles['TableCell']), Paragraph("<b>Deductible:</b> Rs. 0.00 (Nil)", styles['TableCell'])],
        [Paragraph("<b>Moratorium Period:</b> 60 months", styles['TableCell']), Paragraph("<b>Mental Health Coverage:</b> Covered in full under Mental Healthcare Act", styles['TableCell'])],
    ]
    t_sched = Table(sched_rows, colWidths=[261, 262])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FBFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_pol.append(t_sched)
    story_pol.append(Spacer(1, 8))

    story_pol.append(Paragraph("<b>POLICY CLAUSES & TERMS OF COVERAGE</b>", styles['SectionHeading']))
    story_pol.append(Paragraph("<b>Section 2.1: Room Rent & Boarding Entitlement</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "Single Private AC room accommodation is covered without room rent limit per day or proportionate deduction.",
        styles['ClauseBody']
    ))
    story_pol.append(Paragraph("<b>Clause 4.14: Modern Treatment & Day-Care Sub-Limits</b>", styles['ClauseHeading']))
    story_pol.append(Paragraph(
        "Modern treatments and specialized advanced technological methods (including advanced endoscopic/laparoscopic day-care procedures) "
        "are covered subject to an elective day-care sub-limit of Rs. 40,000 per procedure.",
        styles['ClauseBody']
    ))
    doc_pol.build(story_pol, canvasmaker=NumberedCanvas)

    # 3. Rejection / Settlement Letter (Medi Assist TPA)
    rej_path = os.path.join(output_dir, "rejection_letter.pdf")
    doc_rej = SimpleDocTemplate(rej_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=42)
    story_rej = []

    tpa_h = (
        "<b>MEDI ASSIST INSURANCE TPA PVT. LTD.</b><br/>"
        "<font size='7'>Tower D, 4th Floor, IBC Knowledge Park, 4/1, Bannerghatta Road, Bengaluru - 560029<br/>"
        "IRDAI Licensed TPA Reg. No. 003 | Email: claims@mediassist.in | Phone: 1800-425-9449</font>"
    )
    story_rej.append(Paragraph(tpa_h, styles['TableCell']))
    story_rej.append(Spacer(1, 6))
    story_rej.append(Paragraph("<b>CLAIM SETTLEMENT & DEDUCTION ADVICE LETTER</b>", styles['DocTitle']))
    story_rej.append(Spacer(1, 6))

    rej_info = [
        [Paragraph("<b>Claim Ref:</b> MA/2026/ICICI/552109", styles['TableCell']), Paragraph("<b>Policy No:</b> ICICI/CHI/2023/339102", styles['TableCell'])],
        [Paragraph("<b>Insured Patient:</b> Mr. Rajesh Kulkarni", styles['TableCell']), Paragraph("<b>Hospital:</b> Manipal Hospital, HAL Airport Road", styles['TableCell'])],
        [Paragraph("<b>Claim Date:</b> 15-Mar-2026", styles['TableCell']), Paragraph("<b>Settlement Type:</b> PARTIAL_SETTLEMENT", styles['TableCell'])],
        [Paragraph("<b>Total Claimed:</b> Rs. 290,000.00", styles['TableCell']), Paragraph("<b>Approved Amount:</b> Rs. 257,000.00", styles['TableCell'])],
        [Paragraph("<b>Total Deducted:</b> Rs. 33,000.00", styles['TableCellBold']), Paragraph("<b>Net Payable:</b> Rs. 257,000.00", styles['TableCellBold'])],
    ]
    t_rej = Table(rej_info, colWidths=[261, 262])
    t_rej.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF9F7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#DEB0B0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F5E0E0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story_rej.append(t_rej)
    story_rej.append(Spacer(1, 8))

    story_rej.append(Paragraph("<b>SCHEDULE OF DEDUCTIONS & DISALLOWANCES</b>", styles['SectionHeading']))
    ded_items = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Deduction Head / Service</b>", styles['TableHead']),
            Paragraph("<b>Grounds / Citation</b>", styles['TableHead']),
            Paragraph("<b>Claimed (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Deducted (Rs.)</b>", styles['TableHead']),
        ],
        [
            Paragraph("1", styles['TableCellCenter']),
            Paragraph("Modern Treatment Capping (Endoscopic Sub-Limit Exhaustion)", styles['TableCell']),
            Paragraph("Clause 4.14: Modern treatment day-care sub-limit capping applied to laparoscopic surgery (Disallowance of Rs. 30,000.00 under Clause 4.14)", styles['TableCell']),
            Paragraph("290,000.00", styles['TableCellRight']),
            Paragraph("260,000.00", styles['TableCellRight']),
            Paragraph("30,000.00", styles['TableCellRightBold']),
        ],
        [
            Paragraph("2", styles['TableCellCenter']),
            Paragraph("List I Non-Medical Overheads", styles['TableCell']),
            Paragraph("Inpatient admission registration and documentation disallowed under IRDAI Annexure A List I (Disallowed: Rs. 3,000.00)", styles['TableCell']),
            Paragraph("3,000.00", styles['TableCellRight']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("3,000.00", styles['TableCellRightBold']),
        ],
    ]
    t_ded = Table(ded_items, colWidths=[20, 130, 213, 55, 50, 55])
    t_ded.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story_rej.append(t_ded)
    doc_rej.build(story_rej, canvasmaker=NumberedCanvas)


def generate_all_scenarios(base_dir: str):
    s1_dir = os.path.join(base_dir, "scenario_1_fortis_hdfc_mdindia")
    s2_dir = os.path.join(base_dir, "scenario_2_medanta_nivabupa_fhpl")
    s3_dir = os.path.join(base_dir, "scenario_3_manipal_icici_mediassist")

    generate_scenario_1(s1_dir)
    generate_scenario_2(s2_dir)
    generate_scenario_3(s3_dir)
    print("All 3 unseen scenarios generated successfully.")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_docs", "unseen_scenarios")
    generate_all_scenarios(target)
