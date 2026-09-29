# Project: ClaimGuard AI Frontend Overhaul

## Architecture
- **Framework**: React 18 with Vite 6, Tailwind CSS 3.4, React Router v6, TanStack Query v5, Axios, Lucide React, Hot Toast.
- **Design System**: Enterprise Healthcare standards — high information density, clinical slate-900/navy hierarchy, medical teal/cyan accents, and standardized status semantics (Emerald/Pass, Amber/Discrepancy, Rose/Conflict-Fraud, Blue/Analysis).
- **Visualization Layer**: Interactive SVG/CSS & charting components for financial waterfalls, donut status distributions, rule conflict metrics, ELA tamper gauges, and CGHS benchmark bars.
- **Module Boundaries & Code Layout**:
  - `src/types/index.ts`: Unified TypeScript definitions covering all backend schemas (Claim, HospitalBill, InsurancePolicy, RejectionLetter, RuleVerdict, ForensicsResult, AuditTrail).
  - `src/services/api.js`: Resilient API client with data normalization, fallback resilience, and support for all backend endpoints.
  - `src/components/common/`: Shared UI primitives — Skeletons, StatusBadge, Topbar, MetricCard, ErrorBoundary, Tooltips, EmptyStates.
  - `src/components/dashboard/`: Dashboard visual widgets — DashboardCharts (Donut, Waterfall, Bar), ClaimsTable (search, filter tabs, multi-doc pills, sorting, pagination).
  - `src/components/upload/`: UploadStudio (dual-mode: batch multi-drop & guided stepper, document cards with metadata inspection, pre-analysis check).
  - `src/components/analysis/`: Analysis & Forensics Hub — Executive Financial Delta, VerdictCard (rule verdicts with slider/delta bar & IRDAI citations), ForensicsLab (ELA tamper meter, heatmap viewer, CGHS benchmark comparator, clinical consistency matrix), AuditTrailTimeline (SHA-256 block ledger), AppealLetterViewer (letterhead formatting, clipboard copy, print).
  - `src/pages/`: Dashboard.jsx, Upload.jsx, Analysis.jsx.
  - `src/App.jsx`: Enterprise layout shell with desktop Topbar (breadcrumbs, global claim search, tenant selector, auditor profile) and enhanced sidebar.

## Feature Inventory
Every feature from the Survey phase must appear here with its assigned milestone.
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Enterprise Design Tokens & Theme | Custom Tailwind palette (slate, teal, emerald, amber, rose), typography hierarchy, utility classes | M1 | Survey R1 (DONE) |
| 2 | Unified TypeScript Data Contracts | Standardized interfaces for Claims, Bills, Policies, Rejections, RuleVerdicts, Forensics, AuditTrail | M1 | Survey R1 (DONE) |
| 3 | Shared Component Library & Skeletons | StatusBadge, MetricCard, realistic Skeletons, ErrorBoundary, EmptyState, Toast notifications | M1 | Survey R3 (DONE) |
| 4 | Enterprise App Shell & Navigation | Desktop Topbar (breadcrumbs, global claim search, auditor profile, tenant badge), active route sidebar, live API status pill | M1 | Survey R1 (DONE) |
| 5 | Resilient API Client & Schema Normalizer | Correct field mapping (`total_recovered_amount`, `appeal_text`, unwrapped `result.result`, mock resilience) | M1 | Survey R1/API (DONE) |
| 6 | Executive Financial KPI Cards | 4 enhanced metrics with sparklines, INR formatting, variance pills, recovery velocity | M2 | Survey R1 (DONE) |
| 7 | Dashboard Visualizations | Interactive charts: Status distribution donut, Recoverable amount waterfall, Rule conflict frequency | M2 | Survey R2 (DONE) |
| 8 | Enterprise Claims Data Table | Search by Claim ID/Patient, status filter tabs, sortable columns, multi-doc status badges (BILL/POL/REJ), pagination | M2 | Survey R1 (DONE) |
| 9 | Dual-Mode Upload Studio | Smart multi-file dropzone (batch drop 3 files at once) + non-blocking guided stepper mode | M3 | Survey R3 (DONE) |
| 10 | Document Metadata & Extraction Inspection | Document cards showing file size, format chips, thumbnail icon, replace/remove actions | M3 | Survey R3 (DONE) |
| 11 | Pre-Analysis Health Check & UX Transitions | Visual readiness checklist (Bill items, Policy sum insured, Rejection reasons) with smooth animation | M3 | Survey R3 (DONE) |
| 12 | Executive Financial Delta & Reconciliation | High-impact visual comparison: Billed vs Insurer Approved vs Disallowed vs Recoverable with proportion bar | M4 | Survey R2 |
| 13 | Interactive Rule Verdicts & Statutory Engine | Categorized Tier 1/Tier 2 cards, visual delta bar (Insurer vs Correct), IRDAI clause copy button | M4 | Survey R2 |
| 14 | Digital Forensics & Fraud Detection Lab | ELA tamper score meter (0-100 gauge), heatmap viewer, CGHS tariff benchmark comparator, clinical consistency | M4 | Survey R2 |
| 15 | Cryptographic SHA-256 Audit Trail | Interactive chronological timeline of pipeline events with SHA-256 hash chain verification badge | M4 | Survey R2 |
| 16 | Formal Legal Appeal & Grievance Generator | Letterhead format, IRDAI citation inclusion, clipboard copy, print/PDF layout, editable draft | M4 | Survey R2 |
| 17 | Comprehensive E2E Verification & Hardening | Full build test, automated component & integration tests, cross-browser responsiveness, error state verification | M5 | Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Foundations, Design Tokens & Shell | Tailwind theme, typography, types, API client normalizer, shared components, topbar/sidebar app shell | none | COMPLETED |
| M2 | Enterprise Dashboard & Visualizations | Executive KPI cards, DashboardCharts (donut, waterfall, bar), advanced searchable/sortable claims table | M1 | COMPLETED |
| M3 | Upload Studio & UX Polish | Dual-mode batch/stepper upload, document preview cards, pre-analysis check, loading/error states | M1 | COMPLETED |
| M4 | Analysis & Forensics Hub | 4-tab workspace: Financial reconciliation & Rule verdicts, Forensics Lab (ELA/CGHS), Audit Trail, Grievance Letter | M1, M2, M3 | ACTIVE |
| M5 | E2E Verification & Victory Hardening | Automated tests, test runner, full production build validation, edge-case coverage | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Foundations (M1), Dashboard (M2), Upload (M3) -> Analysis Hub (M4)
- Design Tokens: `tailwind.config.js` provides `theme.extend.colors` (`brand`, `medical`, `status`), fonts, and shadow classes.
- API Client: `src/services/api.js` exports normalized functions `getStats()`, `getClaims()`, `getAnalysisResult(id)`, `getReport(id)`, `getAppealDraft(id)`, `getAuditTrail(id)`, `uploadDocument(...)`.
- Types: `src/types/index.ts` provides all data contracts.
- Layout: `src/App.jsx` wraps views with responsive shell, topbar, and sidebar.
- Navigation: `Upload.jsx` navigates to `/analysis/:newClaimId`; `ClaimsTable.jsx` rows navigate to `/analysis/:id`.
