import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, XCircle, Clock, ShieldCheck } from 'lucide-react';

/**
 * Enterprise Status Badge
 * Maps all backend & UI statuses to standardized healthcare risk semantics.
 */
export default function StatusBadge({ status, size = 'md', showIcon = true, className = '' }) {
  const normStatus = (status === undefined || status === null ? 'PENDING' : status).toString().toUpperCase().trim();

  const getStyle = () => {
    switch (normStatus) {
      case 'PASS':
      case 'COMPLETED':
      case 'NO_MISMATCH_FOUND':
      case 'CLEAN':
      case 'APPROVED':
      case 'VERIFIED':
        return {
          wrapper: 'bg-emerald-50 text-emerald-700 border-emerald-200/90',
          dot: 'bg-emerald-500',
          icon: CheckCircle2,
          label: normStatus === 'NO_MISMATCH_FOUND' ? 'No Mismatch' : normStatus === 'COMPLETED' ? 'Completed' : 'Pass',
        };

      case 'FAIL':
      case 'FAILED':
      case 'MISMATCH_DETECTED':
      case 'HIGH_RISK':
      case 'REJECTED':
      case 'SUSPICIOUS':
      case 'TAMPERED':
        return {
          wrapper: 'bg-rose-50 text-rose-700 border-rose-200/90',
          dot: 'bg-rose-500',
          icon: AlertTriangle,
          label: normStatus === 'MISMATCH_DETECTED' ? 'Mismatch Detected' : normStatus === 'FAILED' ? 'Failed' : 'Discrepancy',
        };

      case 'REVIEW_RECOMMENDED':
      case 'NEEDS_REVIEW':
      case 'EXTRACTION_FAILED':
      case 'INSUFFICIENT_EVIDENCE':
      case 'REVIEW_REQUIRED':
      case 'WARNING':
      case 'PENDING':
      case 'QUEUED':
      case 'PARTIAL_SETTLEMENT':
        return {
          wrapper: 'bg-amber-50 text-amber-700 border-amber-200/90',
          dot: 'bg-amber-500',
          icon: Clock,
          label: ['REVIEW_RECOMMENDED', 'EXTRACTION_FAILED', 'INSUFFICIENT_EVIDENCE', 'REVIEW_REQUIRED'].includes(normStatus)
            ? 'Review Needed'
            : normStatus === 'QUEUED' ? 'Queued' : normStatus === 'PENDING' ? 'Pending' : 'Under Review',
        };

      case 'ANALYZING':
      case 'RUNNING':
      case 'EXTRACTING':
      case 'PROCESSING':
        return {
          wrapper: 'bg-sky-50 text-sky-700 border-sky-200/90 animate-pulse',
          dot: 'bg-sky-500',
          icon: Activity,
          label: 'Analyzing...',
        };

      case 'SKIPPED':
      default:
        return {
          wrapper: 'bg-slate-100 text-slate-700 border-slate-200',
          dot: 'bg-slate-400',
          icon: ShieldCheck,
          label: status || 'Standard',
        };
    }
  };

  const style = getStyle();
  const IconComponent = style.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[11px] font-medium gap-1',
    md: 'px-2.5 py-1 text-xs font-semibold gap-1.5',
    lg: 'px-3.5 py-1.5 text-sm font-semibold gap-2',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-xs transition-colors duration-150 ${sizeClasses[size] || sizeClasses.md} ${style.wrapper} ${className}`}
    >
      {showIcon && (
        normStatus === 'ANALYZING' || normStatus === 'RUNNING' || normStatus === 'EXTRACTING' || normStatus === 'PROCESSING' ? (
          <span className="relative flex h-2 w-2 flex-shrink-0" aria-label="Processing indicator">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-600" />
          </span>
        ) : (
          <IconComponent className="w-3.5 h-3.5 flex-shrink-0" />
        )
      )}
      <span>{style.label}</span>
    </span>
  );
}
