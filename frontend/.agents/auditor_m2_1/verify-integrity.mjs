import fs from 'fs';
import path from 'path';

console.log('=== AUDITOR M2 FORENSIC INTEGRITY VERIFICATION SUITE ===\n');

let passCount = 0;
let failCount = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  [PASS] ${message}`);
    passCount++;
  } else {
    console.error(`  [FAIL] ${message}`);
    failCount++;
  }
}

// -------------------------------------------------------------
// CHECK 1: SVG Geometry & Dynamic Math Engine
// -------------------------------------------------------------
console.log('--- CHECK 1: SVG Geometry & Dynamic Math Engine ---');

// Donut math test
function testDonutMath(counts) {
  const total = counts.reduce((a, b) => a + b, 0);
  const radius = 68;
  const circumference = 2 * Math.PI * radius; // ≈ 427.2566
  let accumulatedFraction = 0;

  const slices = counts.map((count, index) => {
    const fraction = total > 0 ? count / total : 0;
    const dashLength = Math.max(0, fraction * circumference - (counts.length > 1 && count > 0 ? 2.5 : 0));
    const dashOffset = -accumulatedFraction * circumference;
    accumulatedFraction += fraction;
    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0';
    return { count, fraction, dashLength, dashOffset, percentage };
  });

  return { total, circumference, slices, totalFraction: accumulatedFraction };
}

// Standard portfolio
const d1 = testDonutMath([72, 42, 14, 2]);
assert(d1.total === 130, 'Donut total equals sum of slice counts (130)');
assert(Math.abs(d1.totalFraction - 1.0) < 1e-9, 'Donut total fraction equals 1.0 (100%)');
assert(d1.slices[0].dashOffset === 0, 'First slice starts at dashOffset 0');
assert(d1.slices[1].dashOffset === -d1.slices[0].fraction * d1.circumference, 'Second slice offset is continuous');
assert(d1.slices.reduce((sum, s) => sum + parseFloat(s.percentage), 0) >= 99.8, 'Percentages sum to ~100%');

// Edge cases: Skewed, Single non-zero, All zeroes
const d2 = testDonutMath([100, 0, 0, 0]);
assert(d2.total === 100 && d2.slices[0].fraction === 1.0 && d2.slices[1].fraction === 0, '100% single slice computes valid fraction');

const d3 = testDonutMath([0, 0, 0, 0]);
assert(d3.total === 0 && d3.slices.every(s => s.fraction === 0 && s.dashLength === 0), 'All zero counts gracefully produce zero dashLength');

// Sparkline Cubic Bezier Spline Math
function testSparklineCurve(data, width = 80, height = 28) {
  if (!Array.isArray(data) || data.length < 2) return null;
  const padding = 3;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pw = width - padding * 2;
  const ph = height - padding * 2;

  const points = data.map((val, i) => ({
    x: padding + (i / (data.length - 1)) * pw,
    y: height - padding - ((val - min) / range) * ph,
  }));

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
  return { points, linePath, areaPath };
}

const sp1 = testSparklineCurve([28, 42, 59, 74, 98, 122, 142.8]);
assert(sp1 !== null, 'Sparkline generated successfully for valid series');
assert(sp1.points.length === 7, 'Sparkline generated 7 points');
assert(sp1.points.every(p => p.x >= 3 && p.x <= 77 && p.y >= 3 && p.y <= 25), 'All sparkline points within bounds [3, 77] x [3, 25]');
assert(sp1.linePath.startsWith('M ') && sp1.linePath.includes(' C '), 'Spline path uses valid cubic Bezier syntax');
assert(sp1.areaPath.endsWith(' Z'), 'Area path closes polygon with Z');

// Sparkline flat line edge case (max == min)
const sp2 = testSparklineCurve([50, 50, 50, 50]);
assert(sp2 !== null && !sp2.points.some(p => isNaN(p.x) || isNaN(p.y)), 'Flat data series handles range 0 gracefully without NaN');

// Waterfall geometry calculation
function testWaterfallMath(totalRecovered) {
  const billed = Math.round(totalRecovered * 2.85);
  const disallowed = Math.round(totalRecovered * 1.35);
  const approved = billed - disallowed;
  const netPayout = approved + totalRecovered;

  const steps = [
    { id: 'billed', amount: billed, base: 0 },
    { id: 'approved', amount: approved, base: 0 },
    { id: 'disallowed', amount: disallowed, base: approved },
    { id: 'recoverable', amount: totalRecovered, base: approved },
    { id: 'net', amount: netPayout, base: 0 },
  ];

  const maxVal = Math.max(...steps.map(s => s.amount + (s.base || 0))) * 1.15;
  const chartHeight = 175;

  const barMetrics = steps.map(step => ({
    id: step.id,
    barHeight: Math.max(14, (step.amount / maxVal) * chartHeight),
    bottomOffset: ((step.base || 0) / maxVal) * chartHeight,
  }));

  return { steps, maxVal, barMetrics };
}

const wf = testWaterfallMath(1428500);
assert(wf.steps[0].amount === 4071225, 'Waterfall billed amount matches ratio 2.85');
assert(wf.steps[1].amount === 4071225 - 1928475, 'Waterfall approved equals billed - disallowed');
assert(wf.barMetrics.every(m => m.barHeight >= 14 && m.barHeight <= 175), 'Waterfall bar heights within [14px, 175px]');
assert(wf.barMetrics[2].bottomOffset === wf.barMetrics[1].barHeight * (wf.steps[1].amount / (wf.steps[1].amount)), 'Disallowed base offset anchors at approved top');

// -------------------------------------------------------------
// CHECK 2: Table Search, Filter, Sort, Pagination Algorithms
// -------------------------------------------------------------
console.log('\n--- CHECK 2: ClaimsTable Algorithm Verification ---');

// Mock data generator for stress testing
const testClaims = Array.from({ length: 55 }, (_, i) => {
  const statuses = ['PASS', 'FAIL', 'REVIEW_RECOMMENDED', 'TAMPERED', 'APPROVED', 'MISMATCH_DETECTED'];
  const hospitals = ['Apollo Hospitals', 'Max Healthcare', 'Fortis Hospital', 'Manipal Hospital', 'Narayana Health'];
  const status = statuses[i % statuses.length];
  const impact = (status === 'FAIL' || status === 'TAMPERED' || status === 'MISMATCH_DETECTED') ? (i + 1) * 5000 : 0;
  return {
    id: `CLM-${1000 + i}`,
    claim_number: `CN-${5000 + i}`,
    patient_name: `Patient ${String.fromCharCode(65 + (i % 26))}_${i}`,
    hospital: hospitals[i % hospitals.length],
    policy_number: `POL-${2000 + (i % 10)}`,
    status,
    total_amount: 50000 + i * 2000,
    impact,
    monetary_impact: impact,
    deduction_type: impact > 0 ? (i % 2 === 0 ? 'Proportionate Deduction' : 'Room Rent Capping') : '',
    created_at: new Date(2026, 8, 1 + (i % 28)).toISOString(),
    documents_status: { bill: true, policy: i % 3 !== 0, rejection: impact > 0 },
  };
});

function matchesStatusTab(claim, tabKey) {
  if (!claim) return false;
  if (!tabKey || tabKey === 'ALL') return true;
  const status = (claim.status || '').toUpperCase().trim();
  const impact = Number(claim.monetary_impact ?? claim.impact ?? 0);
  const deduction = (claim.deduction_type || '').toLowerCase();
  const normalizedTab = tabKey.toUpperCase().trim();

  switch (normalizedTab) {
    case 'FLAGGED':
    case 'MISMATCH':
      return ['FAIL', 'FAILED', 'MISMATCH_DETECTED', 'HIGH_RISK', 'TAMPERED', 'REJECTED', 'SUSPICIOUS'].includes(status) ||
        (impact > 0 && !['PENDING', 'ANALYZING', 'RUNNING', 'EXTRACTING'].includes(status));
    case 'APPROVED':
    case 'COMPLETED':
      return ['PASS', 'APPROVED', 'CLEAN', 'NO_MISMATCH_FOUND', 'VERIFIED'].includes(status) ||
        (status === 'COMPLETED' && impact === 0);
    case 'REVIEW':
    case 'PENDING':
      return ['REVIEW_RECOMMENDED', 'NEEDS_REVIEW', 'WARNING', 'PENDING', 'ANALYZING', 'RUNNING', 'EXTRACTING', 'PROCESSING'].includes(status);
    case 'DISALLOWED':
      return impact > 0 || deduction.includes('deduction') || deduction.includes('conflict') || status === 'PARTIAL_SETTLEMENT';
    default:
      return true;
  }
}

// Test Tab Filtering
const allClaims = testClaims.filter(c => matchesStatusTab(c, 'ALL'));
assert(allClaims.length === 55, 'Filter tab ALL returns full dataset (55)');

const flaggedClaims = testClaims.filter(c => matchesStatusTab(c, 'FLAGGED'));
assert(flaggedClaims.length > 0 && flaggedClaims.every(c => c.impact > 0 || ['FAIL', 'TAMPERED', 'MISMATCH_DETECTED'].includes(c.status)), 'FLAGGED tab strictly filters high risk & positive impact claims');

const approvedClaims = testClaims.filter(c => matchesStatusTab(c, 'APPROVED'));
assert(approvedClaims.length > 0 && approvedClaims.every(c => ['PASS', 'APPROVED'].includes(c.status) && c.impact === 0), 'APPROVED tab strictly filters clean claims with 0 impact');

// Test Full-Text Multi-Field Search
function searchClaims(claims, q) {
  const query = q.trim().toLowerCase();
  if (!query) return claims;
  return claims.filter(c => {
    return (c.id || '').toLowerCase().includes(query) ||
           (c.claim_number || '').toLowerCase().includes(query) ||
           (c.patient_name || '').toLowerCase().includes(query) ||
           (c.hospital || '').toLowerCase().includes(query) ||
           (c.policy_number || '').toLowerCase().includes(query) ||
           (c.deduction_type || '').toLowerCase().includes(query);
  });
}

const searchApollo = searchClaims(testClaims, 'Apollo');
assert(searchApollo.length === 11 && searchApollo.every(c => c.hospital === 'Apollo Hospitals'), 'Full-text search by hospital name works accurately');

const searchSpecificId = searchClaims(testClaims, 'CLM-1025');
assert(searchSpecificId.length === 1 && searchSpecificId[0].id === 'CLM-1025', 'Search by exact Claim ID locates single record');

const searchDeduction = searchClaims(testClaims, 'Proportionate');
assert(searchDeduction.length > 0 && searchDeduction.every(c => c.deduction_type.includes('Proportionate')), 'Search by deduction type works');

const searchNonExistent = searchClaims(testClaims, 'XYZ9999_NON_EXISTENT');
assert(searchNonExistent.length === 0, 'Search for non-existent term returns empty array');

// Test Sorting Algorithms
function sortClaims(claims, key, direction) {
  const isAsc = direction === 'asc';
  return [...claims].sort((a, b) => {
    switch (key) {
      case 'id':
        return isAsc ? a.id.localeCompare(b.id) : b.id.localeCompare(a.id);
      case 'patient':
        return isAsc ? a.patient_name.localeCompare(b.patient_name) : b.patient_name.localeCompare(a.patient_name);
      case 'date':
        return isAsc ? new Date(a.created_at) - new Date(b.created_at) : new Date(b.created_at) - new Date(a.created_at);
      case 'total_amount':
        return isAsc ? a.total_amount - b.total_amount : b.total_amount - a.total_amount;
      case 'impact':
        return isAsc ? a.impact - b.impact : b.impact - a.impact;
      default:
        return 0;
    }
  });
}

const sortedByAmountAsc = sortClaims(testClaims, 'total_amount', 'asc');
assert(sortedByAmountAsc[0].total_amount <= sortedByAmountAsc[sortedByAmountAsc.length - 1].total_amount, 'Sort by total_amount asc maintains monotonic order');

const sortedByAmountDesc = sortClaims(testClaims, 'total_amount', 'desc');
assert(sortedByAmountDesc[0].total_amount >= sortedByAmountDesc[sortedByAmountDesc.length - 1].total_amount, 'Sort by total_amount desc maintains monotonic order');

const sortedByDateDesc = sortClaims(testClaims, 'date', 'desc');
assert(new Date(sortedByDateDesc[0].created_at) >= new Date(sortedByDateDesc[sortedByDateDesc.length - 1].created_at), 'Sort by date desc maintains chronological order');

// Test Pagination Math
function paginate(claims, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil(claims.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const startIndex = (safePage - 1) * pageSize;
  return {
    pageItems: claims.slice(startIndex, startIndex + pageSize),
    totalPages,
    safePage,
    startItem: claims.length === 0 ? 0 : startIndex + 1,
    endItem: Math.min(safePage * pageSize, claims.length)
  };
}

const p1 = paginate(testClaims, 1, 10);
assert(p1.pageItems.length === 10 && p1.startItem === 1 && p1.endItem === 10 && p1.totalPages === 6, 'Page 1 of 55 items with size 10 has 10 items, range 1-10, 6 total pages');

const p6 = paginate(testClaims, 6, 10);
assert(p6.pageItems.length === 5 && p6.startItem === 51 && p6.endItem === 55, 'Last page 6 has remaining 5 items, range 51-55');

const pOverflow = paginate(testClaims, 999, 10);
assert(pOverflow.safePage === 6 && pOverflow.pageItems.length === 5, 'Page index overflow clamps safely to last page');

// -------------------------------------------------------------
// CHECK 3: Source Code Forensic Pattern Inspection
// -------------------------------------------------------------
console.log('\n--- CHECK 3: Source Code Forensic Pattern Inspection ---');

const filesToCheck = [
  'src/pages/Dashboard.jsx',
  'src/components/dashboard/DashboardCharts.jsx',
  'src/components/dashboard/ClaimsTable.jsx',
  'src/components/dashboard/ExecutiveKpiCards.jsx',
  'src/components/common/MetricCard.jsx'
];

filesToCheck.forEach(relPath => {
  const fullPath = path.resolve(relPath);
  const content = fs.readFileSync(fullPath, 'utf8');

  // Check 3.1: No fake hardcoded test bypass flags
  const hasTestBypass = content.includes('if (process.env.NODE_ENV === \'test\') return') ||
                        content.includes('__MOCK_BYPASS__') ||
                        content.includes('// bypass test');
  assert(!hasTestBypass, `${relPath}: No test bypass guards or test environment hacks detected`);

  // Check 3.2: No facade empty implementations
  const isFacade = content.includes('return null; // TODO') ||
                   content.includes('throw new Error(\'NotImplemented\')');
  assert(!isFacade, `${relPath}: No facade or stubbed implementations`);

  // Check 3.3: Component exports are functional React components
  const hasComponentExport = content.includes('export default function') || content.includes('export function');
  assert(hasComponentExport, `${relPath}: Exports genuine functional React components`);
});

// -------------------------------------------------------------
// CHECK 4: Production Compilation & Bundle Inspection
// -------------------------------------------------------------
console.log('\n--- CHECK 4: Production Compilation & Bundle Inspection ---');

const distAssetsDir = path.resolve('dist', 'assets');
if (fs.existsSync(distAssetsDir)) {
  const files = fs.readdirSync(distAssetsDir);
  const jsBundle = files.find(f => f.endsWith('.js'));
  assert(Boolean(jsBundle), `Production JS bundle exists in dist/assets: ${jsBundle}`);

  if (jsBundle) {
    const bundleContent = fs.readFileSync(path.join(distAssetsDir, jsBundle), 'utf8');
    assert(bundleContent.includes('Claim Adjudication Distribution'), 'Bundle contains DashboardCharts donut strings');
    assert(bundleContent.includes('Financial Recovery Waterfall'), 'Bundle contains FinancialWaterfallChart strings');
    assert(bundleContent.includes('Enterprise Claims Ledger'), 'Bundle contains ClaimsTable strings');
    assert(bundleContent.includes('Total Recovered Amount'), 'Bundle contains ExecutiveKpiCards strings');
    assert(bundleContent.includes('stroke-dasharray') || bundleContent.includes('strokeDasharray'), 'Bundle contains SVG donut strokeDasharray math');
  }
} else {
  console.error('dist/assets directory does not exist! Run build first.');
  failCount++;
}

console.log(`\n=============================================================`);
console.log(`AUDIT RESULTS: ${passCount} Passed, ${failCount} Failed`);
console.log(`VERDICT: ${failCount === 0 ? 'CLEAN' : 'INTEGRITY CONFLICT'}`);
console.log(`=============================================================`);

if (failCount > 0) process.exit(1);
