# ClaimGuard AI Frontend — End-to-End Testing Infrastructure Specification

**Document Version:** 2.4.0  
**Target Application:** ClaimGuard AI React Frontend  
**Workspace:** `c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend`  
**Author:** `test_writer_e2e` (Quality Assurance & E2E Testing Specialist)  
**Status:** Active & Enforced  

---

## 1. Testing Philosophy & Methodology

The ClaimGuard AI testing infrastructure is engineered to validate enterprise-grade reliability, clinical and statutory precision, and forensic accuracy across healthcare claim verification workflows. In healthcare finance and insurance dispute resolution, software errors can lead to financial losses, delayed patient appeals, or legal non-compliance under Insurance Regulatory and Development Authority of India (IRDAI) guidelines.

### 1.1 Core Principles
1. **Authoritative Output Derivation**: Every test assertion originates from documented statutory regulations (IRDAI circulars, Mental Healthcare Act 2017, Insurance Act Sec 45), backend Pydantic models (`backend/app/schemas/`), and mined API contracts (`spec_miner_api/handoff.md`). No arbitrary expected values are accepted.
2. **Four-Tier Verification Matrix**: Tests are segregated into hierarchical tiers—from single-feature contract verification to complex adversarial combinations and end-to-end user journeys.
3. **Zero-Flakiness Guarantee**: Tests run deterministically in an isolated execution harness without external network dependencies, while accurately simulating backend network latency, background analysis jobs, and error states.
4. **Adversarial & Boundary Rigor**: Input boundaries (file size caps, MIME types, arithmetic tolerances, timeline edge cases, and tamper score thresholds) are actively probed with invalid and stress-test data.
5. **Contract Resiliency & Normalization**: The harness verifies that the frontend client gracefully handles backend schema variances (e.g. `total_recovered_amount` vs `total_amount_recovered`, `appeal_text` vs `content`).

---

## 2. Feature Inventory & Traceability Matrix

The testing harness provides full coverage for all 16 system capabilities defined in `PROJECT.md` and `spec_miner_api/handoff.md`:

| Feature ID | Category | Name | Authoritative Source | Tested Tiers |
|------------|----------|------|----------------------|--------------|
| **FEAT-01** | Intake | Multi-Document Upload API & State | `backend/app/api/upload.py:17`, `PROJECT.md § Feature 9` | Tier 1, 2, 3 |
| **FEAT-02** | Intake | Claim Document List & Inspection | `backend/app/api/upload.py:82`, `PROJECT.md § Feature 10` | Tier 1, 3 |
| **FEAT-03** | Intake | Pre-Analysis Health Readiness Check | `PROJECT.md § Feature 11`, `explorer_survey_ux:238` | Tier 1, 3, 4 |
| **FEAT-04** | Pipeline | Analysis Trigger & Job Dispatch | `backend/app/api/analysis.py:118`, `PROJECT.md § Feature 5` | Tier 1, 4 |
| **FEAT-05** | Pipeline | Analysis Polling & Background Progress | `backend/app/api/analysis.py:154`, `PROJECT.md § Feature 3` | Tier 1, 2, 4 |
| **FEAT-06** | Pipeline | Analysis Result Unwrapping & Schema Normalization | `backend/app/api/analysis.py:172`, `spec_miner:538` | Tier 1, 2, 4 |
| **FEAT-07** | Rules | Proportionate Deduction Engine (IRDAI May 2024) | `backend/app/rules/proportionate_deduction.py:13` | Tier 1, 2, 3, 4 |
| **FEAT-08** | Rules | Clause Timeline & 60-Month Moratorium Audit | `backend/app/rules/clause_timeline.py:14` | Tier 1, 2, 3, 4 |
| **FEAT-09** | Rules | Mental Health Parity Verification (MHA 2017) | `backend/app/rules/mental_health_parity.py:13` | Tier 1, 2, 3 |
| **FEAT-10** | Rules | Waiting Period Verification (Initial, Specific, PED) | `backend/app/rules/waiting_period.py:14` | Tier 1, 2 |
| **FEAT-11** | Forensics | Error Level Analysis (ELA) Tamper Meter (0-100) | `backend/app/forensics/ela_detector.py:13`, `PROJECT.md § 14`| Tier 1, 2, 3, 4 |
| **FEAT-12** | Forensics | Document Metadata & Software Tampering Scrutiny | `backend/app/forensics/metadata_checker.py:6` | Tier 1, 2, 3, 4 |
| **FEAT-13** | Forensics | CGHS Tariff & Length-of-Stay (LOS) Anomaly Flagging| `backend/app/forensics/bill_anomaly.py:29` | Tier 1, 2, 3, 4 |
| **FEAT-14** | Forensics | Clinical Consistency Matrix & Contradiction Audit | `backend/app/forensics/consistency_checker.py:33` | Tier 1, 3, 4 |
| **FEAT-15** | Audit | Cryptographic SHA-256 Chain Ledger Verification | `backend/app/utils/audit_trail.py:40`, `PROJECT.md § 15` | Tier 1, 3, 4 |
| **FEAT-16** | Legal | Statutory Grievance & Appeal Generator | `backend/app/api/reports.py:32`, `PROJECT.md § 16` | Tier 1, 4 |

---

## 3. Test Tier Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TIER 4: REAL-WORLD SCENARIOS                        │
│   Full End-to-End User Journeys • Multi-Step Audit Workflows            │
│   Apollo Room Rent Appeal • Fraud Detection • Clean Claim • Network Drop│
├─────────────────────────────────────────────────────────────────────────┤
│                     TIER 3: COMBINATIONS & MATRICES                     │
│   Cross-Module Interactions • Multi-Rule Conflicts • Multi-Doc Matrix │
│   Tamper Chains • Clinical Contradiction Matrix • Hash Chain Ledger     │
├─────────────────────────────────────────────────────────────────────────┤
│                     TIER 2: BOUNDARY CASES & ADVERSARIAL                │
│   25MB File Cap • Stripped EXIF • 36m/60m Timeline Limits • ELA Gauges  │
│   Tariff Deviation Limits (2x/3x) • ₹10 Bill Arithmetic Tolerance      │
├─────────────────────────────────────────────────────────────────────────┤
│                     TIER 1: FEATURE COVERAGE & CONTRACTS                │
│   16 Core Features • API Client Normalizers • TypeScript Schema Types   │
│   Status Badges • INR Formatting • VerdictCard Display Logic            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Feature Coverage (Core Happy Paths & Module Contracts)
- **Objective**: Verify that every individual API method, data contract, normalization transform, and UI state calculation functions according to specification.
- **Scope**:
  - API client methods: `uploadDocument`, `triggerAnalysis`, `getAnalysisStatus`, `getAnalysisResult`, `getReport`, `getAppealDraft`, `getAuditTrail`, `getDocuments`, `healthCheck`, `getClaims`, `getStats`.
  - Normalization adapters for field alias reconciliation (`total_recovered_amount`, `appeal_text`, unwrapped `result.result`).
  - TypeScript interface validation: Claim, HospitalBill, InsurancePolicy, RejectionLetter, RuleVerdict, ForensicsResult, AuditTrail.
  - UI Status badge semantics (`COMPLETED`, `PENDING`, `FAILED`, `ANALYZING/RUNNING`, unknown fallback).
  - Indian Rupee (`Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`) formatting.
  - VerdictCard visual elements: PASS/FAIL/NEEDS_REVIEW/SKIPPED styling, delta comparison bar, regulatory citations.
  - Dashboard stats calculation and aggregation.
  - Stepper progression and document state management.

### Tier 2: Boundary Cases & Adversarial Inputs
- **Objective**: Verify application resilience against extreme boundary conditions, malformed payloads, and statutory edge cases.
- **Scope**:
  - File upload size constraints: Empty file (0 bytes), exact 25 MB boundary (`25 * 1024 * 1024` bytes), and rejection of overflow (`25MB + 1 byte`).
  - MIME type boundaries: Whitelisted (`application/pdf`, `image/jpeg`, `image/png`, `image/tiff`) vs blacklisted (`application/zip`, `text/html`, `image/gif`).
  - Monetary values: Zero monetary impact, negative numbers protection, claims exceeding ₹1,00,00,000.
  - Room Rent Proportionate Deduction: `room_rent_limit = null` (no deduction), actual room rate exactly equal to policy limit (`factor = 1.0`, zero deduction), and actual room rate strictly greater than limit.
  - 60-Month Moratorium: Exact 36-month threshold (Insurance Act Sec 45), 36.1 months contestability window, and exact 60-month incontestability line.
  - ELA Tamper Score thresholds: 0.0 (CLEAN), 19.99 (CLEAN), 20.0 (SUSPICIOUS), 49.99 (SUSPICIOUS), 50.0 (HIGHLY_SUSPICIOUS), 100.0 (CAP).
  - CGHS Tariff Benchmarking: Exactly 2.0x max benchmark (MEDIUM severity trigger), 3.0x max benchmark (HIGH severity trigger).
  - Bill Itemization Arithmetic: Discrepancies within ₹10 tolerance vs discrepancies exceeding ₹10 triggering `ITEMIZATION_MISMATCH`.

### Tier 3: Combinations & Cross-Module Interactions
- **Objective**: Test combinatorial matrices and interaction between disparate pipeline sub-systems.
- **Scope**:
  - Multi-document matrix: Single document upload vs dual documents vs full trio (Hospital Bill + Policy + Rejection letter).
  - Concurrent multi-rule conflicts: Simultaneous Proportionate Deduction failure + Moratorium breach + Mental Health parity conflict with cumulative impact summation.
  - Forensic tampering vector combination: Stripped EXIF metadata (`MISSING_EXIF`, LOW) coupled with editing software detection (`Photoshop`, HIGH) and elevated ELA score (82.4).
  - Clinical consistency matrix: Mismatched diagnoses and drug/procedure line items (e.g. Cataract surgery paired with Cardiology medication).
  - Cryptographic SHA-256 Audit Trail: Valid hash chain verification ($H_n = \text{SHA256}(H_{n-1} + \text{data})$) vs tampered block detection.

### Tier 4: Real-World Scenarios (End-to-End User Journeys)
- **Objective**: Validate complete end-to-end user workflows matching real hospital auditing and insurance dispute scenarios.
- **Scope**:
  - **Journey 1 (Enterprise Auditor Discrepancy Triage)**: Auditor uploads Apollo Hospital bill with ICU room rent, Star Health policy with ₹5,000 limit, and TPA rejection letter. System verifies pre-analysis checklist, executes analysis, uncovers ₹42,500 underpayment via IRDAI May 2024 rule, and drafts formal GRO appeal letter.
  - **Journey 2 (Digital Tampering & Fraud Detection Hub)**: Auditor uploads altered bill with Photoshop artifacts. Forensics lab alerts on tamper score (78.5, HIGHLY_SUSPICIOUS), flags CGHS ICU rate 3.5x benchmark, and records SHA-256 audit ledger entry.
  - **Journey 3 (Clean Approved Claim)**: Patient billing strictly satisfies policy limits and tariff norms. Analysis returns `NO_MISMATCH_FOUND`, monetary impact = ₹0, confirming legitimate insurer processing.
  - **Journey 4 (Pre-Existing Disease Moratorium Protection)**: Insurer rejects 62-month-old policy for non-disclosure. Rule engine flags illegal rejection under IRDAI 60-month moratorium rule, generating appeal citation.
  - **Journey 5 (Network Resilience & Fallback Recovery)**: Network failure simulation during status polling, verifying retry mechanisms, contextual error state rendering, and mock resilience.

---

## 4. Coverage Goals & Quality Gates

To achieve production certification, the frontend test suite must meet the following gates:

| Metric | Target | Verification Method |
|--------|--------|---------------------|
| **Feature Coverage (Tiers 1-4)** | 100% of 16 features | Traceability test matrix execution |
| **Test Pass Rate** | 100% (0 failures, 0 flakiness) | Automated test runner execution |
| **API Normalization Coverage** | 100% of discovered key aliases | Normalization unit tests |
| **Statutory Formula Accuracy** | Exact match with IRDAI circulars | Mathematical unit tests |
| **Boundary Coverage** | Min, max, off-by-one, null inputs | Boundary test suite |
| **Execution Time** | < 5 seconds for complete suite | Lightweight ESM runner benchmark |

---

## 5. Test Runner & Execution Guide

The test harness is implemented in modern ECMAScript Modules (`.mjs`) located in `tests/`, utilizing native Node.js capabilities with zero third-party testing dependencies for guaranteed reliability and instant execution.

### 5.1 Directory Layout
```
frontend/
├── TEST_INFRA.md                   # This infrastructure document
├── TEST_READY.md                   # Test readiness and execution summary
├── package.json                    # Contains "test": "node tests/runner.mjs"
└── tests/
    ├── runner.mjs                  # Central test runner with ANSI reporting & summary
    ├── test-framework.mjs          # Lightweight test framework (describe, it, expect, mock)
    ├── tier1-feature-coverage.test.mjs  # Tier 1 test cases
    ├── tier2-boundary-cases.test.mjs    # Tier 2 test cases
    ├── tier3-combinations.test.mjs      # Tier 3 test cases
    └── tier4-real-world-scenarios.test.mjs # Tier 4 test cases
```

### 5.2 Invocation Commands
Execute the full suite across all tiers:
```bash
npm test
```
Or directly via Node:
```bash
node tests/runner.mjs
```

Filter execution to a single tier:
```bash
node tests/runner.mjs --tier=1
node tests/runner.mjs --tier=2
node tests/runner.mjs --tier=3
node tests/runner.mjs --tier=4
```
