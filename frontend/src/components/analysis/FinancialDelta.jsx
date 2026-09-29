/**
 * src/components/analysis/FinancialDelta.jsx
 * Enterprise Financial Delta & Statutory Reconciliation Component
 * Feature 12: Executive Financial Delta & Reconciliation
 * Compliant with IRDAI Master Circular May 2024 & Insurance Act 1938 § 45
 */

import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  ShieldAlert,
  Scale,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

// Format currency in Indian Rupees with full precision
export const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
};

// Aliased export for compatibility
export const formatINR = formatInr;

// Compact INR format (e.g., ₹42.5K, ₹1.24L)
export const formatCompactInr = (amount) => {
  const num = Number(amount) || 0;
  const abs = Math.abs(num);
  const prefix = num < 0 ? '-₹' : '₹';
  if (abs >= 10000000) return `${prefix}${(abs / 10000000).toFixed(2)}Cr`;
  if (abs >= 100000) return `${prefix}${(abs / 100000).toFixed(2)}L`;
  if (abs >= 1000) return `${prefix}${(abs / 1000).toFixed(1)}K`;
  return `${prefix}${abs}`;
};

export default function FinancialDelta({
  result = {},
  claim = null,
  onNavigateToRules = () => {},
  className = '',
}) {
  // 1. Financial Reconciliations & Normalizations (Backend Authoritative)
  const insurerPaid = Number(result?.total_insurer_calculation ?? 0);
  const recoverableAmount = Number(result?.total_monetary_impact ?? 0);
  const correctAllowable = Number(result?.total_correct_calculation ?? 0);
  const billedAmount = Number(result?.billed_amount ?? 0);

  const totalDisallowed = Number(result?.total_disallowed ?? 0);
  const legitimateDeduction = Number(result?.legitimate_deduction ?? 0);

  const safeTotal = billedAmount > 0 ? billedAmount : 1;
  const approvedPct = Number(result?.approved_pct ?? 0);
  const recoverablePct = Number(result?.recoverable_pct ?? 0);
  const legitimatePct = Number(result?.legitimate_pct ?? 0);

  const recoveryYield = result?.recovery_yield ?? '0.0';

  // Hover state for stacked bar segments: 'approved' | 'recoverable' | 'patient' | null
  const [activeSegment, setActiveSegment] = useState(null);

  // Extract fail verdicts for dynamic discrepancy breakdown
  const failVerdicts = (result.rule_verdicts || []).filter((v) => v.status === 'FAIL');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 1. Top Executive KPI 4-Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Billed Amount */}
        <div className="card-enterprise p-5 relative overflow-hidden group hover:border-slate-300">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <span>Total Billed Amount</span>
                <span className="text-[10px] text-slate-400 font-mono">(Gross)</span>
              </div>
              <div className="text-2xl lg:text-3xl font-bold text-slate-900 font-financial">
                {formatInr(billedAmount)}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-100 text-slate-600 border border-slate-200 group-hover:scale-105 transition-transform">
              <Scale className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Gross Hospital Invoice</span>
            <span className="font-semibold text-slate-700">100% Benchmark Base</span>
          </div>
        </div>

        {/* Metric 2: Insurer Approved Amount */}
        <div className="card-enterprise p-5 relative overflow-hidden group hover:border-sky-300">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs font-semibold text-sky-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <span>Insurer Approved</span>
                <span className="text-[10px] text-sky-500 font-mono">(Sanctioned)</span>
              </div>
              <div className="text-2xl lg:text-3xl font-bold text-sky-900 font-financial">
                {formatInr(insurerPaid)}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-sky-50 text-sky-600 border border-sky-200 group-hover:scale-105 transition-transform">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Initial Settlement Voucher</span>
            <span className="font-semibold text-sky-700">{approvedPct.toFixed(1)}% of Bill</span>
          </div>
        </div>

        {/* Metric 3: Total Disallowed Deductions */}
        <div className="card-enterprise p-5 relative overflow-hidden group hover:border-rose-300">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs font-semibold text-rose-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <span>Total Disallowed</span>
                <span className="text-[10px] text-rose-500 font-mono">(Haircut)</span>
              </div>
              <div className="text-2xl lg:text-3xl font-bold text-rose-700 font-financial">
                {formatInr(totalDisallowed)}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-rose-50 text-rose-600 border border-rose-200 group-hover:scale-105 transition-transform">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Aggregate Deductions</span>
            <span className="font-semibold text-rose-700">{((totalDisallowed / safeTotal) * 100).toFixed(1)}% Disallowance</span>
          </div>
        </div>

        {/* Metric 4: Contested & Recoverable (Hero Metric) */}
        <div className="card-enterprise p-5 relative overflow-hidden border-emerald-300 bg-gradient-to-br from-white via-emerald-50/40 to-teal-50/60 shadow-md group">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                  Contested & Recoverable
                </span>
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-extrabold bg-emerald-600 text-white shadow-xs">
                  IRDAI
                </span>
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-emerald-700 font-financial">
                {formatInr(recoverableAmount)}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-100 text-emerald-700 border border-emerald-200 shadow-xs group-hover:scale-105 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-emerald-100 flex items-center justify-between text-xs">
            <span className="text-emerald-800 font-medium">Recovery Yield Potential</span>
            <span className="font-extrabold text-emerald-700">+{recoveryYield}% over Insurer</span>
          </div>
        </div>
      </div>

      {/* 2. Visual Stacked Proportion Bar (Capital Allocation Waterfall) */}
      <div className="card-enterprise p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>Settlement Capital Allocation Waterfall</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                Audited Net: {formatInr(correctAllowable)}
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Proportional distribution of the {formatInr(billedAmount)} hospital invoice across settlement categories.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 self-start">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Target Rightful Settlement: <strong className="text-slate-900">{((correctAllowable / safeTotal) * 100).toFixed(1)}%</strong></span>
          </div>
        </div>

        {/* Stacked Segmented Bar */}
        <div className="space-y-2">
          <div className="h-8 w-full bg-slate-100 rounded-xl overflow-hidden flex shadow-inner-subtle p-0.5 border border-slate-200 relative">
            {/* Segment 1: Insurer Approved */}
            <div
              style={{ width: `${approvedPct}%` }}
              onMouseEnter={() => setActiveSegment('approved')}
              onMouseLeave={() => setActiveSegment(null)}
              className="h-full bg-sky-600 hover:bg-sky-500 transition-all cursor-pointer rounded-l-lg relative group flex items-center justify-center text-[11px] font-bold text-white tracking-wide"
              title={`Insurer Approved: ${formatInr(insurerPaid)} (${approvedPct.toFixed(1)}%)`}
            >
              {approvedPct > 15 && <span>{approvedPct.toFixed(0)}% Approved</span>}
            </div>

            {/* Segment 2: Contested & Recoverable */}
            <div
              style={{ width: `${recoverablePct}%` }}
              onMouseEnter={() => setActiveSegment('recoverable')}
              onMouseLeave={() => setActiveSegment(null)}
              className="h-full bg-emerald-500 hover:bg-emerald-400 transition-all cursor-pointer relative group flex items-center justify-center text-[11px] font-bold text-white tracking-wide shadow-sm"
              title={`Contested & Recoverable: ${formatInr(recoverableAmount)} (${recoverablePct.toFixed(1)}%)`}
            >
              {recoverablePct > 12 && <span>{recoverablePct.toFixed(0)}% Recoverable</span>}
            </div>

            {/* Segment 3: Legitimate / Patient Share */}
            <div
              style={{ width: `${legitimatePct}%` }}
              onMouseEnter={() => setActiveSegment('patient')}
              onMouseLeave={() => setActiveSegment(null)}
              className="h-full bg-slate-300 hover:bg-slate-400 transition-all cursor-pointer rounded-r-lg relative group flex items-center justify-center text-[11px] font-bold text-slate-700 tracking-wide"
              title={`Legitimate Deductibles / Co-pay: ${formatInr(legitimateDeduction)} (${legitimatePct.toFixed(1)}%)`}
            >
              {legitimatePct > 10 && <span>{legitimatePct.toFixed(0)}% Deductible</span>}
            </div>
          </div>

          {/* Interactive Legend & Subtotals */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {/* Legend Item 1: Insurer Approved */}
            <div
              className={`p-3 rounded-lg border transition-all cursor-pointer ${
                activeSegment === 'approved'
                  ? 'bg-sky-50 border-sky-300 shadow-xs ring-1 ring-sky-300'
                  : 'bg-slate-50/70 border-slate-200 hover:border-slate-300'
              }`}
              onClick={() => setActiveSegment(activeSegment === 'approved' ? null : 'approved')}
            >
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-sky-600 flex-shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Insurer Approved</span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="text-base font-bold text-slate-900 font-financial">{formatInr(insurerPaid)}</span>
                <span className="text-xs font-semibold text-sky-700">{approvedPct.toFixed(1)}%</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Sanctioned via initial settlement voucher</div>
            </div>

            {/* Legend Item 2: Contested & Recoverable */}
            <div
              className={`p-3 rounded-lg border transition-all cursor-pointer ${
                activeSegment === 'recoverable'
                  ? 'bg-emerald-50 border-emerald-300 shadow-xs ring-1 ring-emerald-300'
                  : 'bg-emerald-50/40 border-emerald-200 hover:border-emerald-300'
              }`}
              onClick={() => setActiveSegment(activeSegment === 'recoverable' ? null : 'recoverable')}
            >
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500 flex-shrink-0" />
                <span className="text-xs font-bold text-emerald-900">Contested & Recoverable</span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="text-base font-extrabold text-emerald-700 font-financial">{formatInr(recoverableAmount)}</span>
                <span className="text-xs font-bold text-emerald-800">{recoverablePct.toFixed(1)}%</span>
              </div>
              <div className="text-[11px] text-emerald-700 mt-0.5">Statutory conflicts backed by IRDAI Master Circular</div>
            </div>

            {/* Legend Item 3: Conforming Patient Share */}
            <div
              className={`p-3 rounded-lg border transition-all cursor-pointer ${
                activeSegment === 'patient'
                  ? 'bg-slate-100 border-slate-300 shadow-xs ring-1 ring-slate-300'
                  : 'bg-slate-50/70 border-slate-200 hover:border-slate-300'
              }`}
              onClick={() => setActiveSegment(activeSegment === 'patient' ? null : 'patient')}
            >
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-slate-400 flex-shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Conforming Patient Share</span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="text-base font-bold text-slate-900 font-financial">{formatInr(legitimateDeduction)}</span>
                <span className="text-xs font-semibold text-slate-600">{legitimatePct.toFixed(1)}%</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Legitimate Co-pay & Non-medical List I exclusions</div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Itemized Discrepancy Breakdown Cards with IRDAI Statutory Citations */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Itemized Statutory Discrepancy Breakdown</span>
          </h3>
          <span className="text-xs text-slate-500 font-medium">
            {failVerdicts.length} actionable conflicts identified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {failVerdicts.length > 0 ? (
            failVerdicts.map((v, i) => (
              <div
                key={v.rule_name || i}
                className="card-enterprise p-5 border-l-4 border-l-rose-500 flex flex-col justify-between hover:shadow-card-hover transition-shadow"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                      Tier 1 Statutory Conflict
                    </span>
                    <span className="text-sm font-extrabold text-rose-600 font-financial">
                      +{formatInr(v.monetary_impact || 0)}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 mt-2">
                    {v.rule_name}
                  </h4>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed line-clamp-3">
                    {v.finding}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-600 font-medium truncate max-w-[280px]">
                    <Scale className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" />
                    <span className="truncate">{v.regulatory_citation || 'IRDAI Master Circular May 2024'}</span>
                  </div>
                  <button
                    type="button"
                    onClick={onNavigateToRules}
                    className="text-xs font-bold text-brand-600 hover:text-brand-800 flex items-center gap-1 transition-colors flex-shrink-0"
                  >
                    Inspect <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-1 md:col-span-2 card-enterprise p-6 text-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-slate-900">No Statutory Conflicts Detected</h4>
              <p className="text-xs text-slate-500 mt-1">
                The settlement complies with IRDAI guidelines and policy conditions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
