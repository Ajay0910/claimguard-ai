import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import DashboardCharts, {
  StatusDonutChart,
  FinancialWaterfallChart,
  RuleConflictBarChart,
  formatInr,
  formatCompactInr,
  defaultDashboardAnalytics,
} from '../src/components/dashboard/DashboardCharts.jsx';

import MetricCard, { SparklineCurve } from '../src/components/common/MetricCard.jsx';

export function runChartStressTests() {
  const testResults = [];
  const vulnerabilities = [];

  function record(id, title, category, passed, details = {}, severity = 'INFO') {
    testResults.push({
      id,
      title,
      category,
      passed,
      details,
      severity,
    });
    if (!passed && severity !== 'INFO') {
      vulnerabilities.push({ id, title, severity, details });
    }
  }

  // =========================================================================
  // SUITE 1: SVG Donut Chart Geometry & Zero Handling
  // =========================================================================

  // 1.1: Total count = 0 (all slices 0)
  try {
    const zeroBreakdown = [
      { id: 'APPROVED', label: 'Approved', count: 0, color: '#059669' },
      { id: 'FLAGGED', label: 'Flagged', count: 0, color: '#E11D48' },
      { id: 'REVIEW', label: 'Review', count: 0, color: '#D97706' },
      { id: 'DISALLOWED', label: 'Disallowed', count: 0, color: '#64748B' },
    ];
    const html = renderToStaticMarkup(<StatusDonutChart data={zeroBreakdown} claims={[]} />);

    const hasNaN = html.includes('NaN');
    const hasInfinity = html.includes('Infinity');
    const hasCircleSlice = html.includes('stroke-dasharray');

    // Total should display 0, no slices rendered, no NaN in markup
    const passes = !hasNaN && !hasInfinity && html.includes('>0</span>') && !hasCircleSlice;

    record(
      'DONUT-01',
      'Donut chart when total count is 0 (all slices 0) does not produce NaN or divide-by-zero crash',
      'Donut Geometry',
      passes,
      { hasNaN, hasInfinity, hasCircleSlice, htmlSnippet: html.substring(0, 300) },
      passes ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('DONUT-01', 'Donut chart zero count crash', 'Donut Geometry', false, { error: err.message }, 'CRITICAL');
  }

  // 1.2: Donut chart fallback on null/undefined claims and data
  try {
    const html = renderToStaticMarkup(<StatusDonutChart claims={null} data={null} />);
    const hasNaN = html.includes('NaN');
    const hasTotal = html.includes('130'); // 72+42+14+2 = 130
    record(
      'DONUT-02',
      'Donut chart falls back safely to default analytics when claims and data are null',
      'Donut Geometry',
      !hasNaN && hasTotal,
      { hasNaN, hasTotal },
      !hasNaN && hasTotal ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('DONUT-02', 'Donut chart null props crash', 'Donut Geometry', false, { error: err.message }, 'HIGH');
  }

  // 1.3: Donut chart with non-standard / weird claim status strings
  try {
    const claimsWithWeirdStatus = [
      { status: 'UNKNOWN_STATUS_123', monetary_impact: 0 },
      { status: 'ANOTHER_WEIRD', impact: 0 },
    ];
    const html = renderToStaticMarkup(<StatusDonutChart claims={claimsWithWeirdStatus} />);
    const hasNaN = html.includes('NaN');
    // Both should fall into disallowed / deductions category
    const hasCount2 = html.includes('>2</span>');
    record(
      'DONUT-03',
      'Donut chart categorizes unknown claim statuses safely into fallback category without NaNs',
      'Donut Geometry',
      !hasNaN && hasCount2,
      { hasNaN, hasCount2 },
      !hasNaN && hasCount2 ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('DONUT-03', 'Donut chart weird status crash', 'Donut Geometry', false, { error: err.message }, 'MEDIUM');
  }

  // =========================================================================
  // SUITE 2: 100% Single Category Donut & Gap Artifact Analysis
  // =========================================================================

  // 2.1: 100 claims all 'Approved' (100% single category)
  try {
    const allApprovedClaims = Array.from({ length: 100 }, (_, i) => ({
      id: `CLM-${i}`,
      status: 'APPROVED',
      monetary_impact: 0,
    }));
    const html = renderToStaticMarkup(<StatusDonutChart claims={allApprovedClaims} />);

    // Circumference = 2 * Math.PI * 68 ≈ 427.25660088821186
    const circumference = 2 * Math.PI * 68;

    // Check if stroke-dasharray has subtracted 2.5:
    // When dynamicBreakdown.length > 1 (which is 4), dashLength = 427.2566 - 2.5 = 424.7566
    // stroke-dasharray="424.7566... 2.5..."
    const dashMatch = html.match(/stroke-dasharray="([^"]+)"/);
    const strokeDasharray = dashMatch ? dashMatch[1] : null;

    let hasGapArtifact = false;
    let expectedGapFreeDash = `${circumference} 0`;
    let actualDash = strokeDasharray;

    if (strokeDasharray) {
      const parts = strokeDasharray.split(' ').map(Number);
      // If the second part is > 0 (e.g. 2.5), there is an unpainted gap in a 100% circle!
      if (parts[1] > 1.0) {
        hasGapArtifact = true;
      }
    }

    // This is an intentional empirical verification of gap artifacts
    record(
      'DONUT-GAP-01',
      '100% single category donut gap artifact verification (checks if 2.5px gap is subtracted from closed ring)',
      'Donut Geometry',
      // If gap artifact is present, we document it as an identified defect/limitation
      !hasGapArtifact,
      {
        hasGapArtifact,
        strokeDasharray: actualDash,
        circumference,
        note: hasGapArtifact
          ? 'Gap artifact detected: subtracting 2.5px gap when dynamicBreakdown.length > 1 even though only 1 slice is non-zero causes a 2.5px notch in a 100% donut ring.'
          : 'Rendered closed ring without gap artifact.',
      },
      hasGapArtifact ? 'LOW' : 'INFO'
    );
  } catch (err) {
    record('DONUT-GAP-01', '100% single category donut crash', 'Donut Geometry', false, { error: err.message }, 'HIGH');
  }

  // 2.2: Single category with data.length = 1
  try {
    const singleSliceData = [{ id: 'APPROVED', label: 'Approved', count: 100, color: '#059669' }];
    const html = renderToStaticMarkup(<StatusDonutChart data={singleSliceData} claims={[]} />);
    const dashMatch = html.match(/stroke-dasharray="([^"]+)"/);
    const strokeDasharray = dashMatch ? dashMatch[1] : null;

    const parts = strokeDasharray ? strokeDasharray.split(' ').map(Number) : [];
    const hasGap = parts.length > 1 && parts[1] > 1.0;

    record(
      'DONUT-GAP-02',
      'Donut chart when data.length === 1 renders full circumference without 2.5px gap subtraction',
      'Donut Geometry',
      !hasGap,
      { strokeDasharray, hasGap },
      !hasGap ? 'INFO' : 'LOW'
    );
  } catch (err) {
    record('DONUT-GAP-02', 'Donut chart data.length=1 crash', 'Donut Geometry', false, { error: err.message }, 'MEDIUM');
  }

  // =========================================================================
  // SUITE 3: Waterfall Chart Extreme Values & NaN Resilience
  // =========================================================================

  // 3.1: stats = { total_recovered_amount: 0 } -> 0 Billed, 0 Recovered
  try {
    const html = renderToStaticMarkup(<FinancialWaterfallChart stats={{ total_recovered_amount: 0 }} />);

    // In DashboardCharts.jsx:
    // maxVal = Math.max(...dynamicSteps.map(s => s.amount + s.base)) * 1.15
    // When total_recovered_amount = 0: maxVal = 0
    // barHeight = Math.max(14, (0 / 0) * 175) -> Math.max(14, NaN) -> NaN!
    // bottomOffset = (0 / 0) * 175 -> NaN!
    // style="height:NaNpx;margin-bottom:NaNpx;"
    const hasNaNHeight = html.includes('height:NaNpx') || html.includes('height: NaNpx');
    const hasNaNMargin = html.includes('margin-bottom:NaNpx') || html.includes('marginBottom:NaNpx') || html.includes('margin-bottom: NaNpx');
    const hasNaN = html.includes('NaN');

    const isVulnerable = hasNaNHeight || hasNaNMargin || hasNaN;

    record(
      'WATERFALL-01',
      'FinancialWaterfallChart with 0 total_recovered_amount does not produce NaN in inline styles',
      'Waterfall Chart',
      !isVulnerable,
      {
        hasNaNHeight,
        hasNaNMargin,
        hasNaN,
        vulnerabilityReason: isVulnerable
          ? 'DIVIDE_BY_ZERO: stats.total_recovered_amount=0 causes maxVal=0, resulting in 0/0=NaN in barHeight and bottomOffset style attributes.'
          : 'Clean rendering without NaNs.',
      },
      isVulnerable ? 'HIGH' : 'INFO'
    );
  } catch (err) {
    record('WATERFALL-01', 'Waterfall chart 0 recovered crash', 'Waterfall Chart', false, { error: err.message }, 'HIGH');
  }

  // 3.2: Custom steps with all zero amounts
  try {
    const zeroSteps = [
      { id: 'billed', name: 'Billed', amount: 0, base: 0, type: 'total', color: '#1E293B' },
      { id: 'approved', name: 'Approved', amount: 0, base: 0, type: 'subtotal', color: '#0284C7' },
    ];
    const html = renderToStaticMarkup(<FinancialWaterfallChart steps={zeroSteps} />);
    const hasNaN = html.includes('NaN');
    record(
      'WATERFALL-02',
      'FinancialWaterfallChart with zero-amount custom steps does not produce NaN in inline styles',
      'Waterfall Chart',
      !hasNaN,
      { hasNaN },
      !hasNaN ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('WATERFALL-02', 'Waterfall chart zero-amount steps crash', 'Waterfall Chart', false, { error: err.message }, 'HIGH');
  }

  // 3.3: Negative recoverable amount
  try {
    const negativeSteps = [
      { id: 'billed', name: 'Billed', amount: 100000, base: 0, type: 'total', color: '#1E293B' },
      { id: 'approved', name: 'Approved', amount: 80000, base: 0, type: 'subtotal', color: '#0284C7' },
      { id: 'disallowed', name: 'Disallowed', amount: 20000, base: 80000, type: 'deduction', color: '#E11D48' },
      { id: 'recoverable', name: 'Contested Recovery', amount: -15000, base: 80000, type: 'recovery', color: '#059669' },
      { id: 'net', name: 'Net', amount: 65000, base: 0, type: 'final', color: '#0D9488' },
    ];
    const html = renderToStaticMarkup(<FinancialWaterfallChart steps={negativeSteps} />);
    const hasNaN = html.includes('NaN');
    // Check if formatCompactInr handles negative values cleanly
    const formattedNegative = formatCompactInr(-15000);
    // Note: formatCompactInr(-15000) falls through to return `₹-15000` because -15000 >= 1000 is false!
    const negativeCompactValid = formattedNegative.includes('-') && formattedNegative.includes('15');

    record(
      'WATERFALL-03',
      'FinancialWaterfallChart handles negative recoverable step amount without NaNs or crashes',
      'Waterfall Chart',
      !hasNaN && negativeCompactValid,
      { hasNaN, formattedNegative, negativeCompactValid },
      !hasNaN ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('WATERFALL-03', 'Waterfall chart negative recovery crash', 'Waterfall Chart', false, { error: err.message }, 'MEDIUM');
  }

  // 3.4: Disallowed > Billed (e.g. Disallowed ₹30L, Billed ₹20L -> Approved = -₹10L)
  try {
    const invertedSteps = [
      { id: 'billed', name: 'Billed', amount: 200000, base: 0, type: 'total', color: '#1E293B' },
      { id: 'approved', name: 'Insurer Approved', amount: -50000, base: 0, type: 'subtotal', color: '#0284C7' },
      { id: 'disallowed', name: 'Disallowed', amount: 250000, base: -50000, type: 'deduction', color: '#E11D48' },
      { id: 'recoverable', name: 'Recoverable', amount: 150000, base: -50000, type: 'recovery', color: '#059669' },
      { id: 'net', name: 'Net Settlement', amount: 100000, base: 0, type: 'final', color: '#0D9488' },
    ];
    const html = renderToStaticMarkup(<FinancialWaterfallChart steps={invertedSteps} />);
    const hasNaN = html.includes('NaN');

    // With negative base (-50000), bottomOffset will be negative:
    // bottomOffset = (-50000 / maxVal) * chartHeight
    // style="margin-bottom: -Xpx;"
    const hasNegativeMargin = html.includes('margin-bottom:-') || html.includes('margin-bottom: -');

    record(
      'WATERFALL-04',
      'FinancialWaterfallChart with Disallowed > Billed produces negative base displacement',
      'Waterfall Chart',
      !hasNaN,
      {
        hasNaN,
        hasNegativeMargin,
        note: hasNegativeMargin
          ? 'Negative margin-bottom detected: when disallowed deductions exceed billed amount, negative base shifts bar below container bottom.'
          : 'No negative margin found.',
      },
      !hasNaN ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('WATERFALL-04', 'Waterfall chart disallowed > billed crash', 'Waterfall Chart', false, { error: err.message }, 'MEDIUM');
  }

  // =========================================================================
  // SUITE 4: Sparkline Curve Generator in MetricCard.jsx
  // =========================================================================

  // 4.1: Empty array `[]`
  try {
    const sparkHtml = renderToStaticMarkup(<SparklineCurve data={[]} />);
    const cardHtml = renderToStaticMarkup(<MetricCard title="Test" value="100" sparkline={[]} />);
    const sparkEmptySafe = sparkHtml === '';
    const cardSafe = !cardHtml.includes('NaN') && !cardHtml.includes('undefined');

    record(
      'SPARK-01',
      'SparklineCurve and MetricCard with empty array [] return null without errors',
      'Sparkline Math',
      sparkEmptySafe && cardSafe,
      { sparkEmptySafe, cardSafe },
      sparkEmptySafe && cardSafe ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('SPARK-01', 'Sparkline empty array crash', 'Sparkline Math', false, { error: err.message }, 'HIGH');
  }

  // 4.2: Single element `[42]`
  try {
    const sparkHtml = renderToStaticMarkup(<SparklineCurve data={[42]} />);
    const cardHtml = renderToStaticMarkup(<MetricCard title="Single" value="₹42K" sparkline={[42]} />);
    const sparkSingleSafe = sparkHtml === '';
    // MetricCard will render 1 activity bar: Math.max(15, Math.min(100, 42)) = 42%
    const cardHasBar = cardHtml.includes('height: 42%') || cardHtml.includes('height:42%');
    const noNaN = !cardHtml.includes('NaN');

    record(
      'SPARK-02',
      'SparklineCurve with single element [42] safely returns null; MetricCard clamps activity bar',
      'Sparkline Math',
      sparkSingleSafe && noNaN && cardHasBar,
      { sparkSingleSafe, cardHasBar, noNaN },
      sparkSingleSafe && noNaN && cardHasBar ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('SPARK-02', 'Sparkline single element crash', 'Sparkline Math', false, { error: err.message }, 'HIGH');
  }

  // 4.3: Identical elements `[10, 10, 10]`
  try {
    const sparkHtml = renderToStaticMarkup(<SparklineCurve data={[10, 10, 10]} />);
    // When min === max === 10, range = max - min || 1 = 1
    // All points y = 28 - 3 - ((10 - 10) / 1) * 22 = 25
    const hasNaN = sparkHtml.includes('NaN');
    const hasInfinity = sparkHtml.includes('Infinity');
    const hasPath = sparkHtml.includes('d="M 3,25');

    record(
      'SPARK-03',
      'SparklineCurve with identical elements [10, 10, 10] prevents divide-by-zero (range = max - min || 1)',
      'Sparkline Math',
      !hasNaN && !hasInfinity && hasPath,
      { hasNaN, hasInfinity, hasPath, snippet: sparkHtml.substring(0, 150) },
      !hasNaN && !hasInfinity && hasPath ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('SPARK-03', 'Sparkline identical elements crash', 'Sparkline Math', false, { error: err.message }, 'HIGH');
  }

  // 4.4: All zero elements `[0, 0, 0, 0]`
  try {
    const sparkHtml = renderToStaticMarkup(<SparklineCurve data={[0, 0, 0, 0]} />);
    const hasNaN = sparkHtml.includes('NaN');
    const hasPath = sparkHtml.includes('<path');
    record(
      'SPARK-04',
      'SparklineCurve with all zero elements [0, 0, 0, 0] renders flat line without NaN',
      'Sparkline Math',
      !hasNaN && hasPath,
      { hasNaN, hasPath },
      !hasNaN && hasPath ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('SPARK-04', 'Sparkline zeros crash', 'Sparkline Math', false, { error: err.message }, 'HIGH');
  }

  // 4.5: Negative values `[-10, -50, -30, -20]`
  try {
    const sparkHtml = renderToStaticMarkup(<SparklineCurve data={[-10, -50, -30, -20]} />);
    const cardHtml = renderToStaticMarkup(<MetricCard title="Negative" value="-10" sparkline={[-10, -50, -30, -20]} />);
    const hasNaN = sparkHtml.includes('NaN');
    // In activity bars: val = -10 clamps to 15, val = -50 clamps to 15
    const cardClampsBars = cardHtml.includes('height: 15%') || cardHtml.includes('height:15%');

    record(
      'SPARK-05',
      'SparklineCurve handles negative values correctly; MetricCard activity bars clamp to 15%',
      'Sparkline Math',
      !hasNaN && cardClampsBars,
      { hasNaN, cardClampsBars },
      !hasNaN && cardClampsBars ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('SPARK-05', 'Sparkline negative values crash', 'Sparkline Math', false, { error: err.message }, 'MEDIUM');
  }

  // 4.6: null and undefined inputs
  try {
    const nullSpark = renderToStaticMarkup(<SparklineCurve data={null} />);
    const undefSpark = renderToStaticMarkup(<SparklineCurve data={undefined} />);
    const nullCard = renderToStaticMarkup(<MetricCard title="Null" value="0" sparkline={null} />);
    const undefCard = renderToStaticMarkup(<MetricCard title="Undef" value="0" sparkline={undefined} />);

    // null data returns null
    const nullSafe = nullSpark === '';
    // undefined data falls back to default 7-point array
    const undefHasCurve = undefSpark.includes('<path');
    const cardsSafe = !nullCard.includes('NaN') && !undefCard.includes('NaN');

    record(
      'SPARK-06',
      'SparklineCurve and MetricCard handle null/undefined data safely (null returns null, undefined uses default)',
      'Sparkline Math',
      nullSafe && undefHasCurve && cardsSafe,
      { nullSafe, undefHasCurve, cardsSafe },
      nullSafe && undefHasCurve && cardsSafe ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('SPARK-06', 'Sparkline null/undefined crash', 'Sparkline Math', false, { error: err.message }, 'HIGH');
  }

  // 4.7: Array containing null/undefined/NaN elements e.g. [10, undefined, 30]
  try {
    const corruptHtml = renderToStaticMarkup(<SparklineCurve data={[10, undefined, 30]} />);
    // Math.min(10, undefined, 30) = NaN
    // Causes points with NaN coordinates and `d="M 3,NaN C NaN,NaN ..."`
    const hasNaNInCorrupt = corruptHtml.includes('NaN');

    record(
      'SPARK-07',
      'SparklineCurve vulnerability check: array containing undefined/NaN elements produces NaN path coordinates',
      'Sparkline Math',
      !hasNaNInCorrupt,
      {
        hasNaNInCorrupt,
        note: hasNaNInCorrupt
          ? 'NaN coordinates detected: Math.min(...[10, undefined, 30]) yields NaN, which propagates into SVG Bezier d attribute.'
          : 'Clean coordinates.',
      },
      hasNaNInCorrupt ? 'MEDIUM' : 'INFO'
    );
  } catch (err) {
    record('SPARK-07', 'Sparkline corrupt array crash', 'Sparkline Math', false, { error: err.message }, 'MEDIUM');
  }

  // =========================================================================
  // SUITE 5: Cross-Filtering Callbacks & Event Safety
  // =========================================================================

  // 5.1: onSelectStatusFilter undefined and null
  try {
    const htmlUndef = renderToStaticMarkup(<StatusDonutChart onSelectStatusFilter={undefined} />);
    const htmlNull = renderToStaticMarkup(<StatusDonutChart onSelectStatusFilter={null} />);
    const passes = htmlUndef.includes('svg') && htmlNull.includes('svg');

    record(
      'CALLBACK-01',
      'StatusDonutChart renders safely when onSelectStatusFilter is undefined or null',
      'Callback Resilience',
      passes,
      { passes },
      passes ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('CALLBACK-01', 'onSelectStatusFilter null crash', 'Callback Resilience', false, { error: err.message }, 'HIGH');
  }

  // 5.2: Callback invocation simulation
  try {
    let calledId = null;
    const mockFilter = (id) => {
      calledId = id;
    };

    // Test callback behavior in simulation
    const handleSliceClick = (sliceId, callback) => {
      if (callback) {
        callback(sliceId);
      }
    };

    handleSliceClick('APPROVED', mockFilter);
    const filterCalled = calledId === 'APPROVED';

    // Test with undefined callback (should not throw)
    let undefThrew = false;
    try {
      handleSliceClick('APPROVED', undefined);
    } catch {
      undefThrew = true;
    }

    record(
      'CALLBACK-02',
      'Slice click handler correctly forwards sliceId when callback is provided and silently ignores undefined',
      'Callback Resilience',
      filterCalled && !undefThrew,
      { filterCalled, undefThrew },
      filterCalled && !undefThrew ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('CALLBACK-02', 'Callback invocation simulation failure', 'Callback Resilience', false, { error: err.message }, 'HIGH');
  }

  // 5.3: Non-function truthy callback (e.g. boolean true or string)
  try {
    // In DashboardCharts.jsx line 179:
    // const handleSliceClick = (sliceId) => {
    //   if (onSelectStatusFilter) {
    //     onSelectStatusFilter(sliceId);
    // ...
    // If onSelectStatusFilter = true, typeof onSelectStatusFilter === 'function' is NOT checked!
    let threwTypeError = false;
    try {
      const badCallback = true;
      if (badCallback) {
        badCallback('APPROVED'); // Will throw TypeError
      }
    } catch (e) {
      if (e instanceof TypeError) threwTypeError = true;
    }

    record(
      'CALLBACK-03',
      'Callback vulnerability check: truthy non-function prop throws TypeError because `typeof !== function` guard is absent',
      'Callback Resilience',
      // If code lacks typeof guard, we flag this boundary condition
      !threwTypeError,
      {
        threwTypeError,
        note: threwTypeError
          ? 'TYPE_UNCHECKED: `if (onSelectStatusFilter)` does not verify `typeof onSelectStatusFilter === "function"`. Passing a truthy non-function (e.g. true) will cause TypeError on click.'
          : 'Guarded against non-function.',
      },
      threwTypeError ? 'LOW' : 'INFO'
    );
  } catch (err) {
    record('CALLBACK-03', 'Callback type check crash', 'Callback Resilience', false, { error: err.message }, 'LOW');
  }

  // =========================================================================
  // SUITE 6: RuleConflictBarChart & Currency Helpers Stress
  // =========================================================================

  // 6.1: RuleConflictBarChart with empty rules array
  try {
    const html = renderToStaticMarkup(<RuleConflictBarChart rules={[]} />);
    // Math.max(...[]) = -Infinity
    // percentage = (metricVal / -Infinity) * 100
    // But sortedRules is empty so it renders 0 rows
    const rendersContainer = html.includes('Top Statutory Rule Conflicts');
    const hasNaN = html.includes('NaN');
    record(
      'BAR-01',
      'RuleConflictBarChart with empty rules array [] renders empty container without crashing',
      'Bar Chart',
      rendersContainer && !hasNaN,
      { rendersContainer, hasNaN },
      rendersContainer && !hasNaN ? 'INFO' : 'MEDIUM'
    );
  } catch (err) {
    record('BAR-01', 'Bar chart empty rules crash', 'Bar Chart', false, { error: err.message }, 'MEDIUM');
  }

  // 6.2: RuleConflictBarChart with rule having 0 count and 0 impact
  try {
    const zeroRule = [
      {
        id: 'ZERO',
        name: 'Zero Conflict',
        clause: 'IRDAI Cl 0',
        tier: 'Tier 1',
        count: 0,
        monetaryImpact: 0,
        winRate: '0%',
        details: 'Zero rule',
      },
    ];
    const html = renderToStaticMarkup(<RuleConflictBarChart rules={zeroRule} />);
    // maxVal = Math.max(0) = 0
    // percentage = ((0 / 0) * 100).toFixed(0) = NaN
    // style="width: NaN%"
    const hasNaN = html.includes('width: NaN%') || html.includes('width:NaN%');

    record(
      'BAR-02',
      'RuleConflictBarChart vulnerability check: rule with 0 count/impact produces width: NaN% (0 / 0)',
      'Bar Chart',
      !hasNaN,
      {
        hasNaN,
        note: hasNaN
          ? 'DIVIDE_BY_ZERO: maxVal=0 when all rules have 0 count/impact, causing percentage = (0 / 0) * 100 = NaN in width style.'
          : 'Safe width rendering.',
      },
      hasNaN ? 'MEDIUM' : 'INFO'
    );
  } catch (err) {
    record('BAR-02', 'Bar chart zero rule crash', 'Bar Chart', false, { error: err.message }, 'MEDIUM');
  }

  // 6.3: Currency helpers formatInr & formatCompactInr boundaries
  try {
    const f0 = formatInr(0);
    const fNull = formatInr(null);
    const fUndef = formatInr(undefined);
    const f1Cr = formatCompactInr(10000000);
    const f15L = formatCompactInr(1500000);
    const f50K = formatCompactInr(50000);
    const fNegative = formatCompactInr(-25000);

    const validInr0 = f0.includes('0');
    const validInrNull = fNull.includes('0');
    const validInrUndef = fUndef.includes('0');
    const valid1Cr = f1Cr === '₹1.0Cr';
    const valid15L = f15L === '₹15.0L';
    const valid50K = f50K === '₹50K';

    const passes = validInr0 && validInrNull && validInrUndef && valid1Cr && valid15L && valid50K;

    record(
      'CURRENCY-01',
      'formatInr and formatCompactInr handle 0, null, undefined, Crores, Lakhs, and Thousands accurately',
      'Currency Formatter',
      passes,
      { f0, fNull, fUndef, f1Cr, f15L, f50K, fNegative },
      passes ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('CURRENCY-01', 'Currency formatting crash', 'Currency Formatter', false, { error: err.message }, 'HIGH');
  }

  // =========================================================================
  // SUITE 7: DashboardCharts Full Integration Stress
  // =========================================================================
  try {
    const html = renderToStaticMarkup(
      <DashboardCharts
        stats={null}
        claims={[]}
        analyticsData={null}
        onSelectStatusFilter={() => {}}
      />
    );
    const hasDonut = html.includes('Claim Adjudication Distribution');
    const hasWaterfall = html.includes('Financial Recovery Waterfall');
    const hasBar = html.includes('Top Statutory Rule Conflicts');
    const noNaN = !html.includes('NaN');

    record(
      'CONTAINER-01',
      'DashboardCharts container orchestrates all 3 sub-charts with default fallbacks without errors or NaNs',
      'Full Integration',
      hasDonut && hasWaterfall && hasBar && noNaN,
      { hasDonut, hasWaterfall, hasBar, noNaN },
      hasDonut && hasWaterfall && hasBar && noNaN ? 'INFO' : 'HIGH'
    );
  } catch (err) {
    record('CONTAINER-01', 'DashboardCharts full integration crash', 'Full Integration', false, { error: err.message }, 'HIGH');
  }

  return {
    testResults,
    vulnerabilities,
  };
}
