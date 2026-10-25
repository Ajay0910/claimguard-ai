"""
Realistic Complex Claim Documents Generator for ClaimGuard AI.
Generates:
1. Apollo Hospitals Inpatient Final Bill (2 pages: itemized billing with emergency admission certificate)
2. Star Health Comprehensive Insurance Policy Schedule & Terms (2 pages: policy schedule & statutory clauses)
3. Medi Assist TPA Claim Settlement / Deduction Advice Letter (2 pages: formal rejection with 4 subtle flaws)
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
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
        self.drawString(36, 22, "Official Legal Document - Medical & Insurance Adjudication Record")
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()
    
    navy = colors.HexColor("#0B2545")
    crimson = colors.HexColor("#8B0000")
    dark_gray = colors.HexColor("#222222")
    
    styles.add(ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=navy, alignment=1))
    styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=navy, spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle('SectionHeadingRed', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=crimson, spaceBefore=4, spaceAfter=3))
    
    styles.add(ParagraphStyle('TableHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellSmall', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=dark_gray))
    styles.add(ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=dark_gray, alignment=1))
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=dark_gray, alignment=2))
    styles.add(ParagraphStyle('TableCellRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=dark_gray, alignment=2))
    
    styles.add(ParagraphStyle('LegalClauseTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=navy, spaceBefore=3, spaceAfter=1))
    styles.add(ParagraphStyle('LegalClause', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=dark_gray, spaceBefore=1, spaceAfter=3))
    styles.add(ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle('FooterDisclaimer', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor("#555555")))
    
    return styles


# ==============================================================================
# 1. HOSPITAL BILL GENERATOR (Apollo Hospitals Bannerghatta Road, Bengaluru)
# ==============================================================================

def generate_hospital_bill(output_path: str):
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

    # --- PAGE 1: Header, Patient Details, Triage Certificate & Items 1-13 ---
    h_text = (
        "<b>APOLLO HOSPITALS ENTERPRISE LIMITED</b><br/>"
        "<font size='7.5'>154/11, Bannerghatta Main Road, Opp. IIM-B, Bengaluru - 560076, Karnataka<br/>"
        "NABH & JCI Accredited | GSTIN: 29AAACA2894K1Z0 | CIN: L85110TN1979PLC008035<br/>"
        "Phone: +91-80-2630-4050 | Email: billing.bannerghatta@apollohospitals.com</font>"
    )
    inv_text = (
        "<font size='12' color='#0B2545'><b>INPATIENT FINAL BILL</b></font><br/>"
        "<font size='8'><b>TAX INVOICE / SUMMARY</b><br/>"
        "Bill No: <b>AHB/IPB/2026/08941</b><br/>"
        "Bill Date: <b>18-Feb-2026 16:45</b></font>"
    )
    t_head = Table([[Paragraph(h_text, styles['TableCell']), Paragraph(inv_text, styles['TableCellRight'])]], colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#0B2545")),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 5))

    pat_data = [
        [
            Paragraph("<b>Patient Name:</b> Mr. Vikramaditya Singhania", styles['TableCell']),
            Paragraph("<b>UHID / MRN:</b> AP-BLR-2026-98124", styles['TableCell']),
            Paragraph("<b>Age / Sex:</b> 52 Y / Male", styles['TableCell']),
        ],
        [
            Paragraph("<b>IP Admission No:</b> IP/2026/044192", styles['TableCell']),
            Paragraph("<b>Admission:</b> 12-Feb-2026 02:15 AM (Emergency ER)", styles['TableCell']),
            Paragraph("<b>Discharge:</b> 18-Feb-2026 16:30 PM", styles['TableCell']),
        ],
        [
            Paragraph("<b>Primary Consultant:</b> Dr. Srinivas Rao, MS, MCh (GI Surgery)", styles['TableCell']),
            Paragraph("<b>Consultant Anaesthetist:</b> Dr. Meera Nambiar, MD, DNB", styles['TableCell']),
            Paragraph("<b>Ward:</b> SICU (2 Days) + Deluxe Room (4 Days)", styles['TableCell']),
        ],
        [
            Paragraph("<b>Diagnosis:</b> Acute Diverticulitis with Perforation & Peritonitis", styles['TableCell']),
            Paragraph("<b>Procedure:</b> Emergency Exploratory Laparotomy, Sigmoid Resection, Hartmann's Procedure", styles['TableCell']),
            Paragraph("<b>Payer / TPA:</b> Medi Assist TPA / Star Health Ins.", styles['TableCell']),
        ]
    ]
    t_pat = Table(pat_data, colWidths=[180, 200, 143])
    t_pat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFD")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0EAF5")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_pat)
    story.append(Spacer(1, 6))

    er_note = [
        [Paragraph("<b>HOSPITAL EMERGENCY TRIAGE & ROOM ALLOCATION CERTIFICATE:</b><br/>"
                   "Patient arrived in septic emergency at 02:15 AM on 12-Feb-2026 with bowel perforation. Directly admitted to SICU (2 days). "
                   "Upon ward transfer on 14-Feb-2026, Single Private A/C rooms were 100% occupied (Zero vacancy certified in Bed Bureau Log #ER-8841). "
                   "Patient was temporarily accommodated in Deluxe Room as an emergency life-safety measure.", styles['CalloutText'])]
    ]
    t_er = Table(er_note, colWidths=[523])
    t_er.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF8E7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D4A373")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_er)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN - PART I (HOSPITALIZATION & SURGICAL SERVICES)</b>", styles['SectionHeading']))
    
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
        [Paragraph("1", styles['TableCellCenter']), Paragraph("Surgical Intensive Care Unit (SICU) Bed Charges", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("14,000.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("28,000.00", styles['TableCellRightBold'])],
        [Paragraph("2", styles['TableCellCenter']), Paragraph("SICU Specialized Critical Care Nursing & Vital Monitoring", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("4,000.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("8,000.00", styles['TableCellRightBold'])],
        [Paragraph("3", styles['TableCellCenter']), Paragraph("Deluxe Private AC Room Accommodation (Ward Bed #412)", styles['TableCell']), Paragraph("ROOM", styles['TableCell']), Paragraph("4", styles['TableCellCenter']), Paragraph("10,000.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("40,000.00", styles['TableCellRightBold'])],
        [Paragraph("4", styles['TableCellCenter']), Paragraph("General Inpatient Nursing Care & RMO Medical Supervision", styles['TableCell']), Paragraph("NURSING", styles['TableCell']), Paragraph("4", styles['TableCellCenter']), Paragraph("2,500.00", styles['TableCellRight']), Paragraph("999311", styles['TableCellCenter']), Paragraph("10,000.00", styles['TableCellRightBold'])],
        [Paragraph("5", styles['TableCellCenter']), Paragraph("Primary Surgeon Operative Fee - Emergency Hartmann's Resection", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("95,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("95,000.00", styles['TableCellRightBold'])],
        [Paragraph("6", styles['TableCellCenter']), Paragraph("Assistant Surgeon Professional Fee (Emergency Laparotomy)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("25,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("25,000.00", styles['TableCellRightBold'])],
        [Paragraph("7", styles['TableCellCenter']), Paragraph("Consultant Anaesthesiologist Charge (Major Surgery 4.5 hrs)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("30,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("30,000.00", styles['TableCellRightBold'])],
        [Paragraph("8", styles['TableCellCenter']), Paragraph("Intensivist Critical Care Management & Daily Rounds (SICU)", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("7,500.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("15,000.00", styles['TableCellRightBold'])],
        [Paragraph("9", styles['TableCellCenter']), Paragraph("Major Operation Theatre Complex Charges (Emergency Slot)", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("45,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("45,000.00", styles['TableCellRightBold'])],
        [Paragraph("10", styles['TableCellCenter']), Paragraph("Anaesthesia Workstation, Multi-Para Monitoring & EtCO2", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("18,000.00", styles['TableCellRightBold'])],
        [Paragraph("11", styles['TableCellCenter']), Paragraph("Advanced Electrosurgical Cautery Unit & Ultrasonic Shear", styles['TableCell']), Paragraph("OT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("12,000.00", styles['TableCellRight']), Paragraph("999313", styles['TableCellCenter']), Paragraph("12,000.00", styles['TableCellRightBold'])],
        [Paragraph("12", styles['TableCellCenter']), Paragraph("Endo-GIA 60mm Articulating Bowel Linear Stapler Kit (Device)", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("42,000.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("42,000.00", styles['TableCellRightBold'])],
        [Paragraph("13", styles['TableCellCenter']), Paragraph("Endo-GIA Tri-Staple Reload Cartridges (Purple/Gold 3.5mm)", styles['TableCell']), Paragraph("IMPLANT", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("13,000.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("26,000.00", styles['TableCellRightBold'])],
    ]

    t_p1 = Table(items_p1, colWidths=[20, 245, 70, 25, 55, 45, 63])
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    for row_idx in range(1, len(items_p1)):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 1 else colors.HexColor("#F9FBFE")
        t_p1.setStyle(TableStyle([('BACKGROUND', (0, row_idx), (-1, row_idx), bg)]))
    story.append(t_p1)

    story.append(PageBreak())

    # --- PAGE 2: Items 14-27, Tariff Note, Bill Summary & Signatures ---
    story.append(Paragraph("<b>ITEMIZED CHARGES BREAKDOWN - PART II (CONSUMABLES, PHARMACY & DIAGNOSTICS)</b>", styles['SectionHeading']))
    
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
        [Paragraph("14", styles['TableCellCenter']), Paragraph("Laparotomy Sterile Drape Pack & Surgical Gown Set (IRDAI List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRightBold'])],
        [Paragraph("15", styles['TableCellCenter']), Paragraph("Sterile Surgical Powder-Free Latex Gloves (Size 7.0/7.5, 12 prs - List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("12", styles['TableCellCenter']), Paragraph("350.00", styles['TableCellRight']), Paragraph("401511", styles['TableCellCenter']), Paragraph("4,200.00", styles['TableCellRightBold'])],
        [Paragraph("16", styles['TableCellCenter']), Paragraph("Abdominal Suction Irrigation Cannula & Tubing Set (IRDAI List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("4,100.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("4,100.00", styles['TableCellRightBold'])],
        [Paragraph("17", styles['TableCellCenter']), Paragraph("Antibacterial Polyglactin / PDS Suture Loops & Clips (IRDAI List III)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("9,800.00", styles['TableCellRight']), Paragraph("300610", styles['TableCellCenter']), Paragraph("9,800.00", styles['TableCellRightBold'])],
        [Paragraph("18", styles['TableCellCenter']), Paragraph("Ostomy Appliance Stoma Bag System (Post-Hartmann Colostomy)", styles['TableCell']), Paragraph("CONSUMABLES", styles['TableCell']), Paragraph("2", styles['TableCellCenter']), Paragraph("4,100.00", styles['TableCellRight']), Paragraph("901890", styles['TableCellCenter']), Paragraph("8,200.00", styles['TableCellRightBold'])],
        [Paragraph("19", styles['TableCellCenter']), Paragraph("IV Meropenem 1g Infusion (T.I.D. x 5 days - Peritonitis Protocol)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("15", styles['TableCellCenter']), Paragraph("2,450.00", styles['TableCellRight']), Paragraph("300420", styles['TableCellCenter']), Paragraph("36,750.00", styles['TableCellRightBold'])],
        [Paragraph("20", styles['TableCellCenter']), Paragraph("IV Human Albumin 20% 100ml Infusion (Septic Hypoalbuminemia)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("4,800.00", styles['TableCellRight']), Paragraph("300212", styles['TableCellCenter']), Paragraph("14,400.00", styles['TableCellRightBold'])],
        [Paragraph("21", styles['TableCellCenter']), Paragraph("IV Paracetamol, Tramadol, Ondansetron & PPI Injections", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRight']), Paragraph("300490", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRightBold'])],
        [Paragraph("22", styles['TableCellCenter']), Paragraph("Total Parenteral Nutrition (TPN Olimel Peri N4E 1000ml)", styles['TableCell']), Paragraph("PHARMACY", styles['TableCell']), Paragraph("3", styles['TableCellCenter']), Paragraph("3,600.00", styles['TableCellRight']), Paragraph("300450", styles['TableCellCenter']), Paragraph("10,800.00", styles['TableCellRightBold'])],
        [Paragraph("23", styles['TableCellCenter']), Paragraph("Emergency Contrast-Enhanced CT Abdomen & Pelvis (Triple Phase)", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("14,500.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("14,500.00", styles['TableCellRightBold'])],
        [Paragraph("24", styles['TableCellCenter']), Paragraph("Histopathology Examination - Large Resection Specimen (Malignancy R/O)", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("8,500.00", styles['TableCellRightBold'])],
        [Paragraph("25", styles['TableCellCenter']), Paragraph("Complete Metabolic Panel series, ABG, Blood Cultures & Coagulation", styles['TableCell']), Paragraph("DIAGNOSTICS", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("11,500.00", styles['TableCellRight']), Paragraph("999315", styles['TableCellCenter']), Paragraph("11,500.00", styles['TableCellRightBold'])],
        [Paragraph("26", styles['TableCellCenter']), Paragraph("Admission Administrative Registration & Bio-hazard Disposal Fee", styles['TableCell']), Paragraph("NON_MEDICAL", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("2,500.00", styles['TableCellRight']), Paragraph("999319", styles['TableCellCenter']), Paragraph("2,500.00", styles['TableCellRightBold'])],
        [Paragraph("27", styles['TableCellCenter']), Paragraph("Patient Care Toiletries Kit, Slippers & Sanitizer Kit (List I)", styles['TableCell']), Paragraph("NON_MEDICAL", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("1,500.00", styles['TableCellRight']), Paragraph("999319", styles['TableCellCenter']), Paragraph("1,500.00", styles['TableCellRightBold'])],
        [Paragraph("28", styles['TableCellCenter']), Paragraph("Emergency Triage, Resuscitation & Surgical Clearance Fee", styles['TableCell']), Paragraph("CONSULTATION", styles['TableCell']), Paragraph("1", styles['TableCellCenter']), Paragraph("11,000.00", styles['TableCellRight']), Paragraph("999312", styles['TableCellCenter']), Paragraph("11,000.00", styles['TableCellRightBold'])],
    ]

    t_p2 = Table(items_p2, colWidths=[20, 245, 70, 25, 55, 45, 63])
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B2545")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    for row_idx in range(1, len(items_p2)):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 1 else colors.HexColor("#F9FBFE")
        t_p2.setStyle(TableStyle([('BACKGROUND', (0, row_idx), (-1, row_idx), bg)]))
    story.append(t_p2)
    story.append(Spacer(1, 8))

    # Summary Box
    summary_data = [
        [
            Paragraph("<b>INSTITUTIONAL FLAT TARIFF CERTIFICATE:</b><br/>"
                      "Apollo Hospitals Bengaluru operates on an institutional procedural tariff. "
                      "Surgeon operative fees, Anaesthesia fees, and OT package charges are fixed by surgical code "
                      "and DO NOT vary with the room category chosen by the patient.", styles['CalloutText']),
            Paragraph("<font size='8'><b>Sub-Total (Medical Services):</b><br/>"
                      "<b>Pharmacy & Surgical Implants:</b><br/>"
                      "<b>Non-Medical Overhead (List I):</b><br/>"
                      "<b>Healthcare GST Exemption (0%):</b><br/>"
                      "<font size='9' color='#0B2545'><b>TOTAL GROSS BILL:</b></font></font>", styles['TableCellRight']),
            Paragraph("<font size='8'>Rs. 3,88,600.00<br/>"
                      "Rs. 1,56,150.00<br/>"
                      "Rs. 4,000.00<br/>"
                      "Rs. 0.00<br/>"
                      "<font size='9' color='#0B2545'><b>Rs. 5,48,750.00</b></font></font>", styles['TableCellRightBold'])
        ]
    ]
    t_sum = Table(summary_data, colWidths=[270, 155, 98])
    t_sum.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#0B2545")),
        ('BACKGROUND', (1,0), (-1,-1), colors.HexColor("#EBF3FA")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 14))

    # Signatures
    sig_data = [
        [
            Paragraph("Prepared by:<br/><b>A. R. Manjunath</b><br/>Senior Billing Executive", styles['TableCell']),
            Paragraph("Verified by:<br/><b>C. H. Nataraj, ACA</b><br/>Manager - Patient Financial Services", styles['TableCell']),
            Paragraph("For Apollo Hospitals Enterprise Ltd.<br/><br/><b>Authorized Medical Superintendent</b>", styles['TableCellRight'])
        ]
    ]
    t_sig = Table(sig_data, colWidths=[174, 174, 175])
    t_sig.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_sig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


# ==============================================================================
# 2. INSURANCE POLICY GENERATOR (Star Health Comprehensive Insurance Policy)
# ==============================================================================

def generate_insurance_policy(output_path: str):
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

    # --- PAGE 1: Header, Policy Schedule & Endorsement Summary ---
    p_head = [
        [
            Paragraph("<b>STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED</b><br/>"
                      "<font size='7.5'>Regd. Office: No.1, New Tank Street, Valluvar Kottam High Road, Nungambakkam, Chennai - 600034<br/>"
                      "IRDAI Regn No: 129 | CIN: L66010TN2006PLC060268 | Toll Free: 1800 425 2255 / 1800 102 4477<br/>"
                      "Website: www.starhealth.in | Grievance: grievances@starhealth.in</font>", styles['TableCell']),
            Paragraph("<font size='10' color='#0B2545'><b>POLICY SCHEDULE & CERTIFICATE</b></font><br/>"
                      "<font size='7.5'><b>STAR COMPREHENSIVE INSURANCE POLICY</b><br/>"
                      "UIN: <b>SHAHLIP21226V052021</b><br/>"
                      "Policy No: <b>01/2019/COMP/449210</b></font>", styles['TableCellRight'])
        ]
    ]
    t_head = Table(p_head, colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#0B2545")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 6))

    sched_data = [
        [
            Paragraph("<b>Policyholder Name:</b> Vikramaditya Singhania", styles['TableCell']),
            Paragraph("<b>Customer ID:</b> STAR-CUST-883109", styles['TableCell']),
            Paragraph("<b>Issuing Branch:</b> Bengaluru Branch (0102)", styles['TableCell']),
        ],
        [
            Paragraph("<b>Original Inception Date:</b> 15-Mar-2019", styles['TableCellBold']),
            Paragraph("<b>Current Policy Period:</b> 15-Mar-2025 to 14-Mar-2026", styles['TableCell']),
            Paragraph("<b>Coverage Tenure:</b> 7th Continuous Year (>60 Months)", styles['TableCellBold']),
        ],
        [
            Paragraph("<b>Insured Member 1:</b> Vikramaditya Singhania", styles['TableCell']),
            Paragraph("<b>Relationship / Age:</b> Self / 52 Years", styles['TableCell']),
            Paragraph("<b>Policy Type:</b> Individual Comprehensive Health", styles['TableCell']),
        ],
        [
            Paragraph("<b>Base Sum Insured (Since 2019):</b> Rs. 5,00,000.00", styles['TableCellBold']),
            Paragraph("<b>Accrued Cumulative Bonus:</b> Rs. 2,50,000.00", styles['TableCellBold']),
            Paragraph("<b>Base Entitlement Pool:</b> Rs. 7,50,000.00", styles['TableCellBold']),
        ],
        [
            Paragraph("<b>Sum Insured Enhancement:</b> Rs. 5,00,000.00", styles['TableCell']),
            Paragraph("<b>Enhancement Date:</b> 15-Mar-2023", styles['TableCell']),
            Paragraph("<b>Total Policy Sum Insured:</b> Rs. 12,50,000.00", styles['TableCellBold']),
        ],
        [
            Paragraph("<b>Room Entitlement & Rent Limit:</b> Single Private A/C Room (Rs. 6,000.00 / day)", styles['TableCellBold']),
            Paragraph("<b>ICU Limit:</b> Covered At Actuals (No Sub-limit)", styles['TableCell']),
            Paragraph("<b>Co-Payment & Deductible:</b> 10% Co-Pay | Deductible: Nil", styles['TableCell']),
        ]
    ]
    t_sched = Table(sched_data, colWidths=[180, 180, 163])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#0B2545")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>SUMMARY OF COVERAGE & POLICY CLAUSES</b>", styles['SectionHeading']))
    
    p1_clauses = [
        ("SECTION 1.A - ROOM, BOARDING AND NURSING EXPENSES & PROPORTIONATE RATIO",
         "The Insured Person is entitled to accommodation in a <b>Single Private A/C Room</b>. "
         "If the Insured occupies a Room Category higher than the eligible category (e.g., Deluxe Room or Suite), "
         "the Company shall pay only that proportion of Associated Medical Expenses which the entitled room tariff bears to the actual room tariff.<br/>"
         "<b>Statutory Exemption (IRDAI Master Circular 2024 & Circular 2020):</b> Proportionate deduction shall <b>NEVER</b> be applied to: "
         "(i) Pharmacy & In-Hospital Medicines, (ii) Diagnostic and Laboratory tests, (iii) Medical Devices, Implants, and Surgical Consumables.<br/>"
         "<b>Emergency Life-Safety Exception:</b> Proportionate deduction does NOT apply when admission is through emergency life-saving protocol "
         "and higher room allocation is necessitated solely by documented non-availability of the eligible category certified by the hospital."),
        
        ("SECTION 2 - INTENSIVE CARE UNIT (ICU) EXPENSES",
         "ICU / SICU bed charges, critical care monitoring, and intensivist professional fees are covered <b>At Actuals</b> up to the Sum Insured. "
         "No room rent cap or proportionate deduction shall apply to ICU hospitalization."),

        ("SECTION 3 - WAITING PERIODS & ENHANCEMENT RULES",
         "<b>Clause 3.1:</b> 30-day initial waiting period from inception (accidental injuries exempt).<br/>"
         "<b>Clause 3.2:</b> 24-month waiting period for specified illnesses (calculus diseases, hernia, diverticular disease).<br/>"
         "<b>Clause 3.3:</b> 36-month waiting period for declared Pre-Existing Diseases (PED).<br/>"
         "<b>Enhancement Rule:</b> Waiting periods on enhanced Sum Insured apply <i>de novo</i> ONLY to the incremental enhanced portion "
         "(Rs. 5,00,000 enhancement added on 15-Mar-2023). The original base Sum Insured of Rs. 5,00,000 remains fully operative without waiting periods.")
    ]

    for title, content in p1_clauses:
        story.append(Paragraph(title, styles['LegalClauseTitle']))
        story.append(Paragraph(content, styles['LegalClause']))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # --- PAGE 2: Moratorium, Co-Pay, Non-Payable Schedules & Redressal ---
    story.append(Paragraph("<b>STATUTORY TERMS, CONDITIONS & ENDORSEMENTS (CONTINUED)</b>", styles['SectionHeading']))

    p2_clauses = [
        ("SECTION 4 - STATUTORY MORATORIUM PERIOD (IRDAI MASTER CIRCULAR 2024, PARA 5.3)",
         "After completion of <b>sixty (60) continuous months</b> of continuous coverage under this Policy (including continuous renewals, "
         "portability, and migration), no claim shall be contestable by the Company on grounds of non-disclosure, misrepresentation, or pre-existing diseases, "
         "save in cases of established intentional fraud. This Policy having been continuously in force since <b>15-March-2019</b> has completed "
         "<b>83 months</b> of continuous coverage and enjoys statutory irrevocable moratorium protection for the base Sum Insured."),

        ("SECTION 5 - CO-PAYMENT CALCULATION BASIS & ORDER OF APPLICATION",
         "Where applicable, the 10% co-payment shall be deducted <b>solely from the Admissible Claim Amount</b> after the deduction of non-payable "
         "items and contractual sub-limits. Co-payment shall under no circumstances be calculated on the gross billed amount."),

        ("SECTION 6 - NON-PAYABLE EXPENSES SCHEDULE (IRDAI STANDARDIZATION GUIDELINES)",
         "Non-medical items are excluded as per IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List I).<br/>"
         "<b>List III Statutory Exception:</b> Surgical disposables, sterile drapes, surgical gown sets, trocars, suction cannulas, "
         "and sterile surgical gloves are <b>PAYABLE</b> when associated with inpatient surgical or ICU procedures and cannot be disallowed as consumables."),

        ("SECTION 7 - GRIEVANCE REDRESSAL MECHANISM & INSURANCE OMBUDSMAN",
         "In case of any dispute or claim disallowance, the Insured may represent to the Grievance Redressal Officer (GRO) at grievances@starhealth.in. "
         "If the response is unsatisfactory, the Insured has the statutory right to file a complaint before the <b>Office of the Insurance Ombudsman</b> "
         "under Rule 14 of the Insurance Ombudsman Rules, 2017.")
    ]

    for title, content in p2_clauses:
        story.append(Paragraph(title, styles['LegalClauseTitle']))
        story.append(Paragraph(content, styles['LegalClause']))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 25))
    pol_sig = [
        [
            Paragraph("Policy Issuing Officer:<br/><b>K. Venkataraman</b><br/>Assistant General Manager", styles['TableCell']),
            Paragraph("Chief Underwriting Officer:<br/><b>Dr. S. Ramachandran</b><br/>Head - Health Underwriting", styles['TableCell']),
            Paragraph("For Star Health & Allied Insurance Co. Ltd.<br/><br/><b>Duly Authorized Signatory</b>", styles['TableCellRight'])
        ]
    ]
    t_psig = Table(pol_sig, colWidths=[174, 174, 175])
    story.append(t_psig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


# ==============================================================================
# 3. REJECTION / PARTIAL SETTLEMENT LETTER (Medi Assist TPA / Star Health)
# ==============================================================================

def generate_rejection_letter(output_path: str):
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
            Paragraph("<b>MEDI ASSIST INSURANCE TPA PRIVATE LIMITED</b><br/>"
                      "<font size='7.5'>Tower D, 4th Floor, IBC Knowledge Park, 4/1, Bannerghatta Main Road, Bengaluru - 560029<br/>"
                      "IRDAI TPA Regn No: 003 | CIN: U85199KA1999PTC025676 | 24x7 Helpdesk: 1800 425 9449<br/>"
                      "Dedicated In-House Claims Adjudication Cell - Star Health Insurance</font>", styles['TableCell']),
            Paragraph("<font size='10' color='#8B0000'><b>CLAIM SETTLEMENT & DEDUCTION SUMMARY</b></font><br/>"
                      "<font size='7.5'>Claim Ref: <b>MED/2026/STR/8841029</b><br/>"
                      "Date: <b>24-Feb-2026</b><br/>"
                      "Status: <b>PARTIALLY APPROVED / DISALLOWED</b></font>", styles['TableCellRight'])
        ]
    ]
    t_head = Table(tpa_head, colWidths=[330, 193])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#8B0000")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 5))

    demo = [
        [
            Paragraph("<b>Insured Patient:</b> Mr. Vikramaditya Singhania", styles['TableCell']),
            Paragraph("<b>Policy No:</b> 01/2019/COMP/449210", styles['TableCell']),
            Paragraph("<b>Insurer:</b> Star Health & Allied Insurance", styles['TableCell']),
        ],
        [
            Paragraph("<b>Hospital:</b> Apollo Hospitals, Bannerghatta", styles['TableCell']),
            Paragraph("<b>IP No:</b> IP/2026/044192", styles['TableCell']),
            Paragraph("<b>Stay:</b> 12-Feb-2026 to 18-Feb-2026 (6 Days)", styles['TableCell']),
        ],
        [
            Paragraph("<b>Diagnosis:</b> Acute Diverticulitis with Perforation", styles['TableCell']),
            Paragraph("<b>Procedure:</b> Laparotomy & Hartmann's Resection", styles['TableCell']),
            Paragraph("<b>Claim Type:</b> Post-Discharge Reimbursement", styles['TableCell']),
        ]
    ]
    t_demo = Table(demo, colWidths=[180, 180, 163])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF5F5")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#8B0000")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F0D0D0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 5))

    story.append(Paragraph("Dear Mr. Vikramaditya Singhania,", styles['TableCellBold']))
    story.append(Paragraph(
        "We refer to your reimbursement claim towards hospitalization at Apollo Hospitals, Bengaluru. "
        "Upon technical medical audit of the hospital records, bills, and policy contract terms, an amount of "
        "<b>Rs. 2,16,200.00</b> has been approved against the claimed sum of <b>Rs. 5,48,750.00</b>. The disallowance of "
        "<b>Rs. 3,32,550.00</b> has been deducted in accordance with contractual terms as detailed below:",
        styles['TableCell']
    ))
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>ADJUDICATED DEDUCTION SCHEDULE & CITATIONS</b>", styles['SectionHeadingRed']))

    # Disallowance Schedule Table with ALL text properly wrapped in Paragraphs
    disallow_data = [
        [
            Paragraph("<b>Sl</b>", styles['TableHead']),
            Paragraph("<b>Deduction Category / Head</b>", styles['TableHead']),
            Paragraph("<b>Billed (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Deducted (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Approved (Rs.)</b>", styles['TableHead']),
            Paragraph("<b>Adjudication Grounds & Policy Clause Citation</b>", styles['TableHead'])
        ],
        # Flaw 4: Co-Pay on Gross
        [
            Paragraph("1", styles['TableCellCenter']),
            Paragraph("<b>Mandatory Co-Payment</b><br/>(10% on Gross Billed Amount)", styles['TableCell']),
            Paragraph("5,48,750.00", styles['TableCellRight']),
            Paragraph("54,875.00", styles['TableCellRightBold']),
            Paragraph("4,93,875.00", styles['TableCellRight']),
            Paragraph("<b>Clause 5 (Co-Pay):</b> 10% co-payment applied to the total billed gross amount of Rs. 5,48,750.00 as per member entry age bracket (>50 Yrs).", styles['TableCellSmall'])
        ],
        # Flaw 3: Annexure A List III Disallowed
        [
            Paragraph("2", styles['TableCellCenter']),
            Paragraph("<b>Surgical Consumables & Drapes</b><br/>(List III Disallowance)", styles['TableCell']),
            Paragraph("34,800.00", styles['TableCellRight']),
            Paragraph("34,800.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>IRDAI Non-Payable Annexure A (List I):</b> Consumable items, sterile surgical drapes, surgeon gown kit, suction tubing, and gloves classified as non-medical consumables, hence disallowed.", styles['TableCellSmall'])
        ],
        # Flaw 2: Enhancement Waiting Period
        [
            Paragraph("3", styles['TableCellCenter']),
            Paragraph("<b>Surgeon Professional Fees</b><br/>(Primary & Assistant)", styles['TableCell']),
            Paragraph("1,20,000.00", styles['TableCellRight']),
            Paragraph("1,20,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>Clause 3.2 (Specific Disease 24M / PED 36M on Enhancement):</b> Diverticular disease history noted in 2022. Sum Insured enhanced by Rs. 5,00,000 on 15-Mar-2023. Since 36 months have not elapsed on enhanced coverage, diverticular surgery is repudiated under Clause 3.2.", styles['TableCellSmall'])
        ],
        # Flaw 1: Proportionate Deduction on Protected Heads
        [
            Paragraph("4", styles['TableCellCenter']),
            Paragraph("<b>Room Rent Proportionate Cut</b><br/>(40% Cut on Room, ICU, OT & Implants)", styles['TableCell']),
            Paragraph("2,05,500.00", styles['TableCellRight']),
            Paragraph("82,200.00", styles['TableCellRightBold']),
            Paragraph("1,23,300.00", styles['TableCellRight']),
            Paragraph("<b>Section 1.A (Proportionate Room Rent):</b> Insured stayed in Deluxe Room (Rs. 10,000/day) exceeding Single AC room limit (Rs. 6,000/day). Ratio = (1 - 6000/10000) = 40%. A 40% cut is applied across Deluxe Room (Rs. 16,000), SICU (Rs. 11,200), OT Complex (Rs. 24,000), and Endo-GIA Implants (Rs. 31,000).", styles['TableCellSmall'])
        ],
        # Sundry Items
        [
            Paragraph("5", styles['TableCellCenter']),
            Paragraph("<b>Non-Medical Overheads</b><br/>(Registration & Toiletries)", styles['TableCell']),
            Paragraph("4,000.00", styles['TableCellRight']),
            Paragraph("4,000.00", styles['TableCellRightBold']),
            Paragraph("0.00", styles['TableCellRight']),
            Paragraph("<b>List I Non-Payable:</b> Admission administrative registration fee and patient care toiletries kit disallowed.", styles['TableCellSmall'])
        ],
        [
            Paragraph("6", styles['TableCellCenter']),
            Paragraph("<b>Pharmacy & Diagnostics</b><br/>(Supportive Care Disallowance)", styles['TableCell']),
            Paragraph("1,49,700.00", styles['TableCellRight']),
            Paragraph("36,675.00", styles['TableCellRightBold']),
            Paragraph("1,13,025.00", styles['TableCellRight']),
            Paragraph("<b>Pharmacy Review:</b> Disallowance of TPN nutritional infusion (Rs. 10,800) as dietary supplement and unbilled diagnostic baseline differentials.", styles['TableCellSmall'])
        ],
        # Totals
        [
            Paragraph("", styles['TableCellCenter']),
            Paragraph("<b>TOTAL RECONCILIATION</b>", styles['TableCellBold']),
            Paragraph("<b>5,48,750.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>3,32,550.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>2,16,200.00</b>", styles['TableCellRightBold']),
            Paragraph("<b>Net Admissible Claim Payable via NEFT: Rs. 2,16,200.00</b>", styles['TableCellBold'])
        ]
    ]

    t_dis = Table(disallow_data, colWidths=[15, 115, 55, 55, 55, 228])
    t_dis.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#8B0000")),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DCDCDC")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FCE4E4")),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor("#8B0000")),
    ]))
    for r in range(1, len(disallow_data)-1):
        bg = colors.HexColor("#FFFFFF") if r % 2 == 1 else colors.HexColor("#FFF8F8")
        t_dis.setStyle(TableStyle([('BACKGROUND', (0, r), (-1, r), bg)]))
    story.append(t_dis)

    story.append(PageBreak())

    # --- PAGE 2: Medical Officer Justification, Grievance Escalation & Signatures ---
    story.append(Paragraph("<b>ADJUDICATING CHIEF MEDICAL OFFICER'S TECHNICAL RATIONALE</b>", styles['SectionHeadingRed']))
    cmo_note = [
        [Paragraph(
            "<i>\"The claim submitted by Mr. Vikramaditya Singhania has been comprehensively reviewed under the technical provisions of the Star Comprehensive Policy and IRDAI Health Insurance guidelines:<br/>"
            "1. <b>Room Category Breach:</b> The insured elected to occupy a Deluxe Room at Rs. 10,000/day against the policy limit of a Single Private AC room (Rs. 6,000/day). "
            "Under Section 1.A, associated medical expenses are proportionately scaled by 40%. The hospital billing includes procedural packages that incorporate associated overheads.<br/>"
            "2. <b>Pre-Existing Disease / Enhancement Waiting Period:</b> The inpatient clinical history explicitly records past diverticular symptoms in October 2022. "
            "The Sum Insured was enhanced from Rs. 5,00,000 to Rs. 10,00,000 effective 15-Mar-2023. Under Clause 3.2 and Clause 3.3, a fresh waiting period of 24/36 months applies to the enhanced sum insured. "
            "Because 36 months have not elapsed since 15-Mar-2023, surgical treatment for pre-existing diverticular disease is excluded.<br/>"
            "3. <b>Consumables Exclusion:</b> All disposable packs, surgical drapes, and surgical gloves have been excluded in accordance with standard non-payable guidelines.<br/>"
            "The adjudication is mathematically verified, fully compliant with policy terms, and represents the final settlement determination of the insurer.\"</i>",
            styles['TableCell']
        )]
    ]
    t_cmo = Table(cmo_note, colWidths=[523])
    t_cmo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDF7F7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#B22222")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_cmo)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>STATUTORY GRIEVANCE REDRESSAL MECHANISM & INSURANCE OMBUDSMAN</b>", styles['SectionHeading']))
    story.append(Paragraph(
        "If you do not accept this settlement, you may submit a formal representation within 30 days to the "
        "<b>Grievance Redressal Officer (GRO)</b>, Star Health and Allied Insurance Company Limited, "
        "No.1, New Tank Street, Nungambakkam, Chennai - 600034 (Email: grievances@starhealth.in | GRO Toll-Free: 1800 425 2255).<br/><br/>"
        "Should the grievance remain unresolved or if the insurer's response is unsatisfactory, you have the statutory right under "
        "<b>Rule 14(3) of the Insurance Ombudsman Rules, 2017</b> to approach the <b>Office of the Insurance Ombudsman, Bengaluru</b>:<br/>"
        "<i>Address: Office of the Insurance Ombudsman, Jeevan Soudha Building, PID No. 57-27-N-19, Ground Floor, "
        "24th Main Road, JP Nagar, 1st Phase, Bengaluru - 560078 (Karnataka).<br/>"
        "Phone: 080-26652048 / 080-26652049 | Email: bimalokpal.bengaluru@cioins.co.in</i>",
        styles['FooterDisclaimer']
    ))
    story.append(Spacer(1, 20))

    tpa_sig = [
        [
            Paragraph("Medical Auditor:<br/><b>Dr. Rashmi Hegde, MBBS</b><br/>Senior Medical Adjudicator", styles['TableCell']),
            Paragraph("Financial Claims Authorizer:<br/><b>V. Parthasarathy</b><br/>AVP - Technical Claims Adjudication", styles['TableCell']),
            Paragraph("For Medi Assist Insurance TPA Pvt. Ltd.<br/><br/><b>Authorized Signatory</b>", styles['TableCellRight'])
        ]
    ]
    t_tsig = Table(tpa_sig, colWidths=[174, 174, 175])
    story.append(t_tsig)

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


if __name__ == "__main__":
    out_dir = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\test_docs\complex_claim_case"
    os.makedirs(out_dir, exist_ok=True)
    
    bill_path = os.path.join(out_dir, "apollo_hospital_bill.pdf")
    policy_path = os.path.join(out_dir, "star_comprehensive_policy.pdf")
    rejection_path = os.path.join(out_dir, "mediassist_rejection_letter.pdf")
    
    print(f"Generating Hospital Bill -> {bill_path}")
    generate_hospital_bill(bill_path)
    
    print(f"Generating Insurance Policy -> {policy_path}")
    generate_insurance_policy(policy_path)
    
    print(f"Generating Rejection Letter -> {rejection_path}")
    generate_rejection_letter(rejection_path)
    
    print("SUCCESS: All 3 realistic complex claim PDFs generated successfully.")
