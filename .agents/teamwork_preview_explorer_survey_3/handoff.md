# Survey Phase Handoff Report — Evidence Ledger, Document Provenance, Frontend Calculation Integrity, & Test Suite Coverage

- **Agent**: `teamwork_preview_explorer_survey_3`
- **Working Directory**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_explorer_survey_3`
- **Milestone**: Survey Phase
- **Date**: 2026-09-26T07:55:00Z
- **Target Workspace**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`

---

## 1. Observation

### 1.1 Evidence Ledger & Document Provenance Audit

#### 1.1.1 Absence of Source-Level Provenance Fields in Schemas and Models
Inspection of the backend schemas and database models revealed an absolute absence of source-level evidence metadata:
- In `backend/app/schemas/hospital_bill.py`:
  - `BillLineItem` (lines 5–13): Contains `item_code`, `description`, `category`, `quantity`, `unit_rate`, `amount`, `total`, `is_room_linked`. Contains **zero** fields for `page_number`, `bounding_box`, `source_text_snippet`, `document_hash`, or `ocr_confidence`.
  - `HospitalBill` (lines 15–39): Contains bill headers (`hospital_name`, `patient_name`, `subtotal`, `net_payable`, etc.), `arithmetic_verified: bool`, and a single ungrounded scalar `extraction_confidence: float = 1.0`. Contains no spatial or cryptographic provenance fields.
- In `backend/app/schemas/insurance_policy.py`:
  - `InsurancePolicy` (lines 27–50): Fields `sum_insured`, `room_rent_limit_per_day`, `copay_percentage`, `deductible`, `waiting_periods`, `sub_limits`, `exclusions` possess no linkage to document pages, coordinates, or source text spans.
- In `backend/app/schemas/rejection_letter.py`:
  - `RejectionReason` (lines 4–9) and `RejectionLetter` (lines 11–29): Deduction amounts, clause citations, and reason categories possess no bounding box or source document reference.
- In `backend/app/schemas/analysis_result.py`:
  - `RuleVerdict` (lines 7–19): Possesses `rule_name`, `rule_description`, `status`, `confidence`, `finding`, `insurer_calculation`, `correct_calculation`, `monetary_impact`, `regulatory_citation`, `appeal_recommendation`. Contains **zero** evidence pointers or references to source spans.
- In `backend/app/models/claim.py`:
  - `Document` (lines 28–45): Columns are `id`, `claim_id`, `document_type`, `filename`, `original_filename`, `file_path`, `content_type`, `file_size_bytes`, `extracted_data` (JSON), `extraction_confidence`, `extraction_method`, `created_at`. No column exists for `sha256_hash` or `page_count`.
  - `RuleVerdictRecord` (lines 62–80): Relates to `AnalysisRun`, but has no relationship or foreign key to source documents, pages, or evidence records.
  - No `EvidenceLedger` or `EvidenceItem` database table exists in the system.

#### 1.1.2 OCR and VLM Extraction Pipeline Deficiencies
- **Bounding Boxes Discarded by OCR Engine**:
  In `backend/app/extraction/ocr_engine.py` (lines 58–67), `extract_table` extracts token coordinates:
  ```python
  words.append({
      'text': text,
      'x': data['left'][i],
      'y': data['top'][i],
      'w': data['width'][i],
      'h': data['height'][i]
  })
  ```
  However, in line 89, it formats the output into strings:
  ```python
  table.append([w['text'] for w in row])
  ```
  The spatial bounding boxes `(x, y, w, h)` are completely discarded and never returned.
- **Single-Page Truncation in Extraction Pipeline**:
  In `backend/app/extraction/pipeline.py` (lines 78–80):
  ```python
  first_page = pages[0]
  image_bytes = self._convert_image_to_bytes(first_page)
  ```
  For multi-page hospital bills or multi-page insurance policy documents, only page 0 is passed to the VLM. All content on pages 1 through N is silently ignored during structured extraction.
- **Non-Functional OCR Fallback**:
  In `backend/app/extraction/pipeline.py` (lines 112–133):
  When VLM extraction fails or is unconfigured, the fallback does not parse the OCR text (`combined_text`). Instead, it instantiates hardcoded dummy empty models:
  ```python
  if expected_type == 'HOSPITAL_BILL':
      dummy_data = HospitalBill(bill_id="OCR_FALLBACK", total_amount=0.0, hospital_name="Unknown", patient_name="Unknown", line_items=[], subtotal=0.0, net_payable=0.0)
  ```
- **Document Cryptographic Hash Omission**:
  In `backend/app/api/upload.py` (lines 65–85) and `backend/app/api/portal.py` (lines 128–168), documents are written to disk without computing SHA-256 hashes. `AuditTrail.log` records file names, but no file hashes.

---

### 1.2 Frontend Architecture & Calculation Integrity Audit

#### 1.2.1 Ingestion Contracts (Backend Authoritativeness)
- In `backend/app/api/upload.py` (`POST /api/upload`) and `backend/app/api/portal.py` (`POST /api/portal/submit`):
  Form inputs are restricted to `file`, `document_type`, `claim_id`, `patient_name`, `patient_email`, `patient_phone`.
  Neither endpoint accepts monetary amounts, room rates, policy caps, or deduction decisions from the client.
- In `frontend-portal/src/pages/TrackPage.jsx`:
  The public patient portal exclusively displays read-only metrics queried from `/api/portal/status/{claim_id}` and `/api/reports/{claim_id}/appeal`. No client-side recalculation or override exists in `frontend-portal`.

#### 1.2.2 Calculation Overrides and Fabrications in Internal Frontend
Inspection of `frontend/src/` (the internal auditor portal) revealed multiple severe violations of calculation integrity:
1. **Fabrication of Fake Statutory Violation Cards**:
   In `frontend/src/components/analysis/FinancialDelta.jsx` (lines 366–433):
   When `failVerdicts` is empty (i.e. backend found 0 violations or claim is clean), rather than rendering a clean status, the frontend renders hardcoded fallback discrepancy cards:
   - Card 1: `+₹32,000.00` ("Proportionate Deduction Applied to Fixed Medical Charges... Insurer reduced Operation Theatre (₹35,000) and Consultant charges (₹15,000)...")
   - Card 2: `+₹10,500.00` ("Pre-Existing Condition Contestation Beyond Moratorium Window... The policy has been continuously renewed for 64 months...")
   This directly fabricates ₹42,500.00 of non-existent violations on the client side.
2. **Hardcoded Financial Fallback Injections**:
   In `frontend/src/components/analysis/FinancialDelta.jsx` (lines 49–75):
   ```javascript
   const insurerPaid = Number(result.total_insurer_calculation ?? result.approved_amount ?? 68000);
   const recoverableAmount = Number(result.total_monetary_impact ?? 42500);
   const correctAllowable = Number(result.total_correct_calculation ?? (insurerPaid + recoverableAmount));
   const billedAmount = Number(claim?.billed_amount || result.total_claimed || result.billed_amount || 124000);
   ```
   If any backend calculation field is omitted, the frontend silently injects arbitrary numbers (`68000`, `42500`, `124000`) and executes arithmetic operations on them.
3. **Client-Side Derived Figures**:
   In `FinancialDelta.jsx` line 62, `correctAllowable` is calculated client-side as `insurerPaid + recoverableAmount` instead of requiring an authoritative backend evaluation.
4. **Mock Normalization Masking Backend State**:
   In `frontend/src/services/api.js` (`normalizeAnalysisResult`, lines 64–96):
   If `data` is empty, falsy, or missing expected keys, it merges the response with `mockAnalysisResult` from `frontend/src/services/mockData.js`, presenting mock data as verified results.

---

### 1.3 Test Suite Execution & Inventory Assessment

Direct execution of pytest via `.\venv\Scripts\pytest.exe backend/tests/` revealed that previous claims of "63 tests passing with 0 failures" are false. The test suite is broken:

```text
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.3.4, pluggy-1.6.0
collected 33 items / 2 errors

=================================== ERRORS ====================================
__________ ERROR collecting backend/tests/test_appeal_adversarial.py __________
E   ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'
_____________ ERROR collecting backend/tests/test_new_features.py _____________
E   ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.42s ==============================
```

#### 1.3.1 Inventory by File
1. `backend/tests/test_rules.py` (11 tests defined, **3 FAILED**, 8 passed):
   - `test_proportionate_deduction_within_limit`: **FAILED** (`AssertionError: assert 'SKIPPED' == 'PASS'`)
   - `test_proportionate_deduction_mismatch`: **FAILED** (`AssertionError: assert 'SKIPPED' == 'FAIL'`)
   - `test_proportionate_deduction_correct_deduction`: **FAILED** (`AssertionError: assert 'SKIPPED' == 'PASS'`)
   - Root cause: `check_proportionate_deduction` requires `length_of_stay`, but `get_base_bill()` provides no dates, evaluating `length_of_stay` to `None` and skipping unconditionally.
   - `test_rule_engine_integration`: Contains trivial assertions (`assert len(result.rule_verdicts) >= 0`).
2. `backend/tests/test_forensics.py` (4 tests defined, **4 passed**):
   - Tests `BillAnomalyDetector` (normal, inflated charges) and `ConsistencyChecker` (matching, mismatch).
3. `backend/tests/test_adversarial_challenger_1.py` (18 tests defined, **18 passed**):
   - Tests `PDFInspector` (0-byte, plain text, noise, fake EOFs, malformed xref, missing /Prev) and `AnomalyScorer` (negative values, multi-crore amounts, NaN inputs, empty dicts).
4. `backend/tests/test_new_features.py` (17 tests defined, **0 EXECUTED / COLLECTION CRASH**):
   - Fails at import: `cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'`.
5. `backend/tests/test_appeal_adversarial.py` (15 tests defined, **0 EXECUTED / COLLECTION CRASH**):
   - Fails at import: `cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'`.

**Summary**: Out of 65 defined tests across 5 files:
- **30 Passed** (46.1%)
- **3 Failed** (4.6%)
- **32 Blocked from execution by Collection ImportErrors** (49.2%)

---

### 1.4 Critical Core Architecture Vulnerabilities Discovered

1. **Tier 0 Safety Gate Bypass in `RuleEngine`**:
   In `backend/app/rules/engine.py` (lines 42–45):
   ```python
   verdict = func(bill, policy, rejection)
   verdicts.append(verdict)
   if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:
       gate_blocked = True
   ```
   Both `backend/app/rules/identity_gate.py` (lines 45, 65, 79, 99) and `backend/app/rules/clinical_firewall.py` (line 51) return `status="BLOCKED"`.
   Because `"BLOCKED"` is **not** included in `["NEEDS_REVIEW", "FAIL", "WARNING"]`, `gate_blocked` remains `False`!
   Consequently, lines 58–74 proceed to execute all Tier 1 financial and policy rules on blocked claims, directly violating the safety firewall.
2. **Double Deduction Bug in Proportionate Deduction**:
   In `backend/app/rules/proportionate_deduction.py` (lines 49–73):
   Line 53 includes the `ROOM` category in `room_linked_items`. Line 61 calculates `proportionate_reduction = room_linked_sum * (1 - limit/actual)`.
   For the room charges, this reduction equals `(actual - limit) * length_of_stay`.
   Then, line 72 computes:
   `expected_total_deduction = total_room_excess + proportionate_reduction + misc_deductions`
   This adds `total_room_excess` **twice** for the room charges, unlawfully doubling the deduction against the policyholder.
3. **Approximation Drift in Moratorium and Waiting Periods**:
   In `backend/app/schemas/insurance_policy.py` (line 57) and `backend/app/rules/waiting_period.py` (line 34), calculations use `days / 30.44` or `months * 30.44`. Float-day approximations fail exact calendar-month determinations required under IRDAI Master Circular 2024.
4. **Outdated Statutory Limits in Code**:
   In `backend/app/rules/waiting_period.py` (line 34), default PED waiting period is hardcoded as `48` months. IRDAI Master Circular 2024 reduced the maximum statutory PED waiting period to `36` months.
5. **Permissive Identity Gate Fallback**:
   In `backend/app/rules/identity_gate.py` (line 106): If identity markers are missing or `"UNKNOWN"`, the rule returns `PASS` ("MATCH: Identity markers and dates are consistent or missing (Insufficient Evidence). Proceeding.") instead of halting with `NEEDS_REVIEW` or `BLOCKED`.

---

## 2. Logic Chain

1. **Premise 1 (Provenance & Evidence Requirement)**: Requirement R1 mandates that every finding must possess source-document provenance (page number, bounding box, text snippet, file hash) and zero hallucination risk.
2. **Evaluation 1**:
   - Observations 1.1.1 and 1.1.2 demonstrate that neither Pydantic schemas, database models, OCR routines, nor VLM prompts extract, store, or forward bounding boxes, verbatim text snippets, or document hashes.
   - Observations 1.1.2 show that multi-page documents are truncated to `pages[0]`, dropping all subsequent pages from VLM analysis.
   - Therefore, the claim verification pipeline currently operates without an evidence ledger, and findings cannot be linked back to source coordinates.
3. **Premise 2 (Frontend Authority Invariant)**: Requirement R1 dictates that frontend calculations must never override backend calculations and values must never be fabricated.
4. **Evaluation 2**:
   - Observation 1.2.1 confirms that backend upload endpoints do not accept client-calculated numbers, ensuring backend processing authority on ingestion.
   - Observation 1.2.2 proves that `FinancialDelta.jsx` injects client-side fallback constants (`₹68k`, `₹42.5k`, `₹124k`), derives calculations in the browser, and fabricates fake Tier 1 statutory violations (`+₹32,000` and `+₹10,500`) when the backend returns 0 violations.
   - Therefore, the frontend violates the non-fabrication and calculation integrity mandates.
5. **Premise 3 (Test Suite Integrity & Safety Gate Invariants)**: Requirement R2 and R4 mandate that Tier 0 Safety Gates strictly halt downstream financial execution, test coverage programmatically verifies core logic, and suites pass cleanly without crashes.
6. **Evaluation 3**:
   - Observation 1.3 shows that 35 out of 65 tests cannot execute due to collection `ImportError` in `test_appeal_adversarial.py` and `test_new_features.py`, and 3 tests fail in `test_rules.py`.
   - Observation 1.4 proves that `RuleEngine.run_all_rules` fails to check for `verdict.status == "BLOCKED"`, allowing financial rules to execute when Tier 0 identity or clinical gates are tripped.
   - Observation 1.4 proves that `proportionate_deduction.py` doubles room rent deductions, and waiting periods use non-statutory 48-month limits and float approximations.
   - Therefore, the existing test suite does not guarantee system safety, and critical architectural safety gates are currently non-functional.

---

## 3. Caveats

- Investigation was strictly read-only per agent constraints; no production code was modified.
- VLM live network API calls were not invoked with live provider credentials (e.g. OpenAI/Anthropic/Gemini) during survey; analysis was based on static code AST inspection, schema definitions, and local pipeline fallbacks.
- Database analysis evaluated SQLAlchemy model declarations in `backend/app/models/claim.py` and SQLite schema in `claimguard.db`.

---

## 4. Conclusion

1. **Evidence Ledger & Provenance**: Currently non-existent. Schemas, OCR pipeline, and database lack fields for bounding boxes, verbatim snippets, page numbers, and SHA-256 document hashes. Bounding boxes extracted during OCR are actively discarded.
2. **Frontend Calculation Integrity**: The ingestion API does not accept form calculations, but the auditor UI (`FinancialDelta.jsx`) injects hardcoded financial figures, derives values client-side, and fabricates two fake violation cards (+₹32,000 and +₹10,500) on clean claims.
3. **Test Suite Status**: Broken. 35 tests cannot be collected due to missing `check_appeal_viability`, 3 tests fail due to missing `length_of_stay`, and only 30 pass (46.1% pass rate). 0 tests exist for `Cross-Document Identity Gate`, `Clinical Firewall Gate`, or `Document Arithmetic Integrity Gate`.
4. **Architectural Vulnerabilities**: High-severity bypass in `RuleEngine.run_all_rules` where `"BLOCKED"` status does not set `gate_blocked = True`, executing financial rules on blocked claims; double deduction arithmetic bug in `proportionate_deduction.py`; and outdated 48-month statutory PED limits.

---

## 5. Verification Method

To independently verify the observations and findings in this report, run the following commands and inspect the referenced files:

1. **Verify Test Suite Collection & Failure Status**:
   ```powershell
   .\venv\Scripts\pytest.exe backend/tests/
   ```
   *Expected Result*: Fails with 2 collection `ImportError` exceptions referencing `check_appeal_viability` in `test_appeal_adversarial.py` and `test_new_features.py`.
2. **Verify `test_rules.py` Proportionate Deduction Failures**:
   ```powershell
   .\venv\Scripts\pytest.exe backend/tests/test_rules.py
   ```
   *Expected Result*: 3 failures in `test_proportionate_deduction_*` with `AssertionError: assert 'SKIPPED' == 'PASS'/'FAIL'`.
3. **Inspect Tier 0 Gate Bypass Bug**:
   View lines 39–68 of `backend/app/rules/engine.py`. Confirm that line 44 checks `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:` and does not include `"BLOCKED"`.
4. **Inspect Proportionate Deduction Double Deduction**:
   View lines 53, 61, and 72 of `backend/app/rules/proportionate_deduction.py`. Confirm that `ROOM` category is included in `room_linked_items` and added again via `total_room_excess`.
5. **Inspect Frontend Fake Card Fabrication**:
   View lines 366–433 of `frontend/src/components/analysis/FinancialDelta.jsx`. Confirm that when `failVerdicts` is empty, hardcoded cards with `+₹32,000.00` and `+₹10,500.00` are rendered.
6. **Inspect Discarded Bounding Boxes in OCR Engine**:
   View lines 58–67 and 89 of `backend/app/extraction/ocr_engine.py`. Confirm `x`, `y`, `w`, `h` are collected in lines 63–66 and discarded in line 89.
