# Handoff Report: Feature F01 — Provenance[T] Operability & Dunder Design

- **Author**: Explorer M1-1 (Type System & Schema Specialist)
- **Role**: Read-only Investigation & Concrete Architecture Design
- **Milestone**: M1
- **Project Root**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`
- **Target File**: `backend/app/schemas/provenance.py`

---

## 1. Observation

Direct observations from examining the codebase, running test commands, and reproducing errors:

### Obs 1: Current Implementation of `Provenance[T]`
In `backend/app/schemas/provenance.py` (lines 12–41):
```python
class Provenance(BaseModel, Generic[T]):
    value: T = Field(description="The exact extracted value")
    normalized_value: Optional[T] = Field(default=None, description="The normalized version of the value (e.g. for dates or names)")
    source_document_id: str = Field(default="System/Mock", description="The ID of the document")
    source_document_type: str = Field(default="System/Mock", description="The name or type of the document where this value was found (e.g., 'Hospital Bill', 'Policy')")
    source_hash: Optional[str] = None
    page: Optional[str] = None
    section: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    source_text: Optional[str] = None
    context: str = Field(default="Generated", description="The precise page number and original text snippet that proves this value")
    extraction_confidence: float = 1.0
    extraction_model: str = "System"
    model_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    transformations: list[Transformation] = []

    @model_validator(mode='before')
    @classmethod
    def wrap_primitive(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        # If it's a primitive passed directly (e.g. in tests), wrap it
        return {
            "value": data,
            "source_document_id": "System/Mock",
            "source_document_type": "System/Mock",
            "context": "Generated"
        }
```
`Provenance` inherits directly from `pydantic.BaseModel` and declares zero custom dunder methods.

### Obs 2: Test Suite Baseline & Failure Count
Running `.\venv\Scripts\python.exe -m pytest backend/tests/` yields:
```
======================= 32 failed, 190 passed in 1.53s =======================
```
Out of 32 total failures across the test suite, **21 failures** are directly attributable to missing dunder methods and string delegation on `Provenance[T]`.

### Obs 3: Verbatim Equality Assertion Failures
1. `backend/tests/e2e/test_tier1_features.py:749` (`test_tier1_f11_evidence_line_item_provenance_retention`):
   ```
   > assert item.item_code == "MED-TR-10"
   E AssertionError: assert Provenance[str](value='MED-TR-10', ...) == 'MED-TR-10'
   ```
2. `backend/tests/e2e/test_tier1_features.py:219` (`test_tier1_f03_document_integrity_arithmetic_verified_model_validator`):
   ```
   > assert bill.subtotal == 1500.0
   E AssertionError: assert Provenance[float](value=1500.0, ...) == 1500.0
   ```
3. `backend/tests/e2e/test_tier4_real_world.py:286` (`test_tier4_scenario_s5_high_value_cardiac_surgery_copay_sublimit`):
   ```
   > assert bill.total_amount == 415000.0
   E AssertionError: assert Provenance[float](value=415000.0, ...) == 415000.0
   ```

### Obs 4: Verbatim Arithmetic TypeErrors
1. `backend/tests/e2e/test_tier1_features.py:445` (`test_tier1_f07_copay_ten_percent_calculation`):
   ```
   > expected_patient_share = claim_amount * (policy.copay_percentage / 100.0)
   E TypeError: unsupported operand type(s) for /: 'Provenance[float]' and 'float'
   ```
2. `backend/tests/e2e/test_tier1_features.py:468` (`test_tier1_f07_deductible_below_threshold`):
   ```
   > admissible_after_deductible = max(0.0, claim_amount - policy.deductible)
   E TypeError: unsupported operand type(s) for -: 'float' and 'Provenance[float]'
   ```
   (Fails specifically because `__rsub__` is missing on `policy.deductible`).
3. `backend/tests/e2e/test_tier1_features.py:477` (`test_tier1_f07_sublimit_procedure_enforcement`):
   ```
   > excess = max(0.0, bill_amount - applicable_limit)
   E TypeError: unsupported operand type(s) for -: 'float' and 'Provenance[float]'
   ```
4. `backend/tests/e2e/test_tier3_pairwise.py:99` (`test_tier3_pairwise_03_copay_and_icu_shielding`):
   ```
   > admissible = bill.total_amount - prop_verdict.correct_calculation
   E TypeError: unsupported operand type(s) for -: 'Provenance[float]' and 'float'
   ```
5. `backend/tests/e2e/test_tier2_boundaries.py:403, 410, 417, 426, 438`:
   All 5 boundary tests fail with `TypeError: unsupported operand type(s)` for `/` and `-`.

### Obs 5: Verbatim String Delegation AttributeError
In `backend/app/rules/authenticity_check.py:10` during `test_tier3_pairwise_15_authenticity_check_failed_and_clean_gates`:
```python
def mock_verify_hospital(hospital_name: str) -> bool:
    name_lower = hospital_name.lower()
```
Throws:
```
E AttributeError: 'Provenance[str]' object has no attribute 'lower'
```
Because `bill.hospital_name` is typed as `Provenance[str]`, passing it to functions expecting string methods fails.

### Obs 6: `wrap_primitive` Vulnerability to Double-Wrapping
In `backend/app/schemas/provenance.py` lines 32–33:
```python
if isinstance(data, dict):
    return data
return {"value": data, ...}
```
If an already instantiated `Provenance` object is passed into `wrap_primitive` (e.g., re-validating or passing to another field), `isinstance(data, dict)` evaluates to `False`, nesting `Provenance(value=Provenance(value=...))`.

---

## 2. Logic Chain

1. **Root Cause Identification**:
   - `Provenance[T]` wraps extracted fields to preserve audit lineage (`source_document_id`, `page`, `bounding_box`, `transformations`).
   - However, in business rules (`app/rules/`), utility modules, and test assertions (`backend/tests/`), fields like `bill.total_amount`, `item.item_code`, and `policy.copay_percentage` are used as if they are plain Python primitives (`float`, `str`, `int`).
   - In Python, special dunder methods (`__eq__`, `__add__`, `__rsub__`, `__getattr__`, etc.) are looked up directly on the class dictionary. Because `Provenance[T]` inherits `BaseModel` without custom dunders, Python falls back to default `BaseModel` behaviors: `BaseModel.__eq__` (which returns `False` when compared against primitives) and raises `TypeError` for arithmetic and `AttributeError` for string methods.

2. **Dunder Method Requirements Analysis**:
   - **Equality (`__eq__`, `__ne__`)**: Must compare `self.value` against `other.value` if `isinstance(other, Provenance)`, or against `other` directly. This solves Obs 3 (`bill.total_amount == 415000.0`, `item.item_code == "MED-TR-10"`).
   - **Ordering (`__lt__`, `__le__`, `__gt__`, `__ge__`)**: Must compare `self.value` against `other` (handling `Provenance` vs primitive and vice versa). When `self.value is None` or `other is None`, return `NotImplemented`.
   - **Numeric Conversion (`__float__`, `__int__`, `__bool__`, `__abs__`, `__round__`, `__floor__`, `__ceil__`, `__trunc__`)**:
     - `__float__` allows `float(prov)` and enables Pydantic to validate `Provenance` into `float` model fields.
     - `__int__` allows integer casting.
     - `__bool__` ensures `bool(Provenance(value=False))` evaluates to `False` (critical for boolean fields like `covers_maternity` and `covers_mental_health`).
     - `__abs__` and `__round__` enable `abs(prov - target)` in arithmetic balance checks.
   - **String Representation & Formatting (`__str__`, `__repr__`, `__format__`)**:
     - `__str__` returns `str(self.value)`.
     - `__repr__` returns `f"Provenance({self.value!r})"`.
     - `__format__` delegates to `format(self.value, format_spec)`, allowing f-strings like `f"₹{amount:.2f}"` without crashing with `unsupported format string`.
   - **Hashing (`__hash__`)**:
     - In Python, overriding `__eq__` without `__hash__` marks instances unhashable.
     - Defining `__hash__` to return `hash(self.value)` maintains the invariant `a == b => hash(a) == hash(b)` and allows `Provenance` instances in `set` and `dict` keys.
   - **Arithmetic Operators (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__floordiv__`, `__mod__`, `__pow__` & reverse counterparts)**:
     - Must unpack `other.value` if `isinstance(other, Provenance)`.
     - Must implement both standard and reverse dunders (`__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`, etc.) to support primitive-first operations like `claim_amount - policy.deductible` (Obs 4.2) and `sum(items)` (which begins with `0 + item[0]`).
     - Must gracefully handle `Decimal` and `float` mixed arithmetic via coercion (`_coerce`) to prevent standard library `TypeError: unsupported operand type(s) for +: 'float' and 'decimal.Decimal'` when `FinancialMath` (F03) introduces `Decimal`.
   - **Attribute & String Delegation (`__getattr__`)**:
     - When an attribute/method is called that does not exist on `Provenance` (such as `.lower()`, `.upper()`, `.strip()`, `.startswith()`, `.isoformat()`, `.year`), `__getattr__` delegates the call to `self.value`.
     - Must explicitly guard `if name.startswith("_"): raise AttributeError(...)` so Pydantic v2 internal attributes (`__pydantic_validator__`, `__pydantic_fields_set__`, `__copy__`, `__deepcopy__`, etc.) are never intercepted.
   - **Container Operators (`__contains__`, `__len__`, `__getitem__`)**:
     - `__contains__` allows `"Apollo" in bill.hospital_name`.
     - `__len__` allows `len(bill.hospital_name)`.
     - `__getitem__` allows slicing like `item.item_code[0:3]`.
   - **Wrap Primitive Fix**:
     - Update condition to `if isinstance(data, (dict, Provenance)): return data` to eliminate double-wrapping (Obs 6).

3. **Empirical Validation**:
   - Applying this dunder design via memory patch and running `pytest backend/tests/` transformed the test suite from **32 failed, 190 passed** to **11 failed, 211 passed**.
   - Exactly 21 failing tests were resolved purely by fixing `Provenance[T]`.
   - The remaining 11 failures are known downstream milestones:
     - M2: Identity Gate (`test_tier1_f02`, `test_tier1_f04`, `test_tier1_f13`, `test_tier3_pairwise_10`)
     - M3: Proportionate Deduction Rule (`test_tier1_f05`, `test_tier1_f06`, `test_tier2_f05`, `test_tier3_pairwise_09`, `test_tier4_scenario_s1`)

---

## 3. Caveats

1. **In-place Mutation (`__iadd__`, etc.)**:
   - In-place dunders (`__iadd__`, `__isub__`) are intentionally not defined. In Pydantic models, mutating field values in-place can bypass validation. Normal reassignment (`x = x + y`) triggers `__add__` and reassignment, which works seamlessly.
2. **Provenance Preservation vs Primitive Return in Arithmetic**:
   - Ad-hoc Python arithmetic (`a + b`) returns the resulting computed numeric value (`float`, `int`, or `Decimal`).
   - Lineage-tracked calculations with full transformation history and provenance chaining belong to `FinancialMath` (`app/engine/calculator.py`, Feature F03) and `EvidenceLedgerEntry` (Feature F02). This ensures ad-hoc operations (e.g. `policy.copay_percentage / 100.0` or loop counters) don't accumulate unwanted Pydantic wrapper overhead.
3. **Pydantic v2 Generic Typing**:
   - `Provenance[T]` retains `BaseModel, Generic[T]`. Serialization (`model_dump()`, `model_dump_json()`) and schema generation (`model_json_schema()`) remain 100% compliant with Pydantic v2.

---

## 4. Conclusion & Concrete Implementation Specification

The concrete fix for Feature F01 requires updating `backend/app/schemas/provenance.py` with the complete specification below.

### Target File: `backend/app/schemas/provenance.py`

```python
import math
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class Transformation(BaseModel):
    operation: str
    timestamp: str
    details: str


class Provenance(BaseModel, Generic[T]):
    value: T = Field(description="The exact extracted value")
    normalized_value: Optional[T] = Field(
        default=None,
        description="The normalized version of the value (e.g. for dates or names)",
    )
    source_document_id: str = Field(
        default="System/Mock", description="The ID of the document"
    )
    source_document_type: str = Field(
        default="System/Mock",
        description="The name or type of the document where this value was found (e.g., 'Hospital Bill', 'Policy')",
    )
    source_hash: Optional[str] = None
    page: Optional[str] = None
    section: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    source_text: Optional[str] = None
    context: str = Field(
        default="Generated",
        description="The precise page number and original text snippet that proves this value",
    )
    extraction_confidence: float = 1.0
    extraction_model: str = "System"
    model_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    transformations: List[Transformation] = []

    @model_validator(mode="before")
    @classmethod
    def wrap_primitive(cls, data: Any) -> Any:
        if isinstance(data, (dict, Provenance)):
            return data
        # If it's a primitive passed directly (e.g. in tests), wrap it
        return {
            "value": data,
            "source_document_id": "System/Mock",
            "source_document_type": "System/Mock",
            "context": "Generated",
        }

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @staticmethod
    def _extract_val(other: Any) -> Any:
        if isinstance(other, Provenance):
            return other.value
        return other

    @staticmethod
    def _coerce(a: Any, b: Any) -> tuple[Any, Any]:
        """Coerce mixed float and Decimal operands to Decimal to avoid standard library TypeError."""
        if isinstance(a, Decimal) and isinstance(b, float):
            b = Decimal(str(b))
        elif isinstance(a, float) and isinstance(b, Decimal):
            a = Decimal(str(a))
        return a, b

    # =========================================================================
    # Equality and Comparison Dunders
    # =========================================================================

    def __eq__(self, other: Any) -> bool:
        other_val = self._extract_val(other)
        return self.value == other_val

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __lt__(self, other: Any) -> bool:
        other_val = self._extract_val(other)
        if self.value is None or other_val is None:
            return NotImplemented
        a, b = self._coerce(self.value, other_val)
        return a < b

    def __le__(self, other: Any) -> bool:
        other_val = self._extract_val(other)
        if self.value is None or other_val is None:
            return NotImplemented
        a, b = self._coerce(self.value, other_val)
        return a <= b

    def __gt__(self, other: Any) -> bool:
        other_val = self._extract_val(other)
        if self.value is None or other_val is None:
            return NotImplemented
        a, b = self._coerce(self.value, other_val)
        return a > b

    def __ge__(self, other: Any) -> bool:
        other_val = self._extract_val(other)
        if self.value is None or other_val is None:
            return NotImplemented
        a, b = self._coerce(self.value, other_val)
        return a >= b

    # =========================================================================
    # Type Conversion Dunders
    # =========================================================================

    def __float__(self) -> float:
        return float(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __abs__(self) -> Any:
        return abs(self.value)

    def __round__(self, ndigits: Optional[int] = None) -> Any:
        if ndigits is None:
            return round(self.value)
        return round(self.value, ndigits)

    def __floor__(self) -> int:
        return math.floor(self.value)

    def __ceil__(self) -> int:
        return math.ceil(self.value)

    def __trunc__(self) -> int:
        return math.trunc(self.value)

    # =========================================================================
    # String and Representation Dunders
    # =========================================================================

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Provenance({self.value!r})"

    def __format__(self, format_spec: str) -> str:
        if self.value is None:
            return format("", format_spec)
        return format(self.value, format_spec)

    def __hash__(self) -> int:
        try:
            return hash(self.value)
        except TypeError:
            return hash(id(self))

    # =========================================================================
    # Arithmetic Dunders (Binary & Reverse)
    # =========================================================================

    def __add__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a + b

    def __radd__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a + b

    def __sub__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a - b

    def __rsub__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a - b

    def __mul__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a * b

    def __rmul__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a * b

    def __truediv__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a / b

    def __rtruediv__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a / b

    def __floordiv__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a // b

    def __rfloordiv__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a // b

    def __mod__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a % b

    def __rmod__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a % b

    def __pow__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(self.value, other_val)
        return a**b

    def __rpow__(self, other: Any) -> Any:
        other_val = self._extract_val(other)
        a, b = self._coerce(other_val, self.value)
        return a**b

    def __neg__(self) -> Any:
        return -self.value

    def __pos__(self) -> Any:
        return +self.value

    # =========================================================================
    # Container & Method Delegation
    # =========================================================================

    def __contains__(self, item: Any) -> bool:
        if self.value is None:
            return False
        if hasattr(self.value, "__contains__"):
            return item in self.value
        return False

    def __len__(self) -> int:
        if self.value is not None and hasattr(self.value, "__len__"):
            return len(self.value)
        raise TypeError(
            f"object of type '{type(self).__name__}' with value type '{type(self.value).__name__}' has no len()"
        )

    def __getitem__(self, item: Any) -> Any:
        if self.value is not None and hasattr(self.value, "__getitem__"):
            return self.value[item]
        raise TypeError(f"'{type(self).__name__}' object is not subscriptable")

    def __getattr__(self, name: str) -> Any:
        # Never intercept private/internal pydantic attributes
        if name.startswith("_"):
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
        val = self.__dict__.get("value")
        if val is not None and hasattr(val, name):
            return getattr(val, name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
```

---

## 5. Verification Method

To independently verify the design:

### 1. Isolated Unit Verification Command
Run the isolated Feature tests in Tier 1:
```powershell
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -m pytest backend/tests/e2e/test_tier1_features.py -k "f07 or f11 or f03" -v
```
**Expected Outcome**: 15 passed, 0 failed.

### 2. Boundary Verification Command
Run the boundary arithmetic tests in Tier 2:
```powershell
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -m pytest backend/tests/e2e/test_tier2_boundaries.py -k "f07" -v
```
**Expected Outcome**: 5 passed, 0 failed.

### 3. Pairwise & Real World Tests
Run the pairwise and real-world scenarios:
```powershell
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -m pytest backend/tests/e2e/test_tier3_pairwise.py -k "03 or 13 or 14 or 15" -v
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -m pytest backend/tests/e2e/test_tier4_real_world.py -k "s5" -v
```
**Expected Outcome**: All passed.

### 4. Pydantic v2 Serialization Invariance
Run the Pydantic test:
```powershell
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -c "
from app.schemas.hospital_bill import HospitalBill
from tests.e2e.conftest import make_bill

bill = make_bill()
dump = bill.model_dump()
json_str = bill.model_dump_json()
restored = HospitalBill.model_validate_json(json_str)
assert restored.total_amount == bill.total_amount
assert restored.arithmetic_verified is True
print('Pydantic v2 verification passed!')
"
```
**Expected Outcome**: Prints `Pydantic v2 verification passed!` with exit code 0.

### 5. Invalidation Conditions
The design is invalidated if:
- `Provenance(value=10.0) == 10.0` evaluates to `False`.
- `100.0 - Provenance(value=25.0)` raises `TypeError`.
- `Provenance(value='Apollo').lower()` raises `AttributeError`.
- `bill.model_dump()` fails with schema or serialization error.
