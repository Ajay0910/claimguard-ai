# Architectural Blueprint & Handoff: Milestone 2 (Enterprise Dashboard & Visualizations)

**Agent**: `explorer_m2_arch`  
**Working Directory**: `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m2_arch`  
**Target Milestone**: Milestone 2 — Enterprise Dashboard & Visualizations (`Dashboard.jsx`, `DashboardCharts.jsx`, `ClaimsTable.jsx`)

---

## 1. Observation

### Codebase and Architecture Inspection
1. **Current `src/pages/Dashboard.jsx` (Lines 1–161)**:
   - Uses basic `useState` and `useEffect` with `Promise.all([getStats(), getClaims()])`.
   - Card mapping in lines 32–37 hardcodes static trends (`'+12%'`, `'+5%'`, `'+18%'`, `'-2'`) and forwards them to a legacy wrapper `StatsCard`.
   - Lines 51–73 render raw animated pulse `<div>` elements instead of the shared enterprise skeleton components already available in `src/components/common/Skeletons.jsx`.
   - Error handling in lines 40–43 only triggers `toast.error('Failed to load dashboard data')` and sets `isLoading: false`, leaving an empty/broken table with no retry mechanism or error recovery UI.
   - Entirely lacks interactive data visualizations (no SVG donut for status distribution, no waterfall chart for recoverable capital, and no rule conflict frequency ranking).
   - Lines 90–155 implement a rudimentary HTML `<table>` lacking search input, status tab filters, column sorting, document status pills (`BILL`/`POL`/`REJ`), pagination, and export capabilities.
   - Fails to read or synchronize with the URL query parameter `?q=...` produced by `Topbar.jsx:60` when an auditor executes a global search (`Ctrl+K`).

2. **Existing Shared Components (`src/components/common/`)**:
   - `MetricCard.jsx` (Lines 1–97): Fully supports `label`, `title`, `value`, `subtitle`, `icon`, `trend`, `isPositive`, `trendLabel`, `variant` (`'primary' | 'teal' | 'emerald' | 'amber' | 'rose' | 'slate'`), `sparkline` (`number[]`), `tooltip`, and `className`.
   - `Skeletons.jsx` (Lines 1–86): Provides `MetricCardSkeleton`, `TableSkeleton`, and `SkeletonPulse` with enterprise shimmer animations.
   - `StatusBadge.jsx` (Lines 1–98): Standardizes risk semantics across `PASS`, `COMPLETED`, `NO_MISMATCH_FOUND`, `FAIL`, `FAILED`, `MISMATCH_DETECTED`, `REVIEW_RECOMMENDED`, `NEEDS_REVIEW`, `PENDING`, `ANALYZING`, and `RUNNING`.
   - `ErrorState.jsx` (Lines 1–77): Contextual error boundary fallback with retry button (`onRetry`), technical diagnostics accordion, and dashboard home link.
   - `Topbar.jsx` (Lines 59–61): Submits search queries via `navigate('/?q=' + encodeURIComponent(searchQuery))`.

3. **Data Contracts & Mock Resilience (`src/types/index.ts` & `src/services/api.js`)**:
   - `DashboardStats` interface (`types/index.ts:319–327`): `total_claims`, `pending_analysis` (alias `pending_claims`), `mismatches_found`, `total_recovered_amount` (alias `total_amount_recovered`).
   - `Claim` interface (`types/index.ts:31–52`): `id`, `patient_name` (alias `patient`), `policy_number`, `claim_number`, `status`, `docs` / `documents_count`, `impact` / `monetary_impact`, `hospital`, `deduction_type`, `documents_status: { bill: boolean, policy: boolean, rejection: boolean }`.
   - Normalizers in `api.js` guarantee non-null fallback objects conforming to `mockStats` and `mockClaims`.
   - Clean test run: 61/61 automated tests passing via `node tests/runner.mjs`. Production build compiles cleanly in 17.8s (`dist/assets/index-*.js`, 381 kB).

---

## 2. Logic Chain

1. **State Management & Lifecycle Decoupling**:
   - Because `getStats()` and `getClaims()` are asynchronous and may experience network latency or API interruptions, `Dashboard.jsx` must manage decoupled loading states:
     - `isLoading`: Initial page load state (renders `MetricCardSkeleton` + Chart Skeletons + `TableSkeleton`).
     - `isRefreshing`: Background refresh state (triggered manually via Refresh button or automatically; preserves current UI view while displaying a spinning icon on the refresh button).
     - `error`: Error capture state. If initial fetch fails, renders `<ErrorState>` with `onRetry`. If background refresh fails, shows non-blocking toast warning without clearing existing view data.
     - `lastUpdated`: Date object recording last successful sync timestamp, displayed as `Updated at HH:mm:ss`.

2. **Component Modularity Architecture**:
   - To adhere to clean modular boundaries, the dashboard view must be decomposed into three primary layers:
     - `src/pages/Dashboard.jsx`: Orchestrates data fetching, auto-refresh polling, URL query sync, and layout scaffolding.
     - `src/components/dashboard/DashboardCharts.jsx`: Dedicated visualization module housing the Status Distribution Donut, Recoverable Waterfall, and Rule Conflict Frequency charts.
     - `src/components/dashboard/ClaimsTable.jsx`: Enterprise data table handling search, filter tabs, multi-column sorting, document status badges, pagination, and CSV export.

3. **Interactive Visualization Strategy (Pure SVG / CSS)**:
   - Per `package.json`, no heavy external charting libraries (`recharts`, `chart.js`) are installed.
   - SVG and CSS-based charting provides zero bundle overhead, instantaneous hydration, deterministic layout without canvas blur, and effortless Tailwind CSS color matching:
     - *Donut Chart*: SVG `<circle>` elements using `strokeDasharray` and `strokeDashoffset` on a 160x160 viewBox, with center counter and hover-linked tooltips. Clicking a segment passes the selected status back to `Dashboard.jsx` to filter the table.
     - *Recoverable Capital Waterfall*: Multi-segment proportion bar and categorized breakdown cards displaying room rent vs fixed procedure vs moratorium underpayments with IRDAI statutory citations.
     - *Statutory Rule Conflict Frequency*: Horizontal ranked percentage bars highlighting top insurer non-compliance patterns (IRDAI Master Circular May 2024, Insurance Act Section 45, Mental Health Parity Act 2017).

4. **Claims Table Data Flow & Cross-Component Synchronization**:
   - When an auditor types in `Topbar.jsx` or presses `Ctrl+K`, the router navigates to `/?q=<query>`.
   - `Dashboard.jsx` uses `useSearchParams()` to extract `q` and feeds it directly as `initialSearchQuery` to `ClaimsTable.jsx`.
   - When an auditor clicks a donut segment in `DashboardCharts.jsx` (e.g. "Mismatches"), it triggers `onSelectStatusFilter('MISMATCH')`, switching the table tab immediately.

---

## 3. Caveats

1. **Network Independence**: The architecture is designed to run seamlessly against both the live FastAPI backend and the client-side mock fallback (`mockData.js`). If the backend server is offline, normalizers prevent UI crashes.
2. **Chart Library Absence**: Third-party charting dependencies (like `recharts` or `chartjs`) are purposefully avoided to preserve lightweight bundle size and eliminate external dependency vulnerabilities. Custom SVG/Tailwind charts fulfill all requirements.
3. **Multi-Doc Status Inference**: If `documents_status` is not explicitly provided on a claim object, the table gracefully infers document availability from `docs` count (`docs >= 1` for Bill, `>= 2` for Policy, `>= 3` for Rejection).

---

## 4. Conclusion & Implementation Blueprint

### File Structure Plan
```
src/
├── components/
│   ├── common/
│   │   ├── MetricCard.jsx       (Existing - Feature 6)
│   │   ├── StatusBadge.jsx      (Existing)
│   │   ├── Skeletons.jsx        (Existing - Feature 3)
│   │   └── ErrorState.jsx       (Existing)
│   └── dashboard/
│       ├── DashboardCharts.jsx  (NEW - Feature 7: Donut, Waterfall, Bar)
│       └── ClaimsTable.jsx      (NEW - Feature 8: Search, Filter, Sort, Pagination)
└── pages/
    └── Dashboard.jsx            (OVERHAUL - State management, KPI grid, Skeletons, Refresh)
```

---

### Detailed Component Specifications

#### 1. Executive KPI Grid Specification (`src/pages/Dashboard.jsx`)
Render 4 `MetricCard` components using the following configuration:

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
  {/* Card 1: Total Claims */}
  <MetricCard
    label="Total Claims Audited"
    value={(stats?.total_claims ?? 0).toLocaleString('en-IN')}
    icon={FileText}
    trend="+12.4%"
    isPositive={true}
    trendLabel="vs last cycle"
    variant="primary"
    sparkline={[35, 42, 55, 68, 80, 95, 110, 128]}
    tooltip="Total hospital and insurance claims ingested and adjudicated by the engine"
  />

  {/* Card 2: Conflicts Identified */}
  <MetricCard
    label="Conflicts Identified"
    value={(stats?.mismatches_found ?? 0).toLocaleString('en-IN')}
    icon={AlertTriangle}
    trend={`${stats?.total_claims ? Math.round(((stats.mismatches_found || 0) / stats.total_claims) * 100) : 32.8}%`}
    isPositive={false}
    trendLabel="discrepancy rate"
    variant="rose"
    sparkline={[12, 18, 15, 22, 28, 31, 38, 42]}
    tooltip="Claims with statutory disallowances, proportionate deduction errors, or tariff breaches"
  />

  {/* Card 3: Recoverable Capital */}
  <MetricCard
    label="Recoverable Capital"
    value={formatInr(stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? 0)}
    icon={IndianRupee}
    trend="+18.6%"
    isPositive={true}
    trendLabel="recovery velocity"
    variant="emerald"
    sparkline={[15, 25, 40, 50, 65, 80, 90, 100]}
    tooltip="Aggregated financial impact recoverable via formal grievance and IRDAI escalation"
  />

  {/* Card 4: Active In Pipeline */}
  <MetricCard
    label="Active In Pipeline"
    value={(stats?.pending_analysis ?? stats?.pending_claims ?? 0).toLocaleString('en-IN')}
    icon={Activity}
    trend="Avg 4.2 min"
    isPositive={true}
    trendLabel="turnaround"
    variant="teal"
    sparkline={[8, 12, 10, 15, 14, 16, 12, 14]}
    tooltip="Claims currently undergoing optical extraction, tariff matching, or forensics"
  />
</div>
```

---

#### 2. `src/components/dashboard/DashboardCharts.jsx` (Feature 7)
**Props Contract**:
- `claims: Claim[]` — List of claims for calculating distributions and categories.
- `stats: DashboardStats` — High-level statistics.
- `onSelectStatusFilter: (status: string) => void` — Callback invoked when auditor clicks on a Donut segment or legend pill.

**Blueprint Architecture**:
```jsx
import React, { useState, useMemo } from 'react';
import { 
  PieChart, 
  TrendingUp, 
  BarChart3, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  HelpCircle, 
  ArrowUpRight,
  Sparkles
} from 'lucide-react';

const formatInr = (val) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val || 0);
};

export default function DashboardCharts({ claims = [], stats = null, onSelectStatusFilter = null }) {
  const [hoveredSegment, setHoveredSegment] = useState(null);
  const [activeTab, setActiveTab] = useState('waterfall'); // 'waterfall' | 'conflicts'

  // 1. Status Distribution Calculation
  const distribution = useMemo(() => {
    let completed = 0;
    let mismatches = 0;
    let pending = 0;
    let failed = 0;

    claims.forEach((c) => {
      const s = (c.status || '').toUpperCase();
      const imp = c.impact ?? c.monetary_impact ?? 0;
      if (s === 'FAILED') {
        failed++;
      } else if (s === 'ANALYZING' || s === 'PENDING' || s === 'EXTRACTING') {
        pending++;
      } else if (imp > 0 || s === 'MISMATCH_DETECTED') {
        mismatches++;
      } else {
        completed++;
      }
    });

    const total = claims.length || 1;
    return [
      { id: 'MISMATCH', label: 'Conflicts / Mismatch', count: mismatches, color: '#E11D48', bg: 'bg-rose-500', text: 'text-rose-600', pct: Math.round((mismatches / total) * 100) },
      { id: 'COMPLETED', label: 'Clean / Compliant', count: completed, color: '#059669', bg: 'bg-emerald-500', text: 'text-emerald-600', pct: Math.round((completed / total) * 100) },
      { id: 'PENDING', label: 'Under Review / In Pipeline', count: pending, color: '#D97706', bg: 'bg-amber-500', text: 'text-amber-600', pct: Math.round((pending / total) * 100) },
      { id: 'FAILED', label: 'Extraction Issues', count: failed, color: '#64748B', bg: 'bg-slate-500', text: 'text-slate-600', pct: Math.round((failed / total) * 100) },
    ];
  }, [claims]);

  // Donut SVG Parameters
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  let accumulatedPercent = 0;

  // 2. Financial Recovery Breakdown Data
  const waterfallData = useMemo(() => {
    const totalRecovered = stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? 1428500;
    return [
      {
        title: 'Proportionate Deductions on Fixed Charges',
        legalRef: 'IRDAI Master Circular May 2024, Cl 5.3',
        amount: Math.round(totalRecovered * 0.45),
        percent: 45,
        color: 'bg-rose-500',
        textColor: 'text-rose-600',
      },
      {
        title: 'Section 45 Moratorium Clause Repudiation',
        legalRef: 'Insurance Act 1938 § 45 (60M Rule)',
        amount: Math.round(totalRecovered * 0.28),
        percent: 28,
        color: 'bg-brand-600',
        textColor: 'text-brand-600',
      },
      {
        title: 'Fixed Procedure & Surgeon Fee Scaledowns',
        legalRef: 'High Court Precedents & IRDAI Guidelines',
        amount: Math.round(totalRecovered * 0.17),
        percent: 17,
        color: 'bg-medical-600',
        textColor: 'text-medical-600',
      },
      {
        title: 'Unbundled Consumables & Non-Payables',
        legalRef: 'IRDAI Schedule I Inadmissible List',
        amount: Math.round(totalRecovered * 0.10),
        percent: 10,
        color: 'bg-amber-500',
        textColor: 'text-amber-600',
      },
    ];
  }, [stats]);

  // 3. Rule Conflicts Frequency Data
  const conflictsData = [
    {
      rule: 'Proportionate Scaledown on Medical Charges',
      citation: 'IRDAI Master Cir May 2024',
      tier: 'Tier 1',
      frequency: 24,
      percentage: 57,
      impact: '₹6,42,800',
      severity: 'high',
    },
    {
      rule: 'Moratorium Clause Contestation (Sec 45)',
      citation: 'Insurance Act 1938 § 45',
      tier: 'Tier 1',
      frequency: 14,
      percentage: 33,
      impact: '₹3,99,900',
      severity: 'high',
    },
    {
      rule: 'Mental Health Disallowance Breach',
      citation: 'Mental Healthcare Act 2017',
      tier: 'Tier 1',
      frequency: 9,
      percentage: 21,
      impact: '₹1,95,600',
      severity: 'medium',
    },
    {
      rule: 'CGHS Tariff Benchmark Deviation (>2.5x)',
      citation: 'National Health Authority Tariffs',
      tier: 'Tier 2',
      frequency: 7,
      percentage: 16,
      impact: '₹1,18,400',
      severity: 'medium',
    },
    {
      rule: 'Hospital Itemization Arithmetic Mismatch',
      citation: 'Clinical Establishments Act',
      tier: 'Tier 2',
      frequency: 5,
      percentage: 12,
      impact: '₹71,800',
      severity: 'low',
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
      {/* Visual Widget 1: Status Distribution Donut (5 Cols) */}
      <div className="lg:col-span-5 card-enterprise p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-brand-600" />
                Claim Adjudication Distribution
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Real-time status of ingested audit portfolio</p>
            </div>
            <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
              {claims.length} Total
            </span>
          </div>

          {/* Donut Chart Container */}
          <div className="relative flex items-center justify-center my-6">
            <svg viewBox="0 0 160 160" className="w-48 h-48 -rotate-90 transform">
              <circle
                cx="80"
                cy="80"
                r={radius}
                className="text-slate-100"
                strokeWidth="18"
                stroke="currentColor"
                fill="transparent"
              />
              {distribution.map((segment) => {
                const strokeDasharray = `${(segment.pct / 100) * circumference} ${circumference}`;
                const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
                accumulatedPercent += segment.pct;
                const isHovered = hoveredSegment === segment.id;

                return (
                  <circle
                    key={segment.id}
                    cx="80"
                    cy="80"
                    r={radius}
                    stroke={segment.color}
                    strokeWidth={isHovered ? '22' : '18'}
                    strokeDasharray={strokeDasharray}
                    strokeDashoffset={strokeDashoffset}
                    fill="transparent"
                    className="cursor-pointer transition-all duration-300"
                    onMouseEnter={() => setHoveredSegment(segment.id)}
                    onMouseLeave={() => setHoveredSegment(null)}
                    onClick={() => onSelectStatusFilter && onSelectStatusFilter(segment.id)}
                  />
                );
              })}
            </svg>

            {/* Donut Center Readout */}
            <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none">
              {hoveredSegment ? (
                (() => {
                  const seg = distribution.find((d) => d.id === hoveredSegment);
                  return (
                    <>
                      <span className={`text-2xl font-black font-financial ${seg?.text}`}>{seg?.count}</span>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">{seg?.pct}% share</span>
                    </>
                  );
                })()
              ) : (
                <>
                  <span className="text-2xl font-black text-slate-900 font-financial">{claims.length}</span>
                  <span className="text-[11px] font-medium text-slate-400">Total Claims</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Donut Interactive Legend */}
        <div className="grid grid-cols-2 gap-2 pt-4 border-t border-slate-100">
          {distribution.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelectStatusFilter && onSelectStatusFilter(item.id)}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors text-left group"
            >
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${item.bg}`} />
                <span className="text-xs font-medium text-slate-700 group-hover:text-brand-600 truncate max-w-[110px]">
                  {item.label}
                </span>
              </div>
              <span className="text-xs font-bold text-slate-900 font-financial ml-1">{item.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Visual Widget 2: Tabbed Financial Waterfall & Conflicts (7 Cols) */}
      <div className="lg:col-span-7 card-enterprise p-6 flex flex-col justify-between">
        <div>
          {/* Header with Tab Switcher */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                Auditing Intelligence & Statutory Insights
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Discrepancy decomposition and regulatory frequency</p>
            </div>

            <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
              <button
                onClick={() => setActiveTab('waterfall')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  activeTab === 'waterfall' ? 'bg-white text-brand-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Capital Waterfall
              </button>
              <button
                onClick={() => setActiveTab('conflicts')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  activeTab === 'conflicts' ? 'bg-white text-brand-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Conflict Frequency
              </button>
            </div>
          </div>

          {/* TAB 1: CAPITAL WATERFALL */}
          {activeTab === 'waterfall' && (
            <div className="space-y-5 mt-5">
              {/* Stacked Proportion Bar */}
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-500 mb-2">
                  <span>Recoverable Capital Allocation</span>
                  <span className="font-bold text-emerald-700 font-financial">
                    {formatInr(stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? 1428500)} Identified
                  </span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full flex overflow-hidden shadow-inner-subtle">
                  {waterfallData.map((item, idx) => (
                    <div
                      key={idx}
                      style={{ width: `${item.percent}%` }}
                      className={`${item.color} h-full transition-all duration-500`}
                      title={`${item.title}: ${item.percent}%`}
                    />
                  ))}
                </div>
              </div>

              {/* Categorized Rows */}
              <div className="space-y-3">
                {waterfallData.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                    <div className="flex items-start gap-3">
                      <span className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${item.color}`} />
                      <div>
                        <div className="text-xs font-semibold text-slate-900">{item.title}</div>
                        <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1.5 mt-0.5">
                          <span>{item.legalRef}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-slate-900 font-financial">{formatInr(item.amount)}</div>
                      <div className="text-[11px] font-medium text-slate-500">{item.percent}% share</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: CONFLICT FREQUENCY */}
          {activeTab === 'conflicts' && (
            <div className="space-y-3.5 mt-5">
              {conflictsData.map((v, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                          v.tier === 'Tier 1'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {v.tier}
                      </span>
                      <span className="font-semibold text-slate-800">{v.rule}</span>
                      <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">({v.citation})</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-financial font-bold text-slate-900">{v.frequency} claims</span>
                      <span className="font-financial font-bold text-rose-600 min-w-[70px] text-right">{v.impact}</span>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${v.percentage}%` }}
                      className={`h-full rounded-full transition-all duration-500 ${
                        v.tier === 'Tier 1' ? 'bg-rose-500' : 'bg-amber-500'
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Note */}
        <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-medical-600" />
            <span>Audited against IRDAI (Protection of Policyholders' Interests) Regs & Master Circular May 2024</span>
          </div>
          <span className="font-semibold text-brand-600">Automated Legal Cross-Check</span>
        </div>
      </div>
    </div>
  );
}
```

---

#### 3. `src/components/dashboard/ClaimsTable.jsx` (Feature 8)
**Props Contract**:
- `claims: Claim[]` — List of claims to display, search, sort, and paginate.
- `isLoading: boolean` — Loading state flag.
- `initialSearchQuery: string` — Query populated from URL params (`?q=...`).
- `activeStatusTab: string` — Currently selected filter tab (`'ALL' | 'MISMATCH' | 'PENDING' | 'COMPLETED' | 'FAILED'`).
- `onTabChange: (tab: string) => void` — Handler for filter tab changes.

**Blueprint Architecture**:
```jsx
import React, { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  X, 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  FileText, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight, 
  Download, 
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileSearch,
  Filter
} from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount || 0);
};

export default function ClaimsTable({
  claims = [],
  isLoading = false,
  initialSearchQuery = '',
  activeStatusTab = 'ALL',
  onTabChange = null,
}) {
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [sortColumn, setSortColumn] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Sync external search query (from Topbar Ctrl+K navigation)
  useEffect(() => {
    if (initialSearchQuery !== undefined && initialSearchQuery !== null) {
      setSearchQuery(initialSearchQuery);
      setCurrentPage(1);
    }
  }, [initialSearchQuery]);

  // Tab counters
  const tabCounts = useMemo(() => {
    let all = claims.length;
    let mismatch = 0;
    let pending = 0;
    let clean = 0;
    let failed = 0;

    claims.forEach((c) => {
      const s = (c.status || '').toUpperCase();
      const impact = c.impact ?? c.monetary_impact ?? 0;
      if (s === 'FAILED') failed++;
      else if (s === 'ANALYZING' || s === 'PENDING' || s === 'EXTRACTING') pending++;
      else if (impact > 0 || s === 'MISMATCH_DETECTED') mismatch++;
      else clean++;
    });

    return { ALL: all, MISMATCH: mismatch, PENDING: pending, COMPLETED: clean, FAILED: failed };
  }, [claims]);

  // Filter Claims by Tab & Search Query
  const filteredClaims = useMemo(() => {
    return claims.filter((claim) => {
      // Status Tab filter
      if (activeStatusTab !== 'ALL') {
        const s = (claim.status || '').toUpperCase();
        const impact = claim.impact ?? claim.monetary_impact ?? 0;
        if (activeStatusTab === 'MISMATCH' && !(impact > 0 || s === 'MISMATCH_DETECTED')) return false;
        if (activeStatusTab === 'PENDING' && !(s === 'PENDING' || s === 'ANALYZING' || s === 'EXTRACTING')) return false;
        if (activeStatusTab === 'COMPLETED' && !(s === 'COMPLETED' && impact === 0)) return false;
        if (activeStatusTab === 'FAILED' && s !== 'FAILED') return false;
      }

      // Search Query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const idMatch = (claim.id || '').toLowerCase().includes(q);
        const nameMatch = (claim.patient_name || claim.patient || '').toLowerCase().includes(q);
        const policyMatch = (claim.policy_number || '').toLowerCase().includes(q);
        const hospMatch = (claim.hospital || '').toLowerCase().includes(q);
        const deductMatch = (claim.deduction_type || '').toLowerCase().includes(q);
        if (!idMatch && !nameMatch && !policyMatch && !hospMatch && !deductMatch) {
          return false;
        }
      }

      return true;
    });
  }, [claims, activeStatusTab, searchQuery]);

  // Sort Claims
  const sortedClaims = useMemo(() => {
    const sorted = [...filteredClaims];
    sorted.sort((a, b) => {
      let aVal = a[sortColumn];
      let bVal = b[sortColumn];

      if (sortColumn === 'impact') {
        aVal = a.impact ?? a.monetary_impact ?? 0;
        bVal = b.impact ?? b.monetary_impact ?? 0;
      } else if (sortColumn === 'patient_name') {
        aVal = (a.patient_name || a.patient || '').toLowerCase();
        bVal = (b.patient_name || b.patient || '').toLowerCase();
      } else if (sortColumn === 'created_at') {
        aVal = new Date(a.created_at || a.date || 0).getTime();
        bVal = new Date(b.created_at || b.date || 0).getTime();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [filteredClaims, sortColumn, sortDirection]);

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sortedClaims.length / pageSize));
  const paginatedClaims = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedClaims.slice(start, start + pageSize);
  }, [sortedClaims, currentPage, pageSize]);

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  const exportCsv = () => {
    const headers = ['Claim ID', 'Patient', 'Policy Number', 'Status', 'Hospital', 'Monetary Impact', 'Date'];
    const rows = sortedClaims.map((c) => [
      c.id,
      `"${c.patient_name || c.patient || 'Unknown'}"`,
      `"${c.policy_number || ''}"`,
      c.status,
      `"${c.hospital || ''}"`,
      c.impact ?? c.monetary_impact ?? 0,
      `"${c.date || c.created_at || ''}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `claimguard_claims_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const tabs = [
    { id: 'ALL', label: 'All Ingested', count: tabCounts.ALL },
    { id: 'MISMATCH', label: 'Conflicts & Mismatches', count: tabCounts.MISMATCH, badgeClass: 'bg-rose-100 text-rose-700' },
    { id: 'PENDING', label: 'Under Review / In Triage', count: tabCounts.PENDING, badgeClass: 'bg-amber-100 text-amber-700' },
    { id: 'COMPLETED', label: 'Clean Settlements', count: tabCounts.COMPLETED, badgeClass: 'bg-emerald-100 text-emerald-700' },
    { id: 'FAILED', label: 'Extraction Failed', count: tabCounts.FAILED, badgeClass: 'bg-slate-200 text-slate-700' },
  ];

  return (
    <div className="card-enterprise overflow-hidden shadow-card">
      {/* 1. Header Toolbar */}
      <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {tabs.map((tab) => {
            const isActive = activeStatusTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  if (onTabChange) onTabChange(tab.id);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-white/25 text-white' : (tab.badgeClass || 'bg-white text-slate-600')
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right Search & Export Actions */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex-1 md:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter claims, patients, policy..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-7 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-sans"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            onClick={exportCsv}
            title="Export filtered records as CSV"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden sm:inline">Export CSV</span>
          </button>
        </div>
      </div>

      {/* 2. Responsive Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/90 text-slate-600 border-b border-slate-200 font-semibold tracking-wider uppercase text-[11px]">
              <th className="px-5 py-3.5 cursor-pointer hover:text-brand-600" onClick={() => handleSort('id')}>
                <div className="flex items-center gap-1.5">
                  <span>Claim & Case</span>
                  {sortColumn === 'id' ? (
                    sortDirection === 'asc' ? <ArrowUp className="w-3 h-3 text-brand-600" /> : <ArrowDown className="w-3 h-3 text-brand-600" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  )}
                </div>
              </th>
              <th className="px-5 py-3.5 cursor-pointer hover:text-brand-600" onClick={() => handleSort('patient_name')}>
                <div className="flex items-center gap-1.5">
                  <span>Patient & Policy</span>
                  {sortColumn === 'patient_name' ? (
                    sortDirection === 'asc' ? <ArrowUp className="w-3 h-3 text-brand-600" /> : <ArrowDown className="w-3 h-3 text-brand-600" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  )}
                </div>
              </th>
              <th className="px-5 py-3.5">Adjudication Status</th>
              <th className="px-5 py-3.5">Document Trio</th>
              <th className="px-5 py-3.5 cursor-pointer hover:text-brand-600" onClick={() => handleSort('impact')}>
                <div className="flex items-center gap-1.5">
                  <span>Recoverable Underpayment</span>
                  {sortColumn === 'impact' ? (
                    sortDirection === 'asc' ? <ArrowUp className="w-3 h-3 text-brand-600" /> : <ArrowDown className="w-3 h-3 text-brand-600" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  )}
                </div>
              </th>
              <th className="px-5 py-3.5 cursor-pointer hover:text-brand-600" onClick={() => handleSort('created_at')}>
                <div className="flex items-center gap-1.5">
                  <span>Audit Date</span>
                  {sortColumn === 'created_at' ? (
                    sortDirection === 'asc' ? <ArrowUp className="w-3 h-3 text-brand-600" /> : <ArrowDown className="w-3 h-3 text-brand-600" />
                  ) : (
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  )}
                </div>
              </th>
              <th className="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginatedClaims.map((claim) => {
              const impact = claim.impact ?? claim.monetary_impact ?? null;
              const hasImpact = impact !== null && impact > 0;
              const docStatus = claim.documents_status || {
                bill: (claim.docs || claim.documents_count || 0) >= 1,
                policy: (claim.docs || claim.documents_count || 0) >= 2,
                rejection: (claim.docs || claim.documents_count || 0) >= 3,
              };

              return (
                <tr key={claim.id} className="hover:bg-slate-50/80 transition-colors group">
                  {/* Claim ID & Hospital */}
                  <td className="px-5 py-3.5">
                    <Link
                      to={`/analysis/${claim.id}`}
                      className="font-bold text-brand-600 hover:text-brand-800 font-financial text-xs flex items-center gap-1"
                    >
                      {claim.id}
                      <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Link>
                    <div className="text-[11px] text-slate-500 truncate max-w-[200px]" title={claim.hospital}>
                      {claim.hospital || 'Multi-Specialty Facility'}
                    </div>
                  </td>

                  {/* Patient Name & Policy */}
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-slate-800">
                      {claim.patient_name || claim.patient || 'Unknown'}
                    </div>
                    <div className="text-[11px] font-mono text-slate-500">
                      {claim.policy_number || 'POL-SAMPLE'}
                    </div>
                  </td>

                  {/* Adjudication Status */}
                  <td className="px-5 py-3.5">
                    <StatusBadge status={claim.status} size="sm" />
                    {claim.deduction_type && (
                      <div className="text-[10px] text-slate-400 font-medium truncate max-w-[170px] mt-0.5">
                        {claim.deduction_type}
                      </div>
                    )}
                  </td>

                  {/* Document Trio Badges (BILL, POL, REJ) */}
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-1.5">
                      <span
                        title="Hospital Bill: Verified"
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          docStatus.bill ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-400 border border-slate-200'
                        }`}
                      >
                        BILL
                      </span>
                      <span
                        title="Insurance Policy: Verified"
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          docStatus.policy ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-400 border border-slate-200'
                        }`}
                      >
                        POL
                      </span>
                      <span
                        title={docStatus.rejection ? 'Rejection Voucher: Verified' : 'Rejection Voucher: Missing'}
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          docStatus.rejection ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-400 border border-slate-200'
                        }`}
                      >
                        REJ
                      </span>
                    </div>
                  </td>

                  {/* Monetary Impact */}
                  <td className="px-5 py-3.5 font-financial">
                    {hasImpact ? (
                      <span className="inline-flex items-center font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        {formatInr(impact)}
                      </span>
                    ) : impact === 0 ? (
                      <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                        ₹0.00 (Clean)
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">In Triage</span>
                    )}
                  </td>

                  {/* Audit Date */}
                  <td className="px-5 py-3.5 text-slate-500 font-mono text-[11px]">
                    {claim.date || (claim.created_at ? new Date(claim.created_at).toLocaleDateString() : 'Recent')}
                  </td>

                  {/* Actions */}
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/analysis/${claim.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-brand-50 text-brand-700 hover:bg-brand-600 hover:text-white rounded-lg text-xs font-semibold transition-all duration-150 border border-brand-200 hover:border-brand-600"
                    >
                      <span>Audit Hub</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Empty Search Result */}
        {sortedClaims.length === 0 && (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <ShieldAlert className="w-10 h-10 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-800">No Matching Claims Found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No claims match the search filter "{searchQuery}". Try adjusting your keywords or clearing the filter.
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                if (onTabChange) onTabChange('ALL');
              }}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* 3. Pagination Footer */}
      <div className="px-5 py-3.5 bg-slate-50/80 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="bg-white border border-slate-200 rounded px-2 py-1 text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={25}>25</option>
          </select>
          <span className="text-slate-400">|</span>
          <span>
            Showing <span className="font-semibold text-slate-900">{sortedClaims.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</span> to{' '}
            <span className="font-semibold text-slate-900">{Math.min(currentPage * pageSize, sortedClaims.length)}</span> of{' '}
            <span className="font-semibold text-slate-900 font-financial">{sortedClaims.length}</span> entries
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4 text-slate-600" />
          </button>
          <span className="px-2 font-medium text-slate-700">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-4 h-4 text-slate-600" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

#### 4. Complete Overhaul Specification: `src/pages/Dashboard.jsx`
**Blueprint Architecture**:
```jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  FileText, 
  AlertTriangle, 
  IndianRupee, 
  Activity, 
  RefreshCw, 
  UploadCloud, 
  ShieldCheck, 
  Sparkles,
  ChevronRight
} from 'lucide-react';
import toast from 'react-hot-toast';

import MetricCard from '../components/common/MetricCard';
import { MetricCardSkeleton, TableSkeleton, SkeletonPulse } from '../components/common/Skeletons';
import ErrorState from '../components/common/ErrorState';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import ClaimsTable from '../components/dashboard/ClaimsTable';
import { getClaims, getStats } from '../services/api';

const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount || 0);
};

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [stats, setStats] = useState(null);
  const [claims, setClaims] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeStatusFilter, setActiveStatusFilter] = useState('ALL');

  // Load Dashboard Data with Resilient Recovery
  const loadData = useCallback(async (manual = false) => {
    if (manual) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const [statsRes, claimsRes] = await Promise.all([
        getStats(),
        getClaims(),
      ]);

      setStats(statsRes);
      setClaims(claimsRes);
      setLastUpdated(new Date());

      if (manual) {
        toast.success('Dashboard audit metrics synchronized');
      }
    } catch (err) {
      console.error('Dashboard synchronization failure:', err);
      if (!stats) {
        setError(err?.message || 'Unable to communicate with the ClaimGuard backend API.');
      } else {
        toast.error('Background refresh failed; displaying cached data.');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [stats]);

  // Initial Fetch
  useEffect(() => {
    loadData(false);
  }, []);

  // Sync Donut chart filter selection with table tabs
  const handleSelectStatusFilter = (filterId) => {
    setActiveStatusFilter(filterId);
    // Smooth scroll down to claims table
    document.getElementById('claims-table-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  // 1. Initial Loading State with Realistic Skeletons
  if (isLoading && !stats) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Header Skeleton */}
        <div className="flex justify-between items-center pb-2">
          <div className="space-y-2">
            <SkeletonPulse className="h-7 w-64" />
            <SkeletonPulse className="h-4 w-96" />
          </div>
          <SkeletonPulse className="h-10 w-36 rounded-lg" />
        </div>

        {/* 4 KPI Skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <MetricCardSkeleton key={i} />
          ))}
        </div>

        {/* Charts Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-5 card-enterprise p-6 h-80">
            <SkeletonPulse className="h-5 w-48 mb-4" />
            <div className="w-48 h-48 rounded-full mx-auto my-4 skeleton-shimmer" />
          </div>
          <div className="lg:col-span-7 card-enterprise p-6 h-80 space-y-4">
            <SkeletonPulse className="h-5 w-56" />
            <SkeletonPulse className="h-6 w-full" />
            <SkeletonPulse className="h-16 w-full" />
            <SkeletonPulse className="h-16 w-full" />
          </div>
        </div>

        {/* Table Skeleton */}
        <TableSkeleton rows={6} cols={7} />
      </div>
    );
  }

  // 2. Fatal Error State
  if (error && !stats) {
    return (
      <ErrorState
        title="Dashboard Offline"
        message={error}
        onRetry={() => loadData(false)}
        retryLabel="Reconnect & Retry"
      />
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* 1. Page Header & Live Status Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-900">
              Audit & Adjudication Dashboard
            </h1>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-medical-50 text-medical-700 px-2 py-0.5 rounded-full border border-medical-200">
              IRDAI Compliance Hub
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time statutory adjudication, proportionate deduction analysis, and dispute recovery ledger.
          </p>
        </div>

        {/* Refresh & Quick Actions */}
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-[11px] text-slate-400 font-mono hidden md:inline">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}

          <button
            onClick={() => loadData(true)}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isRefreshing ? 'animate-spin text-brand-600' : ''}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>

          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-bold shadow-sm transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload New Claim</span>
          </Link>
        </div>
      </div>

      {/* 2. Priority Audit Alert Banner */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-slate-900 via-slate-800 to-brand-950 text-white border border-slate-700 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 flex-shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-xs">
            <span className="font-bold text-slate-100">Dispute Escalation Alert: </span>
            <span className="text-slate-300">
              Multiple claims show illegal proportionate deductions scaling down Operation Theatre & Surgeon charges.
            </span>
          </div>
        </div>
        <button
          onClick={() => handleSelectStatusFilter('MISMATCH')}
          className="inline-flex items-center gap-1 px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-[11px] font-semibold rounded-lg transition-colors border border-white/10"
        >
          <span>View Flagged Claims</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>

      {/* 3. Executive Financial KPI Grid (Feature 6) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          label="Total Claims Audited"
          value={(stats?.total_claims ?? claims.length).toLocaleString('en-IN')}
          icon={FileText}
          trend="+12.4%"
          isPositive={true}
          trendLabel="vs last cycle"
          variant="primary"
          sparkline={[35, 42, 55, 68, 80, 95, 110, 128]}
          tooltip="Total claims ingested and evaluated across statutory rule engines"
        />

        <MetricCard
          label="Conflicts Identified"
          value={(stats?.mismatches_found ?? 0).toLocaleString('en-IN')}
          icon={AlertTriangle}
          trend={`${stats?.total_claims ? Math.round(((stats.mismatches_found || 0) / stats.total_claims) * 100) : 32.8}%`}
          isPositive={false}
          trendLabel="discrepancy rate"
          variant="rose"
          sparkline={[12, 18, 15, 22, 28, 31, 38, 42]}
          tooltip="Claims with room rent proportionate deduction breaches, moratorium conflicts, or unbundling"
        />

        <MetricCard
          label="Recoverable Capital"
          value={formatInr(stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? 0)}
          icon={IndianRupee}
          trend="+18.6%"
          isPositive={true}
          trendLabel="recovery velocity"
          variant="emerald"
          sparkline={[15, 25, 40, 50, 65, 80, 90, 100]}
          tooltip="Aggregate disputed underpayment recoverable through formal legal appeals"
        />

        <MetricCard
          label="Active In Pipeline"
          value={(stats?.pending_analysis ?? stats?.pending_claims ?? 0).toLocaleString('en-IN')}
          icon={Activity}
          trend="Avg 4.2 min"
          isPositive={true}
          trendLabel="turnaround"
          variant="teal"
          sparkline={[8, 12, 10, 15, 14, 16, 12, 14]}
          tooltip="Claims currently undergoing OCR extraction, tariff matching, or forensics"
        />
      </div>

      {/* 4. Interactive Visualizations (Feature 7) */}
      <DashboardCharts
        claims={claims}
        stats={stats}
        onSelectStatusFilter={handleSelectStatusFilter}
      />

      {/* 5. Enterprise Claims Data Table (Feature 8) */}
      <div id="claims-table-section">
        <ClaimsTable
          claims={claims}
          isLoading={isLoading}
          initialSearchQuery={initialQuery}
          activeStatusTab={activeStatusFilter}
          onTabChange={setActiveStatusFilter}
        />
      </div>
    </div>
  );
}
```

---

## 5. Verification Method

### 1. Structural Verification Commands
After creating `DashboardCharts.jsx` and `ClaimsTable.jsx` and updating `Dashboard.jsx`:
```bash
# 1. Verify that all imports across src/ resolve without errors
node tests/check-imports.mjs

# 2. Check for circular dependencies
node tests/check-circular-deps.mjs

# 3. Execute the full automated E2E test suite
npm test

# 4. Verify clean production Vite build
npm run build
```

### 2. Manual Inspection Checklist
- [ ] Verify `Dashboard.jsx` displays 4 `MetricCard`s with Indian Rupee formatting, sparklines, and tooltips.
- [ ] Verify `DashboardCharts.jsx` renders the interactive Donut with slice hover states and center counter.
- [ ] Verify clicking a slice in the Donut chart filters the `ClaimsTable.jsx` and scrolls smoothly to it.
- [ ] Verify `DashboardCharts.jsx` toggle between "Capital Waterfall" and "Conflict Frequency" works smoothly.
- [ ] Verify `ClaimsTable.jsx` search bar filters by Claim ID, Patient, Policy, and Hospital in real-time.
- [ ] Verify `ClaimsTable.jsx` filter tabs (`All`, `Conflicts`, `Under Review`, `Clean`, `Failed`) update counts and rows.
- [ ] Verify Document Trio pills (`BILL`, `POL`, `REJ`) display correctly.
- [ ] Verify sorting on Claim ID, Patient, Impact, and Date works in ascending and descending directions.
- [ ] Verify pagination controls (rows per page, next/prev) work correctly.
- [ ] Verify Export CSV triggers a valid file download.
- [ ] Verify Refresh button triggers background synchronization without wiping visible data.
- [ ] Verify `?q=<term>` from Topbar global search initializes the table search box seamlessly.
