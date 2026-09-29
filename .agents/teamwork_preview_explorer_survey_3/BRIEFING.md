# BRIEFING — 2026-09-26T07:41:00Z

## Mission
Survey ClaimGuard AI evidence ledger, source document provenance (OCR bounding boxes, snippets, hashes), frontend calculation interaction (no frontend overrides), and backend test suite coverage.

## 🔒 My Identity
- Archetype: explorer
- Roles: [investigation, synthesis]
- Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_explorer_survey_3
- Original parent: 101499e2-9536-4e3a-95f4-a7b372b422ea
- Milestone: Survey Phase

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Write only to working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_explorer_survey_3
- Inspect evidence provenance, OCR bounding boxes, hashes, frontend calculation integrity, backend test suite
- Deliver 5-component handoff report to handoff.md

## Current Parent
- Conversation ID: 101499e2-9536-4e3a-95f4-a7b372b422ea
- Updated: not yet

## Investigation State
- **Explored paths**: `backend/app/extraction/` (`ocr_engine.py`, `pipeline.py`, `vlm_extractor.py`, `prompts.py`, `preprocessor.py`), `backend/app/schemas/` (`hospital_bill.py`, `insurance_policy.py`, `rejection_letter.py`, `analysis_result.py`), `backend/app/rules/` (`engine.py`, `identity_gate.py`, `document_integrity.py`, `clinical_firewall.py`, `proportionate_deduction.py`, `clause_timeline.py`, `waiting_period.py`, `appeal_evaluator.py`), `backend/app/api/` (`upload.py`, `analysis.py`, `portal.py`), `backend/app/models/` (`claim.py`), `frontend/src/` (`services/api.js`, `services/mockData.js`, `components/analysis/FinancialDelta.jsx`, `pages/Analysis.jsx`), `frontend-portal/src/` (`pages/SubmitPage.jsx`, `pages/TrackPage.jsx`), `backend/tests/` (all 5 test files executed via pytest).
- **Key findings**:
  1. Evidence Provenance & Ledger: No evidence ledger or source-level provenance exists anywhere in ClaimGuard AI. Bounding boxes are discarded, no SHA-256 hashes exist for uploaded documents, LLM prompts don't request evidence spans, and only page 0 is parsed.
  2. Frontend Calculation Integrity: Backend API does not accept calculated numbers from forms. However, the internal frontend (`FinancialDelta.jsx`) injects hardcoded fallback values (`₹68k`, `₹42.5k`, `₹124k`), derives calculations client-side, and fabricates fake Tier 1 violation cards (`+₹32k` and `+₹10.5k`) when backend returns 0 violations.
  3. Test Suite Assessment: Test suite is severely broken. 35 of 65 tests crash during collection with `ImportError: cannot import name 'check_appeal_viability'`, 3 tests fail due to missing `length_of_stay`, leaving only 30 passing tests (46.1%). Previous claims of 63 passing tests were inaccurate.
  4. Critical Architecture Vulnerabilities: Tier 0 Gate bypass in `RuleEngine.run_all_rules` (omits `"BLOCKED"` in `gate_blocked` check, so financial rules run even on blocked claims); double deduction bug in `proportionate_deduction.py`; 30.44-day float approximation in moratorium/waiting periods; outdated 48-month PED waiting period limit.
- **Unexplored areas**: None within the assigned survey scope.

## Key Decisions Made
- Executed comprehensive file inspection across backend extraction, models, schemas, rules, APIs, frontend UI, portal, and test suites.
- Validated real test execution via pytest, proving 35 tests crash at collection and 3 fail.
- Formulated complete 5-component handoff report.

## Artifact Index
- DISPATCH.md — Dispatch instructions and received turns
- BRIEFING.md — Situational awareness and working memory
- progress.md — Liveness heartbeat and step tracking
- handoff.md — Comprehensive 5-component survey report
