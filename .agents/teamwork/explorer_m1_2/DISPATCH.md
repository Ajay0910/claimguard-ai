# Dispatch to Explorer M1-2: Evidence Ledger Schema & DB Integration

- **Role**: Data Architect & Provenance Schema Specialist
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_2\
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- **Project Scope**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md

## Objective
Design the concrete implementation for Feature F02 (Standalone Evidence Ledger Schema) and F04 (Document SHA-256 Hashing):
1. Design `backend/app/schemas/evidence_ledger.py` containing `EvidenceLedgerEntry` and `EvidenceLedger`:
   - Must capture: `entry_id`, `claim_id`, `document_id`, `document_hash` (SHA-256), `page_number`, `bounding_box` ([ymin, xmin, ymax, xmax]), `section`, `source_text`, `extracted_value`, `normalized_value`, `rule_id`, `formula`, `calculation_inputs`, `final_output`, `confidence`, `created_at`.
2. Inspect `backend/app/models/claim.py` and determine database schema additions (e.g. `EvidenceLedgerRecord` table or JSON serialization on `AnalysisRun` / `Claim`).
3. Design SHA-256 hash calculation in `backend/app/utils/file_handler.py` and storage in `Document` model upon upload in `backend/app/api/upload.py` and `backend/app/api/portal.py`.
4. Provide the exact implementation design in your `handoff.md` for the worker to implement.

## 2026-09-27T06:46:48Z
You are Explorer M1-2 (Data Architect & Provenance Schema Specialist).
Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_2\
Project root: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

Read:
1. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
2. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md
3. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_2\DISPATCH.md

Your task is to design the concrete implementation for F02 (Standalone Evidence Ledger Schema) and F04 (Document SHA-256 Hashing):
1. Design backend/app/schemas/evidence_ledger.py containing EvidenceLedgerEntry and EvidenceLedger.
2. Determine database model updates in backend/app/models/claim.py (document_hash column on Document, EvidenceLedgerEntry persistence).
3. Design SHA-256 hash calculation in backend/app/utils/file_handler.py and storage upon upload in backend/app/api/upload.py and backend/app/api/portal.py.
4. Write your design and concrete code snippets in handoff.md in your working directory.
5. Send message to orchestrator when done.

