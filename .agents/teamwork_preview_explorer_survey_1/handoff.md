# Handoff Report: Survey Phase — Architecture, Safety Gates, & Core LLM Boundary Inspection

**Author**: Explorer Survey Agent 1 (`teamwork_preview_explorer_survey_1`)  
**Target Recipient**: Project Orchestrator (`101499e2-9536-4e3a-95f4-a7b372b422ea`)  
**Workspace Root**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`  
**Report File**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_explorer_survey_1\handoff.md`  
**Timestamp**: 2026-09-26T07:55:00Z  

---

## Executive Summary
A comprehensive read-only survey of the ClaimGuard AI codebase was conducted across backend entry points, API routes, Tier 0 safety gates, LLM boundary invocations, forensics engines, schemas, tests, and frontend integration contracts. 
Critical findings include:
1. **Tier 0 Gate Bypass Bug**: In `backend/app/rules/engine.py:44`, Tier 0 gate blocking checks `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]`. Because `check_clinical_firewall` and `check_identity_gate` return `status="BLOCKED"`, `gate_blocked` remains `False`, allowing all downstream financial rules to execute when a clinical rejection or identity conflict occurs.
2. **Fail-Open Identity Gate**: `backend/app/utils/text_matching.py` returns `True` if any identifier or name is absent or empty. If a document lacks patient name or policy number, the Identity Gate silently passes. Cross-document hospital validation is absent at Tier 0.
3. **Document Integrity Disconnected from Safety Gates**: `backend/app/rules/document_integrity.py` is registered as `tier=1` (not Tier 0) and only checks line-item arithmetic. The advanced digital PDF inspection (`PDFInspector`), image ELA (`ELADetector`), and metadata checkers in `backend/app/forensics/` are executed as an afterthought after all rules complete, inspecting only a single document.
4. **VLM Single-Page Dropping & Zero-Value Fallbacks**: `ExtractionPipeline.process_document` (`backend/app/extraction/pipeline.py:79`) only passes the first page (`pages[0]`) to the VLM, discarding subsequent pages in multi-page hospital bills and policies. When VLM is unavailable or errors, the OCR fallback instantiates zeroed dummy objects rather than parsing text.
5. **Frontend Value Fabrication & Overrides**: `frontend/src/services/api.js` silently replaces backend responses with hardcoded mock objects (`mockData.js`) on API errors. `frontend/src/components/analysis/FinancialDelta.jsx` hardcodes defaults (₹42,500 recoverable amount, ₹68,000 insurer paid, ₹14,500 offset) whenever backend values are null or undefined.
6. **Broken Test Suite**: Running `pytest backend/tests/` crashes immediately during collection with `ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'`, blocking `test_new_features.py` and `test_appeal_adversarial.py`. Furthermore, `test_rules.py` fails 3 proportionate deduction tests due to missing `length_of_stay` in test fixtures.

---

## 1. Observations

### 1.1 Test Suite & Collection Errors
Execution of `pytest backend/tests/` via `.\venv\Scripts\pytest backend/tests/` produces immediate failure:
```
=================================== ERRORS ====================================
__________ ERROR collecting backend/tests/test_appeal_adversarial.py __________
ImportError while importing test module '.../backend/tests/test_appeal_adversarial.py'.
backend\tests\test_appeal_adversarial.py:11: in <module>
    from app.rules.appeal_evaluator import AppealEvaluator, AppealEvaluationResult, check_appeal_viability
E   ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator' (backend\app\rules\appeal_evaluator.py)
_____________ ERROR collecting backend/tests/test_new_features.py _____________
ImportError while importing test module '.../backend/tests/test_new_features.py'.
backend\tests\test_new_features.py:13: in <module>
    from app.rules.appeal_evaluator import AppealEvaluator, AppealEvaluationResult, check_appeal_viability
E   ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator' (backend\app\rules\appeal_evaluator.py)
```
When running the remaining test files (`test_rules.py`, `test_forensics.py`, `test_adversarial_challenger_1.py`), 3 out of 33 tests fail:
- `backend/tests/test_rules.py::test_proportionate_deduction_within_limit`: FAILED (`assert 'SKIPPED' == 'PASS'`)
- `backend/tests/test_rules.py::test_proportionate_deduction_mismatch`: FAILED (`assert 'SKIPPED' == 'FAIL'`)
- `backend/tests/test_rules.py::test_proportionate_deduction_correct_deduction`: FAILED (`assert 'SKIPPED' == 'PASS'`)

In `backend/app/rules/appeal_evaluator.py`, lines 9-13:
```python
9:     def evaluate_denial(self, denial_reasons: List[Any], claim_data: Dict[str, Any], policy_data: Dict[str, Any]) -> AppealEvaluationResult:
10:         # We don't have the rule verdicts passed here in the original engine.py...
11:         # Wait, the prompt says to NOT hallucinate probabilities and just return deterministic findings.
12:         # So we will just return a placeholder, and engine.py will populate it properly from rule verdicts.
13:         pass
```
The method `evaluate_denial` returns `None` (`pass`), and `check_appeal_viability` was completely stripped from the module.

### 1.2 End-to-End Pipeline & Architecture Map
The system has two primary ingest routes and an asynchronous execution pipeline:
- **Route 1: Patient Portal Ingestion (`POST /api/portal/submit`)** in `backend/app/api/portal.py:85-181`:
  - Ingests `patient_name`, `patient_email`, `patient_phone`, and up to three files (`hospital_bill`, `insurance_policy`, `rejection_letter`).
  - Stores files on local disk under `data/uploads/{claim_id}/{file_id}.ext`.
  - Creates DB records `Claim(status="PENDING")`, `Document` records, and `AnalysisRun(status="PENDING")`.
  - Spawns an untracked background task via `asyncio.create_task(_trigger_analysis(claim_id, analysis_run_id))` (lines 173, 184-188).
- **Route 2: Multi-step Upload Ingestion (`POST /api/upload`)** in `backend/app/api/upload.py:17-90`:
  - Accepts single file uploads with `document_type` (`HOSPITAL_BILL`, `INSURANCE_POLICY`, `REJECTION_LETTER`) and optional `claim_id`.
  - Uses `save_upload` in `backend/app/utils/file_handler.py`.
  - Inserts `Claim(patient_name="Unknown", status="PENDING")` if no claim_id is provided.
  - Appends to SHA-256 hash-chained audit log via `AuditTrail.log()`.
- **Route 3: Manual Pipeline Trigger (`POST /api/analyze/{claim_id}`)** in `backend/app/api/analysis.py:122-156`:
  - Transitions `Claim.status = "ANALYZING"` and creates `AnalysisRun(status="RUNNING")`.
  - Enqueues `run_analysis_pipeline(claim_id, analysis_run_id)` via FastAPI `BackgroundTasks`.
- **Pipeline Execution Engine (`run_analysis_pipeline`)** in `backend/app/api/analysis.py:17-98`:
  1. Retrieves all `Document` rows for `claim_id`.
  2. Instantiates `ExtractionPipeline` with configured VLM provider (`openai`, `gemini`, or `anthropic`).
  3. Iterates through documents, calling `pipeline.process_document(doc.file_path, expected_type=doc.document_type)`.
  4. Passes extracted objects (`extracted_bill`, `extracted_policy`, `extracted_rejection`) to `RuleEngine().run_all_rules(...)`.
  5. Executes `ForensicsEngine().run(documents, bill=extracted_bill)`.
  6. Updates `AnalysisRun(status="COMPLETED")`, writes `overall_status`, `total_monetary_impact`, and `RuleVerdictRecord` rows.
  7. Updates `Claim.status = "COMPLETED"`.
- **Reporting & Dispute Generation**:
  - `GET /api/reports/{claim_id}` (`backend/app/api/reports.py:12-30`): Returns `AnalysisRun.result_data`.
  - `GET /api/reports/{claim_id}/appeal` (`backend/app/api/reports.py:32-74`): Passes verdicts and schema models to `ReportGenerator().generate_appeal_letter(...)` using Jinja2 template (`backend/app/reports/templates/appeal_template.py`).
  - `GET /api/reports/{claim_id}/audit-trail` (`backend/app/api/reports.py:76-86`): Computes verification status of SHA-256 chained audit logs.

### 1.3 LLM Invocation Points & Boundary Usage
LLM invocations are isolated within `backend/app/extraction/vlm_extractor.py`:
- Classes/Methods:
  - `VLMExtractor._extract_anthropic` (lines 35-79): Uses `client.messages.create(tools=[tool], tool_choice={"type": "tool", "name": tool_name})`.
  - `VLMExtractor._extract_openai` (lines 80-111): Uses `client.beta.chat.completions.parse(response_format=schema_class)`.
  - `VLMExtractor._extract_gemini` (lines 112-131): Uses `model.generate_content([img, prompt_text])` with `response_mime_type="application/json"`.
  - `VLMExtractor.classify_document` (lines 147-187): Zero-shot document classifier prompt.
- Prompt Definitions in `backend/app/extraction/prompts.py`:
  - `BILL_EXTRACTION_PROMPT` (lines 1-9): Instructs LLM to extract every line item, clean currency (₹, Rs., INR), classify into 9 categories, sum line items, and extract dates.
  - `POLICY_EXTRACTION_PROMPT` (lines 11-17): Instructs LLM to extract coverage limits, sub-limits, waiting periods, room rent caps, co-pay %, mental health coverage, and dates.
  - `REJECTION_EXTRACTION_PROMPT` (lines 19-25): Instructs LLM to extract deduction line items, reason codes, cited clauses, amounts claimed/approved/deducted, and categories.
- Boundary Vulnerabilities:
  - **Single Page Truncation** (`backend/app/extraction/pipeline.py:79-81`):
    ```python
    79:                 first_page = pages[0]
    80:                 image_bytes = self._convert_image_to_bytes(first_page)
    81:                 mime_type = "image/png"
    ```
    Only the first page of multi-page documents is sent to the VLM. Multi-page bills (e.g. 5 pages of pharmacy and ICU items) or multi-page insurance policy schedules lose all data on pages 2+.
  - **Zero-Value Hallucinatory Fallback** (`backend/app/extraction/pipeline.py:120-126`):
    When VLM is disabled (no API key) or raises an exception, the system returns:
    ```python
    dummy_data = HospitalBill(bill_id="OCR_FALLBACK", total_amount=0.0, ...)
    dummy_data = InsurancePolicy(policy_number="OCR_FALLBACK", sum_insured=0.0, ...)
    dummy_data = RejectionLetter(rejection_id="OCR_FALLBACK", total_claimed=0.0, ...)
    ```
    There is no OCR text parser populating structured data from `combined_text`. Downstream rules run against zero values.
  - **Absence of Grounded Provenance**: Neither VLM extraction nor OCR extraction captures bounding boxes, character coordinates, or page numbers for individual extracted fields.

### 1.4 Status of Tier 0 Safety Gates

#### A. Clinical Firewall (`backend/app/rules/clinical_firewall.py` & `backend/app/rules/engine.py`)
- Purpose: Prevent automated financial adjudication or rejection when a denial is grounded in clinical judgment (medical necessity, experimental treatment, active line of treatment).
- Implementation: `check_clinical_firewall` (lines 14-70) searches rejection reasons and remarks against regex patterns: `r"medical necessity"`, `r"clinically justified"`, `r"unjustified admission"`, `r"experimental"`, `r"investigational"`, `r"active line of treatment"`, `r"not medically necessary"`, `r"clinical grounds"`, `r"treatment protocol"`, `r"standard of care"`, `r"unwarranted hospitalization"`.
- When triggered, it returns:
  ```python
  RuleVerdict(
      status="BLOCKED",
      rule_name="Clinical Firewall Gate",
      finding="STATUS = BLOCKED\nBLOCK_REASON = CLINICAL_REJECTION_DETECTED\nACTION = FINANCIAL_ENGINE_NOT_EXECUTED..."
  )
  ```
- **Critical Execution Bug in `backend/app/rules/engine.py:44-69`**:
  ```python
  39:         for rule_info in tier_0_rules:
  40:             func = rule_info["function"]
  41:             try:
  42:                 verdict = func(bill, policy, rejection)
  43:                 verdicts.append(verdict)
  44:                 if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:
  45:                     gate_blocked = True
  ...
  58:         for rule_info in other_rules:
  59:             if gate_blocked:
  60:                 verdicts.append(RuleVerdict(status="SKIPPED", finding="Execution skipped because a Gatekeeper (Tier 0) rule failed."))
  61:             else:
  62:                 func = rule_info["function"]
  63:                 verdict = func(bill, policy, rejection)
  64:                 verdicts.append(verdict)
  ```
  `check_clinical_firewall` returns `status="BLOCKED"`. `"BLOCKED"` is **not** in `["NEEDS_REVIEW", "FAIL", "WARNING"]`!
  Consequently, `gate_blocked` remains `False`, and lines 58-74 execute all downstream financial rules (proportionate deduction, waiting periods, etc.), directly violating R1 and R2.

#### B. Identity Verification Gate (`backend/app/rules/identity_gate.py` & `backend/app/utils/text_matching.py`)
- Implementation: `check_identity_gate` (registered `tier=0`) compares:
  - Policy number between policy and rejection using `match_ids()`.
  - Patient name between bill and policy, and bill and rejection using `match_names()`.
  - Claim date against policy period using `is_date_in_range()`.
- **Critical Fail-Open Bug in `backend/app/utils/text_matching.py`**:
  ```python
  9: def match_ids(id1: str, id2: str) -> bool:
  10:     """Matches two identifiers strictly."""
  11:     if not id1 or not id2:
  12:         return True # Cannot evaluate, assume pass
  ...
  21: def match_names(name1: str, name2: str, threshold: float = 0.5) -> bool:
  26:     if not name1 or not name2:
  27:         return True # Cannot evaluate
  ```
  If an extracted document is missing the patient name or policy number, `match_ids` and `match_names` return `True`.
  In `identity_gate.py:106`:
  ```python
  finding="MATCH: Identity markers and dates are consistent or missing (Insufficient Evidence). Proceeding."
  ```
  Missing identity markers result in a `PASS` instead of halting the system or routing to human review (`NEEDS_REVIEW`).
- **Missing Hospital Identity Verification**:
  Cross-document verification of hospital details (hospital name, ROHINI registration, address) is completely missing from `identity_gate.py`.
  The only hospital check is in `backend/app/rules/authenticity_check.py:6-15`, which is registered at `tier=1` and uses mock string checks (`"fake"`, `"test"` in name).
- **Family Floater & Dependent Handling Gap**:
  In health policies where the policyholder is a parent/spouse and the patient is a child/dependent, `match_names(name_bill, name_policy)` fails, resulting in a false-positive `BLOCKED` because `InsurancePolicy` lacks a list of insured beneficiaries.

#### C. Document Integrity Gate
- Implementation in `backend/app/rules/document_integrity.py`:
  - Registered as `tier=1`, not `tier=0`!
  - Does not check file tampering, checksums, digital signatures, or duplicate claim submissions.
  - Only computes line items arithmetic difference:
    ```python
    30:         if difference > 10.0:
    31:             return RuleVerdict(status="WARNING", rule_name="Document Arithmetic Integrity", ...)
    ```
    Returns `WARNING` instead of `BLOCKED`.
- Detached Forensics Suite (`backend/app/forensics/`):
  - Advanced forensic modules exist (`PDFInspector` for incremental updates and suspicious editing tools, `ELADetector` for JPEG resave anomalies, `MetadataChecker` for creator tools).
  - However, in `backend/app/api/analysis.py:50-61`, `ForensicsEngine().run()` is called **after** `RuleEngine.run_all_rules()`.
  - In `ForensicsEngine.run()` (`backend/app/forensics/engine.py:112-132`), only one document (`target_path`) is analyzed (defaulting to hospital bill). Tampering in policy or rejection documents is never checked.
  - Forensic results are stored in `analysis_run.result_data["forensics"]` without any gatekeeper power to halt financial adjudication.

### 1.5 Module Boundaries & Data Contracts

#### Status Enum Inconsistency
A severe mismatch exists across backend schemas, rule engine outputs, portal APIs, and frontend views:

| Component | Status Values Produced or Expected |
|---|---|
| `RuleEngine` (`backend/app/rules/engine.py:90-96`) | `BLOCKED`, `MISMATCH_DETECTED`, `REVIEW_RECOMMENDED`, `NO_MISMATCH_FOUND` |
| `AnalysisResult` Schema (`backend/app/schemas/analysis_result.py:25`) | `NO_MISMATCH_FOUND`, `MISMATCH_DETECTED`, `REVIEW_RECOMMENDED`, `EXTRACTION_FAILED`, `BLOCKED` |
| `Portal API` (`backend/app/api/portal.py:259-278`) | `CLAIM_SUPPORTED`, `CLAIM_DISPUTED`, `PARTIAL_DISPUTE`, `NEEDS_REVIEW` |
| Patient Portal UI (`frontend-portal/.../TrackPage.jsx:34, 130`) | `CLAIM_SUPPORTED`, `CLAIM_DISPUTED`, default fallback |

Because `RuleEngine` outputs `MISMATCH_DETECTED`, `portal.py`'s `_generate_plain_summary` fails all branch conditions and outputs the generic string:
`"Your claim has been analyzed. Please review the detailed findings below."`
Similarly, `TrackPage.jsx` defaults to "Review Recommended" badge regardless of violations detected.

### 1.6 Frontend Calculation Overrides & Fallback Fabrications
Inspection of `frontend/src/services/api.js` and `frontend/src/components/analysis/FinancialDelta.jsx` reveals client-side data fabrication:
1. **Mock Fallback on Network / API Failure** (`frontend/src/services/api.js:64-72, 166-169`):
   ```javascript
   export const getAnalysisResult = async (claimId) => {
     try {
       const response = await api.get(`/analyze/${claimId}/result`);
       return normalizeAnalysisResult(response.data, claimId);
     } catch (error) {
       console.warn('API /analyze result fallback for claim:', claimId);
       return normalizeAnalysisResult(null, claimId);
     }
   };
   ```
   When `response.data` is null or the call fails, `normalizeAnalysisResult` returns `mockAnalysisResult` from `mockData.js`, displaying false financial amounts (₹42,500 recovery on demo claim) to the user.
2. **Hardcoded Financial Defaults in FinancialDelta.jsx** (`frontend/src/components/analysis/FinancialDelta.jsx:49-65`):
   ```javascript
   const insurerPaid = Number(result.total_insurer_calculation ?? result.approved_amount ?? 68000);
   const recoverableAmount = Number(result.total_monetary_impact ?? 42500);
   const correctAllowable = Number(result.total_correct_calculation ?? (insurerPaid + recoverableAmount));
   const totalClaimed = Number(result.total_claimed ?? claim?.impact ?? (insurerPaid + recoverableAmount + 14500));
   ```
   If backend calculation fields are missing or not passed, the frontend injects `42500`, `68000`, and `+ 14500`, fabricating numbers out of thin air in direct violation of R1.

### 1.7 Adjudication & Financial Rules
1. **Proportionate Deduction Rule (`backend/app/rules/proportionate_deduction.py`)**:
   - `check_proportionate_deduction` checks `if actual_room_rate is None or length_of_stay is None or length_of_stay <= 0: return RuleVerdict(status="SKIPPED", ...)`.
   - In `backend/tests/test_rules.py`, `get_base_bill()` sets neither `admission_date` nor `discharge_date`, causing `length_of_stay` to evaluate to `None`, which immediately breaks 3 tests in `test_rules.py`.
   - Medical exclusion handling: IRDAI guidelines mandate that proportionate deductions cannot be applied to ICU/ICCU charges, cost of pharmacy/medicines, implants, or diagnostic tests. In line 53, the code only filters `is_linked or cat in ['ROOM', 'NURSING']`.
2. **Waiting Period Rule (`backend/app/rules/waiting_period.py`)**:
   - Line 34: `wp_required_days = getattr(policy, 'ped_waiting_period_months', 48) * 30.44`. Uses floating multiplication rather than calendar day/month calculations.
   - When the rule fails (`delta_days > wp_required_days`), line 48 returns `RuleVerdict(status="FAIL")` **without setting `monetary_impact`**, defaulting impact to 0.0 in the schema.
3. **Continuous Coverage Moratorium Rule (`backend/app/rules/clause_timeline.py`)**:
   - Checks 60-month moratorium per IRDAI Master Circular 2024.
   - Line 59: `if claim_date > moratorium_completion_date:`. If the claim occurs on the exact boundary date (`==`), it does not trigger (`>`).
   - Line 72: On failure, returns `status="FAIL"` but does **not** set `monetary_impact`.
   - In `backend/app/schemas/insurance_policy.py:52-59`, `is_moratorium_expired` uses `(days / 30.44) >= self.moratorium_period_months` calculated against `self.policy_start_date` rather than initial inception date plus portability credits.

---

## 2. Logic Chain

1. **Observation 1.1** establishes that `backend/app/rules/appeal_evaluator.py` is missing `check_appeal_viability`, causing `pytest` to fail during collection on two test modules (`test_appeal_adversarial.py`, `test_new_features.py`).
2. **Observation 1.1 & 1.7** establish that `test_rules.py` fails 3 tests because `HospitalBill.length_of_stay` requires valid admission/discharge dates, but test fixtures omit them, causing `check_proportionate_deduction` to return `SKIPPED`.
   - *Inference*: The repository is currently in a broken test state where regressions cannot be detected until the import errors and fixture mismatches are corrected.
3. **Observation 1.4A** demonstrates that `check_clinical_firewall` returns `status="BLOCKED"`, but `RuleEngine.run_all_rules` at line 44 only checks `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]` to set `gate_blocked = True`.
   - *Inference*: `gate_blocked` remains `False`. The execution loop in lines 58-74 proceeds to run all downstream rules.
   - *Inference*: Clinical necessity denials are actively analyzed by financial calculation rules rather than being halted, directly violating R1 and R2.
4. **Observation 1.4B** reveals that `match_ids` and `match_names` in `text_matching.py` return `True` when inputs are empty or missing.
   - *Inference*: If a document extraction fails to extract a patient name or policy number, the Identity Verification Gate treats missing data as a match and passes the claim.
   - *Inference*: The system fails open instead of adhering to the non-negotiable rule that ambiguity must yield `NEEDS_REVIEW` or `BLOCKED`.
5. **Observation 1.4C** demonstrates that `document_integrity.py` is registered at `tier=1` and only checks bill line-item arithmetic, while `ForensicsEngine` is decoupled from safety gates and executed after rule evaluation.
   - *Inference*: Tier 0 Document Integrity Gate does not exist in the execution flow. A forged or tampered PDF undergoes full financial adjudication without gatekeeper interception.
6. **Observation 1.3** establishes that `ExtractionPipeline.process_document` only submits `pages[0]` to the VLM and substitutes zero-value dummy models when VLM is absent or fails.
   - *Inference*: Multi-page bills and policies lose critical pages, leading to false arithmetic imbalances, missed room rent limits, and spurious rule verdicts.
7. **Observation 1.6** demonstrates that the frontend substitutes mock data on API errors and injects hardcoded fallback values (`recoverableAmount = 42500`, `insurerPaid = 68000`).
   - *Inference*: The frontend actively fabricates financial numbers when the backend is offline or returns incomplete data, directly violating the R1 principle that frontend calculations must never override backend calculations.

---

## 3. Caveats
1. **Dynamic Runtime Behavior of External VLMs**: External API calls to OpenAI, Gemini, or Anthropic were not executed during this read-only survey to prevent unbudgeted API consumption and adhere to offline execution constraints.
2. **Frontend UI Rendering**: The survey analyzed frontend code structure and API contracts via static code analysis (`frontend/src/` and `frontend-portal/src/`). Node.js UI rendering and Vite dev servers were not executed.
3. **No Caveats on Architecture**: All backend execution paths, rules, schemas, entry points, and test failures were directly verified in source code.

---

## 4. Conclusion & Prioritized Inventory of Gaps

The ClaimGuard AI platform possesses a strong modular foundation (rich schemas, comprehensive forensics libraries, and regulatory citations), but exhibits severe architectural disconnects, safety gate bypasses, and contract desynchronizations:

### Prioritized Defect & Gap Matrix

| Priority | Component | Specific Defect | Direct Impact |
|---|---|---|---|
| **P0 - Blocker** | `backend/app/rules/engine.py:44` | `"BLOCKED"` status omitted from `gate_blocked` check list | Tier 0 Clinical Firewall and Identity Gate do not halt financial execution. |
| **P0 - Blocker** | `backend/app/rules/appeal_evaluator.py` | `check_appeal_viability` missing, `evaluate_denial` is a stub | Entire test suite fails during collection (`pytest` cannot run). |
| **P0 - Safety** | `backend/app/utils/text_matching.py:11,26` | `match_ids` and `match_names` return `True` on empty/missing values | Identity Gate fails open on missing data instead of flagging `NEEDS_REVIEW`. |
| **P0 - Safety** | `backend/app/rules/document_integrity.py` | Document integrity is `tier=1` (arithmetic only); forensics decoupled | Tampered PDFs and forged documents pass through financial adjudication unblocked. |
| **P1 - Integrity** | `frontend/src/components/analysis/FinancialDelta.jsx:52,57` | Hardcoded fallback numbers (42500, 68000, 14500) | Frontend fabricates financial calculations when backend data is absent. |
| **P1 - Integrity** | `frontend/src/services/api.js:133,168,222` | API error catches silently return `mockData.js` | Users are presented with simulated claims and recoveries during system errors. |
| **P1 - Extraction** | `backend/app/extraction/pipeline.py:79` | Multi-page documents truncated to `pages[0]` | All line items and policy clauses on pages 2+ are dropped from VLM extraction. |
| **P1 - Extraction** | `backend/app/extraction/pipeline.py:121` | OCR fallback produces zeroed dummy models | Complete pipeline failure when VLM is disabled or API errors occur. |
| **P2 - Contracts** | `engine.py` vs `portal.py` vs UI | Status enum mismatch (`MISMATCH_DETECTED` vs `CLAIM_SUPPORTED`) | Patient portal displays generic text and misidentifies claim violation states. |
| **P2 - Rules** | `waiting_period.py`, `clause_timeline.py` | `monetary_impact` not calculated or returned on `FAIL` | Monetary impact defaults to ₹0 despite detected violations. |
| **P2 - Tests** | `backend/tests/test_rules.py` | `get_base_bill()` fixture lacks admission/discharge dates | Proportionate deduction unit tests fail on missing `length_of_stay`. |

---

## 5. Verification Method

To independently verify all findings and reproduce the observed failures, execute the following commands in the workspace root (`C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`):

### 1. Test Suite Collection Failure Reproduction
```powershell
.\venv\Scripts\pytest backend/tests/
```
**Expected Invalidation Condition**: Pytest should exit with code 1 and display `ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'`.

### 2. Isolated Rule Test Failures Reproduction
```powershell
.\venv\Scripts\pytest backend/tests/test_rules.py
```
**Expected Invalidation Condition**: 3 tests fail in `test_proportionate_deduction_*` with `AssertionError: assert 'SKIPPED' == 'PASS'` and `assert 'SKIPPED' == 'FAIL'`.

### 3. Inspection of Codebase Gate Bypass Bug
Inspect `backend/app/rules/engine.py` lines 42-45:
```python
verdict = func(bill, policy, rejection)
verdicts.append(verdict)
if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:
    gate_blocked = True
```
Compare with `backend/app/rules/clinical_firewall.py` line 51:
```python
return RuleVerdict(status="BLOCKED", rule_name="Clinical Firewall Gate", ...)
```
Verify that `status="BLOCKED"` is not handled in line 44, allowing execution to proceed into `other_rules`.

### 4. Inspection of Fail-Open Text Matching
Inspect `backend/app/utils/text_matching.py` lines 11-12 and 26-27:
```python
if not id1 or not id2:
    return True # Cannot evaluate, assume pass
```
Confirm that missing identity markers evaluate to `True`.

### 5. Inspection of Frontend Value Fabrication
Inspect `frontend/src/components/analysis/FinancialDelta.jsx` lines 49-65:
Confirm fallback default values `68000`, `42500`, and `+ 14500` applied to missing properties.
Inspect `frontend/src/services/api.js` lines 166-169 and 64-72:
Confirm fallback to `mockAnalysisResult` upon API errors.
