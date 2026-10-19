from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..rules import get_val
from ..rules.non_payable_items import classify_line_item, has_surgical_or_icu_procedure
from .calculator import FinancialMath as fmath


class PreDischargeSimulationResult(BaseModel):
    is_interim: bool = True
    has_room_rent_excess: bool = False
    actual_room_rate: float = 0.0
    eligible_room_rate: float = 0.0
    excess_per_day: float = 0.0
    length_of_stay: int = 1
    projected_room_excess: float = 0.0
    projected_proportionate_deduction: float = 0.0
    projected_total_out_of_pocket: float = 0.0
    deduction_ratio: float = 0.0
    warning_message: str = ""
    recommended_action: str = ""
    scrubbed_non_payable_items: List[Dict[str, Any]] = Field(default_factory=list)
    total_scrubbed_non_payables: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PreDischargeSimulator:
    """
    Simulates pre-discharge financial exposures for interim hospital bills.
    Calculates room rent multiplier cascading deductions across associated medical
    expenses (surgeon, nursing, OT) and scrubs line items for unauthorized non-payables.
    """

    def __init__(self, room_excess_buffer: float = 0.0):
        # Buffer threshold above limit before triggering warning (defaults to > 0 excess)
        self.room_excess_buffer = room_excess_buffer

    def simulate(self, bill: HospitalBill, policy: InsurancePolicy) -> PreDischargeSimulationResult:
        actual_room_rate = fmath.extract(get_val(bill, "room_charges_per_day", 0.0) or 0.0)
        policy_room_limit = fmath.extract(get_val(policy, "room_rent_limit_per_day", 0.0) or 0.0)

        # Fallback to scanning line items if room_charges_per_day is missing/zero
        if actual_room_rate <= 0:
            for item in get_val(bill, "line_items", []):
                cat = str(get_val(item, "category", "") or "").upper()
                if cat == "ROOM":
                    unit_rate = fmath.extract(get_val(item, "unit_rate", 0.0) or 0.0)
                    if unit_rate > 0:
                        actual_room_rate = unit_rate
                        break
                    amt = fmath.extract(get_val(item, "amount", 0.0) or 0.0)
                    qty = fmath.extract(get_val(item, "quantity", 1.0) or 1.0)
                    if amt > 0:
                        actual_room_rate = amt / (qty if qty > 0 else 1.0)
                        break
        
        # Length of stay fallback
        los = get_val(bill, "length_of_stay", None)
        if los is None or los <= 0:
            los = 1
        los = int(los)

        is_interim = getattr(bill, "is_interim_bill", False) or (bill.discharge_date is None and bill.estimated_discharge_date is not None)

        excess_per_day = max(0.0, actual_room_rate - policy_room_limit)
        has_excess = excess_per_day > self.room_excess_buffer and policy_room_limit > 0

        projected_room_excess = excess_per_day * los if has_excess else 0.0
        projected_prop_deduction = 0.0
        deduction_ratio = 0.0

        if has_excess and actual_room_rate > 0:
            deduction_ratio = 1.0 - (policy_room_limit / actual_room_rate)

            # Ingest associated medical expenses (Surgeon, Nursing, OT, Consultation)
            associated_sum = 0.0
            for item in get_val(bill, "line_items", []):
                cat = str(get_val(item, "category", "") or "").upper()
                amt = fmath.extract(get_val(item, "amount", 0.0))
                # Associated medical charges subject to room multiplier
                if cat in ["NURSING", "CONSULTATION", "OT"]:
                    associated_sum += amt

            projected_prop_deduction = associated_sum * deduction_ratio

        total_out_of_pocket = projected_room_excess + projected_prop_deduction

        if has_excess:
            warning_msg = (
                f"Your room choice of ₹{actual_room_rate:,.0f}/day exceeds your policy cap of ₹{policy_room_limit:,.0f}/day. "
                f"This ₹{excess_per_day:,.0f} upgrade will trigger a projected ₹{project_amount_format(projected_prop_deduction)} "
                f"out-of-pocket deduction on surgical and OT charges upon discharge. "
                "Recommended action: Request downgrade to eligible category if clinically viable."
            )
            rec_action = "Request downgrade to eligible category if clinically viable."
        else:
            warning_msg = "Room charges are within eligible policy limits. No proportionate deduction cascading expected."
            rec_action = "Maintain current room category."

        # Scrub bill for non-payables
        scrubbed_items, total_scrubbed = self.scrub_interim_bill(bill)

        return PreDischargeSimulationResult(
            is_interim=is_interim,
            has_room_rent_excess=has_excess,
            actual_room_rate=actual_room_rate,
            eligible_room_rate=policy_room_limit,
            excess_per_day=excess_per_day,
            length_of_stay=los,
            projected_room_excess=projected_room_excess,
            projected_proportionate_deduction=projected_prop_deduction,
            projected_total_out_of_pocket=total_out_of_pocket,
            deduction_ratio=deduction_ratio,
            warning_message=warning_msg,
            recommended_action=rec_action,
            scrubbed_non_payable_items=scrubbed_items,
            total_scrubbed_non_payables=total_scrubbed
        )

    def scrub_interim_bill(self, bill: HospitalBill) -> tuple[List[Dict[str, Any]], float]:
        """Scrubs interim bill line items against IRDAI Annexure A non-payable schedules."""
        is_surgical = has_surgical_or_icu_procedure(bill)
        scrubbed = []
        total_amt = 0.0

        for item in get_val(bill, "line_items", []):
            desc = str(get_val(item, "description", "") or "")
            cat = str(get_val(item, "category", "") or "").upper()
            amt = fmath.extract(get_val(item, "amount", 0.0) or 0.0)
            if amt <= 0.0:
                rate = fmath.extract(get_val(item, "unit_rate", 0.0) or 0.0)
                qty = fmath.extract(get_val(item, "quantity", 1.0) or 1.0)
                if rate > 0.0:
                    amt = rate * (qty if qty > 0 else 1.0)

            classification = classify_line_item(desc, cat)
            if classification == "LIST_I":
                scrubbed.append({
                    "description": desc,
                    "category": cat,
                    "amount": amt,
                    "classification": "LIST_I_NON_PAYABLE",
                    "reason": "Strictly non-medical/non-payable item under IRDAI Annexure A List I."
                })
                total_amt += amt
            elif classification == "LIST_III" and not is_surgical:
                scrubbed.append({
                    "description": desc,
                    "category": cat,
                    "amount": amt,
                    "classification": "LIST_III_DISALLOWABLE_WITHOUT_SURGERY",
                    "reason": "Surgical consumable billed without documented OT/ICU procedure."
                })
                total_amt += amt

        return scrubbed, total_amt


def project_amount_format(amt: float) -> str:
    if amt == int(amt):
        return f"{int(amt):,}"
    return f"{amt:,.2f}"


def simulate_predischarge(bill: HospitalBill, policy: InsurancePolicy) -> PreDischargeSimulationResult:
    simulator = PreDischargeSimulator()
    return simulator.simulate(bill, policy)
