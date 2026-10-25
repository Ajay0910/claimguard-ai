import re
from decimal import Decimal, InvalidOperation
from typing import Any


_FIELD_LABELS = {
    "total_amount": ("grand total", "net total", "total due", "amount due", "amount payable", "total bill", "bill total", "total amount", "gross total", "billed amount", "total gross bill", "total gross", "gross bill", "gross bill amount", "net invoice total", "net invoice total payable"),
    "subtotal": ("subtotal", "sub total", "total gross bill", "gross total", "total bill", "total gross", "gross bill", "gross bill amount", "sub-total"),
    "sum_insured": ("sum insured", "insured amount", "coverage amount", "cover amount", "effective coverage", "total coverage", "coverage", "base sum insured", "total sum insured"),
    "room_rent_limit_per_day": ("room rent", "room rental", "rent limit", "room limit", "room entitlement", "single private"),
    "copay_percentage": ("copay", "co pay", "co payment"),
    "deductible": ("deductible", "policy excess"),
    "total_claimed": ("total claimed", "claimed amount", "amount claimed", "claim amount", "claimed sum", "claimed", "total claim billed", "total billed", "claim billed", "billed"),
    "total_approved": ("total approved", "approved amount", "amount approved", "settled amount", "approved an amount", "approved", "admissible claim", "sanctioned and paid", "total approved / paid", "approved / paid", "approved/paid", "paid"),
    "approved_amount": ("approved amount", "amount approved", "settled amount", "approved an amount", "approved", "admissible claim", "sanctioned and paid", "total approved / paid", "approved / paid", "approved/paid", "paid"),
    "total_deducted": ("total deducted", "deducted amount", "total deduction", "disallowed", "disallowance", "deducted", "total disallowance", "total disallowed / deducted", "disallowed / deducted", "disallowed/deducted"),
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _financial_provenance(data: Any, document_type: str) -> list[tuple[str, Any]]:
    fields = {
        "HOSPITAL_BILL": ("total_amount", "subtotal"),
        "INSURANCE_POLICY": ("sum_insured", "room_rent_limit_per_day", "copay_percentage", "deductible"),
        "REJECTION_LETTER": ("total_claimed", "total_approved", "approved_amount", "total_deducted"),
    }
    found = []
    for name in fields.get(document_type, ()):
        value = getattr(data, name, None)
        if value is not None:
            found.append((name, value))
    if document_type == "HOSPITAL_BILL":
        for index, item in enumerate(getattr(data, "line_items", []) or []):
            for name in ("amount", "unit_rate"):
                value = getattr(item, name, None)
                if value is not None:
                    found.append((f"line_items[{index}].{name}", value))
    elif document_type == "INSURANCE_POLICY":
        rule = getattr(data, "proportionate_deduction_rule", None)
        if rule:
            for name in ("threshold_value", "policy_clause", "source_text"):
                value = getattr(rule, name, None)
                if value is not None:
                    found.append((f"proportionate_deduction_rule.{name}", value))
        for index, limit in enumerate(getattr(data, "sub_limits", []) or []):
            for name in ("max_amount", "max_percentage", "description"):
                value = getattr(limit, name, None)
                if value is not None:
                    found.append((f"sub_limits[{index}].{name}", value))
        for index, waiting in enumerate(getattr(data, "waiting_periods", []) or []):
            for name in ("category", "duration_days"):
                value = getattr(waiting, name, None)
                if value is not None:
                    found.append((f"waiting_periods[{index}].{name}", value))
            for condition_index, value in enumerate(getattr(waiting, "applicable_conditions", []) or []):
                found.append((f"waiting_periods[{index}].applicable_conditions[{condition_index}]", value))
        for name in ("deduction_order_clause",):
            value = getattr(data, name, None)
            if value is not None:
                found.append((name, value))
    elif document_type == "REJECTION_LETTER":
        for index, reason in enumerate(getattr(data, "rejection_reasons", []) or []):
            for name in ("description", "details", "clause_cited"):
                value = getattr(reason, name, None)
                if value is not None:
                    found.append((f"rejection_reasons[{index}].{name}", value))
    return found


def _numeric_tokens(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for token in re.findall(r"(?<![\w])(?:₹|Rs\.?\s*)?\(?-?\d[\d,]*(?:\.\d+)?\)?%?(?!\w)", text, flags=re.IGNORECASE):
        cleaned = re.sub(r"^(?:₹|rs\.?\s*)", "", token, flags=re.IGNORECASE)
        cleaned = cleaned.replace(",", "").replace("%", "").replace("(", "-").replace(")", "").strip()
        try:
            values.add(Decimal(cleaned))
        except InvalidOperation:
            continue
    return values


def validate_and_record_financial_evidence(data: Any, document: Any, ocr_text: str | list[str], ledger: Any) -> list[str]:
    """Validate financial source snippets and record them against the uploaded file identity."""
    issues = []
    pages = ocr_text if isinstance(ocr_text, list) else [ocr_text]
    for field_name, provenance in _financial_provenance(data, document.document_type):
        value = getattr(provenance, "value", None)
        confidence = getattr(provenance, "extraction_confidence", 0.0)
        page = getattr(provenance, "page", None)
        source_text = getattr(provenance, "source_text", None)
        if not source_text:
            issues.append(f"MISSING_SOURCE_TEXT:{field_name}")
            continue
        if not isinstance(page, (int, str)) or not str(page).isdigit() or int(page) < 1:
            issues.append(f"MISSING_SOURCE_PAGE:{field_name}")
            continue
        if not isinstance(confidence, (int, float)) or confidence < 0.8:
            issues.append(f"LOW_FIELD_CONFIDENCE:{field_name}")
            continue
        page_index = int(page) - 1
        page_text = pages[page_index] if 0 <= page_index < len(pages) else ""
        snippet = _normalize_text(source_text)
        label_markers = _FIELD_LABELS.get(field_name)
        if label_markers and not any(_normalize_text(label) in snippet for label in label_markers):
            issues.append(f"SOURCE_FIELD_NOT_VERIFIED:{field_name}")
            continue
        source_numbers = _numeric_tokens(str(source_text))
        page_numbers = _numeric_tokens(page_text)
        try:
            extracted_number = Decimal(str(value).replace(",", "")) if isinstance(value, (int, float, Decimal)) else None
        except (InvalidOperation, TypeError, ValueError):
            extracted_number = None

        is_config_or_clause = any(field_name.startswith(p) for p in ("waiting_periods", "proportionate_deduction_rule", "sub_limits", "rejection_reasons", "deduction_order_clause"))
        if is_config_or_clause:
            value_is_in_source = True
            value_is_on_page = True
            snippet_verified = True
        elif extracted_number is None and isinstance(value, str):
            value_is_in_source = _normalize_text(value) in snippet
            value_is_on_page = _normalize_text(value) in _normalize_text(page_text)
        elif (extracted_number == Decimal("0") or extracted_number == 0) and any(w in snippet for w in ("nil", "zero", "none", "nocapping", "nosublimit", "singleprivate")):
            value_is_in_source = True
            value_is_on_page = any(w in _normalize_text(page_text) for w in ("nil", "zero", "none", "nocapping", "nosublimit", "singleprivate"))
        else:
            value_is_in_source = extracted_number is not None and extracted_number in source_numbers
            value_is_on_page = extracted_number is not None and extracted_number in page_numbers

        norm_page = _normalize_text(page_text)
        snippet_verified = (snippet in norm_page) or is_config_or_clause
        if not snippet_verified and not is_config_or_clause:
            if label_markers and value_is_on_page:
                snippet_verified = any(_normalize_text(lbl) in norm_page for lbl in label_markers)
            elif extracted_number is not None and value_is_on_page:
                meaningful_words = [w for w in re.findall(r"[a-zA-Z]{3,}", str(source_text).lower()) if w not in ("amount", "rate", "total", "item", "charges")]
                snippet_verified = bool(meaningful_words) and any(_normalize_text(w) in norm_page for w in meaningful_words)

        if (
            not snippet
            or not page_text
            or not snippet_verified
            or not value_is_in_source
            or not value_is_on_page
        ):
            issues.append(f"SOURCE_TEXT_NOT_VERIFIED:{field_name}")
            continue

        # File identity is system-owned; never trust identifiers generated by the model.
        provenance.source_document_id = document.id
        provenance.source_document_type = document.document_type
        provenance.source_hash = document.document_hash
        if hasattr(ledger, "record_extraction"):
            ledger.record_extraction(
                document_id=document.id,
                document_hash=document.document_hash or "",
                page_number=int(page),
                source_text=source_text,
                extracted_value=value,
                confidence=float(confidence),
            )
    return issues
