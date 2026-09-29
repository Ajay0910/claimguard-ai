# Backend Hardening Roadmap (Post-Phase 3)

The previous implementation of the Evidence Provenance Ledger and Tier 0 Gates formed a strong foundation, but it is not yet mathematically or logically "unshakeable." Based on strict IRDAI regulations and expert architectural feedback, the following mandatory upgrades must be implemented before moving to Phase 4 (Complex Cross-Document Adjudication).

## 1. Provenance Schema Expansion & Arithmetic Engine
- [ ] **Expand `Provenance[T]` schema**: Add `normalized_value`, `source_document_id`, `source_hash`, `page`, `section`, `bounding_box`, `source_text`, `extraction_confidence`, `extraction_model`, `model_version`, `timestamp`, and `transformations`.
- [ ] **Remove Magic Methods**: Strip implicit `__add__`, `__mul__`, etc. from the `Provenance` class to prevent hidden conversions that discard audit trails.
- [ ] **Deterministic Reconciliation Engine**: Create explicit calculation functions (`calc_add`, `calc_mul`) that accept provenance-bearing values, compute the result, and return a *new* provenance-bearing result that mathematically inherits the audit trail of its parents (e.g., `value: 150, transformations: ["Added Rule X: (Provenance A) + (Provenance B)"]`).

## 2. Identity Gate Overhaul
- [ ] **Role-Awareness**: Explicitly differentiate between `policyholder`, `insured_member`, `patient`, `claimant`, and `proposer`. The patient on the bill does not have to exactly match the policyholder on the policy.
- [ ] **Identifier Weighting**: Weight deterministic IDs (`policy_number`, `claim_number`, `member_id`, `DOB`) much higher than names.
- [ ] **Outputs**: Return `MATCH`, `CONFLICT`, or `INSUFFICIENT_EVIDENCE`.

## 3. Moratorium & Portability Upgrades (IRDAI May 2024 Circular)
- [ ] **Timeline Engine**: The 60-month preexisting disease moratorium must track continuous coverage, portability credits, migration, and breaks in coverage.
- [ ] **Enhanced Sum Insured Separation**: The moratorium applies to the original sum insured; an enhanced sum insured starts its own separate 60-month timer.
- [ ] **Rule Applicability**: The system must explicitly establish that the moratorium rule applies to the disputed amount before declaring an IRDAI violation.

## 4. Clinical Firewall Taxonomy & Scoping
- [ ] **Source Scoping**: Ensure the clinical firewall exclusively reads the insurer's actual rejection reason, fully isolated from policy definitions.
- [ ] **Controlled Taxonomy**: Implement a clinical-rejection taxonomy beyond simple regex (e.g., handling negations like "was NOT medically necessary").

## 5. Security & Rule Architecture
- [ ] **Rule States**: Ensure all rules natively support `PASS`, `FAIL`, `NOT_APPLICABLE`, `CONFLICT`, and `NEEDS_REVIEW`.
- [ ] **Prompt Injection Defense**: Uploaded documents must be treated as untrusted data. Wrap extraction context in explicit `<untrusted_document>` tags.
- [ ] **Regulatory Versioning**: Track the exact IRDAI circular version applied (e.g., 29 May 2024 Master Circular).

## 6. Testing Strategy Shift
- [ ] Move beyond implementation-driven tests. Implement independent golden expected-value fixtures, mutation testing, and adversarial edge cases.
