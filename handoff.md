# ClaimGuard Production Readiness Handoff
Updated: 2026-10-02 (Account 1 hit usage limit; resets 2026-10-31)

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
   OPEN: bound active analysis jobs (queue/worker limit) and byte budget.
3. MEDIUM, CWE-459: unexpected upload errors orphan PHI files (api/portal.py L186-207).
   FIXED (cleanup on any exception), verified by regression test.
Regression tests were added and shown to fail before / pass after each fix.
Not covered by scan: live providers, PDF load tests, OIDC proxy, files outside the
28 changed ones. Duplicate-worker candidate dismissed (single-instance Render only).
Check test_ext.py: scratch file? Full backend suite not yet re-run after fixes.
Final review must be a fresh scan of the whole tree.

## Next (in order; start at first unfinished)
1. Job concurrency / duplicate / retry / restart-recovery checks  <- interrupted here
   INCLUDING a cap on active analysis jobs and a total byte budget per
   submission (open part of scan finding 2)
2. Full backend suite; fix failures (also confirms the scan fixes: findings 1-3)
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
(paste exact pytest / npm test / build output here after each session)