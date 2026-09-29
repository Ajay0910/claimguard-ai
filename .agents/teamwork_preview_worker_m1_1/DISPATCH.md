# Dispatch: Milestone 1 Implementation Worker

- Working Directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_worker_m1_1
- Authoritative Request: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\ORIGINAL_REQUEST.md
- Project Scope: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md
- Milestone: M1 — Test Suite Rehabilitation & Baseline Stabilization
- Exclusive Write Ownership:
  - `backend/app/rules/appeal_evaluator.py`
  - `backend/app/schemas/hospital_bill.py`
  - `backend/tests/test_rules.py`
  - `backend/app/rules/engine.py` (only rule registry export if needed)

## Context & Survey Findings
The survey revealed two issues preventing tests from running:
1. `backend/tests/test_appeal_adversarial.py` and `backend/tests/test_new_features.py` fail during pytest collection with:
   `ImportError: cannot import name 'check_appeal_viability' from 'app.rules.appeal_evaluator'`
   Inspection of `backend/app/rules/appeal_evaluator.py` shows `check_appeal_viability` was accidentally removed during an earlier refactor, and `AppealEvaluator.evaluate_denial` was left as a `pass` stub.
2. In `backend/tests/test_rules.py`, 3 tests fail:
   `test_proportionate_deduction_within_limit`, `test_proportionate_deduction_mismatch`, `test_proportionate_deduction_correct_deduction`.
   Root cause: `check_proportionate_deduction` requires `length_of_stay`. In `HospitalBill` (`backend/app/schemas/hospital_bill.py`), `length_of_stay` is computed only from `admission_date` and `discharge_date`. The test fixture `get_base_bill()` provides no dates, so `length_of_stay` is `None`, causing `check_proportionate_deduction` to return `SKIPPED`. Ensure `HospitalBill.length_of_stay` can fall back to the duration/quantity of room line items if dates are missing, or provide dates in `get_base_bill()`, while keeping `check_proportionate_deduction` working properly.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective & Verification
1. Restore `check_appeal_viability` and ensure proper signatures and implementation in `backend/app/rules/appeal_evaluator.py`.
2. Fix `HospitalBill.length_of_stay` / `test_rules.py` fixture so the 3 proportionate deduction tests pass.
3. Run `pytest backend/tests/` via `.\venv\Scripts\pytest backend/tests/` to verify that all 65 tests collect and pass cleanly with 0 errors and 0 failures.
4. Write your detailed handoff report to `handoff.md` in your working directory and notify the orchestrator.

## 2026-09-26T07:51:48Z
You are assigned as the Milestone 1 Implementation Worker for ClaimGuard AI Hardening.
Your working directory is C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_worker_m1_1.
Read your instructions in C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_worker_m1_1\DISPATCH.md, C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md, and C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\ORIGINAL_REQUEST.md.
MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
Implement the changes to restore check_appeal_viability in appeal_evaluator.py and fix length_of_stay / test fixtures so all 65 tests in backend/tests/ collect and pass.
Run the test command to verify. Write your complete handoff report to C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_worker_m1_1\handoff.md.
When finished, send a message to parent orchestrator (ID: 101499e2-9536-4e3a-95f4-a7b372b422ea).

## 2026-09-26T08:08:00Z
**Context**: Milestone 1 Implementation (Test Suite Rehabilitation & Baseline Stabilization)
**Content**: Checking in on your progress. We observed that `appeal_evaluator.py` has been updated with `check_appeal_viability`. Are you currently running `pytest backend/tests/` and wrapping up your handoff report?
**Action**: Please report your current status, test execution results, and let us know if you need any assistance or are preparing `handoff.md`.

