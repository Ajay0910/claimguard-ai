# Project: ClaimGuard Adjudication Architecture Rebuild

## Architecture
ClaimGuard is a multi-tier, deterministic health insurance claim adjudication and fraud detection platform.
Core principle: **AI reads, rules verify, evidence proves, humans handle uncertainty.**
Generic heuristics and ML probability scores must NEVER override deterministic financial calculations.

### System Layers
1. **Tier 0 Safety Gates (Blocking Gates)**:
   - Identity Gate (Bill, Policy, Rejection cross-document match, insured members).
   - Document Integrity & Arithmetic Gate (Strict line-item arithmetic, grand total invariants).
   - Clinical Firewall Gate (Medical necessity, active line of treatment, experimental care).
   If any Tier 0 gate fails, adjudication is `BLOCKED` with zero financial impact.
2. **Document Ingestion & Cross-Verification Layer**:
   - Multi-page PDF parsing (native digital text extraction + multi-page rasterization).
   - Multi-modal / multi-model cross-verification with calibrated confidence.
   - Fail-closed error handling (no synthetic dummy 0.0 fallbacks).
3. **Evidence Ledger & Provenance Layer**:
   - Standalone `EvidenceLedgerEntry` tracking every variable from source bounding box to final statutory payout.
   - Transparent `Provenance[T]` type with seamless primitive equality and arithmetic dunder support.
   - `FinancialMath` with persistent operand provenance IDs and formula lineage.
4. **Policy-Rule Adjudication Engine**:
   - Strict applicability, semantic DAG ordering:
     1. Non-Medical / Excluded Expenses Rule (Schedule I).
     2. Room Rent Capping & Proportionate Deduction Rule (>1.15 threshold, protected expense shielding).
     3. Procedure Sub-Limit Rule (Cataract, Hernia, Joint replacement, etc.).
     4. Policy Deductible Rule.
     5. Co-Payment Rule.
     6. Sum Insured Cap Rule.
   - Moratorium (60-month continuous coverage, portability credits) & Waiting Period Rules (36-month IRDAI PED cap).
   - Statutory compliance (Mental Health Parity Act 2017).
5. **Deterministic Financial Reconciliation Gate**:
   - Expected Payable = sum of remaining item balances.
   - Disputed Amount = Expected Payable - Insurer Payable.
   - Strict invariant: Expected Payable - Insurer Payable == Disputed Amount; otherwise `NEEDS_REVIEW`.
   - Never runs on blocked claims.
6. **Frontend & Portal UI Synchronization**:
   - Eliminates mock data fallbacks, fake violation cards, and hardcoded patient metadata.
   - Synchronizes UI state directly with backend authoritative enum status.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| F01 | Provenance Type Operability | Enable `__eq__`, arithmetic operators, and string delegation on `Provenance[T]` | M1 | Survey 1 & 3 |
| F02 | Standalone Evidence Ledger Schema | Create `EvidenceLedgerEntry` with doc hash, page, bounding box, rule, formula, inputs | M1 | Survey 2 |
| F03 | Calculation Lineage Preservation | Update `FinancialMath` to preserve operand IDs, formula, and use `Decimal` | M1 | Survey 1 & 2 |
| F04 | Document SHA-256 Hashing | Compute and store cryptographic hash on document upload | M1 | Survey 2 |
| F05 | Multi-Page PDF Ingestion | Ingest and parse all pages of hospital bills and policies instead of truncating at page 0 | M2 | Survey 2 & 3 |
| F06 | Non-Destructive Preprocessing | Preserve native digital text layer and high-res rendering without destructive binarization | M2 | Survey 2 |
| F07 | Fail-Closed Extraction Fallback | Replace dummy 0.0 fallback models with explicit `EXTRACTION_FAILED` errors | M2 | Survey 2 |
| F08 | Tier 0 Document Arithmetic Gate | Promote Document Integrity to Tier 0 gatekeeper with `BLOCKED` status on failure | M2 | Survey 2 |
| F09 | Strict Identity Gate & Insured Members | Eliminate fail-open logic, verify patient against `policy.insured_members` | M2 | Survey 3 |
| F10 | Procedure Sub-Limit Rule | Implement sub-limits for specific surgeries/procedures (Cataract, Hernia, etc.) | M3 | Survey 1 |
| F11 | Non-Medical Expenses Rule | Implement exclusion of Schedule I consumables and administrative charges | M3 | Survey 1 |
| F12 | Sum Insured Cap Rule | Implement cap ensuring expected payable never exceeds policy sum insured | M3 | Survey 1 |
| F13 | Proportionate Deduction Fixes | Exclude consultation fees, fix >1.15 threshold, prevent double deduction, sync state | M3 | Survey 1 |
| F14 | Moratorium Calendar Math & Phrases | Calculate exact continuous coverage timelines, detect disguised Clause 4.1 rejections | M3 | Survey 1 |
| F15 | Waiting Period Rule Alignment | Align PED waiting period with IRDAI 2024 (36-month cap) and exact date math | M3 | Survey 1 |
| F16 | Eliminate Heuristic Overturn Overrides | Remove arbitrary additive percentages and 70% probability overrides in appeal evaluator | M4 | Survey 1 |
| F17 | Reconcile Financial Gate & State Sync | Prevent execution on blocked claims, fix legitimate rejections, eliminate double-counting | M4 | Survey 1 |
| F18 | Invariant Financial Equation | Enforce: Expected Payable - Insurer Payable == Disputed Amount, else `NEEDS_REVIEW` | M4 | Survey 1 |
| F19 | Frontend Mock Leak Elimination | Remove `mockAnalysisResult` fallback in `api.js` and fix premature `'COMPLETED'` status | M5 | Survey 3 |
| F20 | Frontend Data Integrity | Remove fake violation cards in `FinancialDelta.jsx` and hardcoded patient header in `Analysis.jsx` | M5 | Survey 3 |
| F21 | Portal Enum Synchronization | Align portal tracking states (`CLAIM_SUPPORTED`, `MISMATCH_DETECTED`) with backend | M5 | Survey 3 |
| F22 | Golden UAT Suite & Full Verification | Connect synthetic PDF corpus, verify 100% test pass across Tiers 1-4 | M5 / E2E Track | Survey 3 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | Type System, Provenance & Evidence Ledger | F01, F02, F03, F04 | none | PLANNED |
| M2 | Extraction Reliability & Fail-Closed Gates | F05, F06, F07, F08, F09 | M1 | PLANNED |
| M3 | Strict Policy-Rule Engine & Missing Rules | F10, F11, F12, F13, F14, F15 | M1 | PLANNED |
| M4 | Deterministic Financial Reconciliation | F16, F17, F18 | M2, M3 | PLANNED |
| M5 | Frontend Consistency & E2E Test Suite | F19, F20, F21, F22 | M4 | PLANNED |
| E2E | E2E Testing Track (Parallel) | Test Infra, Golden UAT Harness, Tiers 1-4 | M1 | PLANNED |

---

## Interface Contracts

### M1 ↔ M2, M3, M4 (Evidence Ledger & Provenance)
- `Provenance[T]`:
  - `Provenance.value`: underlying value of type `T`.
  - Implements `__eq__(other)`: compares with `other.value` if `isinstance(other, Provenance)`, else directly with `other`.
  - Implements `__float__`, `__int__`, `__str__`, `__repr__`, `__hash__`.
  - Implements arithmetic dunders: `__add__`, `__sub__`, `__mul__`, `__truediv__`, `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`.
- `EvidenceLedgerEntry`:
  ```python
  class EvidenceLedgerEntry(BaseModel):
      entry_id: str
      claim_id: str
      document_id: str
      document_hash: str
      page_number: int
      bounding_box: Optional[List[float]] = None
      section: Optional[str] = None
      source_text: str
      extracted_value: Any
      normalized_value: Any
      rule_id: Optional[str] = None
      formula: Optional[str] = None
      calculation_inputs: Optional[Dict[str, Any]] = None
      final_output: Optional[Any] = None
      confidence: float
      created_at: str
  ```
- `FinancialMath`:
  - Uses `decimal.Decimal` internally.
  - Merges operand provenance IDs into `calculation_inputs` preserving document traceability.

### M2 ↔ M3, M4 (Extraction & Gatekeepers)
- Extraction outputs:
  - Valid `HospitalBill`, `InsurancePolicy`, `RejectionLetter` models with validated arithmetic.
  - On failure: raise `ExtractionError` or return `extraction_status="FAILED"`.
- Tier 0 Gates:
  - If any Tier 0 gate fails: `overall_status="BLOCKED"`, `RuleVerdict(status="BLOCKED")`, downstream rule execution halted.

### M3 ↔ M4 (Rule Engine & Financial Reconciliation)
- Adjudication State:
  - `AdjudicationState.line_items`: tracks item balances as deductions are applied.
  - Rule execution order: Non-medical -> Room rent & Proportionate -> Sublimits -> Deductible -> Copay -> Sum insured cap.
  - `Final Financial Reconciliation Gate`:
    - Only runs when all Tier 0 gates pass (`overall_status != "BLOCKED"`).
    - `expected_payable = sum(item.remaining_balance for item in adj_state.line_items.values())`.
    - `insurer_payable = rejection.total_approved`.
    - `disputed_amount = expected_payable - insurer_payable`.
    - `reconciliation_failed = abs(disputed_amount) > 1.0`.

---

## Code Layout
- `backend/app/schemas/`: Pydantic data schemas (`provenance.py`, `hospital_bill.py`, `insurance_policy.py`, `rejection_letter.py`, `analysis_result.py`, `evidence_ledger.py`).
- `backend/app/engine/`: Adjudication state, calculator, dependency graph (`adjudication_state.py`, `calculator.py`, `dependency_graph.py`).
- `backend/app/extraction/`: Preprocessing, OCR, VLM extraction (`pipeline.py`, `preprocessor.py`, `vlm_extractor.py`, `ocr_engine.py`, `prompts.py`).
- `backend/app/rules/`: Safety gates and policy rules (`identity_gate.py`, `clinical_firewall.py`, `document_integrity.py`, `proportionate_deduction.py`, `sublimit_rule.py`, `non_medical_rule.py`, `sum_insured_rule.py`, `copay_rule.py`, `deductible_rule.py`, `clause_timeline.py`, `waiting_period.py`, `appeal_evaluator.py`, `engine.py`).
- `backend/app/api/`: API endpoints (`analysis.py`, `portal.py`, `upload.py`).
- `frontend/src/`: Frontend React application (`services/api.js`, `components/analysis/FinancialDelta.jsx`, `pages/Analysis.jsx`).
- `frontend-portal/src/`: Citizen tracking portal (`pages/TrackPage.jsx`).
- `backend/tests/`: Comprehensive test suite (`e2e/`, `test_rules.py`, `test_appeal_adversarial.py`).
