# Handoff Report — Explorer M1-3: Calculation Lineage Preservation in FinancialMath

- **Agent**: Explorer M1-3 (Mathematical Engine & Calculation Lineage Specialist)
- **Role**: Read-only Investigation & Concrete Architecture Design
- **Milestone**: M1 (Type System, Provenance & Evidence Ledger)
- **Target Feature**: F03 (Calculation Lineage Preservation in `FinancialMath`)
- **Authoritative Request**: `ORIGINAL_REQUEST.md` (Req R1: Deterministic Financial Reconciliation, Req R5: Ubiquitous Evidence Ledger)
- **Target Files**:
  - Primary: `backend/app/engine/calculator.py`
  - Integration: `backend/app/engine/adjudication_state.py`
  - Interfacing Schemas: `backend/app/schemas/provenance.py`, `backend/app/schemas/evidence_ledger.py`
- **Date**: 2026-09-27T06:55:00Z

---

## 1. Observation

Direct observations from examining the codebase, analyzing Python arithmetic behaviors, and executing verification scripts:

### Obs 1: Discarded Operand Lineage and Hardcoded Provenance in `calculator.py`
In `backend/app/engine/calculator.py` (lines 12–34):
```python
    @staticmethod
    def _merge_provenance(op: str, a: Any, b: Any, result: float) -> Provenance[float]:
        sources = []
        if isinstance(a, Provenance):
            sources.append(a.source_document_id)
        if isinstance(b, Provenance):
            sources.append(b.source_document_id)
            
        trans = Transformation(
            operation=op,
            timestamp=datetime.utcnow().isoformat(),
            details=f"Calculated {result} from operands"
        )
        
        return Provenance(
            value=result,
            source_document_id="Engine",
            source_document_type="Calculated",
            context=f"Result of {op}",
            extraction_model="Deterministic Engine",
            transformations=[trans]
        )
```
- **Lineage Discard**: At lines 14–18, `sources = []` is populated with `a.source_document_id` and `b.source_document_id`, but the list `sources` is **never assigned, passed, or referenced** anywhere else in the method. It goes out of scope and is completely garbage-collected.
- **Hardcoded Provenance Identity**: Line 28 hardcodes `source_document_id="Engine"` and line 29 sets `source_document_type="Calculated"`. If `a` originated from `Hospital Bill (BILL-101)` and `b` from `Insurance Policy (POL-202)`, this lineage is permanently severed.
- **Missing Calculation Inputs & Formula**: The returned `Provenance` contains zero record of input operand IDs, operand values, variable names, or the underlying mathematical expression (e.g. `policy_limit / actual_rate`).
- **Truncated Transformation Chain**: Prior transformations present in `a.transformations` and `b.transformations` are ignored. Only a single new `Transformation` is attached, obliterating the calculation DAG history.

### Obs 2: IEEE-754 Floating-Point Precision Issues in Financial Operations
In `backend/app/engine/calculator.py` lines 7–10 and 36–54:
```python
    @staticmethod
    def _extract_val(obj: Any) -> float:
        if isinstance(obj, Provenance):
            return float(obj.value)
        return float(obj)
```
- All operations (`add`, `sub`, `mul`, `div`) cast inputs directly to native 64-bit IEEE-754 `float`.
- In Indian healthcare insurance adjudication, currency must be exact to 2 decimal places (paise). Floating-point arithmetic introduces representation artifacts such as `0.1 + 0.2 = 0.30000000000000004` and `2843.50 * 0.15 = 426.52500000000003`.
- In multi-step adjudication (room rent excess -> proportionate deduction -> procedure sub-limits -> deductible -> co-pay -> sum insured cap), cumulative floating-point drift creates reconciliation mismatches at the Final Reconciliation Gate (`abs(expected_payable - insurer_payable) > 1.0`), falsely routing clean claims to `NEEDS_REVIEW` or `MISMATCH_DETECTED`.

### Obs 3: Python Incompatibility Between `Decimal` and `float` Arithmetic
When converting `FinancialMath` to use standard `decimal.Decimal`, Python's standard library enforces strict separation between `Decimal` and `float`:
- Comparison (`>`, `<`, `==`) between `Decimal` and `float` works (e.g. `Decimal('100') > 1.15` returns `True`).
- However, arithmetic operations (`+`, `-`, `*`, `/`) between `Decimal` and `float` raise an unrecoverable `TypeError`:
  ```
  TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'
  ```
- In existing business rules (such as `backend/app/rules/proportionate_deduction.py:50` and `backend/app/rules/copay_rule.py:39`):
  ```python
  trigger_threshold = policy_room_limit_f * 1.15
  deduction_percentage = 1.0 - (policy_room_limit_f / actual_room_rate_f)
  copay_amount = total_remaining * (copay_pct / 100.0)
  ```
  `1.15`, `1.0`, and `100.0` are native Python float literals.
- If `FinancialMath.extract` were to return a naive `Decimal`, executing `proportionate_deduction.py` triggers `TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'`. Because rules enclose execution in `try...except`, this exception causes the rule to silently fail and emit `RuleVerdict(status="SKIPPED", finding="Error evaluating rule: ...")`.

### Obs 4: Pydantic v2 Core Schema Requirement for Custom Types
When defining a subclass of `Decimal` (e.g. `SafeDecimal`), Pydantic v2 fails model generation during `Provenance[SafeDecimal]` schema creation:
```
pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'SafeDecimal'>.
Set arbitrary_types_allowed=True in the model_config to ignore this error or implement __get_pydantic_core_schema__ on your type to fully support it.
```
Any custom Decimal wrapper must implement `__get_pydantic_core_schema__` using `core_schema.no_info_after_validator_function(cls, core_schema.decimal_schema())` to guarantee transparent serialization and validation.

### Obs 5: `AdjudicationState` Reconciliation Behavior
In `backend/app/engine/adjudication_state.py` (lines 51–90):
- `LineItemState` and `FinancialAdjustment` currently store amounts as floats (`original_amount: float`, `remaining_balance: float`, `adjustment_amount: float`).
- `apply_deduction` does in-place subtraction: `self.line_items[code].remaining_balance -= take`.
- `verify_reconciliation()` performs:
  ```python
  return abs(original_total - (final_total + total_deducted)) < 0.01
  ```
  If `remaining_balance` is float and `take` is Decimal, `float -= Decimal` raises `TypeError`. If `SafeDecimal` implements reverse subtraction `__rsub__` and arithmetic dunders, this operation executes cleanly without errors and preserves exact paise reconciliation.

---

## 2. Logic Chain

1. **Premise 1 (Lineage Severing Root Cause)**:
   - Observation 1 demonstrates that `FinancialMath` deliberately discarded `sources` and hardcoded `source_document_id="Engine"`.
   - To satisfy Requirement R5 ("Ubiquitous Evidence Ledger"), every intermediate and final financial amount must carry the list of source document IDs, cryptographic document hashes, operand provenance IDs, and the exact formula applied.
   - Therefore, `FinancialMath` must inspect all operands, extract their `provenance_id` / `entry_id`, `source_document_id`, and `source_hash`, and persist them in `calculation_inputs`.

2. **Premise 2 (Exact Precision Requirement & Float Hazard)**:
   - Observation 2 demonstrates that float arithmetic introduces precision drift.
   - Requirement R1 requires deterministic financial reconciliation where `expected_payable - insurer_payable == disputed_amount` down to 0 paise.
   - Therefore, `FinancialMath` must perform all computations in fixed-point arithmetic (`decimal.Decimal`) rounded to 2 decimal places (paise) with `ROUND_HALF_UP`.

3. **Premise 3 (Seamless Interoperability via `SafeDecimal`)**:
   - Observation 3 shows that standard `Decimal` crashes with `TypeError` when combined with float literals (`* 1.15`, `- 1.0`, `/ 100.0`) present across existing rules and tests.
   - Observation 4 shows that Pydantic v2 requires `__get_pydantic_core_schema__` for custom Decimal subclasses.
   - Therefore, we create `SafeDecimal(Decimal)`, which:
     1. Implements `_coerce` on all arithmetic dunders (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`, etc.) to automatically coerce `float`, `int`, `str`, and `Provenance` operands to `Decimal`.
     2. Implements `__get_pydantic_core_schema__` delegating to `core_schema.decimal_schema()`.
     3. Provides helper methods `.round_currency(places=2)` and `.to_float()`.
   - This ensures that `FinancialMath.extract(val)` returns `SafeDecimal`, providing 100% backward compatibility with legacy float operations while executing with Decimal exactness.

4. **Premise 4 (Source Document and Transformation Aggregation)**:
   - When calculating `c = a - b`:
     - If `a` originates from `BILL-101` (hash `h1`) and `b` originates from `POL-202` (hash `h2`), the resulting `source_document_id` must aggregate both: `"BILL-101, POL-202"`.
     - In chained operations (`d = c * days`), document sources from `c` and `days` must be merged and deduplicated.
     - All prior `transformations` from `a` and `b` must be preserved, and the new operation step appended.

5. **Premise 5 (Evidence Ledger Schema Bridge)**:
   - Feature F02 (designed by Explorer M1-2) establishes `EvidenceLedgerEntry` and `EvidenceLedger`.
   - `FinancialMath` must provide direct factory bridges (`to_evidence_ledger_entry` and `record_in_ledger`) to convert any calculation output into a validated `EvidenceLedgerEntry` containing `calculation_inputs`, `formula`, and `final_output`.

---

## 3. Caveats

1. **Intermediate Ratio Precision**:
   - In division operations (e.g. `policy_limit / actual_rate` or `copay_percentage / 100`), quantizing intermediate ratios to 2 decimal places (e.g. `4000 / 6000 = 0.67`) introduces rounding bias.
   - **Design Rule**: `FinancialMath.div` defaults to `quantize=False`, preserving full Decimal precision (28 digits by default in Python's Decimal context) during ratio calculations, while `add`, `sub`, `mul`, `sum`, and `calculate_percentage` default to `quantize=True` (paise rounding).
2. **String Currency Parsing**:
   - Real-world extraction data frequently contains currency prefixes (`₹`, `Rs.`, `Rs`) and thousand separators (`,`).
   - `SafeDecimal._coerce` and `FinancialMath.to_decimal` must clean strings before conversion, stripping commas, whitespace, and currency symbols.
3. **Pydantic Model Updates**:
   - `AdjudicationState` line items and adjustments will support `Union[Decimal, float, SafeDecimal]` to prevent runtime attribute type errors.

---

## 4. Conclusion & Concrete Implementation Specifications

### 4.1 Primary Implementation: `backend/app/engine/calculator.py`

Replace the entire contents of `backend/app/engine/calculator.py` with the following production-grade implementation:

```python
"""
Deterministic Financial Mathematics Engine with Calculation Lineage Preservation.
Provides fixed-point Decimal arithmetic (paise precision), operand provenance tracking,
formula capture, source document aggregation, and EvidenceLedger integration.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime
from typing import Any, Optional, Dict, List, Tuple, Iterable, Union
import uuid
from pydantic_core import core_schema

from ..schemas.provenance import Provenance, Transformation


class SafeDecimal(Decimal):
    """
    A robust subclass of Decimal that supports seamless bidirectional arithmetic
    with float, int, str, and Provenance instances without raising standard library
    TypeError: 'unsupported operand type(s) for *: decimal.Decimal and float'.
    Fully integrated with Pydantic v2 core schema.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.decimal_schema()
        )

    @classmethod
    def _coerce(cls, other: Any) -> Any:
        if hasattr(other, 'value'):
            other = other.value
        if isinstance(other, float):
            return Decimal(str(other))
        if isinstance(other, (int, Decimal)):
            return other
        if isinstance(other, str):
            cleaned = other.strip().replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').strip()
            return Decimal(cleaned)
        return other

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

    def __neg__(self) -> "SafeDecimal":
        return SafeDecimal(super().__neg__())

    def __pos__(self) -> "SafeDecimal":
        return SafeDecimal(super().__pos__())

    def __abs__(self) -> "SafeDecimal":
        return SafeDecimal(super().__abs__())

    def round_currency(self, places: int = 2) -> "SafeDecimal":
        """Quantizes to paise (2 decimal places) using standard commercial ROUND_HALF_UP."""
        exp = Decimal('10') ** -places
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

    PAISE = Decimal('0.01')
    DEFAULT_ROUNDING = ROUND_HALF_UP

    @classmethod
    def to_decimal(cls, obj: Any, default: Optional[Union[Decimal, float, str]] = None) -> SafeDecimal:
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
            cleaned = obj.strip().replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').strip()
            if not cleaned and default is not None:
                return SafeDecimal(str(default))
            try:
                return SafeDecimal(cleaned)
            except InvalidOperation as e:
                if default is not None:
                    return SafeDecimal(str(default))
                raise ValueError(f"Cannot convert string '{obj}' to Decimal: {e}")

        if hasattr(obj, 'value'):
            return cls.to_decimal(obj.value, default=default)

        try:
            return SafeDecimal(str(obj))
        except (InvalidOperation, TypeError) as e:
            if default is not None:
                return SafeDecimal(str(default))
            raise ValueError(f"Cannot convert object of type {type(obj)} to Decimal: {e}")

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
        return cls.to_decimal(a, default=Decimal('0.0'))

    @classmethod
    def extract_float(cls, a: Any) -> float:
        """Extracts value strictly as primitive float."""
        return cls.to_float(a, default=0.0)

    @classmethod
    def quantize(cls, val: Any, places: int = 2, rounding=ROUND_HALF_UP) -> SafeDecimal:
        """Quantizes value to specified decimal places."""
        dec = cls.to_decimal(val)
        exp = Decimal('10') ** -places
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
        cls,
        name: str,
        operand: Any
    ) -> Tuple[SafeDecimal, Dict[str, Any], Optional[str], Optional[str], float, List[Transformation]]:
        """
        Extracts numeric value, audit metadata, document IDs, hashes,
        and prior transformation history from an operand.
        """
        val = cls.to_decimal(operand)
        is_prov = isinstance(operand, Provenance)

        prov_id = getattr(operand, 'provenance_id', getattr(operand, 'entry_id', None))
        src_id = getattr(operand, 'source_document_id', None)
        src_hash = getattr(operand, 'source_hash', None)
        src_text = getattr(operand, 'source_text', None)
        page = getattr(operand, 'page', None)
        section = getattr(operand, 'section', None)
        conf = float(getattr(operand, 'extraction_confidence', 1.0))
        trans = list(getattr(operand, 'transformations', []))

        info: Dict[str, Any] = {
            'name': name,
            'value': str(val),
            'type': 'Provenance' if is_prov else type(operand).__name__,
        }
        if prov_id:
            info['provenance_id'] = str(prov_id)
        if src_id:
            info['source_document_id'] = str(src_id)
        if src_hash:
            info['source_hash'] = str(src_hash)
        if src_text:
            info['source_text'] = str(src_text)
        if page:
            info['page'] = str(page)
        if section:
            info['section'] = str(section)

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
        rule_id: Optional[str] = None
    ) -> Provenance[SafeDecimal]:
        """
        Builds the result Provenance carrying aggregated document sources,
        cryptographic hashes, chained transformations, and calculation inputs.
        """
        # Deduplicate source document references
        unique_sources = set()
        for s in sources:
            if s and s not in ('Engine', 'System/Mock', 'None', 'SYSTEM', 'CALCULATED'):
                for part in s.split(','):
                    cleaned = part.strip()
                    if cleaned:
                        unique_sources.add(cleaned)
        sorted_sources = sorted(list(unique_sources))
        source_doc_id = ", ".join(sorted_sources) if sorted_sources else "Engine"

        # Deduplicate source hashes
        unique_hashes = set()
        for h in hashes:
            if h and h not in ('SYSTEM_DETERMINISTIC', 'None'):
                for part in h.split(','):
                    cleaned = part.strip()
                    if cleaned:
                        unique_hashes.add(cleaned)
        sorted_hashes = sorted(list(unique_hashes))
        source_hash = ", ".join(sorted_hashes) if sorted_hashes else None

        doc_type = f"Derived ({source_doc_id})" if sorted_sources else "Calculated"

        # Record this transformation step
        trans = Transformation(
            operation=op,
            timestamp=datetime.utcnow().isoformat(),
            details=f"{formula} = {result_val}"
        )
        all_trans = transformations + [trans]
        min_conf = min(confidences) if confidences else 1.0

        # Construct calculation inputs dictionary
        calc_inputs: Dict[str, Any] = {
            'operator': op,
            'formula': formula,
            'operands': operands_dict,
            'operand_ids': [
                info['provenance_id']
                for info in operands_dict.values()
                if info.get('provenance_id')
            ]
        }
        if rule_id:
            calc_inputs['rule_id'] = rule_id

        prov = Provenance[SafeDecimal](
            value=result_val,
            normalized_value=result_val,
            source_document_id=source_doc_id,
            source_document_type=doc_type,
            source_hash=source_hash,
            context=f"Calculated via {op}: {formula}",
            extraction_confidence=min_conf,
            extraction_model="Deterministic FinancialMath",
            transformations=all_trans
        )
        # Attach calculation metadata directly to the provenance instance
        prov.__dict__['calculation_inputs'] = calc_inputs
        prov.__dict__['formula'] = formula
        prov.__dict__['rule_id'] = rule_id

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
        quantize: bool = True
    ) -> Provenance[SafeDecimal]:
        """Adds two values with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

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
            rule_id=rule_id
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
        quantize: bool = True
    ) -> Provenance[SafeDecimal]:
        """Subtracts b from a with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

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
            rule_id=rule_id
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
        quantize: bool = True
    ) -> Provenance[SafeDecimal]:
        """Multiplies a and b with operand lineage tracking and Decimal exactness."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

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
            rule_id=rule_id
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
        quantize: bool = False
    ) -> Provenance[SafeDecimal]:
        """Divides a by b. Defaults to quantize=False to maintain intermediate ratio precision."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

        if val_b == Decimal('0'):
            raise ZeroDivisionError(f"Division by zero in FinancialMath: {val_a} / {val_b}")

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
            rule_id=rule_id
        )

    @classmethod
    def sum(
        cls,
        items: Iterable[Any],
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        quantize: bool = True
    ) -> Provenance[SafeDecimal]:
        """Sums an iterable of items with aggregated multi-operand provenance."""
        operands_dict: Dict[str, Dict[str, Any]] = {}
        sources: List[Optional[str]] = []
        hashes: List[Optional[str]] = []
        all_trans: List[Transformation] = []
        confidences: List[float] = []

        total = SafeDecimal('0.00')
        vals_str = []

        for i, item in enumerate(items):
            var_name = f"item_{i}"
            val, info, src, hsh, conf, trans = cls._inspect_operand(var_name, item)
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

        f = formula or f"sum([{', '.join(vals_str[:5])}{'...' if len(vals_str) > 5 else ''}])"
        return cls._create_result_provenance(
            op="SUM",
            formula=f,
            result_val=total,
            operands_dict=operands_dict,
            sources=sources,
            hashes=hashes,
            transformations=all_trans,
            confidences=confidences,
            rule_id=rule_id
        )

    @classmethod
    def min(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b"
    ) -> Provenance[SafeDecimal]:
        """Returns min of two values while preserving provenance of both operands."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

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
            rule_id=rule_id
        )

    @classmethod
    def max(
        cls,
        a: Any,
        b: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        var_a: str = "a",
        var_b: str = "b"
    ) -> Provenance[SafeDecimal]:
        """Returns max of two values while preserving provenance of both operands."""
        val_a, info_a, src_a, hash_a, conf_a, trans_a = cls._inspect_operand(var_a, a)
        val_b, info_b, src_b, hash_b, conf_b, trans_b = cls._inspect_operand(var_b, b)

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
            rule_id=rule_id
        )

    @classmethod
    def calculate_percentage(
        cls,
        base_amount: Any,
        percentage_rate: Any,
        formula: Optional[str] = None,
        rule_id: Optional[str] = None,
        quantize: bool = True
    ) -> Provenance[SafeDecimal]:
        """Calculates (base_amount * percentage_rate / 100.0) with full lineage."""
        val_amt, info_amt, src_amt, hash_amt, conf_amt, trans_amt = cls._inspect_operand("base_amount", base_amount)
        val_pct, info_pct, src_pct, hash_pct, conf_pct, trans_pct = cls._inspect_operand("percentage_rate", percentage_rate)

        res = (val_amt * val_pct) / Decimal('100.0')
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
            rule_id=rule_id
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
        section: Optional[str] = None
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
                rule_id=rule_id or getattr(prov, 'rule_id', None),
                formula=formula or getattr(prov, 'formula', None),
                calculation_inputs=getattr(prov, 'calculation_inputs', None),
                final_output=prov.value,
                section=section
            )
        except ImportError:
            # Fallback dictionary if evidence_ledger schema is not yet loaded
            return {
                "entry_id": getattr(prov, 'entry_id', getattr(prov, 'provenance_id', str(uuid.uuid4()))),
                "claim_id": claim_id,
                "document_id": prov.source_document_id,
                "document_hash": prov.source_hash or "SYSTEM_DETERMINISTIC",
                "extracted_value": prov.value,
                "normalized_value": prov.normalized_value or prov.value,
                "rule_id": rule_id or getattr(prov, 'rule_id', None),
                "formula": formula or getattr(prov, 'formula', None),
                "calculation_inputs": getattr(prov, 'calculation_inputs', None),
                "final_output": prov.value,
                "confidence": prov.extraction_confidence,
                "created_at": prov.timestamp
            }

    @classmethod
    def record_in_ledger(
        cls,
        ledger: Any,
        prov: Provenance,
        claim_id: str,
        rule_id: Optional[str] = None,
        formula: Optional[str] = None,
        section: Optional[str] = None
    ) -> Any:
        """Appends the calculation provenance directly into an EvidenceLedger instance."""
        entry = cls.to_evidence_ledger_entry(
            prov=prov,
            claim_id=claim_id,
            rule_id=rule_id,
            formula=formula,
            section=section
        )
        if hasattr(ledger, 'add_entry'):
            ledger.add_entry(entry)
        elif isinstance(ledger, list):
            ledger.append(entry)
        return entry
```

---

### 4.2 Integration Specification: `backend/app/engine/adjudication_state.py`

Update `backend/app/engine/adjudication_state.py` to seamlessly accept `SafeDecimal`, `Decimal`, and `float` while maintaining exact paise reconciliation:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Union
from decimal import Decimal
from ..schemas.provenance import Provenance
from .calculator import FinancialMath, SafeDecimal
import uuid

class FinancialAdjustment(BaseModel):
    model_config = ConfigDict(extra='ignore')
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    policy_clause: Optional[str] = None
    affected_line_items: List[str]
    original_amount: Union[SafeDecimal, Decimal, float]
    adjustment_amount: Union[SafeDecimal, Decimal, float]
    remaining_amount: Union[SafeDecimal, Decimal, float]
    calculation_formula: str
    provenance: List[Provenance] = []
    dependency_rules: List[str] = []
    execution_order: int

class LineItemState(BaseModel):
    model_config = ConfigDict(extra='ignore')
    item_code: str
    category: str
    original_amount: Union[SafeDecimal, Decimal, float]
    remaining_balance: Union[SafeDecimal, Decimal, float]
    applied_adjustments: List[str] = []

class AdjudicationState(BaseModel):
    model_config = ConfigDict(extra='ignore')
    claim_id: str
    line_items: Dict[str, LineItemState] = {}
    adjustments: List[FinancialAdjustment] = []
    ledger: Optional[Any] = None  # Optional EvidenceLedger instance
    
    def get_balance(self, item_code: str) -> SafeDecimal:
        if item_code in self.line_items:
            return FinancialMath.to_decimal(self.line_items[item_code].remaining_balance)
        return SafeDecimal('0.00')

    def apply_deduction(
        self, 
        rule_id: str, 
        target_item_codes: List[str], 
        deduction_amount: Union[SafeDecimal, Decimal, float, Provenance], 
        formula: str,
        policy_clause: str = None,
        prov: List[Provenance] = None,
        dependencies: List[str] = None
    ) -> Optional[FinancialAdjustment]:
        # Extract SafeDecimal deduction amount
        dec_deduction = FinancialMath.to_decimal(deduction_amount)
        
        # Automatically wrap provenance if deduction_amount was a Provenance instance
        if isinstance(deduction_amount, Provenance) and not prov:
            prov = [deduction_amount]

        total_available = sum(self.get_balance(code) for code in target_item_codes)
        actual_deduction = min(dec_deduction, total_available)
        
        if actual_deduction <= SafeDecimal('0.00'):
            return None

        adj = FinancialAdjustment(
            rule_id=rule_id,
            policy_clause=policy_clause,
            affected_line_items=target_item_codes,
            original_amount=total_available,
            adjustment_amount=actual_deduction,
            remaining_amount=total_available - actual_deduction,
            calculation_formula=formula,
            provenance=prov or [],
            dependency_rules=dependencies or [],
            execution_order=len(self.adjustments) + 1
        )
        self.adjustments.append(adj)
        
        # Deduct from balances in exact paise
        remaining_to_deduct = actual_deduction
        for code in target_item_codes:
            if remaining_to_deduct <= SafeDecimal('0.00'):
                break
            bal = self.get_balance(code)
            if bal > SafeDecimal('0.00'):
                take = min(bal, remaining_to_deduct)
                self.line_items[code].remaining_balance = bal - take
                self.line_items[code].applied_adjustments.append(adj.adjustment_id)
                remaining_to_deduct = remaining_to_deduct - take

        # If an EvidenceLedger is attached, record adjustment directly
        if self.ledger and hasattr(self.ledger, 'record_calculation'):
            self.ledger.record_calculation(
                rule_id=rule_id,
                formula=formula,
                calculation_inputs={
                    "target_items": target_item_codes,
                    "requested_deduction": str(dec_deduction),
                    "total_available": str(total_available),
                    "actual_deduction": str(actual_deduction)
                },
                final_output=str(actual_deduction)
            )

        return adj

    def verify_reconciliation(self) -> bool:
        original_total = sum(FinancialMath.to_decimal(item.original_amount) for item in self.line_items.values())
        final_total = sum(FinancialMath.to_decimal(item.remaining_balance) for item in self.line_items.values())
        total_deducted = sum(FinancialMath.to_decimal(adj.adjustment_amount) for adj in self.adjustments)
        
        return abs(original_total - (final_total + total_deducted)) < SafeDecimal('0.01')
```

---

## 5. Verification Method

To independently verify the implementation, execute the following commands in order:

### Verification Command 1: Unit & Rule Test Suite
Run the test suite against the new mathematical engine:
```powershell
.\venv\Scripts\python.exe -m pytest backend/tests/test_rules.py
```
**Expected Result**:
- `test_proportionate_deduction_within_limit`: PASS
- `test_proportionate_deduction_mismatch`: PASS (validates exact monetary impact of 14,000.0)
- `test_proportionate_deduction_correct_deduction`: PASS
- No `TypeError: unsupported operand type(s)` between `Decimal` and `float`.

### Verification Command 2: Full End-to-End Pipeline & Reconciliation Verification
Execute an inline verification script validating the multi-rule adjudication chain and zero-paise reconciliation:
```powershell
.\venv\Scripts\python.exe -c "
import sys
sys.path.insert(0, 'backend')
from app.engine.calculator import FinancialMath, SafeDecimal
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
from app.engine.adjudication_state import AdjudicationState, LineItemState
from app.rules.proportionate_deduction import check_proportionate_deduction
from app.rules.copay_rule import check_copay
from app.rules.deductible_rule import check_deductible

bill = HospitalBill(
    hospital_name='Apollo Hospital', patient_name='John Doe', admission_date='2025-01-01', discharge_date='2025-01-02',
    line_items=[
        BillLineItem(item_code='R1', description='Room Charges', category='ROOM', quantity=1, unit_rate=6000, amount=6000, is_room_linked=True),
        BillLineItem(item_code='S1', description='Surgical OT', category='OT', quantity=1, unit_rate=10000, amount=10000, is_room_linked=False)
    ], subtotal=16000, net_payable=16000
)
policy = InsurancePolicy(
    policy_number='POL-001', insurer_name='Star Health', policyholder_name='John Doe', policy_start_date='2020-01-01', policy_end_date='2021-01-01',
    sum_insured=500000, room_rent_limit_per_day=4000, copay_percentage=10.0, deductible=1000.0
)
rejection = RejectionLetter(
    reference_number='REF-1', insurer_name='Star Health', policyholder_name='John Doe', policy_number='POL-001', claim_number='CLM-1', claim_date='2025-01-01',
    total_claimed=16000, total_approved=0, total_deducted=16000, settlement_type='FULL_REJECTION'
)

state = AdjudicationState(claim_id='claim_1')
state.line_items['R1'] = LineItemState(item_code='R1', category='ROOM', original_amount=6000.0, remaining_balance=6000.0)
state.line_items['S1'] = LineItemState(item_code='S1', category='OT', original_amount=10000.0, remaining_balance=10000.0)

v_prop = check_proportionate_deduction(bill, policy, rejection, state=state)
assert v_prop.status == 'FAIL'
assert state.get_balance('R1') == SafeDecimal('4000.00')

v_ded = check_deductible(bill, policy, rejection, state=state)
assert v_ded.status == 'PASS'
assert state.get_balance('R1') == SafeDecimal('3000.00')

v_copay = check_copay(bill, policy, rejection, state=state)
assert v_copay.status == 'PASS'
assert state.get_balance('R1') == SafeDecimal('1700.00')
assert state.get_balance('S1') == SafeDecimal('10000.00')

assert state.verify_reconciliation() == True
print('Verification SUCCESS: Adjudication reconciliation verified exact to the paise!')
"
```
**Expected Output**:
```
Verification SUCCESS: Adjudication reconciliation verified exact to the paise!
```

### Verification Command 3: Chained Provenance & Lineage Retention Check
Execute verification script testing operand provenance retention, formula string recording, and multi-document source aggregation:
```powershell
.\venv\Scripts\python.exe -c "
import sys
sys.path.insert(0, 'backend')
from app.engine.calculator import FinancialMath, SafeDecimal
from app.schemas.provenance import Provenance

p_rate = Provenance(value=6000.0, source_document_id='BILL-101', source_hash='hash_bill_1', source_text='Room: 6000')
p_limit = Provenance(value=4000.0, source_document_id='POL-202', source_hash='hash_pol_2', source_text='Limit: 4000')
p_days = Provenance(value=3, source_document_id='BILL-101', source_hash='hash_bill_1', source_text='Stay: 3')

excess = FinancialMath.sub(p_rate, p_limit, formula='actual_rate - limit', var_a='actual_rate', var_b='limit')
assert excess.value == SafeDecimal('2000.00')
assert excess.source_document_id == 'BILL-101, POL-202'
assert len(excess.transformations) == 1

total_excess = FinancialMath.mul(excess, p_days, formula='excess_per_day * stay_days', var_a='excess_per_day', var_b='stay_days')
assert total_excess.value == SafeDecimal('6000.00')
assert total_excess.source_document_id == 'BILL-101, POL-202'
assert len(total_excess.transformations) == 2
assert 'excess_per_day' in total_excess.__dict__['calculation_inputs']['operands']
assert 'stay_days' in total_excess.__dict__['calculation_inputs']['operands']
print('Verification SUCCESS: Multi-hop provenance lineage and formula capture verified!')
"
```
**Expected Output**:
```
Verification SUCCESS: Multi-hop provenance lineage and formula capture verified!
```

### Invalidation Conditions
The implementation is invalidated if:
1. `FinancialMath` arithmetic between `SafeDecimal` and a Python native `float` raises `TypeError`.
2. Chained calculations discard source document IDs or replace them unconditionally with `"Engine"`.
3. Input operand values, variable names, or formula expressions are absent from `calculation_inputs`.
4. `AdjudicationState.verify_reconciliation()` returns `False` on valid zero-drift multi-step deductions.
