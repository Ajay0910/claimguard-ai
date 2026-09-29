# Handoff Report: UX, Visual Design & Data Visualization Survey

**Author**: `explorer_survey_ux`  
**Date**: 2026-09-17T14:52:00Z  
**Recipient**: `orchestrator_1` (parent)  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation

A full code audit of `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend` and corresponding backend schema contracts in `c:\Users\krusheek\Desktop\SIH\claimguard-ai\backend` revealed critical UX deficits, missing visualizations, unrendered backend capabilities, and generic template styling.

### 1.1 Styling Foundation & Design Tokens
- **`tailwind.config.js` (lines 1-12)**:
  ```javascript
  export default {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
      extend: {}, // Completely empty! No brand tokens, no semantic status colors
    },
    plugins: [],
  }
  ```
  The application utilizes default vanilla Tailwind CSS colors with zero custom enterprise healthcare tokens (e.g., no clinical slate/navy hierarchy, no distinction between fraud risk severity vs financial variance, no typography sizing for financial figures or ICD-10 medical codes).
- **`src/index.css` (lines 1-10)**:
  Only 10 lines of boilerplate CSS (`@tailwind base; @apply bg-slate-50 text-slate-900;`). No custom scrollbar styling, no glass/card elevation utility classes, no font imports (e.g. Inter, Plus Jakarta Sans, JetBrains Mono for monetary/codes), and no animation keyframes.
- **Dependencies (`package.json`, lines 11-20)**:
  `lucide-react`, `react-dropzone`, `react-hot-toast`, `@tanstack/react-query`, `axios`, `react-router-dom`. **No chart library** is installed (`recharts` or similar is missing), resulting in zero interactive graphs across the entire app.

### 1.2 Global Shell & Navigation (`src/App.jsx`)
- **App Layout (lines 65-115)**:
  - Sidebar is a plain dark slate column (`bg-slate-900 w-64`). No logo branding with tagline, version tag (`v2.4 Enterprise`), or backend connectivity status pill.
  - Sidebar items (`Dashboard`, `Upload Claims`, `Analysis`) use basic hover transitions without active indicator accents (e.g., border stripes, glow badges).
  - Bottom controls ("Settings", "Profile") at lines 52-61 are dummy static `<button>` elements with no modals, pages, or popover behavior.
  - **Missing Desktop Top Header Bar**: There is NO topbar on desktop. No breadcrumbs, no global claim search bar (by Claim ID, Patient, Hospital, or Policy #), no active facility/TPA context selector, no notification center, and no user identity / auditor profile avatar (`Dr. S. Jenkins, CPC — Senior Medical Auditor`).
  - Layout has fixed padding `p-8` with no max-width boundaries or responsive container breakpoints.
  - 404 page (lines 101-108) is a minimal centered text block with no helpful links or navigation aid.

### 1.3 Dashboard Page (`src/pages/Dashboard.jsx` & `src/components/StatsCard.jsx`)
- **Backend Schema Mismatch / Bug**:
  In `Dashboard.jsx` (line 35):
  ```javascript
  { label: 'Underpayment Recovered', value: formatInr(statsData.total_amount_recovered || 0), ... }
  ```
  However, `backend/app/api/upload.py` (lines 130-138) returns:
  ```python
  return {
      "total_claims": total_claims,
      "pending_analysis": pending_analysis,
      "mismatches_found": mismatches_found,
      "total_recovered_amount": total_recovered_amount  # <--- Field is total_recovered_amount!
  }
  ```
  Because the key name is mismatched (`total_amount_recovered` vs `total_recovered_amount`), this metric always fell back to `0.00`!
- **Hardcoded Trends (lines 33-36)**:
  All four stats cards use static hardcoded trend percentages (`+12%`, `+5%`, `+18%`, `-2`) and hardcoded string `"from last month"` (`StatsCard.jsx`, line 18).
- **Generic AI Template Look in `StatsCard.jsx` (lines 1-25)**:
  Every card uses identical icon background colors (`bg-blue-50 text-blue-600`), even for alerts (`AlertTriangle`) and currency (`IndianRupee`). No visual priority, no sparkline, and no semantic color differentiation.
- **Complete Lack of Data Visualizations**:
  The dashboard has zero charts. No claim outcome distribution (Clean vs Mismatch Detected vs Fraud Flagged), no monthly recoverable savings trajectory, no rule conflict distribution (e.g. Proportionate Deduction, Moratorium clause, Mental Health parity), and no turnaround time metrics.
- **Recent Claims Table Deficiencies (lines 90-155)**:
  - No search bar to search claims.
  - No status filter tabs (e.g., All, Pending, Analyzing, Mismatch Detected, Completed, Failed).
  - No sorting by Date, Impact, Patient, or Status.
  - No pagination or row count indicator (e.g. "Showing 10 of 124 claims").
  - The "Documents" column (lines 120-125) renders raw text `FileSearch 0/3` or `2/3`. It provides zero information about *which* document is missing (Hospital Bill vs Policy vs Rejection Letter).
  - Monetary impact column (lines 127-133) renders plain text INR with no visual magnitude bar or indicator.
  - Skeleton loader (lines 51-73) consists of crude pulsing gray rectangles that do not match the real table structure.

### 1.4 Document Upload Flow (`src/pages/Upload.jsx` & `src/components/FileUploader.jsx`)
- **Rigid Linear Stepper (lines 19-23, 70-94)**:
  Users are locked into a strict sequential 3-step wizard (Step 1: Hospital Bill → Step 2: Insurance Policy → Step 3: Rejection Letter). An auditor possessing all 3 PDFs cannot batch drop them or upload them out of order.
- **No Document Management / Preview**:
  - No file preview (thumbnail or PDF page viewer).
  - No file size badge, MIME type verification chip, or OCR confidence estimation.
  - Once a document is uploaded, there is no "Replace" or "Remove" button on that step, only a text link "Next Step".
- **Dropzone UI (`FileUploader.jsx`, lines 20-50)**:
  Standard generic dashed box with standard `UploadCloud` icon. Lacks drag-over pulsing animations, format validation chips, or multi-file queue visibility.
- **Final Pre-Analysis Confirmation (lines 122-166)**:
  Renders a basic green checkmark with an unstyled list of file names in a gray box, and a single blue button. Lacks document metadata review, extraction preview, or parameter toggles.

### 1.5 Claim Analysis & Forensics Hub (`src/pages/Analysis.jsx` & `src/components/VerdictCard.jsx`)
- **CRITICAL OMISSION — Forensics Data is Completely Ignored**:
  The backend produces rich forensics data in `backend/app/forensics/engine.py` and `app/schemas/forensics_result.py`:
  1. `ELAResult`: Error Level Analysis with `tamper_score` (0-100), `assessment` (CLEAN, SUSPICIOUS, HIGHLY_SUSPICIOUS), `heatmap_url`, and `suspicious_regions`.
  2. `BillAnomalyFlag`: Length of stay (LOS) padding, tariff deviation (>2x, >3x CGHS benchmark), duplicate billing, itemization mismatch.
  3. `ConsistencyFlag`: Clinical contradictions (e.g. Cataract surgery billed with Cardiology drugs).
  4. `MetadataFlag`: PDF/Image tampering software traces (Photoshop, GIMP), altered timestamps.
  5. `AuditTrail`: Cryptographically hashed SHA-256 chain verification (`/api/reports/{claim_id}/audit-trail`).
  **Current frontend status**: In `Analysis.jsx`, **ZERO** of this forensics data is displayed! The entire forensics engine output is discarded and never shown to the user.
- **Rule Verdicts Display (`VerdictCard.jsx`, lines 1-116)**:
  - Displays as basic collapsible cards with raw text finding strings.
  - Does not visually contrast Insurer Calculation vs Correct Calculation with a delta bar or difference pill.
  - Lacks rule identification badges (e.g. `RULE-001: Proportionate Deduction (IRDAI Sec 45)`).
  - No copy button for legal citations (`regulatory_citation`).
  - Monetary impact is shown only as a tiny red pill (`Impact: ₹14,000.00`).
- **Overall Verdict Summary (lines 153-197)**:
  - Generic amber/green banner with 3 centered numbers in `bg-slate-50`.
  - No visual financial waterfall chart (Claimed → Insurer Approved → Disallowed → Recoverable).
  - AI confidence is rendered as a static or single number without explainability or document attribution.
- **Grievance Appeal Letter UX Bug & Presentation (lines 209-234)**:
  - In `handleDraftAppeal` (line 63):
    ```javascript
    setDraftAppeal(draft.content || draft.appeal_letter || draft.draft || 'Draft generated successfully.')
    ```
    However, the backend endpoint `/api/reports/{claim_id}/appeal` (`backend/app/api/reports.py`, line 71) returns `{ "appeal_text": ... }`! The keys `content`, `appeal_letter`, and `draft` do not exist in the backend response, causing it to fall back to the placeholder string.
  - When displayed, the appeal is dumped in an unstyled raw monospaced `div` (`h-64 overflow-y-auto`). It lacks legal letter formatting, recipient addresses, an edit mode, PDF download, or clipboard copy buttons.
- **Loading & Error UX (lines 75-121)**:
  - Loading state shows a generic spinner with 4 hardcoded checklist items, rather than real-time WebSocket / polling progress.
  - Error state (`status === 'FAILED'`) is a plain red warning icon with a text link back to home, offering no error diagnostics or retry button.

---

## 2. Logic Chain

1. **Premise 1**: Enterprise healthcare software (e.g., Epic Systems, Cerner, Optum, Oscar Health) demands high information density, clear visual hierarchy, authoritative clinical/statutory color semantics, and defensible auditability.
2. **Premise 2**: Claim auditors and insurance grievance specialists cannot rely on opaque AI verdicts; they require visual delta comparisons (Insurer calculation vs IRDAI statutory benchmark), document-level provenance, and forensic tampering evidence (such as ELA heatmaps and tariff benchmark comparisons).
3. **Premise 3**: The current frontend was built as a lightweight MVP prototype:
   - It relies on bare Tailwind defaults with zero theme extensions.
   - It lacks charts, visual comparative bars, and interactive data visualization.
   - It omits the backend's core value propositions: ELA digital forensics, CGHS tariff benchmarking, clinical consistency checks, and cryptographic SHA-256 audit logging.
   - It suffers from API contract key mismatches (`total_recovered_amount` vs `total_amount_recovered`, `appeal_text` vs `draft.content`).
4. **Conclusion**: To eliminate the generic "AI prototype" aesthetic and achieve enterprise healthcare production standards, the frontend requires:
   - A standardized design token system (slate-900 midnight, medical teal/cyan, crisp risk status tokens).
   - An enterprise layout shell (desktop top navigation with global claim search, breadcrumbs, auditor persona, and system API health monitor).
   - A data-driven Dashboard with visual KPI metrics, interactive SVG/Recharts visualizations (claim status distribution, recovery timeline, rule conflict frequency), and a searchable, sortable claims data table with multi-document status chips.
   - A versatile Upload Studio supporting both batch multi-file drop and stepped modes with file metadata inspection and OCR extraction status.
   - A multi-tab Claim Analysis & Forensics Hub featuring an Executive Financial Reconciliation waterfall, Visual Rule Verdicts with delta comparison bars, an ELA Tamper & Forensics Lab with heatmap inspection, a Cryptographic Audit Trail, and a formal IRDAI Grievance Letter Generator.

---

## 3. Caveats

1. **Charting Library Dependency**: The current `package.json` does not include `recharts`. The implementation phase can either install `recharts` (`npm install recharts`) for full chart features or utilize clean SVG/CSS chart primitives. Recommending `recharts` ensures production-grade responsiveness and tooltips.
2. **Live Backend Execution**: Investigation was conducted by static code analysis and schema inspection. In production, ELA heatmap image generation requires OpenCV (`cv2`) and Pillow on the backend. The frontend must gracefully handle claims where ELA heatmaps are pending or unavailable.
3. **Responsive Breakpoints**: The audit focuses primarily on desktop workstations (1280px to 1920px+), which is the standard viewport for enterprise claims auditors, while preserving mobile drawer responsiveness.

---

## 4. Conclusion & Enterprise Redesign Specifications

### 4.1 Enterprise Healthcare Design System (Design Tokens)

#### 4.1.1 Color Palette
- **Primary / Brand**:
  - `brand-navy`: `#0F172A` (Slate 900) - Primary header, dark sidebar, text emphasis.
  - `brand-accent`: `#0284C7` (Sky 600) / `#2563EB` (Blue 600) - Interactive triggers, primary buttons.
  - `medical-teal`: `#0D9488` (Teal 600) / `#14B8A6` (Teal 500) - Healthcare verified signals, policy compliance.
- **Risk & Status Semantics**:
  - **Match / Clean / Pass**: Background `#ECFDF5` (Emerald 50), Border `#A7F3D0` (Emerald 200), Text `#047857` (Emerald 700), Accent `#10B981`.
  - **Mismatch / Discrepancy / Recoverable**: Background `#FEF3C7` (Amber 50), Border `#FDE68A` (Amber 200), Text `#B45309` (Amber 700), Accent `#F59E0B`.
  - **High Risk / Fraud / Fail**: Background `#FEF2F2` (Rose 50), Border `#FECDD3` (Rose 200), Text `#BE123C` (Rose 700), Accent `#F43F5E`.
  - **Pending / Analyzing**: Background `#EFF6FF` (Blue 50), Border `#BFDBFE` (Blue 200), Text `#1D4ED8` (Blue 700), Accent `#3B82F6`.
- **Surfaces & Borders**:
  - App background: `#F8FAFC` (Slate 50).
  - Card background: `#FFFFFF` (White) with subtle border `#E2E8F0` (Slate 200) and shadow `shadow-xs` / `shadow-sm`.
  - Hover states: `hover:border-slate-300 hover:shadow-md transition-all duration-200`.

#### 4.1.2 Typography & Hierarchy
- **Font Stack**: `Inter`, system-ui, -apple-system, sans-serif.
- **Monospace Stack**: `JetBrains Mono`, `ui-monospace`, monospace (for Claim IDs, ICD-10 codes, Indian Rupee currency figures, and regulatory clause citations).
- **Type Scale**:
  - Page Titles: `text-2xl font-bold tracking-tight text-slate-900`.
  - Section Headings: `text-base font-semibold text-slate-800 tracking-tight`.
  - Financial KPI Numbers: `text-3xl font-extrabold tracking-tight font-mono`.
  - Body Text: `text-sm text-slate-600 leading-relaxed`.
  - Metadata / Badges: `text-xs font-semibold uppercase tracking-wider`.

---

### 4.2 Application Shell & Navigation Redesign

```
+-----------------------------------------------------------------------------------------------+
| SIDEBAR               | TOPBAR: Breadcrumb | Global Claim Search [CLM-...] | Tenant | Auditor |
| [Shield] ClaimGuard AI |-----------------------------------------------------------------------|
| Enterprise v2.4       |                                                                       |
|                       |  PAGE CONTENT:                                                        |
| [Grid] Dashboard      |  - Executive KPI Hero                                                 |
| [Upload] Upload Studio|  - Advanced Data Visualizations (Donut, Waterfall, Bar)               |
| [Search] Claims Audit |  - Claims Data Table (Search, Filter Tabs, Multi-Doc Pills, Actions)  |
|                       |                                                                       |
| --------------------- |                                                                       |
| [Circle] API: Online  |                                                                       |
+-----------------------------------------------------------------------------------------------+
```

1. **Top Header Bar**:
   - **Breadcrumbs**: e.g., `Dashboard / Claims / CLM-84920`.
   - **Global Search Input**: Interactive search field with keyboard shortcut (`Ctrl + K`) allowing immediate lookup by Claim ID, Patient Name, Hospital, or Policy Number.
   - **Facility / Tenant Indicator**: `St. Jude Multi-Specialty Hospital — TPA Auditing Desk`.
   - **Auditor Persona Profile**: Avatar, name ("Dr. Aditi Sharma, CPC"), role badge ("Senior Claims Auditor").
2. **Sidebar Enhancements**:
   - Version badge `v2.4 Production`.
   - Active route styling: `#0284C7` (Sky-600) accent border indicator, clean high-contrast white text, subtle active background.
   - Real-time Backend Health Indicator: Green pulsing ping dot with `API Online (Connected)`.

---

### 4.3 Page-by-Page Redesign Specifications

#### 4.3.1 Dashboard Page (`Dashboard.jsx`)
1. **Executive Financial Hero**:
   - **Card 1: Total Claims Analyzed**: Total volume + subtext showing processing velocity.
   - **Card 2: Unfair Deductions / Mismatches**: Number of flagged claims + mismatch rate percentage (`34.2% discrepancy rate`).
   - **Card 3: Underpayment Recoverable**: Fixed API key mapping (`statsData.total_recovered_amount`) formatted in INR (`₹X,XX,XXX.00`), with green accent badge and visual variance indicator.
   - **Card 4: Active Analysis Pipeline**: Claims currently undergoing OCR extraction and rule engine evaluation.
2. **Data Visualizations Section (New Component `DashboardCharts.jsx`)**:
   - **Chart A (Claims Status Breakdown)**: Semi-donut or donut chart categorizing claims into `No Mismatch (Approved)`, `Unfair Deductions Found`, `Review Recommended`, and `Forensic Alert`.
   - **Chart B (Financial Recovery Trend / Recovery Waterfall)**: Visual bar / area chart comparing `Total Amount Billed` vs `Insurer Approved` vs `Recoverable Underpayment`.
   - **Chart C (Frequent Rule Conflicts)**: Horizontal progress/bar chart highlighting top conflict categories:
     - Room Rent Proportionate Deductions (IRDAI Circular 2020)
     - Moratorium Period Breaches (Section 45)
     - Mental Health Parity Deductions (MHA 2017)
     - Unbundled Surgical & Anesthesia Consumables
3. **Enterprise Claims Table**:
   - **Filter Controls**: Quick-filter pill tabs (`All (128)`, `Discrepancies (42)`, `Under Review (15)`, `Clean (71)`).
   - **Search & Sort**: Real-time client-side filter by Claim ID or Patient Name; sortable table headers (`Claim ID`, `Date`, `Impact`).
   - **Multi-Document Verification Pill**: Replace `0/3` text with 3 micro-badges indicating specific document upload status:
     - `BILL` (Hospital Bill): Green if uploaded, Gray if missing.
     - `POL` (Insurance Policy): Green if uploaded, Gray if missing.
     - `REJ` (Rejection Letter): Green if uploaded, Gray if missing.
   - **Impact Visualization**: Highlight monetary impact with amber/rose badges and mini bar indicator proportional to max claim value.
   - **Density & Pagination**: Show pagination footer (`Showing 1 - 10 of 128 claims`, Prev / Next buttons).

#### 4.3.2 Upload Studio Page (`Upload.jsx`)
1. **Dual Upload Mode**:
   - **Batch Upload Zone**: Allow auditors to drag and drop all 3 documents at once into a smart multi-file dropzone that auto-classifies or lets users tag document types via dropdown pills.
   - **Guided Stepper Mode**: Maintain a stepped option for first-time users, but with non-blocking navigation (ability to jump to any step, replace a single file, or preview without re-uploading the entire claim).
2. **Document Card Inspection**:
   - For each uploaded document, display:
     - File icon (PDF / Image).
     - File name and formatted size (`1.8 MB`).
     - Upload timestamp.
     - Document type badge (`HOSPITAL_BILL`, `INSURANCE_POLICY`, `REJECTION_LETTER`).
     - Quick "View/Preview" and "Replace" actions.
3. **Pre-Analysis Health Check**:
   - Visual checklist confirming required inputs:
     - `[✓] Hospital Bill attached (14 line items detected)`
     - `[✓] Insurance Policy attached (Sum insured ₹5,00,000)`
     - `[✓] Rejection / Settlement Letter attached (Deduction reasons detected)`
   - Prominent, high-contrast action button: `Start AI Cross-Verification & Forensics`.

#### 4.3.3 Claim Analysis & Forensics Hub (`Analysis.jsx`)

The redesigned Claim Analysis view must be organized into a **Unified 4-Tab Workspace**:

```
+---------------------------------------------------------------------------------------------------+
| CLAIM HEADER: CLM-73921 | Patient: Ramesh Gupta | Hospital: Apollo Health | Policy: Star Health   |
| Status: MISMATCH DETECTED | Recovery Potential: ₹42,500 | AI Confidence: 96%                     |
| [Download PDF Report] [Copy Appeal Draft] [Audit Trail Hash]                                      |
+---------------------------------------------------------------------------------------------------+
|  [Tab 1: Financial & Rules]  |  [Tab 2: Forensics & Tampering]  |  [Tab 3: Audit Trail]  |  [Tab 4: Appeal]
+---------------------------------------------------------------------------------------------------+
```

1. **Executive Financial Delta Summary**:
   - High-impact financial comparison bar:
     - `Billed Amount: ₹1,24,000`
     - `Insurer Approved: ₹68,000` (Red/Disallowed: ₹56,000)
     - `Correct Statutory Payable: ₹1,10,500`
     - `Wrongfully Deducted (Recoverable): ₹42,500`
   - Visual comparison bar showing the proportion of approved vs wrongfully deducted vs legitimate policy co-pay.

2. **Tab 1: Rule Engine Verdicts (`VerdictCard.jsx` Redesign)**:
   - Categorization by Statutory Tier:
     - **Tier 1: Regulatory Conflicts** (Proportionate deduction conflicts, Moratorium clause conflicts, Mental Health parity).
     - **Tier 2: Disallowed Line Items & Tariff Mismatches** (Unbundled anesthesia, non-medical charges).
   - **Interactive Comparison Widget**:
     - Visual delta slider/bar comparing `Insurer Paid (₹0)` vs `Correct Calculation (₹14,000)`.
     - Direct IRDAI clause quotation with one-click `Copy Citation` button.
     - `Add to Appeal Letter` toggle switch.

3. **Tab 2: Digital Forensics & Fraud Detection Hub (NEW)**:
   - **Tamper Score Meter**: Semi-circular gauge or segmented meter showing score (0 to 100) and assessment badge (`CLEAN`, `SUSPICIOUS`, `HIGHLY SUSPICIOUS`).
   - **Error Level Analysis (ELA) Heatmap Viewer**: Side-by-side or tabbed image viewer showing:
     - Left: Original Document Page / Crop.
     - Right: ELA Heatmap (highlighting resaved/cloned digital tampering regions in bright magenta/yellow).
   - **Bill Anomaly & CGHS Benchmark Comparator**:
     - Visual bar comparing hospital billed rates against CGHS benchmark maximums (e.g. ICU Room Rent: Billed ₹18,000/day vs CGHS Benchmark ₹5,000/day).
     - Length of stay (LOS) padding flag indicator.
   - **Clinical Consistency Matrix**:
     - Alerts for contradictory clinical treatments (e.g. Diagnostic test vs Prescribed medicines).
   - **Document Metadata Inspector**:
     - Table of file creation dates, modification software tags (e.g. `Adobe Photoshop 2023 detected`), and author discrepancies.
   - **Statutory Regulatory Disclaimer**: Prominently display IRDAI automated review disclaimer.

4. **Tab 3: Cryptographic Audit Trail (NEW)**:
   - Provenance status: `SHA-256 Chain Verified [Valid Block Integrity]`.
   - Interactive chronological timeline of all pipeline events:
     - `Document Uploaded` (with file hash)
     - `VLM Text & Table Extraction Completed`
     - `Forensics & ELA Analysis Ran`
     - `Rule Engine Executed`
     - `Report & Grievance Generated`

5. **Tab 4: Formal Legal Appeal & Grievance Generator**:
   - Correct the API field mapping bug: use `draft.appeal_text`.
   - Render as a formal legal document with hospital letterhead styling:
     - To: Grievance Redressal Officer (GRO), Insurer Name
     - Subject: Formal Grievance regarding Wrongful Claim Deduction for Claim #...
     - Structured sections: Patient Details, Policy Terms, Specific Clauses Violated, Financial Demand Table.
   - **Actions**: `Copy to Clipboard`, `Edit Text`, `Download PDF / Print`.

---

### 4.4 UX Transitions, Loading Skeletons & Error Handling

1. **Realistic Skeleton Screens**:
   - Replace pulsing gray boxes with structured skeleton components that mirror exact card, table, and gauge geometries.
2. **Graceful Error States**:
   - Replace generic red error toasts with contextual error cards featuring:
     - Explanatory human-readable error message.
     - `Retry Request` action button.
     - Technical diagnostic toggle (displaying status code and request ID).
3. **Empty States**:
   - Illustrated empty states with actionable primary buttons (`Upload your first claim`, `Load Demo Sample Claim`).

---

## 5. Verification Method

To verify these findings and validate future implementations:

1. **Build Verification**:
   ```bash
   cd c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend
   npm run build
   ```
   Must compile cleanly without Vite / JSX bundle errors.
2. **API Field Consistency Verification**:
   Inspect network calls or API responses:
   - Ensure `Dashboard.jsx` maps `total_recovered_amount` correctly from `/api/stats`.
   - Ensure `Analysis.jsx` retrieves `appeal_text` correctly from `/api/reports/{id}/appeal`.
   - Ensure `Analysis.jsx` accesses `result.forensics` from `/api/analyze/{id}/result`.
3. **Visual Quality Inspection Checklist**:
   - [ ] No generic AI boilerplate styles; typography uses cohesive hierarchy (Inter + JetBrains Mono for monetary/codes).
   - [ ] Dashboard features at least 2 distinct data visualizations (e.g., status donut and monetary recovery trend/bar).
   - [ ] Upload studio allows reviewing file metadata and offers smooth transitions.
   - [ ] Analysis view renders all backend forensics results (Tamper Score, ELA Heatmap, CGHS Benchmarks, Clinical Consistency).
   - [ ] Loading states display structured skeletons; error states offer retry capability.
