import { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, UploadCloud, Activity, Menu, X, ArrowUpRight } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { Toaster } from 'sonner';
import PageMotion from './components/common/PageMotion';
import Topbar from './components/common/Topbar';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';

function App() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload Claims', path: '/upload', icon: UploadCloud },
    { name: 'Analysis', path: '/analysis', icon: Activity },
  ];

  const SidebarContent = () => (
    <>
      {/* Brand Header */}
      <div className="p-5 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/40">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center shadow-lg shadow-sky-950/50">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-extrabold tracking-tight text-white">ClaimGuard</span>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-sky-500/20 text-sky-400 px-1.5 py-0.5 rounded border border-sky-500/30">
                AI
              </span>
            </div>
            <div className="text-[11px] font-medium text-slate-400">Enterprise v2.4</div>
          </div>
        </Link>
        <button className="md:hidden text-slate-300" onClick={() => setMobileMenuOpen(false)}>
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Navigation Links with Active Borders */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          Auditing Suite
        </div>
        {navItems.map((item) => {
          const isActive = item.path === '/' 
            ? location.pathname === '/' 
            : location.pathname.startsWith(item.path);

          return (
            <Link
              key={item.name}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 relative ${
                isActive
                  ? 'bg-sky-600/15 text-sky-400 border border-sky-500/30 shadow-xs'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 hover:scale-101 active:scale-[0.98]'
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-2 bottom-2 w-1 bg-sky-500 rounded-r-full" />
              )}
              <item.icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Auditor Persona Profile Bottom Card */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
        <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/40 border border-slate-700/50">
          <div className="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
            CG
          </div>
          <div className="overflow-hidden flex-1">
            <div className="text-xs font-semibold text-slate-200 truncate">ClaimGuard AI</div>
            <div className="text-[10px] text-slate-400 truncate">Claims workspace</div>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex-col hidden md:flex border-r border-slate-800 shadow-xl flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile Navigation Drawer with Smooth Slide & Backdrop Fade */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-50 flex">
            {/* Animated Backdrop Fade */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            {/* Animated Sliding Sidebar */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 300 }}
              className="w-64 bg-slate-900 text-white flex flex-col z-10 relative shadow-2xl"
            >
              <SidebarContent />
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      {/* Main Content Column */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden p-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-sky-400" />
            <span className="text-base font-bold">ClaimGuard AI</span>
          </div>
          <button onClick={() => setMobileMenuOpen(true)}>
            <Menu className="w-6 h-6 text-white" />
          </button>
        </div>

        {/* Global Desktop Topbar */}
        <Topbar />

        {/* Page Content Scrollable Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<PageMotion><Dashboard /></PageMotion>} />
              <Route path="/upload" element={<PageMotion><Upload /></PageMotion>} />
              <Route path="/analysis/:id" element={<PageMotion><Analysis /></PageMotion>} />
              <Route path="/analysis" element={<PageMotion><Analysis /></PageMotion>} />
              <Route
                path="*"
                element={
                  <PageMotion>
                    <div className="card-enterprise p-12 text-center max-w-lg mx-auto my-12 space-y-4">
                      <Shield className="w-12 h-12 text-slate-300 mx-auto" />
                      <h1 className="text-3xl font-extrabold text-slate-900">404</h1>
                      <p className="text-sm text-slate-500">The requested claim or view could not be located.</p>
                      <Link
                        to="/"
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700 hover:scale-101 active:scale-[0.98] transition-all shadow-xs"
                      >
                        Return to Dashboard
                      </Link>
                    </div>
                  </PageMotion>
                }
              />
            </Routes>
          </AnimatePresence>
        </main>
      </div>

      <Toaster
        position="top-right"
        expand={true}
        richColors
        closeButton
        visibleToasts={6}
        theme="dark"
        toastOptions={{
          className: 'font-sans text-xs',
          style: {
            borderRadius: '12px',
          },
        }}
      />
    </div>
  );
}

export default App;
