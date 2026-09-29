# Specification Mining & Regulatory Gap Analysis Report: Survey Phase 2

**Agent**: `teamwork_preview_spec_miner_survey_2`  
**Date**: 2026-09-26T07:50:00Z  
**Workspace**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`  
**Target File**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2\handoff.md`  
**Orchestrator Parent ID**: `101499e2-9536-4e3a-95f4-a7b372b422ea`

---

## Executive Summary

As the Specification Miner for Survey Phase 2, an exhaustive inspection and empirical probing of the ClaimGuard AI codebase was conducted covering:
1. Deterministic financial calculations (base deductions, co-pay, room rent capping, ICU capping, proportionate deductions, float precision, frontend overrides).
2. Regulatory verification logic (IRDAI May 2024 Master Circular, 60-calendar-month moratorium, Section 45 Insurance Act 1938, continuous coverage & portability credits, waiting periods, mental health parity under MHCA 2017).
3. Proportionate deduction loopholes (associated medical expenses vs room rent capping, 1.15x trigger threshold, double-deduction arithmetic bugs).
4. Ambiguity, uncertainty & human review triggers (`NEEDS_REVIEW` absence, silent skipping, silent passing, fallback dummy injection).

### Critical Discoveries & Vulnerabilities:
- **Rule Engine Tier 0 Bypass Bug**: Tier 0 gates (`identity_gate.py`, `clinical_firewall.py`) return `status="BLOCKED"`. However, `engine.py` line 44 checks `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:`, completely missing `"BLOCKED"`. As a result, `gate_blocked` remains `False`, and all downstream financial calculation and regulatory rules execute on blocked claims!
- **Proportionate Deduction Double Counting Bug**: In `proportionate_deduction.py`, `room_linked_items` includes items with `category == 'ROOM'`. The engine calculates `total_room_excess` and also applies the proportionate reduction factor `(1 - limit / rate)` to all room-linked items (which includes room charges). Then line 72 computes `expected_total_deduction = total_room_excess + proportionate_reduction + misc_deductions`, doubling the room rent deduction!
- **Arbitrary 1.15x Threshold**: `proportionate_deduction.py` line 44 artificially requires room rent to exceed 1.15x (115%) of the policy limit before applying proportionate deductions. IRDAI regulations have no 1.15x threshold; proportionate deduction applies whenever room rent exceeds the eligible limit, but is strictly restricted to associated medical expenses.
- **Moratorium Boundary & Disguised Rejection Gaps**: In `clause_timeline.py`, claims occurring on the exact 60-month anniversary return `status="PASS"` (upholding rejection) because of strict `>` comparison. Furthermore, any rejection using terms like "suppression of material facts", "clause 4.1", or "omission of health history" (without exact substring "non-disclosure" or category "PRE_EXISTING") is silently `SKIPPED`. Enhanced Sum Insured (ESI) moratorium tracking is completely unimplemented.
- **Zero Implementation of `NEEDS_REVIEW` in Rules**: Not a single rule in `backend/app/rules/` ever emits `NEEDS_REVIEW`. Whenever data is missing, unparsed, or ambiguous, rules either emit `SKIPPED` (which does not trigger mismatch alerts) or `PASS` (e.g., identity gate passes if policy numbers or names are missing).
- **Silent Dummy Injection on Extraction Failure**: When VLM extraction fails or is unavailable, `pipeline.py` inserts dummy models with hardcoded fake dates ("2023-01-01", "2024-01-01") and "Unknown" strings, allowing unverified claims to silently pass through rules.
- **Frontend Fallback Mock Fabrication**: In `frontend/src/components/analysis/FinancialDelta.jsx`, the UI hardcodes fallback amounts (₹68,000, ₹42,500, ₹124,000, +₹32,000, +₹10,500) whenever backend fields are absent, directly violating the single-source-of-truth requirement.

---

## 1. Observation

Direct observations from source inspection, git commits, schema definitions, and empirical probe execution:

### 1.1 Codebase Structure and File Locations
- **Rule Engine & Rules**:
  - `backend/app/rules/engine.py` (Lines 1–156): Tier separation logic, gate blocking loop, overall status aggregation.
  - `backend/app/rules/proportionate_deduction.py` (Lines 1–106): Proportionate deduction formula, room excess, 1.15x threshold.
  - `backend/app/rules/clause_timeline.py` (Lines 1–91): 60-month moratorium, date comparison, non-disclosure keyword matching.
  - `backend/app/rules/waiting_period.py` (Lines 1–67): Initial 30-day, specific disease, PED waiting period evaluation.
  - `backend/app/rules/mental_health_parity.py` (Lines 1–44): Section 21(4) Mental Healthcare Act parity evaluation.
  - `backend/app/rules/identity_gate.py` (Lines 1–112): Tier 0 cross-document name, policy number, date range matching.
  - `backend/app/rules/clinical_firewall.py` (Lines 1–70): Tier 0 medical necessity regex matching.
  - `backend/app/rules/document_integrity.py` (Lines 1–51): Tier 1 bill line item summation vs gross total.
  - `backend/app/rules/authenticity_check.py` (Lines 1–80): Tier 1 ROHINI and IIB registry mock verification.
  - `backend/app/rules/appeal_evaluator.py` (Lines 1–55): Rule verdicts to appeal viability and Ombudsman risk mapping.
- **Schemas**:
  - `backend/app/schemas/hospital_bill.py` (Lines 1–74): `HospitalBill`, `BillLineItem`, arithmetic validator, computed properties (`length_of_stay`, `room_charges_per_day`).
  - `backend/app/schemas/insurance_policy.py` (Lines 1–74): `InsurancePolicy`, `WaitingPeriodConfig`, `SubLimit`, helper methods (`is_moratorium_expired`, `get_waiting_period_status`).
  - `backend/app/schemas/rejection_letter.py` (Lines 1–36): `RejectionLetter`, `RejectionReason`, settlement types.
  - `backend/app/schemas/analysis_result.py` (Lines 1–49): `RuleVerdict`, `AnalysisResult`, status literals.
- **API & Pipeline**:
  - `backend/app/api/analysis.py` (Lines 1–192): Extraction pipeline orchestration, rule engine execution, DB persistence.
  - `backend/app/api/portal.py` (Lines 1–279): WebSocket real-time claim tracker, `/api/portal/status/{claim_id}` summary generator.
  - `backend/app/extraction/pipeline.py` (Lines 1–149): Document preparation, OCR/VLM fallback, dummy model generation.
- **Frontend**:
  - `frontend/src/components/analysis/FinancialDelta.jsx` (Lines 1–440): Metric cards, capital allocation waterfall, discrepancy cards.
  - `frontend/src/pages/Analysis.jsx` (Lines 1–510): 4-tab dossier workspace, status polling, verdict filtering.
  - `frontend-portal/src/pages/TrackPage.jsx` (Lines 1–368): Consumer claim tracker, stage progress, recovery metric display.

### 1.2 Verbatim Errors & Empirical Probe Findings

#### A. Broken Test Suite Collection
Running `venv\Scripts\pytest backend\tests` exited with code 1:
```
ERROR backend/tests/test_appeal_adversarial.py - ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'
ERROR backend/tests/test_new_features.py - ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'
```
Root Cause: An earlier refactoring of `appeal_evaluator.py` deleted the standalone `check_appeal_viability` function that was registered in the rule registry and expected by both test suites.

#### B. Test Failures in `backend/tests/test_rules.py`
Running `venv\Scripts\pytest backend\tests\test_rules.py` produced 3 test failures:
```
FAILED backend/tests/test_rules.py::test_proportionate_deduction_within_limit - assert 'SKIPPED' == 'PASS'
FAILED backend/tests/test_rules.py::test_proportionate_deduction_mismatch - assert 'SKIPPED' == 'FAIL'
FAILED backend/tests/test_rules.py::test_proportionate_deduction_correct_deduction - assert 'SKIPPED' == 'PASS'
```
Root Cause: In `HospitalBill`, `length_of_stay` is computed from `admission_date` and `discharge_date`. The test fixtures created bills without dates. In `proportionate_deduction.py:29-36`, if `length_of_stay is None`, the rule returns `SKIPPED` rather than deriving the duration from the room line item quantity.

#### C. Empirical Probe 1: Proportionate Deduction Double-Counting
Executing Probe 1 with:
- Room Rate: ₹6,000/day, Policy Limit: ₹5,000/day, Stay: 2 days (Room Total: ₹12,000)
- Nursing: ₹1,000/day, 2 days (Total: ₹2,000)
- Doctor Consultation: ₹1,500/day, 2 days (Total: ₹3,000)
- Actual Room Excess = `(6000 - 5000) * 2 = ₹2,000`
- Proportionate factor = `1 - 5000/6000 = 1/6`
- Legitimate deduction should be: Room Excess (₹2,000) + Nursing Reduction (`2000 * 1/6 = ₹333.33`) = **₹2,333.33**.
**Observed Behavior from `check_proportionate_deduction`**:
```
Expected Proportionate Reduction: ₹2333.33
Total Legitimate Deduction (including non-medical): ₹4333.33
Insurer Deducted: ₹2333.33
Verdict Status: PASS (Monetary Impact: 0.0)
```
The rule added `total_room_excess` (₹2,000) to `proportionate_reduction` (₹2,333.33, which already included the ₹2,000 room charge reduction), computing an erroneous legitimate deduction of ₹4,333.33 instead of ₹2,333.33.

#### D. Empirical Probe 2: 1.15x Threshold Anomaly
Executing Probe 2 with room rate = ₹5,500/day against a ₹5,000/day limit (a 1.10x ratio):
```
Finding: Actual Rate: ₹5500.0/day. Eligible: ₹5000.0/day. Room Excess: ₹1000.00. 
Trigger Check: Ratio 1.10 does NOT strictly exceed 1.15 threshold. Proportionate reduction is ZERO.
Expected Proportionate Reduction: ₹0.00. Total Legitimate Deduction: ₹1000.00.
```
Proportionate deduction on associated medical charges was completely blocked because the ratio was not strictly > 1.15.

#### E. Empirical Probe 3: Moratorium Boundary & Disguised Denial
Executing Probe 3:
- Inception date: `2020-01-01`, Claim date: `2025-01-01` (exact 60 calendar months).
- Output: `status=PASS, finding: Claim date (2025-01-01) is before moratorium completion (2025-01-01). Rejection is temporally valid.`
- When claim date was `2025-01-02` (60 months + 1 day), output was `status=FAIL`.
- When rejection cited "Suppression of material medical facts regarding hypertension", output was `status=SKIPPED, finding: Rejection does not cite non-disclosure or pre-existing conditions.`

#### F. Empirical Probe 4: Initial 30-Day Waiting Period Off-by-One
Executing Probe 4:
- Policy Start: `2024-01-01`, Claim Date: `2024-01-31` (day 30). Initial waiting period: 30 days.
- Output: `status=PASS, finding: Rejection is valid, INITIAL waiting period has not expired. Days elapsed: 30.`

#### G. Empirical Probe 5: Tier 0 Gate Blocking Leak
Executing Probe 5 with mismatched patient identity:
- `Cross-Document Identity Gate` returned `status="BLOCKED"`.
- RuleEngine summary output: `ACTION = FINANCIAL_ENGINE_NOT_EXECUTED. Blocked by Tier 0 rule: Cross-Document Identity Gate.`
- However, all subsequent rules executed:
  `Proportionate Deduction Rule: PASS`, `Document Arithmetic Integrity: WARNING`, `Authenticity Verification Check: FAIL`.
- Cause: `engine.py` line 44 checks `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:`. Because `identity_gate.py` returns `"BLOCKED"`, `gate_blocked` remained `False`.

#### H. Empirical Probe 6: Arithmetic Tampering Maps to `NO_MISMATCH_FOUND`
Executing Probe 6 with a bill having `total_amount = 100000.0` but line items summing to `10000.0` (a ₹90,000 arithmetic tampering discrepancy):
```
Overall Status for tampered bill: NO_MISMATCH_FOUND
Document Arithmetic Integrity status: WARNING
Document Arithmetic Integrity finding: Arithmetic inconsistency detected. Sum of line items (₹10000.00) does not match stated gross bill (₹100000.00). Difference: ₹90000.00.
```
Because `Document Arithmetic Integrity` emits `WARNING` and not `FAIL`, `RuleEngine` evaluated `overall_status = "NO_MISMATCH_FOUND"`.

---

## 2. Logic Chain

From the direct observations, the following causal reasoning explains system vulnerabilities:

1. **Gate Bypass Logic Chain**:
   - `identity_gate.py:45,65,79,99` and `clinical_firewall.py:51` explicitly return `RuleVerdict(status="BLOCKED", ...)`.
   - `engine.py:44` checks: `if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]: gate_blocked = True`.
   - Since `"BLOCKED"` is not in that list, `gate_blocked` remains `False`.
   - Downstream loop `for rule_info in other_rules:` checks `if gate_blocked: ... else: execute rule`.
   - Therefore, financial and policy rules execute completely on identity-mismatched or clinical-necessity claims, violating R1 and R2.

2. **Proportionate Deduction Double Counting Logic Chain**:
   - In `proportionate_deduction.py:50-54`, `room_linked_items` gathers items where `is_room_linked` is True or `cat in ['ROOM', 'NURSING']`.
   - In line 39-40, `total_room_excess = (actual_room_rate - policy_room_limit) * length_of_stay`.
   - In line 60-61, `deduction_percentage = 1.0 - (policy_room_limit / actual_room_rate)` and `proportionate_reduction = room_linked_sum * deduction_percentage`.
   - Since `room_linked_sum` includes the room item (`actual_room_rate * length_of_stay`), `proportionate_reduction` already contains `(actual_room_rate * length_of_stay) * (1 - policy_room_limit / actual_room_rate) = total_room_excess`.
   - In line 72, `expected_total_deduction = total_room_excess + proportionate_reduction + misc_deductions`.
   - This sums `total_room_excess` twice, calculating an artificially inflated legitimate deduction and erroneously clearing insurers of underpayments.

3. **Silent Defaults Logic Chain**:
   - Every rule in `backend/app/rules/` handles missing inputs by returning `status="SKIPPED"` or `status="PASS"`.
   - `engine.py:89-96` determines `overall_status`: if no rule returned `FAIL` or `BLOCKED` (and no rule ever returns `NEEDS_REVIEW`), it falls through to `NO_MISMATCH_FOUND`.
   - When OCR/VLM fails, `pipeline.py:120-126` injects dummy models with `Unknown` strings and fake dates.
   - `identity_gate.py:33,53` checks `pol_num_policy.upper() != "UNKNOWN"`. If "UNKNOWN", it skips checks and returns `status="PASS"`.
   - An empty, unreadable, or missing document produces 0 failures, 0 reviews, and receives `NO_MISMATCH_FOUND`.

4. **Frontend Override Logic Chain**:
   - `FinancialDelta.jsx:49-75` initializes `insurerPaid`, `recoverableAmount`, and `billedAmount` using the nullish coalescing operator (`??`) and logical OR (`||`) with hardcoded integers (68000, 42500, 124000).
   - If the backend returns 0 or empty fields, the UI displays these fictional amounts and renders hardcoded discrepancy cards.
   - As a result, the frontend acts as a parallel calculation engine rather than a passive display of backend ground truth.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Financial Calculation | Proportionate Room Rent Deduction | Calculates legitimate deduction on room-linked charges when room rent exceeds policy cap | `HospitalBill`, `InsurancePolicy`, `RejectionLetter` | `RuleVerdict` (`status`, `correct_calculation`, `monetary_impact`) | Skips if stay/rate missing; double-counts room excess if room in linked items | `backend/app/rules/proportionate_deduction.py:13` |
| 2 | Financial Calculation | Daily Room Excess Surcharge | Calculates non-admissible excess room rent per day multiplied by length of stay | `bill.room_charges_per_day`, `policy.room_rent_limit_per_day`, `bill.length_of_stay` | `total_room_excess` (float) | Defaults to 0.0 if actual <= limit | `backend/app/rules/proportionate_deduction.py:39` |
| 3 | Regulatory Verification | 60-Month Moratorium Enforcer | Bars insurer from denying claims for non-disclosure after 60 continuous months (IRDAI May 2024 / Sec 45) | Policy inception date, portability months, claim date, rejection reasons | `RuleVerdict` (`FAIL` if claim > 60m, `PASS` if before) | Skips if dates missing or if rejection uses alternate suppression wording | `backend/app/rules/clause_timeline.py:15` |
| 4 | Regulatory Verification | Portability Credit Offset | Deducts ported tenure months from 60-month moratorium requirement | `policy.portability_credits_months`, `policy.moratorium_period_months` | `months_needed_on_current` | Defaults to 0 if None; completely ignored in waiting_period.py | `backend/app/rules/clause_timeline.py:51` |
| 5 | Regulatory Verification | Waiting Period Verifier | Checks elapsed policy days against Initial (30d), Specific (24m), or PED (48m) waiting periods | Policy start date, claim date, rejection reasons | `RuleVerdict` (`FAIL` if period expired, `PASS` if within) | Uses 30.44-day float multiplier; defaults to PED 48m on unclassified strings | `backend/app/rules/waiting_period.py:14` |
| 6 | Regulatory Verification | Mental Health Parity Check | Enforces Section 21(4) Mental Healthcare Act 2017 prohibiting discrimination against psychiatric care | Rejection reason category, bill diagnosis keywords | `RuleVerdict` (`FAIL` with monetary impact = claimed - approved) | Skips if no keywords match; does not audit other bill deductions | `backend/app/rules/mental_health_parity.py:13` |
| 7 | Safety Gates | Cross-Document Identity Gate (Tier 0) | Halts financial calculation if patient name, policy number, or dates conflict across docs | Policy number, patient name, coverage date range across Bill, Policy, Rejection | `RuleVerdict` (`status="BLOCKED"`) | Silently passes if fields are missing or 'UNKNOWN' | `backend/app/rules/identity_gate.py:27` |
| 8 | Safety Gates | Clinical Firewall Gate (Tier 0) | Halts financial verification if rejection is based on medical necessity / clinical judgement | Rejection reasons and remarks text | `RuleVerdict` (`status="BLOCKED"`) | Case-insensitive regex; misses clinical terms not in hardcoded 11-phrase list | `backend/app/rules/clinical_firewall.py:14` |
| 9 | Safety Gates | Document Arithmetic Integrity | Validates that sum of itemized line item amounts matches stated gross bill total | `bill.line_items`, `bill.total_amount` | `RuleVerdict` (`PASS` or `WARNING`) | Emits `WARNING` on difference > 10 INR; engine maps all-warning to `NO_MISMATCH_FOUND` | `backend/app/rules/document_integrity.py:13` |
| 10 | Regulatory Verification | Provider & Policy Authenticity Check | Mocks ROHINI registry lookup for hospitals and IIB registry for policy status | `bill.hospital_name`, `policy.policy_number` | `RuleVerdict` (`PASS` or `FAIL` with total bill impact) | Fails on strings containing 'test', 'dummy', 'fake', '000', '123' | `backend/app/rules/authenticity_check.py:34` |
| 11 | Schema & Validation | Bill-Level Arithmetic Validator | Pydantic model validator verifying sum of line item amounts matches subtotal | `HospitalBill.line_items`, `HospitalBill.subtotal` | `arithmetic_verified` (bool) | Uses float `abs <= 1.0`; does not verify tax, discount, or net_payable | `backend/app/schemas/hospital_bill.py:40` |
| 12 | Schema & Validation | Length of Stay Computation | Computed property deriving inpatient days from admission and discharge strings | `admission_date`, `discharge_date` | `length_of_stay` (Optional[int]) | Returns None if date parsing fails; does not fall back to room item quantity | `backend/app/schemas/hospital_bill.py:54` |
| 13 | Schema & Validation | Daily Room Charge Derivation | Extracts room unit rate from line items marked with category 'ROOM' | `HospitalBill.line_items` | `room_charges_per_day` (Optional[float]) | Returns None if no item has category ROOM | `backend/app/schemas/hospital_bill.py:46` |
| 14 | Execution Engine | Tiered Rule Engine Orchestration | Executes Tier 0 gatekeepers followed by Tier 1+ rules and computes overall status | `HospitalBill`, `InsurancePolicy`, `RejectionLetter` | `AnalysisResult` | Ignores `status="BLOCKED"` in gate check loop; runs all rules anyway | `backend/app/rules/engine.py:28` |
| 15 | Appeal & Escalation | Statutory Appeal Evaluator | Maps failed rule verdicts to appeal grounds, statutory citations, and action plan | `List[RuleVerdict]` | `AppealEvaluationResult` | Returns 100% risk if any rule fails, 0% if none; method `evaluate_denial` is empty | `backend/app/rules/appeal_evaluator.py:15` |
| 16 | Forensic Billing | Tariff & LOS Anomaly Detector | Compares bill charges against CGHS 2024 benchmarks and typical LOS durations | `HospitalBill` | `List[BillAnomalyFlag]` | Flags items >2x or >3x CGHS; skips if diagnosis or LOS missing | `backend/app/forensics/bill_anomaly.py:29` |
| 17 | Forensic Billing | Clinical Consistency Checker | Cross-references diagnosis against expected / unexpected medicines and tests | `HospitalBill` | `List[ConsistencyFlag]` | Flags chronic medications (e.g. insulin for diabetic cataract patient) as contradictory | `backend/app/forensics/consistency_checker.py:33` |
| 18 | Forensic Fraud | Additive Composite Fraud Risk Scorer | Computes calibrated risk score (0–100%) with TreeSHAP-style factor attributions | Forensics, billing, clinical, and metadata flag lists | `AnomalyAssessment` | Returns score clamped to [0.0, 100.0]; defaults base risk to 2.0% | `backend/app/forensics/fraud_scorer.py:16` |
| 19 | Forensic Integrity | PDF Multi-Revision Inspector | Detects incremental updates, repeated %%EOF markers, and object tampering | Raw PDF bytes | `PDFInspectionResult` | Flags >1 revision as suspicious/tampered | `backend/app/forensics/pdf_inspector.py:18` |
| 20 | Audit & Provenance | Hash-Chained Audit Trail | Logs pipeline lifecycle events with SHA-256 state and previous-hash chaining | Action, actor, payload dict, claim ID | `AuditLog` database record | Computes SHA-256 over json payload and previous record hash | `backend/app/utils/audit_trail.py:12` |
| 21 | Presentation | Financial Delta Waterfall UI | Displays 4 KPI cards and stacked bar breakdown of billed vs approved vs recoverable | `AnalysisResult`, `Claim` | React DOM | Injects hardcoded mock fallback values (68000, 42500, 124000) when backend data missing | `frontend/src/components/analysis/FinancialDelta.jsx:48` |
| 22 | Presentation | Patient Portal Claim Tracker | Real-time WebSocket and REST tracking for consumer claim status and recovery | `portal_claim_status` response | React DOM | Status string mismatch (engine emits MISMATCH_DETECTED; portal checks CLAIM_DISPUTED) | `backend/app/api/portal.py:191` |
| 23 | Ingestion | Extraction Pipeline with OCR Fallback | Processes documents via VLM or fallback OCR | File path, expected document type | Dict containing data model or dummy fallback | Injects hardcoded dummy models with fake dates and "Unknown" strings on failure | `backend/app/extraction/pipeline.py:43` |

---

## 4. Edge Cases

| # | Feature | Input Scenario | Observed Behavior |
|---|---------|----------------|-------------------|
| 1 | `check_proportionate_deduction` | Actual room rate exceeds cap; bill line items include ROOM category and NURSING | `total_room_excess` is added to `proportionate_reduction` (which already included room reduction), resulting in double-deduction of room excess. |
| 2 | `check_proportionate_deduction` | Actual room rate is 1.10x eligible limit (below 1.15x threshold) | Rule outputs: "Ratio does NOT strictly exceed 1.15 threshold. Proportionate reduction is ZERO", refusing to verify legitimate proportionate deductions. |
| 3 | `check_proportionate_deduction` | Hospital bill has itemized room charges with quantity, but dates could not be parsed (`length_of_stay` is None) | Rule returns `status="SKIPPED"` ("Missing room rate or length of stay"), completely failing to evaluate proportionate deduction. |
| 4 | `check_clause_timeline` | Claim occurs on exact 60-month moratorium completion date (e.g., Inception 2020-01-01, Claim 2025-01-01) | Evaluates `claim_date > completion_date` as False; outputs `status="PASS"` ("Claim date is before moratorium completion"), wrongly upholding rejection. |
| 5 | `check_clause_timeline` | Insurer rejects citing "Suppression of material facts regarding pre-existing hypertension" (category: "EXCLUSION") | Word "non-disclosure" not found and category is not "PRE_EXISTING"; rule returns `status="SKIPPED"`, allowing an unlawful rejection to pass. |
| 6 | `check_clause_timeline` | Policy had sum insured enhanced at month 36 from ₹3L to ₹5L; claim at month 48 is for ₹4.5L | Rule has no awareness of enhancement date/amount; assumes base moratorium covers entire amount or lacks multi-tier evaluation. |
| 7 | `check_clause_timeline` | Policy inception date or claim date is missing / empty | Rule returns `status="SKIPPED"` ("Missing policy inception or claim date"), leaving an unlawful pre-existing denial unflagged. |
| 8 | `check_waiting_period` | Claim occurs on Day 30 of a 30-day initial waiting period | Evaluates `delta_days > wp_required_days` as False; outputs `status="PASS"` ("Rejection is valid, INITIAL waiting period has not expired"). |
| 9 | `check_waiting_period` | Claim is for emergency hospitalization due to road traffic accident during initial 30 days | Rule has no check for accidental injury exception; upholds rejection under initial waiting period. |
| 10 | `check_waiting_period` | Insurer rejects citing "Two-year exclusion for Cataract"; policyholder ported policy with 36 months accrued credit | Rule ignores `portability_credits_months`; calculates tenure only from current policy start date, wrongly upholding rejection. |
| 11 | `check_identity_gate` | Policy number or patient name is missing or marked "UNKNOWN" across documents | Rule checks `if pol_num_policy and pol_num_rejection and pol_num_policy != 'UNKNOWN'`; returns `status="PASS"` ("MATCH: Identity markers are consistent or missing"). |
| 12 | `check_identity_gate` | Patient name on bill is "John Doe" and on policy is "Jane Smith" (identity conflict) | Rule returns `status="BLOCKED"`. However, `engine.py` does not check for "BLOCKED" in its gatekeeper loop, so all downstream financial rules run anyway. |
| 13 | `check_clinical_firewall` | Rejection letter states: "Admission not justified on medical grounds; room rent also deducted proportionately" | Rule returns `status="BLOCKED"` on clinical trigger, but downstream rules still execute due to engine gate bypass bug. If gate is patched, entire financial audit is blocked without separating clinical review. |
| 14 | `check_document_integrity` | Sum of line items is ₹10,000; stated gross bill is ₹100,000 (₹90,000 discrepancy) | Rule returns `status="WARNING"`. `engine.py` aggregates verdicts and assigns `overall_status = "NO_MISMATCH_FOUND"`. |
| 15 | `check_document_integrity` | Sum of line items differs from gross bill by ₹9.99 (below ₹10.0 threshold) | Rule returns `status="PASS"` ("Arithmetic integrity verified. Sum of items matches gross bill"). |
| 16 | `HospitalBill.verify_arithmetic` | Floating point representation error: sum of line items is 100.00000000000001, subtotal is 100.0 | Verified as True because `abs <= 1.0`. However, no validation exists that `net_payable == subtotal + tax_amount - discount`. |
| 17 | `ExtractionPipeline.process_document` | Document is corrupted or VLM API key is missing | Pipeline catches error and injects dummy Pydantic model with fake dates ("2023-01-01", "2024-01-01") and "Unknown" strings; rules run on synthetic data. |
| 18 | `FinancialDelta.jsx` | Backend analysis run fails or returns empty/zero calculations | Component defaults `insurerPaid` to 68000, `recoverableAmount` to 42500, `billedAmount` to 124000, and displays fake discrepancy cards (+₹32,000, +₹10,500). |
| 19 | `portal.py` vs `engine.py` | RuleEngine finishes with `overall_status = "MISMATCH_DETECTED"` and recoverable amount of ₹50,000 | `portal.py:_generate_plain_summary` checks for `CLAIM_SUPPORTED` or `CLAIM_DISPUTED`; because strings don't match, it returns generic fallback message. |
| 20 | `ConsistencyChecker` | Diabetic patient admitted for cataract surgery is billed for routine insulin | System flags `insulin` as `CONTRADICTORY_TREATMENT` with `severity="HIGH"` because `cataract` lists insulin as an unexpected medication. |

---

## 5. Detailed Specification & Gap Analysis

### 5.1 Financial Calculation Logic Audit
- **Room Rent Capping & Proportionate Deductions**:
  - *Current Specification*: The codebase implements proportionate deductions in `backend/app/rules/proportionate_deduction.py`. It calculates `room_excess_per_day = actual_room_rate - policy_room_limit`, computes a reduction factor `1 - policy_limit / actual_rate`, and applies it to room-linked items.
  - *Identified Loopholes*:
    1. **Double Counting**: Room line items are categorized under `ROOM` and included in `room_linked_items`. `proportionate_reduction` already deducts `(actual - limit) * days`. Adding `total_room_excess` on top duplicates the room deduction.
    2. **The 1.15x Threshold Fallacy**: The rule requires `actual_room_rate > policy_room_limit * 1.15`. Under IRDAI regulations, proportionate deduction is permitted whenever the room rent exceeds the entitlement; there is no statutory 15% buffer.
    3. **Missing Associated Medical Expense Boundaries**: IRDAI May 2024 Master Circular expressly prohibits proportionate deductions on ICU, medicines, consumables, medical devices, implants, and diagnostics. The codebase relies solely on `is_room_linked` or category `ROOM`/`NURSING`, without explicitly shielding protected categories (e.g., pharmacy, diagnostics).
- **Co-Pay**:
  - `InsurancePolicy` declares `copay_percentage: float = 0.0`. VLM extraction prompt requests co-pay identification.
  - *Gap*: There is **zero calculation logic** for co-pay anywhere in `backend/app/rules/`. If an insurer legitimate applies a 10% co-pay, ClaimGuard AI does not verify it.
- **ICU Capping**:
  - *Gap*: The string `ICU` does not appear anywhere in `backend/app/rules/`. The system has no awareness of ICU limits, nor does it enforce the statutory bar against proportionate deductions on ICU charges.
- **Float vs Decimal Precision**:
  - All currency calculations use IEEE-754 binary floating-point numbers (`float`).
  - Arbitrary margins of error are hardcoded: `+ 100.0` in `proportionate_deduction.py:75`, `10.0` in `document_integrity.py:30`, and `1.0` in `hospital_bill.py:43`.
  - Financial auditing requires exact fixed-point arithmetic (`decimal.Decimal` or integer paisa) with zero tolerance for floating-point drift.
- **Single Source of Truth**:
  - In `frontend/src/components/analysis/FinancialDelta.jsx`, the frontend defines fallback values (`68000`, `42500`, `124000`, `+₹32,000`, `+₹10,500`) when backend fields are nullish or zero.
  - The backend must be the sole authoritative source of truth. If data is unavailable, the UI must render `NEEDS_REVIEW` or an unverified state rather than fabricating numbers.

### 5.2 Regulatory & Policy Rules Audit
- **60-Calendar-Month Moratorium (IRDAI Master Circular 2024 / Section 45)**:
  - *Current Specification*: `check_clause_timeline` calculates `completion_date = policy_start + relativedelta(months=60 - portability_credits)`.
  - *Identified Gaps*:
    1. **Off-by-One Boundary**: Uses `claim_date > completion_date`. A claim occurring exactly on the completion date is treated as occurring before completion.
    2. **Disguised Denial Vulnerability**: Insurers frequently reject claims citing "suppression of material facts", "clause 4.1", or "omission of health history". The rule only checks for category `"PRE_EXISTING"` or the literal word `"non-disclosure"`.
    3. **Enhanced Sum Insured (ESI)**: IRDAI mandates that if the sum insured was increased during the policy tenure, the 60-month clock runs separately for the enhanced portion from the enhancement date. The code explicitly ignores ESI.
    4. **Policy Gaps & Grace Periods**: Portability regulations permit up to a 30-day grace period for continuity. The code assumes uninterrupted coverage from a single start date.
- **Waiting Periods**:
  - *Current Specification*: `check_waiting_period` computes elapsed days and compares against initial (30d), specific disease (24m), or PED (48m).
  - *Identified Gaps*:
    1. **Outdated PED Limit**: Defaults PED waiting period to 48 months. Under the IRDAI May 2024 Master Circular, the maximum allowable PED waiting period was reduced to **36 months**.
    2. **Calendar Inaccuracy**: Uses `months * 30.44` floating-point approximation instead of calendar `relativedelta`.
    3. **Missing Accidental Injury Exception**: Under IRDAI rules, the initial 30-day waiting period does not apply to accidental injuries. The rule has no accident check.
    4. **Portability Neglect**: Does not consider portability credits in waiting period evaluation.
- **Mental Health Parity (MHCA 2017 Sec 21(4))**:
  - Correctly flags rejections citing mental health. However, it assigns `monetary_impact = total_claimed - total_approved` without checking for legitimate non-medical items or room rent limits on the bill.

### 5.3 Ambiguity & Human Review Triggers (`NEEDS_REVIEW`)
- **Complete Absence of `NEEDS_REVIEW`**:
  - Schema `RuleVerdict` allows `status: Literal["PASS", "FAIL", "SKIPPED", "NEEDS_REVIEW", "WARNING", "BLOCKED"]`.
  - Across all 9 rule files in `backend/app/rules/`, **not a single rule ever returns `NEEDS_REVIEW`**.
  - Ambiguous cases (missing dates, unparsed room rates, missing line items) return `SKIPPED`.
  - Missing identity markers return `PASS`.
  - Arithmetic discrepancies return `WARNING` (which aggregates to `NO_MISMATCH_FOUND`).
- **OCR Fallback Dummy Injection**:
  - In `backend/app/extraction/pipeline.py:120-126`, if VLM fails, the system instantiates dummy models with fake dates (`2023-01-01`, `2024-01-01`) and `"Unknown"` strings.
  - Instead of halting with `EXTRACTION_FAILED` or routing to `NEEDS_REVIEW`, the dummy data proceeds to the rule engine, where rules silently skip and produce `NO_MISMATCH_FOUND`.

---

## 6. Caveats

1. **VLM Live API Execution**: VLM extraction was inspected at the prompt and code level; live API calls were not executed during this survey turn to avoid external API dependency and cost.
2. **Frontend Test Framework**: Frontend tests (`frontend/tests/`) rely on Node.js/Vite harnesses; backend tests were inspected via pytest and standalone python probe execution.
3. **Database State**: Local SQLite database was inspected via SQLAlchemy models; schema migrations (`alembic`) were verified against model definitions.
4. **Scope Boundaries**: In accordance with the Dispatch assignment, no production application files were modified during this mining survey.

---

## 7. Conclusion

ClaimGuard AI possesses an extensive structural foundation (tiered rule engine architecture, multi-modal forensics, cryptographic audit logging, appeal template generation), but currently suffers from critical deterministic calculation bugs, regulatory gaps, and an absence of human-review safety routing:

1. **Tier 0 Gate Bypass**: The rule engine fails to recognize `status="BLOCKED"`, allowing financial rules to execute on blocked claims.
2. **Double Deduction**: Proportionate deduction logic doubles room excess deductions when room items are present in line items.
3. **Regulatory Drifts**: The 60-month moratorium has boundary off-by-one errors and misses disguised denials; the PED waiting period defaults to an outdated 48 months (vs. 36 months IRDAI 2024 mandate); accidental injury exemptions and portability credits are missing from waiting periods.
4. **Zero Uncertainty Routing**: Not a single rule emits `NEEDS_REVIEW`. Unparsed or missing data is silently skipped or passed, resulting in `NO_MISMATCH_FOUND` on unverified claims.
5. **Frontend Mock Overrides**: The UI fabricates financial figures when backend data is absent, violating ground-truth integrity.

Fixing these flaws is completely feasible through isolated milestones: patching the Tier 0 gate loop, converting calculations to `decimal.Decimal`, eliminating the double-deduction bug, aligning moratorium and waiting period rules with IRDAI 2024 regulations, replacing silent skips with `NEEDS_REVIEW`, and removing frontend mock fallbacks.

---

## 8. Verification Method

To independently verify the observations, logic chain, and findings documented in this report:

### 8.1 Execute Probe Suite
Run the self-contained verification probe in this folder:
```powershell
venv\Scripts\python .agents\teamwork_preview_spec_miner_survey_2\probe.py
```
Expected Verification Results:
- **Probe 1**: Shows `Expected Proportionate Reduction: ₹2333.33` but `Total Legitimate Deduction: ₹4333.33` (verifies double counting).
- **Probe 2**: Shows `Trigger Check: Ratio 1.10 does NOT strictly exceed 1.15 threshold. Proportionate reduction is ZERO` (verifies arbitrary 1.15x threshold).
- **Probe 3**: Shows `Claim date (2025-01-01) is before moratorium completion (2025-01-01)` for exact 60-month claim (verifies boundary off-by-one). Disguised rejection returns `status=SKIPPED` (verifies keyword vulnerability).
- **Probe 4**: Shows Day 30 of 30-day waiting period returns `status=PASS` (verifies waiting period off-by-one).
- **Probe 5**: Shows Tier 0 Identity Gate returns `status=BLOCKED`, yet all downstream financial rules execute (verifies Tier 0 gate bypass bug).

### 8.2 Inspect Rule Engine Code
- Open `backend/app/rules/engine.py` at line 44:
  ```python
  if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:
      gate_blocked = True
  ```
  Verify that `"BLOCKED"` is missing from the list.
- Open `backend/app/rules/proportionate_deduction.py` at lines 53, 61, 72:
  Verify that `room_linked_items` includes `ROOM` category, and `expected_total_deduction` adds `total_room_excess + proportionate_reduction`.
- Open `frontend/src/components/analysis/FinancialDelta.jsx` at lines 49–75:
  Verify that fallback constants `68000`, `42500`, and `124000` are hardcoded.

### 8.3 Verify Existing Test Suite Failures
Run the existing backend test suite:
```powershell
venv\Scripts\pytest backend\tests\test_rules.py
```
Verify the 3 failures in proportionate deduction tests due to missing admission/discharge dates.
Run:
```powershell
venv\Scripts\pytest backend\tests\test_appeal_adversarial.py
```
Verify `ImportError: cannot import name 'check_appeal_viability'`.
