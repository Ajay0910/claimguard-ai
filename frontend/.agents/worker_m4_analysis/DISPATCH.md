## 2026-09-17T19:13:26Z
You are worker_m4_analysis (teamwork_preview_worker).
Your working directory is: c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m4_analysis
Your task: Implement Milestone 4: Analysis & Forensics Hub (Features 12, 13, 14, 15, 16) in ClaimGuard AI Frontend.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity conflicts WILL be detected and your work WILL be rejected.

MANDATORY INPUTS TO READ:
1. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\ORIGINAL_REQUEST.md (Authoritative user requirements)
2. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_2\PROJECT.md (Project specifications)
3. Blueprints from our 2 explorers:
   - c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m4_financial_verdicts\handoff.md
   - c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m4_forensics_audit_appeal\handoff.md

WRITE OWNERSHIP & FILE BOUNDARIES:
You exclusively own and will create/modify:
- `src/components/analysis/FinancialDelta.jsx` (New file)
- `src/components/analysis/VerdictCard.jsx` (New file or overhaul)
- `src/components/analysis/ForensicsLab.jsx` (New file)
- `src/components/analysis/AuditTimeline.jsx` (New file)
- `src/components/analysis/AppealLetter.jsx` (New file)
- `src/pages/Analysis.jsx` (Complete overhaul into 4-tab clinical workspace)

DETAILED REQUIREMENTS TO IMPLEMENT:
1. **Feature 12: Executive Financial Delta & Reconciliation (`src/components/analysis/FinancialDelta.jsx`)**:
   - 4-metric executive financial summary (Billed Amount, Insurer Approved, Total Disallowed, Contested & Recoverable).
   - High-impact stacked visual proportion bar (percentage distribution of Billed vs Approved vs Disallowed vs Recoverable with clinical color tokens).
   - Itemized discrepancy breakdown cards with statutory citations (IRDAI Master Circular May 2024, Insurance Act § 45).
   - Currency formatted in INR (`formatINR`).

2. **Feature 13: Interactive Rule Verdicts & Statutory Engine (`src/components/analysis/VerdictCard.jsx`)**:
   - Categorized Tier 1 (Mandatory Statutory Conflicts) and Tier 2 (Clinical/Policy Inconsistencies) cards.
   - Proportional visual delta bar displaying Insurer calculation vs Statutory correct amount with strikethrough and recovery delta.
   - 1-click IRDAI statutory clause copy button (`navigator.clipboard.writeText`) with interactive "Copied!" feedback.
   - Severity badges (`FAIL / MISMATCH`, `REVIEW`, `PASS`), AI confidence score (e.g. 98%), and itemized clause references.
   - Category filter tabs (All, Tier 1 Statutory, Tier 2 Policy, Conflicts Only).

3. **Feature 14: Digital Forensics & Fraud Detection Lab (`src/components/analysis/ForensicsLab.jsx`)**:
   - ELA (Error Level Analysis) tamper score meter: Pure SVG 240-degree circular gauge (0-100) with needle, risk pill (Low / Moderate / Tamper Detected), and metadata analysis.
   - Interactive Heatmap Viewer with document vs forensic noise heatmap toggle, opacity slider, and bounding boxes around modified text blocks.
   - CGHS Official Tariff Benchmark Comparator: Dual horizontal bars comparing billed procedure charge vs CGHS official rate with variance percentage.
   - Clinical Consistency Matrix: Diagnostic code (ICD-10) cross-referenced against procedures and medications.

4. **Feature 15: Cryptographic SHA-256 Audit Trail (`src/components/analysis/AuditTimeline.jsx`)**:
   - Interactive chronological timeline across all pipeline blocks (Document Ingestion -> OCR -> NER -> Rule Engine -> Forensics Scan -> Ledger Commit).
   - Cryptographic SHA-256 block ledger with verification badge ("Ledger Hash Chain Verified"), block hash, previous hash link connectors, and one-click copy hash button.

5. **Feature 16: Formal Legal Appeal & Grievance Generator (`src/components/analysis/AppealLetter.jsx`)**:
   - Official NABH hospital legal letterhead addressed to Insurer / TPA Grievance Redressal Officer (GRO).
   - Embedded IRDAI circular citations, claim breakdown table, and legal dispute points.
   - Action controls: Copy to Clipboard, Print / PDF format view (with clean `@media print`), and editable draft textarea with character counter.

6. **4-Tab Workspace in `src/pages/Analysis.jsx`**:
   - Executive header with Patient Name, Claim ID, Policy Number, Auditor Risk Badge, and quick action buttons.
   - 4-tab switcher:
     * Tab 1: Financial Reconciliation & Rule Verdicts
     * Tab 2: Digital Forensics & Fraud Lab
     * Tab 3: Cryptographic Audit Trail
     * Tab 4: Legal Appeal & Grievance Generator
   - URL query parameter synchronization (`?tab=financial|forensics|audit|appeal`).
   - Loading skeletons and clean error state with retry.

VERIFICATION COMMANDS:
- `npm test`
- `node tests/run-stress-tests.mjs`
- `node tests/challenger-m2-table-stress.mjs`
- `npm run build`
Ensure all tests pass 100% and build succeeds with 0 errors.

OUTPUT:
- Write comprehensive handoff report to: c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m4_analysis\handoff.md
- Send message back to parent when done.
