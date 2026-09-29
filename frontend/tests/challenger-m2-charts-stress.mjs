/**
 * ClaimGuard AI — Challenger M2 Charts & Visualizations Stress Test Harness
 * Author: challenger_m2_2 (teamwork_preview_challenger)
 * 
 * Verifies:
 * 1. SVG Donut chart when total count is 0 (all slices 0) — NaN / divide-by-zero checks.
 * 2. 100% single category donut — gap artifact analysis.
 * 3. Waterfall chart with extreme values: 0 billed, negative recoverable, disallowed > billed.
 * 4. Sparkline curve generator in MetricCard.jsx: [], [42], [10, 10, 10], negatives, null/undefined/corrupted inputs.
 * 5. Cross-filtering callbacks: click event when onSelectStatusFilter is undefined/null/non-function.
 * 6. Rule conflict bar chart and currency helper boundaries.
 */

import { build } from 'vite';
import path from 'path';
import fs from 'fs';

const projectRoot = path.resolve('.');

// ANSI Color definitions
const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const MAGENTA = '\x1b[35m';
const GRAY = '\x1b[90m';

async function runChartsStress() {
  const startTime = Date.now();

  console.log(`\n${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════════${RESET}`);
  console.log(`${BOLD}${CYAN}  CHALLENGER M2: SVG MATH, CHART GEOMETRY & VISUALIZATION STRESS HARNESS ${RESET}`);
  console.log(`${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════════${RESET}\n`);

  // Step 1: Compile SSR bundle using Vite
  console.log(`${GRAY}[1/3] Compiling SSR test bundle for DashboardCharts & MetricCard...${RESET}`);
  const outDir = path.join(projectRoot, 'node_modules', '.stress-test-bundle-m2-charts');

  await build({
    root: projectRoot,
    build: {
      ssr: true,
      lib: {
        entry: path.join(projectRoot, 'tests', 'challenger-m2-charts-harness.jsx'),
        formats: ['es'],
        fileName: 'challenger-m2-charts-harness',
      },
      outDir,
      emptyOutDir: true,
      rollupOptions: {
        external: [
          'react',
          'react-dom',
          'react-dom/server',
          'react-router-dom',
          '@tanstack/react-query',
          'lucide-react',
          'react-hot-toast',
          'axios',
          'react-dropzone',
          'framer-motion',
          'sonner',
          'clsx',
          'tailwind-merge',
        ],
      },
    },
  });

  // Step 2: Import compiled harness
  console.log(`${GRAY}[2/3] Loading compiled SSR harness into Node.js runtime...${RESET}`);
  const bundlePath = path.join(outDir, 'challenger-m2-charts-harness.js');
  const { runChartStressTests } = await import(`file://${bundlePath}`);

  // Step 3: Execute tests
  console.log(`${GRAY}[3/3] Executing adversarial test scenarios...${RESET}\n`);
  const { testResults, vulnerabilities } = runChartStressTests();

  // Group results by category
  const categories = {};
  for (const t of testResults) {
    if (!categories[t.category]) categories[t.category] = [];
    categories[t.category].push(t);
  }

  let passedTotal = 0;
  let failedTotal = 0;

  for (const [catName, tests] of Object.entries(categories)) {
    console.log(`\n${BOLD}${MAGENTA}▶ Category: ${catName}${RESET}`);
    for (const t of tests) {
      if (t.passed) {
        passedTotal++;
        console.log(`  ${GREEN}✔ [PASS]${RESET} ${BOLD}${t.id}${RESET}: ${t.title}`);
      } else {
        failedTotal++;
        const sevColor = t.severity === 'CRITICAL' || t.severity === 'HIGH' ? RED : YELLOW;
        console.log(`  ${RED}✖ [${sevColor}${t.severity}${RED}]${RESET} ${BOLD}${t.id}${RESET}: ${t.title}`);
        if (t.details && t.details.note) {
          console.log(`     ${YELLOW}Finding:${RESET} ${t.details.note}`);
        }
        if (t.details && t.details.vulnerabilityReason) {
          console.log(`     ${RED}Reason:${RESET} ${t.details.vulnerabilityReason}`);
        }
        if (t.details && t.details.error) {
          console.log(`     ${RED}Error:${RESET} ${t.details.error}`);
        }
      }
    }
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Summary Report
  console.log(`\n${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════════${RESET}`);
  console.log(`${BOLD}${CYAN}                         CHALLENGE AUDIT SUMMARY                         ${RESET}`);
  console.log(`${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════════${RESET}`);
  console.log(`  Total Test Scenarios : ${BOLD}${testResults.length}${RESET}`);
  console.log(`  Passed               : ${GREEN}${passedTotal}${RESET}`);
  console.log(`  Adversarial Findings : ${failedTotal > 0 ? YELLOW : GREEN}${failedTotal}${RESET}`);
  console.log(`  Execution Time       : ${duration}s`);
  console.log(`${BOLD}${CYAN}──────────────────────────────────────────────────────────────────────────${RESET}`);

  if (vulnerabilities.length > 0) {
    console.log(`\n${BOLD}${YELLOW}IDENTIFIED BEHAVIORAL LIMITATIONS & VULNERABILITIES (${vulnerabilities.length}):${RESET}`);
    vulnerabilities.forEach((v, idx) => {
      const sevColor = v.severity === 'CRITICAL' || v.severity === 'HIGH' ? RED : YELLOW;
      console.log(`\n${idx + 1}. [${sevColor}${v.severity}${RESET}] ${BOLD}${v.id}: ${v.title}${RESET}`);
      if (v.details.vulnerabilityReason) {
        console.log(`   ${RED}Detail:${RESET} ${v.details.vulnerabilityReason}`);
      }
      if (v.details.note) {
        console.log(`   ${YELLOW}Detail:${RESET} ${v.details.note}`);
      }
    });
  } else {
    console.log(`\n${BOLD}${GREEN}✔ ALL ADVERSARIAL CHECKS CONFIRMED RESILIENT WITH ZERO DEFECTS.${RESET}`);
  }

  console.log(`\n${BOLD}${CYAN}══════════════════════════════════════════════════════════════════════════${RESET}\n`);

  // Return full report for programmatic assertions
  return {
    testResults,
    vulnerabilities,
    passedTotal,
    failedTotal,
    duration,
  };
}

runChartsStress().catch((err) => {
  console.error(`${RED}Stress test harness execution failed:${RESET}`, err);
  process.exit(1);
});
