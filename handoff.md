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

## Security scan 7120793f-... (28/28 paths, sealed, 3 findings)
Full report: docs/security-scan-1.json (large; open only if a finding needs checking, never read it whole)
1. Financial evidence misbinding: FIXED (exact numeric tokens + cited OCR page).
2. Aggregate PDF processing / resource exhaustion: FIXED (total pixel budget
   enforced before rendering; per-page temp files no longer collide).
3. Cleanup on unexpected storage/upload errors: FIXED (saved files removed).
Also fixed: verifier field-to-label gap (unrelated payment amounts cannot stand
in for a bill total). Regression tests added and verified to fail before / pass
after each fix.
STATUS: all pending confirmation by a full backend suite run (not yet run).

## Next (in order; start at first unfinished)
1. Job concurrency / duplicate / retry / restart-recovery checks  <- interrupted here
2. Full backend suite; fix failures
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