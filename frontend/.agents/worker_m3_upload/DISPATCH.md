## 2026-09-18T00:27:00Z
You are worker_m3_upload (teamwork_preview_worker).
Your working directory is: c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\worker_m3_upload
Your task: Implement Milestone 3: Upload Studio & UX Polish (Features 9, 10, 11) in ClaimGuard AI Frontend.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity conflicts WILL be detected and your work WILL be rejected.

MANDATORY INPUTS TO READ:
1. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\ORIGINAL_REQUEST.md (Authoritative user requirements)
2. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_2\PROJECT.md (Project specifications)
3. Architectural and UX blueprints produced by our 2 explorers:
   - c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m3_upload\handoff.md
   - c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m3_ux\handoff.md

WRITE OWNERSHIP & FILE BOUNDARIES:
You exclusively own and will create/modify:
- `src/components/upload/BatchDropzone.jsx` (New file)
- `src/components/upload/DocumentCard.jsx` (New file)
- `src/components/upload/ReadinessCheck.jsx` (New file)
- `src/pages/Upload.jsx` (Complete overhaul)

DETAILED REQUIREMENTS TO IMPLEMENT:
1. **Feature 9: Dual-Mode Upload Studio (`src/components/upload/BatchDropzone.jsx`)**:
   - Mode A (Batch Multi-Drop): Smart multi-file drag-and-drop accepting 1 to 3 files at once. Employs regex filename heuristics (`/(bill|inv|invoice|discharge|hosp)/i` -> Hospital Bill; `/(policy|schedule|coverage|ins)/i` -> Policy; `/(rej|rejection|denial|deduct|settle|tpa)/i` -> Rejection Letter) with automatic slot assignment and fallback filling.
   - Mode B (Guided 3-Step): 3 distinct slotted drop targets (Hospital Bill, Insurance Policy, Rejection Letter) supporting non-blocking out-of-order intake.
   - Mode switcher pill toggle ("Batch Upload" vs "Guided 3-Step").
   - Strict file validation: max size 25MB (`26,214,400` bytes), MIME whitelist (`application/pdf`, `image/jpeg`, `image/png`, `image/tiff`), 0-byte check, and informative error toast on rejection.
   - Rich interactive states: active drop ring (`ring-4 ring-brand-500/25 border-brand-500 bg-brand-50/70`), rejected file crimson ring, hover transitions.

2. **Feature 10: Document Metadata & Inspection Cards (`src/components/upload/DocumentCard.jsx`)**:
   - Clean enterprise card displaying document slot title, original filename, format chip (PDF/PNG/JPG), formatted size (KB/MB), extraction status badge.
   - Action controls: Replace Document (opens file picker for this slot) and Remove Document.
   - Retag slot dropdown allowing auditors to reassign document type.

3. **Feature 11: Pre-Analysis Health Check & UX Transitions (`src/components/upload/ReadinessCheck.jsx`)**:
   - Pre-analysis visual readiness checklist:
     * Hospital Bill presence & line items status.
     * Policy presence & sum insured / deductible limits status.
     * Rejection Letter presence & deduction reasons status.
   - Dynamic readiness meter (0%, 33%, 66%, 100%) with status badge.
   - Fast-track 1-Click Apollo Hospital Benchmark Claim Loader: "Load Sample Apollo Hospital Claim" button that populates the 3 documents with sample data (`CLM-84920`), illuminates readiness to 100%, and activates the analysis trigger.
   - 4-Stage Extraction Progress Animation during upload/analysis initiation:
     `Uploading & Hashing` (0-25%) -> `Extracting OCR Tokens` (25-60%) -> `Verifying Clinical Schema` (60-85%) -> `Ready for Forensics` (85-100%).
   - "Run Claim Forensics & Audit" CTA button: disabled until required documents uploaded, animated on click, navigates to `/analysis/:claimId`.

4. **Integration in `src/pages/Upload.jsx`**:
   - Connect with `uploadDocument` in `src/services/api.js`.
   - Support seamless transition from upload to analysis hub.
   - Responsive high-density clinical layout matching enterprise standards.

VERIFICATION COMMANDS:
- `npm test`
- `node tests/run-stress-tests.mjs`
- `node tests/challenger-m2-table-stress.mjs`
- `npm run build`
Ensure 100% pass across all test suites and 0 build errors.
