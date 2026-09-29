# ClaimGuard AI — Component Survey & Quality Assurance Audit Report

**Date**: 2026-09-18  
**Auditor**: `explorer_survey_components_qa`  
**Workspace**: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend`  
**Evaluation Target**: Newly added components, runtime stability, test harnesses, API resilience, and UI/UX polish against prompt specifications (notably `2026-09-18T03:55:30Z`).

---

## 1. Executive Summary

A comprehensive architectural and empirical verification survey was conducted across the ClaimGuard AI React frontend. The codebase represents an enterprise healthcare statutory adjudication and fraud detection application designed around IRDAI Master Circular (May 2024), Insurance Act 1938 § 45, and Central Government Health Scheme (CGHS) benchmarks.

### Key Highlights
- **Existing Test Suites**: 
  - `npm test`: **72 of 72 tests passing (100%)** across 4 evaluation tiers (Feature Coverage, Boundary Cases, Cross-Module Combinations, Real-World E2E Journeys).
  - `tests/run-stress-tests.mjs`: Successfully compiles SSR test bundles and runs 4 adversarial challenger suites with 154+ stress scenarios.
  - Dependency verification: **0 unresolved imports** across 29 modules; **0 circular dependencies**.
- **Identified Deficiencies & Latent Bugs**:
  - **CRITICAL [HIGH]**: `FinancialWaterfallChart` in `DashboardCharts.jsx` crashes with `TypeError: Cannot read properties of undefined (reading 'amount')` when passed custom or truncated step arrays (`dynamicSteps[2].amount` without optional chaining).
  - **MEDIUM**: Upload size validation in `BatchDropzone.jsx` fails to reject negative file sizes (`-1` byte passes validation).
  - **LOW**: Non-numeric/NaN file sizes pass upload validation.
  - **LOW**: MIME validation bypass allows `.exe` files with spoofed `application/pdf` MIME headers due to loose logical OR/AND evaluation.
  - **LOW**: Filename regex auto-tagging has substring false-positive collision: "daycare_procedure_bill.pdf" matches "care" and incorrectly classifies as `INSURANCE_POLICY` instead of `HOSPITAL_BILL`.
  - **CODE SMELL / REDUNDANCY**: Two `VerdictCard.jsx` implementations exist (`src/components/VerdictCard.jsx` and `src/components/analysis/VerdictCard.jsx`).
  - **SECURITY / ROBUSTNESS**: Clipboard operations lack `try...catch` and unhandled Promise rejection guards in non-HTTPS / restricted iframe contexts. Object URLs in `AppealLetter.jsx` are created without calling `URL.revokeObjectURL()`.
  - **GAP VS BENCHMARK PROMPT (2026-09-18T03:55:30Z)**: `framer-motion` and `sonner` are not yet installed in `package.json`. Contextual sidebars (drawers) for claim details and strict Bento Grid layout are pending implementation.

---

## 2. Component-by-Component Technical Audit

### 2.1 ForensicsLab.jsx (`src/components/analysis/ForensicsLab.jsx`)
- **Primary Features**:
  - Pure SVG Circular ELA Tamper Gauge (`ElaTamperGauge`): 240° sweep arc (from 150° to 390° / -120° to +120°), calibrated tick marks (0, 25, 50, 75, 100), dynamic color gradient (`#059669` → `#10B981` → `#D97706` → `#E11D48`), animated needle pointer with drop shadow.
  - Hardware Provenance & Metadata Inspector: EXIF inspection, PDF producer validation (Canon imageRUNNER vs Adobe Normalizer), timestamp parity checks, DPI optical density (300 DPI), and SHA-256 checksums.
  - Interactive Forensic Heatmap & Document Viewer: 3 view modes (`Original Document`, `Forensic Heatmap`, `Blend Overlay`), opacity slider (0–100%), and zoom controls (80%–140% with reset).
  - CGHS Official Tariff Comparator: City schedule selector (Bengaluru, Delhi-NCR, Mumbai), comparative horizontal bars (Hospital Billed in amber vs CGHS Official in teal), delta badges, and IRDAI statutory admissibility caveats.
  - Clinical Consistency Matrix: ICD-10 cross-referencing (Cholelithiasis K80.20) against billed surgical items, prophylaxis antibiotics, and disallowed medications.
- **Latent Issues & Vulnerabilities**:
  1. *Static Benchmark Data*: The `benchmarkItems` and `consistencyItems` arrays are declared inside the component body, recreating object references on every render.
  2. *City Schedule Disconnect*: Switching the city selector state (`selectedMetro`) updates UI state but does not alter procedure benchmark rates.
  3. *SVG ID Collision*: Filter IDs (`#noiseFilter`, `#elaGaugeGrad`, `#gaugeShadow`) are hardcoded; rendering multiple instances causes DOM ID conflicts.
  4. *Mobile Zoom Pan*: While container has `overflow-x-auto`, zooming to 140% on mobile displays requires two-finger pan which is not touch-optimized.

### 2.2 FinancialDelta.jsx (`src/components/analysis/FinancialDelta.jsx`)
- **Primary Features**:
  - 4-metric executive KPI grid: Total Billed Amount (Gross), Insurer Approved (Sanctioned), Total Disallowed (Haircut), and Contested & Recoverable (Hero Metric with IRDAI yield pill).
  - Capital Allocation Waterfall Bar: Proportional stacked segments (`approvedPct`, `recoverablePct`, `legitimatePct`) with interactive hover states and legend cards.
  - Itemized Statutory Discrepancy Breakdown: Cards with IRDAI Master Circular May 2024 and Insurance Act § 45 citations.
- **Latent Issues & Vulnerabilities**:
  1. *Null Pointer Vulnerability*: Default parameter `result = {}` only catches `undefined`. If `result={null}` is passed, lines 49–53 (`result.total_insurer_calculation`) and line 91 (`result.rule_verdicts`) throw `TypeError: Cannot read properties of null`.
  2. *React Key Warning*: Line 329 uses `key={v.rule_name || i}`. If multiple verdicts share the same rule name or rule name is undefined, duplicate keys may be generated.
  3. *Division Safety*: Line 84 computes `(recoverableAmount / insurerPaid) * 100`. If `insurerPaid` is 0, it safely returns `'0.0'`, but if `insurerPaid` is negative or malformed, it produces unexpected strings.

### 2.3 VerdictCard.jsx (`src/components/analysis/VerdictCard.jsx` & `src/components/VerdictCard.jsx`)
- **Primary Features**:
  - Dual-Tier Categorization: Auto-classifies Tier 1 (Mandatory Statutory Rules: Proportionate deduction, moratorium, mental health) vs Tier 2 (Clinical/Policy Conditions).
  - Calculation Delta Reconciliation: Proportional dual bars comparing Insurer Calculated settlement (struck through in red) vs Statutory Correct Allowable amount (in emerald).
  - 1-Click Clipboard Citation: Copies statutory regulatory citation to clipboard with toast notification.
  - Legal Appeal Directives: Callout boxes containing legal grievance arguments.
  - `VerdictsFilterTabs`: Tab bar with dynamic counters for All, Tier 1, Tier 2, and Conflicts Only.
- **Latent Issues & Vulnerabilities**:
  1. *Component Duplication*: `src/components/VerdictCard.jsx` (legacy simple version, 117 lines) vs `src/components/analysis/VerdictCard.jsx` (modern enterprise version, 385 lines). `Analysis.jsx` imports the enterprise version, while legacy tests inspect the old version.
  2. *Null Pointer on `verdict`*: If `verdict={null}` is passed, line 35 (`verdict.status === 'FAIL'`) throws `TypeError`.
  3. *Unhandled Clipboard Promise*: In non-secure contexts (HTTP / sandboxed iframes), `navigator.clipboard.writeText` returns a rejected Promise that is not wrapped in `try...catch`.
  4. *Unmount Timer Leak*: `setTimeout(() => setCopied(false), 2500)` lacks cleanup on unmount.

### 2.4 AuditTimeline.jsx (`src/components/analysis/AuditTimeline.jsx`)
- **Primary Features**:
  - Cryptographic SHA-256 Ledger: FIPS 180-4 compliant block presentation.
  - Interactive "Verify Hash Chain": Iterates chronological blocks and verifies `block[i].previous_hash === block[i-1].entry_hash`, providing visual feedback.
  - Hash linking: Connects previous block hash to current block entry hash with 1-click clipboard copy.
  - Collapsible JSON Payload Inspector: Displays raw metadata and action payloads.
- **Latent Issues & Vulnerabilities**:
  1. *Date Parsing RangeError*: Line 213 executes `new Date(block.created_at).toUTCString()`. If `block.created_at` is invalid or corrupted, `.toUTCString()` throws `RangeError: Invalid time value` and crashes the timeline.
  2. *Zero Blocks Verification*: If `auditTrail.audit_logs` is empty, `handleVerifyChain` reports `All 0 Blocks Sealed & Valid`.
  3. *Unmounted Timeout*: `setTimeout` in `handleVerifyChain` (1100ms) is not cancelled if the user navigates away mid-verification.

### 2.5 AppealLetter.jsx (`src/components/analysis/AppealLetter.jsx`)
- **Primary Features**:
  - Formal Legal Grievance Letterhead: Standardized format addressed to the Insurer's Grievance Redressal Officer (GRO).
  - Dual Mode (View vs Edit): Toggle between printable hospital letterhead (St. Jude Multi-Specialty Hospital, NABH accredited) and editable textarea draft.
  - Textarea Metrics: Real-time character count and word count.
  - Export Options: 1-click clipboard copy, plain text (`.txt`) file download, and native `@media print` print layout.
- **Latent Issues & Vulnerabilities**:
  1. *Memory Leak on Object URL*: Line 74 creates a blob URL via `URL.createObjectURL(file)`, but `URL.revokeObjectURL()` is never invoked.
  2. *Empty Word Count Glitch*: If `draftContent` is empty string `""`, `"".trim().split(/\s+/).length` returns `1` instead of `0`.
  3. *Static Dispute Grounds*: While header reference values are dynamic, the grounds paragraphs (lines 284, 295) specifically hardcode ₹32,000 for Cholecystectomy and ₹10,500 for hypertension, regardless of what claim is viewed.

### 2.6 ClaimsTable.jsx (`src/components/dashboard/ClaimsTable.jsx`)
- **Primary Features**:
  - Enterprise Filter Tabs: 5 tabs (`All`, `Flagged`, `Approved`, `Under Review`, `Disallowed`) with dynamic calculated badge counts.
  - Multi-Column Sorting: Supports ascending/descending sorts across Claim ID, Patient & Policy, Date, Total Billed, Disallowed Impact, and Audit Status.
  - Multi-Document Presence Pills: Dedicated `BILL`, `POL`, `REJ` indicators displaying tripartite extraction status.
  - Pagination Engine: First/Prev/Next/Last controls, numbered pills, ellipsis windowing, and page size selector (10, 25, 50).
  - CSV Export with Sanitization: Escapes quotation marks and prepends single quotes (`'`) to Excel DDE formula prefixes (`=`, `+`, `-`, `@`).
- **Latent Issues & Vulnerabilities**:
  1. *Numeric CSV Injection*: Text columns are sanitized with `sanitizeCsvCell()`, but numeric columns (`total_amount`, `monetary_impact`) are appended directly. If a monetary impact is negative (e.g. `-5000`), it begins with `-`, which Excel treats as a formula.
  2. *Data URL Size Limitation*: CSV export uses `data:text/csv;charset=utf-8,` with `encodeURI()`. On datasets exceeding ~2MB (thousands of claims), browsers truncate data URLs. A `Blob` with `URL.createObjectURL()` should be used.
  3. *Un-debounced Search Filter*: Typing into the search box executes filtering across all rows synchronously on every keystroke. While fast for 1,500 claims (~4.6ms), a 150ms debounce would prevent unnecessary recalculations.

### 2.7 DashboardCharts.jsx (`src/components/dashboard/DashboardCharts.jsx`)
- **Primary Features**:
  - Pure SVG `StatusDonutChart`: Interactive slices with hover effects, slice gap calculations (`2.5px`), and click-to-filter cross-filtering callback.
  - Pure CSS/SVG `FinancialWaterfallChart`: Visualizes Billed → Approved → Disallowed → Recoverable → Net Settlement with floating metric pills and hover tooltips.
  - `RuleConflictBarChart`: Lists top IRDAI rule breaches, with sort toggle by Frequency vs Recoverable Amount, win-rate pills, and citation copying.
- **Latent Issues & Vulnerabilities**:
  1. **CRITICAL [HIGH] BUG (`WATERFALL-02`)**: Lines 442, 446, 450 in `FinancialWaterfallChart`:
     ```jsx
     <span>Billed: {formatCompactInr(dynamicSteps[0].amount)}</span>
     <span>Deducted: {formatCompactInr(dynamicSteps[2].amount)}</span>
     <span>Recovered: +{formatCompactInr(dynamicSteps[3].amount)}</span>
     ```
     If custom `steps` is passed with fewer than 4 items or an empty array `[]`, `dynamicSteps[2]` is undefined, throwing:
     `TypeError: Cannot read properties of undefined (reading 'amount')` and crashing the entire React dashboard.
     *Fix*: Use optional chaining: `dynamicSteps[0]?.amount`, `dynamicSteps[2]?.amount`, `dynamicSteps[3]?.amount`.

### 2.8 Upload Studio Components (`BatchDropzone.jsx`, `ReadinessCheck.jsx`, `DocumentCard.jsx`)
- **Primary Features**:
  - `BatchDropzone`: Dual-mode intake (Batch Multi-Drop vs Guided 3-Step Targets). 25MB boundary validation, MIME whitelist, drag-and-drop active visual rings.
  - `autoTagDocument`: Regex classification of filenames into `HOSPITAL_BILL`, `INSURANCE_POLICY`, or `REJECTION_LETTER`.
  - `DocumentCard`: Displays attached document format chips (PDF, JPG, PNG, TIFF), file size, verification badge, extracted metadata preview (line items, sum insured, hospital), replace, remove, and category retag selector.
  - `ReadinessCheck`: 3-segment progress indicator, tripartite verification checklist, 4-stage sequential extraction animation ticker, and 1-Click Apollo Benchmark Claim loader (`CLM-84920`).
- **Latent Issues & Vulnerabilities**:
  1. **[MEDIUM] SIZE-04 (Negative File Size)**: In `validateUploadFile`:
     ```js
     if (!file || file.size === 0) { ... }
     if (file.size > MAX_FILE_SIZE) { ... }
     ```
     Negative file sizes (`file.size < 0`, e.g. `-1`) bypass both conditions and pass validation.
  2. **[LOW] SIZE-05 (NaN File Size)**: If `file.size` is `NaN`, both comparisons evaluate to `false`, allowing invalid non-numeric sizes to pass.
  3. **[LOW] MIME-06 (MIME Spoofing)**:
     ```js
     if (!isMimeAllowed && !isExtAllowed)
     ```
     Because of the logical AND `!isMimeAllowed && !isExtAllowed`, a file with a spoofed MIME type (e.g. `application/pdf`) and an executable extension (`malware.exe`) is accepted! The rule should require that BOTH extension and MIME type match, or strictly reject blacklisted extensions.
  4. **[LOW] TAG-08 (Heuristic Collision on "care")**:
     ```js
     if (/(policy|schedule|coverage|ins|insurance|star|care|hdfc...)/i.test(name))
     ```
     The token `care` matches within `daycare_procedure_bill.pdf`, incorrectly classifying a hospital bill as an insurance policy.

### 2.9 API Integration & Normalizers (`src/services/api.js`, `mockData.js`)
- **Primary Features**:
  - Axios client with 10,000ms timeout and `/api` base URL.
  - 11 endpoint wrappers: `uploadDocument`, `triggerAnalysis`, `getAnalysisStatus`, `getAnalysisResult`, `getReport`, `getAppealDraft`, `getAuditTrail`, `getDocuments`, `healthCheck`, `getClaims`, `getStats`.
  - Offline Fallback Engine: Every API function catches network errors and falls back to normalized mock fixtures.
  - Normalization helpers: `normalizeStats`, `normalizeClaims`, `normalizeAnalysisResult`, `normalizeAppealDraft` ensure backward compatibility with legacy property names (`total_amount_recovered`, `pending_claims`).
- **Latent Issues & Vulnerabilities**:
  1. *Error Boundary Suppression*: Catching all axios errors inside the service functions and returning mock data means React Query and callers never experience a rejected promise. As a result, React Query `isError` is always `false`, preventing standard error boundaries or retry mechanisms from triggering on network loss.
  2. *Empty State Masking*: `normalizeClaims([])` returns `mockClaims`. If an active backend database legitimately has zero claims, the UI displays 8 sample claims rather than the designed empty state.
  3. *Missing Bearer Token Interceptor*: `api.js` does not attach an `Authorization: Bearer <token>` interceptor from browser storage, preventing authenticated enterprise communication.

---

## 3. Survey of Existing Verification Harnesses

| Suite / Script | Location | Type | Status | Coverage / Scenarios |
| :--- | :--- | :--- | :--- | :--- |
| **Main Test Runner** | `tests/runner.mjs` (`npm test`) | Node.js E2E & Contract Harness | **PASSED (72/72)** | 100% pass rate across Tier 1, 2, 3, 4 |
| - *Tier 1: Feature Coverage* | `tests/tier1-feature-coverage.test.mjs` | Contract & Schema | Passed (30/30) | API endpoints, normalizers, TypeScript data models, status badge mapping, currency formatting, stepper machine |
| - *Tier 2: Boundary Cases* | `tests/tier2-boundary-cases.test.mjs` | Adversarial Boundaries | Passed (28/28) | 0-25MB file boundaries, MIME types, extreme crore amounts, room rent ratios, moratorium 36m vs 60m, ELA score 0-100, CGHS multipliers, divide-by-zero math |
| - *Tier 3: Combinations* | `tests/tier3-combinations.test.mjs` | Cross-Module Matrix | Passed (9/9) | Tripartite documents, concurrent rule conflicts, compound fraud risk, clinical consistency, cryptographic SHA-256 chain integrity |
| - *Tier 4: Real-World E2E* | `tests/tier4-real-world-scenarios.test.mjs` | User Journey Workflows | Passed (5/5) | Apollo Hospital bill journey, high-risk fraud journey, clean settlement journey, moratorium protection, network recovery |
| **SSR Component Stress** | `tests/run-stress-tests.mjs` | Vite SSR Runtime Bundle | **PASSED (41/41)** | StatusBadge, MetricCard, Skeletons, ErrorState, Topbar, App Shell routes, ExecutiveKpiCards, DashboardCharts, ClaimsTable |
| **Challenger M1: Adversarial**| `tests/challenger-m1-stress.mjs` | Normalizer Stress | **PASSED (34/34)** | Extreme inputs, nulls, primitive strings, shallow clone isolation, 11 offline mock endpoints |
| **Challenger M2: Chart Math** | `tests/challenger-m2-charts-stress.mjs` | Geometry & SVG Math | **21 Passed / 2 Findings** | Identified `WATERFALL-02` crash on truncated steps and `CALLBACK-03` non-function prop |
| **Challenger M2: Table Stress**| `tests/challenger-m2-table-stress.mjs`| Table & Big Data | **PASSED (41/41)** | 1,500 claims benchmark (4.37ms tab count, 4.62ms search), hostile regex, XSS/SQLi literal filtering, CSV DDE formula sanitization |
| **Challenger M3: Upload Stress**| `tests/challenger-m3-upload-stress.mjs`| File Engine Stress | **52 Passed / 4 Findings** | Identified `SIZE-04` negative size, `SIZE-05` NaN size, `MIME-06` spoofed mime, and `TAG-08` "care" collision |
| **Import Integrity Check** | `tests/check-imports.mjs` | AST Import Scanner | **PASSED (29/29 files)**| Zero unresolved relative or external package imports |
| **Circular Dependency Check** | `tests/check-circular-deps.mjs` | DFS Cycle Detection | **PASSED (28 modules)** | Zero circular dependency cycles in `src/` |

---

## 4. UI/UX Polish, Layout, Z-Index & Runtime Stability

### 4.1 Z-Index Layering Hierarchy
The application maintains a consistent z-index hierarchy:
- `z-10`: Interactive cards, block step indicators, stepper nodes.
- `z-30`: `Topbar.jsx` (sticky glass-morphic header).
- `z-50`: Global search dropdown suggestions, waterfall hover tooltips, mobile navigation drawer backdrop and drawer panel.
- `z-9999`: `react-hot-toast` notification container.
*Observation*: No z-index collisions or unintended layering overlaps were detected between tooltips and sticky headers.

### 4.2 Viewport Responsiveness & Layout Overflow
- **Dashboard Grid**: The 4 KPI cards collapse from 4 columns (`lg:grid-cols-4`) to 2 columns (`sm:grid-cols-2`) and 1 column (`grid-cols-1`) cleanly.
- **Charts Row**: The 12-column grid (`lg:col-span-5` for Donut and `lg:col-span-7` for Waterfall) stacks vertically on viewports under 1024px.
- **Table Overflow**: `ClaimsTable.jsx` wraps its `<table>` in `overflow-x-auto`. Minimum column widths (`min-w-[170px]`, `min-w-[190px]`, etc.) prevent squished data on mobile.
- **Forensics Canvas**: The document viewer has `overflow-x-auto` to handle scale factors up to 140%.

### 4.3 Build Artifacts & Bundle Size
Running `npm run build` succeeds in 5.95s:
- Minified CSS: `dist/assets/index-vnM-UR5m.css` (62.75 kB / gzip: 10.19 kB)
- Minified JS: `dist/assets/index-CMVFyoe2.js` (557.66 kB / gzip: 161.11 kB)
*Vite Warning*: Chunk size exceeds 500 kB. Code-splitting routes (`Upload` and `Analysis`) via `React.lazy()` or configuring Rollup `manualChunks` (splitting `lucide-react` and `@tanstack/react-query`) will reduce main chunk size below 200 kB.

### 4.4 Prompt Delta Analysis (2026-09-18T03:55:30Z)
The latest project prompt introduces specific enterprise requirements:
1. **Hardware-accelerated animations with `framer-motion`**: Not yet installed in `package.json`. Animations currently rely on CSS transitions and Tailwind utility classes.
2. **Stacked toast notifications (`sonner`)**: The project currently uses `react-hot-toast`. Replacing or augmenting with `sonner` will deliver stacked toast physics.
3. **Bento Grid Layout**: The dashboard uses a traditional grid layout. Restructuring into an asymmetric, high-density Bento Grid with varied tile spans will fulfill R2.
4. **Contextual Sidebar / Drawers for Claim Details**: Clicking a row currently navigates to `/analysis/:id`. A slide-out drawer pattern will allow rapid triage without losing table context.

---

## 5. Hardening & Verification Checklist

The following concrete tasks should be executed to achieve production-grade quality:

### Priority 1: Critical Stability & Runtime Fixes (Must Fix)
- [ ] **Fix Waterfall Chart Undefined Steps Crash**:
  - In `src/components/dashboard/DashboardCharts.jsx` (lines 442, 446, 450), add optional chaining: `dynamicSteps[0]?.amount ?? 0`, `dynamicSteps[2]?.amount ?? 0`, `dynamicSteps[3]?.amount ?? 0`.
- [ ] **Harden File Size Validation**:
  - In `src/components/upload/BatchDropzone.jsx`, update `validateUploadFile`:
    ```javascript
    const size = Number(file?.size);
    if (!file || isNaN(size) || size <= 0) {
      return { valid: false, error: `File "${file?.name || 'document'}" is empty or invalid (0 bytes)` };
    }
    ```
- [ ] **Harden MIME & Extension Whitelist**:
  - In `validateUploadFile`, strictly verify that extension matches whitelist and prevent spoofed `.exe` or disallowed extensions from passing when MIME type is spoofed:
    ```javascript
    if (!isExtAllowed || (!isMimeAllowed && mime !== '')) {
      return { valid: false, error: `File type "${ext || file.type}" is not supported` };
    }
    ```
- [ ] **Fix Substring Collision in Filename Auto-Tagging**:
  - In `autoTagDocument`, replace substring `care` with word-boundary `\bcare\b` so `daycare_procedure_bill.pdf` is correctly classified as `HOSPITAL_BILL`.
- [ ] **Safe Date Parsing in Audit Timeline**:
  - In `src/components/analysis/AuditTimeline.jsx`, wrap date formatting in a safe helper to prevent `RangeError: Invalid time value` on malformed timestamps:
    ```javascript
    const formatDateSafe = (d) => {
      try {
        const date = new Date(d);
        return isNaN(date.getTime()) ? 'Timestamp Sealed' : date.toUTCString();
      } catch { return 'Timestamp Sealed'; }
    };
    ```

### Priority 2: Security & Defect Hardening
- [ ] **Sanitize Numeric CSV Export Columns**:
  - In `ClaimsTable.jsx`, pass `total_amount` and `monetary_impact` through `sanitizeCsvCell()` to neutralize leading `-` formula signs.
- [ ] **Replace CSV Data URL with Blob URL**:
  - In `ClaimsTable.jsx`, replace `data:text/csv` URI with `new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })` and `URL.createObjectURL(blob)`, revoking the URL after download.
- [ ] **Wrap Clipboard Operations**:
  - Wrap all `navigator.clipboard.writeText()` calls across `VerdictCard.jsx`, `AuditTimeline.jsx`, `AppealLetter.jsx`, `ClaimsTable.jsx`, and `DashboardCharts.jsx` with `try...catch` and `.catch(() => toast.error('Clipboard permission denied'))`.
- [ ] **Revoke Object URLs in AppealLetter**:
  - In `AppealLetter.jsx`, call `URL.revokeObjectURL(element.href)` inside a `setTimeout` after triggering text file download.
- [ ] **Consolidate `VerdictCard.jsx`**:
  - Re-export `src/components/analysis/VerdictCard.jsx` from `src/components/VerdictCard.jsx` to eliminate duplicate implementations.

### Priority 3: UI/UX & Architectural Polish (Prompt R1/R2)
- [ ] **Install Animation & Toast Libraries**:
  - Add `framer-motion` and `sonner` to `package.json`.
- [ ] **Implement Contextual Claim Drawer**:
  - Add a slide-out drawer on the Dashboard for instant preview of rule verdicts, ELA score, and financial delta when clicking a row in `ClaimsTable`.
- [ ] **Restructure Bento Grid**:
  - Refactor `Dashboard.jsx` to use an asymmetric Bento Grid layout for KPI metrics and charts with soft diffused borders (`0 4px 20px rgba(0,0,0,0.03)`).
- [ ] **Route-Based Code Splitting**:
  - Use `React.lazy()` for `/upload` and `/analysis` routes in `App.jsx` to reduce initial bundle chunk size below 200 kB.

---

## 6. Verification Method

To verify these survey findings:
1. Run main test suite:
   ```bash
   npm test
   ```
2. Run stress test suite (including challenger modules):
   ```bash
   node tests/run-stress-tests.mjs
   ```
3. Run import resolution and circular dependency checks:
   ```bash
   node tests/check-imports.mjs
   node tests/check-circular-deps.mjs
   ```
4. Build production bundle and check chunk sizes:
   ```bash
   npm run build
   ```
