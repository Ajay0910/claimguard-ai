import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Search, ChevronRight, Shield, Building2 } from 'lucide-react';
import { healthCheck } from '../../services/api';

export default function Topbar({ onSearch = null }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [apiOnline, setApiOnline] = useState(true);
  const [searchFocused, setSearchFocused] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      try {
        const res = await healthCheck();
        if (isMounted) {
          setApiOnline(res?.status === 'ok');
        }
      } catch (err) {
        if (isMounted) setApiOnline(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Keyboard shortcut Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        document.getElementById('global-claim-search')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const q = searchQuery.trim().toUpperCase();
    if (!q) return;

    if (typeof onSearch === 'function') {
      onSearch(searchQuery);
    } else if (q.startsWith('CLM-') || q.startsWith('CLM')) {
      navigate(`/analysis/${q}`);
    } else {
      navigate(`/?q=${encodeURIComponent(searchQuery)}`);
    }
    setSearchFocused(false);
  };

  // Generate dynamic breadcrumb segments
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const getBreadcrumbLabel = (seg) => {
    if (seg === 'upload') return 'Upload Claims';
    if (seg === 'analysis') return 'Analysis Hub';
    if (seg.startsWith('CLM-')) return seg;
    return seg.charAt(0).toUpperCase() + seg.slice(1);
  };

  return (
    <header className="glass-header sticky top-0 z-30 px-6 py-3 flex items-center justify-between gap-4">
      {/* Left: Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm">
        <Link to="/" className="text-slate-500 hover:text-brand-600 transition-colors font-medium">
          Dashboard
        </Link>
        {pathSegments.map((segment, idx) => {
          const path = `/${pathSegments.slice(0, idx + 1).join('/')}`;
          const isLast = idx === pathSegments.length - 1;
          return (
            <React.Fragment key={path}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              {isLast ? (
                <span className="font-semibold text-slate-900 font-financial">
                  {getBreadcrumbLabel(segment)}
                </span>
              ) : (
                <Link to={path} className="text-slate-500 hover:text-brand-600 transition-colors">
                  {getBreadcrumbLabel(segment)}
                </Link>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Middle: Global Search Input */}
      <div className="flex-1 max-w-md relative">
        <form onSubmit={handleSearchSubmit}>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              id="global-claim-search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setTimeout(() => setSearchFocused(false), 200)}
              placeholder="Search Claim ID, Patient, or Policy #..."
              className="w-full bg-slate-100/90 border border-slate-200/80 rounded-lg pl-9 pr-14 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-sans"
            />
            <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white rounded border border-slate-200 shadow-xs pointer-events-none">
              Ctrl K
            </kbd>
          </div>
        </form>

        {/* Search guidance */}
        {searchFocused && searchQuery.trim().length > 0 && (
          <div className="absolute top-full mt-1.5 left-0 right-0 bg-white rounded-xl shadow-elevation border border-slate-200 py-2 z-50 text-xs">
            <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Search
            </div>
            <p className="px-3 py-2 text-slate-600">Press Enter to search the current claims list.</p>
          </div>
        )}
      </div>

      {/* Workspace and API Health */}
      <div className="flex items-center gap-4">
        {/* Workspace Badge */}
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-100/80 border border-slate-200 text-xs">
          <Building2 className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-medium text-slate-700 truncate max-w-[170px]">
            ClaimGuard Workspace
          </span>
          <span className="text-[10px] bg-white text-slate-600 px-1.5 py-0.5 rounded font-semibold border border-slate-200">
            Claims
          </span>
        </div>

        {/* Live Backend Indicator */}
        <div
          className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border"
          title={apiOnline ? 'Backend connected' : 'Backend unavailable; live data cannot be loaded'}
        >
          <span className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
          <span className="text-[11px] text-slate-600 hidden sm:inline">
            {apiOnline ? 'API Online' : 'API Offline'}
          </span>
        </div>

        {/* Workspace Icon */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-brand-900 text-white flex items-center justify-center font-semibold text-xs shadow-xs border border-brand-700">
            <Shield className="h-4 w-4" />
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-xs font-bold text-slate-800 leading-tight">
              ClaimGuard
            </div>
            <div className="text-[11px] text-slate-500 leading-tight">
              Claims review
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
