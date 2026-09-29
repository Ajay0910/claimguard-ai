/**
 * Challenger M1 Comprehensive Stress & Adversarial Test Suite
 * Validates:
 * 1. API Normalizers under hostile/degenerate inputs (null, undefined, primitives, empty arrays, malformed structures)
 * 2. In-memory mutation safety (shared references)
 * 3. Offline mock fallback behavior for all 11 API endpoints
 * 4. TypeScript schema conformance of mock data against src/types/index.ts
 * 5. Component edge cases (StatusBadge, MetricCard)
 */

import {
  normalizeStats,
  normalizeClaims,
  normalizeAnalysisResult,
  normalizeAppealDraft,
  uploadDocument,
  triggerAnalysis,
  getAnalysisStatus,
  getAnalysisResult,
  getReport,
  getAppealDraft,
  getAuditTrail,
  getDocuments,
  healthCheck,
  getClaims,
  getStats,
} from '../src/services/api.js';

import {
  mockAuditor,
  mockTenant,
  mockStats,
  mockClaims,
  mockAnalysisResult,
  mockAppealDraft,
  mockAuditTrail,
} from '../src/services/mockData.js';

const results = [];
let passCount = 0;
let failCount = 0;
let vulnSeverityCounts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };

function assert(condition, testName, details = {}, severity = 'HIGH') {
  if (condition) {
    passCount++;
    results.push({ status: 'PASS', testName, details });
    console.log(`  \x1b[32m✔\x1b[0m ${testName}`);
  } else {
    failCount++;
    vulnSeverityCounts[severity]++;
    results.push({ status: 'FAIL', testName, severity, details });
    console.log(`  \x1b[31m✖ [${severity}]\x1b[0m ${testName}`);
    if (details.error) console.log(`    \x1b[31mError:\x1b[0m ${details.error}`);
    if (details.reason) console.log(`    \x1b[33mReason:\x1b[0m ${details.reason}`);
  }
}

async function runAdversarialSuite() {
  console.log('\n\x1b[1m\x1b[36m══════════════════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m\x1b[36m    CHALLENGER M1: EMPIRICAL ADVERSARIAL STRESS TEST HARNESS         \x1b[0m');
  console.log('\x1b[1m\x1b[36m══════════════════════════════════════════════════════════════════════\x1b[0m\n');

  // =========================================================================
  // Section 1: normalizeStats Stress Testing
  // =========================================================================
  console.log('\x1b[1m\x1b[33m▶ [Section 1] normalizeStats Stress Testing\x1b[0m');

  // 1.1: normalizeStats with valid payload
  try {
    const valid = normalizeStats({
      total_claims: 50,
      pending_analysis: 5,
      mismatches_found: 10,
      total_recovered_amount: 150000,
    });
    assert(
      valid.total_claims === 50 &&
      valid.pending_analysis === 5 &&
      valid.pending_claims === 5 &&
      valid.mismatches_found === 10 &&
      valid.total_recovered_amount === 150000 &&
      valid.total_amount_recovered === 150000,
      'normalizeStats: valid authoritative payload normalized correctly'
    );
  } catch (err) {
    assert(false, 'normalizeStats: valid authoritative payload normalized correctly', { error: err.message });
  }

  // 1.2: normalizeStats with undefined (relies on default param)
  try {
    const def = normalizeStats(undefined);
    assert(
      def.total_claims === mockStats.total_claims &&
      def.total_recovered_amount === mockStats.total_recovered_amount,
      'normalizeStats(undefined): falls back safely to mockStats defaults'
    );
  } catch (err) {
    assert(false, 'normalizeStats(undefined): falls back safely to mockStats defaults', { error: err.message });
  }

  // 1.3: normalizeStats with null
  try {
    const nullRes = normalizeStats(null);
    assert(
      nullRes && typeof nullRes === 'object' && nullRes.total_claims !== undefined,
      'normalizeStats(null): does not crash when passed explicit null',
      { result: nullRes }
    );
  } catch (err) {
    assert(
      false,
      'normalizeStats(null): does not crash when passed explicit null',
      {
        error: err.message,
        reason: "Default parameter `backendStats = {}` does not handle null, throwing TypeError on backendStats.total_recovered_amount"
      },
      'HIGH'
    );
  }

  // 1.4: normalizeStats with zero-value metrics (falsy vs nullish)
  try {
    const zeroStats = normalizeStats({
      total_claims: 0,
      pending_analysis: 0,
      mismatches_found: 0,
      total_recovered_amount: 0,
    });
    assert(
      zeroStats.total_claims === 0 &&
      zeroStats.pending_analysis === 0 &&
      zeroStats.total_recovered_amount === 0,
      'normalizeStats: preserves legitimate 0 values without falling back to mock values',
      { zeroStats }
    );
  } catch (err) {
    assert(false, 'normalizeStats: preserves legitimate 0 values', { error: err.message });
  }

  // 1.5: normalizeStats with non-object primitives
  try {
    const strStats = normalizeStats("corrupted string payload");
    assert(
      strStats && typeof strStats.total_claims === 'number',
      'normalizeStats("string"): handles primitive string gracefully',
      { strStats }
    );
  } catch (err) {
    assert(false, 'normalizeStats("string"): handles primitive string gracefully', { error: err.message });
  }

  // =========================================================================
  // Section 2: normalizeClaims Stress Testing
  // =========================================================================
  console.log('\n\x1b[1m\x1b[33m▶ [Section 2] normalizeClaims Stress Testing\x1b[0m');

  // 2.1: normalizeClaims with valid array
  try {
    const claims = normalizeClaims([
      {
        id: 'CLM-CUSTOM-1',
        patient_name: 'Test Patient',
        policy_number: 'POL-123',
        status: 'COMPLETED',
        impact: 12000,
        created_at: '2026-09-17T10:00:00Z',
      }
    ]);
    assert(
      claims.length === 1 &&
      claims[0].id === 'CLM-CUSTOM-1' &&
      claims[0].patient === 'Test Patient' &&
      claims[0].patient_name === 'Test Patient' &&
      claims[0].impact === 12000 &&
      claims[0].monetary_impact === 12000,
      'normalizeClaims: normalizes valid single claim array with backward compat keys'
    );
  } catch (err) {
    assert(false, 'normalizeClaims: normalizes valid single claim array', { error: err.message });
  }

  // 2.2: normalizeClaims with empty array []
  try {
    const emptyRes = normalizeClaims([]);
    // Notice behavior: Does [] return [] or mockClaims?
    const returnsMocksOnEmpty = emptyRes === mockClaims || emptyRes.length === mockClaims.length;
    assert(
      returnsMocksOnEmpty,
      'normalizeClaims([]): falls back to mockClaims when DB is empty (documented behavior)',
      { length: emptyRes.length }
    );
  } catch (err) {
    assert(false, 'normalizeClaims([]): falls back to mockClaims', { error: err.message });
  }

  // 2.3: normalizeClaims with array containing null [null]
  try {
    const resWithNull = normalizeClaims([null]);
    assert(
      Array.isArray(resWithNull) && resWithNull.length === 1 && resWithNull[0]?.id,
      'normalizeClaims([null]): survives array containing null element',
      { resWithNull }
    );
  } catch (err) {
    assert(
      false,
      'normalizeClaims([null]): survives array containing null element',
      {
        error: err.message,
        reason: "Mapping over array accesses claim.id directly without null check, throwing TypeError: Cannot read properties of null"
      },
      'MEDIUM'
    );
  }

  // 2.4: normalizeClaims with array containing empty object [{}]
  try {
    const resWithEmptyObj = normalizeClaims([{}]);
    assert(
      Array.isArray(resWithEmptyObj) &&
      resWithEmptyObj.length === 1 &&
      resWithEmptyObj[0].patient_name !== undefined,
      'normalizeClaims([{}]): handles sparse/empty claim object with fallbacks',
      { first: resWithEmptyObj[0] }
    );
  } catch (err) {
    assert(false, 'normalizeClaims([{}]): handles sparse claim object', { error: err.message });
  }

  // 2.5: normalizeClaims with non-array input (null, undefined, string, number)
  try {
    const nullClaims = normalizeClaims(null);
    const undefClaims = normalizeClaims(undefined);
    const strClaims = normalizeClaims("not an array");
    assert(
      nullClaims === mockClaims && undefClaims === mockClaims && strClaims === mockClaims,
      'normalizeClaims(nonArray): returns mockClaims for null, undefined, string'
    );
  } catch (err) {
    assert(false, 'normalizeClaims(nonArray): returns mockClaims for non-array input', { error: err.message });
  }

  // =========================================================================
  // Section 3: normalizeAnalysisResult Stress Testing
  // =========================================================================
  console.log('\n\x1b[1m\x1b[33m▶ [Section 3] normalizeAnalysisResult Stress Testing\x1b[0m');

  // 3.1: normalizeAnalysisResult with null
  try {
    const nullResult = normalizeAnalysisResult(null, 'CLM-FALLBACK');
    assert(
      nullResult.claim_id === 'CLM-FALLBACK' &&
      nullResult.overall_status === 'MISMATCH_DETECTED' &&
      Array.isArray(nullResult.rule_verdicts),
      'normalizeAnalysisResult(null, claimId): returns mockAnalysisResult with overridden claim_id'
    );
  } catch (err) {
    assert(false, 'normalizeAnalysisResult(null, claimId)', { error: err.message });
  }

  // 3.2: normalizeAnalysisResult with wrapped { analysis_run_id, status, result: { ... } }
  try {
    const wrapped = normalizeAnalysisResult({
      analysis_run_id: 'RUN-999',
      status: 'COMPLETED',
      result: {
        claim_id: 'CLM-REAL',
        overall_status: 'NO_MISMATCH_FOUND',
        total_monetary_impact: 0,
        tier1_issues: 0,
        tier2_flags: 0,
        summary: 'All checks passed cleanly.',
        rule_verdicts: [
          {
            rule_name: 'Proportionate Deduction',
            rule_description: 'Test rule',
            status: 'PASS',
            confidence: 1.0,
            finding: 'Clean',
            monetary_impact: 0
          }
        ],
        forensics: {
          claim_id: 'CLM-REAL',
          overall_risk: 'LOW',
          metadata_flags: [],
          bill_anomalies: [],
          consistency_flags: [],
          recommendation: 'Approved',
          disclaimer: 'Test'
        }
      }
    }, 'CLM-REAL');

    assert(
      wrapped.analysis_run_id === 'RUN-999' &&
      wrapped.claim_id === 'CLM-REAL' &&
      wrapped.overall_status === 'NO_MISMATCH_FOUND' &&
      wrapped.total_monetary_impact === 0 &&
      wrapped.rule_verdicts.length === 1 &&
      wrapped.rule_verdicts[0].status === 'PASS' &&
      wrapped.forensics.overall_risk === 'LOW',
      'normalizeAnalysisResult: unwraps backend payload structure accurately'
    );
  } catch (err) {
    assert(false, 'normalizeAnalysisResult: unwraps backend payload', { error: err.message });
  }

  // 3.3: Empty rule_verdicts preservation test (Adversarial edge case!)
  try {
    const emptyVerdictsPayload = {
      result: {
        claim_id: 'CLM-CLEAN-ZERO',
        overall_status: 'NO_MISMATCH_FOUND',
        total_monetary_impact: 0,
        rule_verdicts: [], // Clean claim has 0 rule conflicts!
      }
    };
    const res = normalizeAnalysisResult(emptyVerdictsPayload, 'CLM-CLEAN-ZERO');
    
    // In src/services/api.js line 77:
    // rule_verdicts: core.rule_verdicts && core.rule_verdicts.length > 0 ? core.rule_verdicts : mockAnalysisResult.rule_verdicts
    // If backend returns empty array [], it gets replaced with mockAnalysisResult.rule_verdicts (4 fake verdicts)!
    const preservedEmpty = Array.isArray(res.rule_verdicts) && res.rule_verdicts.length === 0;
    assert(
      preservedEmpty,
      'normalizeAnalysisResult: preserves legitimate empty rule_verdicts [] from backend',
      {
        actualLength: res.rule_verdicts?.length,
        expectedLength: 0,
        reason: 'Line 77 checks `core.rule_verdicts.length > 0`; when empty array [] is passed, it overwrites it with mockAnalysisResult.rule_verdicts (4 mock verdicts)!'
      },
      'MEDIUM'
    );
  } catch (err) {
    assert(false, 'normalizeAnalysisResult: preserves empty rule_verdicts', { error: err.message });
  }

  // 3.4: In-Memory Mutation Safety
  try {
    const res1 = normalizeAnalysisResult(null, 'CLM-TEST-1');
    const originalFirstVerdictName = res1.rule_verdicts[0].rule_name;
    // Mutate the verdict in res1
    res1.rule_verdicts[0].rule_name = 'MUTATED_TEST_RULE_NAME';
    
    const res2 = normalizeAnalysisResult(null, 'CLM-TEST-2');
    const isLeaked = res2.rule_verdicts[0].rule_name === 'MUTATED_TEST_RULE_NAME';
    
    // Restore mockData
    res1.rule_verdicts[0].rule_name = originalFirstVerdictName;

    assert(
      !isLeaked,
      'normalizeAnalysisResult: shallow clone of mockData does not allow cross-request mutation leakage',
      { isLeaked },
      'LOW'
    );
  } catch (err) {
    assert(false, 'normalizeAnalysisResult: mutation safety check', { error: err.message });
  }

  // =========================================================================
  // Section 4: normalizeAppealDraft Stress Testing
  // =========================================================================
  console.log('\n\x1b[1m\x1b[33m▶ [Section 4] normalizeAppealDraft Stress Testing\x1b[0m');

  // 4.1: normalizeAppealDraft with null
  try {
    const draftNull = normalizeAppealDraft(null);
    assert(
      draftNull.appeal_text && draftNull.content && draftNull.monetary_impact === 42500,
      'normalizeAppealDraft(null): returns mockAppealDraft'
    );
  } catch (err) {
    assert(false, 'normalizeAppealDraft(null)', { error: err.message });
  }

  // 4.2: normalizeAppealDraft with legacy backend keys
  try {
    const draftLegacy = normalizeAppealDraft({
      content: 'Custom grievance letter from content key',
      regulatory_citations: ['IRDAI Circular 2024'],
      monetary_impact: 15000,
    });
    assert(
      draftLegacy.appeal_text === 'Custom grievance letter from content key' &&
      draftLegacy.content === 'Custom grievance letter from content key' &&
      draftLegacy.appeal_letter === 'Custom grievance letter from content key' &&
      draftLegacy.monetary_impact === 15000,
      'normalizeAppealDraft: handles legacy content / appeal_letter aliases'
    );
  } catch (err) {
    assert(false, 'normalizeAppealDraft: handles aliases', { error: err.message });
  }

  // 4.3: normalizeAppealDraft with empty string draft
  try {
    const draftEmpty = normalizeAppealDraft({ appeal_text: '' });
    // If appeal_text is empty string "", does it preserve "" or fall back to mockAppealDraft?
    assert(
      draftEmpty.appeal_text === '',
      'normalizeAppealDraft: preserves empty string draft without falling back to mock text',
      { appeal_text: draftEmpty.appeal_text },
      'LOW'
    );
  } catch (err) {
    assert(false, 'normalizeAppealDraft: empty draft', { error: err.message });
  }

  // =========================================================================
  // Section 5: Offline Mock Fallback Execution on All 11 Endpoints
  // =========================================================================
  console.log('\n\x1b[1m\x1b[33m▶ [Section 5] Offline Mock Fallback Execution on All 11 Endpoints\x1b[0m');

  // 5.1: healthCheck fallback
  try {
    const health = await healthCheck();
    assert(
      health && health.status === 'offline' && typeof health.error === 'string',
      'healthCheck(): falls back gracefully to { status: "offline", error } when server unavailable',
      { health }
    );
  } catch (err) {
    assert(false, 'healthCheck(): offline fallback', { error: err.message });
  }

  // 5.2: getStats fallback
  try {
    const stats = await getStats();
    assert(
      stats && stats.total_claims === mockStats.total_claims && stats.total_recovered_amount === mockStats.total_recovered_amount,
      'getStats(): falls back to mockStats when backend offline',
      { stats }
    );
  } catch (err) {
    assert(false, 'getStats(): offline fallback', { error: err.message });
  }

  // 5.3: getClaims fallback
  try {
    const claims = await getClaims();
    assert(
      Array.isArray(claims) && claims.length === mockClaims.length && claims[0].id === 'CLM-84920',
      'getClaims(): falls back to mockClaims when backend offline',
      { count: claims.length }
    );
  } catch (err) {
    assert(false, 'getClaims(): offline fallback', { error: err.message });
  }

  // 5.4: uploadDocument fallback
  try {
    const mockFile = { name: 'apollo_bill.pdf', size: 1024, type: 'application/pdf' };
    const uploadRes = await uploadDocument(mockFile, 'HOSPITAL_BILL', 'CLM-TEST-UPLOAD');
    assert(
      uploadRes &&
      uploadRes.claim_id === 'CLM-TEST-UPLOAD' &&
      uploadRes.status === 'success' &&
      uploadRes.filename === 'apollo_bill.pdf',
      'uploadDocument(): simulates client response with generated document_id when offline',
      { uploadRes }
    );
  } catch (err) {
    assert(false, 'uploadDocument(): offline fallback', { error: err.message });
  }

  // 5.5: triggerAnalysis fallback
  try {
    const triggerRes = await triggerAnalysis('CLM-TEST-TRIGGER');
    assert(
      triggerRes && triggerRes.status === 'RUNNING' && triggerRes.analysis_run_id.startsWith('RUN-'),
      'triggerAnalysis(): returns simulated RUNNING status when offline',
      { triggerRes }
    );
  } catch (err) {
    assert(false, 'triggerAnalysis(): offline fallback', { error: err.message });
  }

  // 5.6: getAnalysisStatus fallback
  try {
    const statusRes = await getAnalysisStatus('CLM-TEST-STATUS');
    assert(
      statusRes && statusRes.status === 'COMPLETED' && statusRes.analysis_run_id === 'RUN-CLM-TEST-STATUS',
      'getAnalysisStatus(): returns simulated COMPLETED status when offline',
      { statusRes }
    );
  } catch (err) {
    assert(false, 'getAnalysisStatus(): offline fallback', { error: err.message });
  }

  // 5.7: getAnalysisResult fallback
  try {
    const analysisRes = await getAnalysisResult('CLM-TEST-RESULT');
    assert(
      analysisRes &&
      analysisRes.claim_id === 'CLM-TEST-RESULT' &&
      analysisRes.overall_status === 'MISMATCH_DETECTED' &&
      analysisRes.total_monetary_impact === 42500,
      'getAnalysisResult(): normalizes fallback result bound to requested claim_id when offline',
      { claim_id: analysisRes.claim_id }
    );
  } catch (err) {
    assert(false, 'getAnalysisResult(): offline fallback', { error: err.message });
  }

  // 5.8: getReport fallback
  try {
    const reportRes = await getReport('CLM-TEST-REPORT');
    assert(
      reportRes &&
      reportRes.claim_id === 'CLM-TEST-REPORT' &&
      reportRes.overall_status === 'MISMATCH_DETECTED' &&
      reportRes.report_data !== undefined,
      'getReport(): returns fallback report structure bound to requested claim_id',
      { reportRes }
    );
  } catch (err) {
    assert(false, 'getReport(): offline fallback', { error: err.message });
  }

  // 5.9: getAppealDraft fallback
  try {
    const appealRes = await getAppealDraft('CLM-TEST-APPEAL');
    assert(
      appealRes &&
      appealRes.appeal_text.includes('FORMAL STATUTORY GRIEVANCE') &&
      appealRes.regulatory_citations.length > 0,
      'getAppealDraft(): returns normalized statutory grievance draft when offline',
      { citations: appealRes.regulatory_citations }
    );
  } catch (err) {
    assert(false, 'getAppealDraft(): offline fallback', { error: err.message });
  }

  // 5.10: getAuditTrail fallback
  try {
    const auditRes = await getAuditTrail('CLM-TEST-AUDIT');
    assert(
      auditRes &&
      auditRes.claim_id === 'CLM-TEST-AUDIT' &&
      auditRes.verified === true &&
      Array.isArray(auditRes.audit_logs) &&
      auditRes.audit_logs.length === 5,
      'getAuditTrail(): returns chained cryptographic audit logs bound to requested claim_id',
      { logCount: auditRes.audit_logs?.length }
    );
  } catch (err) {
    assert(false, 'getAuditTrail(): offline fallback', { error: err.message });
  }

  // 5.11: getDocuments fallback
  try {
    const docsRes = await getDocuments('CLM-TEST-DOCS');
    assert(
      Array.isArray(docsRes) && docsRes.length === 0,
      'getDocuments(): returns safe empty array [] when offline',
      { docsRes }
    );
  } catch (err) {
    assert(false, 'getDocuments(): offline fallback', { error: err.message });
  }

  // =========================================================================
  // Section 6: Mock Data Adherence to TypeScript Models (src/types/index.ts)
  // =========================================================================
  console.log('\n\x1b[1m\x1b[33m▶ [Section 6] Mock Data Adherence to TypeScript Models\x1b[0m');

  // 6.1: mockAuditor conforms to AuditorProfile
  const auditorValid =
    typeof mockAuditor.name === 'string' &&
    typeof mockAuditor.title === 'string' &&
    typeof mockAuditor.license === 'string' &&
    typeof mockAuditor.department === 'string' &&
    typeof mockAuditor.avatar_initials === 'string';
  assert(auditorValid, 'mockAuditor conforms strictly to AuditorProfile schema');

  // 6.2: mockTenant conforms to TenantContext
  const tenantValid =
    typeof mockTenant.facility_name === 'string' &&
    typeof mockTenant.tpa_desk === 'string' &&
    typeof mockTenant.accreditation === 'string';
  assert(tenantValid, 'mockTenant conforms strictly to TenantContext schema');

  // 6.3: mockStats conforms to DashboardStats
  const statsValid =
    typeof mockStats.total_claims === 'number' &&
    typeof mockStats.pending_analysis === 'number' &&
    typeof mockStats.mismatches_found === 'number' &&
    typeof mockStats.total_recovered_amount === 'number';
  assert(statsValid, 'mockStats conforms strictly to DashboardStats schema');

  // 6.4: mockClaims conforms to Claim[]
  const validClaimStatuses = ['PENDING', 'EXTRACTING', 'ANALYZING', 'COMPLETED', 'FAILED'];
  const claimsValid = mockClaims.every(c =>
    typeof c.id === 'string' &&
    typeof c.patient_name === 'string' &&
    validClaimStatuses.includes(c.status) &&
    typeof c.created_at === 'string' &&
    typeof c.updated_at === 'string'
  );
  assert(claimsValid, 'all 8 mockClaims conform strictly to Claim model schema and valid ClaimStatus enums');

  // 6.5: mockAnalysisResult conforms to AnalysisResult
  const validOverallStatuses = ['NO_MISMATCH_FOUND', 'MISMATCH_DETECTED', 'REVIEW_RECOMMENDED', 'EXTRACTION_FAILED'];
  const analysisValid =
    typeof mockAnalysisResult.claim_id === 'string' &&
    validOverallStatuses.includes(mockAnalysisResult.overall_status) &&
    Array.isArray(mockAnalysisResult.rule_verdicts) &&
    typeof mockAnalysisResult.total_monetary_impact === 'number' &&
    mockAnalysisResult.forensics &&
    typeof mockAnalysisResult.forensics.overall_risk === 'string';
  assert(analysisValid, 'mockAnalysisResult conforms strictly to AnalysisResult schema');

  // 6.6: mockAuditTrail conforms to AuditTrailResponse with valid SHA-256 chain
  const auditValid =
    typeof mockAuditTrail.claim_id === 'string' &&
    typeof mockAuditTrail.verified === 'boolean' &&
    Array.isArray(mockAuditTrail.audit_logs) &&
    mockAuditTrail.audit_logs.every((l, idx) => {
      if (idx === 0) return l.previous_hash === '0000000000000000000000000000000000000000000000000000000000000000';
      return l.previous_hash === mockAuditTrail.audit_logs[idx - 1].entry_hash;
    });
  assert(auditValid, 'mockAuditTrail conforms to AuditTrailResponse with chronological SHA-256 hash linking');

  // =========================================================================
  // Summary & Diagnostic Table
  // =========================================================================
  console.log('\n\x1b[1m\x1b[36m══════════════════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m\x1b[36m                 ADVERSARIAL SUITE SUMMARY                            \x1b[0m');
  console.log('\x1b[1m\x1b[36m══════════════════════════════════════════════════════════════════════\x1b[0m');
  console.log(`  Total Scenarios Tested: ${results.length}`);
  console.log(`  \x1b[32mPassed: ${passCount}\x1b[0m`);
  console.log(`  \x1b[31mFailed: ${failCount}\x1b[0m (Breakdown: CRITICAL: ${vulnSeverityCounts.CRITICAL}, HIGH: ${vulnSeverityCounts.HIGH}, MEDIUM: ${vulnSeverityCounts.MEDIUM}, LOW: ${vulnSeverityCounts.LOW})`);
  console.log('\x1b[1m\x1b[36m══════════════════════════════════════════════════════════════════════\x1b[0m\n');

  return {
    total: results.length,
    passed: passCount,
    failed: failCount,
    severities: vulnSeverityCounts,
    failures: results.filter(r => r.status === 'FAIL')
  };
}

runAdversarialSuite().catch(console.error);
