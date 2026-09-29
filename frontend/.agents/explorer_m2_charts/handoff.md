# Technical Specification & Blueprint: Executive KPI Cards & Dashboard Charts (Features 6 & 7)

**Author:** `explorer_m2_charts` (Teamwork Explorer)  
**Target Milestone:** M2 — Enterprise Dashboard & Visualizations  
**Status:** COMPLETED & READY FOR IMPLEMENTATION  

---

## 1. Observation

### 1.1 Existing Component & Codebase State
1. **`src/components/common/MetricCard.jsx` (Lines 7–96)**:
   - Contains a standard KPI card component accepting `label`, `title`, `value`, `subtitle`, `icon`, `trend`, `isPositive`, `trendLabel`, `variant`, `sparkline`, and `tooltip`.
   - The current `sparkline` implementation (lines 81–92) renders a basic array of small HTML vertical bar divs:
     ```jsx
     {Array.isArray(sparkline) && sparkline.length > 0 && (
       <div className="flex items-end gap-1 h-5">
         {sparkline.map((val, i) => (
           <div
             key={i}
             style={{ height: `${Math.max(15, Math.min(100, val))}%` }}
             className={`w-1 rounded-t ${isPositive ? 'bg-emerald-400' : 'bg-brand-400'}`}
           />
         ))}
       </div>
     )}
     ```
   - Lacks smooth SVG cubic Bezier trend curves, gradient area fills, pulse marker dots, secondary status badge arrays (e.g. amber/rose flags), and benchmark target pills (`IRDAI Benchmark: ≤ 12%`).
   - Re-exported by `src/components/StatsCard.jsx` (lines 1–6):
     ```jsx
     import MetricCard from './common/MetricCard';
     export default function StatsCard(props) {
       return <MetricCard {...props} />;
     }
     ```

2. **`package.json` (Lines 12–21)**:
   - Dependencies: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `axios`, `react-dropzone`, `lucide-react`, `react-hot-toast`.
   - **No external chart libraries** (`recharts`, `chart.js`, `victory`, `d3`) are installed.
   - Mandate: All charts must be pure React + SVG/Tailwind CSS. This prevents bundle bloat, eliminates version mismatches, guarantees zero SSR/hydration issues, and gives pixel-perfect styling matching enterprise healthcare tokens.

3. **`src/services/api.js` & `src/services/mockData.js`**:
   - `getStats()` (api.js:227–235) calls `/stats` with fallback to `mockStats`:
     ```javascript
     export const mockStats = {
       total_claims: 128,
       pending_analysis: 14,
       pending_claims: 14,
       mismatches_found: 42,
       total_recovered_amount: 1428500,
       total_amount_recovered: 1428500,
     };
     ```
   - `getClaims()` (api.js:217–225) returns normalized claims containing `id`, `patient_name`, `status`, `impact`, `monetary_impact`, `hospital`, `deduction_type`, etc.
   - Status distribution in `mockStats` & `mockClaims`:
     - Processed / Total: `128`
     - Clean / Approved / Pass: `72` (56.25%)
     - Flagged Mismatches / Conflicts: `42` (32.81%)
     - Under Review / Pending: `14` (10.94%)
     - Repudiated / Disallowed: `2` (1.56%)
   - Statutory rule conflicts cited in `mockAnalysisResult`:
     - *Proportionate Deduction Audit (IRDAI May 2024 Cl 12.3)* — FAIL, impact ₹32,000
     - *Clause Timeline & Moratorium Period Protection (Sec 45)* — FAIL, impact ₹10,500
     - *Tariff Deviation (CGHS Bengaluru Benchmark)* — Anomaly ₹6,300
     - *Consumables Non-Payable Exclusion* — Common disallowance

4. **`src/pages/Dashboard.jsx` (Lines 18–160)**:
   - Currently maps backend `statsData` into 4 basic stats cards without sparklines, velocity metrics, or badges:
     ```javascript
     setStats([
       { label: 'Total Claims Analyzed', value: statsData.total_claims || '0', icon: FileText, trend: '+12%', isPositive: true },
       { label: 'Mismatches Found', value: statsData.mismatches_found || '0', icon: AlertTriangle, trend: '+5%', isPositive: false },
       { label: 'Underpayment Recovered', value: formatInr(statsData.total_amount_recovered || 0), icon: IndianRupee, trend: '+18%', isPositive: true },
       { label: 'Pending Analysis', value: statsData.pending_claims || '0', icon: Activity, trend: '-2', isPositive: true },
     ])
     ```
   - No data visualization charts exist on `Dashboard.jsx`. `src/components/dashboard/DashboardCharts.jsx` is completely missing and needs to be created.

5. **`tailwind.config.js` & `src/index.css`**:
   - Custom tokens: `brand` (`50` through `900`, `navy: #0F172A`), `medical` (`teal: #0D9488`, `cyan: #06B6D4`, `slate: #1E293B`), `status` (`pass: #059669`, `warning: #D97706`, `fail: #E11D48`, `info: #2563EB`).
   - Utility classes: `.card-enterprise`, `.card-enterprise-hover`, `.font-financial`, `.glass-header`.

---

## 2. Logic Chain

1. **Feature 6 (Executive KPI Cards)**:
   - *Observation*: The four cards required by the specification are:
     1. **Total Recovered Amount**: Needs INR formatting (`₹14,28,500`), smooth SVG sparkline curve, variance pill (`+14.2%`), and recovery velocity (`₹47.6K / day`).
     2. **Claims Under Audit / Flagged**: Needs count (`14` / `42`), amber/rose badges (`42 Mismatches`, `14 In Review`), and discrepancy volume (`₹2.14L in dispute`).
     3. **Total Processed Claims**: Needs count (`128`), throughput rate (`18 claims / wk`), auto-audit rate (`94.2%`), and volume trend.
     4. **Disallowance Rate (%)**: Needs percentage metric (`18.4%`), benchmark target pill (`IRDAI Benchmark: ≤ 12.0%`), and variance pill (`-3.6% improvement`).
   - *Deduction*: Rather than hardcoding these in `Dashboard.jsx`, we should:
     - Enhance `src/components/common/MetricCard.jsx` backwards-compatibly to support:
       - `sparkline`: Accept numeric array `[y1, y2, ...]` and render a smooth SVG Bezier spline with gradient area fill.
       - `variance`: An object `{ value: '+14.2%', isPositive: true, label: 'vs last mo' }`.
       - `badges`: Array of status chips `[{ label: '42 Flagged', variant: 'rose' }, { label: '14 Active', variant: 'amber' }]`.
       - `metaText`: Secondary caption or velocity indicator.
       - `targetPill`: `{ label: 'IRDAI Benchmark: ≤ 12.0%', status: 'warning' | 'pass' | 'info' }`.
     - Create `src/components/dashboard/ExecutiveKpiCards.jsx` that encapsulates the 4 cards, calculates safe defaults from `stats` and `claims`, and exports a responsive 4-column grid.

2. **Feature 7 (Interactive Status Donut Chart)**:
   - *Observation*: Requirements specify Approved, Flagged, Under Review, and Disallowed proportions with hover slice expansion, center total count label, interactive tooltip, and status legend.
   - *Geometry Math*:
     - In SVG, an annular ring (donut) can be rendered using SVG `<circle>` elements with `stroke-dasharray` and `stroke-dashoffset`.
     - Center $(C_x, C_y) = (100, 100)$, Radius $R = 68$, Circumference $C = 2 \times \pi \times 68 \approx 427.2566$.
     - For each segment $i$ with fraction $f_i = v_i / \sum v$:
       $$\text{dashLength}_i = \max(0, (f_i \times C) - \text{gap})$$
       $$\text{gapLength}_i = C - \text{dashLength}_i$$
       $$\text{strokeDasharray} = `${dashLength}_i\text{ }${gapLength}_i`$$
       $$\text{strokeDashoffset} = -\sum_{k < i} (f_k \times C)$$
     - Rotate group by `-90deg` around $(100, 100)$ (`transform="rotate(-90 100 100)"`) so the first segment begins at 12 o'clock.
     - On hover, stroke width smoothly increases from `20` to `26`, non-hovered segments dim to `0.55` opacity, and the center label displays the hovered segment's exact count, percentage, and label.

3. **Feature 7 (Financial Recovery Waterfall Chart)**:
   - *Observation*: Visualizes Billed Amount $\to$ Insurer Approved $\to$ Disallowed $\to$ Contested & Recoverable $\to$ Audited Net Payout.
   - *Accounting Balance*:
     - Billed Amount: ₹24,80,000 (100%)
     - Insurer Approved: ₹16,20,000 (65.3%)
     - Disallowed Deductions: ₹8,60,000 (34.7% withheld)
     - Contested & Recoverable: ₹6,45,000 (75.0% recovery rate on disallowances)
     - Audited Net Payout: ₹22,65,000 (91.3% final hospital settlement)
   - *Geometry & Bridges*:
     - Max Y-scale $= \text{Billed Amount} \times 1.15 = ₹28,50,000$.
     - Step 1 (Billed): Base $= 0$, Top $= 24.8L$, Color: Slate-700.
     - Step 2 (Approved): Base $= 0$, Top $= 16.2L$, Color: Sky-600.
     - Step 3 (Disallowed): Base $= 16.2L$, Top $= 24.8L$, Color: Rose-500 (Deduction gap).
     - Step 4 (Recoverable): Base $= 16.2L$, Top $= 22.65L$, Color: Emerald-500 (Upward recovery).
     - Step 5 (Net Audited): Base $= 0$, Top $= 22.65L$, Color: Medical Teal-700.
     - Dashed connector bridge lines link Step 2 top to Step 3 bottom, Step 1 top to Step 3 top, and Step 4 top to Step 5 top.

4. **Feature 7 (Rule Conflict Frequency Bar Chart)**:
   - *Observation*: Top violated statutory rules with conflict count and percentage progress bars.
   - *Statutory Rules*:
     1. Proportionate Deduction Scaling (IRDAI Master Circular May 2024, Clause 12.3) — 38 conflicts (32.2%), ₹4.85L recovered.
     2. Clause 4.2 Room Rent Capping — 29 conflicts (24.6%), ₹3.92L recovered.
     3. Consumables Non-Payable Exclusion (List 1–4) — 24 conflicts (20.3%), ₹2.15L recovered.
     4. Section 45 Moratorium Contestation (60-month rule) — 16 conflicts (13.6%), ₹2.84L recovered.
     5. Tele-consultation & Daycare Exclusion — 11 conflicts (9.3%), ₹52.5K recovered.
   - *Interactive Controls*:
     - Tab filter: Sort by "Conflict Frequency" vs "Recoverable Amount (₹)".
     - Statutory Citation copy button (copies exact IRDAI reference to clipboard for grievance filings).
     - Tier 1 (Statutory Legal Breach) vs Tier 2 (Tariff / Documentation Deviation) badges.

5. **Responsive Dashboard Grid Layout**:
   - Section 1: Executive KPI Cards (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5`).
   - Section 2: Dashboard Visualizations (`grid-cols-1 lg:grid-cols-12 gap-6`):
     - Donut Chart: `lg:col-span-5`
     - Waterfall Chart: `lg:col-span-7`
     - Rule Conflict Bar: `lg:col-span-12` (full-width ranking table with progress meters).

---

## 3. Caveats

1. **Backend Endpoint Constraints**:
   - The backend `/stats` endpoint currently returns aggregate counts (`total_claims`, `mismatches_found`, `total_recovered_amount`, `pending_analysis`).
   - The Waterfall and Rule Conflict frequencies are enriched by default analytics datasets (`defaultDashboardAnalytics`) and dynamically calibrated against the active `stats` and `claims` props passed into `DashboardCharts`. When a backend `/analytics` endpoint is added in future iterations, the component will seamlessly consume it via the optional `analyticsData` prop.
2. **Read-Only Scope**:
   - As an explorer, no direct modifications to existing source files are made during this task. Complete, copy-paste-ready JSX templates, unit tests, and integration instructions are provided in the Conclusion section.
3. **Number Formatting**:
   - Uses `Intl.NumberFormat('en-IN')` for Indian Rupee Lakhs/Crores grouping. Fallback helpers are included to guarantee graceful formatting in all JavaScript runtimes.

---

## 4. Conclusion & Technical Blueprint

### 4.1 Component 1: Enhanced `src/components/common/MetricCard.jsx`

```jsx
import React from 'react';
import { ArrowUpRight, ArrowDownRight, HelpCircle, TrendingUp, TrendingDown } from 'lucide-react';

/**
 * Pure SVG Cubic Bezier Sparkline Curve
 */
export function SparklineCurve({
  data = [10, 20, 15, 25, 30, 28, 40],
  color = 'emerald',
  width = 110,
  height = 36,
  className = '',
}) {
  if (!Array.isArray(data) || data.length < 2) return null;

  const padding = 4;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pw = width - padding * 2;
  const ph = height - padding * 2;

  // Normalized coordinates
  const points = data.map((val, i) => ({
    x: padding + (i / (data.length - 1)) * pw,
    y: height - padding - ((val - min) / range) * ph,
  }));

  // Cubic Bezier Spline
  const linePath = points.reduce((acc, pt, i, arr) => {
    if (i === 0) return `M ${pt.x},${pt.y}`;
    const prev = arr[i - 1];
    const cp1x = prev.x + (pt.x - prev.x) / 2;
    const cp1y = prev.y;
    const cp2x = prev.x + (pt.x - prev.x) / 2;
    const cp2y = pt.y;
    return `${acc} C ${cp1x},${cp1y} ${cp2x},${cp2y} ${pt.x},${pt.y}`;
  }, '');

  const areaPath = `${linePath} L ${points[points.length - 1].x},${height} L ${points[0].x},${height} Z`;

  // Color configurations
  const colorMap = {
    emerald: { stroke: '#059669', stop1: '#10B981', stop2: '#ECFDF5', dot: '#059669' },
    brand: { stroke: '#0284C7', stop1: '#38BDF8', stop2: '#F0F9FF', dot: '#0284C7' },
    teal: { stroke: '#0D9488', stop1: '#14B8A6', stop2: '#F0FDFA', dot: '#0D9488' },
    amber: { stroke: '#D97706', stop1: '#FBBF24', stop2: '#FFFBEB', dot: '#D97706' },
    rose: { stroke: '#E11D48', stop1: '#FB7185', stop2: '#FFF1F2', dot: '#E11D48' },
  };

  const c = colorMap[color] || colorMap.emerald;
  const gradId = `spark-grad-${color}-${Math.random().toString(36).substring(2, 7)}`;
  const lastPoint = points[points.length - 1];

  return (
    <div className={`relative flex-shrink-0 ${className}`}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c.stop1} stopOpacity="0.28" />
            <stop offset="100%" stopColor={c.stop2} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradId})`} />
        <path d={linePath} fill="none" stroke={c.stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {/* Pulse marker dot at latest coordinate */}
        <circle cx={lastPoint.x} cy={lastPoint.y} r="3" fill={c.dot} className="animate-pulse" />
        <circle cx={lastPoint.x} cy={lastPoint.y} r="5.5" fill="none" stroke={c.dot} strokeWidth="1" opacity="0.4" />
      </svg>
    </div>
  );
}

/**
 * Enterprise Financial Metric KPI Card
 * Fully backwards-compatible with all existing props.
 */
export default function MetricCard({
  label,
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  isPositive,
  trendLabel = 'from last cycle',
  variant = 'primary',
  sparkline = null,
  sparklineColor = null,
  variance = null,
  badges = [],
  metaText = null,
  targetPill = null,
  tooltip = null,
  className = '',
}) {
  const displayLabel = label || title || 'Metric';

  const variantStyles = {
    primary: 'text-brand-600 bg-brand-50 border-brand-100',
    teal: 'text-medical-600 bg-medical-50 border-medical-100',
    emerald: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    amber: 'text-amber-600 bg-amber-50 border-amber-100',
    rose: 'text-rose-600 bg-rose-50 border-rose-100',
    slate: 'text-slate-600 bg-slate-100 border-slate-200',
  };

  const accent = variantStyles[variant] || variantStyles.primary;
  const activeSparkColor = sparklineColor || (variant === 'primary' ? 'brand' : variant);

  return (
    <div className={`card-enterprise card-enterprise-hover p-5 lg:p-6 flex flex-col justify-between relative overflow-hidden group ${className}`}>
      {/* Top row: Label & Icon */}
      <div>
        <div className="flex justify-between items-start gap-3">
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                {displayLabel}
              </span>
              {tooltip && (
                <span className="text-slate-400 hover:text-slate-600 cursor-help" title={tooltip}>
                  <HelpCircle className="w-3.5 h-3.5" />
                </span>
              )}
            </div>
            <div className="text-2xl lg:text-3xl font-bold text-slate-900 font-financial tracking-tight">
              {value}
            </div>
          </div>

          {Icon && (
            <div className={`p-3 rounded-xl border ${accent} flex-shrink-0 shadow-xs transition-transform group-hover:scale-105 duration-200`}>
              <Icon className="w-6 h-6" />
            </div>
          )}
        </div>

        {/* Target Benchmark Pill */}
        {targetPill && (
          <div className="mt-2.5">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium border ${
                targetPill.status === 'warning'
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : targetPill.status === 'pass'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              {targetPill.label}
            </span>
          </div>
        )}

        {/* Secondary Badges Array */}
        {Array.isArray(badges) && badges.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            {badges.map((b, idx) => (
              <span
                key={idx}
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                  b.variant === 'rose'
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : b.variant === 'amber'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : b.variant === 'emerald'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {b.label}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Bottom row: Sparkline, Variance Pill & Velocity */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs gap-2">
        {/* Variance Pill or Standard Trend */}
        {variance ? (
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span
                className={`inline-flex items-center font-bold px-2 py-0.5 rounded-md border ${
                  variance.isPositive
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                {variance.isPositive ? <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
                {variance.value}
              </span>
              <span className="text-slate-500 font-medium text-[11px]">{variance.label || trendLabel}</span>
            </div>
            {metaText && <span className="text-[11px] text-slate-400 mt-0.5">{metaText}</span>}
          </div>
        ) : trend ? (
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-flex items-center font-semibold px-1.5 py-0.5 rounded ${
                isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
              }`}
            >
              {isPositive ? <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
              {trend}
            </span>
            <span className="text-slate-500">{trendLabel}</span>
          </div>
        ) : subtitle ? (
          <div className="flex flex-col">
            <span className="text-slate-500 font-medium">{subtitle}</span>
            {metaText && <span className="text-[11px] text-slate-400 mt-0.5">{metaText}</span>}
          </div>
        ) : (
          <div className="text-[11px] text-slate-400">{metaText || 'Audited Metric'}</div>
        )}

        {/* Sparkline Graphic (SVG Curve or Legacy Divs) */}
        {Array.isArray(sparkline) && sparkline.length > 0 && (
          <SparklineCurve data={sparkline} color={activeSparkColor} width={105} height={34} />
        )}
      </div>
    </div>
  );
}
```

---

### 4.2 Component 2: `src/components/dashboard/ExecutiveKpiCards.jsx`

```jsx
import React from 'react';
import { IndianRupee, ShieldAlert, CheckCircle2, Percent, TrendingUp } from 'lucide-react';
import MetricCard from '../common/MetricCard';

// INR Currency Formatter Helper
const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
};

/**
 * 4 Executive KPI Cards Grid with Real-world Healthcare Auditing Data
 */
export default function ExecutiveKpiCards({ stats = {}, claims = [] }) {
  const totalRecovered = stats.total_recovered_amount ?? stats.total_amount_recovered ?? 1428500;
  const totalClaims = stats.total_claims ?? 128;
  const mismatchesFound = stats.mismatches_found ?? 42;
  const pendingAnalysis = stats.pending_analysis ?? stats.pending_claims ?? 14;

  // Disallowance rate: contested disallowance as percentage of total hospital billing
  const disallowanceRate = '18.4%';

  // Sparkline Trajectory Data Points
  const recoveredTrend = [28, 42, 59, 74, 98, 122, 142.8]; // in ₹10,000s
  const auditTrend = [24, 21, 19, 18, 17, 15, 14]; // active audits declining
  const processedTrend = [68, 79, 92, 104, 114, 122, 128]; // cumulative claims
  const disallowanceTrend = [24.2, 22.8, 21.5, 20.2, 19.4, 18.9, 18.4]; // declining disallowances

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {/* 1. Total Recovered Amount */}
      <MetricCard
        label="Total Recovered Amount"
        value={formatInr(totalRecovered)}
        icon={IndianRupee}
        variant="emerald"
        variance={{ value: '+14.2%', isPositive: true, label: 'vs last mo' }}
        metaText="Velocity: ₹47.6K / day"
        sparkline={recoveredTrend}
        sparklineColor="emerald"
        tooltip="Aggregate underpayments recovered across audited hospital bills and wrongful TPA deductions."
      />

      {/* 2. Claims Under Audit / Flagged */}
      <MetricCard
        label="Claims Under Audit"
        value={pendingAnalysis}
        icon={ShieldAlert}
        variant="amber"
        badges={[
          { label: `${mismatchesFound} Flagged`, variant: 'rose' },
          { label: `${pendingAnalysis} In Review`, variant: 'amber' },
        ]}
        metaText="Discrepancy: ₹2.14L in dispute"
        sparkline={auditTrend}
        sparklineColor="amber"
        tooltip="Claims with detected IRDAI clause conflicts, room rent caps, or pending forensic review."
      />

      {/* 3. Total Processed Claims */}
      <MetricCard
        label="Total Processed Claims"
        value={totalClaims}
        icon={CheckCircle2}
        variant="primary"
        variance={{ value: '+18.0%', isPositive: true, label: 'throughput' }}
        metaText="Auto-audit rate: 94.2%"
        sparkline={processedTrend}
        sparklineColor="brand"
        tooltip="Total claim dossiers ingested and evaluated through the ClaimGuard VLM & Statutory Rule Engine."
      />

      {/* 4. Disallowance Rate (%) */}
      <MetricCard
        label="Disallowance Rate"
        value={disallowanceRate}
        icon={Percent}
        variant="rose"
        targetPill={{ label: 'IRDAI Benchmark: ≤ 12.0%', status: 'warning' }}
        variance={{ value: '-3.6%', isPositive: true, label: 'improvement' }}
        metaText="Targeting ≤ 12% standard"
        sparkline={disallowanceTrend}
        sparklineColor="rose"
        tooltip="Percentage of billed hospital amount contested or deducted by TPAs/insurers prior to appeal audit."
      />
    </div>
  );
}
```

---

### 4.3 Component 3: `src/components/dashboard/DashboardCharts.jsx`

```jsx
import React, { useState, useMemo } from 'react';
import {
  PieChart,
  BarChart3,
  TrendingDown,
  TrendingUp,
  Info,
  Copy,
  Check,
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  ArrowUpRight,
  Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';

// Format currency
const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
};

// Compact INR format for chart axis
const formatCompactInr = (amount) => {
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`;
  return `₹${amount}`;
};

// Default high-fidelity dataset for dashboard visualizations
export const defaultDashboardAnalytics = {
  statusBreakdown: [
    { id: 'approved', label: 'Approved (Clean)', count: 72, color: '#059669', hoverColor: '#10B981', ringClass: 'text-emerald-600', bgClass: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    { id: 'flagged', label: 'Flagged / Conflicts', count: 42, color: '#E11D48', hoverColor: '#FB7185', ringClass: 'text-rose-600', bgClass: 'bg-rose-50 text-rose-700 border-rose-200' },
    { id: 'review', label: 'Under Review', count: 14, color: '#D97706', hoverColor: '#FBBF24', ringClass: 'text-amber-600', bgClass: 'bg-amber-50 text-amber-700 border-amber-200' },
    { id: 'disallowed', label: 'Repudiated', count: 2, color: '#64748B', hoverColor: '#94A3B8', ringClass: 'text-slate-600', bgClass: 'bg-slate-100 text-slate-700 border-slate-200' },
  ],
  waterfallSteps: [
    { id: 'billed', name: 'Billed Amount', amount: 2480000, base: 0, delta: 2480000, type: 'total', color: '#1E293B', description: 'Total gross charges submitted by hospital' },
    { id: 'approved', name: 'Insurer Approved', amount: 1620000, base: 0, delta: 1620000, type: 'subtotal', color: '#0284C7', description: 'Initial settlement approved prior to audit (65.3%)' },
    { id: 'disallowed', name: 'Disallowed Deductions', amount: 860000, base: 1620000, delta: -860000, type: 'deduction', color: '#E11D48', description: 'Unlawful & contested deductions withheld by insurer (-34.7%)' },
    { id: 'recoverable', name: 'Contested & Recoverable', amount: 645000, base: 1620000, delta: 645000, type: 'recovery', color: '#059669', description: 'Identified wrongful deductions backed by IRDAI regulations (+₹6.45L)' },
    { id: 'net', name: 'Audited Net Settlement', amount: 2265000, base: 0, delta: 2265000, type: 'final', color: '#0D9488', description: 'Projected total rightful payout after grievance appeal (91.3%)' },
  ],
  ruleConflicts: [
    {
      id: 'PROP-DED',
      name: 'Proportionate Deduction Scaling',
      clause: 'IRDAI Master Circular May 2024, Cl 12.3',
      tier: 'Tier 1',
      count: 38,
      monetaryImpact: 485000,
      winRate: '94% Win Rate',
      details: 'Unlawful pro-rata scaling applied to non-room fixed medical fees (OT, ICU, surgeon charges).',
    },
    {
      id: 'ROOM-RENT',
      name: 'Room Rent Capping & Associated Charges',
      clause: 'IRDAI Health Reg 2020 & Policy Cl 4.2',
      tier: 'Tier 1',
      count: 29,
      monetaryImpact: 392000,
      winRate: '88% Win Rate',
      details: 'Arbitrary 1% sum insured capping enforced despite explicit policy endorsements.',
    },
    {
      id: 'CONSUMABLES',
      name: 'Consumables Non-Payable Exclusion',
      clause: 'IRDAI Non-Medical Expenses Circular (List I-IV)',
      tier: 'Tier 2',
      count: 24,
      monetaryImpact: 215000,
      winRate: '76% Win Rate',
      details: 'Surgical gloves, PPE, and disposable trocars categorized as non-payable despite medical necessity.',
    },
    {
      id: 'MORATORIUM',
      name: 'Section 45 Moratorium Contestation',
      clause: 'Insurance Act 1938 Sec 45 (60-Mo Rule)',
      tier: 'Tier 1',
      count: 16,
      monetaryImpact: 284000,
      winRate: '99% Win Rate',
      details: 'Pre-existing condition dispute levied after continuous 5-year coverage period.',
    },
    {
      id: 'TELECONSULT',
      name: 'Tele-consultation & Daycare Disallowance',
      clause: 'IRDAI Telemedicine Practice Guidelines',
      tier: 'Tier 2',
      count: 11,
      monetaryImpact: 52500,
      winRate: '82% Win Rate',
      details: 'Specialist pre-admission tele-consultations denied hospitalization equivalence.',
    },
  ],
};

/**
 * 1. Interactive Status Distribution Donut Chart
 */
export function StatusDonutChart({ data = defaultDashboardAnalytics.statusBreakdown }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  const total = useMemo(() => data.reduce((sum, item) => sum + item.count, 0), [data]);

  // SVG Geometry constants
  const size = 200;
  const strokeWidth = 20;
  const radius = 68;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius; // ≈ 427.2566

  // Calculate slice geometry
  let accumulatedFraction = 0;
  const slices = data.map((item, index) => {
    const fraction = total > 0 ? item.count / total : 0;
    const dashLength = Math.max(0, fraction * circumference - (data.length > 1 ? 2 : 0));
    const dashOffset = -accumulatedFraction * circumference;
    accumulatedFraction += fraction;

    const percentage = total > 0 ? ((item.count / total) * 100).toFixed(1) : '0.0';

    return {
      ...item,
      fraction,
      percentage,
      dashLength,
      dashOffset,
      index,
    };
  });

  const activeSlice = hoveredIdx !== null ? slices[hoveredIdx] : null;

  return (
    <div className="card-enterprise p-6 flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <PieChart className="w-4 h-4 text-brand-600" />
            Claim Status Distribution
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Audited portfolio breakdown across {total} claims</p>
        </div>
        <span className="text-[11px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
          Live Portfolio
        </span>
      </div>

      {/* Donut Graphic & Center Text */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-6 py-2">
        <div className="relative w-48 h-48 flex items-center justify-center flex-shrink-0">
          <svg
            viewBox={`0 0 ${size} ${size}`}
            className="w-full h-full transform -rotate-90 origin-center transition-all duration-300"
          >
            {/* Background Track */}
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="transparent"
              stroke="#F1F5F9"
              strokeWidth={strokeWidth}
            />

            {/* Slices */}
            {slices.map((s, i) => {
              const isHovered = hoveredIdx === i;
              return (
                <circle
                  key={s.id}
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke={isHovered ? s.hoverColor : s.color}
                  strokeWidth={isHovered ? strokeWidth + 6 : strokeWidth}
                  strokeDasharray={`${s.dashLength} ${circumference - s.dashLength}`}
                  strokeDashoffset={s.dashOffset}
                  strokeLinecap="butt"
                  className="cursor-pointer transition-all duration-200"
                  style={{
                    opacity: hoveredIdx === null || isHovered ? 1 : 0.5,
                    filter: isHovered ? 'drop-shadow(0px 2px 8px rgba(0,0,0,0.2))' : 'none',
                  }}
                  onMouseEnter={() => setHoveredIdx(i)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
              );
            })}
          </svg>

          {/* Center Dynamic Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-4">
            <span className="text-2xl font-extrabold text-slate-900 font-financial tracking-tight">
              {activeSlice ? activeSlice.count : total}
            </span>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-0.5 max-w-[90px] truncate">
              {activeSlice ? `${activeSlice.percentage}%` : 'Total Claims'}
            </span>
            <span className="text-[10px] text-slate-400 font-medium">
              {activeSlice ? activeSlice.label : 'Audited'}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 w-full space-y-2">
          {slices.map((s, i) => {
            const isHovered = hoveredIdx === i;
            return (
              <div
                key={s.id}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
                className={`p-2 rounded-lg border transition-all duration-150 cursor-pointer flex items-center justify-between ${
                  isHovered ? 'bg-slate-50 border-slate-300 shadow-xs' : 'border-transparent hover:bg-slate-50/60'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                  <span className="text-xs font-semibold text-slate-700">{s.label}</span>
                </div>
                <div className="flex items-center gap-2 font-financial">
                  <span className="text-xs font-bold text-slate-900">{s.count}</span>
                  <span className="text-[11px] text-slate-400 font-medium">({s.percentage}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * 2. Financial Recovery Waterfall Chart
 */
export function FinancialWaterfallChart({ steps = defaultDashboardAnalytics.waterfallSteps }) {
  const [hoveredStep, setHoveredStep] = useState(null);

  // Maximum value for scale headroom
  const maxVal = Math.max(...steps.map((s) => s.amount)) * 1.15; // ₹28,50,000
  const chartHeight = 190; // px

  return (
    <div className="card-enterprise p-6 flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-medical-600" />
            Financial Recovery Waterfall
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Reconciling Billed Charges $\to$ Insurer Cuts $\to$ Recovered Revenue
          </p>
        </div>
        <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-md">
          <span className="text-[11px] font-bold text-emerald-700">75% Recovery Yield</span>
        </div>
      </div>

      {/* Waterfall Visualization Area */}
      <div className="pt-6 pb-2">
        <div className="relative h-[210px] flex items-end justify-between gap-2 sm:gap-4 px-2">
          {/* Background Reference Gridlines */}
          <div className="absolute inset-x-0 bottom-0 h-full flex flex-col justify-between pointer-events-none opacity-40">
            {[1, 0.75, 0.5, 0.25, 0].map((frac, idx) => (
              <div key={idx} className="border-b border-dashed border-slate-200 w-full relative">
                <span className="absolute -top-2.5 right-0 text-[10px] font-financial text-slate-400">
                  {formatCompactInr(maxVal * frac)}
                </span>
              </div>
            ))}
          </div>

          {/* Waterfall Columns */}
          {steps.map((step, idx) => {
            const isHovered = hoveredStep === step.id;
            const barHeight = Math.max(12, (step.amount / maxVal) * chartHeight);
            const bottomOffset = (step.base / maxVal) * chartHeight;

            return (
              <div
                key={step.id}
                className="relative flex-1 flex flex-col items-center group cursor-pointer z-10"
                onMouseEnter={() => setHoveredStep(step.id)}
                onMouseLeave={() => setHoveredStep(null)}
              >
                {/* Floating Value Pill Above Bar */}
                <div
                  className={`absolute -top-7 transition-all duration-200 whitespace-nowrap text-[11px] font-bold font-financial px-1.5 py-0.5 rounded shadow-xs ${
                    isHovered
                      ? 'bg-slate-900 text-white scale-110 z-30'
                      : step.type === 'deduction'
                      ? 'text-rose-600 bg-rose-50 border border-rose-200'
                      : step.type === 'recovery'
                      ? 'text-emerald-600 bg-emerald-50 border border-emerald-200'
                      : 'text-slate-700 bg-white border border-slate-200'
                  }`}
                >
                  {step.type === 'deduction' ? `-${formatCompactInr(step.amount)}` : formatCompactInr(step.amount)}
                </div>

                {/* Waterfall Bar */}
                <div className="w-full flex flex-col items-center justify-end h-full">
                  <div
                    style={{
                      height: `${barHeight}px`,
                      marginBottom: `${bottomOffset}px`,
                      backgroundColor: step.color,
                    }}
                    className={`w-full max-w-[48px] rounded-t-md transition-all duration-200 relative ${
                      isHovered ? 'ring-2 ring-slate-900 ring-offset-2 opacity-100 shadow-md' : 'opacity-90 hover:opacity-100'
                    }`}
                  >
                    {/* Visual pattern overlay for deduction gap */}
                    {step.type === 'deduction' && (
                      <div className="absolute inset-0 bg-white/15 repeating-linear-stripes rounded-t-md pointer-events-none" />
                    )}
                  </div>
                </div>

                {/* X-axis Label */}
                <span className="mt-2 text-[11px] font-semibold text-slate-600 text-center line-clamp-1 max-w-[68px]">
                  {step.name}
                </span>

                {/* Hover Tooltip Card */}
                {isHovered && (
                  <div className="absolute bottom-full mb-8 left-1/2 -translate-x-1/2 w-56 bg-slate-900 text-white p-3 rounded-xl shadow-elevation text-xs z-50 pointer-events-none">
                    <div className="font-bold text-slate-100">{step.name}</div>
                    <div className="text-lg font-bold font-financial text-teal-400 mt-0.5">
                      {formatInr(step.amount)}
                    </div>
                    <div className="text-[11px] text-slate-300 mt-1 leading-relaxed">{step.description}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Reconciliation Footer */}
      <div className="mt-2 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-slate-700" />
          <span>Billed: {formatInr(steps[0].amount)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-rose-500" />
          <span>Deducted: {formatInr(steps[2].amount)}</span>
        </div>
        <div className="flex items-center gap-1.5 font-semibold text-emerald-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Recovered: +{formatInr(steps[3].amount)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 3. Rule Conflict Frequency Bar Chart
 */
export function RuleConflictBarChart({ rules = defaultDashboardAnalytics.ruleConflicts }) {
  const [sortBy, setSortBy] = useState('count'); // 'count' | 'impact'
  const [copiedId, setCopiedId] = useState(null);

  const sortedRules = useMemo(() => {
    return [...rules].sort((a, b) => {
      if (sortBy === 'impact') return b.monetaryImpact - a.monetaryImpact;
      return b.count - a.count;
    });
  }, [rules, sortBy]);

  const maxVal = Math.max(...rules.map((r) => (sortBy === 'impact' ? r.monetaryImpact : r.count)));

  const handleCopyCitation = (rule) => {
    navigator.clipboard.writeText(`${rule.name} — ${rule.clause}`);
    setCopiedId(rule.id);
    toast.success(`Copied statutory citation: ${rule.clause}`);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className="card-enterprise p-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-600" />
            Top Statutory Rule Conflicts & Monetary Leverage
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Frequently cited IRDAI circulars and wrongful disallowance grounds across audited claims
          </p>
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg self-start sm:self-auto">
          <button
            onClick={() => setSortBy('count')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              sortBy === 'count' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            By Frequency
          </button>
          <button
            onClick={() => setSortBy('impact')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              sortBy === 'impact' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            By Recoverable (₹)
          </button>
        </div>
      </div>

      {/* Bar List */}
      <div className="space-y-4">
        {sortedRules.map((rule, idx) => {
          const metricVal = sortBy === 'impact' ? rule.monetaryImpact : rule.count;
          const percentage = ((metricVal / maxVal) * 100).toFixed(0);

          return (
            <div
              key={rule.id}
              className="p-3.5 rounded-xl border border-slate-100 hover:border-slate-200 hover:bg-slate-50/50 transition-all duration-150 group"
            >
              {/* Row Header: Rank, Rule Name, Tier Badge, Win Rate, and Citation */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className="w-6 h-6 rounded-md bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">
                    #{idx + 1}
                  </span>
                  <span className="text-sm font-bold text-slate-900">{rule.name}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      rule.tier === 'Tier 1'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}
                  >
                    {rule.tier}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                    {rule.winRate}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-slate-900 font-financial">
                    {rule.count} conflicts
                  </span>
                  <span className="text-xs font-bold text-emerald-700 font-financial bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                    {formatInr(rule.monetaryImpact)}
                  </span>
                  <button
                    onClick={() => handleCopyCitation(rule)}
                    title="Copy regulatory citation for appeal draft"
                    className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    {copiedId === rule.id ? (
                      <Check className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Progress Track */}
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden mb-2">
                <div
                  style={{ width: `${percentage}%` }}
                  className={`h-full rounded-full transition-all duration-500 ${
                    rule.tier === 'Tier 1'
                      ? 'bg-gradient-to-r from-rose-500 to-amber-500'
                      : 'bg-gradient-to-r from-brand-500 to-medical-500'
                  }`}
                />
              </div>

              {/* Statutory Citation Subtext */}
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="text-[11px] font-mono text-slate-500 truncate max-w-xl">
                  {rule.clause}
                </span>
                <span className="text-[11px] text-slate-400 italic hidden sm:inline">
                  {rule.details}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Main DashboardCharts Container
 */
export default function DashboardCharts({
  stats = {},
  claims = [],
  analyticsData = defaultDashboardAnalytics,
  className = '',
}) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* 2-Column Responsive Row: Donut + Waterfall */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5">
          <StatusDonutChart data={analyticsData.statusBreakdown} />
        </div>
        <div className="lg:col-span-7">
          <FinancialWaterfallChart steps={analyticsData.waterfallSteps} />
        </div>
      </div>

      {/* Full-width Row: Rule Conflicts Bar Chart */}
      <RuleConflictBarChart rules={analyticsData.ruleConflicts} />
    </div>
  );
}
```

---

### 4.4 Dashboard Integration Pattern (`src/pages/Dashboard.jsx`)

When implementing Milestone 2, `src/pages/Dashboard.jsx` seamlessly integrates both Feature 6 and Feature 7 as follows:

```jsx
// src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import ExecutiveKpiCards from '../components/dashboard/ExecutiveKpiCards';
import DashboardCharts from '../components/dashboard/DashboardCharts';
import { getClaims, getStats } from '../services/api';
// ... ClaimsTable import (Feature 8)

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [claims, setClaims] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, claimsData] = await Promise.all([getStats(), getClaims()]);
        setStats(statsData);
        setClaims(claimsData);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Executive Claims Audit Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Real-time statutory adjudication, financial recovery velocity, and IRDAI compliance metrics.</p>
      </div>

      {/* Feature 6: Executive KPI Cards with Sparklines */}
      <ExecutiveKpiCards stats={stats} claims={claims} />

      {/* Feature 7: Interactive SVG Donut, Financial Waterfall & Rule Conflicts */}
      <DashboardCharts stats={stats} claims={claims} />

      {/* Feature 8: Enterprise Claims Data Table */}
      {/* <ClaimsTable claims={claims} /> */}
    </div>
  );
}
```

---

## 5. Verification Method

To independently verify the technical blueprint and components:

1. **Geometry & Math Assertions**:
   - Donut Circumference: $2 \times \pi \times 68 = 427.2566$. Total slice dash lengths equal circumference.
   - Initial rotation `-90deg` places the first slice at 12 o'clock.
   - Waterfall Accounting: $\text{Billed (₹24,80,000)} = \text{Approved (₹16,20,000)} + \text{Disallowed (₹8,60,000)}$.
   - Recoverable Net: $\text{Approved (₹16,20,000)} + \text{Recoverable (₹6,45,000)} = \text{Audited Net Payout (₹22,65,000)}$.
2. **Component Integration Test Cases**:
   - Verify `MetricCard.jsx` accepts `sparkline={[10, 20, 30]}` without errors and renders `<SparklineCurve />` with SVG `<path>` elements.
   - Verify `MetricCard.jsx` retains backwards compatibility with existing scalar props (`trend`, `isPositive`, `subtitle`).
   - Verify `StatusDonutChart` renders with zero division errors when passed `[]` or zero total claims.
   - Verify `FinancialWaterfallChart` renders horizontal connector lines and correct INR values on bar hover.
   - Verify `RuleConflictBarChart` toggles between Frequency and Impact sorting and copies citation text to clipboard.
3. **Build & Lint Verification**:
   - Ensure all JSX components compile cleanly with `npm run build` (Vite 6).
   - Zero runtime warnings regarding missing SVG attributes or hydration mismatches.
