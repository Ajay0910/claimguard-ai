## 2026-09-18T04:33:05Z

You are worker_m7_motion.
Your working directory is:
c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m7_motion
Workspace root:
c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend

MANDATORY: Read ORIGINAL_REQUEST.md at:
c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\ORIGINAL_REQUEST.md
Also read PROJECT.md at:
c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_4\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity conflicts WILL be detected and your work WILL be rejected.

Detailed specifications and implementation diffs have been prepared by three Explorers. Read their reports:
1. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m7_motion\report.md
2. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m7_toasts\report.md
3. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m7_skeletons\report.md

Files Owned Exclusively:
- src/components/common/PageMotion.jsx
- src/components/common/Skeletons.jsx
- src/components/common/StatusBadge.jsx
- src/App.jsx
- src/pages/Dashboard.jsx
- src/pages/Upload.jsx
- src/pages/Analysis.jsx
- src/components/dashboard/ExecutiveKpiCards.jsx
- src/components/dashboard/DashboardCharts.jsx
- src/components/dashboard/ClaimsTable.jsx
- src/components/upload/BatchDropzone.jsx
- src/components/upload/DocumentCard.jsx
- src/components/upload/ReadinessCheck.jsx
- src/components/analysis/VerdictCard.jsx
- src/components/analysis/AuditTimeline.jsx
- src/components/analysis/AppealLetter.jsx
- tests/component-harness.jsx

Tasks for Milestone 7:
1. Motion Architecture & Page Routing:
   - Create `src/components/common/PageMotion.jsx` wrapping page views with `initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}`.
   - Wrap routes in `src/App.jsx` with `<AnimatePresence mode="wait">` using `location={location}` and `key={location.pathname}`.
   - Wrap page bodies in `Dashboard.jsx`, `Upload.jsx`, `Analysis.jsx` in `<PageMotion>`.
   - Implement animated mobile drawer in `src/App.jsx` with backdrop fade and spring sliding sidebar.
   - Stagger KPI cards in `ExecutiveKpiCards.jsx` (`staggerChildren: 0.08`) and animate sparkline curves (`motion.path pathLength: 0 -> 1`).
   - Add spring progress bar and animated checkmarks in `ReadinessCheck.jsx`.
   - Apply `hover:scale-101` and `active:scale-[0.98]` micro-interactions across key buttons and cards.

2. Sonner Stacked Toast Migration:
   - In `src/App.jsx`: Replace `react-hot-toast` `<Toaster>` with Sonner `<Toaster position="top-right" expand={true} richColors closeButton visibleToasts={6} theme="dark" />`.
   - In all 10 component files (`App.jsx`, `Dashboard.jsx`, `Upload.jsx`, `Analysis.jsx`, `ClaimsTable.jsx`, `DashboardCharts.jsx`, `BatchDropzone.jsx`, `VerdictCard.jsx`, `AuditTimeline.jsx`, `AppealLetter.jsx`), replace `react-hot-toast` imports with named import: `import { toast } from 'sonner';`.
   - Update call sites with semantic title + description pairs.
   - Add the 4-stage stacked pipeline tracking toast in `Upload.jsx` for OCR intake.
   - Verify 0 imports of `react-hot-toast` remain in `src/`.

3. Skeletons & Loaders Modernization:
   - Replace all 6 legacy spinning loaders (`animate-spin`) across 7 code locations:
     - `src/pages/Analysis.jsx`: Replace 96px spinner with Concentric Auditor Scanner HUD with pulsing radar beacon and pulsing skeleton screens.
     - `src/components/upload/DocumentCard.jsx`: Replace spinning loader with pulsing mini-beacon.
     - `src/components/upload/ReadinessCheck.jsx`: Replace spinning Activity icon with pulsing progress beacon.
     - `src/components/analysis/AuditTimeline.jsx`: Replace spinning ShieldCheck with cryptographic verification beacon.
     - `src/components/common/StatusBadge.jsx`: Replace spinning Activity with soft pulsing beacon.
     - `src/pages/Dashboard.jsx`: Replace spinning RefreshCw with smooth rotate transition.
   - Enhance `src/components/common/Skeletons.jsx` with rich pulsing shimmers and add `ClaimDrawerSkeleton`, `TimelineSkeleton`, `AuditorScannerHUD`, `PulsingBeacon`, `ShimmerBar`.
   - Update `tests/component-harness.jsx:99` assertion to match the modern pulsing beacon.

4. Verification:
   Run all verification steps and document in handoff:
   - `npm test` (72/72 tests pass)
   - `node tests/check-imports.mjs` (0 unresolved imports)
   - `node tests/check-circular-deps.mjs` (0 cycles)
   - `node tests/run-stress-tests.mjs` (41/41 SSR pass, all challenger suites pass)
   - `npm run build` (builds cleanly with exit code 0)

Deliverable:
Write a comprehensive handoff report to `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m7_motion\handoff.md`.
Notify the orchestrator via send_message when complete.
