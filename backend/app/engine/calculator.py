"""
Deterministic Financial Mathematics Engine with Calculation Lineage Preservation.
Provides fixed-point Decimal arithmetic (paise precision), operand provenance tracking,
formula capture, source document aggregation, and EvidenceLedger integration.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import uuid
from pydantic_core import core_schema

from ..schemas.provenance import Provenance, Transformation


class SafeDecimal(Decimal):
    """
    A robust subclass of Decimal that supports seamless bidirectional arithmetic
    and comparison with float, int, str, and Provenance instances without raising
    standard library TypeError: 'unsupported operand type(s) for *: decimal.Decimal and float'.
    Fully integrated with Pydantic v2 core schema.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, core_schema.decimal_schema()
        )

    @classmethod
    def _coerce(cls, other: Any) -> Any:
        if hasattr(other, "value"):
            other = other.value
        if isinstance(other, float):
            return Decimal(str(other))
        if isinstance(other, (int, Decimal)):
            return other
        if isinstance(other, str):
            cleaned = (
                other.strip()
                .replace(",", "")
                .replace("₹", "")
                .replace("Rs.", "")
                .replace("Rs", "")
                .strip()
            )
            return Decimal(cleaned)
        return other

    def __new__(cls, value: Any = "0", context: Any = None) -> "SafeDecimal":
        coerced = cls._coerce(value)
        return super().__new__(cls, coerced, context)

    def __add__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__add__(self._coerce(other)))

    def __radd__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__radd__(self._coerce(other)))

    def __sub__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__sub__(self._coerce(other)))

    def __rsub__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rsub__(self._coerce(other)))

    def __mul__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__mul__(self._coerce(other)))

    def __rmul__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rmul__(self._coerce(other)))

    def __truediv__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__truediv__(self._coerce(other)))

    def __rtruediv__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rtruediv__(self._coerce(other)))

    def __floordiv__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__floordiv__(self._coerce(other)))

    def __rfloordiv__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rfloordiv__(self._coerce(other)))

    def __mod__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__mod__(self._coerce(other)))

    def __rmod__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rmod__(self._coerce(other)))

    def __pow__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__pow__(self._coerce(other)))

    def __rpow__(self, other: Any) -> "SafeDecimal":
        return SafeDecimal(super().__rpow__(self._coerce(other)))

    def __neg__(self) -> "SafeDecimal":
        return SafeDecimal(super().__neg__())

    def __pos__(self) -> "SafeDecimal":
        return SafeDecimal(super().__pos__())

    def __abs__(self) -> "SafeDecimal":
        return SafeDecimal(super().__abs__())

    def __eq__(self, other: Any) -> bool:
        try:
            return super().__eq__(self._coerce(other))
        except Exception:
            return False

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __lt__(self, other: Any) -> bool:
        return super().__lt__(self._coerce(other))

    def __le__(self, other: Any) -> bool:
        return super().__le__(self._coerce(other))

    def __gt__(self, other: Any) -> bool:
        return super().__gt__(self._coerce(other))

    def __ge__(self, other: Any) -> bool:
        return super().__ge__(self._coerce(other))

    def round_currency(self, places: int = 2) -> "SafeDecimal":
        """Quantizes to paise (2 decimal places) using standard commercial ROUND_HALF_UP."""
        exp = Decimal("10") ** -places
        return SafeDecimal(self.quantize(exp, rounding=ROUND_HALF_UP))

    def to_float(self) -> float:
        """Explicit conversion to primitive float."""
        return float(self)

    def to_decimal(self) -> Decimal:
        """Returns standard Decimal instance."""
        return Decimal(self)


class FinancialMath:
    """
    Authoritative deterministic calculation engine for insurance adjudication.
    Guarantees exact Decimal arithmetic, lineage preservation, formula tracking,
    and automatic operand provenance aggregation.
    """

    PAISE = Decimal("0.01")
    DEFAULT_ROUNDING = ROUND_HALF_UP

    @classmethod
    def to_decimal(
        cls, obj: Any, default: Optional[Union[Decimal, float, str]] = None
    ) -> SafeDecimal:
        """
        Converts any operand (Provenance, SafeDecimal, Decimal, float, int, str)
        into a SafeDecimal instance.
        """
        if obj is None:
            if default is not None:
                return SafeDecimal(str(default))
            raise ValueError("Cannot convert None to Decimal without default")

        if isinstance(obj, SafeDecimal):
            return obj

        if isinstance(obj, Decimal):
            return SafeDecimal(obj)

        if isinstance(obj, Provenance):
            return cls.to_decimal(obj.value, default=default)

        if isinstance(obj, (int, bool)):
            return SafeDecimal(int(obj))

        if isinstance(obj, float):
            return SafeDecimal(str(obj))

        if isinstance(obj, str):
            cleaned = (
                obj.strip()
                .replace(",", "")
                .replace("₹", "")
                .replace("Rs.", "")
                .replace("Rs", "")
                .strip()
            )
            if not cleaned and default is not None:
                return SafeDecimal(str(default))
            try:
                return SafeDecimal(cleaned)
            except InvalidOperation as e:
                if default is not None:
                    return SafeDecimal(str(default))
                raise ValueError(f"Cannot convert string '{obj}' to Decimal: {e}")

        if hasattr(obj, "value"):
            return cls.to_decimal(obj.value, default=default)

        try:
            return SafeDecimal(str(obj))
        except (InvalidOperation, TypeError) as e:
            if default is not None:
                return SafeDecimal(str(default))
            raise ValueError(
                f"Cannot convert object of type {type(obj)} to Decimal: {e}"
            )

    @classmethod
    def to_float(cls, obj: Any, default: Optional[float] = None) -> float:
        """Converts any operand to primitive float."""
        if obj is None:
            return default if default is not None else 0.0
        return float(cls.to_decimal(obj, default=default))

    @classmethod
    def extract(cls, a: Any) -> SafeDecimal:
        """
        Extracts value as SafeDecimal. Drop-in replacement for old extract(),
        providing exact Decimal math while supporting legacy float expressions.
        """
        return cls.to_decimal(a, default=Decimal("0.0"))

    @classmethod
    def extract_float(cls, a: Any) -> float:
        """Extracts value strictly as primitive float."""
        return cls.to_float(a, default=0.0)

    @classmethod
    def quantize(
        cls, val: Any, places: int = 2, rounding=ROUND_HALF_UP
    ) -> SafeDecimal:
        """Quantizes value to specified decimal places."""
        dec = cls.to_decimal(val)
        exp = Decimal("10") ** -places
        return SafeDecimal(dec.quantize(exp, rounding=rounding))

    @classmethod
    def round_currency(cls, val: Any) -> SafeDecimal:
        """Rounds value to 2 decimal places (paise) with commercial rounding."""
        return cls.quantize(val, places=2, rounding=cls.DEFAULT_ROUNDING)

    # -------------------------------------------------------------------------
    # Provenance and Lineage Extraction Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _inspect_operand(
        cls, name: str, operand: Any
    ) -> Tuple[
        SafeDecimal,
        Dict[str, Any],
        Optional[str],
        Optional[str],
        float,
        List[Transformation],
    ]:
        """
        Extracts numeric value, audit metadata, document IDs, hashes,
        and prior transformation history from an operand.
        """
        val = cls.to_decimal(operand)
        is_prov = isinstance(operand, Provenance)

        prov_id = getattr(
            operand, "provenance_id", getattr(operand, "entry_id", None)
        )
        src_id = getattr(operand, "source_document_id", None)
        src_hash = getattr(operand, "source_hash", None)
        src_text = getattr(operand, "source_text", None)
        page = getattr(operand, "page", None)
        section = getattr(operand, "section", None)
        conf = float(getattr(operand, "extraction_confidence", 1.0))
        trans = list(getattr(operand, "transformations", []))

        info: Dict[str, Any] = {
            "name": name,
            "value": str(val),
            "type": "Provenance" if is_prov else type(operand).__name__,
        }
        if prov_id:
            info["provenance_id"] = str(prov_id)
        if src_id:
            info["source_document_id"] = str(src_id)
        if src_hash:
            info["source_hash"] = str(src_hash)
        if src_text:
            info["source_text"] = str(src_text)
        if page:
            info["page"] = str(page)
        if section:
            info["section"] = str(section)

        return val, info, src_id, src_hash, conf, trans

    @classmethod
    def _create_result_provenance(
        cls,
        op: str,
        formula: str,
        result_val: SafeDecimal,
        operands_dict: Dict[str, Dict[str, Any]],
        sources: List[Optional[str]],
        hashes: List[Optional[str]],
        transformations: List[Transformation],
        confidences: List[float],
        rule_id: Optional[str] = None,
    ) -> Provenance[SafeDecimal]:
        """
        Builds the result Provenance carrying aggregated document sources,
        cryptographic hashes, chained transformations, and calculation inputs.
        """
        # Deduplicate source document references
        unique_sources = set()
        for s in sources:
            if s and s not in (
                "Engine",
                "System/Mock",
                "None",
                "SYSTEM",
                "CALCULATED",
            ):
                for part in s.split(","):
                    cleaned = part.strip()
                    if cleaned:
                        unique_sources.add(cleaned)
        sorted_sources = sorted(list(unique_sources))
        source_doc_id = ", ".join(sorted_sources) if sorted_sources else "Engine"

        # Deduplicate source hashes
        unique_hashes = set()
        for h in hashes:
            if h and h not in ("SYSTEM_DETERMINISTIC", "None"):
                for part in h.split(","):
                    cleaned = part.strip()
                    if cleaned:
                        unique_hashes.add(cleaned)
        sorted_hashes = sorted(list(unique_hashes))
        source_hash = ", ".join(sorted_hashes) if sorted_hashes else None

        doc_type = (
            f"Derived ({source_doc_id})" if sorted_sources else "Calculated"
        )

        # Record this transformation step
        trans = Transformation(
            operation=op,
            timestamp=datetime.utcnow().isoformat(),
            details=f"{formula} = {result_val}",
        )
        all_trans = transformations + [trans]
        min_conf = min(confidences) if confidences else 1.0

        # Construct calculation inputs dictionary
        calc_inputs: Dict[str, Any] = {
            "operator": op,
            "formula": formula,
            "operands": operands_dict,
            "operand_ids": [
                info["provenance_id"]
                for info in operands_dict.values()
                if info.get("provenance_id")
            ],
        }
        if rule_id:
            calc_inputs["rule_id"] = rule_id

        prov = Provenance[SafeDecimal](
            value=result_val,
            normalized_value=result_val,
            source_document_id=source_doc_id,
            source_document_type=doc_type,
            source_hash=source_hash,
            context=f"Calculated via {op}: {formula}",
            extraction_confidence=min_conf,
            extraction_model="Deterministic FinancialMath",
            transformations=all_trans,
        )
        # Attach calculation metadata directly to the provenance instance
        prov.__dict__["calculation_inputs"] = calc_inputs
        prov.__dict__["formula"] = formula
        prov.__dict__["rule_id"] = rule_id

        return prov

    # -------------------------------------------------------------------------
    # Core Arithmetic Operations
    # -------------------------------------------------------------------------

    @classmethod
    def add(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
        quantize: bool = True,
    ) -> Provenance[SafeDecimal]:
        """Adds two values with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        res = val_a + val_b
        if quantize:
            res = cls.round_currency(res)

        f = formula or f"({val_a} + {val_b})"
        return cls._create_result_provenance(
            op="ADD",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def sub(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
        quantize: bool = True,
    ) -> Provenance[SafeDecimal]:
        """Subtracts b from a with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        res = val_a - val_b
        if quantize:
            res = cls.round_currency(res)

        f = formula or f"({val_a} - {val_b})"
        return cls._create_result_provenance(
            op="SUBTRACT",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def mul(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
        quantize: bool = True,
    ) -> Provenance[SafeDecimal]:
        """Multiplies a and b with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        res = val_a * val_b
        if quantize:
            res = cls.round_currency(res)

        f = formula or f"({val_a} * {val_b})"
        return cls._create_result_provenance(
            op="MULTIPLY",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def div(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
        quantize: bool = False,
    ) -> Provenance[SafeDecimal]:
        """Divides a by b. Defaults to quantize=False to maintain intermediate ratio precision."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        if val_b == Decimal("0"):
            raise ZeroDivisionError(
                f"Division by zero in FinancialMath: {val_a} / {val_b}"
            )

        res = val_a / val_b
        if quantize:
            res = cls.round_currency(res)

        f = formula or f"({val_a} / {val_b})"
        return cls._create_result_provenance(
            op="DIVIDE",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def sum(
        cls,
        items: Iterable[Any],
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        quantize: bool = True,
    ) -> Provenance[SafeDecimal]:
        """Sums an iterable of items with aggregated multi-operand provenance."""
        operands_dict: Dict[str, Dict[str, Any]] = {}
        sources: List[Optional[str]] = []
        hashes: List[Optional[str]] = []
        all_trans: List[Transformation] = []
        confidences: List[float] = []

        total = SafeDecimal("0.00")
        vals_str = []

        for i, item in enumerate(items):
            var_name = f"item_{i}"
            val, info, src, hsh, conf, trans = cls._inspect_operand(
                var_name, item
            )
            operands_dict[var_name] = info
            if src:
                sources.append(src)
            if hsh:
                hashes.append(hsh)
            all_trans.extend(trans)
            confidences.append(conf)
            total = total + val
            vals_str.append(str(val))

        if quantize:
            total = cls.round_currency(total)

        f = (
            formula
            or f"sum([{', '.join(vals_str[:5])}{'...' if len(vals_str) > 5 else ''}])"
        )
        return cls._create_result_provenance(
            op="SUM",
            formula=f,
            result_val=total,
            operands_dict=operands_dict,
            sources=sources,
            hashes=hashes,
            transformations=all_trans,
            confidences=confidences,
            rule_id=rule_id,
        )

    @classmethod
    def min(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
    ) -> Provenance[SafeDecimal]:
        """Returns min of two values while preserving provenance of both operands."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        res = min(val_a, val_b)
        f = formula or f"min({val_a}, {val_b})"
        return cls._create_result_provenance(
            op="MIN",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def max(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b",
    ) -> Provenance[SafeDecimal]:
        """Returns max of two values while preserving provenance of both operands."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(
            var_a, a
        )
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(
            var_b, b
        )

        res = max(val_a, val_b)
        f = formula or f"max({val_a}, {val_b})"
        return cls._create_result_provenance(
            op="MAX",
            formula=f,
            result_val=res,
            operands_dict={var_a: info_a, var_b: info_b},
            sources=[src_a, src_b],
            hashes=[hash_a, hash_b],
            transformations=trans_a + trans_b,
            confidences=[conf_a, conf_b],
            rule_id=rule_id,
        )

    @classmethod
    def calculate_percentage(
        cls,
        base_amount: Any,
        percentage_rate: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        quantize: bool = True,
    ) -> Provenance[SafeDecimal]:
        """Calculates (base_amount * percentage_rate / 100.0) with full lineage."""
        val_amt, info_amt, src_amt, hash_amt, conf_amt, trans_amt = (
            cls._inspect_operand("base_amount", base_amount)
        )
        val_pct, info_pct, src_pct, hash_pct, conf_pct, trans_pct = (
            cls._inspect_operand("percentage_rate", percentage_rate)
        )

        res = (val_amt * val_pct) / Decimal("100.0")
        if quantize:
            res = cls.round_currency(res)

        f = formula or f"({val_amt} * {val_pct}%)"
        return cls._create_result_provenance(
            op="PERCENTAGE",
            formula=f,
            result_val=res,
            operands_dict={"base_amount": info_amt, "percentage_rate": info_pct},
            sources=[src_amt, src_pct],
            hashes=[hash_amt, hash_pct],
            transformations=trans_amt + trans_pct,
            confidences=[conf_amt, conf_pct],
            rule_id=rule_id,
        )

    # -------------------------------------------------------------------------
    # Comparison Operators
    # -------------------------------------------------------------------------

    @classmethod
    def gt(cls, a: Any, b: Any) -> bool:
        """Exact Decimal greater-than comparison."""
        return cls.to_decimal(a) > cls.to_decimal(b)

    @classmethod
    def lt(cls, a: Any, b: Any) -> bool:
        """Exact Decimal less-than comparison."""
        return cls.to_decimal(a) < cls.to_decimal(b)

    @classmethod
    def ge(cls, a: Any, b: Any) -> bool:
        """Exact Decimal greater-or-equal comparison."""
        return cls.to_decimal(a) >= cls.to_decimal(b)

    @classmethod
    def le(cls, a: Any, b: Any) -> bool:
        """Exact Decimal less-or-equal comparison."""
        return cls.to_decimal(a) <= cls.to_decimal(b)

    @classmethod
    def eq(cls, a: Any, b: Any) -> bool:
        """Exact Decimal equality comparison."""
        return cls.to_decimal(a) == cls.to_decimal(b)

    # -------------------------------------------------------------------------
    # Evidence Ledger Bridge
    # -------------------------------------------------------------------------

    @classmethod
    def to_evidence_ledger_entry(
        cls,
        prov: Provenance,
        claim_id: str,
        rule_id: Optional[str] = None,
        formula: Optional[str] = None,
        section: Optional[str] = None,
    ) -> Any:
        """
        Converts a Provenance instance produced by FinancialMath into a validated
        EvidenceLedgerEntry from backend.app.schemas.evidence_ledger.
        """
        try:
            from ..schemas.evidence_ledger import EvidenceLedgerEntry

            return EvidenceLedgerEntry.from_provenance(
                prov=prov,
                claim_id=claim_id,
                rule_id=rule_id or getattr(prov, "rule_id", None),
                formula=formula or getattr(prov, "formula", None),
                calculation_inputs=getattr(prov, "calculation_inputs", None),
                final_output=prov.value,
                section=section,
            )
        except ImportError:
            # Fallback dictionary if evidence_ledger schema is not yet loaded
            return {
                "entry_id": getattr(
                    prov, "entry_id", getattr(prov, "provenance_id", str(uuid.uuid4()))
                ),
                "claim_id": claim_id,
                "document_id": prov.source_document_id,
                "document_hash": prov.source_hash or "SYSTEM_DETERMINISTIC",
                "extracted_value": prov.value,
                "normalized_value": prov.normalized_value or prov.value,
                "rule_id": rule_id or getattr(prov, "rule_id", None),
                "formula": formula or getattr(prov, "formula", None),
                "calculation_inputs": getattr(prov, "calculation_inputs", None),
                "final_output": prov.value,
                "confidence": prov.extraction_confidence,
                "created_at": prov.timestamp,
            }

    @classmethod
    def record_in_ledger(
        cls,
        ledger: Any,
        prov: Provenance,
        claim_id: str,
        rule_id: Optional[str] = None,
        formula: Optional[str] = None,
        section: Optional[str] = None,
    ) -> Any:
        """Appends the calculation provenance directly into an EvidenceLedger instance."""
        entry = cls.to_evidence_ledger_entry(
            prov=prov,
            claim_id=claim_id,
            rule_id=rule_id,
            formula=formula,
            section=section,
        )
        if hasattr(ledger, "add_entry"):
            ledger.add_entry(entry)
        elif isinstance(ledger, list):
            ledger.append(entry)
        return entry
