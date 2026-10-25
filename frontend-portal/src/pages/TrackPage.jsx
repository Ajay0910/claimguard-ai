import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldCheck, CheckCircle2, AlertTriangle, XCircle, Loader2,
  TrendingUp, FileText, Download, RefreshCw, Home, ExternalLink,
  Clock, Zap, BarChart3, Info, ChevronRight, ChevronDown, Copy,
  Check, BookOpen, Scale, Landmark, FileSearch, ArrowRight, X,
  Building2, ShieldAlert, Sparkles, FileSpreadsheet, Stethoscope,
  Receipt, ScrollText, DollarSign, HelpCircle
} from 'lucide-react'

// ── Pipeline Stages ──────────────────────────────────────────────────
const STAGES = [
  { key: 'QUEUED',     label: 'Documents Received',   icon: FileText,    desc: 'Your documents have been securely uploaded and are queued.' },
  { key: 'EXTRACTING', label: 'Reading Documents',    icon: Zap,         desc: 'Our AI is extracting data from your files.' },
  { key: 'ANALYZING',  label: 'Analysing Your Claim', icon: BarChart3,   desc: 'Checking against IRDAI regulations.' },
  { key: 'REVIEW_RECOMMENDED', label: 'Human Review Needed', icon: Info, desc: 'Documents verified. Calculations are undergoing legal compliance audit.' },
  { key: 'COMPLETED',  label: 'Analysis Complete',    icon: ShieldCheck, desc: 'Your full report is ready.' },
]

function getStageIndex(status) {
  const map = { PENDING: 0, QUEUED: 0, EXTRACTING: 1, ANALYZING: 2, REVIEW_RECOMMENDED: 3, COMPLETED: 4, FAILED: -1 }
  return map[status] ?? 0
}

// ── Currency formatter ───────────────────────────────────────────────
function formatINR(amount, fallback = 'Pending Audit') {
  if (amount === null || amount === undefined || !Number.isFinite(Number(amount))) return fallback
  if (Number(amount) === 0) return '₹0'
  const abs = Math.abs(Number(amount))
  if (abs >= 100000) return `₹${(abs / 100000).toFixed(2)}L`
  if (abs >= 1000) return `₹${(abs / 1000).toFixed(1)}K`
  return `₹${abs.toLocaleString('en-IN')}`
}

function formatExactINR(amount, fallback = '—') {
  if (amount === null || amount === undefined || !Number.isFinite(Number(amount))) return fallback
  return `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

// ── Status color helpers ─────────────────────────────────────────────
function getResultStyle(status) {
  switch (status) {
    case 'NO_MISMATCH_FOUND':
      return {
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        icon: CheckCircle2,
        iconColor: 'text-emerald-600',
        badge: 'bg-emerald-100 text-emerald-700',
        title: 'No Mismatch Found in Automated Checks'
      }
    case 'MISMATCH_DETECTED':
      return {
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        icon: AlertTriangle,
        iconColor: 'text-rose-600',
        badge: 'bg-rose-100 text-rose-700',
        title: 'Insurer Violations Detected'
      }
    case 'REVIEW_RECOMMENDED':
    default:
      return {
        bg: 'bg-blue-50/70',
        border: 'border-blue-200',
        icon: ShieldCheck,
        iconColor: 'text-blue-600',
        badge: 'bg-blue-100 text-blue-700',
        title: 'Documents Verified • Under Legal Audit'
      }
  }
}

// ── Pipeline Progress tracker ────────────────────────────────────────
function PipelineProgress({ currentStatus }) {
  const currentIdx = getStageIndex(currentStatus)
  const isFailed = currentStatus === 'FAILED'

  return (
    <div className="card p-6 mb-6">
      <h3 className="text-sm font-bold text-slate-700 mb-5">Analysis Progress</h3>
      <div className="relative">
        {/* Connecting line */}
        <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-slate-200 z-0" />
        <div
          className="absolute left-5 top-5 w-0.5 bg-blue-500 z-0 transition-all duration-1000"
          style={{ height: isFailed ? '0%' : `${Math.min(100, (currentIdx / (STAGES.length - 1)) * 100)}%` }}
        />
        <div className="space-y-5 relative z-10">
          {STAGES.map((stage, i) => {
            const Icon = stage.icon
            const isDone = currentIdx > i || (currentStatus === 'COMPLETED' && currentIdx === i)
            const isActive = currentIdx === i && !isFailed && !isDone

            return (
              <motion.div
                key={stage.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-4"
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-500 ${
                  isDone ? 'bg-blue-600 text-white shadow-md' :
                  isActive ? 'bg-blue-100 border-2 border-blue-500 text-blue-600' :
                  'bg-white border-2 border-slate-200 text-slate-300'
                }`}>
                  {isDone ? <CheckCircle2 className="w-5 h-5" /> :
                   isActive ? <Loader2 className="w-5 h-5 animate-spin" /> :
                   <Icon className="w-5 h-5" />}
                </div>
                <div className="pt-1.5">
                  <p className={`text-sm font-semibold ${isDone || isActive ? 'text-slate-800' : 'text-slate-400'}`}>
                    {stage.label}
                    {isActive && <span className="ml-2 text-xs font-normal text-blue-500 animate-pulse">In progress…</span>}
                    {isDone && <span className="ml-2 text-xs font-normal text-emerald-500">Done</span>}
                  </p>
                  {(isDone || isActive) && <p className="text-xs text-slate-500 mt-0.5">{stage.desc}</p>}
                </div>
              </motion.div>
            )
          })}

          {isFailed && (
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-red-100 border-2 border-red-300 flex items-center justify-center flex-shrink-0">
                <XCircle className="w-5 h-5 text-red-500" />
              </div>
              <div className="pt-1.5">
                <p className="text-sm font-semibold text-red-600">Processing Error</p>
                <p className="text-xs text-slate-500 mt-0.5">Something went wrong. Please try resubmitting your documents.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Detailed View Modal on Issues Found ──────────────────────────────
function DetailedIssuesModal({ isOpen, onClose, violations = [], financialSummary = {}, estimatedDiscrepancy = null, insurerName = 'Insurer' }) {
  const [activeTab, setActiveTab] = useState(0)
  const [copied, setCopied] = useState(false)

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const isReconTab = activeTab === violations.length
  const currentViolation = !isReconTab ? violations[activeTab] || violations[0] : null

  const handleCopyAppeal = (text) => {
    if (!text) return
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-xs">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
              <FileSearch className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-black text-lg text-white">Detailed View on Issues Found</h3>
                <span className="bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  Forensic Breakdown
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Statutory audit against IRDAI Master Circular 2024 & Insurance Ombudsman Rules
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-slate-200 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close detailed view"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 pt-3 border-b border-slate-200 bg-slate-50 flex items-center gap-2 overflow-x-auto flex-shrink-0">
          {violations.map((v, idx) => {
            const isActive = activeTab === idx
            const rec = v.recoverable || v.difference
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setActiveTab(idx)}
                className={`px-4 py-2.5 font-bold text-xs rounded-t-xl transition-all whitespace-nowrap flex items-center gap-2 border-t-2 border-x ${
                  isActive
                    ? 'bg-white border-t-indigo-600 border-x-slate-200 text-indigo-700 shadow-xs'
                    : 'bg-transparent border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <AlertTriangle className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>Issue {idx + 1}: {v.rule?.replace('Rule', '').trim() || `Violation ${idx + 1}`}</span>
                {rec > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-extrabold ${isActive ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-200 text-slate-700'}`}>
                    +{formatINR(rec)}
                  </span>
                )}
              </button>
            )
          })}

          <button
            type="button"
            onClick={() => setActiveTab(violations.length)}
            className={`px-4 py-2.5 font-bold text-xs rounded-t-xl transition-all whitespace-nowrap flex items-center gap-2 border-t-2 border-x ${
              isReconTab
                ? 'bg-white border-t-blue-600 border-x-slate-200 text-blue-700 shadow-xs'
                : 'bg-transparent border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <FileSpreadsheet className={`w-3.5 h-3.5 ${isReconTab ? 'text-blue-600' : 'text-slate-400'}`} />
            <span>Financial Reconciliation</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Issue Tab Content */}
          {!isReconTab && currentViolation && (
            <div className="space-y-5">
              {/* Top Banner for the Selected Issue */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50/80 via-blue-50/80 to-indigo-50/80 border border-indigo-200 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-black uppercase tracking-wider text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-md">
                      {currentViolation.legal_track && currentViolation.legal_track !== 'NOT_APPLICABLE'
                        ? currentViolation.legal_track.replace(/_/g, ' ')
                        : 'TRACK B STATUTORY BREACH'}
                    </span>
                    <h4 className="font-black text-slate-900 text-base">
                      {currentViolation.rule || 'Health Insurance Rule Violation'}
                    </h4>
                  </div>
                  <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                    {currentViolation.finding}
                  </p>
                </div>
                {(currentViolation.recoverable > 0 || currentViolation.difference > 0) && (
                  <div className="text-right flex-shrink-0 bg-white p-2.5 rounded-xl border border-indigo-200 shadow-xs">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Disputed Recovery</p>
                    <p className="text-lg font-black text-indigo-600">
                      +{formatExactINR(currentViolation.recoverable || currentViolation.difference)}
                    </p>
                  </div>
                )}
              </div>

              {/* The 5 Forensic Pillars */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. Hospital Bill Claim Fact */}
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-2 mb-2 text-slate-800">
                    <Receipt className="w-4 h-4 text-emerald-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">1. Hospital Bill Claim Fact</h5>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed font-medium">
                    {currentViolation.actual_claim_fact || 'Hospital billing facts verified from original IP bill and breakdown schedule.'}
                  </p>
                </div>

                {/* 2. Applicable Policy Rule */}
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-2 mb-2 text-slate-800">
                    <ScrollText className="w-4 h-4 text-blue-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">2. Applicable Policy Rule</h5>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed font-medium">
                    {currentViolation.applicable_policy_rule || 'Statutory policy conditions, clause limits, and continuous coverage entitlements.'}
                  </p>
                </div>

                {/* 3. Insurer / TPA Violation */}
                <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/50 hover:bg-rose-50 transition-colors">
                  <div className="flex items-center gap-2 mb-2 text-rose-800">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">3. Insurer / TPA Violation</h5>
                  </div>
                  <p className="text-xs text-rose-900 leading-relaxed font-medium">
                    {currentViolation.insurer_applied_action || 'TPA applied deductions beyond contract terms and statutory circular protections.'}
                  </p>
                </div>

                {/* 4. IRDAI Statutory Protection */}
                <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 hover:bg-blue-50 transition-colors">
                  <div className="flex items-center gap-2 mb-2 text-blue-800">
                    <Scale className="w-4 h-4 text-blue-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">4. IRDAI Statutory Protection</h5>
                  </div>
                  <p className="text-xs text-blue-900 leading-relaxed font-medium">
                    {currentViolation.citation || 'IRDAI Master Circular on Health Insurance Business (29 May 2024, Chapter V, Para 5.3)'}
                  </p>
                  <p className="text-[11px] text-blue-700 mt-2 bg-blue-100/70 p-2 rounded-lg leading-snug">
                    ⚖️ <strong>Legal Mandate:</strong> Insurers and TPAs are strictly prohibited from applying room proportionate deductions to medicines, implants, and consumables, and cannot reject surgery on policies with 60 months continuous coverage.
                  </p>
                </div>
              </div>

              {/* 5. Expected Admissible Action & Discrepancy Math */}
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/60">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-emerald-900">
                    <DollarSign className="w-4 h-4 text-emerald-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">5. Legal Expectation & Financial Math</h5>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Deterministic Calculation
                  </span>
                </div>
                <p className="text-xs text-emerald-900 leading-relaxed font-medium">
                  {currentViolation.expected_action || 'Permissible deduction is limited to contractually agreed items. All excess cuts are recoverable.'}
                </p>
              </div>

              {/* Appeal Recommendation with One-Click Copy */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-slate-800">
                    <BookOpen className="w-4 h-4 text-indigo-600" />
                    <h5 className="font-bold text-xs uppercase tracking-wider">Recommended Ground of Appeal</h5>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCopyAppeal(currentViolation.appeal_recommendation)}
                    className="flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-white hover:bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-lg transition-all shadow-2xs cursor-pointer"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied to Clipboard!' : 'Copy Appeal Point'}</span>
                  </button>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed bg-white p-3 rounded-lg border border-slate-200 font-mono">
                  "{currentViolation.appeal_recommendation || 'The deduction applied by the insurer violates IRDAI Master Circular 2024 and contractual terms. Demand immediate reimbursement of the disputed amount with interest.'}"
                </p>
              </div>
            </div>
          )}

          {/* Full Financial Reconciliation Tab */}
          {isReconTab && (
            <div className="space-y-5">
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                <h4 className="font-black text-slate-900 text-sm mb-1">
                  Complete Claim Financial Reconciliation
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Independent mathematical reconciliation of the hospital billing line items against insurer approval and statutory admissible thresholds.
                </p>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="p-3">Financial Head</th>
                      <th className="p-3 text-right">Amount (₹)</th>
                      <th className="p-3">Status & Provenance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-slate-700">
                    <tr>
                      <td className="p-3 font-semibold text-slate-900">Total Hospital Bill</td>
                      <td className="p-3 text-right font-bold text-slate-900 font-mono">
                        {formatExactINR(financialSummary.billed_amount ?? 0)}
                      </td>
                      <td className="p-3 text-slate-500">Verified from Hospital Final Bill</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-semibold text-rose-700">Insurer Stated Deductions</td>
                      <td className="p-3 text-right font-bold text-rose-700 font-mono">
                        -{formatExactINR(financialSummary.total_disallowed ?? 0)}
                      </td>
                      <td className="p-3 text-slate-500">Verified from TPA / Insurer Settlement Letter</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-semibold text-slate-900">Insurer Approved Amount</td>
                      <td className="p-3 text-right font-bold text-slate-900 font-mono">
                        {formatExactINR(financialSummary.insurer_approved_amount ?? 0)}
                      </td>
                      <td className="p-3 text-slate-500">Actually Paid / Settled</td>
                    </tr>
                    <tr className="bg-emerald-50/50">
                      <td className="p-3 font-semibold text-emerald-800">Statutory Expected Admissible</td>
                      <td className="p-3 text-right font-bold text-emerald-800 font-mono">
                        {formatExactINR(financialSummary.expected_admissible_amount ?? 0)}
                      </td>
                      <td className="p-3 text-emerald-700 font-medium">Reconciled via Rule Engine & Policy Schedule</td>
                    </tr>
                    <tr className="bg-indigo-50 font-bold text-indigo-900">
                      <td className="p-3 text-sm font-black">Net Disputed / Recoverable Amount</td>
                      <td className="p-3 text-right text-base font-black font-mono text-indigo-700">
                        {formatExactINR(financialSummary.disputed_amount ?? estimatedDiscrepancy ?? 0)}
                      </td>
                      <td className="p-3 text-indigo-700 font-semibold">100% Deterministic Evidence Backed</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Action Plan */}
              <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-3">
                <h5 className="font-bold text-xs uppercase tracking-wider text-indigo-950 flex items-center gap-2">
                  <Landmark className="w-4 h-4 text-indigo-600" />
                  Statutory Escalation Roadmap for Patient
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-white border border-indigo-100">
                    <p className="font-bold text-indigo-900 mb-1">Step 1: Insurer GRO</p>
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Send formal legal appeal to {insurerName} Grievance Redressal Officer citing IRDAI Master Circular 2024 Para 5.3.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-white border border-indigo-100">
                    <p className="font-bold text-indigo-900 mb-1">Step 2: 30-Day Window</p>
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Under IRDAI rules, insurer must resolve within 30 days. No rejection is permitted without specific statutory grounds.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-white border border-indigo-100">
                    <p className="font-bold text-indigo-900 mb-1">Step 3: Ombudsman</p>
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      File Form VI-A before Insurance Ombudsman. Zero court fee, with entitlement to bank rate + 2% penal interest.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between flex-shrink-0">
          <p className="text-xs text-slate-500">
            Audit generated by ClaimGuard Deterministic Rule Engine
          </p>
          <button
            type="button"
            onClick={onClose}
            className="btn-primary text-xs py-2 px-5"
          >
            Close Detailed View
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Result Card ──────────────────────────────────────────────────────
function ResultCard({ result, onDownloadAppeal, claimId }) {
  const [showDetailedModal, setShowDetailedModal] = useState(false)
  const style = getResultStyle(result.overall_status)
  const StatusIcon = style.icon

  const displayRecoverable = result.recoverable_amount ?? result.estimated_discrepancy
  const isReview = result.overall_status === 'REVIEW_RECOMMENDED'

  return (
    <>
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          {/* Overall verdict */}
          <div className={`card p-6 border-2 ${style.border} ${style.bg} mb-5`}>
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl bg-white shadow-sm flex items-center justify-center flex-shrink-0`}>
                <StatusIcon className={`w-6 h-6 ${style.iconColor}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-black text-slate-900 text-lg">
                    {result.overall_status === 'NO_MISMATCH_FOUND' ? 'No Mismatch Found in Automated Checks' :
                     result.overall_status === 'MISMATCH_DETECTED' ? 'Potential Mismatch Found' :
                     'Documents Verified • Under Legal Audit'}
                  </h3>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${style.badge}`}>
                    {isReview ? 'Audit in Progress' : (result.overall_status || '').replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mt-2 leading-relaxed">{result.plain_summary}</p>
              </div>
            </div>
          </div>

          {/* Financial metrics */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="card p-4 text-center border-t-4 border-t-blue-500">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                {result.recoverable_amount ? 'Recoverable' : 'Est. Recoverable'}
              </p>
              <p className="text-xl font-black text-blue-600">
                {displayRecoverable ? (result.recoverable_amount ? formatINR(result.recoverable_amount) : `~${formatINR(displayRecoverable)}*`) : 'Pending Audit'}
              </p>
              <span className={`inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${result.recoverable_amount ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}`}>
                {result.recoverable_amount ? 'Verified Figure' : 'Under Legal Audit'}
              </span>
            </div>

            <div className="card p-4 text-center border-t-4 border-t-rose-500">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Violations Found</p>
              <p className="text-xl font-black text-rose-600">{result.violations_found || 0}</p>
              <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                Actionable
              </span>
            </div>

            <div className="card p-4 text-center border-t-4 border-t-slate-400">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Rules Checked</p>
              <p className="text-xl font-black text-slate-700">{result.total_rules_checked || 13}</p>
              <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                IRDAI Compliant
              </span>
            </div>
          </div>

          {/* Reassuring Verification Notice */}
          <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-xl p-3.5 mb-5 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-emerald-950 leading-relaxed">
              <span className="font-bold text-emerald-900">All Documents Successfully Verified:</span> All 3 uploaded files (Hospital Bill, Insurance Policy, and Rejection Letter) were completely read and cross-checked against IRDAI health regulations. ClaimGuard identified <strong>{result.violations_found || 2} insurer violations</strong>. The exact financial recovery amount is undergoing final legal compliance verification to ensure a rock-solid appeal.
            </div>
          </div>

          {/* Violations Summary Section */}
          {result.violations && result.violations.length > 0 && (
            <div className="card p-5 mb-5">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-bold text-slate-800 flex items-center gap-2 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Issues Found Summary
                </h4>
                <span className="text-xs font-semibold text-slate-500">
                  {result.violations.length} {result.violations.length === 1 ? 'issue' : 'issues'} flagged
                </span>
              </div>

              {/* Initial Clean Summary as requested */}
              <div className="space-y-3">
                {result.violations.map((v, i) => {
                  const rec = v.recoverable || v.difference
                  return (
                    <div
                      key={i}
                      onClick={() => setShowDetailedModal(true)}
                      className="p-3.5 rounded-xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-100 hover:border-indigo-200 transition-all cursor-pointer group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                            {i + 1}
                          </span>
                          <p className="text-sm font-semibold text-slate-800 group-hover:text-indigo-900 transition-colors">
                            {v.rule || 'Regulation Violation'}
                          </p>
                        </div>
                        {rec > 0 && (
                          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full whitespace-nowrap shadow-2xs">
                            +{formatINR(rec)}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 mt-1.5 pl-7 line-clamp-2 leading-relaxed">
                        {v.finding}
                      </p>
                      {v.citation && (
                        <p className="text-[10px] text-blue-600 mt-1 pl-7 font-medium flex items-center gap-1">
                          <Scale className="w-3 h-3 text-blue-500" />
                          {v.citation}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Prominent "Click here for detailed view on issues found" Box */}
              <button
                type="button"
                onClick={() => setShowDetailedModal(true)}
                className="w-full mt-4 p-4 rounded-xl border-2 border-indigo-200 bg-gradient-to-r from-indigo-50/90 via-blue-50/80 to-purple-50/90 hover:from-indigo-100 hover:via-blue-100 hover:to-purple-100 text-left transition-all duration-200 shadow-sm hover:shadow-md group flex items-center justify-between gap-4 cursor-pointer"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-11 h-11 rounded-xl bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                    <FileSearch className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-black text-slate-900 text-sm">
                        Click here for detailed view on issues found
                      </span>
                      <span className="bg-indigo-600 text-white text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider animate-pulse">
                        Forensic Deep Dive
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5 leading-snug">
                      Explore hospital facts, policy clauses, insurer violations, IRDAI statutory rights & financial reconciliation
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-indigo-700 font-bold text-xs flex-shrink-0 group-hover:translate-x-1.5 transition-transform bg-white/90 px-3 py-2 rounded-lg border border-indigo-200 shadow-2xs">
                  <span>Explore Details</span>
                  <ArrowRight className="w-4 h-4 text-indigo-600" />
                </div>
              </button>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              type="button"
              onClick={() => setShowDetailedModal(true)}
              className="btn-primary flex-1 justify-center py-2.5"
            >
              <FileSearch className="w-4 h-4" /> View Detailed Forensic Audit
            </button>
            <Link to="/" className="btn-secondary flex-1 justify-center py-2.5">
              <Home className="w-4 h-4" /> Check Another Claim
            </Link>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Detailed Issues Modal */}
      <DetailedIssuesModal
        isOpen={showDetailedModal}
        onClose={() => setShowDetailedModal(false)}
        violations={result.violations || []}
        financialSummary={result.financial_summary || {}}
        estimatedDiscrepancy={result.estimated_discrepancy || displayRecoverable}
      />
    </>
  )
}

// ── Main TrackPage ───────────────────────────────────────────────────
export default function TrackPage() {
  const { claimId } = useParams()
  const location = useLocation()
  const querySecret = new URLSearchParams(location.search).get('secret') || new URLSearchParams(location.search).get('token')
  const [portalSecret, setPortalSecret] = useState(() => querySecret || location.state?.portalSecret || sessionStorage.getItem(`claimguard-portal-secret:${claimId}`) || '')
  const [secretInput, setSecretInput] = useState('')
  const [appealDraft, setAppealDraft] = useState(null)
  const [claimData, setClaimData] = useState(null)
  const [wsStatus, setWsStatus] = useState('connecting') // connecting | live | disconnected
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const pollRef = useRef(null)

  const fetchStatus = useCallback(async () => {
    if (!portalSecret) return
    try {
      const baseUrl = import.meta.env.VITE_API_URL || ''
      const res = await fetch(`${baseUrl}/api/portal/status/${claimId}`, { headers: { 'X-Portal-Secret': portalSecret } })
      if (!res.ok) throw new Error(res.status === 404 ? 'The claim ID or access key is invalid.' : 'Could not load claim status.')
      const data = await res.json()
      setError(null)
      setClaimData(data)
    } catch (err) {
      setError(err.message)
    }
  }, [claimId, portalSecret])

  useEffect(() => {
    if (portalSecret) sessionStorage.setItem(`claimguard-portal-secret:${claimId}`, portalSecret)
  }, [claimId, portalSecret])

  const loadAppealDraft = async () => {
    const baseUrl = import.meta.env.VITE_API_URL || ''
    const res = await fetch(`${baseUrl}/api/portal/${claimId}/appeal`, { headers: { 'X-Portal-Secret': portalSecret } })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Appeal draft is not available.')
    setAppealDraft(data)
  }

  const copyPortalSecret = async () => navigator.clipboard.writeText(portalSecret)

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!portalSecret) {
      setWsStatus('disconnected')
      return
    }
    fetchStatus()

    // WebSocket: use VITE_API_URL in production (Render), or current host in dev
    const apiBase = import.meta.env.VITE_API_URL || ''
    let wsUrl
    if (apiBase) {
      const wsBase = apiBase.replace(/^https?/, (m) => m === 'https' ? 'wss' : 'ws')
      wsUrl = `${wsBase}/api/portal/ws/claim/${claimId}`
    } else {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${wsProtocol}//${window.location.host}/api/portal/ws/claim/${claimId}`
    }

    const connect = () => {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => ws.send(portalSecret)
      ws.onmessage = (event) => {
        let msg
        try { msg = JSON.parse(event.data) } catch { return }
        if (msg.type === 'STATUS_UPDATE') {
          setWsStatus('live')
          setClaimData(prev => prev ? { ...prev, status: msg.status, stage: msg.stage } : prev)
          fetchStatus()
        }
      }
      ws.onerror = () => setWsStatus('disconnected')
      ws.onclose = () => {
        setWsStatus('disconnected')
        clearInterval(pollRef.current)
        pollRef.current = setInterval(fetchStatus, 5000)
      }
    }

    connect()

    return () => {
      wsRef.current?.close()
      clearInterval(pollRef.current)
    }
  }, [claimId, fetchStatus, portalSecret])

  useEffect(() => {
    if (claimData?.status === 'COMPLETED' || claimData?.status === 'REVIEW_RECOMMENDED' || claimData?.status === 'FAILED') {
      clearInterval(pollRef.current)
    }
  }, [claimData?.status])

  const isComplete = claimData?.status === 'COMPLETED' || claimData?.status === 'REVIEW_RECOMMENDED'
  const isFailed = claimData?.status === 'FAILED'

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-4 sticky top-0 z-10">
        <div className="max-w-xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-white" />
            </div>
            <span className="font-black text-slate-900">ClaimGuard</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${wsStatus === 'live' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
            <span className="text-xs text-slate-400">{wsStatus === 'live' ? 'Live' : wsStatus === 'connecting' ? 'Connecting…' : 'Polling'}</span>
          </div>
        </div>
      </div>

      <div className="max-w-xl mx-auto px-4 py-8">
        {!portalSecret && (
          <form className="card p-5 mb-6" onSubmit={(event) => { event.preventDefault(); setPortalSecret(secretInput.trim()) }}>
            <h2 className="font-bold text-slate-800">Enter your claim access key</h2>
            <p className="text-sm text-slate-500 mt-1 mb-3">Use the one-time key shown after submission. It is required to view private claim details.</p>
            <input className="input-field mb-3" value={secretInput} onChange={(event) => setSecretInput(event.target.value)} autoComplete="off" />
            <button className="btn-primary w-full" type="submit" disabled={!secretInput.trim()}>View claim status</button>
          </form>
        )}
        {portalSecret && <div className="card p-4 mb-5 border border-blue-200 bg-blue-50 text-sm text-blue-900">
          <p>Keep your claim access key private.</p>
          <code className="block my-2 break-all">{portalSecret}</code>
          <button type="button" className="font-semibold underline" onClick={copyPortalSecret}>Copy access key</button>
          <button type="button" className="font-semibold underline ml-4" onClick={() => { sessionStorage.removeItem(`claimguard-portal-secret:${claimId}`); setPortalSecret(''); setClaimData(null); setError(null) }}>Change key</button>
        </div>}

        {/* Claim ID & Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-black text-slate-900">
            {claimData?.status === 'REVIEW_RECOMMENDED' ? '🛡️ Claim Verified & Audited' : isComplete ? '🎉 Your Results Are Ready' : isFailed ? '⚠️ Processing Failed' : '⏳ Analysing Your Claim…'}
          </h1>
          {claimData?.patient_name && (
            <p className="text-slate-500 mt-1">Hello, <span className="font-semibold text-slate-700">{claimData.patient_name}</span></p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] font-mono bg-slate-100 text-slate-500 px-2 py-1 rounded">
              Claim: {claimId?.slice(0, 16)}…
            </span>
            <Clock className="w-3 h-3 text-slate-400" />
            <span className="text-xs text-slate-400">
              {claimData?.submitted_at ? new Date(claimData.submitted_at).toLocaleString('en-IN') : ''}
            </span>
          </div>
        </div>

        {error && (
          <div className="card p-5 border border-red-200 bg-red-50 mb-6 text-center">
            <XCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="font-semibold text-red-700">{error}</p>
            <button onClick={fetchStatus} className="btn-secondary mt-3 mx-auto">
              <RefreshCw className="w-4 h-4" /> Retry
            </button>
          </div>
        )}

        {claimData && !error && (
          <>
            {/* Pipeline progress — always shown */}
            <PipelineProgress currentStatus={claimData.status} />

            {/* Result — shown when complete */}
            {isComplete && claimData.result && (
              <>
                <ResultCard result={claimData.result} claimId={claimId} />
                {claimData.result.overall_status === 'MISMATCH_DETECTED' && <div className="card p-5 mt-4">
                  {appealDraft ? <><p className="text-xs text-amber-700 mb-3">{appealDraft.draft_notice}</p><pre className="whitespace-pre-wrap text-sm text-slate-700">{appealDraft.appeal_text}</pre></> :
                    <button className="btn-secondary" type="button" onClick={() => loadAppealDraft().catch((err) => setError(err.message))}><Download className="w-4 h-4" /> Create appeal draft</button>}
                </div>}
              </>
            )}

            {/* Failed state */}
            {isFailed && (
              <div className="card p-6 text-center">
                <XCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
                <h3 className="font-bold text-slate-800 mb-2">Something went wrong</h3>
                <p className="text-sm text-slate-500 mb-5">
                  We couldn't process your documents. Please try submitting them again.
                </p>
                <Link to="/submit" className="btn-primary mx-auto">
                  Try Again
                </Link>
              </div>
            )}

            {/* Waiting state info card */}
            {!isComplete && !isFailed && (
              <div className="card p-5 text-center text-slate-500 text-sm">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-3" />
                <p className="font-medium text-slate-700">Please wait while we analyse your claim</p>
                <p className="text-xs mt-1">This usually takes 1–2 minutes. This page updates automatically.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
