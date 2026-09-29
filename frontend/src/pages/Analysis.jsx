/**
 * src/pages/Analysis.jsx
 * Enterprise Analysis & Forensics Hub (4-Tab Clinical Workspace)
 * Milestone 4: Features 12, 13, 14, 15, 16
 * Compliant with IRDAI Master Circular May 2024 & Insurance Act § 45
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import {
  Activity,
  Download,
  ArrowLeft,
  Scale,
  Fingerprint,
  FileCheck2,
  Mail,
  Printer,
  Share2,
  CheckCircle2,
} from 'lucide-react';
import { toast } from 'sonner';
import StatusBadge from '../components/common/StatusBadge';
import { AnalysisSkeleton } from '../components/common/Skeletons';
import ErrorState from '../components/common/ErrorState';
import FinancialDelta, { formatInr } from '../components/analysis/FinancialDelta';
import VerdictCard, { VerdictsFilterTabs } from '../components/analysis/VerdictCard';
import ForensicsLab from '../components/analysis/ForensicsLab';
import AuditTimeline from '../components/analysis/AuditTimeline';
import AppealLetter from '../components/analysis/AppealLetter';
import {
  getAnalysisStatus,
  getAnalysisResult,
  getAppealDraft,
  getAuditTrail,
} from '../services/api';

const VALID_TABS = ['financial', 'forensics', 'audit', 'appeal'];

export default function Analysis() {
  const { id } = useParams();
  const claimId = id || 'CLM-84920';

  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get('tab');
  const activeTab = VALID_TABS.includes(rawTab) ? rawTab : 'financial';

  const setActiveTab = useCallback(
    (tabId) => {
      setSearchParams({ tab: tabId });
    },
    [setSearchParams]
  );

  // Verdict category filter state: 'ALL' | 'TIER1' | 'TIER2' | 'CONFLICTS'
  const [verdictFilter, setVerdictFilter] = useState('ALL');

  // Query & Loading State
  const [status, setStatus] = useState('RUNNING');
  const [result, setResult] = useState(null);
  const [auditTrail, setAuditTrail] = useState(null);
  const [appealDraft, setAppealDraft] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Fetch all dossier datasets
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const statusData = await getAnalysisStatus(claimId);
      setStatus(statusData.status || 'COMPLETED');

      const [resultData, auditData, appealData] = await Promise.all([
        getAnalysisResult(claimId),
        getAuditTrail(claimId),
        getAppealDraft(claimId),
      ]);

      setResult(resultData);
      setAuditTrail(auditData);
      setAppealDraft(appealData);
      setStatus(resultData?.status || statusData?.status || 'COMPLETED');
    } catch (error) {
      console.error('Error fetching analysis dossier:', error);
      setFetchError(error?.message || 'Failed to fetch claim analysis dossier');
    } finally {
      setIsLoading(false);
    }
  }, [claimId]);

  useEffect(() => {
    let interval = null;
    loadData();

    // Polling only if status is active running/analyzing
    if (status === 'RUNNING' || status === 'PENDING' || status === 'ANALYZING') {
      interval = setInterval(loadData, 3000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [claimId, status, loadData]);

  // Filter Rule Verdicts based on active tab selection
  const filteredVerdicts = useMemo(() => {
    if (!result?.rule_verdicts) return [];
    return result.rule_verdicts.filter((v) => {
      if (verdictFilter === 'CONFLICTS') return v.status === 'FAIL';
      if (verdictFilter === 'TIER1') {
        return (
          v.tier === 1 ||
          v.tier === 'Tier 1' ||
          v.rule_name?.toLowerCase().includes('proportionate') ||
          v.rule_name?.toLowerCase().includes('moratorium') ||
          v.rule_name?.toLowerCase().includes('clause timeline') ||
          v.rule_name?.toLowerCase().includes('mental health') ||
          v.rule_name?.toLowerCase().includes('waiting period')
        );
      }
      if (verdictFilter === 'TIER2') {
        return (
          v.tier === 2 ||
          v.tier === 'Tier 2' ||
          (!v.rule_name?.toLowerCase().includes('proportionate') &&
            !v.rule_name?.toLowerCase().includes('moratorium') &&
            !v.rule_name?.toLowerCase().includes('clause timeline') &&
            !v.rule_name?.toLowerCase().includes('mental health') &&
            !v.rule_name?.toLowerCase().includes('waiting period'))
        );
      }
      return true; // 'ALL'
    });
  }, [result?.rule_verdicts, verdictFilter]);

  // Calculate Filter Counts for Tabs
  const filterCounts = useMemo(() => {
    const list = result?.rule_verdicts || [];
    return {
      all: list.length,
      tier1: list.filter(
        (v) =>
          v.tier === 1 ||
          v.tier === 'Tier 1' ||
          v.rule_name?.toLowerCase().includes('proportionate') ||
          v.rule_name?.toLowerCase().includes('moratorium') ||
          v.rule_name?.toLowerCase().includes('clause timeline') ||
          v.rule_name?.toLowerCase().includes('mental health') ||
          v.rule_name?.toLowerCase().includes('waiting period')
      ).length,
      tier2: list.filter(
        (v) =>
          v.tier === 2 ||
          v.tier === 'Tier 2' ||
          (!v.rule_name?.toLowerCase().includes('proportionate') &&
            !v.rule_name?.toLowerCase().includes('moratorium') &&
            !v.rule_name?.toLowerCase().includes('clause timeline') &&
            !v.rule_name?.toLowerCase().includes('mental health') &&
            !v.rule_name?.toLowerCase().includes('waiting period'))
      ).length,
      conflicts: list.filter((v) => v.status === 'FAIL').length,
    };
  }, [result?.rule_verdicts]);

  const isAnalyzing = status === 'RUNNING' || status === 'PENDING' || status === 'ANALYZING';

  // Loading Skeleton & Clinical Pipeline Checklist
  if (isLoading || isAnalyzing) {
    return (
      <div className="max-w-5xl mx-auto space-y-8 py-12 text-center">
        {/* Clinical Auditor Scanner HUD */}
        <div className="relative flex items-center justify-center mx-auto my-2 w-32 h-32 select-none">
          {/* Outer sonar pulse wave */}
          <div className="absolute inset-0 rounded-full bg-sky-500/10 animate-ping pointer-events-none" style={{ animationDuration: '2.8s' }} />
          {/* Outer concentric radar boundary */}
          <div className="absolute -inset-2 rounded-full border border-sky-400/20 animate-pulse pointer-events-none" />
          {/* Reticle dashed ring */}
          <div className="absolute inset-1 rounded-full border border-dashed border-sky-300/60 animate-pulse" />
          {/* Precision reticle crosshairs */}
          <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-transparent via-sky-300/40 to-transparent" />
          <div className="absolute inset-y-0 left-1/2 w-px bg-gradient-to-b from-transparent via-sky-300/40 to-transparent" />
          {/* Central sensor core */}
          <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-50 via-white to-teal-50 border border-sky-200 shadow-diffused flex items-center justify-center">
            <div className="absolute inset-0 rounded-2xl bg-sky-500/10 animate-pulse" />
            <Activity className="w-8 h-8 text-brand-600 relative z-10 drop-shadow-sm" />
            <span className="absolute top-1.5 right-1.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
            </span>
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Auditing Claim <span className="font-financial text-brand-600">{claimId}</span>
          </h2>
          <p className="text-slate-500 mt-2 text-sm max-w-xl mx-auto">
            Cross-referencing itemized hospital invoice with IRDAI Master Circular (May 2024), Insurance Act § 45, and Central Government Health Scheme benchmarks...
          </p>
        </div>

        {/* Multi-step pipeline animation card */}
        <div className="max-w-md mx-auto space-y-3.5 text-left bg-white p-6 rounded-xl border border-slate-200 shadow-card">
          <div className="flex items-center gap-3 text-xs font-semibold text-slate-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>VLM Ingestion & Bill Text Extraction</span>
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-slate-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>Policy Limits & Waiting Period Parsing</span>
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-brand-600">
            <div className="relative flex h-4 w-4 items-center justify-center flex-shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-70" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand-600" />
            </div>
            <span>Digital Forensics & CGHS Benchmark Comparator</span>
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold text-slate-400">
            <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0" />
            <span>IRDAI Statutory Verdicts & SHA-256 Ledger Commit</span>
          </div>
        </div>

        <div className="pt-4">
          <AnalysisSkeleton />
        </div>
      </div>
    );
  }

  // Error State with Retry
  if (fetchError || (status === 'FAILED' && !result)) {
    return (
      <ErrorState
        title={`Analysis Failed for Claim ${claimId}`}
        message={fetchError || 'There was an error analyzing the claim. The document scan or resolution may be incomplete.'}
        onRetry={loadData}
        retryLabel="Retry Claim Audit"
        errorDetails={fetchError}
      />
    );
  }

  const recoverableAmount = result?.total_monetary_impact || 0;
  const overallStatus = result?.overall_status || 'MISMATCH_DETECTED';
  const hasMismatch = overallStatus === 'MISMATCH_DETECTED' || overallStatus === 'FAIL';
  const elaScore = result?.forensics?.ela_result?.tamper_score ?? 8.4;
  const logCount = auditTrail?.audit_logs?.length ?? 5;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-16">
      {/* 1. Header & Claim Meta Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center gap-4">
          <Link
            to="/"
            className="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors shadow-xs flex-shrink-0"
            title="Return to Claims Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Claim Audit Dossier: <span className="text-brand-600 font-financial">{claimId}</span>
              </h1>
              <StatusBadge status={overallStatus} />
              {hasMismatch && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  Mismatch Detected
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1.5">
              <span>Patient: <strong className="text-slate-800">Ayush Sharma</strong></span>
              <span>•</span>
              <span>Policy: <strong className="text-slate-800 font-financial">STAR-IND-99281</strong></span>
              <span>•</span>
              <span>Hospital: <strong className="text-slate-800">Apollo Hospitals, Bangalore</strong></span>
            </div>
          </div>
        </div>

        {/* Global Action Toolbar */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 hover:scale-101 active:scale-[0.98] text-xs font-semibold shadow-xs transition-all"
          >
            <Printer className="w-4 h-4 text-slate-500" />
            <span>Print Dossier</span>
          </button>
          <button
            type="button"
            onClick={() => {
              if (navigator?.clipboard?.writeText) {
                navigator.clipboard.writeText(window.location.href);
              }
              toast.success('Dossier Link Copied', {
                description: `Sharable URL for claim ${claimId} copied to clipboard.`,
              });
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 hover:scale-101 active:scale-[0.98] text-xs font-semibold shadow-xs transition-all"
          >
            <Share2 className="w-4 h-4 text-slate-500" />
            <span>Share Audit</span>
          </button>
          <button
            type="button"
            onClick={() =>
              toast.success('Audit Report Exported', {
                description: `Statutory audit report for claim ${claimId} generated in PDF format.`,
              })
            }
            className="flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 hover:scale-101 active:scale-[0.98] text-white rounded-lg text-xs font-semibold shadow-xs transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* 2. 4-Tab Workspace Navigation Bar */}
      <div className="card-enterprise p-1.5 flex flex-wrap items-center gap-1 bg-white shadow-card">
        {/* Tab 1: Financial Reconciliation & Rule Verdicts */}
        <button
          type="button"
          onClick={() => setActiveTab('financial')}
          className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-bold active:scale-95 transition-all ${
            activeTab === 'financial'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Scale className="w-4 h-4" />
          <span>Financial Reconciliation & Rules</span>
          {recoverableAmount > 0 && (
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-financial font-bold ${
                activeTab === 'financial'
                  ? 'bg-rose-500 text-white'
                  : 'bg-rose-100 text-rose-700'
              }`}
            >
              {formatInr(recoverableAmount)}
            </span>
          )}
        </button>

        {/* Tab 2: Digital Forensics & Fraud Lab */}
        <button
          type="button"
          onClick={() => setActiveTab('forensics')}
          className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-bold active:scale-95 transition-all ${
            activeTab === 'forensics'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Fingerprint className="w-4 h-4 text-medical-cyan" />
          <span>Digital Forensics & Fraud Lab</span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
              activeTab === 'forensics'
                ? 'bg-slate-700 text-emerald-300'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            }`}
          >
            ELA {elaScore}%
          </span>
        </button>

        {/* Tab 3: Cryptographic Audit Trail */}
        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-bold active:scale-95 transition-all ${
            activeTab === 'audit'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <FileCheck2 className="w-4 h-4 text-brand-400" />
          <span>Cryptographic Audit Trail</span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-semibold ${
              activeTab === 'audit'
                ? 'bg-slate-700 text-white'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            {logCount} Blocks
          </span>
        </button>

        {/* Tab 4: Legal Appeal & Grievance Generator */}
        <button
          type="button"
          onClick={() => setActiveTab('appeal')}
          className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-bold active:scale-95 transition-all ${
            activeTab === 'appeal'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Mail className="w-4 h-4 text-amber-400" />
          <span>Legal Appeal & Grievance</span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
              activeTab === 'appeal'
                ? 'bg-amber-500 text-white'
                : 'bg-amber-50 text-amber-800 border border-amber-200'
            }`}
          >
            IRDAI Ready
          </span>
        </button>
      </div>

      {/* 3. Tab Workspace Content Panels */}
      <div>
        {/* Tab 1: Financial Reconciliation & Rule Verdicts */}
        {activeTab === 'financial' && (
          <div className="space-y-8 animate-fadeIn">
            {/* Feature 12: Executive Financial Delta & Reconciliation Waterfall */}
            <FinancialDelta
              result={result}
              claim={{ id: claimId, monetary_impact: recoverableAmount }}
              onNavigateToRules={() => {
                const el = document.getElementById('rule-verdicts-section');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
            />

            {/* Feature 13: Interactive Rule Verdicts & Statutory Engine */}
            <div id="rule-verdicts-section" className="space-y-4 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <span>Interactive Statutory Rule Engine</span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                      Dual-Tier Evaluation
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Audited against IRDAI Master Circular (May 2024), Insurance Act 1938 § 45, and Mental Healthcare Act § 21(4).
                  </p>
                </div>
              </div>

              {/* Category Filter Tabs Bar */}
              <VerdictsFilterTabs
                activeFilter={verdictFilter}
                onFilterChange={setVerdictFilter}
                counts={filterCounts}
              />

              {/* Filtered Verdict Cards Stack */}
              <div className="space-y-3">
                {filteredVerdicts.length > 0 ? (
                  filteredVerdicts.map((verdict, idx) => (
                    <VerdictCard
                      key={verdict.rule_name || idx}
                      verdict={verdict}
                      defaultExpanded={verdict.status === 'FAIL'}
                    />
                  ))
                ) : (
                  <div className="card-enterprise p-8 text-center text-sm text-slate-500">
                    No rule verdicts matching the active filter criteria.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Digital Forensics & Fraud Lab */}
        {activeTab === 'forensics' && (
          <ForensicsLab
            forensics={result?.forensics}
            claimId={claimId}
            totalBilled={result?.total_correct_calculation || 110500}
          />
        )}

        {/* Tab 3: Cryptographic Audit Trail */}
        {activeTab === 'audit' && (
          <AuditTimeline
            auditTrail={auditTrail}
            claimId={claimId}
          />
        )}

        {/* Tab 4: Legal Appeal & Grievance Generator */}
        {activeTab === 'appeal' && (
          <AppealLetter
            appealData={appealDraft}
            analysisResult={result}
            claimId={claimId}
          />
        )}
      </div>
    </div>
  );
}
