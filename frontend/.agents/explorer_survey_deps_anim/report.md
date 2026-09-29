# ClaimGuard AI — Frontend Dependency & Animation Readiness Survey Report

**Author:** `explorer_survey_deps_anim`  
**Date:** 2026-09-18  
**Scope:** `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend`  
**Focus:** Package Dependencies, Page Transitions, Modals/Drawers, Metric Cards & Steppers, Loaders vs. Skeletons, Hover States & Micro-Interactions  

---

## Executive Summary

A comprehensive architectural audit of the ClaimGuard AI React frontend was conducted across 37 files, dependencies, build configurations, and component lifecycles. 

The frontend is currently powered by **React 18.3.1**, **Vite 6.0.3**, **Tailwind CSS 3.4.16**, and **@tanstack/react-query 5.62.0**. All 72 E2E unit/contract tests (`npm test`) and production bundle builds (`npm run build`) currently pass cleanly (15.59s build, 0.38s test execution).

However, to satisfy the enterprise requirements defined in the latest project prompt (`2026-09-18T03:55:30Z`), several critical dependency, layout, and animation gaps must be resolved:
1. **`framer-motion` and `sonner` are completely absent** from `package.json`. In addition, `clsx` and `tailwind-merge` are missing. `react-hot-toast` is currently hardcoded across 10 component files.
2. **Page transitions and tab switches are instantaneous** with zero exit animations or motion smoothing. Navigating routes or switching between the 4 analysis tabs causes abrupt DOM replacement.
3. **No contextual sidebars or animated modals exist**; clicking a claim in `ClaimsTable.jsx` immediately triggers a disruptive full-page navigation to `/analysis/:id`.
4. **Metric cards and SVG sparklines/gauges are statically rendered** without entrance staggering, path drawing animations, or number tweening.
5. **Legacy raw spinning loaders (`animate-spin`) persist in 6 distinct component locations**, including a massive 96px spinning border ring in `Analysis.jsx` and spinning shields/activities.
6. **Tailwind configuration lacks essential design tokens**: `scale-101` does not exist in standard Tailwind, and the required ultra-soft diffused shadow (`0 4px 20px rgba(0,0,0,0.03)`) is not configured in `tailwind.config.js`.

---

## 1. Package Dependencies & Compatibility Survey

### Current Dependency Baseline (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "@tanstack/react-query": "^5.62.0",
    "axios": "^1.7.9",
    "react-dropzone": "^14.3.5",
    "lucide-react": "^0.460.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "vite": "^6.0.3"
  }
}
```

### Gap Analysis & Library Compatibility

| Library | Installed? | Recommended Version | Compatibility & Rationale |
|---|---|---|---|
| **`framer-motion`** | ❌ No | `^11.11.17` (or `^11.18.2`) | Fully battle-tested with React 18.3.1 and future-proofed for React 19. Provides `AnimatePresence`, `motion.div`, `layoutId`, SVG `pathLength` interpolation, and spring physics. |
| **`sonner`** | ❌ No | `^1.7.4` | Directly requested in R2 ("stacked toast notifications using `sonner`"). Supports stacked notifications, action buttons, swipe dismiss, rich styling, and zero Tailwind conflicts. |
| **`clsx`** | ❌ No | `^2.1.1` | Required for reliable conditional className composition. |
| **`tailwind-merge`** | ❌ No | `^2.6.0` | Required for merging Tailwind utility classes without specificity conflicts (`cn()` utility). |

### Current `react-hot-toast` Footprint (10 files requiring migration)
`react-hot-toast` is currently imported and used in:
1. `src/App.jsx` (line 4: `<Toaster />`)
2. `src/pages/Dashboard.jsx` (line 11: `toast.success`, `toast.error`)
3. `src/pages/Upload.jsx` (line 4: `toast.success`, `toast.error`)
4. `src/pages/Analysis.jsx` (line 22: `toast.success`)
5. `src/components/dashboard/ClaimsTable.jsx` (line 28: `toast.success`)
6. `src/components/dashboard/DashboardCharts.jsx` (line 14: `toast.success`)
7. `src/components/upload/BatchDropzone.jsx` (line 15: `toast.success`, `toast.error`)
8. `src/components/analysis/VerdictCard.jsx` (line 21: `toast.success`)
9. `src/components/analysis/AuditTimeline.jsx` (line 25: `toast.success`)
10. `src/components/analysis/AppealLetter.jsx` (line 19: `toast.success`)

*Recommendation:* Provide a centralized toast abstraction `src/utils/toast.js` or directly replace imports with `import { toast, Toaster } from 'sonner'`. The core API (`toast.success(msg)`, `toast.error(msg)`) is drop-in compatible. In `App.jsx`, replace `<Toaster position="top-right" ... />` with Sonner's `<Toaster position="top-right" expand={true} richColors closeButton />`.

---

## 2. Page Routing, Shell Layout & Transition Architecture

### Existing Routing Structure (`src/App.jsx`)
```jsx
// Lines 124-147 in src/App.jsx
<main className="flex-1 overflow-y-auto p-6 md:p-8">
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/upload" element={<Upload />} />
    <Route path="/analysis/:id" element={<Analysis />} />
    <Route path="/analysis" element={<Analysis />} />
    <Route path="*" element={<NotFound />} />
  </Routes>
</main>
```

### Deficiencies Observed
1. **Immediate DOM Destruction:** When navigating from `/` (Dashboard) to `/upload` or `/analysis/CLM-84920`, the outgoing component unmounts instantly with 0ms transition. The incoming page pops into existence, producing layout jerk.
2. **Mobile Drawer Has No Exit Animation:** In `src/App.jsx` (lines 98-105), `{mobileMenuOpen && <div className="md:hidden fixed inset-0 z-50 flex">...</div>}` unmounts instantly on close. The black backdrop does not fade out, and the sidebar does not slide back left.
3. **Topbar Search Dropdown Has No Transition:** In `src/components/common/Topbar.jsx` (lines 123-145), the quick search results box (`searchFocused && searchQuery.length > 0`) appears and disappears with no scale/fade animation.

### Recommended Implementation Strategy

#### A. Motion Page Wrapper (`src/components/common/PageMotion.jsx`)
Wrap routes inside `<AnimatePresence mode="wait">` using the current pathname key:
```jsx
import { motion } from 'framer-motion';

export const pageVariants = {
  initial: { opacity: 0, y: 8, filter: 'blur(2px)' },
  animate: { 
    opacity: 1, 
    y: 0, 
    filter: 'blur(0px)',
    transition: { duration: 0.22, ease: [0.25, 0.1, 0.25, 1.0] } 
  },
  exit: { 
    opacity: 0, 
    y: -8, 
    filter: 'blur(2px)',
    transition: { duration: 0.18, ease: [0.25, 0.1, 0.25, 1.0] } 
  }
};
```
In `App.jsx`:
```jsx
const location = useLocation();
...
<AnimatePresence mode="wait">
  <Routes location={location} key={location.pathname}>
    <Route path="/" element={<PageMotion><Dashboard /></PageMotion>} />
    <Route path="/upload" element={<PageMotion><Upload /></PageMotion>} />
    <Route path="/analysis/:id" element={<PageMotion><Analysis /></PageMotion>} />
    <Route path="/analysis" element={<PageMotion><Analysis /></PageMotion>} />
  </Routes>
</AnimatePresence>
```

#### B. Mobile Drawer Animation
```jsx
<AnimatePresence>
  {mobileMenuOpen && (
    <div className="md:hidden fixed inset-0 z-50 flex">
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        exit={{ opacity: 0 }} 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm" 
        onClick={() => setMobileMenuOpen(false)} 
      />
      <motion.aside 
        initial={{ x: -280 }} 
        animate={{ x: 0 }} 
        exit={{ x: -280 }} 
        transition={{ type: 'spring', damping: 28, stiffness: 300 }}
        className="w-64 bg-slate-900 text-white flex flex-col z-10 relative"
      >
        <SidebarContent />
      </motion.aside>
    </div>
  )}
</AnimatePresence>
```

---

## 3. Modals, Dialogs & Contextual Sidebars (Drawers)

### Audit Findings
- **Zero Modal/Dialog Components:** A grep search for `modal`, `dialog`, `Dialog`, `Modal` across `src/` yielded **0 matching files**.
- **Conflict of R2 Pattern:** Requirement R2 explicitly dictates:
  > *"Implement contextual sidebars (drawers) for claim details instead of full page navigations."*
- Currently in `src/components/dashboard/ClaimsTable.jsx` (lines 420-423, 725, 830):
  ```javascript
  const handleRowClick = (claimId) => {
    navigate(`/analysis/${claimId}`);
  };
  ```
  Every single row click in the claims ledger forcibly unmounts the dashboard and performs a heavy full-page route switch to `/analysis/:id`.
- In `src/components/analysis/VerdictCard.jsx` (lines 212-215):
  ```jsx
  {isExpanded && (
    <div className="border-t border-slate-100 bg-slate-50/50 p-5 space-y-4">
      ...
    </div>
  )}
  ```
  The accordion drawer expands and collapses abruptly without height animation.

### Recommended Implementation Strategy

#### A. Contextual Claim Detail Drawer (`src/components/dashboard/ClaimDetailDrawer.jsx`)
Create a right-docked drawer component triggered by clicking any claim in `ClaimsTable`:
- Backdrop: `motion.div` with subtle blur `backdrop-blur-[2px] bg-slate-900/30`.
- Sidebar: `motion.aside` sliding in from right:
  ```jsx
  initial={{ x: '100%' }}
  animate={{ x: 0 }}
  exit={{ x: '100%' }}
  transition={{ type: 'spring', damping: 30, stiffness: 320 }}
  ```
- Contents: Quick claim overview, patient/policy chips, Tripartite document status badges, monetary impact alert, quick ELA forensic score, and an explicit secondary CTA button `Open Full Forensic Dossier` linking to `/analysis/:id`.
- Keeps the auditor grounded in their claims table workflow without losing context or scroll position.

#### B. Reusable Animated Dialog Component (`src/components/common/Modal.jsx`)
Provide a reusable modal for confirmation actions, document inspection, or quick filters:
```jsx
<AnimatePresence>
  {isOpen && (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-slate-950/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ type: 'spring', damping: 25, stiffness: 350 }}
        className="relative z-10 w-full max-w-lg bg-white rounded-2xl p-6 shadow-elevation border border-slate-200"
      >
        {children}
      </motion.div>
    </div>
  )}
</AnimatePresence>
```

#### C. Smooth Accordion Drawers for `VerdictCard.jsx`
Replace plain `{isExpanded && <div>}` with `AnimatePresence`:
```jsx
<AnimatePresence initial={false}>
  {isExpanded && (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1.0] }}
      className="overflow-hidden border-t border-slate-100"
    >
      ...
    </motion.div>
  )}
</AnimatePresence>
```

---

## 4. Metric Cards & Upload Stepper Survey

### Metric Cards (`MetricCard.jsx` & `ExecutiveKpiCards.jsx`)
- **Current State:** Cards render inside a 4-column responsive grid (`ExecutiveKpiCards.jsx` line 33).
- **Hover:** Handled via `.card-enterprise-hover:hover { box-shadow: theme('boxShadow.card-hover'); }` in CSS, with icon `group-hover:scale-105`.
- **Deficiencies:**
  - No container-level staggered entrance. When the dashboard mounts, all 4 cards appear simultaneously.
  - Sparklines (`SparklineCurve`, lines 7-78) use static SVG cubic Bézier paths that do not animate.
  - Numbers are static formatted text without numeric tweening.

#### Recommended Animation Strategy:
1. **Container Stagger:** In `ExecutiveKpiCards.jsx`, wrap cards with a `motion.div` container with `variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.07 } } }}`.
2. **Card Lift Micro-Interaction:** `motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} whileHover={{ y: -3, transition: { duration: 0.2 } }}`.
3. **SVG Sparkline Drawing:** Animate the stroke using `motion.path`:
   ```jsx
   <motion.path 
     d={linePath} 
     initial={{ pathLength: 0 }} 
     animate={{ pathLength: 1 }} 
     transition={{ duration: 0.9, ease: 'easeOut' }}
     stroke={c.stroke} 
     strokeWidth="1.75" 
   />
   ```

### Upload Stepper & Intake Pipeline (`Upload.jsx` & `ReadinessCheck.jsx`)
- **Current State:**
  - Multi-step document intake tracks 3 slots: `HOSPITAL_BILL`, `INSURANCE_POLICY`, `REJECTION_LETTER`.
  - `ReadinessCheck.jsx` (lines 192-208) implements a 3-segment progress gauge using CSS classes (`transition-all duration-300`).
  - Pre-Analysis health check uses 4 checklist items (`checklistItems`, lines 135-160).
  - During analysis (`handleRunAudit` in `Upload.jsx`), a `setInterval` timer (lines 233-250) advances `extractionProgress` (0 to 100%) and updates `extractionStage` (0 to 3) through 4 phases:
    1. Uploading & Hashing
    2. Extracting OCR Tokens
    3. Verifying Clinical Schema
    4. Ready for Forensics
- **Deficiencies:**
  - Stage indicator changes in `ReadinessCheck.jsx` (lines 324-337) pop between colors with standard CSS classes.
  - Document cards in `Upload.jsx` (lines 331-341) swap slots with zero layout motion (`layout`).
  - Button state transitions between locked (`bg-slate-200`) and active (`bg-gradient-to-r`) pop instantly.

#### Recommended Animation Strategy:
1. **Framer-Motion Stepper Progress:** Use `motion.div` on the progress fill with spring damping:
   ```jsx
   <motion.div 
     className="h-full rounded-full bg-gradient-to-r from-sky-500 via-teal-400 to-emerald-400"
     initial={{ width: 0 }}
     animate={{ width: `${extractionProgress}%` }}
     transition={{ type: 'spring', damping: 20, stiffness: 100 }}
   />
   ```
2. **Animated Checklist Badges:** Checklist items (`ReadinessCheck.jsx`) should animate checkmarks with SVG `pathLength: 0 -> 1` upon file drop.
3. **Card Reordering & Removal Animation:** In `Upload.jsx`, wrap `DocumentCard` items in `<AnimatePresence>` with `motion.div layout initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}`.

---

## 5. Loading Indicators vs. Pulsing Skeleton Screens (Shimmers)

### Exact Inventory of Legacy Spinning Loaders (`animate-spin`)

| File Location | Line Number | Element & Current Implementation | Issue | Recommended Replacement |
|---|---|---|---|---|
| `src/pages/Analysis.jsx` | 174 | `<div className="absolute inset-0 border-4 border-brand-600 rounded-full border-t-transparent animate-spin" />` | Massive 96px spinning ring dominates the loading viewport. Feels dated and generic. | Replace with a high-fidelity **Auditor Scanner HUD**: multi-ring concentric clinical radar with soft pulse ripple + central glowing shield icon. |
| `src/pages/Analysis.jsx` | 197 | `<div className="w-4 h-4 border-2 border-brand-600 border-t-transparent rounded-full animate-spin flex-shrink-0" />` | Small spinner inside the 4-step analysis checklist. | Replace with a high-tech **Pulsing Status Beacon**: double ring beacon (`relative flex h-3 w-3` with `animate-ping bg-brand-400` + `bg-brand-600`). |
| `src/components/upload/DocumentCard.jsx` | 167 | `<div className="w-3 h-3 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />` | Spinning ring while document is extracting. | Replace with an **In-Card Progress Shimmer**: horizontal pulsing shimmer bar (`skeleton-shimmer h-2 w-24 rounded-full`). |
| `src/components/upload/ReadinessCheck.jsx` | 400 | `<Activity className="w-5 h-5 animate-spin text-white" />` | Activity icon spinning inside the main audit CTA button. | Replace with a subtle **Linear Shimmer Beam** scanning across the button face + glowing pulse. |
| `src/components/analysis/AuditTimeline.jsx` | 152 | `<ShieldCheck className={`w-4 h-4 ${isVerifying ? 'animate-spin' : ''}`} />` | The shield icon spins like a wheel when verifying cryptographic hashes. | Replace with a **Cryptographic Hash Scanner**: sequential dot sequence or laser scan bar passing across ledger blocks. |
| `src/components/common/StatusBadge.jsx` | 89 | `<Activity className="w-3 h-3 animate-spin text-sky-600" />` | Activity icon spinning for `ANALYZING`, `RUNNING`, `EXTRACTING`. | Replace with a refined **Clinical Pulse Beacon** (`span className="relative flex h-2 w-2"` with ping animation). |
| `src/pages/Dashboard.jsx` | 163 | `<RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />` | Standard spinning sync icon. | Refine with smooth rotation easing (`rotate-180 transition-transform duration-500`). |

### Pulsing Skeleton Shimmers Evaluation
The base shimmer utility already exists in `src/index.css` (lines 51-54):
```css
.skeleton-shimmer {
  @apply relative overflow-hidden bg-slate-200/80 before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/40 before:to-transparent;
}
```
And `src/components/common/Skeletons.jsx` provides:
- `SkeletonPulse`
- `MetricCardSkeleton`
- `TableSkeleton`
- `AnalysisSkeleton`

**Gaps to Fix:**
1. In `src/pages/Analysis.jsx`, the page currently renders both the giant spinner AND `AnalysisSkeleton` below it. When the spinner is replaced by the clinical radar HUD, the skeleton screen should integrate seamlessly with coordinated shimmer waves.
2. In `src/components/dashboard/ClaimsTable.jsx`, pagination and search updates currently show no inline shimmer state. A subtle table overlay shimmer (`TableShimmerOverlay`) will make filter changes feel seamless.
3. Add a dedicated `ClaimDrawerSkeleton` for the new contextual sidebar.

---

## 6. Hover States, Shadows & Micro-Interactions

### Audit of Existing Hover & Shadow Tokens

#### 1. Hover Scale Tokens
- **Current State:** Default Tailwind only provides `scale-95`, `scale-100`, `scale-105`, `scale-110`.
- **The Gap:** The project specification explicitly requires `scale-101` (`1.01`) for ultra-subtle enterprise card micro-interactions without distorting typography. Currently, `scale-101` is **undefined** in `tailwind.config.js`! Any attempt to use `hover:scale-101` currently fails to compile or evaluate.

#### 2. Diffused Shadows
- **Current State in `tailwind.config.js`:**
  ```javascript
  boxShadow: {
    'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'card': '0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.06)',
    'card-hover': '0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)',
    'elevation': '0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)',
    'inner-subtle': 'inset 0 1px 2px 0 rgba(0, 0, 0, 0.04)',
  }
  ```
- **The Gap:** Requirement R2 specifies:
  > *"Refine borders and shadows to use ultra-soft diffused styles (`0 4px 20px rgba(0,0,0,0.03)`) and 1px borders."*
  Neither `card` nor `card-hover` uses this ultra-soft diffused blur. A dedicated `diffused` shadow token must be added.

#### 3. Table Rows Micro-Interactions
- In `src/components/dashboard/ClaimsTable.jsx` (line 732):
  ```jsx
  className="group hover:bg-slate-50/90 transition-colors duration-150 cursor-pointer focus:outline-none focus:bg-sky-50/30"
  ```
  Hover only changes background color. There is no subtle elevation lift or border highlight.
  *Upgrade:* Add `hover:shadow-xs hover:border-slate-300/80 hover:bg-slate-50/95` and smooth easing.

#### 4. Buttons & Active Press Physics
- Currently buttons have inconsistent active states (`active:scale-[0.98]` in `ReadinessCheck.jsx`, but none in `ClaimsTable.jsx`, `Topbar.jsx`, or `Dashboard.jsx`).
- *Upgrade:* Standardize button utility class `.btn-press` with `active:scale-[0.98] transition-transform duration-100 ease-out`.

#### 5. Interactive Chips & Filter Tabs (Sliding Pill Indicators)
- Currently in `ClaimsTable.jsx` (lines 561-578) and `Analysis.jsx` (lines 303-395), switching tabs swaps background colors instantly with hard borders.
- *Upgrade:* Using framer-motion `layoutId="activeTabPill"`, an animated sliding indicator pill can fluidly glide between tab options as the user switches categories.

---

## 7. Recommended Tailwind Config Extensions

To support all required styles, `tailwind.config.js` should be updated with:
```javascript
// Additions to theme.extend:
scale: {
  '101': '1.01',
  '102': '1.02',
},
boxShadow: {
  'diffused': '0 4px 20px 0 rgba(0, 0, 0, 0.03)',
  'diffused-hover': '0 8px 25px 0 rgba(0, 0, 0, 0.05)',
  'diffused-card': '0 4px 20px 0 rgba(0, 0, 0, 0.03), 0 1px 2px 0 rgba(0, 0, 0, 0.02)',
},
transitionTimingFunction: {
  'enterprise': 'cubic-bezier(0.25, 0.1, 0.25, 1.0)',
}
```

And in `src/index.css`:
```css
.card-enterprise {
  @apply bg-white rounded-xl border border-slate-200/80 transition-all duration-200;
  box-shadow: theme('boxShadow.diffused');
}
.card-enterprise-hover {
  @apply hover:border-slate-300/90 hover:scale-101;
  transition: all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1.0);
}
.card-enterprise-hover:hover {
  box-shadow: theme('boxShadow.diffused-hover');
}
```

---

## 8. Step-by-Step Implementation Roadmap for Downstream Agents

| Phase | Target Module | Concrete Implementation Steps |
|---|---|---|
| **Phase 1: Dependencies & Design Tokens** | `package.json`, `tailwind.config.js`, `src/index.css` | 1. Install `framer-motion@^11.11.17`, `sonner@^1.7.4`, `clsx@^2.1.1`, `tailwind-merge@^2.6.0`.<br>2. Add `scale-101`, `boxShadow.diffused`, `boxShadow.diffused-hover` to `tailwind.config.js`.<br>3. Update `.card-enterprise` and `.card-enterprise-hover` in `src/index.css`.<br>4. Create `src/utils/cn.js` helper. |
| **Phase 2: Global Shell & Toast Migration** | `src/App.jsx`, `src/components/common/Topbar.jsx` | 1. Replace `react-hot-toast` with `sonner` `<Toaster position="top-right" richColors />`.<br>2. Migrate `toast.*` calls across the 10 files.<br>3. Wrap `<Routes>` in `<AnimatePresence mode="wait">` with `<PageMotion>` wrapper.<br>4. Add animated backdrop and sliding drawer to mobile menu.<br>5. Animate Topbar search dropdown. |
| **Phase 3: Contextual Drawer & Modal System** | `src/components/dashboard/ClaimDetailDrawer.jsx`, `src/components/common/Modal.jsx` | 1. Implement `ClaimDetailDrawer` with `AnimatePresence` and spring transition (`x: '100%' -> 0`).<br>2. Wire row clicks in `ClaimsTable.jsx` to open the drawer instead of full navigation.<br>3. Provide an explicit "View Full Dossier" button linking to `/analysis/:id`.<br>4. Add smooth height accordion animation to `VerdictCard.jsx`. |
| **Phase 4: Dashboard Bento Grid & Metric Animations** | `src/pages/Dashboard.jsx`, `ExecutiveKpiCards.jsx`, `MetricCard.jsx` | 1. Refactor dashboard container into a clean Bento Grid layout.<br>2. Add staggered entrance variants to `ExecutiveKpiCards`.<br>3. Animate SVG sparkline paths using `motion.path pathLength: 0 -> 1`.<br>4. Add `hover:scale-101` and `shadow-diffused-hover` to KPI cards. |
| **Phase 5: Stepper & Loader Hardening** | `src/pages/Analysis.jsx`, `ReadinessCheck.jsx`, `DocumentCard.jsx`, `AuditTimeline.jsx`, `StatusBadge.jsx` | 1. Replace the 96px giant spinner in `Analysis.jsx` with an Auditor Scanner HUD + coordinated skeleton.<br>2. Replace spinning icons in `StatusBadge`, `DocumentCard`, `ReadinessCheck`, and `AuditTimeline` with pulsing beacons and shimmer bars.<br>3. Enhance the upload stepper with spring progress and checklist checkmark animations. |
| **Phase 6: Verification & Test Regression** | `tests/runner.mjs`, Vite build | 1. Run `npm test` to verify all 72 E2E contract tests still pass (100%).<br>2. Run `npm run build` to verify bundle packaging with zero build errors.<br>3. Inspect console output and verify zero runtime errors. |

---

*Report prepared and compiled by `explorer_survey_deps_anim`.*
