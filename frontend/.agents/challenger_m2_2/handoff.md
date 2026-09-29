# Challenger Report: Milestone 2 — Visualization Resilience & SVG Math Audit

**Author**: `challenger_m2_2` (teamwork_preview_challenger)  
**Recipient**: `orchestrator_2` / parent (`bc58ea62-e6ba-49c9-a011-2939171e657b`)  
**Scope**: Adversarial stress testing of SVG math, chart geometry, and visualization resilience in `src/components/dashboard/DashboardCharts.jsx` and `src/components/common/MetricCard.jsx`.  
**Date**: 2026-09-18T00:10:30Z  
**Verdict**: **REJECT** (Blocking defects detected in cold-start divide-by-zero styles and donut circle gap geometry)

---

## 1. Observation

### 1.1 Source Code Inspections

1. **`src/components/dashboard/DashboardCharts.jsx` (Lines 314–329 & 367–368)**:
   ```javascript
   314: const totalRecovered = stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? 1428500;
   315: const billed = Math.round(totalRecovered * 2.85);
   316: const disallowed = Math.round(totalRecovered * 1.35);
   317: const approved = billed - disallowed;
   318: const netPayout = approved + totalRecovered;
   ...
   329: const maxVal = Math.max(...dynamicSteps.map((s) => s.amount + (s.base || 0))) * 1.15;
   ...
   367: const barHeight = Math.max(14, (step.amount / maxVal) * chartHeight);
   368: const bottomOffset = ((step.base || 0) / maxVal) * chartHeight;
   ```
   - When `stats` has `{ total_recovered_amount: 0 }`, `totalRecovered` evaluates to `0` because `0 ?? ...` evaluates to `0` in JavaScript.
   - Every step amount and base evaluates to `0`.
   - `maxVal = Math.max(0, 0, 0, 0, 0) * 1.15 = 0`.
   - Line 367: `(step.amount / maxVal) * chartHeight` = `(0 / 0) * 175 = NaN`.
   - In IEEE-754 floating-point arithmetic, `Math.max(14, NaN)` evaluates to `NaN`.
   - Line 368: `((step.base || 0) / maxVal) * chartHeight` = `(0 / 0) * 175 = NaN`.
   - The rendered HTML produces invalid inline styles: `style="height: NaNpx; margin-bottom: NaNpx;"`.

2. **`src/components/dashboard/DashboardCharts.jsx` (Lines 159–162 & 219–233)**:
   ```javascript
   159: const fraction = total > 0 ? item.count / total : 0;
   160: const dashLength = Math.max(0, fraction * circumference - (dynamicBreakdown.length > 1 && item.count > 0 ? 2.5 : 0));
   161: const dashOffset = -accumulatedFraction * circumference;
   162: accumulatedFraction += fraction;
   ...
   219: {slices.map((s, i) => {
   220:   if (s.count === 0) return null;
   ...
   231:   strokeDasharray={`${s.dashLength} ${circumference - s.dashLength}`}
   ```
   - `dynamicBreakdown` defaults to 4 items (`APPROVED`, `FLAGGED`, `REVIEW`, `DISALLOWED`).
   - When 100 claims are all 'Approved', `dynamicBreakdown.length` is `4`.
   - Condition `(dynamicBreakdown.length > 1 && item.count > 0 ? 2.5 : 0)` evaluates to `2.5` because `4 > 1` and `100 > 0`.
   - `circumference = 2 * Math.PI * 68 ≈ 427.2566`.
   - `dashLength = 427.2566 - 2.5 = 424.7566`.
   - `strokeDasharray = "424.7566... 2.5..."`.
   - Slices 1, 2, and 3 have `count === 0` and are skipped (`return null`).
   - Result: A 100% single-category donut circle is rendered with an unclosed `2.5px` notch (gap of `~2.11°`) at the 12 o'clock position.

3. **`src/components/dashboard/DashboardCharts.jsx` (Lines 467 & 520)**:
   ```javascript
   467: const maxVal = Math.max(...rules.map((r) => (sortBy === 'impact' ? r.monetaryImpact : r.count)));
   ...
   520: const percentage = ((metricVal / maxVal) * 100).toFixed(0);
   ...
   572: style={{ width: `${percentage}%` }}
   ```
   - When all rules have `count: 0` and `monetaryImpact: 0`, `maxVal = 0`.
   - `percentage = ((0 / 0) * 100).toFixed(0) = NaN`.
   - Resulting inline style: `style="width: NaN%"`.

4. **`src/components/dashboard/DashboardCharts.jsx` (Lines 26–31)**:
   ```javascript
   26: export const formatCompactInr = (amount) => {
   27:   if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`;
   28:   if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
   29:   if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`;
   30:   return `₹${amount || 0}`;
   31: };
   ```
   - When `amount = -50000`, `amount >= 1000` evaluates to `false`.
   - Formatter falls through to line 30, returning `"₹-50000"` rather than `"-₹50K"`.

5. **`src/components/common/MetricCard.jsx` (Lines 17–27 & 30–38)**:
   ```javascript
   17: const min = Math.min(...data);
   18: const max = Math.max(...data);
   19: const range = max - min || 1;
   ...
   24: const points = data.map((val, i) => ({
   25:   x: padding + (i / (data.length - 1)) * pw,
   26:   y: height - padding - ((val - min) / range) * ph,
   27: }));
   ```
   - When `data = [10, 10, 10]`, `min = 10`, `max = 10`, `range = 10 - 10 || 1 = 1`. No divide-by-zero occurs; flat horizontal line at `y = 25` is rendered.
   - When `data = []` or `[42]`, `data.length < 2` safely returns `null`.
   - When `data = [10, undefined, 30]`, `Math.min(...data)` evaluates to `NaN`. Coordinates evaluate to `NaN`, rendering invalid SVG path `d="M 3,NaN C NaN,NaN ..."`.

6. **`src/components/dashboard/DashboardCharts.jsx` (Lines 178–183)**:
   ```javascript
   178: const handleSliceClick = (sliceId) => {
   179:   if (onSelectStatusFilter) {
   180:     onSelectStatusFilter(sliceId);
   181:     toast.success(`Filtering claims: ${sliceId}`, { duration: 1500 });
   182:   }
   183: };
   ```
   - Safe when `onSelectStatusFilter` is `undefined` or `null`.
   - If passed a truthy non-function value (e.g. `true`), calling `onSelectStatusFilter(sliceId)` throws an unhandled `TypeError`.

### 1.2 Execution Results from Automated Harnesses

- **`node tests/run-stress-tests.mjs`**:
  ```
  Running component stress tests in SSR runtime...
  [... 33 baseline tests pass ...]
  ✔ PASS: Challenger M2: StatusDonutChart handles zero total count (all slices 0) without NaN or crash
  ✔ PASS: Challenger M2: StatusDonutChart 100% single category gap artifact analysis
  ✔ PASS: Challenger M2: FinancialWaterfallChart detects NaN when stats.total_recovered_amount is 0
  ✔ PASS: Challenger M2: FinancialWaterfallChart handles extreme negative and inverted values
  ✔ PASS: Challenger M2: SparklineCurve handles [], [42], and [10, 10, 10] safely
  ✔ PASS: Challenger M2: SparklineCurve handles negative values and null/undefined gracefully
  ✔ PASS: Challenger M2: MetricCard integrates SparklineCurve with activity bar clamping
  ✔ PASS: Challenger M2: Cross-filtering callback handles undefined and null gracefully
  ======================================================
  Component Stress Test Results: 41 Passed, 0 Failed
  ======================================================
  ```
- **`npm test` (`node tests/runner.mjs`)**:
  ```
  Tier 1: Feature Coverage & Contracts       [30/30 Passed] (100%)
  Tier 2: Boundary Cases & Adversarial       [28/28 Passed] (100%)
  Tier 3: Combinations & Cross-Module        [9/9 Passed] (100%)
  Tier 4: Real-World Scenarios               [5/5 Passed] (100%)
  ──────────────────────────────────────────────────────────────────────
  Total: 72 | Passed: 72 | Failed: 0 | Execution Time: 0.22s
  ```
- **`npm run build` (`vite build`)**:
  ```
  dist/assets/index-CBC72zTF.css   42.05 kB │ gzip:   7.44 kB
  dist/assets/index-CDncrjBs.js   436.64 kB │ gzip: 133.96 kB
  ✓ built in 5.03s
  ```

---

## 2. Logic Chain

1. **Cold-Start Divide-by-Zero in Waterfall Chart (HIGH Severity)**:
   - *Observation*: Line 329 calculates `maxVal = Math.max(...) * 1.15`. When a tenant or ledger has `total_recovered_amount: 0`, all steps evaluate to 0, resulting in `maxVal = 0`.
   - *Logic*: Lines 367 and 368 compute `(step.amount / maxVal)` and `((step.base || 0) / maxVal)`. Both evaluate to `0 / 0 = NaN`.
   - *Impact*: In inline styles, React outputs `style="height: NaNpx; margin-bottom: NaNpx;"`. CSS specifications reject `NaNpx` as invalid syntax. Browsers drop the declarations, collapsing the chart columns to 0 height or erratic geometry on cold start.
   - *Conclusion*: A fallback `const maxVal = Math.max(1, ... * 1.15)` is required to guarantee a non-zero denominator.

2. **100% Single Category Donut Gap Artifact (MEDIUM Severity)**:
   - *Observation*: Line 160 computes `dashLength = Math.max(0, fraction * circumference - (dynamicBreakdown.length > 1 && item.count > 0 ? 2.5 : 0))`.
   - *Logic*: `dynamicBreakdown` always contains 4 category objects (`APPROVED`, `FLAGGED`, `REVIEW`, `DISALLOWED`), so `dynamicBreakdown.length > 1` is always true. If a portfolio has 100% approved claims, `count > 0` is true only for the Approved category.
   - *Impact*: The code subtracts `2.5px` from the circumference, leaving an unintended `2.5px` notch at 12 o'clock in what should be a closed, continuous ring.
   - *Conclusion*: The gap subtraction must check the number of *active non-zero slices* (`const nonZeroCount = dynamicBreakdown.filter(i => i.count > 0).length; nonZeroCount > 1 ? 2.5 : 0`), rather than the schema length.

3. **Zero Impact Divide-by-Zero in Rule Conflict Bar Chart (MEDIUM Severity)**:
   - *Observation*: Line 467 computes `maxVal` from rule counts/impacts.
   - *Logic*: If all rule conflicts have `count: 0` and `monetaryImpact: 0`, `maxVal = 0`. Line 520 computes `(metricVal / maxVal) * 100`, which evaluates to `(0 / 0) * 100 = NaN`.
   - *Impact*: Progress bar renders `style="width: NaN%"`.
   - *Conclusion*: Denominator must be guarded with `const safeMax = maxVal || 1`.

4. **Negative Currency Unit Formatting Omission (LOW Severity)**:
   - *Observation*: Line 27–29 checks `amount >= 1000`. Negative amounts fail this check.
   - *Logic*: `formatCompactInr(-50000)` returns `"₹-50000"` instead of `"-₹50K"`.
   - *Impact*: Inconsistent negative currency rendering in financial reconciliation.
   - *Conclusion*: Formatter should evaluate magnitude `Math.abs(amount)` and prepend the negative sign appropriately.

5. **Sparkline Curve Resilience & Corrupted Elements (LOW Severity)**:
   - *Observation*: `SparklineCurve` correctly protects against division-by-zero for identical elements via `range = max - min || 1`. Empty arrays and single elements safely return `null`.
   - *Logic*: However, if an array contains `undefined` or `NaN`, `Math.min(...data)` returns `NaN`, propagating `NaN` into Bezier coordinates.
   - *Conclusion*: Filtering non-finite elements `data.filter(v => typeof v === 'number' && Number.isFinite(v))` provides complete immunity.

6. **Cross-Filtering Callback Type Guard (LOW Severity)**:
   - *Observation*: `if (onSelectStatusFilter)` checks truthiness instead of function type.
   - *Conclusion*: Change to `if (typeof onSelectStatusFilter === 'function')`.

---

## 3. Caveats

1. **Vite Production Bundle Status**: The project compiles successfully with 0 errors via `npm run build` (436.64 kB JS bundle). The defects identified are runtime semantic, mathematical, and layout flaws rather than bundling errors.
2. **Current Mock Data Mitigation**: In the default mock dataset (`mockStats.total_recovered_amount = 1428500`), `maxVal` is positive (`₹46.8L`), so the divide-by-zero in the waterfall chart is masked during default mock rendering. The bug only surfaces on live empty API states, zeroed stats, or cold start.

---

## 4. Conclusion

**Verdict: REJECT**

While the component library and visualizations are beautifully styled and feature-rich, the codebase contains two blocking mathematical/geometric issues:
1. A **cold-start divide-by-zero vulnerability** in `FinancialWaterfallChart` producing invalid `NaNpx` CSS styles when `total_recovered_amount` is 0.
2. A **100% single-category seam artifact** in `StatusDonutChart` leaving a 2.5px gap in full rings.

### Actionable Remediation Plan for Worker:

#### Patch 1: `src/components/dashboard/DashboardCharts.jsx`
1. **Fix Waterfall Chart divide-by-zero**:
   ```javascript
   // Line 329: Replace with:
   const maxVal = Math.max(1, ...dynamicSteps.map((s) => s.amount + (s.base || 0))) * 1.15;
   ```
2. **Fix Donut Chart 100% gap artifact**:
   ```javascript
   // Line 157: Replace with:
   const activeCategoriesCount = dynamicBreakdown.filter((item) => item.count > 0).length;
   let accumulatedFraction = 0;
   const slices = dynamicBreakdown.map((item, index) => {
     const fraction = total > 0 ? item.count / total : 0;
     const gapPadding = activeCategoriesCount > 1 && item.count > 0 ? 2.5 : 0;
     const dashLength = Math.max(0, fraction * circumference - gapPadding);
   ```
3. **Fix RuleConflictBarChart divide-by-zero**:
   ```javascript
   // Line 467 & 520: Replace with:
   const maxVal = Math.max(1, ...rules.map((r) => (sortBy === 'impact' ? r.monetaryImpact : r.count)));
   const percentage = ((metricVal / maxVal) * 100).toFixed(0);
   ```
4. **Fix compact currency formatter for negatives**:
   ```javascript
   // Line 26: Replace with:
   export const formatCompactInr = (amount) => {
     const num = Number(amount) || 0;
     const abs = Math.abs(num);
     const prefix = num < 0 ? '-₹' : '₹';
     if (abs >= 10000000) return `${prefix}${(abs / 10000000).toFixed(1)}Cr`;
     if (abs >= 100000) return `${prefix}${(abs / 100000).toFixed(1)}L`;
     if (abs >= 1000) return `${prefix}${(abs / 1000).toFixed(0)}K`;
     return `${prefix}${abs}`;
   };
   ```
5. **Fix callback type safety**:
   ```javascript
   // Line 178: Replace with:
   const handleSliceClick = (sliceId) => {
     if (typeof onSelectStatusFilter === 'function') {
       onSelectStatusFilter(sliceId);
       toast.success(`Filtering claims: ${sliceId}`, { duration: 1500 });
     }
   };
   ```

#### Patch 2: `src/components/common/MetricCard.jsx`
1. **Sanitize array inputs**:
   ```javascript
   // Line 14: Replace with:
   const cleanData = Array.isArray(data) ? data.filter((v) => typeof v === 'number' && Number.isFinite(v)) : [];
   if (cleanData.length < 2) return null;
   ```

---

## 5. Verification Method

To independently verify these findings and confirm any applied remediations:

```bash
# 1. Run the master E2E test suite (72 automated tests across Tiers 1-4)
npm test

# 2. Run the SSR component stress test harness (41 stress test scenarios)
node tests/run-stress-tests.mjs

# 3. Verify production Vite bundle
npm run build
```

### Invalidation Conditions
- Any occurrence of `NaN` or `Infinity` in rendered HTML or CSS attributes (`height: NaNpx`, `margin-bottom: NaNpx`, `width: NaN%`).
- Any non-zero gap in `strokeDasharray` when a single category contains 100% of claims.
- Negative values formatting as `₹-50000` instead of `-₹50K`.
- Failure in `npm test` or `node tests/run-stress-tests.mjs`.
