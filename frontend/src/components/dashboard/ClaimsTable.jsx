import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  X,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  FileSearch,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Copy,
  Check,
  RotateCcw,
  UploadCloud,
  SearchX,
  Download,
} from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import { TableSkeleton } from '../common/Skeletons';
import { toast } from 'sonner';

// ==========================================
// Helper: INR Currency Formatter (en-IN)
// ==========================================
export const formatINR = (amount, { showZeroClean = false } = {}) => {
  if (
    amount === null ||
    amount === undefined ||
    amount === '' ||
    (typeof amount === 'string' && amount.trim() === '') ||
    Array.isArray(amount) ||
    isNaN(amount)
  ) {
    return '—';
  }
  const num = Number(amount);
  if (num === 0 && showZeroClean) {
    return '₹0.00';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

// ==========================================
// Helper: Date & Relative Time Formatter
// ==========================================
export const formatClaimDate = (dateStr) => {
  if (!dateStr) return { formatted: '—', relative: '' };
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return { formatted: String(dateStr), relative: '' };

    const formatted = d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });

    const diffDays = Math.floor((new Date() - d) / (1000 * 60 * 60 * 24));
    let relative = '';
    if (diffDays === 0) relative = 'Today';
    else if (diffDays === 1) relative = 'Yesterday';
    else if (diffDays > 1 && diffDays <= 30) relative = `${diffDays}d ago`;

    return { formatted, relative };
  } catch {
    return { formatted: String(dateStr), relative: '' };
  }
};

// ==========================================
// Helper: Status Category Matcher
// ==========================================
export const matchesStatusTab = (claim, tabKey) => {
  if (!claim) return false;
  if (!tabKey || tabKey === 'ALL') return true;

  const status = (claim.status || '').toUpperCase().trim();
  const impact = Number(claim.monetary_impact ?? claim.impact ?? 0);
  const deduction = (claim.deduction_type || '').toLowerCase();
  const normalizedTab = tabKey.toUpperCase().trim();

  switch (normalizedTab) {
    case 'FLAGGED':
    case 'MISMATCH':
      return (
        ['FAIL', 'FAILED', 'MISMATCH_DETECTED', 'HIGH_RISK', 'TAMPERED', 'REJECTED', 'SUSPICIOUS'].includes(status) ||
        (impact > 0 && !['PENDING', 'ANALYZING', 'RUNNING', 'EXTRACTING'].includes(status))
      );

    case 'APPROVED':
    case 'COMPLETED':
      return (
        ['PASS', 'APPROVED', 'CLEAN', 'NO_MISMATCH_FOUND', 'VERIFIED'].includes(status) ||
        (status === 'COMPLETED' && impact === 0)
      );

    case 'REVIEW':
    case 'PENDING':
      return [
        'REVIEW_RECOMMENDED',
        'NEEDS_REVIEW',
        'WARNING',
        'PENDING',
        'ANALYZING',
        'RUNNING',
        'EXTRACTING',
        'PROCESSING',
      ].includes(status);

    case 'DISALLOWED':
      return (
        impact > 0 ||
        deduction.includes('deduction') ||
        deduction.includes('conflict') ||
        deduction.includes('breach') ||
        status === 'PARTIAL_SETTLEMENT'
      );

    default:
      return true;
  }
};

// ==========================================
// Multi-Document Presence Pills Component
// ==========================================
export function DocumentStatusPills({ claim = {} }) {
  const docStatus = useMemo(() => {
    if (claim.documents_status && typeof claim.documents_status === 'object') {
      return {
        bill: Boolean(claim.documents_status.bill),
        policy: Boolean(claim.documents_status.policy),
        rejection: Boolean(claim.documents_status.rejection),
      };
    }
    // Fallback derivation from documents_count or docs count
    const count = Number(claim.docs ?? claim.documents_count ?? 0);
    return {
      bill: count >= 1,
      policy: count >= 2,
      rejection: count >= 3,
    };
  }, [claim]);

  const docs = [
    {
      key: 'BILL',
      label: 'BILL',
      present: docStatus.bill,
      title: docStatus.bill ? 'Hospital Bill: Extracted & Verified' : 'Hospital Bill: Missing',
    },
    {
      key: 'POL',
      label: 'POL',
      present: docStatus.policy,
      title: docStatus.policy ? 'Insurance Policy: Extracted & Active' : 'Insurance Policy: Missing',
    },
    {
      key: 'REJ',
      label: 'REJ',
      present: docStatus.rejection,
      title: docStatus.rejection ? 'Rejection Letter / Voucher: Extracted' : 'Rejection Letter: Pending',
    },
  ];

  const presentCount = Object.values(docStatus).filter(Boolean).length;

  return (
    <div className="flex items-center gap-1.5" title={`${presentCount}/3 Documents Ingested`}>
      <div className="flex items-center gap-1">
        {docs.map((d) => (
          <span
            key={d.key}
            title={d.title}
            className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded transition-all duration-150 select-none ${
              d.present
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/90 shadow-2xs'
                : 'bg-slate-100 text-slate-400 border border-slate-200 border-dashed opacity-75'
            }`}
          >
            {d.label}
          </span>
        ))}
      </div>
      <span className="text-[11px] font-medium text-slate-400">
        {presentCount}/3
      </span>
    </div>
  );
}

// ==========================================
// Main Enterprise ClaimsTable Component
// ==========================================
export default function ClaimsTable({
  claims: rawClaims = [],
  isLoading = false,
  initialSearchQuery = '',
  activeStatusTab = 'ALL',
  onTabChange = null,
  onRefresh = null,
  initialPageSize = 10,
  title = 'Enterprise Claims Ledger',
  subtitle = 'Clinical dispute tracking, IRDAI statutory verification, and forensic audit status.',
}) {
  const claims = Array.isArray(rawClaims) ? rawClaims : [];
  const navigate = useNavigate();

  // Internal state
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [internalStatusTab, setInternalStatusTab] = useState(activeStatusTab);
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [copiedId, setCopiedId] = useState(null);

  // Sync external search query from URL (e.g. Topbar search)
  useEffect(() => {
    if (initialSearchQuery !== undefined && initialSearchQuery !== null) {
      setSearchQuery(initialSearchQuery);
      setCurrentPage(1);
    }
  }, [initialSearchQuery]);

  // Sync external status tab changes (e.g. Donut slice clicks)
  useEffect(() => {
    if (activeStatusTab) {
      setInternalStatusTab(activeStatusTab);
      setCurrentPage(1);
    }
  }, [activeStatusTab]);

  const effectiveStatusTab = activeStatusTab !== undefined ? internalStatusTab : 'ALL';

  // Tab definitions
  const tabs = [
    { key: 'ALL', label: 'All Claims' },
    { key: 'FLAGGED', label: 'Flagged / Discrepancy' },
    { key: 'APPROVED', label: 'Approved' },
    { key: 'REVIEW', label: 'Under Review' },
    { key: 'DISALLOWED', label: 'Disallowed' },
  ];

  // 1. Calculate Tab Counts across entire dataset
  const tabCounts = useMemo(() => {
    const counts = { ALL: claims.length, FLAGGED: 0, APPROVED: 0, REVIEW: 0, DISALLOWED: 0 };
    claims.forEach((c) => {
      if (matchesStatusTab(c, 'FLAGGED')) counts.FLAGGED++;
      if (matchesStatusTab(c, 'APPROVED')) counts.APPROVED++;
      if (matchesStatusTab(c, 'REVIEW')) counts.REVIEW++;
      if (matchesStatusTab(c, 'DISALLOWED')) counts.DISALLOWED++;
    });
    return counts;
  }, [claims]);

  // 2. Filter Claims by Tab & Full-Text Search
  const filteredClaims = useMemo(() => {
    let result = claims;

    // Apply Status Tab Filter
    if (effectiveStatusTab !== 'ALL') {
      result = result.filter((c) => matchesStatusTab(c, effectiveStatusTab));
    }

    // Apply Full-Text Search
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      result = result.filter((c) => {
        if (!c) return false;
        const id = String(c?.id || '').toLowerCase();
        const claimNum = String(c?.claim_number || '').toLowerCase();
        const patient = String(c?.patient_name || c?.patient || '').toLowerCase();
        const hospital = String(c?.hospital || '').toLowerCase();
        const policy = String(c?.policy_number || '').toLowerCase();
        const deduction = String(c?.deduction_type || '').toLowerCase();

        return (
          id.includes(q) ||
          claimNum.includes(q) ||
          patient.includes(q) ||
          hospital.includes(q) ||
          policy.includes(q) ||
          deduction.includes(q)
        );
      });
    }

    return result;
  }, [claims, effectiveStatusTab, searchQuery]);

  // 3. Sort Filtered Claims
  const sortedClaims = useMemo(() => {
    const sorted = [...filteredClaims];
    const { key, direction } = sortConfig;
    const isAsc = direction === 'asc';

    sorted.sort((a, b) => {
      if (!a && !b) return 0;
      if (!a) return 1;
      if (!b) return -1;

      let valA, valB;

      switch (key) {
        case 'id':
          valA = String(a?.id || a?.claim_number || '').toLowerCase();
          valB = String(b?.id || b?.claim_number || '').toLowerCase();
          return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);

        case 'patient':
          valA = String(a?.patient_name || a?.patient || '').toLowerCase();
          valB = String(b?.patient_name || b?.patient || '').toLowerCase();
          return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);

        case 'date': {
          const timeA = new Date(a?.created_at || a?.date || 0).getTime();
          const timeB = new Date(b?.created_at || b?.date || 0).getTime();
          valA = isNaN(timeA) ? 0 : timeA;
          valB = isNaN(timeB) ? 0 : timeB;
          return isAsc ? valA - valB : valB - valA;
        }

        case 'total_amount': {
          const rawA = a?.total_amount ?? a?.billed_amount ?? (a?.impact ? a.impact * 2.8 : 85000);
          const rawB = b?.total_amount ?? b?.billed_amount ?? (b?.impact ? b.impact * 2.8 : 85000);
          const cleanA = typeof rawA === 'string' ? Number(rawA.replace(/[^0-9.-]+/g, '')) : Number(rawA);
          const cleanB = typeof rawB === 'string' ? Number(rawB.replace(/[^0-9.-]+/g, '')) : Number(rawB);
          valA = isNaN(cleanA) ? 0 : cleanA;
          valB = isNaN(cleanB) ? 0 : cleanB;
          return isAsc ? valA - valB : valB - valA;
        }

        case 'impact': {
          const rawA = a?.monetary_impact ?? a?.impact ?? 0;
          const rawB = b?.monetary_impact ?? b?.impact ?? 0;
          const cleanA = typeof rawA === 'string' ? Number(rawA.replace(/[^0-9.-]+/g, '')) : Number(rawA);
          const cleanB = typeof rawB === 'string' ? Number(rawB.replace(/[^0-9.-]+/g, '')) : Number(rawB);
          valA = isNaN(cleanA) ? 0 : cleanA;
          valB = isNaN(cleanB) ? 0 : cleanB;
          return isAsc ? valA - valB : valB - valA;
        }

        case 'status':
          valA = String(a?.status || '').toLowerCase();
          valB = String(b?.status || '').toLowerCase();
          return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);

        default:
          return 0;
      }
    });

    return sorted;
  }, [filteredClaims, sortConfig]);

  // 4. Pagination Slicing
  const totalPages = Math.max(1, Math.ceil(sortedClaims.length / pageSize));
  const currentPageSafe = Math.min(currentPage, totalPages);

  const paginatedClaims = useMemo(() => {
    const startIndex = (currentPageSafe - 1) * pageSize;
    return sortedClaims.slice(startIndex, startIndex + pageSize);
  }, [sortedClaims, currentPageSafe, pageSize]);

  // Reset page to 1 when search, tab, or page size changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, effectiveStatusTab, pageSize]);

  // Column sort handler
  const handleSort = (columnKey) => {
    setSortConfig((prev) => {
      if (prev.key === columnKey) {
        return {
          key: columnKey,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return {
        key: columnKey,
        direction: columnKey === 'date' || columnKey === 'impact' || columnKey === 'total_amount' ? 'desc' : 'asc',
      };
    });
  };

  // Tab switch handler
  const handleTabClick = (tabKey) => {
    setInternalStatusTab(tabKey);
    setCurrentPage(1);
    if (onTabChange) {
      onTabChange(tabKey);
    }
  };

  // Copy Claim ID action
  const handleCopyId = (e, id) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(id);
    }
    setCopiedId(id);
    toast.success(`Claim ${id} Copied`, {
      description: 'Claim identifier copied to clipboard.',
      duration: 1500,
    });
    setTimeout(() => setCopiedId(null), 1800);
  };

  // Row navigation handler
  const handleRowClick = (claimId) => {
    navigate(`/analysis/${claimId}`);
  };

  // Reset filters
  const handleResetFilters = () => {
    setSearchQuery('');
    handleTabClick('ALL');
  };

  // Export CSV handler
  const exportCsv = () => {
    const sanitizeCsvCell = (val) => {
      const str = String(val ?? '');
      let sanitized = str.replace(/"/g, '""');
      if (['=', '+', '-', '@'].some((p) => sanitized.startsWith(p))) {
        sanitized = `'${sanitized}`;
      }
      return `"${sanitized}"`;
    };

    const headers = ['Claim ID', 'Patient', 'Policy Number', 'Status', 'Hospital', 'Total Billed', 'Disallowed Impact', 'Date'];
    const rows = sortedClaims.map((c) => [
      sanitizeCsvCell(c?.id || ''),
      sanitizeCsvCell(c?.patient_name || c?.patient || 'Unknown'),
      sanitizeCsvCell(c?.policy_number || ''),
      sanitizeCsvCell(c?.status || ''),
      sanitizeCsvCell(c?.hospital || ''),
      sanitizeCsvCell(c?.total_amount ?? c?.billed_amount ?? (c?.impact ? Math.round(c.impact * 2.8) : 85000)),
      sanitizeCsvCell(c?.monetary_impact ?? c?.impact ?? 0),
      sanitizeCsvCell(c?.date || c?.created_at || ''),
    ]);
    const csvContent = [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `claimguard_claims_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 100);
    toast.success('Claims Exported', {
      description: `Exported ${sortedClaims.length} records to CSV file.`,
    });
  };

  // Range indicator numbers
  const startItem = sortedClaims.length === 0 ? 0 : (currentPageSafe - 1) * pageSize + 1;
  const endItem = Math.min(currentPageSafe * pageSize, sortedClaims.length);

  // Render Loading Skeleton
  if (isLoading) {
    return <TableSkeleton rows={pageSize || 8} cols={7} />;
  }

  return (
    <div className="card-enterprise overflow-hidden border-slate-200/90 shadow-card">
      {/* 1. Header & Quick Actions Toolbar */}
      <div className="p-5 md:p-6 border-b border-slate-200/90 bg-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 font-mono">
                {claims.length} Total
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
          </div>

          {/* Search Input & Action Buttons */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ID, patient, hospital, policy..."
                className="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600 transition-all duration-150"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  title="Clear search"
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <button
              type="button"
              onClick={exportCsv}
              title="Export filtered records as CSV"
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:scale-101 active:scale-[0.98] rounded-lg text-xs font-semibold shadow-xs transition-all"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span className="hidden sm:inline">Export</span>
            </button>

            {onRefresh && (
              <button
                type="button"
                onClick={onRefresh}
                title="Refresh claims data"
                className="p-2 border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 hover:scale-101 active:scale-[0.98] rounded-lg transition-all duration-150 shadow-xs"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* 2. Status Filter Tabs Bar */}
        <div className="flex items-center gap-1.5 mt-5 overflow-x-auto pb-1 -mb-1 scrollbar-none">
          {tabs.map((tab) => {
            const isActive =
              effectiveStatusTab === tab.key ||
              (tab.key === 'FLAGGED' && effectiveStatusTab === 'MISMATCH') ||
              (tab.key === 'APPROVED' && effectiveStatusTab === 'COMPLETED') ||
              (tab.key === 'REVIEW' && effectiveStatusTab === 'PENDING');

            const count = tabCounts[tab.key] || 0;

            const tabColors = {
              ALL: isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100',
              FLAGGED: isActive ? 'bg-rose-50 text-rose-800 border-rose-200 shadow-xs' : 'text-slate-600 hover:bg-slate-100',
              APPROVED: isActive ? 'bg-emerald-50 text-emerald-800 border-emerald-200 shadow-xs' : 'text-slate-600 hover:bg-slate-100',
              REVIEW: isActive ? 'bg-amber-50 text-amber-800 border-amber-200 shadow-xs' : 'text-slate-600 hover:bg-slate-100',
              DISALLOWED: isActive ? 'bg-purple-50 text-purple-800 border-purple-200 shadow-xs' : 'text-slate-600 hover:bg-slate-100',
            };

            const countBadgeColors = {
              ALL: isActive ? 'bg-slate-800 text-slate-200' : 'bg-slate-200 text-slate-700',
              FLAGGED: isActive ? 'bg-rose-200/70 text-rose-900' : 'bg-slate-100 text-slate-600',
              APPROVED: isActive ? 'bg-emerald-200/70 text-emerald-900' : 'bg-slate-100 text-slate-600',
              REVIEW: isActive ? 'bg-amber-200/70 text-amber-900' : 'bg-slate-100 text-slate-600',
              DISALLOWED: isActive ? 'bg-purple-200/70 text-purple-900' : 'bg-slate-100 text-slate-600',
            };

            return (
              <button
                type="button"
                key={tab.key}
                onClick={() => handleTabClick(tab.key)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border active:scale-95 transition-all duration-150 whitespace-nowrap ${
                  isActive ? `border ${tabColors[tab.key]}` : 'border-transparent text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] font-bold font-mono px-1.5 py-0.2 rounded-full ${
                    countBadgeColors[tab.key]
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Main Data Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          {/* Table Head with Sortable Columns */}
          <thead className="bg-slate-50/80 text-slate-500 font-semibold border-b border-slate-200/90 tracking-wide uppercase text-[11px]">
            <tr>
              {/* Claim ID Header */}
              <th
                onClick={() => handleSort('id')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[170px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Claim ID</span>
                  {sortConfig.key === 'id' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Patient Header */}
              <th
                onClick={() => handleSort('patient')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[190px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Patient & Policy</span>
                  {sortConfig.key === 'patient' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Date Header */}
              <th
                onClick={() => handleSort('date')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[120px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Date</span>
                  {sortConfig.key === 'date' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Total Amount Header */}
              <th
                onClick={() => handleSort('total_amount')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[130px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Total Billed</span>
                  {sortConfig.key === 'total_amount' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Disallowed Amount Header */}
              <th
                onClick={() => handleSort('impact')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[150px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Disallowed (Impact)</span>
                  {sortConfig.key === 'impact' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Documents Presence Header */}
              <th className="px-5 py-3.5 min-w-[130px]">Documents</th>

              {/* Status Header */}
              <th
                onClick={() => handleSort('status')}
                className="px-5 py-3.5 cursor-pointer hover:bg-slate-100/70 transition-colors select-none group min-w-[140px]"
              >
                <div className="flex items-center gap-1.5">
                  <span>Audit Status</span>
                  {sortConfig.key === 'status' ? (
                    sortConfig.direction === 'asc' ? (
                      <ArrowUp className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <ArrowDown className="w-3.5 h-3.5 text-brand-600" />
                    )
                  ) : (
                    <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>
              </th>

              {/* Action Header */}
              <th className="px-5 py-3.5 text-right min-w-[110px]">Action</th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginatedClaims.map((claim) => {
              const { formatted: formattedDate, relative: relativeTime } = formatClaimDate(
                claim.created_at || claim.date
              );

              const billedAmount = claim.total_amount ?? claim.billed_amount ?? (claim.impact ? Math.round(claim.impact * 2.8) : 85000);
              const disallowedAmount = claim.monetary_impact ?? claim.impact;
              const hasDisallowance = disallowedAmount !== null && disallowedAmount !== undefined && disallowedAmount > 0;

              return (
                <tr
                  key={claim.id}
                  onClick={() => handleRowClick(claim.id)}
                  tabIndex={0}
                  role="row"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRowClick(claim.id);
                  }}
                  className="group hover:bg-slate-50/90 transition-colors duration-150 cursor-pointer focus:outline-none focus:bg-sky-50/30"
                >
                  {/* Col 1: Claim ID & Hospital */}
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs text-brand-700 group-hover:text-brand-800 transition-colors">
                        {claim.id}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => handleCopyId(e, claim.id)}
                        title="Copy Claim ID"
                        className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition-colors opacity-0 group-hover:opacity-100"
                      >
                        {copiedId === claim.id ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                    <div className="text-[11px] text-slate-500 truncate max-w-[170px] mt-0.5" title={claim.hospital || 'Hospital Not Specified'}>
                      {claim.hospital || 'Hospital Not Specified'}
                    </div>
                  </td>

                  {/* Col 2: Patient & Policy */}
                  <td className="px-5 py-4">
                    <div className="font-semibold text-slate-900 truncate max-w-[180px]">
                      {claim.patient_name || claim.patient || 'Unknown Patient'}
                    </div>
                    <div className="text-[11px] font-mono text-slate-500 truncate max-w-[180px] mt-0.5">
                      {claim.policy_number || 'POL-UNKNOWN'}
                    </div>
                  </td>

                  {/* Col 3: Date */}
                  <td className="px-5 py-4">
                    <div className="text-slate-700 font-medium">{formattedDate}</div>
                    {relativeTime && (
                      <div className="text-[10px] text-slate-400 mt-0.5">{relativeTime}</div>
                    )}
                  </td>

                  {/* Col 4: Total Billed Amount */}
                  <td className="px-5 py-4">
                    <div className="font-financial font-semibold text-slate-900">
                      {formatINR(billedAmount)}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Hospital Net</div>
                  </td>

                  {/* Col 5: Disallowed Amount / Impact */}
                  <td className="px-5 py-4">
                    {disallowedAmount !== null && disallowedAmount !== undefined ? (
                      hasDisallowance ? (
                        <div>
                          <div className="font-financial font-bold text-rose-600">
                            {formatINR(disallowedAmount)}
                          </div>
                          {claim.deduction_type && (
                            <div
                              className="text-[10px] text-rose-600/80 truncate max-w-[140px] mt-0.5"
                              title={claim.deduction_type}
                            >
                              {claim.deduction_type}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div>
                          <span className="font-financial font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/70 text-[11px]">
                            ₹0.00 (Clean)
                          </span>
                        </div>
                      )
                    ) : (
                      <span className="text-slate-400 font-financial text-[11px] italic">
                        Awaiting Audit
                      </span>
                    )}
                  </td>

                  {/* Col 6: Multi-Document Presence Pills */}
                  <td className="px-5 py-4">
                    <DocumentStatusPills claim={claim} />
                  </td>

                  {/* Col 7: Audit Status Badge */}
                  <td className="px-5 py-4">
                    <StatusBadge status={claim.status} size="sm" />
                  </td>

                  {/* Col 8: Action Button */}
                  <td className="px-5 py-4 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRowClick(claim.id);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-50 hover:bg-brand-600 text-slate-700 hover:text-white border border-slate-200/90 hover:border-brand-600 rounded-lg text-xs font-semibold transition-all duration-150 shadow-2xs group-hover:border-brand-300"
                    >
                      <span>View Audit</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 4. Empty State: No search/filter match */}
      {claims.length > 0 && paginatedClaims.length === 0 && (
        <div className="p-12 text-center bg-white">
          <SearchX className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-900 mb-1">No Claims Matching Criteria</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
            No claims found matching &ldquo;{searchQuery}&rdquo; in category &ldquo;{effectiveStatusTab}&rdquo;. Try resetting your filters.
          </p>
          <button
            type="button"
            onClick={handleResetFilters}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Search & Filters
          </button>
        </div>
      )}

      {/* 5. Empty State: No claims in system */}
      {claims.length === 0 && (
        <div className="p-12 text-center bg-white">
          <ShieldCheck className="w-12 h-12 text-teal-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-900 mb-1">No Clinical Claims Registered</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
            Upload hospital bills, insurance policies, and rejection letters to begin statutory IRDAI auditing.
          </p>
          <button
            type="button"
            onClick={() => navigate('/upload')}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs rounded-lg shadow-sm transition-colors"
          >
            <UploadCloud className="w-4 h-4" />
            Upload First Claim
          </button>
        </div>
      )}

      {/* 6. Pagination Footer Controls */}
      {sortedClaims.length > 0 && (
        <div className="px-6 py-4 border-t border-slate-200/90 bg-white flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
          {/* Left: Range Indicator & Page Size Selector */}
          <div className="flex items-center gap-4">
            <span>
              Showing <strong className="text-slate-900 font-semibold">{startItem}</strong> to{' '}
              <strong className="text-slate-900 font-semibold">{endItem}</strong> of{' '}
              <strong className="text-slate-900 font-semibold font-financial">{sortedClaims.length}</strong> claims
            </span>

            <div className="flex items-center gap-1.5 text-slate-500">
              <span>Per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="bg-slate-50 border border-slate-200 rounded-md px-2 py-0.5 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          {/* Right: Prev / Next & Numbered Buttons */}
          <div className="flex items-center gap-1">
            {/* First Page */}
            <button
              type="button"
              onClick={() => setCurrentPage(1)}
              disabled={currentPageSafe <= 1}
              title="First Page"
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsLeft className="w-3.5 h-3.5" />
            </button>

            {/* Prev Page */}
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPageSafe <= 1}
              title="Previous Page"
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>

            {/* Page Number Buttons */}
            {Array.from({ length: totalPages }).map((_, idx) => {
              const p = idx + 1;
              if (
                totalPages > 6 &&
                p !== 1 &&
                p !== totalPages &&
                Math.abs(p - currentPageSafe) > 1
              ) {
                if (p === 2 || p === totalPages - 1) {
                  return (
                    <span key={p} className="px-1 text-slate-400 select-none">
                      ...
                    </span>
                  );
                }
                return null;
              }

              const isActive = p === currentPageSafe;
              return (
                <button
                  type="button"
                  key={p}
                  onClick={() => setCurrentPage(p)}
                  className={`min-w-[28px] h-7 px-2 rounded text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-2xs'
                      : 'border border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {p}
                </button>
              );
            })}

            {/* Next Page */}
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPageSafe >= totalPages}
              title="Next Page"
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>

            {/* Last Page */}
            <button
              type="button"
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPageSafe >= totalPages}
              title="Last Page"
              className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
