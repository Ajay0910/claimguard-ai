# ClaimGuard Safe Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure incomplete or failed document extraction cannot produce a financial adjudication, a fabricated result, or a misleading successful UI state.

**Architecture:** Keep the existing upload, extraction, rule-engine, and React structure. Make the extraction-to-adjudication boundary fail closed, preserve processing status separately from the analysis outcome, and remove live UI fallback values that can disguise missing backend data.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic, SQLAlchemy, pytest; React, JavaScript/TypeScript, Node test harness.

**Spec:** `PROJECT.md`, `ORIGINAL_REQUEST.md`, and the supplied ClaimGuard audit brief. The referenced chat contributes research context but does not contain the full architecture history.

## Global Constraints

- AI may extract information but may not independently adjudicate financial correctness or clinical necessity.
- Missing, conflicting, or low-confidence evidence must route to human review.
- Never replace missing extracted values with zero-valued adjudication inputs or demo data.
- Keep the existing user edits in the working tree and preserve unrelated code.
- Do not expose credentials in tracked example/configuration files.

## Review Focus

- A VLM error or absent credential must not return fabricated structured data; assert data is absent and extraction is unsuccessful.
- Any unsuccessful critical document extraction must bypass the financial rule engine; assert no payout or disputed amount is produced.
- An analysis job that finishes with an extraction failure must preserve `EXTRACTION_FAILED` or review state in its result and not be represented as a successful adjudication.
- Missing API response fields must remain missing in the UI model; assert the normalizer does not substitute demo claim, amount, verdict, or appeal content.
- Existing complete-document adjudications must retain their established outputs and pass the backend and frontend suites.

---

### Task 1: Make extraction fallback explicitly unsuccessful

**Files:**
- Modify: `backend/app/extraction/pipeline.py`
- Test: `backend/tests/test_extraction_fail_closed.py`

**Interfaces:**
- Consumes: existing `ExtractionPipeline.process_document(file_path, expected_type)`.
- Produces: extraction result with `source="none"`, `data=None`, `status="INSUFFICIENT_EVIDENCE"` (or the existing agreed extraction-failure enum), and diagnostic issues when VLM extraction is unavailable or fails.

- [x] Add tests for missing credentials, placeholder credentials, VLM exceptions, configured Gemini model, and all-page PDF handoff.
- [x] Verify red tests for placeholder credentials and the multi-page handoff before implementing the fixes.
- [x] Change fallback to return no structured data and identify OCR text only as unstructured diagnostic content.
- [x] Send every rendered PDF page to multimodal extraction; retain the first page for classification.
- [x] Run extraction tests and verify they pass.

### Task 2: Stop adjudication on extraction failure

**Files:**
- Modify: `backend/app/api/analysis.py`
- Test: `backend/tests/test_analysis_fail_closed.py`

**Interfaces:**
- Consumes: extraction result statuses and `AnalysisResult`.
- Produces: a persisted result with `overall_status="EXTRACTION_FAILED"`, no financial totals, and a review explanation without invoking `RuleEngine.run_all_rules` when a required document is incomplete.

- [x] Add an integration regression test asserting the rule engine is not called and financial result fields remain null on extraction failure.
- [x] Verify the regression test exposed the old unconditional rule-engine call.
- [x] Short-circuit before rule execution on missing or unsuccessful critical extraction and persist explicit extraction failure.
- [x] Keep job lifecycle status separate from the authoritative analysis outcome; expose `overall_status` in the status response.
- [x] Run the focused tests and verify they pass.

### Task 3: Remove demo fallback values from live analysis views

**Files:**
- Modify: `frontend/src/services/api.js`
- Modify: `frontend/src/pages/Analysis.jsx`
- Modify: `frontend/src/components/analysis/FinancialDelta.jsx`
- Modify: `frontend/src/components/analysis/AppealLetter.jsx`
- Test: `frontend/tests/analysis-normalization.test.mjs`

**Interfaces:**
- Consumes: API responses and the existing React view props.
- Produces: normalized values that preserve `null`/missing data and render explicit unavailable/review states instead of mock financials, patient data, verdicts, or appeal text.

- [x] Add frontend regression tests showing missing analysis, amounts, claims, and appeal drafts do not synthesize demo data.
- [x] Verify these tests caught mock-value fallback behavior.
- [x] Remove live-flow mock defaults and render explicit unavailable states for absent result data.
- [x] Remove the one-click synthetic Apollo claim loader and fabricated extraction-progress success messages.
- [x] Remove fraud-accusatory recommendation copy; high and medium forensic signals route to human review.
- [x] Treat an empty audit chain as unverified, not valid.
- [x] Stop classifying processing completion as a clean adjudication; return each claim's latest analysis outcome and fix the mismatch statistic enum.
- [x] Suppress result money when any rule verdict requires review or is blocked; hide recoverable amounts from portal summaries in those states.
- [x] Suppress per-verdict financial figures as well as aggregate figures when review is pending; remove invented AI-confidence defaults.
- [x] Remove estimated billed amounts from claim rows and CSV exports.
- [x] Require critical financial fields to cite a page, matching OCR text, and field confidence; bind accepted entries to uploaded document IDs/hashes in the evidence ledger.
- [x] Represent image error-level analysis as `NOT_ANALYZED` when it did not run and hide its zero score.
- [x] Keep unknown portfolio recovery totals null and exclude unverified analyses from aggregate recovery totals.
- [x] Run frontend tests and verify they pass.

### Task 4: Verify complete and incomplete workflows

**Files:**
- Verify: `backend/tests/`
- Verify: `frontend/tests/`

- [x] Run the full backend suite: 315 passed, 2 skipped.
- [x] Run the full frontend suite directly with Node: 77 passed, 0 failed.
- [x] Import the FastAPI application without starting a network-facing service.
- [x] Complete the independent adversarial review and incorporate its five material findings.
- [x] Complete the production frontend build; Vite finished successfully with a large-chunk warning.
- [x] Review final diff and confirm pre-existing user changes remain in the working tree.
- [x] Document remaining live-provider, provenance, and legal-rule limitations in the final report.

## Work Log

- Backend tests: `python -m pytest tests -q` → 315 passed, 2 skipped (2026-10-01).
- Frontend tests: `node ./tests/runner.mjs` → Tier 1 35/35, Tier 2 28/28, Tier 3 9/9, Tier 4 5/5.
- Startup import: `from app.main import app` → FastAPI app imported successfully.
- npm launcher is misconfigured on this host (`npm-cli.js` missing); direct Node invocation ran the same package test runner successfully.
- Production bundle: Vite built successfully; it warns that one JavaScript chunk exceeds 500 kB.
- Independent review follow-up: failed-recovery serialization is masked at API boundaries, financial evidence capture is implemented for key monetary inputs, and all displayed rule amounts are suppressed when review is pending. Broader clause/nonfinancial provenance and live provider behavior still require validation with real documents and configured credentials.

---
