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
    transformations: List[Transformation] = Field(default_factory=list)

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
        if isinstance(self.value, Decimal) and isinstance(other_val, float):
            return self.value == Decimal(str(other_val))
        if isinstance(self.value, float) and isinstance(other_val, Decimal):
            return Decimal(str(self.value)) == other_val
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
