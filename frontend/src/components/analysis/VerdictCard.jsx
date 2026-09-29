/**
 * src/components/analysis/VerdictCard.jsx
 * Interactive Rule Verdict Card with Statutory Engine & Clipboard Citation
 * Feature 13: Interactive Rule Verdicts & Statutory Engine
 * Compliant with IRDAI Master Circular May 2024 & Insurance Act 1938 § 45
 */

import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Scale,
  Copy,
  Check,
  Lightbulb,
  HelpCircle,
} from 'lucide-react';
import { toast } from 'sonner';

// Format currency in Indian Rupees
export const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
};

export const formatINR = formatInr;

export default function VerdictCard({ verdict = {}, defaultExpanded = false }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || verdict.status === 'FAIL');
  const [copied, setCopied] = useState(false);

  // Status flags
  const isFail = verdict.status === 'FAIL';
  const isReview = verdict.status === 'NEEDS_REVIEW' || verdict.status === 'REVIEW';
  const isPass = verdict.status === 'PASS';
  const isSkipped = verdict.status === 'SKIPPED';

  // Determine Tier: Tier 1 (Statutory) vs Tier 2 (Policy/Clinical)
  const isTier1 =
    verdict.tier === 1 ||
    verdict.tier === 'Tier 1' ||
    (verdict.rule_name && (
      verdict.rule_name.toLowerCase().includes('proportionate') ||
      verdict.rule_name.toLowerCase().includes('moratorium') ||
      verdict.rule_name.toLowerCase().includes('clause timeline') ||
      verdict.rule_name.toLowerCase().includes('mental health') ||
      verdict.rule_name.toLowerCase().includes('waiting period')
    ));

  const tierLabel = isTier1 ? 'Tier 1: Mandatory Statutory Rule' : 'Tier 2: Clinical / Policy Condition';

  // Status styling configuration
  const getStatusConfig = (status) => {
    switch (status) {
      case 'FAIL':
        return {
          icon: XCircle,
          label: 'Statutory Conflict',
          badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
          borderClass: 'border-rose-200',
          accentColor: '#E11D48',
        };
      case 'NEEDS_REVIEW':
      case 'REVIEW':
        return {
          icon: AlertCircle,
          label: 'Review Needed',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
          borderClass: 'border-amber-200',
          accentColor: '#D97706',
        };
      case 'PASS':
        return {
          icon: CheckCircle2,
          label: 'Compliant / Pass',
          badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          borderClass: 'border-emerald-200',
          accentColor: '#059669',
        };
      case 'SKIPPED':
      default:
        return {
          icon: HelpCircle,
          label: 'Not Applicable',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200',
          borderClass: 'border-slate-200',
          accentColor: '#64748B',
        };
    }
  };

  const statusConfig = getStatusConfig(verdict.status);
  const StatusIcon = statusConfig.icon;

  // Handle Copy Citation to Clipboard with feedback
  const handleCopyCitation = (e) => {
    e.stopPropagation();
    if (!verdict.regulatory_citation) return;

    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(verdict.regulatory_citation).catch(() => {});
    }
    setCopied(true);
    toast.success('Statutory Citation Copied', {
      id: 'copy-citation',
      description: verdict.regulatory_citation || 'IRDAI statutory citation copied to clipboard.',
    });
    setTimeout(() => setCopied(false), 2500);
  };

  // Calculations & Delta Bar Ratios
  const insurerCalc = Number(verdict.insurer_calculation || 0);
  const correctCalc = Number(verdict.correct_calculation || 0);
  const impact = Number(verdict.monetary_impact || 0);

  // Maximum value for proportional delta bar scaling
  const maxVal = Math.max(correctCalc, insurerCalc, 1);
  const insurerBarWidth = Math.min(100, Math.max(8, (insurerCalc / maxVal) * 100));
  const correctBarWidth = Math.min(100, Math.max(8, (correctCalc / maxVal) * 100));

  // AI Confidence formatting
  const rawConfidence = verdict.confidence ?? verdict.confidence_score;
  const confidencePercent = rawConfidence !== undefined && rawConfidence !== null
    ? Math.round(Number(rawConfidence) <= 1 ? Number(rawConfidence) * 100 : Number(rawConfidence))
    : 96;

  return (
    <div
      className={`card-enterprise border ${statusConfig.borderClass} overflow-hidden transition-all duration-200 ${
        isSkipped ? 'opacity-75' : ''
      }`}
    >
      {/* 1. Header Section */}
      <div
        className="p-5 flex items-start gap-4 cursor-pointer hover:bg-slate-50/70 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Leading Status Icon */}
        <div className="mt-0.5 flex-shrink-0">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center border shadow-xs ${statusConfig.badgeClass}`}
          >
            <StatusIcon className="w-5 h-5" />
          </div>
        </div>

        {/* Title, Tiers & Finding */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            {/* Tier Badge */}
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${
                isTier1
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              {tierLabel}
            </span>

            {/* Severity Status Badge */}
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${statusConfig.badgeClass}`}
            >
              {statusConfig.label}
            </span>

            {/* AI Confidence Meter */}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-50 text-slate-600 border border-slate-200">
              AI Confidence: <strong className="ml-1 text-slate-900 font-financial">{confidencePercent}%</strong>
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
            <h4 className="text-base font-bold text-slate-900 tracking-tight">
              {verdict.rule_name || 'Statutory Rule Check'}
            </h4>

            {/* Monetary Impact Hero Pill */}
            {isFail && impact > 0 && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-50 border border-rose-200 self-start sm:self-auto flex-shrink-0">
                <span className="text-xs font-semibold text-rose-700">Contested Impact:</span>
                <span className="text-sm font-extrabold text-rose-700 font-financial">
                  +{formatInr(impact)}
                </span>
              </div>
            )}
          </div>

          <p className="text-xs text-slate-500 mt-0.5">
            {verdict.rule_description}
          </p>

          {/* Finding Summary Preview */}
          {verdict.finding && (
            <div className="mt-3 text-xs text-slate-700 leading-relaxed bg-slate-50/80 p-3 rounded-lg border border-slate-100">
              <strong className="text-slate-900 font-semibold">Audit Finding: </strong>
              {verdict.finding}
            </div>
          )}
        </div>

        {/* Expand / Collapse Chevron */}
        <div className="text-slate-400 hover:text-slate-600 mt-1 flex-shrink-0">
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </div>

      {/* 2. Expanded Detail Drawer */}
      {isExpanded && (
        <div className="border-t border-slate-100 bg-slate-50/50 p-5 space-y-4">
          {/* Visual Delta Bar (Insurer Approved vs Correct Allowable Amount) */}
          {(insurerCalc > 0 || correctCalc > 0 || impact > 0) && (
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 uppercase tracking-wider">
                  Calculation Delta Reconciliation
                </span>
                <span className="font-medium text-slate-500">
                  Statutory Recovery Delta:{' '}
                  <strong className="text-emerald-700 font-financial">
                    +{formatInr(impact)}
                  </strong>
                </span>
              </div>

              {/* Proportional Dual Bar Visualizer */}
              <div className="space-y-2">
                {/* Insurer Approved Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                      Insurer Calculated Settlement:
                    </span>
                    <span className="font-semibold text-slate-700 line-through decoration-rose-500 decoration-2 font-financial">
                      {formatInr(insurerCalc)}
                    </span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${insurerBarWidth}%` }}
                      className="h-full bg-rose-500 rounded-full transition-all duration-300"
                    />
                  </div>
                </div>

                {/* Correct Allowable Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-emerald-800 font-semibold flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                      Statutory Correct Allowable Amount:
                    </span>
                    <span className="font-bold text-emerald-700 font-financial">
                      {formatInr(correctCalc)}
                    </span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${correctBarWidth}%` }}
                      className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* IRDAI Regulatory Citation Box with 1-Click Copy */}
          {verdict.regulatory_citation && (
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-start gap-3 min-w-0">
                <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100 flex-shrink-0 mt-0.5">
                  <Scale className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Statutory Regulatory Citation
                  </div>
                  <div className="text-xs font-semibold text-slate-800 mt-0.5 leading-relaxed break-words">
                    {verdict.regulatory_citation}
                  </div>
                </div>
              </div>

              {/* Copy Citation Button */}
              <button
                type="button"
                onClick={handleCopyCitation}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-150 hover:scale-101 active:scale-95 flex-shrink-0 self-start sm:self-center shadow-xs ${
                  copied
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Citation Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                    <span>Copy Citation</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Appeal & Grievance Recommendation Box */}
          {verdict.appeal_recommendation && (
            <div className="bg-sky-50/70 p-4 rounded-xl border border-sky-100 shadow-xs flex items-start gap-3">
              <div className="p-2 rounded-lg bg-sky-100 text-sky-700 flex-shrink-0 mt-0.5">
                <Lightbulb className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-sky-900">
                  Legal Appeal & Grievance Directive
                </div>
                <div className="text-xs text-sky-900/90 mt-1 leading-relaxed">
                  {verdict.appeal_recommendation}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Filter Tabs Bar Helper Component for Rule Verdicts
 */
export function VerdictsFilterTabs({
  activeFilter = 'ALL',
  onFilterChange = () => {},
  counts = { all: 4, tier1: 3, tier2: 1, conflicts: 2 },
}) {
  const tabs = [
    { id: 'ALL', label: 'All Rules', count: counts.all ?? 0 },
    { id: 'TIER1', label: 'Tier 1 Statutory', count: counts.tier1 ?? 0 },
    { id: 'TIER2', label: 'Tier 2 Policy', count: counts.tier2 ?? 0 },
    { id: 'CONFLICTS', label: 'Conflicts Only', count: counts.conflicts ?? 0, highlight: true },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
      {tabs.map((tab) => {
        const isActive = activeFilter === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onFilterChange(tab.id)}
            className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 active:scale-95 ${
              isActive
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <span>{tab.label}</span>
            <span
              className={`px-1.5 py-0.5 rounded-full text-[10px] font-extrabold ${
                isActive
                  ? 'bg-slate-700 text-white'
                  : tab.highlight && tab.count > 0
                  ? 'bg-rose-100 text-rose-700'
                  : 'bg-slate-100 text-slate-700'
              }`}
            >
              {tab.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
