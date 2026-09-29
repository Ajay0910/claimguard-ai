# Task Assignment: Milestone 1 Remediation Worker

## 2026-09-17T15:15:00Z
- **Target Role:** teamwork_preview_worker
- **Identity:** `worker_m1_remediation`
- **Working Directory:** `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m1_remediation`
- **Scope Documents:**
  - `ORIGINAL_REQUEST.md`: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\ORIGINAL_REQUEST.md`
  - `PROJECT.md`: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_1\PROJECT.md`
  - `GATE_STATUS.md`: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_1\GATE_STATUS.md`
  - `Challenger 1 Report`: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\challenger_m1_1\handoff.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity conflicts WILL be detected and your work WILL be rejected.

## Objective
Remediate the 6 defects and 2 polish findings discovered during the Milestone 1 Gate verification.

### Specific Tasks:
1. `src/services/api.js`:
   - Line 8: Update import from `./mockData` to `./mockData.js` to enable direct Node ESM execution.
   - Line 19: In `normalizeStats`, handle null safely: `const s = backendStats || {};` and read fields from `s`.
   - Line 37: In `normalizeClaims`, handle sparse/null arrays safely: `rawClaims.filter(Boolean).map(...)`.
   - Line 77: In `normalizeAnalysisResult`, preserve clean claims with empty conflicts: `rule_verdicts: Array.isArray(core.rule_verdicts) ? core.rule_verdicts : mockAnalysisResult.rule_verdicts`.
   - Line 86: In `normalizeAppealDraft(data)`, when `!data`, return `{ ...mockAppealDraft, content: mockAppealDraft.appeal_text, appeal_letter: mockAppealDraft.appeal_text }` so backward-compatible aliases exist.
2. `src/App.jsx`:
   - Line 100: Change `backdrop-blur-xs` to `backdrop-blur-sm`.
3. `src/components/common/StatusBadge.jsx`:
   - Line 88: Add `normStatus === 'EXTRACTING' || normStatus === 'PROCESSING'` to the spinning icon condition.
4. `tests/tier1-feature-coverage.test.mjs`:
   - Update imports to pull `normalizeStats`, `normalizeAnalysisResult`, `normalizeAppealDraft` directly from `../src/services/api.js`.
5. Verification:
   - Run `npm run build` and ensure exit 0.
   - Run `npm test` and ensure 61/61 tests pass.
   - Run `node --loader ./tests/esm-loader.mjs ./tests/challenger-m1-stress.mjs` and ensure all 34 tests pass.
   - Deliver `handoff.md` in your working directory and notify parent.
