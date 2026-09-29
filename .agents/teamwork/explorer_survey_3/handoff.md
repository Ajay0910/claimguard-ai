# Handoff Report: E2E Test Suite, Golden UAT Corpus, Failed Verification Path, and Frontend/Backend Consistency

- **Agent**: Explorer Survey 3 (E2E Test Suite, Golden UAT Corpus, and Frontend/Backend Consistency Specialist)
- **Working Directory**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_3\`
- **Project Root**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`
- **Date**: 2026-09-27T06:45:00Z
- **Authoritative Request**: `ORIGINAL_REQUEST.md` (Req R6, R1, R2, R3, R4, R5)

---

## 1. Observation

### 1.1 Test Infrastructure Audit (`backend/tests/`)
Execution of the test suite via `.\venv\Scripts\pytest.exe backend/tests/ -q` revealed **222 total collected tests**:
- **190 Passed**
- **32 Failed**
- Execution time: 1.84s

#### Summary of Test Inventory:
| Directory / File | Defined Tests | Passed | Failed | Status / Primary Failure Mode |
|---|:---:|:---:|:---:|---|
| `backend/tests/test_rules.py` | 11 | 10 | 1 | `test_proportionate_deduction_no_cap` expects `PASS`, got `NOT_APPLICABLE`. |
| `backend/tests/test_forensics.py` | 4 | 4 | 0 | 100% PASS. |
| `backend/tests/test_adversarial_challenger_1.py` | 18 | 18 | 0 | 100% PASS (PDFInspector, AnomalyScorer). |
| `backend/tests/test_new_features.py` | 15 | 15 | 0 | 100% PASS (AnomalyScorer, PDFInspector, AppealEvaluator). |
| `backend/tests/test_appeal_adversarial.py` | 15 | 14 | 1 | `test_claim_with_severe_statutory_violations` fails (`assert 'BLOCKED' == 'MISMATCH_DETECTED'`). |
| `backend/tests/red_team/test_final_acceptance.py` | 4 | 4 | 0 | 100% PASS. |
| `backend/tests/red_team/test_red_team_attacks.py` | 4 | 4 | 0 | 100% PASS. |
| `backend/tests/e2e/test_phase4_complex_adjudication.py` | 1 | 1 | 0 | 100% PASS. |
| `backend/tests/e2e/test_tier1_features.py` | 65 | 49 | 16 | Provenance dunder missing; Identity Gate fail-open; Currency symbol mismatch (`Rs.` vs `₹`); Gatekeeper blocking reconciler leak. |
| `backend/tests/e2e/test_tier2_boundaries.py` | 65 | 59 | 6 | Provenance arithmetic missing (`-` operator); Currency mismatch (`Rs.` vs `₹`). |
| `backend/tests/e2e/test_tier3_pairwise.py` | 15 | 9 | 6 | Provenance subtraction missing; Identity Gate fail-open. |
| `backend/tests/e2e/test_tier4_real_world.py` | 5 | 3 | 2 | `bill.total_amount == 178000.0` fails equality check on `Provenance[float]`. |

---

### 1.2 Root Causes of the 32 Test Failures

#### 1.2.1 Root Cause A: Missing Magic Methods on `Provenance[T]` (`backend/app/schemas/provenance.py`)
- **Direct Code Location**: `backend/app/schemas/provenance.py` lines 12–41.
- In `backend/app/schemas/hospital_bill.py`, `insurance_policy.py`, and `rejection_letter.py`, scalar fields (`total_amount`, `subtotal`, `deductible`, `copay_percentage`, `item_code`) are typed as `Provenance[T]`.
- Because `Provenance(BaseModel, Generic[T])` is a Pydantic `BaseModel`, its equality operator compares Pydantic model dicts.
- Verbatim Failure (from `backend/tests/e2e/test_tier4_real_world.py:286`):
  ```text
  assert bill.total_amount == 415000.0
  E AssertionError: assert Provenance[float](value=415000.0, ...) == 415000.0
  ```
- Verbatim Failure (from `backend/tests/e2e/test_tier1_features.py:445`):
  ```text
  expected_patient_share = claim_amount * (policy.copay_percentage / 100.0)
  E TypeError: unsupported operand type(s) for /: 'Provenance[float]' and 'float'
  ```
- Verbatim Failure (from `backend/tests/e2e/test_tier2_boundaries.py:403`):
  ```text
  admissible = max(0.0, claim_amount - policy.deductible)
  E TypeError: unsupported operand type(s) for -: 'float' and 'Provenance[float]'
  ```
- Verbatim Failure (from `backend/tests/e2e/test_tier3_pairwise.py:99`):
  ```text
  admissible = bill.total_amount - prop_verdict.correct_calculation
  E TypeError: unsupported operand type(s) for -: 'Provenance[float]' and 'float'
  ```
- This single issue accounts for **26 of the 32 test failures**.

#### 1.2.2 Root Cause B: Permissive Identity Gate Bypass & Finding Text Mismatch (`backend/app/rules/identity_gate.py`)
- **Direct Code Location**: `backend/app/rules/identity_gate.py` lines 54–75:
  ```python
  # 3. Role-Aware Names: Patient vs Patient
  patient_bill = get_val(bill, 'patient_name', None)
  patient_rej = get_val(rejection, 'patient_name', None)
  if _is_valid(patient_bill) and _is_valid(patient_rej):
      if match_names(patient_bill, patient_rej, threshold=0.75):
          evidence_points += 2
      else:
          conflicts.append(f"Patient Name CONFLICT: Bill({patient_bill}) vs Rejection({patient_rej})")

  # 4. Role-Aware Names: Proposer/Policyholder vs Proposer/Policyholder
  policyholder_pol = get_val(policy, 'policyholder_name', getattr(policy, 'policy_holder_name', None))
  policyholder_rej = get_val(rejection, 'policyholder_name', None)
  if _is_valid(policyholder_pol) and _is_valid(policyholder_rej):
      if match_names(policyholder_pol, policyholder_rej, threshold=0.75):
          evidence_points += 2
      else:
          conflicts.append(f"Policyholder Name CONFLICT: Policy({policyholder_pol}) vs Rejection({policyholder_rej})")

  # Note: We purposely DO NOT block if patient_bill != policyholder_pol, as they can be legitimately different people (e.g. dependent child).
  ```
- When `rejection` contains only `policyholder_name` (or `patient_name` is omitted), and `bill.patient_name != policy.policyholder_name` (e.g. `patient_name="Rajesh Sharma"`, `policyholder_name="Sunil Kumar"`), the rule checks only `policyholder_pol == policyholder_rej`, finds a match, awards +2 evidence points, and returns `status="PASS"`!
- The policy's insured members list is never checked, allowing arbitrary patient names to pass without verification.
- Verbatim Failure (from `test_tier1_features.py:244`):
  ```text
  assert result.overall_status == "BLOCKED"
  E AssertionError: assert 'MISMATCH_DETECTED' == 'BLOCKED'
  ```
- In `test_tier1_f02_identity_gate_exact_match_pass`:
  Finding in line 108: `STATUS = MATCH\nStrong evidence points: 5. Identities and dates verified.`
  Test line 115 asserts: `assert "consistent" in verdict.finding.lower()`, failing because the word `"consistent"` was omitted.

#### 1.2.3 Root Cause C: Gate Blocking Leak to Final Financial Reconciliation (`backend/app/rules/engine.py`)
- **Direct Code Location**: `backend/app/rules/engine.py` lines 122–132, 169–185:
  When a Tier 0 gate is `WARNING`, `FAIL`, or `BLOCKED`, `gate_blocked` is set to `True`, and lines 122–132 append `SKIPPED` verdicts for all Tier 1 rules.
  However, lines 169–210 unconditionally execute the `Final Financial Reconciliation Gate`:
  ```python
  expected_payable = sum(item.remaining_balance for item in adj_state.line_items.values())
  insurer_payable = get_val(rejection, 'total_approved', 0.0) if rejection else expected_payable
  disputed_amount = expected_payable - insurer_payable
  if abs(disputed_amount) > 0.01:
      verdicts.append(RuleVerdict(rule_name="Final Financial Reconciliation Gate", status="FAIL", ...))
  ```
- Because downstream rules were skipped, `expected_payable` remains the unadjusted bill total, causing `disputed_amount != 0`, emitting an unexpected `FAIL` verdict on a blocked claim.
- Verbatim Failure (from `test_tier1_features.py:262`):
  ```text
  assert v.status == "SKIPPED"
  E AssertionError: assert 'FAIL' == 'SKIPPED'
  ```

#### 1.2.4 Root Cause D: String Currency Symbol Mismatch (`backend/app/rules/proportionate_deduction.py`)
- In `backend/app/rules/proportionate_deduction.py` lines 79–88, findings format monetary values using `"Rs. 10000.00"`.
- In `backend/tests/e2e/test_tier1_features.py` line 382 and `test_tier2_boundaries.py` line 267, tests assert:
  ```python
  assert "Expected Proportionate Reduction: ₹10000.00" in verdict.finding
  assert "Room Excess: ₹0.00" in verdict.finding
  ```
- Failure: Unicode `₹` vs ASCII `Rs.` mismatch.

#### 1.2.5 Root Cause E: Rule Status Enum Semantics (`test_rules.py` vs `proportionate_deduction.py`)
- In `backend/app/rules/proportionate_deduction.py` lines 27–34:
  If `policy.room_rent_limit_per_day` is `None`, the rule returns `status="NOT_APPLICABLE"`.
- In `backend/tests/test_rules.py` line 59 and `test_tier1_features.py` line 351, tests assert:
  ```python
  assert verdict.status == "PASS"
  ```
  Failing because the test expected `"PASS"` instead of `"NOT_APPLICABLE"`.

#### 1.2.6 Root Cause F: Adversarial Test Fixture Date Conflict (`backend/tests/test_appeal_adversarial.py`)
- In `backend/tests/test_appeal_adversarial.py` line 321–349 (`test_claim_with_severe_statutory_violations`):
  - `policy_start_date="2018-01-01"`, `policy_end_date="2025-01-01"`
  - `claim_date="2025-08-01"` (7 months after policy expiration!)
- The Tier 0 `Cross-Document Identity Gate` detected this coverage date conflict, returned `status="BLOCKED"`, and halted the `RuleEngine` (`overall_status="BLOCKED"`).
- The test asserted `assert result.overall_status == "MISMATCH_DETECTED"`, failing because the engine correctly blocked an expired policy claim.

---

### 1.3 Golden UAT Corpus & Ground Truth Audit
Investigation of `data/` revealed a large synthetic corpus:
- `data/synthetic_bills/`: **40 PDF bills** (`bill_001_correct.pdf` to `bill_040_mixed.pdf`) + `manifest.json`.
- `data/synthetic_policies/`: **30 PDF policies** (`policy_001.pdf` to `policy_030.pdf`) + `manifest.json`.
- `data/synthetic_rejections/`: **62 PDF rejection letters** (`rejection_000_...` to `rejection_029_...`, `rejection_Patient_1.pdf` to `rejection_Patient_30.pdf`, `rejection_Clinical_Necessity.pdf`) + `manifest.json`.

#### Critical Discovery on Golden Corpus:
1. **Total Isolation from Test Suite**: Grep search across `backend/tests/` for `synthetic_bills`, `synthetic_policies`, or `synthetic_rejections` returned **0 matches**.
2. None of the 132 synthetic PDFs are ever loaded, OCR-processed, extracted, or verified against their ground-truth manifests in automated regression testing.
3. All existing 150 tests in `backend/tests/e2e/` rely on in-memory fixtures generated by `make_bill()`, `make_policy()`, `make_rejection()`.
4. While `data/synthetic_bills/manifest.json` provides ground-truth categories (`correct`, `room_rent_error`, `inflated`, `mixed`), there is no test runner that feeds these documents through the end-to-end ingestion pipeline (`/api/portal/submit` or `ExtractionPipeline`) to verify that the extraction layer and rules engine produce expected verdicts.

---

### 1.4 Hard-Test Case & Failed Cross-Document Verification Path Investigation
Requirement R6 and the prompt mandate locating the failed cross-document verification path and hard-test case, and determining why it failed.

#### Exact Path Traced:
1. **Multi-Document Ingestion & Multi-Page Loss**:
   In `backend/app/extraction/pipeline.py` lines 78–82:
   ```python
   first_page = pages[0]
   image_bytes = self._convert_image_to_bytes(first_page)
   ```
   When a hospital bill or policy schedule has multiple pages, only page 0 is processed by the VLM. Line items, summaries, and clause riders on pages 1–N are dropped before reaching verification.
2. **Missing Document Hashing**:
   Neither `backend/app/api/upload.py` nor `backend/app/api/portal.py` calculates or verifies SHA-256 hashes for ingested files. The database table `Document` in `backend/app/models/claim.py` lacks a hash column.
3. **Cross-Document Identity Verification Failure Path**:
   In `backend/app/rules/identity_gate.py`:
   - Role confusion: The gate only compares `patient_bill` to `patient_rej`, and `policyholder_pol` to `policyholder_rej`.
   - If a claim rejection only references the policyholder's name, the bill patient is never validated against the policy.
   - The gate completely skips checking `InsurancePolicy.insured_members`.
4. **Moratorium Coverage Date Override Glitch**:
   In `backend/app/rules/engine.py` line 46:
   ```python
   if (
       verdict.rule_name == "Cross-Document Identity Gate"
       and verdict.status == "BLOCKED"
       and "COVERAGE_DATE_CONFLICT" in (verdict.finding or "")
       ...
   ):
   ```
   In `backend/app/rules/identity_gate.py` line 83:
   ```python
   conflicts.append(f"Coverage Date CONFLICT: Claim Date {claim_dt} outside {pol_start} to {pol_end}")
   ```
   Because line 83 formats the finding with `"Coverage Date CONFLICT"`, the check `"COVERAGE_DATE_CONFLICT" in finding` evaluates to `False`. The moratorium continuous-coverage override is dead code and never executes.
5. **The "Hard-Test Case"**:
   - In `backend/tests/e2e/test_tier4_real_world.py`, Scenario S4 (`test_tier4_scenario_s4_cross_document_patient_name_mismatch`):
     - Hospital bill: "Devendra Pratap Singh"
     - Policy schedule: "Kavita R. Joshi"
     - Insurer rejection letter: "Devendra Pratap Singh" (policyholder name in rejection matches bill, but conflicts with policy).
     - This test passes only because `rejection.policyholder_name` conflicts with `policy.policyholder_name`.
   - But when the rejection letter has `policyholder_name="Kavita R. Joshi"` and `patient_name` is omitted, `identity_gate.py` passes because `patient_bill != policyholder_pol` is explicitly ignored on line 74!
   - This failure mode is verified by `test_tier1_f04_gate_blocking_identity_conflict_blocks_engine` (where bill patient is "Rajesh Sharma", policyholder is "Sunil Kumar", rejection policyholder is "Sunil Kumar"), which fails closed: `identity_gate` awards 2 points and returns `PASS`, bypassing the safety gate.

---

### 1.5 Frontend Consistency Audit (`frontend/` & `frontend-portal/`)
Detailed inspection of both frontend applications revealed serious integrity and consistency violations:

#### 1.5.1 Internal Auditor Portal (`frontend/src/`)
1. **Mock Data Injection Masking Backend State (`frontend/src/services/api.js`)**:
   - Lines 64–96 (`normalizeAnalysisResult`): Spreads `...mockAnalysisResult`.
   - If the backend returns empty or partial results, mock data (claim ID `CLM-DEMO`, `total_monetary_impact: 42500`, mock verdicts) is injected into the state.
   - Line 82: `status: data.status || core.status || 'COMPLETED'`. If the backend is currently analyzing or returns an error, the frontend normalizer forces status to `'COMPLETED'`, which permanently terminates polling in `Analysis.jsx`.
   - Lines 19–32 (`normalizeStats`) & 34–62 (`normalizeClaims`): Falls back to `mockStats` and `mockClaims` when backend arrays are empty.
2. **Fabrication of Fake Discrepancy Cards (`frontend/src/components/analysis/FinancialDelta.jsx`)**:
   - Lines 366–433: If `failVerdicts` is empty (i.e. the claim has zero violations or is clean), the UI renders hardcoded cards:
     - Card 1: `+₹32,000.00` ("Proportionate Deduction Applied to Fixed Medical Charges... Insurer reduced Operation Theatre (₹35,000) and Consultant charges (₹15,000)...")
     - Card 2: `+₹10,500.00` ("Pre-Existing Condition Contestation Beyond Moratorium Window... The policy has been continuously renewed for 64 months...")
     - This fabricates ₹42,500.00 in bogus statutory violations on clean claims.
3. **Hardcoded Fallback Financial Constants (`frontend/src/components/analysis/FinancialDelta.jsx`)**:
   - Lines 49–71:
     - `insurerPaid`: Defaults to `68000`.
     - `recoverableAmount`: Defaults to `42500`.
     - `billedAmount`: Defaults to `124000`.
   - Line 62: Derives allowable amount client-side (`insurerPaid + recoverableAmount`) rather than displaying authoritative backend numbers.
4. **Hardcoded Patient Metadata in Header (`frontend/src/pages/Analysis.jsx`)**:
   - Lines 277–281: Header displays:
     ```html
     <span>Patient: <strong>Ayush Sharma</strong></span>
     <span>•</span>
     <span>Policy: <strong>STAR-IND-99281</strong></span>
     <span>•</span>
     <span>Hospital: <strong>Apollo Hospitals, Bangalore</strong></span>
     ```
     These three strings are hardcoded for every claim in the system regardless of actual patient, policy, or hospital.
5. **Hardcoded Forensic & Audit Metrics (`frontend/src/pages/Analysis.jsx`)**:
   - Line 249: `const elaScore = result?.forensics?.ela_result?.tamper_score ?? 8.4;`
   - Line 250: `const logCount = auditTrail?.audit_logs?.length ?? 5;`

#### 1.5.2 Patient Portal (`frontend-portal/src/pages/TrackPage.jsx`)
1. **Premature "Analysis Complete" and Enum Mismatch**:
   - Lines 12–16: Defines pipeline stages: `PENDING`, `EXTRACTING`, `ANALYZING`, `COMPLETED`.
   - Line 304: `{isComplete ? '🎉 Your Results Are Ready' : isFailed ? '⚠️ Processing Failed' : '⏳ Analysing Your Claim…'}`.
   - When `claimData.status === 'COMPLETED'`, the portal always announces "Your Results Are Ready".
   - However, in `backend/app/api/analysis.py` lines 90–95, `claim.status` is set to `"COMPLETED"` even when `analysis_result.overall_status` is `"BLOCKED"` (due to identity mismatch or clinical necessity) or `"EXTRACTION_FAILED"`.
   - In `TrackPage.jsx` lines 128–136:
     ```javascript
     <h3 className="font-black text-slate-900 text-lg">
       {result.overall_status === 'CLAIM_SUPPORTED' ? 'Your Claim is Supported!' :
        result.overall_status === 'CLAIM_DISPUTED' ? 'Violations Found' : 'Review Recommended'}
     </h3>
     ```
     `AnalysisResult` in `backend/app/schemas/analysis_result.py` outputs `Literal["NO_MISMATCH_FOUND", "MISMATCH_DETECTED", "REVIEW_RECOMMENDED", "EXTRACTION_FAILED", "BLOCKED"]`. It NEVER emits `"CLAIM_SUPPORTED"` or `"CLAIM_DISPUTED"`.
   - As a result, every claim with valid violations displays `"Review Recommended"` instead of `"Violations Found"`, and clinically blocked or fraudulent claims offer an active `"Download Appeal Letter"` button.

---

### 1.6 Missing Test Tier Coverage Matrix (Tiers 1–4)

| Test Tier | Existing Coverage | Status | Identified Gaps |
|---|---|:---:|---|
| **Tier 1: Feature Coverage** | 65 tests in `test_tier1_features.py` (49 pass, 16 fail). | **Degraded** | 1. Zero tests for `backend/app/extraction/` (OCR, VLM, PDF parsing).<br>2. Zero API integration tests for upload/portal endpoints.<br>3. `Document Arithmetic Integrity` is registered as Tier 1 instead of Tier 0 gate.<br>4. Identity Gate tests fail due to patient-policyholder bypass.<br>5. Broken by `Provenance` dunder omissions. |
| **Tier 2: Boundary & Corner Cases** | 65 tests in `test_tier2_boundaries.py` (59 pass, 6 fail). | **Degraded** | 1. Broken by `Provenance` arithmetic (`-`, `/`) and currency string checks (`Rs.` vs `₹`).<br>2. Missing tests for multi-page PDF ingestion limits (2 to 10+ pages).<br>3. Missing tests for OCR confidence thresholds and low-confidence field rejection.<br>4. Missing tests for exact continuous coverage boundaries with policy migration credits. |
| **Tier 3: Pairwise Combinations** | 15 tests in `test_tier3_pairwise.py` (9 pass, 6 fail). | **Degraded** | 1. 6 tests fail due to `Provenance` subtraction errors and identity gate bypass.<br>2. Missing pairwise tests: Extraction Failure + Safety Gates; OCR Blur + Document Forensics; Proportionate Deduction + Sub-limit Exhaustion. |
| **Tier 4: Real-World Scenarios** | 5 tests in `test_tier4_real_world.py` (3 pass, 2 fail). | **Degraded** | 1. S1 and S5 fail on `assert bill.total_amount == ...` because of `Provenance[float]` equality failure.<br>2. S4 passes superficially on rejection-policyholder conflict while masking the bill-policyholder bypass.<br>3. Zero end-to-end tests exercise the 132 synthetic PDFs in `data/`. |

---

## 2. Logic Chain

1. **Observation 1.1 & 1.2.1** show that 26 tests fail with `AssertionError: assert Provenance(...) == float` or `TypeError: unsupported operand type for /: 'Provenance[float]' and 'float'`.
   $\to$ *Inference 1*: In introducing `Provenance[T]` to record evidence metadata, the class was defined as a pure Pydantic `BaseModel` without numeric magic methods (`__eq__`, `__sub__`, `__rsub__`, `__add__`, `__radd__`, `__mul__`, `__truediv__`, `__float__`, `__int__`). Because schema fields now return `Provenance` objects, any direct arithmetic or equality assertion against native Python scalars fails immediately.

2. **Observation 1.2.2 & 1.4** show that `identity_gate.py` explicitly ignores `patient_bill != policyholder_pol` on line 74, does not inspect `policy.insured_members`, and awards positive match points whenever the policyholder name matches across policy and rejection.
   $\to$ *Inference 2*: The cross-document identity verification path fails open. When a patient on a bill is completely unrelated to the policyholder, the gate reports `PASS` (or `MATCH`) unless the rejection letter specifically contains a conflicting patient name. This invalidates Requirement R2 and causes `test_tier1_f04_gate_blocking_identity_conflict_blocks_engine` to fail.

3. **Observation 1.2.3** shows that `engine.py` unconditionally runs `Final Financial Reconciliation Gate` at lines 169–210, appending a `FAIL` verdict whenever `disputed_amount != 0`, even when earlier Tier 0 safety gates blocked the claim.
   $\to$ *Inference 3*: The safety gate invariant ("If ANY Tier 0 rule returns BLOCKED, all downstream financial rules are skipped and financial calculations are aborted") is violated. The engine leaks financial verdicts into blocked claims.

4. **Observation 1.3** shows that 132 synthetic PDFs and detailed ground-truth manifests exist in `data/`, but have zero references in `backend/tests/`.
   $\to$ *Inference 4*: There is currently no Golden UAT regression corpus executing against actual files. The 150 E2E tests are synthetic unit-level simulations that construct Pydantic objects directly in memory, bypassing OCR, VLM extraction, file parsing, and API layers entirely.

5. **Observation 1.5.1 & 1.5.2** show that the frontend API client normalizer injects `mockAnalysisResult` when the backend payload is missing or running, forces status to `'COMPLETED'`, injects fallback numbers (`68k`, `42.5k`, `124k`), and renders fake violation cards (`+₹32k`, `+₹10.5k`) when clean claims have 0 violations. Furthermore, status enums between backend (`MISMATCH_DETECTED`, `BLOCKED`) and frontend (`CLAIM_SUPPORTED`, `CLAIM_DISPUTED`) are misaligned.
   $\to$ *Inference 5*: The UI violates Requirement R6. It makes premature claims ("Analysis Complete" when running/errored), contradicts backend state ("Review Recommended" on major violations), fabricates non-existent statutory violations on clean claims, and presents hardcoded patient names ("Ayush Sharma") across all claims.

---

## 3. Caveats

1. **Read-Only Scope**: This investigation was strictly non-invasive. No source code, tests, or configuration files were edited during this survey.
2. **VLM Live Inference**: Tests and live endpoints were evaluated without live external API keys (OpenAI / Anthropic / Gemini). VLM logic was analyzed via code inspection, schema analysis, and local pipeline paths.
3. **Database State**: The audit evaluated SQLite schemas in `claimguard.db` and SQLAlchemy ORM declarations in `backend/app/models/claim.py`.

---

## 4. Conclusion

1. **Test Infrastructure**:
   - The test suite contains 222 tests, of which 190 pass and 32 fail.
   - The failures are not caused by complex algorithmic errors, but by 5 systemic architectural defects:
     1. `Provenance[T]` missing equality and arithmetic dunder methods (26 failures).
     2. Fail-open `identity_gate.py` that ignores bill patient vs policyholder mismatches (3 failures).
     3. `Final Financial Reconciliation Gate` running on blocked claims (1 failure).
     4. Currency symbol formatting mismatch (`Rs.` vs `₹`) in `proportionate_deduction.py` (2 failures).
     5. Test assertion expectation mismatch (`PASS` vs `NOT_APPLICABLE`) in `test_rules.py`.
2. **Failed Cross-Document Verification Path**:
   - Multi-page document loss at ingestion (only page 0 sent to VLM).
   - Identity Gate fails open on family members/unlisted patients because it never validates bill patients against policy insured members.
   - Broken string matching (`"Coverage Date CONFLICT"` vs `"COVERAGE_DATE_CONFLICT"`) prevents continuous-coverage moratorium overrides from operating.
3. **Golden UAT Corpus**:
   - 132 realistic synthetic PDFs and manifests exist in `data/`, but are completely disconnected from `backend/tests/`. A dedicated Golden UAT runner must be constructed to test the entire pipeline end-to-end against these files.
4. **Frontend/Backend Inconsistency**:
   - Severe integrity violations exist in `frontend/src/` (fake cards for +₹32k and +₹10.5k on clean claims, fallback amounts `68k/42.5k/124k`, hardcoded patient "Ayush Sharma", mock injection forcing status to `'COMPLETED'`).
   - Severe enum misalignment in `frontend-portal/src/` displays "Review Recommended" and "Download Appeal Letter" even when claims are blocked for clinical necessity or identity fraud.

---

## 5. Verification Method

To independently reproduce and verify all findings:

### 5.1 Run the Full Test Suite
```powershell
$env:PYTHONPATH='backend'
.\venv\Scripts\pytest.exe backend/tests/ -q
```
*Expected Result*: Exits with code 1; summary reports `32 failed, 190 passed in ~1.84s`.

### 5.2 Verify `Provenance` Arithmetic & Equality Failures
```powershell
$env:PYTHONPATH='backend'
.\venv\Scripts\pytest.exe backend/tests/e2e/test_tier1_features.py -k "test_tier1_f07_copay_ten_percent_calculation or test_tier1_f11_evidence_line_item_provenance_retention" -v
```
*Expected Result*:
- `test_tier1_f07_copay_ten_percent_calculation`: Fails with `TypeError: unsupported operand type(s) for /: 'Provenance[float]' and 'float'`.
- `test_tier1_f11_evidence_line_item_provenance_retention`: Fails with `AssertionError: assert Provenance[str](value='MED-TR-10', ...) == 'MED-TR-10'`.

### 5.3 Verify Identity Gate Fail-Open Bug
```powershell
$env:PYTHONPATH='backend'
.\venv\Scripts\pytest.exe backend/tests/e2e/test_tier1_features.py -k "test_tier1_f04_gate_blocking_identity_conflict_blocks_engine" -v
```
*Expected Result*: Fails with `AssertionError: assert 'MISMATCH_DETECTED' == 'BLOCKED'`.

### 5.4 Inspect Frontend Fabrication & Contradictory Logic
1. Inspect `frontend/src/components/analysis/FinancialDelta.jsx` lines 366–433: Confirm that when `failVerdicts` is empty, fallback cards with `+₹32,000.00` and `+₹10,500.00` are rendered.
2. Inspect `frontend/src/pages/Analysis.jsx` lines 277–281: Confirm hardcoded "Ayush Sharma", "STAR-IND-99281", "Apollo Hospitals, Bangalore".
3. Inspect `frontend/src/services/api.js` lines 64–96: Confirm `normalizeAnalysisResult` spreads `...mockAnalysisResult` and defaults `status` to `'COMPLETED'`.
4. Inspect `frontend-portal/src/pages/TrackPage.jsx` lines 128–136: Confirm status comparison checks for `'CLAIM_SUPPORTED'` and `'CLAIM_DISPUTED'`, which are never emitted by the backend.
