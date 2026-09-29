# Comprehensive Survey Report: Adjudication Architecture, Rules Engine, and Financial Reconciliation

- **Author**: Explorer Survey 1 (Adjudication, Rules Engine, and Financial Reconciliation Specialist)
- **Date**: 2026-09-27
- **Project Root**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai`
- **Working Directory**: `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1`
- **Authoritative Scope**: Requirements R1 (Deterministic Financial Reconciliation), R2 (Strict Policy-Rule Applicability & Ordering), and R4 (Moratorium & Clinical Reasoning) from `ORIGINAL_REQUEST.md`

---

## 1. Observation

### 1.1 Architecture & Module Inventory
The ClaimGuard adjudication and rules engine is organized across the following core files and directories:

| Component | File Path | Primary Classes / Functions | Lines | Purpose |
|---|---|---|---|---|
| **Pipeline Runner** | `backend/app/api/analysis.py` | `run_analysis_pipeline(claim_id, analysis_run_id)` | 17–121 | Orchestrates extraction, rule engine execution, forensics, database updates |
| **Portal Controller** | `backend/app/api/portal.py` | `portal_submit()`, `get_claim_status()`, `_generate_plain_summary()` | 200–279 | Patient intake, status serialization, plain summary generation |
| **Rule Engine** | `backend/app/rules/engine.py` | `RuleEngine.run_all_rules(bill, policy, rejection)` | 28–252 | Tier partitioning (0 vs >0), DAG topological sorting, AdjudicationState tracking, Final Financial Reconciliation Gate |
| **Adjudication State** | `backend/app/engine/adjudication_state.py` | `AdjudicationState`, `LineItemState`, `FinancialAdjustment` | 1–92 | Stateful ledger tracking line-item balances, deductions, and formulas |
| **Dependency Graph** | `backend/app/engine/dependency_graph.py` | `RuleDependencyGraph` | 1–52 | Kahn's topological sort, cycle detection, mutual exclusivity validation |
| **Calculator** | `backend/app/engine/calculator.py` | `FinancialMath` | 1–78 | Arithmetic wrappers (`add`, `sub`, `mul`, `div`, comparisons) with provenance merge |
| **Rule Registry** | `backend/app/rules/rule_registry.py` | `@register_rule`, `get_all_rules()`, `get_rule()` | 1–36 | In-memory decorator registry storing rule metadata (tier, dependencies, citations) |
| **Cross-Doc Identity Gate** | `backend/app/rules/identity_gate.py` | `check_identity_gate(bill, policy, rejection)` | 25–114 | Tier 0 gate checking policy number, claim ID, names, dates |
| **Clinical Firewall Gate** | `backend/app/rules/clinical_firewall.py` | `check_clinical_firewall(bill, policy, rejection)` | 9–71 | Tier 0 gate regex scanning for medical necessity, active line of treatment, experimental care |
| **Proportionate Deduction** | `backend/app/rules/proportionate_deduction.py` | `check_proportionate_deduction(bill, policy, rejection, state)` | 8–132 | Tier 1 room rent excess and proportionate haircut on room-linked charges (>1.15 threshold) |
| **Deductible Rule** | `backend/app/rules/deductible_rule.py` | `check_deductible(bill, policy, rejection, state)` | 8–59 | Tier 1 fixed policy deductible deduction across remaining balances |
| **Co-Pay Rule** | `backend/app/rules/copay_rule.py` | `check_copay(bill, policy, rejection, state)` | 8–64 | Tier 1 percentage co-pay deduction applied post-deductible |
| **Moratorium / Timeline** | `backend/app/rules/clause_timeline.py` | `check_clause_timeline(bill, policy, rejection)` | 10–92 | Tier 1 60-month IRDAI moratorium verification for PED/non-disclosure |
| **Waiting Period** | `backend/app/rules/waiting_period.py` | `check_waiting_period(bill, policy, rejection)` | 9–68 | Tier 1 initial, specific disease, and PED waiting period checks |
| **Mental Health Parity** | `backend/app/rules/mental_health_parity.py` | `check_mental_health_parity(bill, policy, rejection)` | 8–45 | Tier 1 Section 21(4) Mental Healthcare Act 2017 enforcement |
| **Document Integrity** | `backend/app/rules/document_integrity.py` | `check_document_integrity(bill, policy, rejection)` | 8–52 | Tier 1 line-item arithmetic balance validation |
| **Authenticity Check** | `backend/app/rules/authenticity_check.py` | `check_authenticity(bill, policy, rejection)` | 28–80 | Tier 1 mock ROHINI hospital and policy registry check |
| **Appeal Evaluator** | `backend/app/rules/appeal_evaluator.py` | `AppealEvaluator.evaluate_denial()` | 17–257 | Statistical overturn probability engine, statutory violation aggregator |
| **Report Generator** | `backend/app/reports/generator.py` | `ReportGenerator.generate_analysis_report()` | 24–91 | Structured JSON report and formal appeal letter generation |

---

### 1.2 Verbatim Errors and Failed Test Run
Running the project test suite (`.\venv\Scripts\pytest backend/tests/`) yielded:
```
=========================== short test summary info ===========================
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f02_identity_gate_exact_match_pass
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f02_identity_gate_bill_policy_name_mismatch_blocked
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f02_identity_gate_coverage_date_conflict_blocked
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f03_document_integrity_arithmetic_verified_model_validator
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f04_gate_blocking_identity_conflict_blocks_engine
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f04_gate_blocking_document_warning_skips_downstream
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f05_proportionate_deduction_no_room_cap_pass
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f06_protected_expense_pharmacy_shielded
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f06_protected_expense_ot_charges_shielded
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f07_copay_ten_percent_calculation
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f07_copay_twenty_percent_calculation
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f07_copay_zero_percent_full_admissibility
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f07_deductible_below_threshold
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f07_sublimit_procedure_enforcement
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f11_evidence_line_item_provenance_retention
FAILED backend/tests/e2e/test_tier1_features.py::test_tier1_f13_blocked_engine_zero_financial_impact
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f05_proportionate_deduction_exact_limit
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f07_deductible_exact_boundary
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f07_deductible_one_rupee_above
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f07_copay_extreme_fifty_percent
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f07_deductible_then_copay_ordering
FAILED backend/tests/e2e/test_tier2_boundaries.py::test_tier2_f07_sublimit_exact_match
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_03_copay_and_icu_shielding
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_09_sublimit_exhaustion_and_proportionate_deduction
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_10_identity_mismatch_and_document_arithmetic_error
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_13_mental_health_and_deductible_reconciliation
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_14_room_rent_within_limit_and_copay
FAILED backend/tests/e2e/test_tier3_pairwise.py::test_tier3_pairwise_15_authenticity_check_failed_and_clean_gates
FAILED backend/tests/e2e/test_tier4_real_world.py::test_tier4_scenario_s1_multiday_inpatient_room_rent_excess_protected_icu
FAILED backend/tests/e2e/test_tier4_real_world.py::test_tier4_scenario_s5_high_value_cardiac_surgery_copay_sublimit
FAILED backend/tests/test_appeal_adversarial.py::TestRuleEngineIntegration::test_claim_with_severe_statutory_violations
FAILED backend/tests/test_rules.py::test_proportionate_deduction_no_cap
======================= 32 failed, 190 passed in 1.93s ========================
```

---

### 1.3 Exact Code Findings by Topic

#### Finding A: Generic Heuristic Probability & Hardcoded Overrides (R1 Violation)
1. **Hardcoded Overturn Probability Engine** (`backend/app/rules/appeal_evaluator.py`, lines 184–225):
   ```python
   base_overturn = 25.0  # Baseline appeal overturn rate across all commercial claims

   # Additive probability shifts based on concrete legal defects
   if has_ped_denial and elapsed_months >= moratorium_months:
       base_overturn += 62.0  # Moratorium claims win 90%+ at Ombudsman
   if has_mental_health_denial or (diagnosis_mh and has_ped_denial):
       base_overturn += 58.0  # Mental health parity has binding high court precedent
   if has_proportionate_deduction:
       base_overturn += 45.0  # Proportionate deduction adjustments succeed 78% of the time
   if is_emergency and has_waiting_period_denial:
       base_overturn += 52.0  # Emergency waiting period exemption wins 85%
   if has_vague_denial:
       base_overturn += 30.0  # Vague notices reversed in 68% of hearings
   if tat_days > 30:
       base_overturn += 15.0
   if is_cosmetic:
       base_overturn -= 40.0

   overturn_prob = max(5.0, min(96.0, round(base_overturn, 1)))

   if overturn_prob >= 70.0:
       appeal_viability = "STRONG"
   elif overturn_prob >= 40.0:
       appeal_viability = "MODERATE"
   else:
       appeal_viability = "LOW"

   ombudsman_risk = round(min(98.0, max(10.0, overturn_prob * 1.05)), 1)
   if statutory_violations:
       ombudsman_risk = max(ombudsman_risk, 75.0)
   ```
2. **Heuristic Overriding Financial Deductions** (`backend/app/rules/appeal_evaluator.py`, lines 402–410):
   ```python
   return RuleVerdict(
       status=status,
       rule_name="Denial Contestability & Ombudsman Dispute Rule",
       rule_description="Predicts appeal overturn probability...",
       confidence=0.90,  # Hardcoded arbitrary confidence
       finding=finding,
       monetary_impact=claim_data.get("deducted_amount", 0.0) if status == "FAIL" else 0.0
   )
   ```
   If appeal viability is `STRONG` (overturn >= 70%), the entire claim deduction is marked as a recoverable monetary impact, completely discarding bill-level arithmetic.
3. **Ad-Hoc Test Hack Script** (`backend/fix_tests.py`, line 27):
   ```python
   content = content.replace('>= 70.0', '>= 50.0')
   ```
   A quick-fix script previously lowered the assertion threshold in test files from 70% to 50% to mask heuristic instability.
4. **Composite Forensics Risk Score** (`backend/app/forensics/fraud_scorer.py`, lines 83–90):
   ```python
   raw_composite = (
       base_risk
       + (f_score_clean * self.WEIGHT_FORENSICS * 100.0)
       + (m_score_clean * self.WEIGHT_METADATA * 100.0)
       + (b_score_clean * self.WEIGHT_BILLING * 100.0)
       + (c_score_clean * self.WEIGHT_CLINICAL * 100.0)
       + (p_score_clean * 0.05 * 100.0)
   )
   ```
   Collapses clinical issues, document tampering, and billing arithmetic into an arbitrary weighted percentage (0–100%).

---

#### Finding B: Final Financial Reconciliation Gate Flaws (R1 Violation)
1. **Unconditional Execution on Blocked Gate** (`backend/app/rules/engine.py`, lines 169–205):
   ```python
   # FINAL RECONCILIATION GATE
   expected_payable = sum(item.remaining_balance for item in adj_state.line_items.values())
   insurer_payable = get_val(rejection, 'total_approved', 0.0) if rejection else expected_payable
   disputed_amount = expected_payable - insurer_payable
   ...
   if abs(disputed_amount) > 1.0:
       reconciliation_failed = True
       if overall_status == "NO_MISMATCH_FOUND":
           overall_status = "MISMATCH_DETECTED"
       verdicts.append(RuleVerdict(
           status="FAIL",
           rule_name="Final Financial Reconciliation Gate",
           finding=f"Reconciliation Failed: Expected Payable (₹{expected_payable:.2f}) - Insurer Payable (₹{insurer_payable:.2f}) = Disputed Amount (₹{disputed_amount:.2f}).",
           monetary_impact=disputed_amount
       ))
   ```
   - When a Tier 0 Gatekeeper returns `BLOCKED` (e.g. Identity conflict or Clinical necessity), downstream rules are skipped, so `remaining_balance` equals the gross bill.
   - The reconciliation gate runs anyway, calculating `disputed_amount = gross_bill - 0`, adding a `FAIL` verdict with monetary impact equal to the full bill.
   - This causes `test_tier1_f13_blocked_engine_zero_financial_impact` to fail (`MISMATCH_DETECTED` instead of `BLOCKED`).
2. **False Reconciliation Failure on Legitimate Rejections**:
   - If an insurer legitimately rejects a claim (e.g., initial waiting period), `check_waiting_period` returns `status="PASS"`.
   - The non-financial rules do NOT deduct from `adj_state`.
   - `adj_state.line_items` still holds the gross bill balance.
   - The Final Financial Reconciliation Gate compares `gross_bill` against `rejection.total_approved` (which is 0), flags `reconciliation_failed = True`, appends a `FAIL` verdict, and flips `overall_status` to `MISMATCH_DETECTED`.
3. **Double Counting Monetary Impact in Model Validator** (`backend/app/schemas/analysis_result.py`, lines 33–48):
   ```python
   @model_validator(mode='after')
   def compute_aggregates(self) -> 'AnalysisResult':
       impact = 0.0
       t1 = 0
       for rv in self.rule_verdicts:
           if rv.status == "FAIL":
               impact += (rv.monetary_impact or 0.0)
               t1 += 1
       self.total_monetary_impact = impact
   ```
   Both the individual rule (e.g. `Proportionate Deduction Rule`, monetary impact = ₹34,000) and `Final Financial Reconciliation Gate` (monetary impact = ₹34,000) are flagged as `FAIL`. The validator sums them up, resulting in ₹68,000 (double the actual dispute).
4. **Floating Point Precision**:
   `FinancialMath` in `backend/app/engine/calculator.py` uses native Python `float`. Fixed-point currency (`decimal.Decimal` / paise) is not used, risking 1-paise drift across multi-step calculations.

---

#### Finding C: Strict Policy-Rule Applicability & Ordering (R2 Violation)
1. **Missing Rules in Rules Engine**:
   - **Procedure Sub-Limit Rule**: Does NOT exist in `backend/app/rules/`. Sub-limits in `policy.sub_limits` (Cataract, Hernia, CABG, Joint Replacement) are completely ignored during adjudication.
   - **Non-Medical / Excluded Expenses Rule**: Does NOT exist. Non-payable items (Schedule I consumables, administrative charges) are not removed before policy sub-limits/deductibles.
   - **Sum Insured Cap Rule**: Does NOT exist. If total admissible expense exceeds `policy.sum_insured`, the engine does not cap the expected payable at `sum_insured`.
2. **Proportionate Deduction Scope & Double Deduction** (`backend/app/rules/proportionate_deduction.py`):
   - **Line 68 includes `'CONSULTATION'`**:
     ```python
     if is_linked or cat in ['ROOM', 'NURSING', 'CONSULTATION']:
         room_linked_items.append(item)
     ```
     Specialist doctor consultation fees are doctor professional charges, protected by IRDAI regulations. Including consultation inflates the room-linked deduction pool and breaks `test_tier1_f06_protected_expense_room_linked_items_properly_differentiated`.
   - **Double Deduction of Room Charges**:
     Room excess is computed as `(actual_rate - limit) * days`.
     Proportionate reduction is computed as `room_linked_sum * (1 - limit / actual_rate)`.
     Because `room_linked_codes` includes the room item itself, room charges are subjected to BOTH the direct excess haircut AND the proportional haircut.
   - **State Balance Desync**:
     Line 86 calls `state.apply_deduction(...)` ONLY for `proportionate_reduction`.
     `total_room_excess` is NEVER deducted from `state`! Consequently, `adj_state` still retains room excess in `remaining_balance`.
   - **Return Status on Missing Limit**:
     Lines 18–25 return `NOT_APPLICABLE` when `policy.room_rent_limit_per_day is None`. The test suite (`test_rules.py:59`, `test_tier1_features.py:302`) expects `PASS`.
3. **Static Rule Dependencies vs Policy Semantic Derivation**:
   - `backend/app/engine/dependency_graph.py` builds edges solely from static decorators (`copay_rule.py` hardcodes `depends_on=["Deductible Rule", "Proportionate Deduction Rule"]`).
   - The ordering is not derived from policy metadata (e.g., whether policy specifies co-pay applies before or after deductible).

---

#### Finding D: Moratorium & Clinical Reasoning (R4 Violation)
1. **Flawed Moratorium Calendar Math** (`backend/app/schemas/insurance_policy.py`, lines 70–73 & `backend/app/rules/clause_timeline.py`, lines 57–59):
   ```python
   start_date_str = get_val(self, 'inception_date', getattr(self, 'policy_start_date', None))
   effective_moratorium_end = start + relativedelta(months=(months_limit - portability_months))
   ```
   - If `inception_date` is the original inception date of continuous coverage (e.g., 2018-01-01), subtracting portability months (e.g., 48) and adding 12 months to 2018-01-01 sets the completion date to 2019-01-01 (12 months into the policy instead of 60).
   - Portability credits only apply to the current policy period: `current_policy_start + (60 - portability_credits)`. For an original uninterrupted policy, moratorium completion is simply `original_inception_date + 60 months`.
2. **Disguised Rejection Phrases Bypassed** (`backend/app/rules/clause_timeline.py`, lines 21–25):
   ```python
   is_non_disclosure = any(
       get_val(reason, 'category', '') == "PRE_EXISTING" or 
       "non-disclosure" in str(get_val(reason, 'description', '')).lower()
       for reason in reasons_list
   )
   ```
   Misses common insurer repudiation phrasings: "suppression of material facts", "omission of medical history", "breach of utmost good faith", "Clause 4.1", "pre-existing" in description.
3. **Waiting Period Rule Flaws** (`backend/app/rules/waiting_period.py`, lines 35–45):
   - Computes days using `30.44 * months` (floating-point approximation) rather than exact calendar dates via `relativedelta`.
   - Defaults PED waiting period to 48 months (`get_val(policy, 'ped_waiting_period_months', 48)`), violating the IRDAI 2024 Master Circular that caps PED waiting period at 36 months (3 years).
   - Completely ignores `policy.waiting_periods: list[WaitingPeriodConfig]` on the `InsurancePolicy` schema.
4. **Gate Bypass Bug in Rule Engine** (`backend/app/rules/engine.py`, lines 43–63):
   - Inspects `identity_gate` finding for substring `"COVERAGE_DATE_CONFLICT"`.
   - `identity_gate.py` (line 83) writes `"Coverage Date CONFLICT"` (with spaces).
   - More critically, an out-of-coverage date conflict is an invalid claim date (outside policy term), which cannot legally be excused by a PED moratorium.

---

#### Finding E: Type System & Provenance Wrapper Failures
1. **`Provenance[T]` Operator Deficiency** (`backend/app/schemas/provenance.py`):
   - `Provenance` is a Pydantic model with `value: T`.
   - Lacks numeric operator overloads (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`).
   - Lacks equality comparison with primitives (`__eq__`).
   - Lacks type casting (`__float__`, `__int__`).
   - Lacks string delegation (`lower()`, `upper()`).
   - Results in widespread `TypeError: unsupported operand type(s)` and `AssertionError: Provenance[float](value=415000.0) == 415000.0` in tests.
2. **Missing Schema Attributes**:
   - `RejectionLetter` schema lacks `patient_name: Optional[Provenance[str]]`.
   - `InsurancePolicy` schema lacks `ped_waiting_period_months: Optional[Provenance[int]]`.
3. **Currency Symbol and String Formatting**:
   - `proportionate_deduction.py` formats numbers as `"Rs. {amt:.2f}"` instead of `"₹{amt:.2f}"`.
   - `identity_gate.py` finding text lacks the expected word `"consistent"` on matching passes.

---

## 2. Logic Chain

```
[Observation: appeal_evaluator.py:184-225 base_overturn=25.0 + additive heuristic jumps (62, 58, 45, 52)]
       ↓
(Inference: Overturn probability is an arbitrary empirical approximation rather than a deterministic audit)
       ↓
[Observation: appeal_evaluator.py:409 sets monetary_impact = full deducted_amount when overturn >= 70%]
       ↓
(Inference: Heuristic probability directly overrides bill-level financial verification and statutory calculations)
       ↓
[Conclusion A: System directly violates Requirement R1 (Heuristic overrides deterministic calculations)]
```

```
[Observation: engine.py:170-205 Final Financial Reconciliation Gate runs outside the gate_blocked check]
       ↓
(Inference: When Tier 0 Gatekeeper blocks, gross bill is compared to approved 0, creating a false dispute)
       ↓
[Observation: When rejection is legitimate (e.g. valid waiting period), rules don't adjust state, expected_payable remains gross bill]
       ↓
(Inference: Final Financial Reconciliation Gate flags all legitimate rejections as reconciliation failures)
       ↓
[Observation: AnalysisResult.compute_aggregates sums impact of all FAIL verdicts, doubling reconciliation + rule impact]
       ↓
(Inference: Monetary impact is inflated and inaccurate across all failure scenarios)
       ↓
[Conclusion B: Financial reconciliation layer has fundamental architectural flaws requiring complete refactoring]
```

```
[Observation: No sub-limit rule, non-medical rule, or sum-insured rule exists in backend/app/rules/]
       ↓
(Inference: Sub-limits and non-payable expenses are completely unhandled during balance deductions)
       ↓
[Observation: proportionate_deduction.py lines 68 includes CONSULTATION, line 46 computes room excess but never deducts it from state]
       ↓
(Inference: Consultation is unlawfully penalized, room charges are double-deducted in formulas, and state balance desyncs)
       ↓
[Conclusion C: System violates Requirement R2 (Strict applicability, immune categories, and ordering)]
```

```
[Observation: insurance_policy.py:71 subtracts portability from 60 and adds to original inception date]
       ↓
(Inference: If continuous coverage started 60 months ago at inception, this erroneously requires up to 108 months)
       ↓
[Observation: clause_timeline.py:21 only checks PRE_EXISTING or 'non-disclosure', missing Clause 4.1 or suppression phrases]
       ↓
[Observation: clinical_firewall.py blocks downstream rules but engine.py still appends reconciliation FAIL verdict with monetary impact]
       ↓
(Inference: Clinical rejections are not properly segregated from financial adjudication)
       ↓
[Conclusion D: System violates Requirement R4 (Continuous coverage math, disguised rejections, and clinical segregation)]
```

---

## 3. Caveats
- **Read-Only Inspection**: In accordance with the Explorer mandate, no source code, configuration, or test files were modified during this investigation.
- **VLM & OCR Pipeline Scope**: This survey specifically focused on Adjudication, Rules Engine, and Financial Reconciliation. Detailed VLM prompt engineering and OCR coordinate parsing were examined only at interface boundaries (`HospitalBill`, `InsurancePolicy`, `RejectionLetter`, `Provenance`).
- **UI Code Inspection**: Frontend implementations in `frontend/` and `frontend-portal/` were inspected for contract and status alignment; deep component rendering will be detailed by the frontend/testing specialist.

---

## 4. Conclusion & Gap Analysis vs Requirements

### Gap Matrix

| Requirement | Description | Current State in Code | Architectural Gap / Flaw | Severity |
|---|---|---|---|---|
| **R1. Deterministic Financial Reconciliation** | Disputed amount = Expected Payable - Insurer Payable; zero heuristic overrides. | `AppealEvaluator` uses arbitrary +62%, +45% additive points and 70% threshold to override financial impact; Reconciliation Gate fails on legitimate rejections; double-counts monetary impact. | Must eliminate heuristic overturn overrides from financial paths; tie reconciliation strictly to line items; ensure valid rejections zero out expected payable; reconcile to exact zero. | **CRITICAL** |
| **R2. Strict Applicability & Ordering** | Trigger strictly > 1.15; immune categories (OT, Cath Lab, ICU, Pharmacy, Consultation); policy-derived ordering. | `proportionate_deduction.py` includes `CONSULTATION`; room excess is double-counted in formula but not deducted in state; sub-limits, non-medical items, and sum insured capping are missing; rule ordering is static. | Implement Procedure Sub-Limit Rule, Non-Medical Items Rule, Sum Insured Cap Rule; fix proportionate deduction scope and state mutation; derive rule order dynamically from policy. | **CRITICAL** |
| **R4. Moratorium & Clinical Reasoning** | 60-month continuous coverage calendar engine; portability credits; ESI timelines; separate clinical vs document vs fraud. | Moratorium math in `insurance_policy.py` double-counts portability against original inception; disguised rejections missed; waiting period uses 48mo and 30.44 float; clinical block still gets financial fail verdict. | Fix exact calendar date math (`relativedelta`); detect disguised repudiation phrases; cap PED waiting period at 36mo (IRDAI 2024); cleanly segregate clinical blocks from financial reconciliation. | **CRITICAL** |
| **Cross-Cutting: Type Safety** | Transparent provenance tracking without breaking Python arithmetic. | `Provenance[T]` lacks numeric operators, equality with primitives, and string method delegation, causing 20+ test crashes. | Enhance `Provenance` with operator overloading (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__eq__`, `__float__`) or transparent unwrap proxies. | **BLOCKER** |

---

## 5. Proposed Architectural Redesign & Action Plan

### 5.1 Adjudication Pipeline Execution Model

```
                    ┌───────────────────────────────┐
                    │      Document Ingestion       │
                    │  (Bill, Policy, Rejection)    │
                    └──────────────┬────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │     Tier 0 Safety Gates       │
                    │  - Identity Verification      │
                    │  - Clinical Firewall Gate     │
                    │  - Document Integrity Gate    │
                    └──────────────┬────────────────┘
                                   │
                    Is ANY Gate BLOCKED / REVIEW?
                         /                  \
                       YES                   NO
                       /                      \
                      ▼                        ▼
        ┌─────────────────────────┐  ┌───────────────────────────────────┐
        │  ABORT FINANCIAL ENGINE │  │    Initialize AdjudicationState   │
        │  - Skip Tier 1 Rules    │  │    (Gross line items & balances)  │
        │  - Overall: BLOCKED     │  └─────────────────┬─────────────────┘
        │  - Monetary Impact: 0.0 │                    │
        │  - Human Review Ticket  │                    ▼
        └─────────────────────────┘  ┌───────────────────────────────────┐
                                     │   Dynamic Semantic DAG Ordering   │
                                     │   (Derived from Policy Clauses)   │
                                     └─────────────────┬─────────────────┘
                                                       │
                                                       ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │                 Sequential State Deductions (Tier 1)                   │
        │                                                                        │
        │  1. Non-Medical Exclusions (Schedule I / Non-Payables)                 │
        │  2. Moratorium & Waiting Period Validity Check                         │
        │     - If claim is LEGITIMATELY repudiated -> Clear balance to 0        │
        │     - If rejection is UNLAWFUL -> Retain balance & flag violation      │
        │  3. Room Rent Capping (Direct Excess Haircut on Room)                  │
        │  4. Proportionate Deduction (> 1.15 threshold, Room-linked only)       │
        │     - Explicitly immune: OT, Cath Lab, ICU, Pharmacy, Consultation     │
        │  5. Procedure Sub-Limits (Cataract, Hernia, CABG, Joint Replacements)  │
        │  6. Policy Deductible Deduction                                        │
        │  7. Co-Payment Application (% of remaining balance)                   │
        │  8. Policy Sum Insured Cap Enforcement                                 │
        └──────────────────────────────────────┬─────────────────────────────────┘
                                               │
                                               ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │                  Final Financial Reconciliation Gate                   │
        │                                                                        │
        │  Expected Payable = sum(line_item.remaining_balance)                   │
        │  Insurer Payable = rejection.total_approved                            │
        │  Disputed Amount = max(0.0, Expected Payable - Insurer Payable)        │
        │                                                                        │
        │  If Disputed Amount == 0.0 -> PASS (Reconciliation Matched)            │
        │  If Disputed Amount > 0.0  -> FAIL (Deterministic Underpayment)        │
        │  Overall Monetary Impact = Disputed Amount (Zero double-counting)      │
        └──────────────────────────────────────┬─────────────────────────────────┘
                                               │
                                               ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │                Independent Statutory Appeal Advisor                    │
        │  - Advisory only; NEVER mutates AdjudicationState or Disputed Amount   │
        │  - Maps deterministic rule violations to statutory clauses             │
        │    (IRDAI Master Circular 2024, Insurance Act Sec 45, MHCA Sec 21)     │
        │  - Generates itemized Ombudsperson appeal grounds & structured letter  │
        └────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Implementation Priorities for Downstream Workers
1. **Priority 1: Harden `Provenance[T]`**:
   Implement `__add__`, `__sub__`, `__mul__`, `__truediv__`, `__eq__`, `__float__`, `__int__`, `__str__` in `backend/app/schemas/provenance.py` so standard arithmetic and assertions work seamlessly.
2. **Priority 2: Refactor `Final Financial Reconciliation Gate` & `RuleEngine`**:
   - In `backend/app/rules/engine.py`, skip the reconciliation gate completely if `gate_blocked` is True, setting `total_monetary_impact = 0.0`.
   - When a claim rejection is legitimate (e.g., initial waiting period), reduce `remaining_balance` to 0 so expected payable matches insurer payable (0.0).
   - Fix `AnalysisResult.compute_aggregates` to prevent summing individual rule impacts with the total disputed amount.
3. **Priority 3: Fix `Proportionate Deduction Rule`**:
   - Exclude `'CONSULTATION'` from room-linked expenses.
   - Cleanly separate Room Rent Excess deduction from Proportionate Deduction on associated expenses to prevent double-counting.
   - Ensure both deductions update `adj_state` balances.
   - Return `PASS` when `room_rent_limit_per_day` is None.
   - Use `"₹"` instead of `"Rs."`.
4. **Priority 4: Implement Missing Rules**:
   - `sublimit_rule.py`: Enforce procedure sub-limits from `policy.sub_limits`.
   - `non_medical_rule.py`: Enforce Schedule I exclusions / non-payable consumables.
   - `sum_insured_rule.py`: Cap net payable at `policy.sum_insured`.
5. **Priority 5: Harden Moratorium & Waiting Periods**:
   - In `insurance_policy.py` and `clause_timeline.py`, fix calendar date math: `effective_moratorium_end = (original_inception + 60 months)` or `(current_policy_start + (60 - portability_credits))`.
   - Expand disguised rejection keywords in `clause_timeline.py` (Clause 4.1, suppression, omission, historical).
   - In `waiting_period.py`, cap PED waiting period at 36 months per IRDAI May 2024 circular, read from `policy.waiting_periods`, and use `relativedelta`.
6. **Priority 6: Decouple `AppealEvaluator` from Adjudication**:
   - Move `AppealEvaluator` to an advisory reporting service that operates strictly on the verdicts of deterministic rules.
   - Remove heuristic overturn probability shifts from all financial calculation logic.

---

## 6. Verification Method

### How to Independently Verify Findings:
1. **Inspect Code Files**:
   - `backend/app/rules/appeal_evaluator.py`: Lines 184–225 (heuristic probability jumps) and line 409 (overriding monetary impact with full deduction).
   - `backend/app/rules/engine.py`: Lines 43–63 (Coverage Date CONFLICT string mismatch), lines 169–205 (unconditional reconciliation gate execution).
   - `backend/app/rules/proportionate_deduction.py`: Line 68 (inclusion of `CONSULTATION`), lines 85–92 (omission of room excess from `adj_state`).
   - `backend/app/schemas/provenance.py`: Verify absence of arithmetic/comparison dunder methods.
   - `backend/app/schemas/insurance_policy.py`: Line 71 (portability credits subtracted from inception date).
2. **Execute Test Commands**:
   - Run full test suite:
     ```powershell
     .\venv\Scripts\pytest backend/tests/
     ```
     *Current result*: 32 failures, 190 passed.
   - Run Tier 1 feature tests:
     ```powershell
     .\venv\Scripts\pytest backend/tests/e2e/test_tier1_features.py
     ```
     *Current result*: 16 failures, 49 passed.
   - Run boundary tests:
     ```powershell
     .\venv\Scripts\pytest backend/tests/e2e/test_tier2_boundaries.py
     ```
     *Current result*: 6 failures, 59 passed.
   - Run real world scenarios:
     ```powershell
     .\venv\Scripts\pytest backend/tests/e2e/test_tier4_real_world.py
     ```
     *Current result*: 2 failures, 3 passed.
3. **Invalidation Conditions**:
   - This survey would be invalidated if:
     - `Provenance[T]` already implemented arithmetic overloads (disproved by `TypeError` traces).
     - Sub-limit rules already existed in `backend/app/rules/` (disproved by `grep_search` returning 0 results).
     - The Final Financial Reconciliation Gate was bypassed when `gate_blocked = True` (disproved by `test_tier1_f13` failure trace).
