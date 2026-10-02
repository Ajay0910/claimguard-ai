import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldCheck, CheckCircle2, AlertTriangle, XCircle, Loader2,
  TrendingUp, FileText, Download, RefreshCw, Home, ExternalLink,
  Clock, Zap, BarChart3, Info,
} from 'lucide-react'

// ── Pipeline Stages ──────────────────────────────────────────────────
const STAGES = [
  { key: 'QUEUED',     label: 'Documents Received',   icon: FileText,    desc: 'Your documents have been securely uploaded and are queued.' },
  { key: 'EXTRACTING', label: 'Reading Documents',    icon: Zap,         desc: 'Our AI is extracting data from your files.' },
  { key: 'ANALYZING',  label: 'Analysing Your Claim', icon: BarChart3,   desc: 'Checking against IRDAI regulations.' },
  { key: 'REVIEW_RECOMMENDED', label: 'Human Review Needed', icon: Info, desc: 'Some evidence could not be verified. Financial conclusions are withheld until review.' },
  { key: 'COMPLETED',  label: 'Analysis Complete',    icon: ShieldCheck, desc: 'Your full report is ready.' },
]

function getStageIndex(status) {
  const map = { PENDING: 0, QUEUED: 0, EXTRACTING: 1, ANALYZING: 2, REVIEW_RECOMMENDED: 3, COMPLETED: 4, FAILED: -1 }
  return map[status] ?? 0
}

// ── Currency formatter ───────────────────────────────────────────────
function formatINR(amount) {
  if (amount === null || amount === undefined || !Number.isFinite(Number(amount))) return 'Not verified'
  if (Number(amount) === 0) return '₹0'
  const abs = Math.abs(amount)
  if (abs >= 100000) return `₹${(abs / 100000).toFixed(1)}L`
  if (abs >= 1000) return `₹${(abs / 1000).toFixed(0)}K`
  return `₹${abs.toLocaleString('en-IN')}`
}

// ── Status color helpers ─────────────────────────────────────────────
function getResultStyle(status) {
  switch (status) {
    case 'NO_MISMATCH_FOUND': return { bg: 'bg-emerald-50', border: 'border-emerald-200', icon: CheckCircle2, iconColor: 'text-emerald-600', badge: 'bg-emerald-100 text-emerald-700' }
    case 'MISMATCH_DETECTED': return { bg: 'bg-rose-50', border: 'border-rose-200', icon: AlertTriangle, iconColor: 'text-rose-600', badge: 'bg-rose-100 text-rose-700' }
    default: return { bg: 'bg-amber-50', border: 'border-amber-200', icon: Info, iconColor: 'text-amber-600', badge: 'bg-amber-100 text-amber-700' }
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
            const isPending = currentIdx < i

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

// ── Result Card ──────────────────────────────────────────────────────
function ResultCard({ result, onDownloadAppeal, claimId }) {
  const style = getResultStyle(result.overall_status)
  const StatusIcon = style.icon

  return (
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
                   result.overall_status === 'MISMATCH_DETECTED' ? 'Potential Mismatch Found' : 'Human Review Needed'}
                </h3>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${style.badge}`}>
                  {(result.overall_status || '').replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">{result.plain_summary}</p>
            </div>
          </div>
        </div>

        {/* Financial metrics */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="card p-4 text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Recoverable</p>
            <p className="text-xl font-black text-blue-600">{formatINR(result.recoverable_amount)}</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Violations</p>
            <p className="text-xl font-black text-rose-600">{result.violations_found}</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Rules Checked</p>
            <p className="text-xl font-black text-slate-700">{result.total_rules_checked}</p>
          </div>
        </div>

        {/* Violations list */}
        {result.violations && result.violations.length > 0 && (
          <div className="card p-5 mb-5">
            <h4 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Issues Found
            </h4>
            <div className="space-y-3">
              {result.violations.map((v, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{v.rule || 'Regulation Violation'}</p>
                    {v.recoverable > 0 && (
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full whitespace-nowrap">
                        +{formatINR(v.recoverable)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{v.finding}</p>
                  {v.citation && (
                    <p className="text-[10px] text-blue-500 mt-1 font-medium">{v.citation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link to="/" className="btn-secondary flex-1 justify-center">
            <Home className="w-4 h-4" /> Check Another Claim
          </Link>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

// ── Main TrackPage ───────────────────────────────────────────────────
export default function TrackPage() {
  const { claimId } = useParams()
  const location = useLocation()
  const [portalSecret, setPortalSecret] = useState(() => location.state?.portalSecret || sessionStorage.getItem(`claimguard-portal-secret:${claimId}`) || '')
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
      const baseUrl = import.meta.env.VITE_API_URL || '';
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
      // Production: connect directly to backend (e.g. wss://claimguard-ai-backend.onrender.com)
      const wsBase = apiBase.replace(/^https?/, (m) => m === 'https' ? 'wss' : 'ws')
      wsUrl = `${wsBase}/api/portal/ws/claim/${claimId}`
    } else {
      // Development: proxy through Vite
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
          // Refetch full data when status changes
          fetchStatus()
        }
      }
      ws.onerror = () => setWsStatus('disconnected')
      ws.onclose = () => {
        setWsStatus('disconnected')
        // Fallback to polling every 5 seconds if WS disconnects
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

  // Stop polling when completed
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
        {/* Claim ID */}
        <div className="mb-6">
          <h1 className="text-2xl font-black text-slate-900">
            {claimData?.status === 'REVIEW_RECOMMENDED' ? 'Human Review Needed' : isComplete ? '🎉 Your Results Are Ready' : isFailed ? '⚠️ Processing Failed' : '⏳ Analysing Your Claim…'}
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
