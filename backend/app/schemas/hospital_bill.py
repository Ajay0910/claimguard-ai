from pydantic import BaseModel, model_validator, computed_field
from typing import Optional, Literal
from datetime import datetime
from .provenance import Provenance

class BillLineItem(BaseModel):
    item_code: Optional[Provenance[str]] = None
    description: Optional[Provenance[str]] = None
    category: Optional[Provenance[Literal["ROOM", "NURSING", "CONSULTATION", "LAB", "RADIOLOGY", "OT", "PHARMACY", "CONSUMABLES", "MISCELLANEOUS"]]] = None
    quantity: Optional[Provenance[float]] = None
    unit_rate: Optional[Provenance[float]] = None
    amount: Optional[Provenance[float]] = None
    total: float = 0.0
    is_room_linked: bool = False

class HospitalBill(BaseModel):
    bill_id: Optional[Provenance[str]] = None
    total_amount: Provenance[float] = Provenance(value=0.0)
    hospital_name: Optional[Provenance[str]] = None
    hospital_address: Optional[Provenance[str]] = None
    gstin: Optional[Provenance[str]] = None
    uhid: Optional[Provenance[str]] = None
    patient_name: Optional[Provenance[str]] = None
    patient_age: Optional[Provenance[int]] = None
    patient_gender: Optional[Provenance[str]] = None
    admission_date: Optional[Provenance[str]] = None
    discharge_date: Optional[Provenance[str]] = None
    estimated_discharge_date: Optional[Provenance[str]] = None
    is_interim_bill: bool = False
    doctor_name: Optional[Provenance[str]] = None
    ward_type: Optional[Provenance[str]] = None
    bed_number: Optional[Provenance[str]] = None
    tpa_or_insurer: Optional[Provenance[str]] = None
    diagnosis: Optional[Provenance[str]] = None
    line_items: list[BillLineItem] = []
    subtotal: Optional[Provenance[float]] = None
    tax_amount: Provenance[float] = Provenance(value=0.0)
    discount: Provenance[float] = Provenance(value=0.0)
    net_payable: Optional[Provenance[float]] = None
    arithmetic_verified: bool = False
    extraction_confidence: float = 1.0

    @model_validator(mode='after')
    def verify_arithmetic(self) -> 'HospitalBill':
        if not self.line_items or not self.subtotal:
            self.arithmetic_verified = False
            return self
        try:
            total = sum((item.amount.value if item.amount else 0.0) for item in self.line_items)
            self.arithmetic_verified = abs(total - self.subtotal.value) <= 1.0
        except Exception:
            self.arithmetic_verified = False
        return self

    @computed_field
    @property
    def room_charges_per_day(self) -> Optional[float]:
        for item in self.line_items:
            cat = getattr(item.category, 'value', item.category) if item.category else None
            if cat == "ROOM":
                rate = getattr(item.unit_rate, 'value', item.unit_rate) if item.unit_rate else None
                if rate is not None and float(rate) > 0:
                    return float(rate)
                amt = getattr(item.amount, 'value', item.amount) if item.amount else None
                qty = getattr(item.quantity, 'value', item.quantity) if item.quantity else 1.0
                if amt is not None and float(amt) > 0:
                    q = float(qty) if qty and float(qty) > 0 else 1.0
                    return float(amt) / q
        return None

    @computed_field
    @property
    def length_of_stay(self) -> Optional[int]:
        effective_discharge = self.discharge_date or self.estimated_discharge_date
        if self.admission_date and effective_discharge:
            def parse_date(d_val) -> Optional[datetime]:
                d_str = getattr(d_val, 'value', d_val) if d_val else None
                if not d_str or str(d_str).strip().upper() in ["", "NONE", "NULL", "N/A"]:
                    return None
                d_str = str(d_str).strip()
                for fmt in [
                    None,
                    '%d/%m/%Y',
                    '%d-%m-%Y',
                    '%Y-%m-%d',
                    '%Y/%m/%d'
                ]:
                    try:
                        if fmt is None:
                            return datetime.fromisoformat(d_str.replace('Z', '+00:00'))
                        else:
                            return datetime.strptime(d_str, fmt)
                    except (ValueError, TypeError):
                        continue
                return None
            try:
                admit = parse_date(self.admission_date)
                discharge = parse_date(effective_discharge)
                if admit and discharge:
                    days = (discharge.date() - admit.date()).days
                    return max(1, days)
            except Exception:
                pass
        return None
