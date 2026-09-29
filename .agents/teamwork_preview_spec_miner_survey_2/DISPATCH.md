# Dispatch Task: Survey Phase - Regulatory, Moratorium, Policy Rules & Deterministic Calculation Inspection

- Working Directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2
- Authoritative Request: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\ORIGINAL_REQUEST.md
- Workspace Root: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

## Objective
Act as a specification miner to extract all existing rules, policy logic, financial calculation logic, and regulatory requirements across the codebase (`backend/app/rules/`, `backend/app/services/`, etc.).

## Scope of Investigation
1. Inspect the financial calculation logic:
   - Base deductions, co-pay, room rent capping, ICU capping, proportionate deductions.
   - Check if float arithmetic or rounding issues exist.
   - Check if frontend calculations can override backend numbers or if backend is single source of truth.
2. Inspect the policy & regulatory verification logic:
   - 60-calendar-month moratorium logic and continuous-coverage reasoning (IRDAI / regulatory guidelines). Check how continuous coverage periods are calculated, gaps handled, and exclusions treated.
   - Waiting periods (PED, specific ailments, 30-day initial waiting period).
   - Proportionate deduction loopholes (associated medical expenses vs room rent capping).
3. Ambiguity & Human Review Triggers:
   - How `NEEDS_REVIEW` is currently triggered and handled.
   - Any cases where ambiguous data is silently defaulted or guessed.
4. Extract all explicit and implicit mathematical/regulatory specifications implemented or missing.

## Output Requirements
Write your detailed specification inventory and gap analysis to:
`C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2\handoff.md`
Follow the Handoff Protocol (Observation, Logic Chain, Caveats, Conclusion, Verification Method).
When finished, send a message to parent (ID: 101499e2-9536-4e3a-95f4-a7b372b422ea).

## 2026-09-26T07:40:22Z
You are assigned to the Survey Phase for ClaimGuard AI Hardening.
Your working directory is C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2.
Read your instructions in C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2\DISPATCH.md and C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\ORIGINAL_REQUEST.md.
Mine specifications and inspect regulatory logic, 60-calendar-month moratorium, continuous-coverage reasoning, financial calculation rules, proportionate deduction loopholes, and NEEDS_REVIEW triggers.
Write your complete report to C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\.agents\teamwork_preview_spec_miner_survey_2\handoff.md.
When finished, send a message to parent orchestrator (ID: 101499e2-9536-4e3a-95f4-a7b372b422ea) with your report summary and handoff path.

