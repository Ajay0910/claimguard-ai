# Original User Request

## Initial Request — 2026-09-18T15:25:00Z

# Teamwork Project Prompt — Draft

> Status: Step 5-6 — Designing Verification & Acceptance Criteria
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Use a very large team of agents to analyze the 15 papers in parallel, then spin up separate implementation agents for the top 2-3 most impactful features.

Analyze 15 provided research papers on medical insurance assessment, fraud detection, and document extraction, compare them to the existing ClaimGuard AI system, and implement the most impactful missing features into the core system without causing errors.

Working directory: c:\Users\krusheek\Desktop\SIH\claimguard-ai
Integrity mode: development

Research URLs:
- https://academic.oup.com/jamiaopen/article/8/1/ooaf016/8042205
- https://aclanthology.org/2021.findings-acl.58/
- https://doi.org/10.1109/UBMK.2018.8566309
- https://arxiv.org/abs/2004.07464
- https://doi.org/10.1145/3503161.3548112
- https://doi.org/10.1109/BigData59044.2023.10386518
- https://arxiv.org/abs/2505.19804
- https://arxiv.org/abs/2102.10978
- https://www.nature.com/articles/s41598-024-82062-x
- https://aclanthology.org/2024.acl-long.559/
- https://arxiv.org/abs/2404.10097
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3965192
- https://jisem-journal.com/index.php/journal/article/view/3121
- https://arxiv.org/abs/2507.00827
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9943622/

## Requirements

### R1. Research and Analysis
Scrape the public text/abstracts from the provided URLs to identify advanced features for medical insurance assessment and fraud detection. Compare these concepts against the current ClaimGuard AI architecture.

### R2. Feature Selection
Select the top 2-3 most impactful and feasible features that are missing from ClaimGuard AI. 

### R3. Implementation
Implement the selected features into the core system (backend/frontend). The implementation must be robust and integrated gracefully without breaking existing functionality.

## Verification Resources
- The backend has a test suite located in `backend/tests/`. Run tests using `pytest backend/tests/` to verify core system stability.

## Acceptance Criteria

### Research Output
- [ ] A written summary artifact is produced detailing the analysis of the 15 papers, the features considered, and the rationale for the 2-3 features selected for implementation.

### System Stability
- [ ] The backend test suite (`pytest backend/tests/`) passes without any new failures.
- [ ] The backend server can start successfully (`uvicorn app.main:app`) without crashing.

### Feature Implementation
- [ ] The newly implemented features are accessible via API or UI.
- [ ] The implementation includes programmatic tests (e.g., new pytest functions) that verify the new features work as expected.

## Follow-up — 2026-09-19T04:28:23Z

The server restarted and interrupted your final verification gate. Please resume your work, complete the final verification, and finalize the research and implementation artifacts to achieve the goal.

## 2026-09-26T07:37:56Z

Conduct a multi-agent engineering campaign to harden the ClaimGuard health-insurance claim verification system into a production-grade, auditable platform with zero hallucination risk, strict provenance, and adversarial auditing.

Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai
Integrity mode: development

## Requirements

### R1. Non-Negotiable Safety Principles
The system must never allow an LLM to independently adjudicate financial correctness, fabricate values, silently resolve conflicts, or make clinical-necessity judgments. Every finding must have source-document provenance, use deterministic calculations, and output NEEDS_REVIEW on ambiguity. Frontend calculations must never override backend calculations. 

### R2. Core Architecture & System Layers
Ensure the presence and correctness of Tier 0 Safety Gates (Identity, Document Integrity, Clinical Firewall), Policy Applicability, Regulatory Verification, Financial Reconciliation, Evidence Ledger, and Appeal routing. The core architecture must remain: AI reads, rules verify, evidence proves, humans handle uncertainty.

### R3. Workflow & Phased Implementation
Execute a 5-phase workflow:
1. Inspect entire repository.
2. Create a binding implementation plan identifying weaknesses, risks, and missing tests.
3. Implement improvements in isolated milestones.
4. Run unit, integration, regression, adversarial, and cross-document conflict tests after every milestone.
5. Deploy an independent adversarial auditor to attempt to falsify the implementation (hunting for off-by-one errors, OCR drift, hallucinated clauses, missing evidence, etc.).

### R4. Test Engineering & Falsification
Do not optimize for the number of changes; optimize for correctness and traceability. For every failed adversarial test, determine the root cause, fix it, add a regression test, re-run the suite, and record the lesson. Do not declare success merely because tests pass; actively attempt to break the system.

## Acceptance Criteria

### Final Handoff & Falsification Checks
- [ ] System demonstrates deterministic financial calculations and exact policy-condition evaluation.
- [ ] Safe handling of clinical cases and identity conflicts is programmatically verified.
- [ ] Correct 60-calendar-month moratorium logic and continuous-coverage reasoning is verified.
- [ ] Source-level evidence provenance exists for every extracted variable.
- [ ] No unsupported legal, regulatory, or financial conclusions are produced.
- [ ] Complete regression coverage exists for previously discovered failures (e.g., proportionate deduction loopholes).
- [ ] A final report is generated including: architecture summary, changed components, test matrix, adversarial test results, unresolved risks, known limitations, and exact acceptance criteria achieved/not achieved.

## 2026-09-27T06:33:06Z

# Teamwork Project Prompt — Draft

> Requested team: Full team of specialists (extraction, policy-rule applicability, financial reconciliation, moratorium/portability, provenance, frontend/backend consistency, testing, adversarial review)

Re-audit the entire ClaimGuard adjudication architecture and rebuild the failed cross-document verification path to eliminate generic heuristic overrides and make every final financial amount deterministic and traceable to bill + policy + settlement evidence.

Working directory: C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai

Integrity mode: development

## Requirements

### R1. Deterministic Financial Reconciliation
The system must explicitly connect bill values, policy clauses, and insurer deductions. It must independently derive the expected payable and compare it with the insurer payable to calculate the exact disputed amount. Generic heuristics (e.g., 70% appeal probability) must never override deterministic verification.

### R2. Strict Policy-Rule Applicability & Ordering
Rules must only trigger when their specific thresholds are strictly crossed (e.g., >1.15 for proportionate deduction) and must exclude immune categories (e.g., OT/Cath Lab). Rule ordering must be derived semantically from policy-specific metadata, not universally assumed. 

### R3. Extraction Reliability & Cross-Verification
Rebuild the extraction layer to cross-verify VLMs, calculate confidence scores, and reject low-confidence or mathematically inconsistent outputs (e.g., room rate, claim amount). Critical fields must require strict confidence validation.

### R4. Moratorium & Clinical Reasoning
Moratorium reasoning must utilize continuous coverage, portability/migration credits, and correct sum insured timelines. Clinical issues, document inconsistency, and fraud signals must be segregated into distinct finding types rather than collapsed into a generic violation score.

### R5. Ubiquitous Evidence Ledger
Every finding must carry complete provenance: document ID, page, section, source text, extracted value, normalized value, rule ID, formula, calculation inputs, final output, and confidence.

### R6. E2E Consistency & Testing
The UI state must exactly reflect the backend (e.g., "Analysis Complete" only when successful). A full golden UAT corpus must be established covering edge cases (exact thresholds, portability, incorrect rejections), and the hard-test case must pass end-to-end.

## Acceptance Criteria

### Final Handoff & Falsification
- [ ] No heuristic or ML probability score overrides a deterministic financial calculation.
- [ ] Expected payable minus insurer payable exactly equals the disputed amount; otherwise, the claim routes to NEEDS_REVIEW.
- [ ] Extraction layer actively rejects low-confidence predictions and cross-verifies values before adjudication.
- [ ] Every financial result is traceable to a calculation chain with complete source-document provenance.
- [ ] Rule execution order and applicability strictly respect policy-defined conditions.
- [ ] The full golden UAT test suite (including adversarial boundaries, identity mismatches, and portability) passes independently.
- [ ] The frontend UI accurately reflects the authoritative backend status without contradicting itself.
