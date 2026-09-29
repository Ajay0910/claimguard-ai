# Dispatch to Explorer Survey 2: Extraction Layer, VLM Cross-Verification, and Evidence Ledger

- **Role**: Codebase Researcher & Extraction/Provenance Specialist
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_2\
- **Project Root**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md

## Objective
Survey the ClaimGuard codebase specifically focusing on:
1. Document extraction pipeline: OCR, PDF parsing, Vision-Language Model (VLM) extractors, prompt structures, multi-document ingestion.
2. VLM Cross-verification and Confidence Scoring: how extraction results are validated, confidence calculation, how conflicting extractions across models or documents are handled.
3. Validation and Rejection: mechanisms to reject low-confidence or mathematically inconsistent outputs (e.g., room rate, total claim amount, line-item arithmetic vs grand total).
4. Ubiquitous Evidence Ledger: provenance tracking data structures (document ID, page number, bounding box/section, source text, extracted value, normalized value, rule ID, formula, calculation inputs, confidence).
5. Identify all failure modes, hardcoded heuristics, hallucination risks, missing cross-checks, and required architectural changes to fulfill requirements R3 and R5 in ORIGINAL_REQUEST.md.

## Scope Boundaries
- READ-ONLY investigation. Do NOT modify any source code or test files.
- Produce a comprehensive survey report at `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_2\handoff.md`.

## Deliverables
- Write `handoff.md` in your working directory containing:
  - Exact file locations, module boundaries, data classes/schemas.
  - Precise inventory of current extraction flows, confidence mechanisms, and provenance tracking.
  - Concrete gap analysis vs Requirements R3, R5.
  - Proposed architectural redesign / refactoring recommendations for cross-verification and evidence ledger.
- When done, send a message to orchestrator with a summary and link to your `handoff.md`.

## 2026-09-27T06:36:05Z
You are Explorer Survey 2 (Extraction Layer, VLM Cross-Verification, and Evidence Ledger Specialist).
Your working directory is: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_2\
Project root: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

First, read:
1. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
2. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_2\DISPATCH.md

Your task is to conduct a thorough, read-only survey of the ClaimGuard codebase:
1. Document extraction pipeline: OCR, PDF parsing, Vision-Language Model (VLM) extractors, prompt structures, multi-document ingestion.
2. VLM Cross-verification and Confidence Scoring: how extraction results are validated, confidence calculation, how conflicting extractions across models or documents are handled.
3. Validation and Rejection: mechanisms to reject low-confidence or mathematically inconsistent outputs (e.g., room rate, total claim amount, line-item arithmetic vs grand total).
4. Ubiquitous Evidence Ledger: provenance tracking data structures (document ID, page number, bounding box/section, source text, extracted value, normalized value, rule ID, formula, calculation inputs, confidence).
5. Identify all failure modes, hardcoded heuristics, hallucination risks, missing cross-checks, and required architectural changes to fulfill requirements R3 and R5 in ORIGINAL_REQUEST.md.

Produce your detailed report in:
C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_2\handoff.md

When complete, call send_message to report back to parent orchestrator with your key findings and notification that handoff.md is ready.

