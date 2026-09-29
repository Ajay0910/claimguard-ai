# ClaimGuard Verification Standards

**1. AI Extraction vs. Deterministic Adjudication**
- **Constraint:** The LLM must NEVER independently determine financial correctness, clinical necessity, or regulatory violations. Missing information is never permission to guess. Ambiguous or insufficient evidence must produce a `NEEDS_REVIEW` state.

**2. Evidence Provenance & Ledger**
- **Constraint:** Do not use flat numbers in data models. Every extracted value must map exactly to its source: `document -> page/section -> extracted field -> rule -> calculation -> result`.

**3. Source-Backed Regulatory Claims & Thresholds**
- **Constraint:** Never hallucinate or hardcode generic thresholds (e.g., 115% for proportionate deduction) unless explicitly backed by the policy document or authoritative regulatory source (e.g., IRDAI Master Circular). Proportionate deduction applies strictly when the ratio exceeds 1.0.

**4. No Heuristic Overrides & Strict Reconciliation**
- **Constraint:** LLM heuristics (e.g., Ombudsman appeal probability) must be strictly decoupled from the core `RuleEngine` and run downstream. The engine must compute discrepancies via a `Final Financial Reconciliation Gate`. Aggregators must NEVER blindly sum rule impacts to avoid double-counting; the final calculated `disputed_amount` is authoritative.

**5. Regulatory Timelines & Exact Arithmetic**
- **Constraint:** Never substitute approximate day counts (e.g., 1825 days) for calendar-month rules (e.g., 60 months). Use exact calendar arithmetic and account for portability/migration.

**6. Tier 0 Safety Gates & Short-Circuiting**
- **Constraint:** Identity conflicts and Clinical-necessity decisions must trigger Tier 0 gates (Identity Gate, Clinical Firewall). These gates must output structured block states (`BLOCKED`) and completely short-circuit the financial rule engine.

**7. Frontend/Backend Consistency**
- **Constraint:** The backend status is strictly authoritative. Frontend pipelines must crash gracefully and never display misleading success indicators (e.g., checkmarks) for unreached or failed pipeline stages.

**8. Testing Constraints**
- **Constraint:** Every important bug must become a regression test. Add adversarial edge-case tests whenever a failure involves a boundary condition, double-counting, or document mismatch.
