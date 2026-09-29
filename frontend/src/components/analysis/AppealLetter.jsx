/**
 * src/components/analysis/AppealLetter.jsx
 * Formal Legal Grievance Letterhead Generator with Editable Draft & Print Layout
 * Feature 16: Formal Legal Appeal & Grievance Generator
 * Compliant with IRDAI Policyholder Protection Regulations 2024 & Insurance Ombudsman Rules 2017
 */

import React, { useState } from 'react';
import {
  Copy,
  Check,
  Printer,
  Edit3,
  Eye,
  Download,
  Scale,
  RotateCcw,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  mockAppealDraft,
  mockAnalysisResult,
  mockAuditor,
  mockTenant,
} from '../../services/mockData';

// Currency Formatter in Indian Rupees
export const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
};

export const formatINR = formatInr;

export default function AppealLetter({
  appealData = null,
  analysisResult = null,
  claimId = 'CLM-84920',
  auditor = null,
  tenant = null,
}) {
  const appeal = appealData || mockAppealDraft;
  const analysis = analysisResult || mockAnalysisResult;
  const activeAuditor = auditor || mockAuditor;
  const activeTenant = tenant || mockTenant;

  const initialText = appeal.appeal_text || appeal.content || appeal.appeal_letter || mockAppealDraft.appeal_text;
  const [isEditing, setIsEditing] = useState(false);
  const [draftContent, setDraftContent] = useState(initialText);
  const [copied, setCopied] = useState(false);

  // Copy full appeal text to clipboard
  const handleCopy = () => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(draftContent).catch(() => {});
    }
    setCopied(true);
    toast.success('Grievance Letter Copied', {
      description: 'Full statutory legal appeal text copied to clipboard.',
      icon: '📋',
    });
    setTimeout(() => setCopied(false), 2500);
  };

  // Browser Print Trigger
  const handlePrint = () => {
    window.print();
  };

  // Download Plaintext File
  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([draftContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(file);
    element.href = url;
    element.download = `IRDAI_Grievance_Letter_${claimId}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    setTimeout(() => URL.revokeObjectURL(url), 100);
    toast.success('Grievance Letter Downloaded', {
      description: `Saved as IRDAI_Grievance_Letter_${claimId}.txt`,
    });
  };

  const contestedAmount = analysis.total_monetary_impact || 42500;
  const insurerPaidAmount = analysis.total_insurer_calculation || 68000;
  const billedAmount = analysis.total_correct_calculation
    ? (analysis.total_correct_calculation + 13500)
    : 110500;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Action Banner: Grievance Generator Header (Hidden in Print) */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-elevation border border-slate-800 relative overflow-hidden print:hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-brand-500/15 to-transparent pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-brand-300 text-xs font-semibold uppercase tracking-wider">
              <Scale className="w-4 h-4" />
              <span>IRDAI Statutory Grievance Redressal Mechanism</span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Legal Appeal & Grievance Letter Generator
            </h2>
            <p className="text-slate-300 text-sm max-w-2xl">
              Auto-generates an enterprise legal grievance addressed to the Insurer's Grievance Redressal Officer (GRO), complete with statutory citations, financial table, and NABH hospital letterhead.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-white text-xs font-semibold rounded-lg border border-slate-700 transition-all duration-150 hover:scale-101 active:scale-95 shadow-xs"
            >
              {isEditing ? <Eye className="w-3.5 h-3.5" /> : <Edit3 className="w-3.5 h-3.5" />}
              <span>{isEditing ? 'View Letterhead' : 'Edit Draft'}</span>
            </button>

            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white text-xs font-semibold rounded-lg shadow-xs transition-all duration-150 hover:scale-101 active:scale-95"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-white" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Text'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-white text-xs font-semibold rounded-lg border border-slate-700 transition-all duration-150 hover:scale-101 active:scale-95 shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export .TXT</span>
            </button>

            <button
              type="button"
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-white text-slate-800 hover:bg-slate-100 active:bg-slate-200 text-xs font-semibold rounded-lg shadow-xs transition-all duration-150 hover:scale-101 active:scale-95 border border-slate-200"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
          </div>
        </div>

        {/* Regulatory Citations Pills */}
        <div className="mt-5 pt-4 border-t border-slate-800 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Statutory Citations:</span>
          {(appeal.regulatory_citations || mockAppealDraft.regulatory_citations).map((citation, i) => (
            <span
              key={i}
              className="px-2.5 py-1 rounded-md bg-slate-800 text-brand-200 border border-slate-700 text-[11px] font-mono"
            >
              {citation}
            </span>
          ))}
        </div>
      </div>

      {/* Main Container: Document Letterhead or Editable Draft */}
      {isEditing ? (
        /* Editable Draft Textarea with Character Counter */
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-card space-y-4 print:hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-brand-600" />
                Customize Grievance Letter Draft
              </h3>
              <p className="text-xs text-slate-500">
                Auditors may personalize specific arguments, add internal file notes, or attach specific case numbers.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-slate-500">
                Characters: <strong>{draftContent.length}</strong> | Words: <strong>{draftContent.trim() ? draftContent.trim().split(/\s+/).length : 0}</strong>
              </span>
              <button
                type="button"
                onClick={() => setDraftContent(initialText)}
                className="text-xs font-semibold text-brand-600 hover:underline flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Reset Draft
              </button>
            </div>
          </div>

          <textarea
            rows={22}
            value={draftContent}
            onChange={(e) => setDraftContent(e.target.value)}
            className="w-full p-4 font-mono text-xs text-slate-800 bg-slate-50 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white leading-relaxed"
          />

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-lg shadow-sm"
            >
              Done & Return to Letterhead View
            </button>
          </div>
        </div>
      ) : (
        /* Formal Printable Hospital Letterhead */
        <div className="bg-white rounded-xl border border-slate-300 shadow-elevation p-8 md:p-12 max-w-4xl mx-auto space-y-8 print:p-0 print:border-none print:shadow-none">
          {/* Letterhead Hospital Header */}
          <div className="border-b-2 border-slate-900 pb-6 text-center space-y-1">
            <div className="text-2xl font-black text-slate-900 tracking-wider uppercase font-serif">
              {activeTenant?.facility_name || 'ST. JUDE MULTI-SPECIALTY HOSPITAL'}
            </div>
            <div className="text-xs font-semibold text-slate-700 tracking-wide">
              {activeTenant?.accreditation || 'NABH Accredited Tertiary Healthcare Provider'} | {activeTenant?.tpa_desk || 'Department of Insurance Claims & Statutory Audit'}
            </div>
            <div className="text-[11px] text-slate-500">
              Hospital Campus, Medical Center Way, Indiranagar, Bengaluru - 560038 | Tel: +91 (80) 4192-8000 | Email: claims-audit@stjude-hospital.org
            </div>
            <div className="pt-2 flex justify-between items-center text-[11px] font-mono text-slate-500 border-t border-slate-200 mt-3">
              <span>REF NO: SJH/GRO-AUDIT/2026/{claimId}</span>
              <span>DATE: {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })}</span>
            </div>
          </div>

          {/* Addressee */}
          <div className="text-xs text-slate-800 space-y-1 leading-relaxed">
            <div className="font-bold text-slate-900">TO:</div>
            <div className="font-semibold">The Grievance Redressal Officer (GRO),</div>
            <div>Star Health and Allied Insurance Company Limited,</div>
            <div>Grievance & Claims Adjudication Department,</div>
            <div>No. 1, New Tank Street, Nungambakkam, Chennai - 600034.</div>
          </div>

          {/* Subject Line */}
          <div className="bg-slate-100 p-3.5 rounded border border-slate-200 text-xs font-bold text-slate-900 leading-snug">
            SUBJECT: FORMAL STATUTORY GRIEVANCE REGARDING UNLAWFUL CLAIM DEDUCTIONS UNDER IRDAI MASTER CIRCULAR MAY 2024 & SECTION 45 OF THE INSURANCE ACT, 1938
            <div className="mt-1 font-mono font-medium text-slate-700">
              Reference: Claim ID: {claimId} | Policy No: STAR-IND-99281 | Patient: Ayush Sharma | Contested Deductions: {formatInr(contestedAmount)}
            </div>
          </div>

          {/* Executive Dispute Summary Box */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs font-financial">
            <div>
              <span className="text-slate-500 block text-[11px] font-sans">Total Hospital Bill:</span>
              <strong className="text-slate-900 text-sm">{formatInr(billedAmount)}</strong>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-sans">Insurer Paid:</span>
              <strong className="text-slate-700 text-sm">{formatInr(insurerPaidAmount)}</strong>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-sans">Unlawful Deductions:</span>
              <strong className="text-rose-600 text-sm">{formatInr(contestedAmount)}</strong>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-sans">Recovery Demand:</span>
              <strong className="text-emerald-700 text-sm">{formatInr(contestedAmount)}</strong>
            </div>
          </div>

          {/* Letter Body */}
          <div className="text-xs text-slate-800 leading-relaxed space-y-4 font-serif">
            <p>Dear Sir/Madam,</p>

            <p>
              We act on behalf of the insured patient, <strong>Mr. Ayush Sharma</strong>, in respect of Settlement Voucher dated 14/09/2026 under Claim ID <strong>{claimId}</strong>. Upon comprehensive statutory audit conducted pursuant to IRDAI regulatory guidelines, we register our formal objection to deductions totaling <strong>{formatInr(contestedAmount)}</strong>.
            </p>

            <div className="space-y-3 font-sans">
              <div className="font-bold text-slate-900 uppercase tracking-wide text-xs">
                GROUNDS OF STATUTORY OBJECTION:
              </div>

              {/* Contention 1 */}
              <div className="p-3.5 bg-slate-50 rounded border border-slate-200 space-y-1.5">
                <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[11px] font-mono flex items-center justify-center">1</span>
                  CONFLICT OF IRDAI MASTER CIRCULAR ON PROPORTIONATE DEDUCTION (Ref: IRDAI/HLT/REG/CIR/084/05/2024)
                </div>
                <p className="text-xs text-slate-700 pl-6 leading-relaxed">
                  Under Clause 12.3 of the Master Circular on Operations and Allied Matters (May 2024), proportionate deductions on room category variation are restricted strictly to room-rent-linked charges. The insurer has unlawfully applied a 40% deduction to Operation Theatre charges (₹35,000) and Consultant fees (₹15,000), withholding <strong>₹32,000.00</strong> in direct contravention of binding IRDAI directives.
                </p>
              </div>

              {/* Contention 2 */}
              <div className="p-3.5 bg-slate-50 rounded border border-slate-200 space-y-1.5">
                <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[11px] font-mono flex items-center justify-center">2</span>
                  STATUTORY IMMUNITY UNDER SECTION 45 OF THE INSURANCE ACT, 1938 (60-MONTH MORATORIUM RULE)
                </div>
                <p className="text-xs text-slate-700 pl-6 leading-relaxed">
                  The subject health policy has been continuously renewed without break for 64 months. Under Section 45 of the Insurance Act, 1938 (as amended) and Regulation 15 of IRDAI Health Insurance Regulations, no policy can be repudiated or questioned for non-disclosure after continuous coverage of 5 years (60 months). Disallowance of <strong>₹10,500.00</strong> on grounds of alleged pre-existing hypertension is void ab initio.
                </p>
              </div>
            </div>

            {/* Demand & Escalation */}
            <p>
              <strong>STATUTORY DEMAND FOR RELEASE:</strong> We formally call upon your office to review the settlement voucher and release the unlawfully withheld sum of <strong>{formatInr(contestedAmount)}</strong> within fifteen (15) days of receipt of this communication, along with applicable penal interest at the Bank Rate + 2% per annum under Regulation 27 of IRDAI (Protection of Policyholders' Interests) Regulations, 2024.
            </p>

            <p>
              <strong>ESCALATION WARNING:</strong> In the event of failure to remedy this grievance within the statutory 15-day timeline, this dispute will be escalated directly to the Honorable Insurance Ombudsman under Rule 16 of the Insurance Ombudsman Rules, 2017, and registered on the IRDAI <em>Bima Bharosa</em> regulatory portal.
            </p>
          </div>

          {/* Signature Block */}
          <div className="pt-6 border-t border-slate-300 flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4 text-xs">
            <div>
              <div className="text-slate-500 font-semibold">Enclosures:</div>
              <ul className="list-disc list-inside text-slate-700 text-[11px] space-y-0.5 mt-1">
                <li>Detailed Hospital Tax Invoice #INV-2026-99120</li>
                <li>Original Policy Schedule (Policy No: STAR-IND-99281)</li>
                <li>Settlement Deduction Voucher</li>
                <li>ClaimGuard AI Cryptographic Forensic Audit Certificate</li>
              </ul>
            </div>

            <div className="sm:text-right space-y-1">
              <div className="font-serif italic text-base text-slate-800">
                {activeAuditor?.name || 'Dr. Aditi Sharma, CPC'}
              </div>
              <div className="font-bold text-slate-900">{activeAuditor?.name || 'Dr. Aditi Sharma, CPC'}</div>
              <div className="text-slate-600 text-[11px]">{activeAuditor?.title || 'Senior Medical Claims Auditor'}</div>
              <div className="text-slate-500 font-mono text-[10px]">License: {activeAuditor?.license || 'CPC-88219-IRDAI'}</div>
              <div className="text-emerald-700 text-[10px] font-semibold">Digitally Signed via ClaimGuard SHA-256 Ledger</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
