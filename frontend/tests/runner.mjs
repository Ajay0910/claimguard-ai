/**
 * ClaimGuard AI — Master E2E Automated Test Runner
 * Executes Tiers 1-4, measures execution benchmarks, formats comprehensive ANSI
 * results, and produces the readiness metrics table for TEST_READY.md.
 */

import { context } from './test-framework.mjs';

// Parse command line arguments (e.g. --tier=1)
const args = process.argv.slice(2);
let selectedTier = null;
for (const arg of args) {
  if (arg.startsWith('--tier=')) {
    selectedTier = parseInt(arg.split('=')[1], 10);
  }
}

// ANSI colors
const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const GRAY = '\x1b[90m';

async function runTestSuite() {
  const startTime = Date.now();

  console.log(`\n${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════${RESET}`);
  console.log(`${BOLD}${CYAN}        ClaimGuard AI Frontend — Enterprise E2E Test Runner           ${RESET}`);
  console.log(`${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════${RESET}\n`);

  // Dynamically load test tiers
  if (!selectedTier || selectedTier === 1) {
    await import('./analysis-normalization.test.mjs');
    await import('./tier1-feature-coverage.test.mjs');
  }
  if (!selectedTier || selectedTier === 2) {
    await import('./tier2-boundary-cases.test.mjs');
  }
  if (!selectedTier || selectedTier === 3) {
    await import('./tier3-combinations.test.mjs');
  }
  if (!selectedTier || selectedTier === 4) {
    await import('./tier4-real-world-scenarios.test.mjs');
  }

  let totalTests = 0;
  let totalPassed = 0;
  let totalFailed = 0;
  const failureDetails = [];

  const tierStats = {
    1: { name: 'Tier 1: Feature Coverage & Contracts', total: 0, passed: 0, failed: 0 },
    2: { name: 'Tier 2: Boundary Cases & Adversarial', total: 0, passed: 0, failed: 0 },
    3: { name: 'Tier 3: Combinations & Cross-Module', total: 0, passed: 0, failed: 0 },
    4: { name: 'Tier 4: Real-World Scenarios', total: 0, passed: 0, failed: 0 }
  };

  for (const suite of context.suites) {
    if (selectedTier && suite.tier !== selectedTier) continue;

    console.log(`\n${BOLD}${YELLOW}▶ ${suite.name}${RESET} ${GRAY}(Tier ${suite.tier})${RESET}`);

    for (const test of suite.tests) {
      totalTests++;
      tierStats[test.tier].total++;

      try {
        const result = test.fn();
        if (result && typeof result.then === 'function') {
          await result;
        }
        totalPassed++;
        tierStats[test.tier].passed++;
        console.log(`  ${GREEN}✔${RESET} ${test.name}`);
      } catch (error) {
        totalFailed++;
        tierStats[test.tier].failed++;
        console.log(`  ${RED}✖ ${test.name}${RESET}`);
        console.log(`    ${RED}Error: ${error.message}${RESET}`);
        failureDetails.push({
          suite: suite.name,
          test: test.name,
          tier: test.tier,
          error: error.message,
          stack: error.stack
        });
      }
    }
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Summary Table
  console.log(`\n${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════${RESET}`);
  console.log(`${BOLD}${CYAN}                       TEST EXECUTION SUMMARY                         ${RESET}`);
  console.log(`${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════${RESET}`);

  for (const tierId of [1, 2, 3, 4]) {
    if (selectedTier && selectedTier !== tierId) continue;
    const stats = tierStats[tierId];
    const pct = stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(0) : '0';
    const statusColor = stats.failed === 0 ? GREEN : RED;
    const line = `  ${stats.name.padEnd(42)} [${stats.passed}/${stats.total} Passed] (${pct}%)`;
    console.log(`${statusColor}${line}${RESET}`);
  }

  console.log(`${GRAY}──────────────────────────────────────────────────────────────────────${RESET}`);
  const overallColor = totalFailed === 0 ? `${BOLD}${GREEN}` : `${BOLD}${RED}`;
  console.log(`${overallColor}  Total: ${totalTests} | Passed: ${totalPassed} | Failed: ${totalFailed} | Execution Time: ${duration}s${RESET}`);
  console.log(`${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════${RESET}\n`);

  if (totalFailed > 0) {
    console.log(`${BOLD}${RED}FAILURES DETECTED (${totalFailed}):${RESET}`);
    failureDetails.forEach((f, idx) => {
      console.log(`\n${idx + 1}) [Tier ${f.tier}] ${f.suite} -> ${f.test}`);
      console.log(`   ${RED}${f.error}${RESET}`);
    });
    if (process.env.NODE_ENV !== 'test_embed') {
      process.exit(1);
    }
    return { success: false, totalTests, totalPassed, totalFailed, tierStats, duration };
  } else {
    console.log(`${BOLD}${GREEN}🎉 ALL ${totalTests} E2E TESTS PASSED SUCCESSFULLY!${RESET}\n`);
    return { success: true, totalTests, totalPassed, totalFailed, tierStats, duration };
  }
}

// Auto-run when executed as main script
runTestSuite().catch(err => {
  console.error('Test runner fatal error:', err);
  process.exit(1);
});
