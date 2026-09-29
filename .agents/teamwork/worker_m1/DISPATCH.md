# Dispatch to Worker M1: Type System, Provenance & Evidence Ledger (F01-F04)

- **Role**: Core Systems & Data Architecture Worker
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\worker_m1\
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- **Project Scope**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md
- **Explorer Findings**:
  - `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_1\handoff.md` (F01: Provenance Dunders)
  - `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_2\handoff.md` (F02 & F04: Evidence Ledger & Hashing)
  - `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3\handoff.md` (F03: FinancialMath Lineage & SafeDecimal)

## Exclusive File Ownership
You have exclusive write access to:
1. `backend/app/schemas/provenance.py`
2. `backend/app/schemas/evidence_ledger.py` (create new)
3. `backend/app/models/claim.py`
4. `backend/app/utils/file_handler.py`
5. `backend/app/api/upload.py`
6. `backend/app/api/portal.py`
7. `backend/app/engine/calculator.py`
8. `backend/tests/test_evidence_ledger.py` (create new)

## Tasks
1. Implement F01 in `backend/app/schemas/provenance.py`:
   - Implement equality (`__eq__`, `__ne__`) against both other `Provenance` and primitive values.
   - Implement ordering (`__lt__`, `__le__`, `__gt__`, `__ge__`).
   - Implement numeric conversions (`__float__`, `__int__`, `__bool__`, `__abs__`, `__round__`).
   - Implement representations (`__str__`, `__repr__`, `__format__`).
   - Implement hashing (`__hash__`).
   - Implement arithmetic operators (`__add__`, `__radd__`, `__sub__`, `__rsub__`, `__mul__`, `__rmul__`, `__truediv__`, `__rtruediv__`, `__floordiv__`, `__mod__`, `__neg__`, `__pos__`) with safe cross-type numeric handling.
   - Implement attribute delegation (`__getattr__`) without intercepting Pydantic internals.
   - Implement container operations (`__contains__`, `__len__`, `__getitem__`).
   - Fix `wrap_primitive` validator to prevent double-wrapping.
2. Implement F02 in `backend/app/schemas/evidence_ledger.py`:
   - Define `EvidenceLedgerEntry` (all 16 fields, bounding-box validation, Pydantic v2 config).
   - Define `EvidenceLedger` collection model with indexing and lookup methods.
3. Implement F02 & F04 in `backend/app/models/claim.py`:
   - Add `document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)` to `Document`.
   - Add `EvidenceLedgerRecord` table mapping entries to database.
4. Implement F04 in `backend/app/utils/file_handler.py`, `backend/app/api/upload.py`, and `backend/app/api/portal.py`:
   - Streaming SHA-256 calculation during file save.
   - Store `document_hash` in `Document` record in upload endpoints.
5. Implement F03 in `backend/app/engine/calculator.py`:
   - Implement `SafeDecimal` with cross-type arithmetic and Pydantic v2 core schema.
   - Refactor `FinancialMath`: preserve input operand IDs in `calculation_inputs`, store formulas, aggregate source IDs, and bridge to `EvidenceLedgerEntry`.
6. Add unit tests in `backend/tests/test_evidence_ledger.py` covering all implemented features.
7. Run the test suite:
   - Run `pytest backend/tests/test_evidence_ledger.py`
   - Run `pytest backend/tests/` to verify that existing test failures drop from 32 to ~11 (with 211+ tests passing).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Deliverables
- Write `handoff.md` in your working directory containing:
  - Exact changes made and files modified.
  - Test commands run and exact test output.
  - Verification that F01-F04 are fully implemented and verified.
- When done, call `send_message` to parent orchestrator.

## 2026-09-27T06:56:00Z
You are Worker M1 (Core Systems & Data Architecture Worker).
Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\worker_m1\
Project root: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

Read:
1. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
2. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md
3. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\worker_m1\DISPATCH.md
4. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_1\handoff.md
5. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_2\handoff.md
6. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3\handoff.md

Your task is to implement Features F01, F02, F03, F04 for Milestone 1:
1. Implement F01 in backend/app/schemas/provenance.py (dunder operators for Provenance[T], primitive comparison, cross-type arithmetic, wrap_primitive fix).
2. Implement F02 in backend/app/schemas/evidence_ledger.py (EvidenceLedgerEntry, EvidenceLedger).
3. Implement F02 & F04 in backend/app/models/claim.py (Document.document_hash, EvidenceLedgerRecord table).
4. Implement F04 in backend/app/utils/file_handler.py, backend/app/api/upload.py, backend/app/api/portal.py (SHA-256 calculation and storage on upload).
5. Implement F03 in backend/app/engine/calculator.py (SafeDecimal, FinancialMath operand preservation and EvidenceLedgerEntry bridge).
6. Create test file backend/tests/test_evidence_ledger.py to verify all F01-F04 functionality.
7. Run tests:
   pytest backend/tests/test_evidence_ledger.py
   pytest backend/tests/
   Verify that test failures drop from 32 down to ~11 (with 211+ tests passing).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your report in handoff.md in your working directory and notify the parent orchestrator via send_message when complete.

