# CRITICAL ROOT-CAUSE INVESTIGATION: NEW DOCUMENT FAILURES

## 1. The Exact First Point of Failure
The first point of failure when processing unseen, novel, or malformed documents was traced to **Schema Fragility** within the VLM extraction pipeline (`backend/app/extraction/pipeline.py` and `backend/app/schemas/`). 
When a new document lacked non-critical but strictly required schema fields (e.g., `hospital_name` or `subtotal`), the Gemini VLM omitted those fields, causing the Pydantic parser to immediately crash with a `ValidationError`.

## 2. The Architectural Root Cause
The true architectural flaw was not the Pydantic crash itself, but the **Fallback Mechanism**.
In `pipeline.py`, the `except Exception as e:` block caught the Pydantic crash and silently replaced the entire document's extracted data with hardcoded `dummy_data` (e.g., `patient_name="Mr. Ramesh Kulkarni"` for bills and policies). 
This resulted in **Dummy Data Contamination**. When one document was successfully parsed (e.g., Hospital Bill for "Anita Desai") but another failed (e.g., Rejection Letter falling back to "Ramesh Kulkarni"), the mismatch poisoned the `Cross-Document Identity Gate`.
The Identity Gate correctly recognized the conflicting names and returned `STATUS = BLOCKED`, incorrectly flagging a valid new document as an identity conflict/fraud attempt simply because of a missing subtotal.

## 3. The True Root-Cause Class
This maps directly to:
- **Schema fragility**: Optional fields were incorrectly required, causing missing values to crash validation.
- **Error handling assumption**: The fallback mechanism silently poisoned downstream deterministic systems (the Identity Gate) instead of passing a safe `INSUFFICIENT_EVIDENCE` object.

## 4. The Architectural Fix
1. **Schema Resilience**: Updated the core Pydantic extraction schemas (`HospitalBill`, `InsurancePolicy`, `RejectionLetter`) to mark almost all fields as `Optional`, so that real-world documents lacking specific data points yield a partial object rather than crashing the parser.
2. **Safe Model Validators**: Updated `@model_validator` functions (e.g., `verify_arithmetic`) to safely handle `None` values without throwing `AttributeError`.
3. **Elimination of Contamination**: Replaced the hardcoded `dummy_data` in the fallback block with empty object instantiations (`HospitalBill()`, `InsurancePolicy()`). If the VLM completely fails, the system now safely forwards an empty schema, triggering a legitimate `INSUFFICIENT_EVIDENCE` status, rather than hallucinating "Mr. Ramesh Kulkarni."

## 5. Non-Degradation Proof
- The baseline test suite (301 tests) was recorded and verified as **GREEN** before modifications.
- After implementing the schema fixes and removing dummy data, **0 existing tests were broken**. The suite remains fully green.

## 6. Generalization Proof
- A suite of simulated new documents (including FPDF generated bills missing required names and totals) was uploaded to the pipeline.
- Before the fix, the Identity Gate threw a false `BLOCKED` due to the "Unknown vs Ramesh Kulkarni" conflict.
- After the fix, the pipeline correctly recognized the missing data, avoided dummy fallback, and returned `REVIEW_RECOMMENDED` (`INSUFFICIENT_EVIDENCE`), accurately describing the missing data without hallucinating a conflict.

## 7. Mutation Test Results
- **Mutation 1**: Forcing the VLM extractor to throw a `ValueError` in the test `test_pipeline_no_dummy_data_leakage`.
- **Result**: The pipeline correctly caught the error, instantiated an empty `HospitalBill`, and returned `status="INSUFFICIENT_EVIDENCE"` without raising an exception and without injecting the dummy name. The new regression tests capture this permanently.

## 8. Artifacts/Test Cases Added
- Created `test_new_docs2.py` and `test_fail_docs.py` to continuously mock and test complete e2e multi-document upload workflows with intentionally corrupted schemas.
- Added `backend/tests/test_new_document_generalization.py` to enforce that Pydantic validation handles missing data gracefully and that dummy data leakage is permanently prevented.

## 9. `/learn` Rules Authored
Added `.cursor/rules/extraction-schema-fragility.mdc` mandating that future extraction schemas must make fields `Optional` to prevent Pydantic crashes on real-world inputs, and explicitly banning the use of hardcoded fallback data that poisons downstream Identity Gates.

## 10. Financial/Calculation Impact
- Deterministic calculation logic (`FinancialMath`, `Proportionate Deduction`) was not degraded. They were already equipped to handle `None` values via the `get_val()` helper. Removing the dummy fallback ensures the engine calculates true discrepancies instead of comparing against fabricated dummy totals.

## 11. Final Assessment
The system is now robust against novel/unseen document layouts. If an OCR or VLM extraction misses a field, it now cleanly degrades to a `REVIEW_RECOMMENDED` escalation rather than generating a catastrophic false-positive `BLOCKED` condition. The architectural boundary between AI extraction fragility and deterministic policy enforcement has been securely sealed.
