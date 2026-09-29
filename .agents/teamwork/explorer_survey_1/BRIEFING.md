# BRIEFING — 2026-09-27T06:45:00Z

## Mission
Survey the ClaimGuard codebase regarding Adjudication, Rules Engine, and Financial Reconciliation to identify heuristic overrides, rule applicability/ordering gaps, moratorium/clinical reasoning issues, and produce a detailed gap analysis and architectural recommendation report.

## 🔒 My Identity
- Archetype: explorer
- Roles: Codebase Researcher & Adjudication Architecture Specialist
- Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1
- Original parent: 8a31858b-a7fa-4833-b69a-793b18272149
- Milestone: Survey & Gap Analysis (R1, R2, R4)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT modify any source code or test files
- Target requirements: R1 (Deterministic Financial Reconciliation), R2 (Strict Policy-Rule Applicability & Ordering), R4 (Moratorium & Clinical Reasoning)

## Current Parent
- Conversation ID: 8a31858b-a7fa-4833-b69a-793b18272149
- Updated: not yet

## Investigation State
- **Explored paths**: `backend/app/api/analysis.py`, `backend/app/api/portal.py`, `backend/app/rules/` (`engine.py`, `proportionate_deduction.py`, `copay_rule.py`, `deductible_rule.py`, `waiting_period.py`, `clause_timeline.py`, `clinical_firewall.py`, `identity_gate.py`, `document_integrity.py`, `authenticity_check.py`, `mental_health_parity.py`, `appeal_evaluator.py`, `rule_registry.py`), `backend/app/engine/` (`adjudication_state.py`, `calculator.py`, `dependency_graph.py`), `backend/app/schemas/` (`provenance.py`, `hospital_bill.py`, `insurance_policy.py`, `rejection_letter.py`, `analysis_result.py`), `backend/app/forensics/fraud_scorer.py`, `backend/app/reports/generator.py`, test suites in `backend/tests/`.
- **Key findings**:
  1. Generic heuristic override in `appeal_evaluator.py` (+62%, +45% etc.) overrides financial deduction when overturn probability >= 70%.
  2. Final Financial Reconciliation Gate runs unconditionally even when Tier 0 gate is BLOCKED, and fails falsely on legitimate rejections.
  3. `AnalysisResult.compute_aggregates` sums individual rule monetary impact with reconciliation impact, double-counting monetary impact.
  4. Missing rules: Procedure Sub-Limit Rule, Non-Medical Items Rule, Sum Insured Capping Rule.
  5. Proportionate deduction includes `CONSULTATION`, double-counts room excess in formula, and never deducts room excess from `AdjudicationState`.
  6. Moratorium calendar math in `insurance_policy.py` subtracts portability from 60 and adds to original inception date, breaking continuous coverage calculations; disguised repudiation phrases are not detected.
  7. `Provenance[T]` lacks numeric operator overloads and equality with primitives, causing 20+ test crashes.
- **Unexplored areas**: None within Survey 1 scope.

## Key Decisions Made
- Conducted exhaustive read-only inspection and cataloged all 32 test failures.
- Completed comprehensive 5-component handoff report (`handoff.md`).

## Artifact Index
- C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1\BRIEFING.md — Persistent state
- C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1\progress.md — Liveness heartbeat
- C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_survey_1\handoff.md — Final comprehensive survey report
