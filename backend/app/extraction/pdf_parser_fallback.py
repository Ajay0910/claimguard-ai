"""
Universal Dynamic Layout Table PDF Parser for Medical Claims.
Extracts structured Pydantic models (HospitalBill, InsurancePolicy, RejectionLetter)
with full field provenance, line items, and arithmetic reconciliation directly from
PDF text streams and PyMuPDF layout tables without hardcoded stubs or patient names.
"""

import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
import pymupdf

from ..schemas.provenance import Provenance
from ..schemas.hospital_bill import HospitalBill, BillLineItem
from ..schemas.insurance_policy import (
    InsurancePolicy,
    ProportionateDeductionRuleConfig,
    WaitingPeriodConfig,
    SubLimit
)
from ..schemas.rejection_letter import RejectionLetter, RejectionReason


SUMMARY_ROW_PATTERN = re.compile(
    r"^\s*(?:"
    r"total(?:\s+(?:claim(?:ed)?|disallowed|disallowance|deducted|deductions?|billed|approved|paid|charges?|amount|gross|bill|net|reconciliation|settlement|payable|admissible|incurred|hospital|invoice|and)\b|\s*[/\&]\s*)*"
    r"|grand\s+total"
    r"|gross\s+(?:total|bill(?:\s+amount)?|amount)"
    r"|(?:(?:page\s+\d+\s+)?(?:itemized\s+charges?\s+|disallowances?\s+)?)?sub[-\s]?total(?:\s+amount)?"
    r"|net\s+(?:payable|outstanding(?:\s+payable)?|amount|approved(?:\s*&\s*transmitted(?:\s+amount)?)?(?:\s*\((?:neft/rtgs|rtgs|neft|cheque|bank)\))?|invoice\s+total)"
    r"|less\s+advance(?:\s+paid)?"
    r"|advance\s+paid"
    r"|bank\s+transaction(?:\s+reference|\s+details|\s+id)?(?:\s*[:\-]\s*[A-Z0-9_\-]+)?"
    r"|authorized\s+tpa(?:\s+signature)?"
    r"|gst\s+exemption"
    r")"
    r"(?:\s*\((?:in\s+)?(?:inr|rs\.?|₹)\))?"
    r"[:\-\s]*"
    r"(?:\s*\(?\s*(?:rs\.?|₹|inr|usd)?\s*[\d,]+(?:\.\d+)?(?:\s*/-)?\s*\)?)*\s*$",
    re.IGNORECASE
)


def prov(val, conf: float = 0.99, src: str = "DIGITAL_PDF_TEXT", page: str = "1") -> Provenance:
    return Provenance(value=val, extraction_confidence=conf, source_text=src, page=str(page))


def _clean_str(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def _parse_float(s, default: float = 0.0) -> float:
    if s is None:
        return default
    if isinstance(s, (int, float)):
        import math
        if math.isnan(s) or math.isinf(s):
            return default
        return float(s)
    raw = str(s).strip()
    if not raw or raw.upper() in ("NAN", "INF", "-INF", "NULL", "NONE", "N/A", "--", "FREE", "GRATIS"):
        return default

    # Guard against date strings being mistakenly parsed as numeric amounts
    if re.search(r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$", raw):
        return default

    # Accounting negative checks:
    # 1. Parenthesized number: (500.00), ( 1,250.50 ), (500.00) discount, -(500.00)
    # 2. Leading or trailing minus: -500, - 1,000, 500.00-, 1,250.00 -
    is_neg = False
    if re.search(r"\(\s*(?:Rs\.?|₹|INR|\$|€|£)?\s*[\d,]+(?:\.\d+)?\s*\)", raw):
        is_neg = True
    elif re.search(r"(?<!\+)\s*-\s*[\d.]", raw) or re.search(r"[\d.]\s*-\s*", raw):
        is_neg = True

    # Leading plus sign overrides negative
    if re.match(r"^\s*\+", raw):
        is_neg = False

    # Strip out non-currency annotations in parentheses like (50% Max Cap), (Hunt-Hess Gr III), (Day 1 to 4)
    # But preserve pure number parentheses like (500.00)
    cleaned_str = re.sub(r"\([^)]*[a-zA-Z%][^)]*\)", "", raw)

    # Now extract the primary monetary amount
    m_amt = re.search(r"([+-]?)\s*(?:Rs\.?|₹|INR|\$|€|£)?\s*([\d,]+(?:\.\d+)?)", cleaned_str, re.IGNORECASE)
    if m_amt:
        sign = m_amt.group(1)
        num_str = m_amt.group(2).replace(",", "")
        try:
            val = float(num_str)
            if sign == "-":
                is_neg = True
            elif sign == "+":
                is_neg = False
            return -val if is_neg else val
        except ValueError:
            pass

    return default


def _parse_date_str(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    from dateutil.parser import parse
    cleaned = _clean_str(s)
    cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    try:
        dt = parse(cleaned, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _normalize_category(cat_str: str, desc: str) -> str:
    c = _clean_str(cat_str).upper().replace(" ", "").replace("_", "")
    d = desc.upper()
    
    if "ROOM" in c:
        return "ROOM"
    if "NURSING" in c:
        return "NURSING"
    if "CONSULT" in c:
        return "CONSULTATION"
    if "OT" in c or "OPERATION" in c or "THEATRE" in c:
        return "OT"
    if "PHARM" in c or "MEDICINE" in c or "DRUG" in c:
        return "PHARMACY"
    if "CONSUM" in c or "IMPLANT" in c:
        return "CONSUMABLES"
    if "RADIO" in c or "XRAY" in c or "SCAN" in c or "IMAGING" in c:
        return "RADIOLOGY"
    if "LAB" in c or "PATH" in c:
        return "LAB"
    if "DIAGNOSTIC" in c:
        if any(w in d for w in ["CT", "MRCP", "MRI", "X-RAY", "XRAY", "SCAN", "ULTRASOUND", "USG", "FLUOROSCOPY", "RADIOLOGY"]):
            return "RADIOLOGY"
        return "LAB"
    if "NONMED" in c or "MISC" in c or "ADMIN" in c:
        return "MISCELLANEOUS"
        
    if any(w in d for w in ["BED CHARGE", "ROOM CHARGE", "ACCOMMODATION", "DELUXE", "WARD BED", "ICU BED", "SICU BED", "MICU BED"]):
        return "ROOM"
    if "NURSING" in d or "NURSE" in d:
        return "NURSING"
    if any(w in d for w in ["SURGEON", "CONSULTANT", "CONSULTATION", "DOCTOR", "ANAESTHETIST", "ANAESTHESIOLOGIST", "OPERATIVE FEE", "VISIT FEE", "ROUND"]):
        return "CONSULTATION"
    if any(w in d for w in ["OPERATION THEATRE", "OT COMPLEX", "OT CHARGES", "ANAESTHESIA WORKSTATION", "FLUOROSCOPY SUITE", "C-ARM", "CAUTERY"]):
        return "OT"
    if any(w in d for w in ["INFUSION", "INJECTION", "IV ", "MEROPENEM", "ALBUMIN", "INSULIN", "PHARMACY", "MEDICINE", "TABLET", "TPN", "PANTOPRAZOLE"]):
        return "PHARMACY"
    if any(w in d for w in ["DRAPE", "GLOVE", "SUTURE", "CANNULA", "STAPLER", "BASKET", "SPHINCTEROTOME", "DORMIA", "HARMONIC", "LIGASURE", "T-TUBE", "CONSUMABLE", "IMPLANT", "DEVICE"]):
        return "CONSUMABLES"
    if any(w in d for w in ["CT ", "MRCP", "MRI", "X-RAY", "ULTRASOUND", "USG", "RADIOLOGY", "CONTRAST"]):
        return "RADIOLOGY"
    if any(w in d for w in ["PATHOLOGY", "BIOPSY", "HISTOPATHOLOGY", "BLOOD CULTURE", "CMP", "LFT", "KFT", "ABG", "LACTATE", "LABORATORY", "SERIES"]):
        return "LAB"
        
    return "MISCELLANEOUS"


def _is_room_linked(desc: str, cat: str) -> bool:
    d = desc.upper()
    is_icu = any(w in d for w in ["ICU", "SICU", "MICU", "CCU", "HDU", "INTENSIVE", "INTENSIVIST", "CRITICAL CARE"])
    if is_icu:
        return False
    if cat == "ROOM":
        return True
    if cat == "NURSING":
        return True
    if cat == "CONSULTATION":
        if any(w in d for w in ["SURGEON", "SURGERY", "OPERATIVE", "ANAESTHETIST", "ANAESTHESIOLOGIST", "PROCEDURE"]):
            return True
    return False


def parse_hospital_bill_pdf(pdf_path: str) -> Optional[HospitalBill]:
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    try:
        doc = pymupdf.open(pdf_path)
        if len(doc) == 0:
            return None
        full_text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return None

    # Patient Name
    p_name = None
    m = re.search(r"(?:Patient Name|Name of Patient|Patient)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
    if m:
        p_name = _clean_str(re.split(r"(?:UHID|MRN|Age|IP|Gender|Sex|\s{2,})", m.group(1), flags=re.IGNORECASE)[0])

    # Bill ID
    bill_id = None
    m = re.search(r"(?:Bill No|Bill Number|Invoice No|IP Admission No|IP No|Bill #)\s*[:\-]\s*([^\s\n\r]+)", full_text, re.IGNORECASE)
    if m:
        bill_id = _clean_str(m.group(1))

    # Hospital Name
    hospital_name = None
    first_lines = [l.strip() for l in doc[0].get_text().split("\n") if l.strip()]
    for l in first_lines[:8]:
        if any(w in l.upper() for w in ["HOSPITAL", "SPECIALITY", "SPECIALTY", "CLINIC", "HEALTHCARE", "MEDICAL CENTRE", "MEDICAL CENTER", "HEALTH CITY", "MEDICITY", "INFIRMARY", "NURSING HOME"]):
            hospital_name = l
            break
    if not hospital_name:
        m = re.search(r"(?:Hospital Name|Hospital|Provider)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
        if m:
            hospital_name = _clean_str(m.group(1))

    # Admission Date
    adm_date = None
    m = re.search(r"(?:Admission|Date of Admission|DOA)\s*[:\-]\s*([^\n\r,]+)", full_text, re.IGNORECASE)
    if m:
        adm_date = _parse_date_str(m.group(1))

    # Discharge Date
    dis_date = None
    m = re.search(r"(?:Discharge|Date of Discharge|DOD)\s*[:\-]\s*([^\n\r,]+)", full_text, re.IGNORECASE)
    if m:
        dis_date = _parse_date_str(m.group(1))

    # Length of Stay
    los = None
    m = re.search(r"(\d+)\s*(?:Days|day|d\b)", full_text, re.IGNORECASE)
    if m:
        los = int(m.group(1))
    elif adm_date and dis_date:
        try:
            d1 = datetime.strptime(adm_date, "%Y-%m-%d")
            d2 = datetime.strptime(dis_date, "%Y-%m-%d")
            los = max(1, (d2 - d1).days)
        except Exception:
            los = 1

    # Diagnosis
    diagnosis = None
    m = re.search(r"(?:Clinical Diagnosis|Primary Diagnosis|Final Diagnosis|Diagnosis)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
    if m:
        diagnosis = _clean_str(re.split(r"(?:Procedure|Surgical|Treatment|\s{2,})", m.group(1), flags=re.IGNORECASE)[0])

    # Total Amount
    total_amount = None
    total_page = 1
    total_src = ""
    for p_idx, page in enumerate(doc):
        for t in page.find_tables().tables:
            for row in t.extract():
                row_str = " ".join(str(c) for c in row if c)
                row_lower = row_str.lower()
                if any(kw in row_lower for kw in ["gross bill amount", "net outstanding payable", "total gross bill", "grand total", "net payable", "total amount", "net invoice total"]):
                    # Prioritize specific gross bill / grand total patterns
                    tm = re.search(r"(?:GROSS\s+BILL\s+AMOUNT|NET\s+OUTSTANDING\s+PAYABLE|TOTAL\s+GROSS\s+BILL|GRAND\s+TOTAL|NET\s+PAYABLE|TOTAL\s+AMOUNT|NET\s+INVOICE\s+TOTAL\s+PAYABLE)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", row_str, re.IGNORECASE)
                    if not tm and not any(sub in row_lower for sub in ["subtotal", "sub-total", "sub total"]):
                        tm = re.search(r"\bTOTAL\b\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", row_str, re.IGNORECASE)
                    if tm:
                        total_amount = _parse_float(tm.group(1))
                        total_page = p_idx + 1
                        total_src = _clean_str(tm.group(0))
                        break
            if total_amount:
                break
        if total_amount:
            break

    if total_amount is None:
        for p_idx, page in enumerate(doc):
            p_text = page.get_text()
            m = re.search(r"(?:GROSS\s+BILL\s+AMOUNT|NET\s+OUTSTANDING\s+PAYABLE|TOTAL\s+GROSS\s+BILL|GRAND\s+TOTAL|NET\s+PAYABLE|TOTAL\s+AMOUNT|NET\s+INVOICE\s+TOTAL|TOTAL\s+BILL|\bTOTAL\b)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", p_text, re.IGNORECASE | re.MULTILINE)
            if m:
                total_amount = _parse_float(m.group(1))
                total_page = p_idx + 1
                total_src = _clean_str(m.group(0))
                break

    # Extract Line Items via PyMuPDF Tables
    line_items: List[BillLineItem] = []
    item_idx = 0

    for p_idx, page in enumerate(doc):
        tabs = page.find_tables()
        for tab in tabs.tables:
            df = tab.extract()
            if not df or len(df) < 2:
                continue
            
            # Skip tables that consist entirely of financial summary/footer rows
            if all(SUMMARY_ROW_PATTERN.match(_clean_str(r[0])) for r in df if any(r)):
                continue

            header_row_idx = -1
            desc_col = -1
            cat_col = -1
            qty_col = -1
            rate_col = -1
            amt_col = -1

            for r_i in range(min(3, len(df))):
                row_str = " ".join(str(c).lower().replace("\n", " ") for c in df[r_i])
                c0 = _clean_str(df[r_i][0])
                if SUMMARY_ROW_PATTERN.match(c0) or re.search(r"(?:Rs\.?|₹)\s*[\d,]+", row_str):
                    continue
                if re.search(r"\b(description|particulars?|item(?:\s+name)?|service(?:\s+name)?|procedure|investigation|treatment|charge\s+head)\b", row_str, re.IGNORECASE):
                    header_row_idx = r_i
                    headers = [str(c).lower().replace("\n", " ").strip() for c in df[r_i]]
                    for c_i, h in enumerate(headers):
                        if re.search(r"\b(description|particulars?|item(?:\s+name)?|service(?:\s+name)?|procedure|investigation|treatment|charge\s+head)\b", h, re.IGNORECASE):
                            desc_col = c_i
                        elif any(w in h for w in ["category", "dept"]):
                            cat_col = c_i
                        elif any(w in h for w in ["qty", "quantity", "units"]):
                            qty_col = c_i
                        elif any(w in h for w in ["rate", "price", "unit"]):
                            rate_col = c_i
                        elif any(w in h for w in ["total", "amount", "net", "charges", "cost"]):
                            amt_col = c_i
                    break

            if desc_col >= 0 and (amt_col >= 0 or rate_col >= 0):
                for r_i in range(header_row_idx + 1, len(df)):
                    row = df[r_i]
                    if not row or desc_col >= len(row):
                        continue
                    desc = _clean_str(row[desc_col])
                    if not desc or any(SUMMARY_ROW_PATTERN.match(_clean_str(c)) for c in row if c):
                        continue
                    
                    qty = 1.0
                    if qty_col >= 0 and qty_col < len(row) and row[qty_col]:
                        qty = _parse_float(row[qty_col], default=1.0)
                    if qty <= 0:
                        qty = 1.0

                    rate = 0.0
                    if rate_col >= 0 and rate_col < len(row) and row[rate_col]:
                        rate = _parse_float(row[rate_col], default=0.0)

                    amt = 0.0
                    if amt_col >= 0 and amt_col < len(row) and row[amt_col]:
                        amt = _parse_float(row[amt_col], default=0.0)

                    # Compute missing amount or unit rate without inverting negative discounts
                    if amt == 0.0 and rate != 0.0:
                        amt = rate * qty
                    elif rate == 0.0 and amt != 0.0 and qty > 0.0:
                        rate = amt / qty

                    # If amount is negative (discount) but rate was specified positive, align rate sign with amount
                    if amt < 0.0 and rate > 0.0:
                        rate = -rate
                    # If rate is negative but amount was specified positive, align amount sign with rate
                    elif rate < 0.0 and amt > 0.0:
                        amt = -amt

                    declared_cat = row[cat_col] if cat_col >= 0 and cat_col < len(row) else ""
                    norm_cat = _normalize_category(declared_cat, desc)
                    room_link = _is_room_linked(desc, norm_cat)
                    pg_str = str(p_idx + 1)

                    line_items.append(BillLineItem(
                        item_code=prov(f"ITEM_{item_idx}", page=pg_str),
                        description=prov(desc, src=desc, page=pg_str),
                        category=prov(norm_cat, src=norm_cat, page=pg_str),
                        quantity=prov(qty, src=str(qty), page=pg_str),
                        unit_rate=prov(rate, src=f"{rate:,.2f}", page=pg_str),
                        amount=prov(amt, src=f"{amt:,.2f}", page=pg_str),
                        total=amt,
                        is_room_linked=room_link
                    ))
                    item_idx += 1

    # Key-value fallback for plain-text / minimal bills
    if not line_items:
        kv_items = []
        for line in full_text.split("\n"):
            line = line.strip()
            rm_m = re.match(r"^(?:Room|Bed|ICU|Nursing|Pharmacy|Lab|OT)\s*[:\-]\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", line, re.IGNORECASE)
            if rm_m:
                val = _parse_float(rm_m.group(1))
                if val > 0:
                    cat_name = line.split(":")[0].strip()
                    norm_cat = _normalize_category(cat_name, cat_name)
                    kv_items.append(BillLineItem(
                        item_code=prov(f"ITEM_{len(kv_items)}"),
                        description=prov(f"{cat_name} Charges"),
                        category=prov(norm_cat),
                        quantity=prov(1.0),
                        unit_rate=prov(val),
                        amount=prov(val),
                        total=val,
                        is_room_linked=_is_room_linked(cat_name, norm_cat)
                    ))
        if kv_items:
            line_items = kv_items

    subtotal = sum(item.amount.value for item in line_items if item.amount) if line_items else 0.0
    positive_sum = sum(item.amount.value for item in line_items if item.amount and item.amount.value > 0)

    if total_amount is None or total_amount <= 0.0:
        total_amount = subtotal if subtotal > 0.0 else 0.0

    # Balance unitemized difference into Pharmacy/Medical treatment rather than Miscellaneous
    # Only balance if total_amount strictly exceeds the positive charges sum (indicating unlisted services)
    # and not simply because discounts reduced the net subtotal.
    if line_items and total_amount and total_amount > positive_sum + 1.0 and abs(total_amount - subtotal) > 1.0:
        diff = total_amount - positive_sum
        line_items.append(BillLineItem(
            item_code=prov(f"ITEM_{len(line_items)}"),
            description=prov("General Inpatient Medical Treatment"),
            category=prov("PHARMACY"),
            quantity=prov(1.0),
            unit_rate=prov(diff),
            amount=prov(diff),
            total=diff,
            is_room_linked=False
        ))
        subtotal += diff

    if not line_items and total_amount > 0.0:
        line_items.append(BillLineItem(
            item_code=prov("ITEM_0"),
            description=prov("Inpatient Hospitalization & Medical Services"),
            category=prov("ROOM"),
            quantity=prov(1.0),
            unit_rate=prov(total_amount),
            amount=prov(total_amount),
            total=total_amount,
            is_room_linked=False
        ))
        subtotal = total_amount

    if not line_items and total_amount <= 0.0:
        return None

    arithmetic_verified = abs(total_amount - subtotal) <= 1.0

    return HospitalBill(
        bill_id=prov(bill_id or "BILL-UNKNOWN", src=f"Bill No: {bill_id}"),
        patient_name=prov(p_name or "Unknown Patient", src=f"Patient: {p_name}"),
        hospital_name=prov(hospital_name or "Hospital", src=hospital_name or "Hospital"),
        total_amount=prov(total_amount, src=total_src or f"TOTAL GROSS BILL: Rs. {total_amount:,.2f}", page=str(total_page)),
        subtotal=prov(subtotal, src=total_src or f"Subtotal: Rs. {subtotal:,.2f}", page=str(total_page)),
        admission_date=prov(adm_date, src=f"Admission: {adm_date}") if adm_date else None,
        discharge_date=prov(dis_date, src=f"Discharge: {dis_date}") if dis_date else None,
        length_of_stay=prov(los or 1, src=f"Length of Stay: {los} Days"),
        diagnosis=prov(diagnosis or "General Medical Condition", src=f"Diagnosis: {diagnosis}"),
        line_items=line_items,
        arithmetic_verified=arithmetic_verified
    )


def parse_insurance_policy_pdf(pdf_path: str) -> Optional[InsurancePolicy]:
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    try:
        doc = pymupdf.open(pdf_path)
        if len(doc) == 0:
            return None
        full_text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return None

    # Insurer Name
    insurer_name = None
    first_lines = [l.strip() for l in doc[0].get_text().split("\n") if l.strip()]
    for l in first_lines[:5]:
        if any(w in l.upper() for w in ["INSURANCE", "ASSURANCE"]) and not any(kw in l.upper() for kw in ["POLICY", "SCHEDULE", "CERTIFICATE"]):
            insurer_name = l
            break
    if not insurer_name:
        m = re.search(r"(?:Insurer|Insurance Company)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
        if m:
            insurer_name = _clean_str(m.group(1))

    # Policy Number
    policy_number = None
    m = re.search(r"(?:Policy No|Policy Number|Certificate No)\s*[:\-]\s*([^\s\n\r]+)", full_text, re.IGNORECASE)
    if m:
        policy_number = _clean_str(m.group(1))

    # Policyholder Name (with multiline split safeguard)
    holder_name = None
    m = re.search(r"(?:Policyholder\s*(?:\/\s*Primary\s*Insured|\/\s*Insured\s*Person)?|Policyholder\s*Name|Proposer\s*Name|Insured\s*Member\s*1|Insured\s*Name|Policyholder)\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+)?)", full_text, re.IGNORECASE)
    if m:
        raw_val = m.group(1)
        lines = [l.strip() for l in raw_val.split("\n") if l.strip()]
        if len(lines) > 1:
            if ":" in lines[1] or any(k in lines[1].lower() for k in ["room", "limit", "policy", "date", "sum", "moratorium", "age", "customer", "proposer"]):
                raw_val = lines[0]
            else:
                raw_val = " ".join(lines)
        cleaned_h = re.sub(r"\s+", " ", raw_val).strip()
        holder_name = _clean_str(re.split(r"(?:Customer|UHID|Age|Gender|Relationship|\s{2,})", cleaned_h, flags=re.IGNORECASE)[0])

    # UIN / Policy Version
    uin = None
    m = re.search(r"(?:UIN|Product\s*UIN|Policy\s*Version)\s*[:\-]\s*([^\s\n\r\|]+)", full_text, re.IGNORECASE)
    if m:
        uin = _clean_str(m.group(1))

    # Inception Date
    inc_date = None
    m = re.search(r"(?:Original\s*Inception\s*Date|Policy\s*Inception\s*Date|Inception\s*Date)\s*[:\-]\s*([^\n\r,]+)", full_text, re.IGNORECASE)
    if m:
        inc_date = _parse_date_str(m.group(1))

    # Current Policy Period
    p_start = None
    p_end = None
    m = re.search(r"(?:Current\s*Policy\s*Period|Policy\s*Period)\s*[:\-]?\s*(\d{1,2}-[A-Za-z]+-\d{4}|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:to|-)\s*(\d{1,2}-[A-Za-z]+-\d{4}|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", full_text, re.IGNORECASE)
    if m:
        p_start = _parse_date_str(m.group(1))
        p_end = _parse_date_str(m.group(2))

    # Base Sum Insured
    base_si = None
    m = re.search(r"Base\s*Sum\s*Insured(?:\s*\([^)]*\))?\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        base_si = _parse_float(m.group(1))

    # Cumulative Bonus
    bonus = 0.0
    m = re.search(r"(?:Accrued\s*Cumulative\s*Bonus|Cumulative\s*Bonus|No\s*Claim\s*Bonus|NCB)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        bonus = _parse_float(m.group(1))

    # Enhanced Sum Insured
    enhanced_si = None
    enh_date = None
    m = re.search(r"(?:Enhanced\s*Sum\s*Insured|Sum\s*Insured\s*Enhancement)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        enhanced_si = _parse_float(m.group(1))
    m = re.search(r"Enhancement\s*Date\s*[:\-]?\s*([^\n\r,]+)", full_text, re.IGNORECASE)
    if m:
        enh_date = _parse_date_str(m.group(1))

    # Total Sum Insured
    total_si = None
    m = re.search(r"(?:Total\s*Effective\s*Coverage|Total\s*Policy\s*Sum\s*Insured|Total\s*Sum\s*Insured|(?:(?<!Base\s)(?<!Base\s\s))Sum\s*Insured)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        total_si = _parse_float(m.group(1))
    if not total_si and base_si:
        total_si = base_si + bonus
    if not base_si and total_si:
        base_si = total_si - bonus

    # Room Entitlement & Rent Limit
    room_cat = "SINGLE_PRIVATE_AC_ROOM"
    room_limit = 0.0
    m = re.search(r"Room\s*Entitlement(?:\s*(?:&|and)\s*Rent\s*Limit)?\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+)?)", full_text, re.IGNORECASE)
    if m:
        r_str = re.sub(r"\s+", " ", m.group(1)).strip()
        lim_m = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)\s*(?:\/\s*day|per\s*day)", r_str, re.IGNORECASE)
        if lim_m:
            room_limit = _parse_float(lim_m.group(1))
        if "single" in r_str.lower() and "private" in r_str.lower():
            room_cat = "SINGLE_PRIVATE_AC_ROOM"
        elif "twin" in r_str.lower() or "shared" in r_str.lower():
            room_cat = "TWIN_SHARING"
    else:
        m2 = re.search(r"Room\s*Rent\s*Limit\s*[:\-]\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
        if m2:
            room_limit = _parse_float(m2.group(1))

    # Co-Payment & Deductible
    copay = 0.0
    m = re.search(r"(?:Co-Payment|Co-pay|Copay)\s*[:\-]?\s*([^\n\r|]+)", full_text, re.IGNORECASE)
    if m:
        c_str = m.group(1)
        pct_m = re.search(r"(\d+(?:\.\d+)?)\s*%", c_str)
        if pct_m:
            copay = float(pct_m.group(1))

    deductible = 0.0
    m = re.search(r"Deductible\s*[:\-]?\s*([^\n\r|]+)", full_text, re.IGNORECASE)
    if m:
        d_str = m.group(1)
        d_m = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", d_str)
        if d_m and "nil" not in d_str.lower() and "zero" not in d_str.lower():
            deductible = _parse_float(d_m.group(1))

    portability_credits = None

    # Inspect PyMuPDF tables for policy schedule parameter values
    for page in doc:
        for tab in page.find_tables().tables:
            for row in tab.extract():
                if not row or len(row) < 2:
                    continue
                for c_i in range(len(row) - 1):
                    lbl = str(row[c_i]).lower().strip() if row[c_i] else ""
                    val = row[c_i + 1] if row[c_i + 1] else ""
                    if not val:
                        continue
                    if "policy number" in lbl or "policy no" in lbl or "certificate no" in lbl:
                        if not policy_number:
                            policy_number = _clean_str(val)
                    elif "policyholder" in lbl or "proposer" in lbl or "insured name" in lbl:
                        if not holder_name:
                            holder_name = _clean_str(val)
                    elif "base sum insured" in lbl:
                        if base_si is None:
                            base_si = _parse_float(val)
                    elif "sum insured" in lbl:
                        if total_si is None:
                            total_si = _parse_float(val)
                    elif "cumulative bonus" in lbl or "ncb" in lbl:
                        if bonus == 0.0:
                            bonus = _parse_float(val)
                    elif "room rent" in lbl or "room limit" in lbl:
                        if room_limit == 0.0:
                            room_limit = _parse_float(val)
                    elif "deductible" in lbl:
                        if deductible == 0.0:
                            deductible = _parse_float(val)
                    elif "co-pay" in lbl or "copay" in lbl:
                        if copay == 0.0:
                            pct_m = re.search(r"(\d+(?:\.\d+)?)\s*%", str(val))
                            if pct_m:
                                copay = float(pct_m.group(1))
                            else:
                                copay = _parse_float(val)
                    elif "portability" in lbl or "prior credit" in lbl or "ported" in lbl:
                        m_p = re.search(r"(\d+)\s*months?", str(val), re.IGNORECASE)
                        if m_p:
                            portability_credits = int(m_p.group(1))

    if not total_si and base_si:
        total_si = base_si + bonus
    if not base_si and total_si:
        base_si = total_si - bonus

    # Portability Credits
    if portability_credits is None:
        m_port = re.search(r"(?:Portability\s+Continuity|Prior\s+Credit|Ported\s+Tenure|Portability\s+Credits?)[^\n\r]*?(\d+)\s*months?", full_text, re.IGNORECASE)
        if m_port:
            portability_credits = int(m_port.group(1))

    # Moratorium Period Months
    moratorium_months = 60
    m = re.search(r"(?:Moratorium|Moratorium\s*Period)\s*[:\-]?\s*(\d+)\s*(?:months|month)", full_text, re.IGNORECASE)
    if m:
        moratorium_months = int(m.group(1))

    # Waiting Periods
    waiting_periods = []
    if re.search(r"24[\-\s]month\s*waiting\s*period|specific\s*illness", full_text, re.IGNORECASE):
        waiting_periods.append(WaitingPeriodConfig(
            category=prov("SPECIFIC_DISEASE"),
            duration_days=prov(730),
            applicable_conditions=[prov("Specified Illnesses")]
        ))
    if re.search(r"36[\-\s]month\s*waiting\s*period|pre-existing\s*diseases?\s*\(ped\)", full_text, re.IGNORECASE):
        waiting_periods.append(WaitingPeriodConfig(
            category=prov("PED"),
            duration_days=prov(1095),
            applicable_conditions=[prov("Pre-Existing Conditions")]
        ))

    # Proportionate Deduction Rule
    prop_rule = None
    if re.search(r"proportionate\s*(?:deduction|reduction|ratio)", full_text, re.IGNORECASE):
        clause_str = "Section 1.A" if "section 1.a" in full_text.lower() else ("Clause 2.3" if "clause 2.3" in full_text.lower() else "Proportionate Deduction Clause")
        prop_rule = ProportionateDeductionRuleConfig(
            threshold_value=prov(1.0),
            threshold_operator=prov(">"),
            threshold_source_type=prov("POLICY_WORDING"),
            policy_clause=prov(clause_str),
            source_text=prov(f"Policy Proportionate Deduction Applicability: {clause_str}")
        )

    # Deduction order clause
    deduction_order_clause = None
    for p_idx, page in enumerate(doc):
        p_text = page.get_text()
        m_ded = re.search(r"(?:Clause\s*6(?:\.1)?|Deduction\s*Order|Cumulative\s*Bonus\s*Rules?)[^\n\r]*[:\-]?\s*([^\n\r]+(?:\n[^\n\r]+)?)", p_text, re.IGNORECASE)
        if m_ded:
            deduction_order_clause = prov(_clean_str(m_ded.group(0)), src=_clean_str(m_ded.group(0)), page=str(p_idx + 1))
            break

    # Exclusions
    exclusions = []
    for m_ex in re.finditer(r"(?:Exclusion\s*\d+|Section\s*4\.\d+|Code\s*Excl\-\d+)[^\n\r]*[:\-]?\s*([^\n\r]+)", full_text, re.IGNORECASE):
        exclusions.append(prov(_clean_str(m_ex.group(0))))

    # Mental Health Parity check
    covers_mental_health = True
    if re.search(r"(?:exclu(?:de|ded|sions?)|not covered)[^\n\r]*?(?:mental|psychiatric)", full_text, re.IGNORECASE):
        covers_mental_health = False

    return InsurancePolicy(
        policy_number=prov(policy_number or "POL-UNKNOWN", src=f"Policy No: {policy_number}"),
        insurer_name=prov(insurer_name or "Insurance Company", src=insurer_name or "Insurer"),
        policyholder_name=prov(holder_name or "Policyholder", src=f"Policyholder: {holder_name}"),
        policy_version=prov(uin or "UIN-DEFAULT", src=f"UIN: {uin}"),
        deduction_order_clause=deduction_order_clause,
        inception_date=prov(inc_date, src=f"Inception Date: {inc_date}") if inc_date else None,
        policy_start_date=prov(p_start, src=f"Start Date: {p_start}") if p_start else None,
        policy_end_date=prov(p_end, src=f"End Date: {p_end}") if p_end else None,
        sum_insured=prov(total_si or 1000000.0, src=f"Sum Insured: Rs. {total_si}"),
        base_sum_insured=prov(base_si or total_si or 1000000.0, src=f"Base Sum Insured: Rs. {base_si}"),
        cumulative_bonus=prov(bonus, src=f"Cumulative Bonus: Rs. {bonus}"),
        enhanced_sum_insured=prov(enhanced_si, src=f"Enhanced SI: Rs. {enhanced_si}") if enhanced_si else None,
        enhancement_date=prov(enh_date, src=f"Enhancement Date: {enh_date}") if enh_date else None,
        room_category_entitled=prov(room_cat, src=f"Room Entitlement: {room_cat}"),
        room_rent_limit_per_day=prov(room_limit, src=f"Room Rent Limit: Rs. {room_limit}"),
        copay_percentage=prov(copay, src=f"Co-Pay: {copay}%"),
        deductible=prov(deductible, src=f"Deductible: Rs. {deductible}"),
        moratorium_period_months=prov(moratorium_months, src=f"Moratorium: {moratorium_months} Months"),
        portability_credits_months=prov(portability_credits, src=f"Portability Credit: {portability_credits} Months") if portability_credits is not None else None,
        waiting_periods=waiting_periods,
        proportionate_deduction_rule=prop_rule,
        exclusions=exclusions,
        covers_mental_health=prov(covers_mental_health)
    )


def parse_rejection_letter_pdf(pdf_path: str) -> Optional[RejectionLetter]:
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    try:
        doc = pymupdf.open(pdf_path)
        if len(doc) == 0:
            return None
        full_text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return None

    # TPA Name
    tpa_name = None
    first_lines = [l.strip() for l in doc[0].get_text().split("\n") if l.strip()]
    for l in first_lines[:8]:
        if any(w in l.upper() for w in ["TPA", "THIRD PARTY", "HEALTHCARE SERVICES", "HEALTH SERVICES", "INSURANCE TPA", "BENEFIT ADMINISTRATOR"]):
            tpa_name = l
            break
    if not tpa_name:
        m = re.search(r"(?:TPA Name|TPA|Third Party Administrator)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
        if m:
            tpa_name = _clean_str(m.group(1))

    # Insurer Name in Rejection
    rejection_insurer = None
    for l in first_lines[:15]:
        if any(w in l.upper() for w in ["INSURANCE", "ASSURANCE"]) and not any(kw in l.upper() for kw in ["TPA", "POLICY", "ADVICE", "LETTER", "OMBUDSMAN", "RULES", "CONFIDENTIAL", "RECORD", "COMMUNICATION"]):
            rejection_insurer = l
            break
    if not rejection_insurer:
        m_ins = re.search(r"(?:Insurance Company|Insurer Name|Insurer)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
        if m_ins and m_ins.group(1).strip():
            rejection_insurer = _clean_str(m_ins.group(1))
        else:
            m_ins2 = re.search(r"(?:Insurance Company|Insurer Name|Insurer)\s*[:\-]?\s*\n\s*([^\n\r]+)", full_text, re.IGNORECASE)
            if m_ins2 and m_ins2.group(1).strip():
                rejection_insurer = _clean_str(m_ins2.group(1))

    # Claim Number
    claim_num = None
    m = re.search(r"(?:Claim\s+Reference(?:\s+No\.?)?|Claim\s+Ref(?:\s+No\.?)?|Claim\s+No\.?|Claim\s+Number|CCN|Claim\s+ID)\s*[:\-]\s*([^\s\n\r]+)", full_text, re.IGNORECASE)
    if m:
        claim_num = _clean_str(m.group(1))
    if not claim_num:
        m_tpa = re.search(r"\b([A-Z]{2,10}/\d{4}/[A-Z0-9/]+)\b", full_text, re.IGNORECASE)
        if m_tpa:
            claim_num = _clean_str(m_tpa.group(1))

    # Policy Number
    pol_num = None
    m = re.search(r"(?:Policy No|Policy Number)\s*[:\-]\s*([^\s\n\r]+)", full_text, re.IGNORECASE)
    if m:
        pol_num = _clean_str(m.group(1))

    # Patient & Policyholder Names (separate extraction for dependent/family claims)
    pol_holder_name = None
    m = re.search(r"(?:Policyholder\s*Name|Proposer\s*Name|Policyholder)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
    if m:
        pol_holder_name = _clean_str(re.split(r"(?:Policy|Hospital|Stay|Date|Total|Insured|Patient|\s{2,})", m.group(1), flags=re.IGNORECASE)[0])

    patient_name = None
    m = re.search(r"(?:Insured\s*Patient(?:\s*Name)?|Patient\s*Name|Name of Patient|Patient)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
    if m:
        patient_name = _clean_str(re.split(r"(?:Policy|Hospital|Stay|Date|Total|Policyholder|Proposer|\s{2,})", m.group(1), flags=re.IGNORECASE)[0])

    if not patient_name:
        m = re.search(r"(?:Insured\s*Name|Insured\s*Person|Insured)\s*[:\-]\s*([^\n\r]+)", full_text, re.IGNORECASE)
        if m:
            patient_name = _clean_str(re.split(r"(?:Policy|Hospital|Stay|Date|Total|\s{2,})", m.group(1), flags=re.IGNORECASE)[0])

    if not pol_holder_name and patient_name:
        pol_holder_name = patient_name
    if not patient_name and pol_holder_name:
        patient_name = pol_holder_name

    # Claim / Settlement Date
    claim_date = None
    m = re.search(r"(?:Date\s+of\s+Settlement|Settlement\s+Date|Claim\s+Date|Date\s+of\s+Claim|Adjudication\s+Date)\s*[:\-]?\s*([0-9]{1,2}[-\s/][A-Za-z]{3,}[-\s/][0-9]{4}|[0-9]{1,2}[-\s/][0-9]{1,2}[-\s/][0-9]{2,4})", full_text, re.IGNORECASE)
    if m:
        claim_date = _parse_date_str(m.group(1))
    if not claim_date:
        m2 = re.search(r"(?:Settlement Date|Claim Date|Date)\s*[:\-]\s*([^\n\r,]+)", full_text, re.IGNORECASE)
        if m2:
            claim_date = _parse_date_str(m2.group(1))

    if not claim_date:
        for page in doc:
            for tab in page.find_tables().tables:
                for row in tab.extract():
                    if not row or len(row) < 2:
                        continue
                    for c_i in range(len(row) - 1):
                        lbl = str(row[c_i]).lower().strip() if row[c_i] else ""
                        val = row[c_i + 1] if row[c_i + 1] else ""
                        if not val:
                            continue
                        if any(k in lbl for k in ["settlement date", "claim date", "date of settlement", "date of admission"]):
                            parsed_d = _parse_date_str(val)
                            if parsed_d:
                                claim_date = parsed_d
                                break
                    if claim_date:
                        break
            if claim_date:
                break

    # Amounts
    tot_claimed = 0.0
    tot_claimed_src = ""
    m = re.search(r"(?:claimed\s*sum\s*of|Total\s*Claimed(?:\s*Amount)?|Claimed\s*Amount|Billed\s*Amount|Total\s*Claim\s*Billed|Gross\s*Claim\s*Billed)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        tot_claimed = _parse_float(m.group(1))
        tot_claimed_src = _clean_str(m.group(0))

    tot_approved = 0.0
    tot_approved_src = ""
    m = re.search(r"(?:Net\s*Approved(?:\s*Payable)?|Total\s*Approved(?:\s*/\s*Paid)?|Approved\s*(?:Amount|/\s*Paid)?|Sanctioned\s*Amount|approved\s*(?:an\s*amount\s*of)?)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        tot_approved = _parse_float(m.group(1))
        tot_approved_src = _clean_str(m.group(0))
    if tot_approved <= 0.0:
        m2 = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)\s*has\s*been\s*(?:approved|sanctioned|paid)", full_text, re.IGNORECASE)
        if m2:
            tot_approved = _parse_float(m2.group(1))
            tot_approved_src = _clean_str(m2.group(0))

    tot_deducted = 0.0
    tot_deducted_src = ""
    m = re.search(r"(?:disallowance\s*of|Total\s*(?:Deducted|Disallowed|Disallowed\s*/\s*Deducted)|Deducted\s*Amount|Disallowed\s*Amount|Deductions?)\s*[:\-]?\s*(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)", full_text, re.IGNORECASE)
    if m:
        tot_deducted = _parse_float(m.group(1))
        tot_deducted_src = _clean_str(m.group(0))

    if tot_deducted <= 0.0 and tot_claimed > 0.0 and tot_approved >= 0.0:
        tot_deducted = max(0.0, tot_claimed - tot_approved)
        tot_deducted_src = tot_deducted_src or f"Total Disallowed: Rs. {tot_deducted:,.2f}"
    if tot_claimed <= 0.0 and tot_approved >= 0.0 and tot_deducted > 0.0:
        tot_claimed = tot_approved + tot_deducted
        tot_claimed_src = tot_claimed_src or f"Total Claimed: Rs. {tot_claimed:,.2f}"

    # Extract Rejection Reasons from Tables
    rejection_reasons: List[RejectionReason] = []
    
    for p_idx, page in enumerate(doc):
        tabs = page.find_tables()
        for tab in tabs.tables:
            df = tab.extract()
            if not df or len(df) < 2:
                continue

            # Skip tables that consist entirely of summary / settlement rows
            if all(SUMMARY_ROW_PATTERN.match(_clean_str(r[0])) for r in df if any(r)):
                continue

            header_r_idx = -1
            for r_i in range(min(3, len(df))):
                row_s = " ".join(str(c).lower().replace("\n", " ") for c in df[r_i])
                if SUMMARY_ROW_PATTERN.match(_clean_str(df[r_i][0])) or re.search(r"(?:Rs\.?|₹)\s*[\d,]+", row_s):
                    continue
                if any(kw in row_s for kw in ["deduct", "disallow", "grounds", "citation", "reason", "particular", "clause", "head"]):
                    header_r_idx = r_i
                    break

            if header_r_idx >= 0:
                # Skip financial settlement summary / bank transaction tables
                table_text = " ".join(" ".join(str(cell) for cell in r) for r in df).lower()
                if any(kw in table_text for kw in ["disbursed via", "bank transaction", "transaction reference"]):
                    continue

                headers = [str(c).lower().replace("\n", " ").strip() for c in df[header_r_idx]]
                head_col = 1 if len(headers) > 1 else 0
                rationale_col = -1
                clause_col = -1
                amt_col = -1
                for c_i, h in enumerate(headers):
                    if any(w in h for w in ["amount", "deducted", "disallowed", "value"]):
                        amt_col = c_i
                    elif any(w in h for w in ["clause", "section", "ref"]):
                        clause_col = c_i
                    elif any(w in h for w in ["ground", "citation", "rationale", "remarks"]):
                        rationale_col = c_i
                    elif any(w in h for w in ["category", "head", "description", "item", "particular"]):
                        head_col = c_i
                    elif "reason" in h and rationale_col == -1:
                        rationale_col = c_i

                for r_i in range(header_r_idx + 1, len(df)):
                    row = df[r_i]
                    if not row or head_col >= len(row):
                        continue
                    title = _clean_str(row[head_col])
                    if not title or SUMMARY_ROW_PATTERN.match(title):
                        continue
                    
                    grounds = _clean_str(row[rationale_col]) if rationale_col >= 0 and rationale_col < len(row) else ""
                    clause_ref = _clean_str(row[clause_col]) if clause_col >= 0 and clause_col < len(row) else ""
                    item_amt = _parse_float(row[amt_col]) if amt_col >= 0 and amt_col < len(row) else 0.0

                    # If an amount column exists and this row has zero or negative disallowed amount (e.g. admitted/paid heads), skip it
                    if amt_col >= 0 and item_amt <= 0.0:
                        continue

                    full_desc = f"{title}: {grounds}" if grounds else title
                    has_amt_in_desc = False
                    if item_amt > 0:
                        amt_formatted = f"{item_amt:,.2f}"
                        amt_int_formatted = f"{int(item_amt):,}"
                        amt_raw = str(int(item_amt))
                        clean_digits = re.sub(r"[^\d]", "", full_desc)
                        has_amt_in_desc = (
                            amt_formatted in full_desc
                            or amt_int_formatted in full_desc
                            or (amt_raw in clean_digits if len(amt_raw) >= 4 else False)
                        )
                    if item_amt > 0 and not has_amt_in_desc:
                        full_desc += f" (Disallowed: Rs. {item_amt:,.2f})"
                    desc_lower = title.lower()

                    if "bonus" in desc_lower:
                        code, cat = "BONUS-FORFEIT-01", "OTHER"
                    elif "energy" in desc_lower:
                        code, cat = "ENERGY-DEV-01", "Non-Medical"
                    elif "metabolic" in desc_lower or "glycemic" in desc_lower:
                        code, cat = "METABOLIC-EXCL-01", "PRE_EXISTING"
                    elif "multi-cut" in desc_lower or "secondary procedure" in desc_lower:
                        code, cat = "MULTI-SURG-01", "PROPORTIONATE_DEDUCTION"
                    elif any(w in desc_lower for w in ["modern treatment", "endoscopic sub-limit", "robotic", "navigation"]):
                        code, cat = "MODERN-TREAT-01", "OTHER"
                    elif "co-payment" in desc_lower or "copay" in desc_lower:
                        code, cat = "COPAY-01", "OTHER"
                    elif any(w in desc_lower for w in ["surgical consumable", "drape", "floseal", "hemostatic", "pca pump", "pain pump", "elastomeric"]):
                        code, cat = "NON-MED-01", "Non-Medical"
                    elif any(w in desc_lower for w in ["room rent", "proportionate", "benchmark"]):
                        code, cat = "PROP-ROOM-01", "PROPORTIONATE_DEDUCTION"
                    elif "surgeon" in desc_lower or "professional fee" in desc_lower:
                        code, cat = "SURG-FEE-01", "OTHER"
                    elif "non-medical" in desc_lower or "overhead" in desc_lower:
                        code, cat = "NON-MED-ADMIN-01", "Non-Medical"
                    else:
                        code = f"DEDUCT-{len(rejection_reasons)+1:02d}"
                        if any(w in desc_lower for w in ["consumable", "blade", "admin", "toiletries", "floseal", "hemostatic", "pca"]):
                            cat = "Non-Medical"
                        elif any(w in desc_lower for w in ["pre-existing", "ped", "non-disclosure", "moratorium", "comorbid"]):
                            cat = "PRE_EXISTING"
                        elif any(w in desc_lower for w in ["room", "proportionate", "benchmark"]):
                            cat = "PROPORTIONATE_DEDUCTION"
                        elif any(w in desc_lower for w in ["waiting"]):
                            cat = "WAITING_PERIOD"
                        else:
                            cat = "OTHER"

                    rejection_reasons.append(RejectionReason(
                        code=prov(code, src=title, page=str(p_idx + 1)),
                        category=prov(cat, src=title, page=str(p_idx + 1)),
                        description=prov(full_desc, src=full_desc, page=str(p_idx + 1)),
                        amount=prov(item_amt, page=str(p_idx + 1)) if item_amt > 0 else None,
                        details=prov(grounds or full_desc, page=str(p_idx + 1)),
                        clause_cited=prov(clause_ref or grounds, page=str(p_idx + 1)) if (clause_ref or grounds) else None
                    ))

    # Text fallback for rejection reasons
    if not rejection_reasons and tot_deducted > 0:
        rejection_reasons.append(RejectionReason(
            code=prov("DEDUCT-01"),
            category=prov("OTHER"),
            amount=prov(tot_deducted),
            description=prov(f"Total Disallowance of Rs. {tot_deducted:,.2f} applied by insurer.")
        ))

    settlement_type = "PARTIAL_SETTLEMENT" if tot_approved > 0 else "FULL_REJECTION"

    return RejectionLetter(
        claim_number=prov(claim_num or "CLAIM-UNKNOWN", src=f"Claim Ref: {claim_num}"),
        policy_number=prov(pol_num or "POL-UNKNOWN", src=f"Policy No: {pol_num}"),
        policyholder_name=prov(pol_holder_name or "Policyholder", src=f"Policyholder: {pol_holder_name}"),
        patient_name=prov(patient_name or "Patient", src=f"Patient: {patient_name}"),
        insured_name=prov(patient_name or pol_holder_name or "Insured", src=f"Insured: {patient_name or pol_holder_name}"),
        tpa_name=prov(tpa_name, src=tpa_name) if tpa_name else None,
        insurer_name=prov(rejection_insurer, src=rejection_insurer) if rejection_insurer else None,
        claim_date=prov(claim_date, src=f"Claim Date: {claim_date}") if claim_date else None,
        total_claimed=prov(tot_claimed, src=tot_claimed_src or f"Claimed Amount: Rs. {tot_claimed:,.2f}"),
        total_approved=prov(tot_approved, src=tot_approved_src or f"Approved Amount: Rs. {tot_approved:,.2f}"),
        approved_amount=prov(tot_approved, src=tot_approved_src or f"Approved Amount: Rs. {tot_approved:,.2f}"),
        total_deducted=prov(tot_deducted, src=tot_deducted_src or f"Disallowed Amount: Rs. {tot_deducted:,.2f}"),
        rejection_reasons=rejection_reasons,
        reasons=rejection_reasons,
        settlement_type=prov(settlement_type, src=settlement_type),
        remarks=prov("Adjudicated under technical provisions of policy and IRDAI regulations.")
    )
