# BRIEFING — 2026-09-27T06:55:00Z

## Mission
Design concrete implementation for F03 (Calculation Lineage Preservation in FinancialMath) with Decimal precision, operand provenance tracking, formula lineage, and compatibility with AdjudicationState and rules.

## 🔒 My Identity
- Archetype: explorer
- Roles: Mathematical Engine & Calculation Lineage Specialist
- Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3
- Original parent: 8a31858b-a7fa-4833-b69a-793b18272149
- Milestone: M1 (Type System, Provenance & Evidence Ledger)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement source code directly
- Must use Decimal for exact financial math rounded to 2 decimal places (paise)
- Must preserve operand provenance IDs in calculation_inputs
- Must support formula tracking and source document lineage aggregation
- Must ensure full compatibility with AdjudicationState and rule evaluation

## Current Parent
- Conversation ID: 8a31858b-a7fa-4833-b69a-793b18272149
- Updated: not yet

## Investigation State
- **Explored paths**: `backend/app/engine/calculator.py`, `backend/app/schemas/provenance.py`, `backend/app/engine/adjudication_state.py`, `backend/app/rules/proportionate_deduction.py`, `backend/app/rules/copay_rule.py`, `backend/app/rules/deductible_rule.py`, `backend/app/rules/engine.py`, `explorer_m1_1/handoff.md`, `explorer_m1_2/handoff.md`.
- **Key findings**:
  1. `FinancialMath` in `calculator.py` used float, causing precision drift; collected `sources = []` at lines 14-18 and discarded them; hardcoded `source_document_id="Engine"`.
  2. Python standard `Decimal` raises `TypeError` when combined with `float` in arithmetic operations (e.g. `policy_room_limit_f * 1.15`), breaking rules with float literals.
  3. Created `SafeDecimal(Decimal)` with cross-type dunders (`_coerce`) and Pydantic v2 core schema (`__get_pydantic_core_schema__`) that cleanly allows float, int, str, and Provenance math.
  4. Fully designed refactored `FinancialMath` with `_inspect_operand`, `calculation_inputs`, formula tracking, source document aggregation, and `EvidenceLedgerEntry` bridge.
  5. Verified end-to-end pipeline execution across `AdjudicationState` with `check_proportionate_deduction`, `check_deductible`, and `check_copay`, with `verify_reconciliation()` passing.
- **Unexplored areas**: None for M1 scope.

## Key Decisions Made
- `SafeDecimal` will inherit from `Decimal`, implement `__get_pydantic_core_schema__`, and implement cross-type arithmetic coercion to support legacy float expressions without errors.
- `FinancialMath.extract` will return `SafeDecimal` (preserving compatibility with floats while enabling exact Decimal arithmetic).
- Lineage tracking will record operand IDs, source documents, hashes, and formulas in `calculation_inputs` and chain `Transformation` objects.
- `FinancialMath.to_evidence_ledger_entry` and `FinancialMath.record_in_ledger` will bridge `Provenance[SafeDecimal]` into `EvidenceLedgerEntry` for seamless persistence.

## Artifact Index
- `BRIEFING.md` — persistent working memory
- `DISPATCH.md` — dispatch history and task instructions
- `progress.md` — liveness heartbeat and step tracking
- `handoff.md` — concrete architecture specification and implementation guide for F03
