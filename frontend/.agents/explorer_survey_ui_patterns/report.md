# ClaimGuard AI — Frontend UI Patterns, Layout Architecture & Design Token Survey

**Timestamp**: 2026-09-18T03:57:34Z  
**Investigator**: `explorer_survey_ui_patterns`  
**Target Repository**: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend`  
**Integrity Mode**: Benchmark / Production-Ready Overhaul  

---

## 1. Executive Summary

A comprehensive forensic survey of the ClaimGuard AI React frontend was conducted across layout architecture, navigation flows, typography, shadow/border design tokens, and pipeline notifications.

The application possesses strong medical and financial audit foundations (with pure SVG charts, robust mathematical calculations, and 72/72 passing test suites), but exhibits notable architectural and interaction bottlenecks that prevent it from achieving top-tier enterprise SaaS quality:

1. **Dashboard Layout is a Linear Stack, not a Bento Grid**: Currently, `Dashboard.jsx` is structured as a vertical sequence of detached containers (`space-y-6`) comprising an alert banner, a rigid 4-card horizontal strip (`ExecutiveKpiCards.jsx`), two chart rows (`DashboardCharts.jsx`), and a separate full-width table (`ClaimsTable.jsx`). It lacks the asymmetric visual hierarchy, unified grid coordinate system, and dense information packing characteristic of modern enterprise Bento Grids.
2. **Claim Inspection Causes Destructive Navigation & State Loss**: Clicking any claim row or action button in `ClaimsTable.jsx` invokes `navigate('/analysis/' + claimId)`. This performs a full-page client route navigation that unmounts `Dashboard.jsx`, destroying all auditor workspace state (active search filters, pagination page index, status tab selections, sort configurations, and scroll positions). When the auditor clicks "Back", all filters reset to defaults.
3. **Typography Tokens are Solid but Can Be Heightened**: Google Fonts loads `Inter` (300-800) and `JetBrains Mono`. Tailwind defaults `font-sans` to `Inter` and `font-mono` to `JetBrains Mono`. Muted `slate-*` colors are strictly adhered to (zero `gray-*` regressions detected). However, tabular financial figures require stricter alignment rules, and subtitle contrasts need sharper hierarchy.
4. **Shadows and Outdated Borders Require Refinement**: The requested ultra-soft diffused shadow token (`0 4px 20px rgba(0,0,0,0.03)`) is missing from `tailwind.config.js`. Several legacy components and sections still use harsh or heavy default shadows (`shadow-lg shadow-sky-950/50`, `shadow-xl`, `shadow-md`), and some legacy cards lack the crisp `1px` subtle border standard (`border-slate-200/90`).
5. **Toast Notifications Rely on Legacy Unstacked Library**: The project currently uses `react-hot-toast`, which renders disjointed floating badges without card-stacking physics. Replacing this with `sonner` in `App.jsx` will introduce stacked notification physics, native action buttons (e.g. "View Dossier", "Undo"), and dynamic pipeline event updates across file uploads, multi-stage OCR extraction, and statutory citation copies.

---

## 2. Component & File Inventory

The following core files were inspected:

| File Path | Role | Key Findings & Deficiencies |
|:---|:---|:---|
| `src/pages/Dashboard.jsx` | Main dashboard page | Linear vertical layout (`space-y-6`), disconnected alert banner, no Bento grid container. |
| `src/components/dashboard/ExecutiveKpiCards.jsx` | 4 KPI summary cards | Homogeneous 4-column horizontal grid (`grid-cols-4`); lacks asymmetric hero weighting for recovered capital. |
| `src/components/dashboard/DashboardCharts.jsx` | Donut, Waterfall, and Bar charts | Divided into two disconnected rows (`lg:col-span-5` / `7` and full-width bar chart). |
| `src/components/dashboard/ClaimsTable.jsx` | Claims ledger & pagination | Row click (`handleRowClick`, line 420) forces full-page navigation to `/analysis/:id`. Table state is not preserved. |
| `src/pages/Analysis.jsx` | Full claim dossier (4 tabs) | Rich analysis suite; heavily unmounted and mounted during quick claim triage. |
| `src/pages/Upload.jsx` | Multi-step claim intake | Uses sequential `toast.success`/`toast.error` without stacked pipeline stage tracking. |
| `src/components/common/MetricCard.jsx` | KPI card base component | Good SVG sparkline support; needs subtle diffused shadow and tighter padding for Bento integration. |
| `src/components/common/Topbar.jsx` | Global header & quick search | Triggers full-page navigation on quick-search selection. |
| `src/App.jsx` | Application shell & routing | Holds `react-hot-toast` `<Toaster>` with fixed dark theme styling and heavy sidebar shadow (`shadow-xl`). |
| `tailwind.config.js` | Tailwind design tokens | Lacks `diffused` shadow definition (`0 4px 20px rgba(0,0,0,0.03)`). |
| `src/index.css` | Global styling & utilities | Defines `.card-enterprise` using standard `boxShadow.card`. |

---

## 3. Survey 1: Dashboard Layout Architecture & Bento Grid Transformation

### Current Architecture (`Dashboard.jsx`)
In `Dashboard.jsx` (lines 131–221), the layout follows a sequential block structure:
```jsx
<div className="space-y-6 max-w-7xl mx-auto">
  {/* Header & Refresh */}
  <div className="flex flex-col sm:flex-row ...">...</div>

  {/* Priority Audit Alert Banner (Standalone band) */}
  <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 via-slate-800 ...">...</div>

  {/* 4 Equal-width KPI Cards */}
  <ExecutiveKpiCards stats={stats} claims={claims} />

  {/* Charts Container */}
  <DashboardCharts claims={claims} stats={stats} onSelectStatusFilter={handleSelectStatusFilter} />

  {/* Standalone Full-Width Table */}
  <div id="claims-table-section">
    <ClaimsTable ... />
  </div>
</div>
```

Inside `ExecutiveKpiCards.jsx`:
```jsx
<div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 ${className}`}>
  {/* 4 identical 1x1 cards */}
</div>
```

Inside `DashboardCharts.jsx`:
```jsx
<div className={`space-y-6 ${className}`}>
  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
    <div className="lg:col-span-5"><StatusDonutChart /></div>
    <div className="lg:col-span-7"><FinancialWaterfallChart /></div>
  </div>
  <RuleConflictBarChart />
</div>
```

### Limitations of Current Layout
1. **Lack of Visual Hierarchy**: Total Recovered Amount (`₹14,28,500`) is the primary value proposition of ClaimGuard AI, yet it receives identical visual real estate to Disallowance Rate (`18.4%`) and Processed Claims (`128`).
2. **Disconnected Alert Banner**: The alert banner sits as an isolated stripe between header and KPIs, disrupting visual flow. In enterprise healthcare dashboards, active dispute alerts should integrate directly as an urgent Bento triage card or an integrated status marquee.
3. **Information Fragmentation**: The screen requires extensive scrolling to correlate rule conflicts with the claims affected in the table below.

### Proposed Bento Grid Layout Architecture
A cohesive Bento Grid uses an asymmetric 12-column responsive layout with standardized card borders, micro-interactions, and visual density:

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ Page Header: Executive Audit Dashboard | Facility Context | Refresh & Upload Controls     │
├─────────────────────────────────────────┬───────────────────────────┬─────────────────────┤
│ [BENTO TILE 1: HERO METRIC]             │ [BENTO TILE 2: RISK]      │ [BENTO TILE 3: OPS] │
│ Total Recovered Capital                 │ Flagged & Discrepancies   │ Throughput & Claims │
│ ₹14,28,500 (+14.2%)                     │ 42 Detected | 14 Review   │ 128 Processed       │
│ Trajectory Sparkline + Velocity Tag     │ One-click "Filter Flagged"│ Auto-Audit: 94.2%   │
│ (col-span-12 lg:col-span-5)             │ (col-span-6 lg:col-span-4)│ (col-span-6 lg:3)   │
├─────────────────────────────────────────┼───────────────────────────┴─────────────────────┤
│ [BENTO TILE 4: ADJUDICATION DONUT]      │ [BENTO TILE 5: FINANCIAL WATERFALL]             │
│ Live Portfolio Status Distribution      │ Capital Recovery Reconciliation                 │
│ SVG Donut + Interactive Filter Slices   │ Billed -> Insurer Cut -> Recoverable -> Net     │
│ (col-span-12 lg:col-span-5)             │ (col-span-12 lg:col-span-7)                     │
├─────────────────────────────────────────┴─────────────────────────────────────────────────┤
│ [BENTO TILE 6: STATUTORY ENGINE & CONFLICT LEVERAGE]                                     │
│ Top IRDAI Rule Conflicts: Proportionate Scaling (Cl 12.3), Room Rent (Cl 4.2), Sec 45    │
│ Frequency vs Recoverable INR Sort | One-click Citation Copying                            │
│ (col-span-12)                                                                             │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ [BENTO TILE 7: ENTERPRISE CLAIMS LEDGER]                                                  │
│ Real-time search, status tabs, document presence pills, sorting, pagination              │
│ Row click triggers CONTEXTUAL SLIDE-OVER DRAWER (preserves all filters/pagination)        │
│ (col-span-12)                                                                             │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### Bento Tile Styling Specifications
- Base container: `grid grid-cols-1 md:grid-cols-6 lg:grid-cols-12 gap-5`
- Bento Card standard:
  ```css
  bg-white rounded-2xl border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all duration-200
  ```
- Asymmetric sizing:
  - Hero Tile 1: `col-span-12 lg:col-span-5 flex flex-col justify-between p-6 bg-gradient-to-br from-white via-slate-50/50 to-emerald-50/20`
  - Risk Tile 2: `col-span-12 sm:col-span-6 lg:col-span-4 p-5 flex flex-col justify-between`
  - Operational Tile 3: `col-span-12 sm:col-span-6 lg:col-span-3 p-5 flex flex-col justify-between`
  - Visualizations Tile 4 & 5: Aligned height (`min-h-[380px]`) with synchronized card padding.

---

## 4. Survey 2: Claim Inspection & Navigation Architecture

### Current Navigation Behavior
In `src/components/dashboard/ClaimsTable.jsx`:
- Line 420:
  ```javascript
  const handleRowClick = (claimId) => {
    navigate(`/analysis/${claimId}`);
  };
  ```
- Line 725:
  ```javascript
  <tr
    key={claim.id}
    onClick={() => handleRowClick(claim.id)}
    ...
  ```
- Line 830:
  ```javascript
  <button
    type="button"
    onClick={(e) => {
      e.stopPropagation();
      handleRowClick(claim.id);
    }}
    ...
  >
    <span>View Audit</span>
    <ArrowUpRight className="w-3.5 h-3.5" />
  </button>
  ```

### Why Full Page Navigation Hurts User Experience
1. **Destructive Route Change**: When navigating to `/analysis/:id`, the `Dashboard` component unmounts.
2. **Loss of Filter & Pagination Context**: If an auditor is reviewing page 3 of "Flagged Claims" with search query `"Apollo"`, clicking an item unmounts the page. When clicking the "Return to Dashboard" back button, all React component state resets to:
   - Page 1
   - All claims (filter tab cleared)
   - Empty search input
   - Default sorting
3. **Loss of Scroll Position**: The user must scroll down to find their place again.
4. **Latency Overhead**: Unmounting the dashboard and mounting `Analysis.jsx` initiates 4 network calls (`getAnalysisStatus`, `getAnalysisResult`, `getAuditTrail`, `getAppealDraft`) and renders the full 4-tab workspace even if the user only wanted to verify a disallowance clause or patient UHID.

### Contextual Slide-Over Drawer Architecture
To solve this, implement a dedicated `ClaimInspectionDrawer.jsx` component that opens on top of the dashboard without unmounting it.

#### State Synchronization Model
Use URL query parameter `?inspect=CLM-XXXXX` combined with React state:
- When a user clicks a row: `setInspectedClaimId(claim.id)` (and sync to URL `?inspect=${claim.id}`).
- When the drawer closes: `setInspectedClaimId(null)` (remove `?inspect` param).
- Browser back button automatically closes the drawer without resetting dashboard scroll or table state.
- Links to `/analysis/:id` remain available inside the drawer as an "Open Full Dossier Workspace" CTA.

#### Component Architecture (`ClaimInspectionDrawer.jsx`)
```jsx
// Conceptual Structure
<AnimatePresence>
  {inspectedClaimId && (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs"
      />

      {/* Slide-over Panel */}
      <motion.aside
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
        className="fixed inset-y-0 right-0 z-50 w-full sm:w-[540px] lg:w-[620px] bg-white border-l border-slate-200 shadow-elevation flex flex-col overflow-hidden"
      >
        {/* 1. Drawer Header */}
        <div className="p-5 border-b border-slate-200/90 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-50 border border-brand-100 text-brand-600">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sm text-slate-900">{claim.id}</span>
                <StatusBadge status={claim.status} size="xs" />
              </div>
              <span className="text-xs text-slate-500">{claim.patient_name} • {claim.hospital}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/analysis/${claim.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              <span>Full Dossier</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 2. Scrollable Body: High-Density Audit Summary */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Financial Reconciliation Strip */}
          <div className="grid grid-cols-3 gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Billed</div>
              <div className="text-sm font-bold font-financial text-slate-900">{formatInr(claim.total_amount)}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Disallowed</div>
              <div className="text-sm font-bold font-financial text-rose-600">{formatInr(claim.monetary_impact)}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-emerald-600 uppercase">Recoverable</div>
              <div className="text-sm font-bold font-financial text-emerald-700">+{formatInr(claim.monetary_impact)}</div>
            </div>
          </div>

          {/* Tripartite Document Verification Matrix */}
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5">Document Ingestion Status</h4>
            <div className="space-y-2">
              <DocumentRow name="Hospital Bill" status={claim.documents_status?.bill} meta="24 line items extracted" />
              <DocumentRow name="Insurance Policy" status={claim.documents_status?.policy} meta="Sum Insured ₹10L | 1% Room Cap" />
              <DocumentRow name="Rejection Voucher" status={claim.documents_status?.rejection} meta="Disallowed Cl 12.3 Pro-rata" />
            </div>
          </div>

          {/* Detected Conflicts Highlights */}
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5">Key Statutory Conflicts</h4>
            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/50 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold text-rose-800">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>IRDAI Master Circular May 2024, Cl 12.3</span>
              </div>
              <p className="text-xs text-rose-700 leading-relaxed">
                Unlawful proportionate deduction scaling applied to ICU and Surgeon fees.
              </p>
            </div>
          </div>

          {/* Quick Legal Citation Copy */}
          <div className="pt-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(`IRDAI Master Circular May 2024, Cl 12.3: Proportionate deductions are strictly barred from non-room fixed charges.`);
                toast.success('Statutory clause citation copied!');
              }}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Statutory Citation for Dispute Filing</span>
            </button>
          </div>
        </div>

        {/* 3. Drawer Footer Quick Actions */}
        <div className="p-4 border-t border-slate-200 bg-white flex items-center justify-between gap-3">
          <button
            onClick={() => {
              toast.success(`Claim ${claim.id} marked verified`);
              onClose();
            }}
            className="flex-1 py-2 px-3 border border-slate-200 text-slate-700 font-semibold text-xs rounded-lg hover:bg-slate-50"
          >
            Mark Verified
          </button>
          <Link
            to={`/analysis/${claim.id}?tab=appeal`}
            className="flex-1 py-2 px-3 bg-brand-600 text-white font-semibold text-xs rounded-lg hover:bg-brand-700 text-center shadow-xs"
          >
            Generate Appeal
          </Link>
        </div>
      </motion.aside>
    </>
  )}
</AnimatePresence>
```

---

## 5. Survey 3: Typography Hierarchy & Design Tokens

### Current Configuration Audit
1. **HTML Font Preload (`index.html`)**:
   - Loads `Inter` (weights 300, 400, 500, 600, 700, 800).
   - Loads `JetBrains Mono` (weights 400, 500, 600, 700).
2. **Tailwind Config (`tailwind.config.js`)**:
   - `fontFamily.sans`: `['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif']`
   - `fontFamily.mono`: `['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']`
3. **Base CSS (`src/index.css`)**:
   - Applies font feature settings: `font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';` (enables alternate character forms like curved 'l' and open '4' in Inter).
   - Defines `.font-financial`: `@apply font-mono tracking-tight tabular-nums;`

### Color Palette Consistency Check
A regex search for un-themed `gray-*` classes (`text-gray-`, `bg-gray-`, `border-gray-`) across all JSX components returned **0 occurrences**. The frontend adheres to Tailwind's `slate-*` spectrum.

### Typography Hierarchy Guidelines for Refinement
To ensure crisp enterprise hierarchy across all views:

| Role | Font Family | Size / Leading | Weight | Tailwind Classes |
|:---|:---|:---|:---|:---|
| **Page Title** | Inter | 24px / 32px | Extrabold (800) | `text-2xl font-extrabold tracking-tight text-slate-900` |
| **Section Title** | Inter | 18px / 28px | Bold (700) | `text-lg font-bold tracking-tight text-slate-900` |
| **Card Header / Tile Title** | Inter | 14px / 20px | Bold (700) | `text-sm font-bold text-slate-900` |
| **Hero Financial Metric** | JetBrains Mono | 28px–32px | Bold (700) | `text-2xl lg:text-3xl font-bold font-financial tracking-tight text-slate-900` |
| **Table Header** | Inter | 11px / 16px | Semibold (600) | `text-[11px] font-semibold text-slate-500 uppercase tracking-wider` |
| **Body Primary** | Inter | 12px–13px | Medium/Semibold | `text-xs font-medium text-slate-800` |
| **Body Secondary** | Inter | 12px / 16px | Regular/Medium | `text-xs text-slate-500 leading-relaxed` |
| **Metadata / Micro-labels** | Inter | 10px–11px | Semibold (600) | `text-[10px] font-semibold text-slate-400 uppercase tracking-wide` |
| **Financial Delta** | JetBrains Mono | 12px / 16px | Bold (700) | `text-xs font-bold font-financial tabular-nums` |

---

## 6. Survey 4: Borders, Shadows, and Elevation Design Tokens

### Current Shadow Tokens in `tailwind.config.js`
Lines 66–72:
```javascript
boxShadow: {
  'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  'card': '0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.06)',
  'card-hover': '0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)',
  'elevation': '0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)',
  'inner-subtle': 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.04)',
},
```

### Gap Analysis against R2 Requirements
The prompt states:
> *"Refine borders and shadows to use ultra-soft diffused styles (`0 4px 20px rgba(0,0,0,0.03)`) and 1px borders."*

1. **Current `card` shadow is too tight and dark**: `0 1px 3px 0 rgba(15, 23, 42, 0.06)` has a 3px blur radius at 6% opacity, producing a distinct edge rather than a soft diffused glow.
2. **Outdated Heavy Shadows in Components**:
   - `App.jsx` (line 26): `shadow-lg shadow-sky-950/50` (heavy, saturated shadow).
   - `App.jsx` (line 93): `shadow-xl` on sidebar.
   - `BatchDropzone.jsx` (lines 264–266): `shadow-lg`.
   - `ReadinessCheck.jsx` (line 392–394): `shadow-md`, `hover:shadow-lg`.
   - `FinancialDelta.jsx` (line 164): `shadow-md`.
   - Legacy `src/components/VerdictCard.jsx` (line 32): `shadow-sm rounded-lg` with loose borders.

### Proposed Shadow Token Specification
Extend `tailwind.config.js`:
```javascript
boxShadow: {
  'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.04)',
  'card': '0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04)',
  'diffused': '0 4px 20px 0 rgba(0, 0, 0, 0.03)',
  'diffused-md': '0 6px 24px 0 rgba(15, 23, 42, 0.04)',
  'diffused-lg': '0 10px 30px -2px rgba(15, 23, 42, 0.05)',
  'bento': '0 4px 20px 0 rgba(0, 0, 0, 0.03), 0 1px 2px 0 rgba(0, 0, 0, 0.02)',
  'card-hover': '0 10px 25px -4px rgba(15, 23, 42, 0.06), 0 4px 10px -2px rgba(15, 23, 42, 0.03)',
  'elevation': '0 20px 30px -6px rgba(15, 23, 42, 0.08), 0 8px 12px -4px rgba(15, 23, 42, 0.03)',
  'inner-subtle': 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
}
```

Update `.card-enterprise` in `src/index.css`:
```css
.card-enterprise {
  @apply bg-white rounded-2xl border border-slate-200/90 transition-all duration-200;
  box-shadow: theme('boxShadow.diffused');
}
.card-enterprise-hover {
  @apply hover:border-slate-300;
}
.card-enterprise-hover:hover {
  box-shadow: theme('boxShadow.card-hover');
}
```

---

## 7. Survey 5: Toast Notifications & Sonner Integration

### Current Status of Toast Notifications
- `package.json` currently declares `"react-hot-toast": "^2.4.1"`.
- `App.jsx` imports `Toaster` from `react-hot-toast` and mounts it at line 150:
  ```jsx
  <Toaster
    position="top-right"
    toastOptions={{
      style: {
        background: '#0F172A',
        color: '#F8FAFC',
        fontSize: '13px',
        borderRadius: '10px',
        border: '1px solid #1E293B',
      },
    }}
  />
  ```
- Exactly **21 invocation call sites** exist across 10 files (audited in Section 2).

### Deficiencies of `react-hot-toast`
1. **No Stacked Card Physics**: In `react-hot-toast`, multiple toasts expand as separate full-height blocks that push each other vertically, cluttering the top-right viewport.
2. **Missing Action Support**: Toasts lack first-class action buttons (e.g. `action: { label: 'View', onClick: ... }`).
3. **Static Styling**: Hardcoded inline dark styles in `App.jsx` clash with the crisp white/slate enterprise theme of the dashboard.

### Sonner Architecture & Integration Blueprint
`sonner` provides the gold standard for stacked enterprise toasts:
1. **Stacked Physics**: Up to 3–5 notifications stack behind each other with scale and translation transforms. Hovering or clicking expands the stack seamlessly.
2. **Rich Event Support**: Supports custom headers, descriptions, spinners, and interactive buttons.
3. **Drop-in API Compatibility**: Both libraries support `toast.success(message)`, `toast.error(message)`, `toast.loading(message)`, and `toast.dismiss(id)`.

#### Integration in `App.jsx`:
```jsx
import { Toaster, toast } from 'sonner';

// Inside App component:
<Toaster
  position="top-right"
  richColors={false}
  closeButton
  expand={false}
  visibleToasts={4}
  toastOptions={{
    className: 'font-sans text-xs bg-white text-slate-900 border border-slate-200/90 shadow-card rounded-xl p-3.5',
    descriptionClassName: 'text-[11px] text-slate-500 mt-0.5',
    actionButtonStyle: {
      backgroundColor: '#0284C7',
      color: '#FFFFFF',
      fontSize: '11px',
      fontWeight: '600',
      borderRadius: '6px',
      padding: '4px 10px',
    },
  }}
/>
```

#### Pipeline Status Events Integration
During claim upload and analysis pipeline execution:

| Event / Pipeline Trigger | Sonner Invocation Pattern | UI Result |
|:---|:---|:---|
| **Batch File Upload** | `toast.success('Attached hospital_bill.pdf', { description: 'Verified: 24 line items extracted' })` | Clean stack card with secondary text |
| **Invalid File Type / Size** | `toast.error('Intake rejected: malware.exe', { description: 'Allowed formats: PDF, JPG, PNG, TIFF (≤ 25MB)' })` | Rose accent border with error description |
| **Pipeline Stage 1 -> 4** | `toast.loading('Computing SHA-256 block hash...', { id: 'pipeline-progress' })` followed by `toast.info('Extracting tabular OCR tokens...', { id: 'pipeline-progress' })` | Single in-place updating toast |
| **Analysis Complete** | `toast.success('Claim CLM-84920 audited successfully', { id: 'pipeline-progress', description: '₹42,500 wrongful disallowance detected', action: { label: 'Inspect Claim', onClick: () => openDrawer('CLM-84920') } })` | Stacked card with interactive CTA button |
| **Copy Citation** | `toast.success('IRDAI Master Circular Cl 12.3 copied', { description: 'Ready to paste into grievance appeal draft' })` | Micro-interaction toast |
| **CSV Export** | `toast.success(`Exported ${count} claims to CSV`, { description: 'Saved to Downloads folder' })` | Informational confirmation |

#### Dependency & Test Guardrails
- **`package.json`**: Must add `"sonner": "^1.7.0"` (or peer `"framer-motion": "^11.11.0"`).
- **`tests/check-imports.mjs`**: Reads `package.json.dependencies`. Adding `sonner` to `package.json` ensures zero unresolved import errors.
- **`tests/run-stress-tests.mjs`**: Rollup SSR bundle externalizes dependencies. Line 24 must add `'sonner'` alongside `'react-hot-toast'`.

---

## 8. Summary of Actionable Recommendations for Implementation Team

1. **Dashboard Bento Grid**:
   - Refactor `Dashboard.jsx` layout container into a 12-column CSS grid.
   - Restructure `ExecutiveKpiCards.jsx` to render an asymmetric 5-column hero card for "Total Recovered Capital" with live sparkline, and compact cards for remaining KPIs.
   - Integrate the statutory alert directly into the Bento Grid flow.
2. **Contextual Slide-Over Drawer**:
   - Create `src/components/dashboard/ClaimInspectionDrawer.jsx`.
   - In `ClaimsTable.jsx`, change `handleRowClick(claim.id)` to trigger `onSelectClaim(claim.id)` instead of navigating away.
   - Sync `inspectedClaimId` with URL query parameter `?inspect=CLM-XXXXX`.
   - Keep full route `/analysis/:id` as an escalated workspace accessible via "Open Full Dossier" buttons.
3. **Design Tokens & Shadows**:
   - Add `'diffused': '0 4px 20px 0 rgba(0, 0, 0, 0.03)'` and `'bento'` to `tailwind.config.js`.
   - Update `.card-enterprise` in `src/index.css` to use diffused shadows and 16px radius (`rounded-2xl`).
   - Replace legacy harsh shadows (`shadow-lg shadow-sky-950/50`, `shadow-xl`) across `App.jsx`, `BatchDropzone.jsx`, and `FinancialDelta.jsx`.
4. **Sonner Integration**:
   - Add `sonner` to `package.json`.
   - Replace `<Toaster>` in `App.jsx` with Sonner's stacked `<Toaster>`.
   - Enhance upload pipeline in `Upload.jsx` to update a persistent toast (`id: 'audit-pipeline'`) through the 4 extraction stages.
   - Update `tests/run-stress-tests.mjs` to include `'sonner'` in external dependencies.
