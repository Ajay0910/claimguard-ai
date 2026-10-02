import React, { useEffect, useState } from 'react';
import { Check, Copy, Download, Edit3, Eye, Printer, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

export const formatInr = (amount) => new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
}).format(amount || 0);

export const formatINR = formatInr;

export default function AppealLetter({ appealData = null, claimId = null }) {
  const sourceText = appealData?.appeal_text || appealData?.content || appealData?.appeal_letter || '';
  const [isEditing, setIsEditing] = useState(false);
  const [draftContent, setDraftContent] = useState(sourceText);
  const [copied, setCopied] = useState(false);

  useEffect(() => setDraftContent(sourceText), [sourceText]);

  const handleCopy = async () => {
    if (!draftContent.trim() || !navigator?.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(draftContent);
      setCopied(true);
      toast.success('Appeal draft copied');
      setTimeout(() => setCopied(false), 2500);
    } catch {
      toast.error('Could not copy the appeal draft');
    }
  };

  const handleDownload = () => {
    if (!draftContent.trim()) return;
    const fileUrl = URL.createObjectURL(new Blob([draftContent], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = `ClaimGuard_Appeal_${claimId || 'draft'}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(fileUrl);
  };

  if (!sourceText.trim()) {
    return (
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-6" role="status">
        <h2 className="font-semibold text-amber-900">Appeal draft unavailable</h2>
        <p className="mt-2 text-sm text-amber-800">
          No appeal draft was returned for this claim. Complete document review before preparing an appeal.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-5" aria-label="Appeal draft">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4">
        <div>
          <h2 className="font-semibold text-slate-900">Appeal draft</h2>
          <p className="mt-1 text-sm text-slate-600">Review all facts and citations before sending.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setIsEditing((value) => !value)} className="rounded-lg border px-3 py-2 text-sm">
            {isEditing ? <Eye className="mr-1 inline h-4 w-4" /> : <Edit3 className="mr-1 inline h-4 w-4" />}
            {isEditing ? 'Preview' : 'Edit'}
          </button>
          <button type="button" onClick={() => setDraftContent(sourceText)} className="rounded-lg border px-3 py-2 text-sm">
            <RotateCcw className="mr-1 inline h-4 w-4" /> Reset
          </button>
          <button type="button" onClick={handleCopy} className="rounded-lg border px-3 py-2 text-sm">
            {copied ? <Check className="mr-1 inline h-4 w-4" /> : <Copy className="mr-1 inline h-4 w-4" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button type="button" onClick={handleDownload} className="rounded-lg border px-3 py-2 text-sm">
            <Download className="mr-1 inline h-4 w-4" /> Download
          </button>
          <button type="button" onClick={() => window.print()} className="rounded-lg border px-3 py-2 text-sm print:hidden">
            <Printer className="mr-1 inline h-4 w-4" /> Print
          </button>
        </div>
      </div>

      {isEditing ? (
        <textarea
          aria-label="Edit appeal draft"
          className="min-h-[28rem] w-full rounded-xl border border-slate-300 bg-white p-5 text-sm leading-6"
          value={draftContent}
          onChange={(event) => setDraftContent(event.target.value)}
        />
      ) : (
        <article className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-white p-6 text-sm leading-7 text-slate-800">
          {draftContent}
        </article>
      )}

      {appealData?.regulatory_citations?.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-slate-900">Citations supplied with this draft</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {appealData.regulatory_citations.map((citation, index) => <li key={`${citation}-${index}`}>{citation}</li>)}
          </ul>
        </div>
      )}
    </section>
  );
}
