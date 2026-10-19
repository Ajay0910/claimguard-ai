from . import get_val
from typing import List, Dict, Any, Tuple
from ..schemas.hospital_bill import HospitalBill, BillLineItem
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import RuleVerdict
from .rule_registry import register_rule
from ..engine.calculator import FinancialMath as fmath

# ==============================================================================
# IRDAI Guidelines on Standardization in Health Insurance (Annexure A)
# Lists I to IV: 68 Non-Payable Items & Subsumed Expenses Schedule
# ==============================================================================

# List I: Strictly Non-Payable Items (Items for which optional cover may be offered / excluded non-medical items)
LIST_I_ITEMS = [
    "BABY FOOD", "BABY UTILITIES CHARGES", "BEAUTY SERVICES", "BELTS", "BRACES",
    "BUDS", "COLD PACK", "HOT PACK", "CARRY BAGS", "COMMODE",
    "DIAPERS", "DISPOSABLES", "TOILET PAPER", "TISSUE PAPER", "SLIPPERS",
    "FOOTWEAR", "TOOTHBRUSH", "TOOTHPASTE", "THERMOMETER", "TELEPHONE CHARGES",
    "ATTENDANT CHARGES", "MINERAL WATER", "BOTTLED WATER", "ATTENDANT FOOD",
    "VISITOR FOOD", "LUXURY CHARGES", "LAUNDRY CHARGES", "EXTRA BED CHARGES",
    "ADMINISTRATIVE FEES", "REGISTRATION FEE", "ADMISSION FEE", "DOCUMENTATION CHARGES",
    "MEDICAL RECORD CHARGES", "ADMISSION KIT", "BIRTH CERTIFICATE", "MORTUARY CHARGES",
    "HEARSE CHARGES", "BARBER CHARGES", "RAZOR", "BLADE", "TOWEL",
    "SOAP", "SHAMPOO", "VISITOR HAND SANITIZER", "MOUTHWASH", "TALCUM POWDER",
    "COMB", "WET WIPES", "FACE TISSUE", "KETTLE", "TELEVISION CHARGES",
    "WIFI CHARGES", "INTERNET CHARGES", "CAR PARKING", "AMBULANCE COLLAR",
    "ARM SLING", "KNEE BRACE", "KNEE CAPS", "LUMBAR SACRAL BELT", "CERVICAL COLLAR",
    "WALKING STICK", "CRUTCHES", "WHEELCHAIR RENTAL", "EYE PATCH", "HEARING AID",
    "SPECTACLES", "CONTACT LENSES", "PROTEIN POWDER", "WEIGHT MACHINE"
]

# List II: Items that are to be subsumed into Room Charges
LIST_II_ITEMS = [
    "HOUSEKEEPING CHARGES", "ROOM CLEANING", "ROOM SANITIZATION", "LINEN",
    "BED SHEETS", "PILLOW COVERS", "BLANKET", "WATER HEATER", "GEYSER",
    "AIR CONDITIONER CHARGES", "FAN CHARGES", "LIGHTING", "BASIC NURSING CHARGES",
    "BED PAN", "URINAL", "SPUTUM CUP", "IV STAND", "DRIP STAND",
    "PATIENT GOWN", "HOSPITAL UNIFORM", "ROOM SERVICE TAX", "ROOM GST", "ROOM LUXURY TAX",
    "BIO-MEDICAL WASTE DISPOSAL"
]

# List III: Items payable when associated with Surgery or ICU (Subsumed into Procedure/ICU charges)
LIST_III_ITEMS = [
    "SURGICAL BLADE", "SURGICAL GLOVES", "STERILE GLOVES", "OT GOWNS", "SURGEON GOWN",
    "SURGICAL DRAPES", "DRAPE SHEET", "MONITOR SHEETS", "OT SHEETS", "DISPOSABLE SURGICAL",
    "SURGICAL DISPOSABLES", "SURGICAL DISPOSABLE", "DISPOSABLE SURGICALS",
    "SURGICAL ACCESSORIES", "OT MASKS", "SURGICAL CAPS", "SHOE COVERS", "DISPOSABLE SYRINGES",
    "NEEDLES", "SURGICAL GAUZE", "ROLLER BANDAGE", "BAND-AID", "STERILE DRESSING",
    "ADHESIVE TAPE", "LEUCOPLAST", "STERILE DISPOSABLE KIT", "LAPAROSCOPY ACCESSORIES",
    "ARTHROSCOPY ACCESSORIES", "CARDIAC MONITOR ELECTRODES", "PULSE OXIMETER PROBES",
    "ENDOTRACHEAL TUBE", "STYLET", "SUCTION CATHETER", "YANKAUER SUCTION",
    "CAUTERY PENCIL", "CAUTERY PLATE", "GROUND PAD", "SPINAL NEEDLE", "EPIDURAL KIT",
    "CENTRAL LINE CATHETER", "TRIPLE LUMEN CATHETER", "IV CANNULA", "SUTURE MATERIALS",
    "VICRYL", "PROLENE", "ETHILON", "SURGICAL STAPLES", "SURGICAL SUTURE",
    "DRAINAGE BAGS", "WOUND DRAIN", "ROMO VAC DRAIN", "ARTERIAL LINE KIT",
    "TRANSDUCER", "DEFIBRILLATOR PADS", "VENTILATOR CIRCUIT", "HME FILTER",
    "FORMALIN CONTAINER", "BIOPSY CONTAINER", "3-WAY STOPCOCK", "COTTON"
]

# List IV: Items to be subsumed into Treatment / Doctor / Consultant Package
LIST_IV_ITEMS = [
    "EXAMINATION GLOVES", "CLEAN GLOVES", "ALCOHOL SWABS", "SPIRIT SWABS",
    "ANTISEPTIC SOLUTION", "BETADINE", "CHLORHEXIDINE", "BASIC DRESSING CHARGES",
    "STETHOSCOPE", "BP CUFF", "SPHYGMOMANOMETER", "TONGUE DEPRESSOR"
]


def _normalize_token(token: str) -> str:
    t = token.strip().upper()
    if len(t) > 3 and t.endswith("S"):
        return t[:-1]
    return t


def _match_item_list(description: str, item_list: List[str]) -> bool:
    desc_clean = description.upper().replace("-", " ").replace("/", " ")
    desc_words = {_normalize_token(w) for w in desc_clean.split()}
    for entry in item_list:
        entry_clean = entry.upper().replace("-", " ").replace("/", " ")
        if entry_clean in desc_clean:
            return True
        entry_words = [_normalize_token(w) for w in entry_clean.split()]
        if entry_words and all(w in desc_words for w in entry_words):
            return True
    return False


def classify_line_item(item_desc: str, item_category: str = "") -> str:
    """Classifies a hospital bill line item into IRDAI Annexure A Lists I-IV or UNCLASSIFIED."""
    desc = str(item_desc or "").strip()
    if not desc:
        return "UNCLASSIFIED"
    
    if _match_item_list(desc, LIST_III_ITEMS):
        return "LIST_III"
    if _match_item_list(desc, LIST_I_ITEMS):
        return "LIST_I"
    if _match_item_list(desc, LIST_II_ITEMS):
        return "LIST_II"
    if _match_item_list(desc, LIST_IV_ITEMS):
        return "LIST_IV"
    return "UNCLASSIFIED"


def has_surgical_or_icu_procedure(bill: HospitalBill) -> bool:
    """Detects if the hospitalization involved surgery, OT, or ICU care."""
    diagnosis = str(get_val(bill, "diagnosis", "") or "").lower()
    if any(kw in diagnosis for kw in ["surgery", "operative", "post-op", "fracture", "trauma", "icu", "c-section", "laparoscopy", "appendectomy", "cholecystectomy"]):
        return True

    for item in get_val(bill, "line_items", []):
        cat = str(get_val(item, "category", "") or "").upper()
        desc = str(get_val(item, "description", "") or "").lower()
        if cat in ["OT", "ICU"]:
            return True
        if any(kw in desc for kw in ["operation theatre", "surgery", "surgeon fee", "ot charges", "icu charges", "intensive care", "laparoscop", "arthroscop"]):
            return True

    return False


@register_rule(
    name="Non-Payable Items Rule",
    description="Validates deductions against IRDAI Annexure A 68 Non-Payable Items Schedule.",
    tier=1,
    regulatory_citation="IRDAI Guidelines on Standardization in Health Insurance (Annexure A - Lists I to IV)"
)
def check_non_payable_items(bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, state=None) -> RuleVerdict:
    """
    Validates whether items deducted as 'non-payable' or 'consumables' comply with
    IRDAI Guidelines on Standardization in Health Insurance (Annexure A, Lists I-IV).
    
    Specifically guards:
    - List III surgical items (surgical blades, OT gowns, monitor sheets, sterile gloves, suture)
      are STATUTORILY PAYABLE during surgery or ICU admissions and cannot be deducted.
    - List I items are confirmed as legitimate non-medical exclusions.
    """
    try:
        line_items = get_val(bill, "line_items", [])
        if not line_items:
            return RuleVerdict(
                status="SKIPPED",
                rule_name="Non-Payable Items Rule",
                rule_description="Validates deductions against IRDAI Annexure A non-payable schedule.",
                confidence=1.0,
                finding="No line items available in bill to audit non-payable schedule."
            )

        is_surgery_or_icu = has_surgical_or_icu_procedure(bill)

        list_i_billed = 0.0
        list_iii_billed = 0.0
        list_iii_items_found: List[Tuple[str, float]] = []
        list_i_items_found: List[Tuple[str, float]] = []

        for item in line_items:
            desc = str(get_val(item, "description", "") or "")
            cat = str(get_val(item, "category", "") or "").upper()
            amt = fmath.extract(get_val(item, "amount", 0.0))

            classification = classify_line_item(desc, cat)
            if classification == "LIST_III":
                list_iii_billed += amt
                list_iii_items_found.append((desc, amt))
            elif classification == "LIST_I":
                list_i_billed += amt
                list_i_items_found.append((desc, amt))

        rejection_reasons = get_val(rejection, "rejection_reasons", None) or get_val(rejection, "reasons", []) or []
        reasons_text = " ".join(
            str(get_val(r, "description", "")) + " " + str(get_val(r, "category", ""))
            for r in rejection_reasons
        ).lower()

        insurer_deducted = fmath.extract(get_val(rejection, "total_deducted", 0.0))
        
        has_consumable_deduction_reason = any(
            kw in reasons_text
            for kw in ["consumable", "non-payable", "non payable", "non-medical", "annexure a", "schedule", "disallowed items"]
        )

        is_exclusively_other_reason = bool(rejection_reasons) and not has_consumable_deduction_reason and any(
            str(get_val(r, "category", "")).upper() in ["PROPORTIONATE_DEDUCTION", "ROOM_RENT", "COPAY", "DEDUCTIBLE", "WAITING_PERIOD", "PRE_EXISTING"]
            or any(kw in str(get_val(r, "description", "")).lower() for kw in ["room rent", "proportionate", "copay", "deductible", "waiting period", "moratorium", "pre-existing"])
            for r in rejection_reasons
        )

        # If surgery or ICU took place, List III items must not be deducted
        wrongful_list_iii_deduction = 0.0
        if is_surgery_or_icu and list_iii_billed > 0 and not is_exclusively_other_reason:
            if has_consumable_deduction_reason:
                wrongful_list_iii_deduction = min(list_iii_billed, insurer_deducted) if insurer_deducted > 0 else list_iii_billed
            elif not rejection_reasons and insurer_deducted >= list_iii_billed:
                wrongful_list_iii_deduction = min(list_iii_billed, insurer_deducted)

        if wrongful_list_iii_deduction > 0:
            item_summary = ", ".join(f"{d} (Rs. {a:.2f})" for d, a in list_iii_items_found[:5])
            finding = (
                f"TPA/Insurer unlawfully deducted Rs. {wrongful_list_iii_deduction:.2f} of List III surgical consumables. "
                f"Under IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List III), "
                f"these items are mandatory payable procedure/OT costs when surgery or ICU is performed. "
                f"Wrongfully deducted items: {item_summary}."
            )
            appeal_rec = (
                "Demand reimbursement of Rs. "
                f"{wrongful_list_iii_deduction:.2f} for List III surgical consumables "
                "under IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List III)."
            )
            return RuleVerdict(
                status="FAIL",
                rule_name="Non-Payable Items Rule",
                rule_description="Validates deductions against IRDAI Annexure A non-payable schedule.",
                confidence=1.0,
                finding=finding,
                legal_track="TRACK_A_ARITHMETIC_BREACH",
                monetary_impact=wrongful_list_iii_deduction,
                expected_admissible_amount=wrongful_list_iii_deduction,
                regulatory_citation="IRDAI Guidelines on Standardization in Health Insurance (Annexure A, List III)",
                appeal_recommendation=appeal_rec
            )

        # Otherwise, if only List I items were deducted or no wrongful deduction occurred
        finding = (
            "Non-payable item deductions comply with IRDAI Standardization Guidelines (Annexure A). "
            f"List I non-medical items (Rs. {list_i_billed:.2f}) are legitimately non-payable."
        )
        return RuleVerdict(
            status="PASS",
            rule_name="Non-Payable Items Rule",
            rule_description="Validates deductions against IRDAI Annexure A non-payable schedule.",
            confidence=1.0,
            finding=finding,
            legal_track="TRACK_C_VALID_DEDUCTION",
            monetary_impact=0.0,
            regulatory_citation="IRDAI Guidelines on Standardization in Health Insurance (Annexure A)",
            appeal_recommendation=None
        )

    except Exception as e:
        return RuleVerdict(
            status="SKIPPED",
            rule_name="Non-Payable Items Rule",
            rule_description="Validates deductions against IRDAI Annexure A non-payable schedule.",
            confidence=1.0,
            finding=f"Error evaluating non-payable items rule: {str(e)}"
        )
