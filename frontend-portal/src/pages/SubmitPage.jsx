import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  User, Mail, Phone, UploadCloud, FileText, ShieldCheck, FileSearch,
  X, CheckCircle2, ArrowRight, ArrowLeft, Loader2, AlertCircle,
} from 'lucide-react'

const STEPS = ['Your Details', 'Upload Documents', 'Confirm & Submit']

const DOC_SLOTS = [
  {
    key: 'hospital_bill',
    label: 'Hospital Bill',
    description: 'The itemized bill from your hospital or clinic',
    icon: FileText,
    required: true,
    color: 'blue',
  },
  {
    key: 'insurance_policy',
    label: 'Insurance Policy',
    description: 'Your health insurance policy document',
    icon: ShieldCheck,
    required: true,
    color: 'emerald',
  },
  {
    key: 'rejection_letter',
    label: 'Rejection / Settlement Letter',
    description: "Your insurer's rejection or partial settlement letter",
    icon: FileSearch,
    required: true,
    color: 'amber',
  },
]

function FileDropzone({ slot, file, onFile, onRemove }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const Icon = slot.icon
  const colorMap = {
    blue: { border: 'border-blue-300 bg-blue-50', icon: 'text-blue-500', badge: 'bg-blue-100 text-blue-700' },
    emerald: { border: 'border-emerald-300 bg-emerald-50', icon: 'text-emerald-500', badge: 'bg-emerald-100 text-emerald-700' },
    amber: { border: 'border-amber-300 bg-amber-50', icon: 'text-amber-500', badge: 'bg-amber-100 text-amber-700' },
  }
  const c = colorMap[slot.color]

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  if (file) {
    return (
      <div className="card p-4 flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${c.border}`}>
          <Icon className={`w-5 h-5 ${c.icon}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">{slot.label}</p>
          <p className="text-xs text-slate-500 truncate">{file.name} · {(file.size / 1024).toFixed(0)} KB</p>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          <button type="button" onClick={onRemove} className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center transition-colors">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`w-full card p-5 border-2 border-dashed transition-all text-left ${
        dragging ? `${c.border} scale-[1.01]` : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,image/*"
        className="hidden"
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center flex-shrink-0 ${c.border}`}>
          <Icon className={`w-6 h-6 ${c.icon}`} />
        </div>
        <div>
          <p className="font-semibold text-slate-700 text-sm">
            {slot.label}
            {slot.required && <span className="text-red-400 ml-1">*</span>}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">{slot.description}</p>
          <p className="text-xs text-blue-500 font-medium mt-1">Click to upload · PDF, JPG, PNG</p>
        </div>
      </div>
    </button>
  )
}

export default function SubmitPage() {
  const navigate = useNavigate()
  const submissionSecretRef = useRef(sessionStorage.getItem('claimguard-pending-submission-secret'))
  const [step, setStep] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const [details, setDetails] = useState({ name: '', email: '', phone: '' })
  const [files, setFiles] = useState({ hospital_bill: null, insurance_policy: null, rejection_letter: null })

  const canProceedStep0 = details.name.trim().length >= 2 && details.email.includes('@')
  const canProceedStep1 = files.hospital_bill && files.insurance_policy && files.rejection_letter

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      if (!submissionSecretRef.current) {
        const bytes = crypto.getRandomValues(new Uint8Array(32))
        submissionSecretRef.current = btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
        sessionStorage.setItem('claimguard-pending-submission-secret', submissionSecretRef.current)
      }
      const form = new FormData()
      form.append('patient_name', details.name)
      form.append('patient_email', details.email)
      form.append('patient_phone', details.phone)
      if (files.hospital_bill) form.append('hospital_bill', files.hospital_bill)
      if (files.insurance_policy) form.append('insurance_policy', files.insurance_policy)
      if (files.rejection_letter) form.append('rejection_letter', files.rejection_letter)

      const baseUrl = import.meta.env.VITE_API_URL || '';
      const res = await fetch(`${baseUrl}/api/portal/submit`, {
        method: 'POST',
        headers: { 'X-Portal-Secret': submissionSecretRef.current },
        body: form,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Submission failed')
      }
      const data = await res.json()
      sessionStorage.removeItem('claimguard-pending-submission-secret')
      toast.success('Documents submitted!', { description: 'Analysis is starting. You will see live updates.' })
      sessionStorage.setItem(`claimguard-portal-secret:${data.claim_id}`, data.portal_secret)
      navigate(`/track/${data.claim_id}`, { state: { portalSecret: data.portal_secret } })
    } catch (err) {
      toast.error('Submission failed', { description: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="max-w-xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-white" />
            </div>
            <span className="font-black text-slate-900">ClaimGuard</span>
          </div>
          <span className="text-xs text-slate-400">Step {step + 1} of {STEPS.length}</span>
        </div>
      </div>

      {/* Step indicator */}
      <div className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-xl mx-auto flex gap-1">
          {STEPS.map((s, i) => (
            <div key={s} className="flex-1">
              <div className={`h-1 rounded-full transition-all duration-300 ${i <= step ? 'bg-blue-600' : 'bg-slate-200'}`} />
              <p className={`text-[10px] font-semibold mt-1.5 text-center hidden sm:block ${i === step ? 'text-blue-600' : 'text-slate-400'}`}>{s}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 max-w-xl mx-auto w-full px-4 py-8">
        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div key="step0" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
              <h2 className="text-2xl font-black text-slate-900 mb-1">Your Details</h2>
              <p className="text-sm text-slate-500 mb-6">We need this to identify your claim. Your data is private and secure.</p>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5 block">Full Name *</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      className="input-field pl-10"
                      placeholder="e.g. Rajesh Kumar"
                      value={details.name}
                      onChange={(e) => setDetails(p => ({ ...p, name: e.target.value }))}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5 block">Email Address *</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="email"
                      className="input-field pl-10"
                      placeholder="rajesh@example.com"
                      value={details.email}
                      onChange={(e) => setDetails(p => ({ ...p, email: e.target.value }))}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5 block">Phone Number (optional)</label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="tel"
                      className="input-field pl-10"
                      placeholder="+91 98765 43210"
                      value={details.phone}
                      onChange={(e) => setDetails(p => ({ ...p, phone: e.target.value }))}
                    />
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={!canProceedStep0}
                className="btn-primary w-full mt-8"
              >
                Next: Upload Documents <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
              <h2 className="text-2xl font-black text-slate-900 mb-1">Upload Documents</h2>
              <p className="text-sm text-slate-500 mb-6">Upload PDF or image files. Hospital Bill and Insurance Policy are required.</p>
              <div className="space-y-3">
                {DOC_SLOTS.map((slot) => (
                  <FileDropzone
                    key={slot.key}
                    slot={slot}
                    file={files[slot.key]}
                    onFile={(f) => setFiles(p => ({ ...p, [slot.key]: f }))}
                    onRemove={() => setFiles(p => ({ ...p, [slot.key]: null }))}
                  />
                ))}
              </div>
              {!canProceedStep1 && (
                <div className="mt-4 flex items-center gap-2 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  Hospital Bill and Insurance Policy are required to proceed.
                </div>
              )}
              <div className="flex gap-3 mt-8">
                <button type="button" onClick={() => setStep(0)} className="btn-secondary flex-1">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
                <button type="button" onClick={() => setStep(2)} disabled={!canProceedStep1} className="btn-primary flex-1">
                  Review & Submit <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
              <h2 className="text-2xl font-black text-slate-900 mb-1">Confirm & Submit</h2>
              <p className="text-sm text-slate-500 mb-6">Review your submission before we begin the analysis.</p>
              <div className="card p-5 space-y-4 mb-6">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">Your Details</p>
                  <p className="font-semibold text-slate-800">{details.name}</p>
                  <p className="text-sm text-slate-500">{details.email}</p>
                  {details.phone && <p className="text-sm text-slate-500">{details.phone}</p>}
                </div>
                <div className="border-t border-slate-100 pt-4">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">Documents</p>
                  {DOC_SLOTS.map((slot) => (
                    <div key={slot.key} className="flex items-center gap-2 py-1">
                      {files[slot.key] ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 flex-shrink-0" />
                      )}
                      <span className={`text-sm ${files[slot.key] ? 'text-slate-700 font-medium' : 'text-slate-400'}`}>
                        {slot.label} {files[slot.key] && <span className="text-xs font-normal text-slate-400">· {files[slot.key].name}</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-slate-400 text-center mb-4">
                By submitting, you agree that this data is used solely for claim analysis. All data is encrypted and handled under DPDP Act 2023.
              </p>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(1)} className="btn-secondary flex-1">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
                <button type="button" onClick={handleSubmit} disabled={submitting} className="btn-primary flex-1">
                  {submitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Submitting...</> : <><UploadCloud className="w-4 h-4" /> Submit Claim</>}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
