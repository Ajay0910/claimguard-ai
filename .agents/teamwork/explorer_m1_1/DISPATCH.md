# Dispatch to Explorer M1-1: Provenance Type & Dunder Operators

- **Role**: Type System & Schema Specialist
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_1\
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- **Project Scope**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md

## Objective
Design the concrete fix for Feature F01 (`Provenance[T]` in `backend/app/schemas/provenance.py`):
1. Analyze all dunder methods needed on `Provenance[T]`:
   - Equality (`__eq__`, `__ne__`): must support comparison against both another `Provenance` instance and raw primitive values (`str`, `int`, `float`, `Decimal`).
   - Ordering (`__lt__`, `__le__`, `__gt__`, `__ge__`).
   - Number conversion (`__float__`, `__int__`, `__abs__`, `__round__`).
   - String representation (`__str__`, `__repr__`).
   - Hashing (`__hash__`).
   - Arithmetic operators (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__floordiv__`, `__mod__`, `__pow__`, and their reverse `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`).
2. Verify how Pydantic v2 handles generic models with custom dunders and custom model validators.
3. Check all failing tests in `backend/tests/` that fail due to `Provenance` comparisons or arithmetic.
4. Provide the exact implementation design in your `handoff.md` for the worker to implement.
