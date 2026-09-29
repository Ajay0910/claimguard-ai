# Dispatch to Explorer M1-3: Calculation Lineage Preservation in FinancialMath

- **Role**: Mathematical Engine & Calculation Lineage Specialist
- **Working Directory**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3\
- **Authoritative Request**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- **Project Scope**: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md

## Objective
Design the concrete implementation for Feature F03 (Calculation Lineage Preservation in `FinancialMath`):
1. Inspect `backend/app/engine/calculator.py` (`FinancialMath`):
   - Current implementation discards `sources` and hardcodes `source_document_id="Engine"`.
   - Current math uses native Python `float`, introducing IEEE-754 precision issues.
2. Design the refactored `FinancialMath`:
   - Decimal precision support (`decimal.Decimal`) with rounding to 2 decimal places (paise).
   - Provenance preservation: record input operand IDs in `calculation_inputs`, record mathematical formula string, and aggregate source document references.
   - Integration with `EvidenceLedgerEntry` generation when rules execute financial operations.
3. Check interactions between `FinancialMath`, `AdjudicationState`, and existing rules (`proportionate_deduction.py`, `copay_rule.py`, `deductible_rule.py`).
4. Provide the exact implementation design in your `handoff.md` for the worker to implement.

## 2026-09-27T06:46:48Z
You are Explorer M1-3 (Mathematical Engine & Calculation Lineage Specialist).
Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3\
Project root: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

Read:
1. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\ORIGINAL_REQUEST.md
2. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\PROJECT.md
3. C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork\explorer_m1_3\DISPATCH.md

Your task is to design the concrete implementation for F03 (Calculation Lineage Preservation in FinancialMath):
1. Inspect backend/app/engine/calculator.py (FinancialMath).
2. Design refactored FinancialMath using Decimal for exact financial math and preserving operand provenance IDs in calculation_inputs.
3. Include formula tracking and source document lineage aggregation.
4. Ensure full compatibility with AdjudicationState and rule evaluation.
5. Write your design and concrete code snippets in handoff.md in your working directory.
6. Send message to orchestrator when done.
