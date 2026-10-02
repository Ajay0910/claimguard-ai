import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Activity,
  ArrowRight,
  Lock,
  Scale,
  FileSearch,
  Microscope,
  FileSpreadsheet,
  AlertOctagon,
  RotateCcw,
  Clock
} from 'lucide-react';

/**
 * Animated Checkmark with SVG pathLength stroke draw
 */
function AnimatedCheckmark({ isAttached, color = 'teal' }) {
  if (!isAttached) {
    return <XCircle className="w-4 h-4 text-slate-300 flex-shrink-0" />;
  }

  const strokeColor =
    color === 'teal' ? '#0d9488' : color === 'sky' ? '#0284c7' : '#d97706';

  return (
    <motion.div
      initial={{ scale: 0.6, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 500, damping: 25 }}
      className="flex items-center justify-center flex-shrink-0"
    >
      <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke={strokeColor}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" stroke={strokeColor} strokeWidth="2" />
        <motion.path
          d="m9 12 2 2 4-4"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.05 }}
        />
      </svg>
    </motion.div>
  );
}

export const EXTRACTION_STAGES = [
  {
    id: 1,
    title: 'Uploading & Hashing',
    subtitle: 'Streaming encrypted multipart chunks & computing SHA-256 block hash...',
    range: [0, 25]
  },
  {
    id: 2,
    title: 'Extracting OCR Tokens',
    subtitle: 'Scanning tabular line items, HSN/SAC codes & TPA deduction clauses...',
    range: [25, 60]
  },
  {
    id: 3,
    title: 'Verifying Clinical Schema',
    subtitle: 'Validating arithmetic totals, room-rent proportion limits & IRDAI schedules...',
    range: [60, 85]
  },
  {
    id: 4,
    title: 'Ready for Forensics',
    subtitle: 'Schema sealed. Forwarding payload to Rule Adjudication & Digital Forensics Lab.',
    range: [85, 100]
  }
];

export default function ReadinessCheck({
  documents = {},
  claimId = null,
  isAnalyzing = false,
  extractionStage = 0,
  extractionProgress = 0,
  onRunAudit,
  onClearAll
}) {
  const hasBill = Boolean(documents.HOSPITAL_BILL);
  const hasPolicy = Boolean(documents.INSURANCE_POLICY);
  const hasRejection = Boolean(documents.REJECTION_LETTER);

  const uploadedCount = [hasBill, hasPolicy, hasRejection].filter(Boolean).length;
  const canAnalyze = uploadedCount === 3;
  const readinessPercentage = Math.round((uploadedCount / 3) * 100);

  const checklistItems = [
    {
      title: 'Itemized Tariff & Line Items',
      desc: 'Room rent, nursing, OT, pharmacy, and consumables separation',
      ready: hasBill,
      icon: Scale,
    },
    {
      title: 'Statutory Policy Limits',
      desc: 'Sum insured, room rent capping, copay clause & waiting periods',
      ready: hasPolicy,
      icon: ShieldCheck,
    },
    {
      title: 'TPA Disallowance Grounds',
      desc: 'Deductions, exclusion citations & settlement dispute basis',
      ready: hasRejection,
      icon: FileSearch,
    },
    {
      title: 'Digital Forensics Pre-Scan (ELA)',
      desc: 'Pixel discontinuity, EXIF tampering & CGHS benchmark audit',
      ready: canAnalyze,
      icon: Microscope,
    }
  ];

  const currentStageInfo = EXTRACTION_STAGES[extractionStage] || EXTRACTION_STAGES[0];

  return (
    <div className="card-enterprise p-6 space-y-6 bg-white border-slate-200/90 shadow-card">
      {/* Header & Readiness Gauge */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-900 text-white shadow-2xs">
              <Activity className="w-4 h-4 text-teal-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Pre-Analysis Health Check</h3>
              <p className="text-[11px] text-slate-500">Automated intake validation</p>
            </div>
          </div>
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full border transition-colors ${
              canAnalyze
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : uploadedCount > 0
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            {uploadedCount}/3 Docs Attached ({readinessPercentage}%)
          </span>
        </div>

        {/* 3-Segment Progress Bar */}
        <div className="mt-3.5 w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex gap-1 p-0.5 border border-slate-200/80">
          <motion.div
            initial={false}
            animate={{
              backgroundColor: hasBill ? '#14b8a6' : '#e2e8f0',
              opacity: hasBill ? 1 : 0.35,
            }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
            className="h-full rounded-full flex-1"
          />
          <motion.div
            initial={false}
            animate={{
              backgroundColor: hasPolicy ? '#0ea5e9' : '#e2e8f0',
              opacity: hasPolicy ? 1 : 0.35,
            }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
            className="h-full rounded-full flex-1"
          />
          <motion.div
            initial={false}
            animate={{
              backgroundColor: hasRejection ? '#f59e0b' : '#e2e8f0',
              opacity: hasRejection ? 1 : 0.35,
            }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
            className="h-full rounded-full flex-1"
          />
        </div>
      </div>

      {/* Tripartite Intake Matrix Status */}
      <div className="space-y-2 bg-slate-50/70 p-3.5 rounded-xl border border-slate-200/80">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center justify-between">
          <span>Tripartite Verification Matrix</span>
          <span className="font-financial font-bold text-slate-700">{uploadedCount} of 3</span>
        </div>
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 text-slate-700">
              <AnimatedCheckmark isAttached={hasBill} color="teal" />
              Hospital Bill
            </span>
            <span className={`font-semibold font-financial ${hasBill ? 'text-teal-700' : 'text-slate-400'}`}>
              {hasBill ? 'Attached' : 'Missing'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 text-slate-700">
              <AnimatedCheckmark isAttached={hasPolicy} color="sky" />
              Insurance Policy
            </span>
            <span className={`font-semibold font-financial ${hasPolicy ? 'text-sky-700' : 'text-slate-400'}`}>
              {hasPolicy ? 'Attached' : 'Missing'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 text-slate-700">
              <AnimatedCheckmark isAttached={hasRejection} color="amber" />
              Rejection / Settlement Letter
            </span>
            <span className={`font-semibold font-financial ${hasRejection ? 'text-amber-700' : 'text-slate-400'}`}>
              {hasRejection ? 'Attached' : 'Missing'}
            </span>
          </div>
        </div>
      </div>

      {/* Forensic Inspection Capabilities Checklist */}
      <div className="space-y-3">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
          Forensic Inspection Scope
        </div>
        <div className="space-y-2.5">
          {checklistItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex items-start gap-2.5">
                <div
                  className={`p-1 rounded mt-0.5 transition-colors ${
                    item.ready ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-slate-800 flex items-center justify-between">
                    <span>{item.title}</span>
                    {item.ready ? (
                      <span className="text-[10px] font-bold text-emerald-600 uppercase">Ready</span>
                    ) : (
                      <span className="text-[10px] font-medium text-slate-400 uppercase">Gated</span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 leading-tight mt-0.5">
                    {item.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4-Stage Extraction Progress Animation Display */}
      {isAnalyzing && (
        <div className="p-4 rounded-xl bg-slate-900 text-white space-y-3 animate-in fade-in-50">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping inline-block" />
              <span>{currentStageInfo.title}</span>
            </span>
            <span className="font-financial font-bold text-teal-400 text-sm">
              {Math.round(extractionProgress)}%
            </span>
          </div>

          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-sky-500 via-teal-400 to-emerald-400 relative overflow-hidden"
              style={{ width: `${extractionProgress}%` }}
              initial={{ width: 0 }}
              animate={{ width: `${extractionProgress}%` }}
              transition={{ type: 'spring', damping: 22, stiffness: 120 }}
            >
              <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.4)_50%,transparent_100%)] animate-[shimmer_1.5s_infinite]" />
            </motion.div>
          </div>

          <p className="text-[11px] text-slate-400 font-mono italic leading-relaxed">
            {currentStageInfo.subtitle}
          </p>

          <div className="grid grid-cols-4 gap-1 pt-1">
            {EXTRACTION_STAGES.map((st, idx) => {
              const isPast = extractionStage > idx;
              const isCurr = extractionStage === idx;
              return (
                <div
                  key={st.id}
                  className={`h-1 rounded-full transition-colors ${
                    isPast ? 'bg-emerald-400' : isCurr ? 'bg-teal-400 animate-pulse' : 'bg-slate-700'
                  }`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Fast-Track 1-Click Apollo Hospital Benchmark Claim Loader */}
      <div className="pt-2 border-t border-slate-200/80">
          {uploadedCount > 0 && onClearAll && (
            <button
              type="button"
              onClick={onClearAll}
              disabled={isAnalyzing}
              title="Reset documents"
              className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors border border-slate-200 bg-white"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
      </div>

      {/* CTA Button & Session Info */}
      <div className="pt-2 border-t border-slate-200/80 space-y-3">
        <button
          type="button"
          onClick={onRunAudit}
          disabled={!canAnalyze || isAnalyzing}
          className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm shadow-md transition-all duration-200 flex items-center justify-center gap-2.5 relative overflow-hidden ${
            canAnalyze && !isAnalyzing
              ? 'bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-500 hover:to-teal-500 hover:scale-101 active:scale-[0.98] text-white shadow-sky-600/20 hover:shadow-lg cursor-pointer'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300/60 shadow-none'
          }`}
        >
          {isAnalyzing ? (
            <>
              <div className="relative flex h-4 w-4 items-center justify-center flex-shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-200 opacity-80" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white shadow-sm" />
              </div>
              <span className="tracking-wide font-semibold">Executing Forensic Pipeline...</span>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent animate-[shimmer_2s_infinite] pointer-events-none" />
            </>
          ) : canAnalyze ? (
            <>
              <ShieldCheck className="w-5 h-5 text-teal-300" />
              <span>Run Claim Forensics & Audit</span>
              <ArrowRight className="w-4 h-4" />
            </>
          ) : (
            <>
              <Lock className="w-4 h-4 text-slate-400" />
              <span>Attach All 3 Documents ({3 - uploadedCount} remaining)</span>
            </>
          )}
        </button>

        {claimId && (
          <div className="text-center text-[11px] text-slate-500 font-financial">
            Active Session Claim ID: <span className="font-bold text-slate-800 font-mono">{claimId}</span>
          </div>
        )}

        {!canAnalyze && (
          <p className="text-center text-[11px] text-slate-500 leading-tight">
            Attach all 3 documents to initiate the IRDAI statutory verification audit.
          </p>
        )}
      </div>
    </div>
  );
}
