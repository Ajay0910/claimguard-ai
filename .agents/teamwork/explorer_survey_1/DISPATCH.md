# Dispatch to Explorer Survey 1: Adjudication, Rules Engine, and Financial Reconciliation

- **Role**: Codebase Researcher & Adjudication Architecture Specialist
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1\
- **Project Root**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md

## Objective
Survey the ClaimGuard codebase specifically focusing on:
1. Backend Adjudication & Rules Engine (`backend/app/` or relevant paths).
2. Financial reconciliation logic: how expected payable, insurer payable, and disputed amounts are computed. Search for any generic heuristic overrides (e.g., hardcoded 70% appeal probability, heuristic scoring overriding financial arithmetic).
3. Strict Policy-Rule Applicability & Ordering: room rent capping, proportionate deduction thresholds (>1.15), immune categories (OT, Cath Lab, ICU, medicines, etc.), copay application order, deductibles.
4. Moratorium & Clinical Reasoning: 60-month moratorium rules, continuous coverage, portability/migration credits, clinical firewall vs document discrepancy segregation.
5. Identify all failure modes, bugs, technical debt, and required architectural changes to fulfill requirements R1, R2, and R4 in ORIGINAL_REQUEST.md.

## Scope Boundaries
- READ-ONLY investigation. Do NOT modify any source code or test files.
- Produce a comprehensive survey report at `C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1\handoff.md`.

## Deliverables
- Write `handoff.md` in your working directory containing:
  - Exact file locations, module boundaries, class/function definitions.
  - Precise inventory of existing rules, calculation steps, and heuristic overrides discovered.
  - Concrete gap analysis vs Requirements R1, R2, R4.
  - Proposed architectural redesign / refactoring recommendations.
- When done, send a message to orchestrator with a summary and link to your `handoff.md`.
