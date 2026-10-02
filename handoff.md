# ClaimGuard Production Readiness Handoff
Updated: 2026-10-02 (Step 2 verified; DB-outage and live-provider behavior remain NOT VERIFIED)

## Architecture rule
AI reads the case; deterministic rules verify the case.

## Invariants that MUST NOT regress
Tier 0 safety gates; fail-closed extraction; fail-closed adjudication; clinical
firewall; role-aware identity; exact calendar arithmetic for moratorium; portability
handling; original vs enhanced sum-insured separation; provenance ledger;
FinancialMath; Rule Dependency Graph; dependency ordering; mutually exclusive
rules; duplicate-deduction prevention; human-review routing; frontend null/unknown
semantics; no demo values in live analysis; no missing-value-to-zero conversion;
no unsupported financial conclusions.

## Production target
Public patient portal. Patients: Claim ID + one-time high-entropy claim secret
(only the hash is stored). Staff/admin: upstream OIDC proxy; direct backend
bypass must not be possible. Deployment: Render.

## Working rules
- Branch: wip/release-candidate. Do NOT revert, rewrite, or restart.
- Use `git status`, `git log --oneline -20`, `git diff --stat`. Do NOT read the
  full diff; open only the files a task needs.
- Do NOT spawn subagents or repeat completed reviews. Run only tests relevant
  to the current task, then the full suite once at the end of the task.
- Regression test first, then fix. Commit after each task; update this file.
- Anything unverifiable (e.g. live VLM without credentials) = NOT VERIFIED
  and a release blocker. No "production ready" claim without passing validation.
- Allowed verdicts: PRODUCTION READY / RELEASE CANDIDATE - BLOCKED BY SPECIFIC
  ITEMS / STAGING READY - NOT PRODUCTION READY

## Baseline (before hardening)
Backend 315 passed, 2 skipped; frontend 77 passed; FastAPI import OK;
production build OK (Vite large-chunk warning).

## Security scan 7120793f-f058-4a0d-b295-912495ecdc3a (static, 28 changed files)
Raw manifest: docs/security-scan-1.json (do not read whole; ~53 KB)
1. HIGH, CWE-345: financial evidence accepted from wrong amount/page
   (utils/evidence_capture.py L41-52). FIXED (exact numeric token + cited OCR page).
   Also fixed: verifier field-to-label gap (unrelated payment amounts cannot
   stand in for a bill total).
2. HIGH, CWE-400: public PDF uploads can exhaust memory (api/portal.py L108-125).
   PARTLY FIXED: pixel budget before rendering + temp-file collision fixed.
   CLOSED IN CODE: bound active analysis jobs (queue/worker limit) and aggregate
   submission byte budget. See Step 1 results below; DB outage recovery remains
   NOT VERIFIED.
3. MEDIUM, CWE-459: unexpected upload errors orphan PHI files (api/portal.py L186-207).
   FIXED (cleanup on any exception), verified by regression test.
Regression tests were added and shown to fail before / pass after each fix.
Not covered by scan: live providers, PDF load tests, OIDC proxy, files outside the
28 changed ones. Duplicate-worker candidate dismissed (single-instance Render only).
The backend scratch scripts and root document runners were handled in Step 2; see exact results below.
Final review must be a fresh scan of the whole tree.

## Next (in order; start at first unfinished)
1. Job concurrency / duplicate / retry / restart-recovery checks — implemented
   and locally verified for the covered cases; DB outage behavior remains NOT
   VERIFIED.
2. Full backend suite and mutation verification — COMPLETE (2026-10-02; see Step 2 results).
3. Frontend suite + production build
4. Migration / API-contract / import-startup checks
5. Broader provenance (policy clauses, critical fields)
6. Auth: claim-secret flow, cross-claim access, WebSocket, staff OIDC proxy
   bypass, CORS
7. Upload limits/validation, rate controls, safe storage
8. Render readiness: config validation, health checks, shutdown, logging
9. Live VLM validation (NOT VERIFIED if no credentials)
10. 50-100 case synthetic UAT benchmark + invariant/mutation/adversarial tests
11. Second adversarial review -> final Codex Security review on FINAL patch
12. Final release gate and verdict

## Last test results

### Step 1: analysis job lifecycle and intake limits (2026-10-02)

- Added global active-job admission control across public and staff APIs. The
  default cap is 4 `PENDING` plus `RUNNING` jobs; a full queue returns HTTP 503
  with `Retry-After: 30`. Admission is serialized for the configured single
  Render instance / single Uvicorn worker. Provider execution uses a per-loop
  semaphore with the same cap, including jobs restored at startup, so a legacy
  backlog cannot exceed the worker limit. Multi-process admission is NOT
  VERIFIED and is outside the current Render configuration.
- Added a 50 MB aggregate patient submission limit, checked across all three
  uploaded documents before any claim or persistent upload file is created.
- Startup recovery clears result fields, verdict rows and evidence-ledger rows
  for interrupted `RUNNING` jobs before requeueing them as `PENDING`; claim
  state returns to `QUEUED`. The result is committed atomically with the job's
  `COMPLETED` state.
- Portal-secret duplicate submission remains idempotent. Concurrent workers
  use a database compare-and-set so only one worker owns a pending run. Portal
  submissions now require the stable high-entropy secret on the initial request;
  reusing it on retry returns the existing claim.
- Regression tests cover queue-full behavior in both APIs, aggregate byte
  rejection before persistent save, portal retry idempotency, storage cleanup,
  concurrent workers, bounded startup recovery, provider failure and a
  transient result commit failure. The transient commit failure rolls back and
  marks the job `FAILED` without result or verdict rows. A prolonged DB outage
  is NOT VERIFIED: while the database is unavailable, no durable status update
  can be recorded; the next startup recovers any surviving `RUNNING` state.
- Regression-first evidence: queue-cap test initially returned 200 instead of
  503; aggregate-budget test initially returned 200 instead of 413; restart
  test initially found stale financial result data on a requeued run; startup
  backlog test initially ran 3 workers concurrently with a cap of 1; a portal
  submission without a retry secret initially returned 200 instead of 400.
- From `backend/`, focused command before the final provider-failure regression:
  `.\venv\Scripts\python.exe -m pytest tests/test_analysis_job_lifecycle.py tests/test_patient_portal_access.py tests/test_analysis_fail_closed.py -q`
  — 12 passed. The provider-failure regression then passed separately:
  `.\venv\Scripts\python.exe -m pytest tests/test_analysis_job_lifecycle.py::test_provider_failure_marks_job_failed_without_financial_result -q`
  — 1 passed.
- From `backend/`, full backend suite command:
  `.\venv\Scripts\python.exe -m pytest tests -q` — 341 passed, 3 failed,
  2 skipped. Failures are the three `test_extraction_fail_closed.py` cases
  whose `prepare_document` stubs do not accept the new `max_pages` and
  `max_total_pixels` keyword arguments. They were not changed because this
  session is scoped to Step 1. The root-level `python -m pytest -q` collection
  also stopped on the scratch script `backend/test_gemini.py` because its
  extraction result was `None`.
- From `backend/`, lifecycle tests after adding transient DB coverage:
  `.\venv\Scripts\python.exe -m pytest tests/test_analysis_job_lifecycle.py -q`
  — 5 passed, 1 deprecation warning.
- Latest focused Step 1 command from `backend/`:
  `.\venv\Scripts\python.exe -m pytest tests/test_analysis_job_lifecycle.py tests/test_patient_portal_access.py tests/test_analysis_fail_closed.py -q` — 15 passed, 1 deprecation warning.
- After requiring the retry secret, portal tests from `backend/`:
  `.\venv\Scripts\python.exe -m pytest tests/test_patient_portal_access.py -q` — 9 passed, 1 deprecation warning.
- Live provider behavior and prolonged DB-outage persistence are NOT VERIFIED
  and remain release blockers.

## Step 2 Results (2026-10-02)

- Preflight was clean on `wip/release-candidate` at ancestor `71abe92`.
- Moved `test_fail_docs.py` to `scripts/make_fail_docs.py` and
  `test_new_docs.py` to `scripts/make_new_docs.py`. Their generation and API
  activity now runs only under `main()`; generated files keep their original
  repository-relative paths. Also moved the import-time API runner
  `test_new_docs2.py` to `scripts/run_new_docs_analysis.py` and guarded it with
  `main()` so root pytest does not send network requests during import.
- Root pytest command from the repository root:
  `& '.\backend\venv\Scripts\python.exe' -m pytest -q --tb=no` —
  345 passed, 2 skipped, 0 collection errors. Immediately afterward,
  `git status --short --branch` showed a clean tree; no tracked PDFs were
  regenerated or modified. Backend-only discovery runs one fewer test.
- Scratch files removed in commit `71abe92` (recoverable from checkpoint
  commit `f59a871`): `test_ext.py`, `backend/test_extraction.py`,
  `backend/test_gemini.py`, `backend/test_json.py`, `backend/test_subsets.py`,
  and `backend/test_total_approved.py`.
- Mutation verification was run with a clean tree before each mutation and a
  one-file-only `git diff --stat`. Every mutation failed its regression for
  the intended reason; each source file was restored individually and its
  regression passed afterward:

  | Fix | Regression test(s) | Failed when removed | Passed after restore |
  | --- | --- | --- | --- |
  | Exact numeric token, cited OCR page, and total-field label | `test_amount_substring_must_match_complete_numeric_token_and_claimed_page`; `test_amount_citation_on_wrong_page_is_not_accepted`; `test_total_amount_requires_a_total_field_label_not_an_unrelated_payment` | Yes (each targeted test failed) | Yes (each targeted test passed) |
  | PDF aggregate pixel budget before rendering and unique page temp names | `test_pdf_aggregate_pixel_budget_rejects_before_rendering`; `test_pdf_temporary_page_names_do_not_collide_across_documents` | Yes (both failed) | Yes (both passed) |
  | Cleanup of earlier saved uploads after any later save exception | `test_portal_submission_cleans_prior_files_when_later_storage_save_fails` | Yes (orphaned upload remained) | Yes |
  | Pipeline forwards `max_pages` and `max_total_pixels` | `tests/test_extraction_fail_closed.py` (three limit assertions) | Yes (3 failed with captured values `None`) | Yes (5 passed) |

- Changed `backend/tests/test_extraction_fail_closed.py` so preparation stubs
  record explicit limit arguments and the test bodies assert the configured
  values. No permanent production-code change was needed or retained.
- From `backend/`, the final full-suite command was
  `& '.\venv\Scripts\python.exe' -m pytest tests -q` — 344 passed,
  2 skipped, 0 failed. One deprecation warning was reported by Starlette.
- The root run reported one more passing test than the backend-only run; both
  commands completed with zero failures.
- Remaining Step 1 risks: prolonged DB-outage status persistence is NOT
  VERIFIED. The global job cap is not a per-IP rate limit; review that alongside
  edge rate controls later. Live VLM behavior is NOT VERIFIED. These remain
  release blockers.
- Step 2 is complete. Next unfinished item is Step 3 (frontend suite and
  production build); it was not run in this task.
