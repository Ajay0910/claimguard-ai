# Scope: Milestone 1 — Test Suite Rehabilitation & Baseline Stabilization

## Architecture
Stabilize the existing backend test infrastructure so that all existing tests in `backend/tests/` collect and run without errors.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Test Suite Collection & Baseline | Fix import errors and fixtures in test suite (`backend/tests/`) | M1 | survey_1, survey_3 |

## Scope & Concrete Objectives
1. Resolve the collection errors in `backend/tests/test_appeal_adversarial.py` and `backend/tests/test_new_features.py`:
   - Restore the missing `check_appeal_viability` function in `backend/app/rules/appeal_evaluator.py`.
   - Ensure `AppealEvaluator` and `AppealEvaluationResult` signatures and behavior match what the tests expect.
2. Resolve the 3 test failures in `backend/tests/test_rules.py`:
   - `test_proportionate_deduction_within_limit`
   - `test_proportionate_deduction_mismatch`
   - `test_proportionate_deduction_correct_deduction`
   - Root cause: In `HospitalBill` (`backend/app/schemas/hospital_bill.py`), `length_of_stay` evaluates to `None` if `admission_date` or `discharge_date` is missing or unparsed. In `backend/app/rules/proportionate_deduction.py:29-36`, `length_of_stay is None` causes the rule to unconditionally return `SKIPPED`. Ensure `HospitalBill` derives `length_of_stay` from room line item quantity if dates are absent, and/or update test fixtures in `test_rules.py` to provide valid dates.
3. Target Verification Condition:
   - Running `pytest backend/tests/` collects all 65 tests and passes with 100% pass rate (0 errors, 0 failures).

## Interface Contracts
- `check_appeal_viability(bill, policy, rejection, rule_verdicts=None) -> RuleVerdict`
- `AppealEvaluator.evaluate_denial(...) -> AppealEvaluationResult`
- `HospitalBill.length_of_stay -> Optional[int]`
