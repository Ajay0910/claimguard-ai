# E2E Test Infrastructure Specification: ClaimGuard AI Hardening

## 1. Test Philosophy & Principles

The ClaimGuard AI verification track is built upon strict **Opaque-Box, Requirement-Driven** engineering. All verification scenarios are derived directly from the authoritative specifications in `ORIGINAL_REQUEST.md` (R1–R6), statutory healthcare regulations, and `PROJECT.md`. Tests never depend on implementation shortcuts or internal mock flags.

### Core Testing Tenets:
1. **Opaque-Box & Requirement-Driven**: Tests interact exclusively with public module APIs, Pydantic data schemas, rule entry points, and end-to-end multi-document pipelines.
2. **Dual Track Methodology**: The E2E testing track is developed in parallel with implementation milestones. Tests define the binding acceptance criteria for milestones M1 through M5.
3. **Deterministic Financial Verification**: Generic heuristics, arbitrary ML probabilities, or mock fallbacks must never override financial correctness. Tests verify that:
   $$\text{Expected Payable} - \text{Insurer Payable} = \text{Disputed Amount}$$
   Any deviation or ambiguity must strictly route claims to `NEEDS_REVIEW` or `BLOCKED`.
4. **Fail-Closed Safety Gates**: If any Tier 0 safety gate (Identity, Document Integrity, Clinical Firewall) fails, adjudication must halt immediately with status `BLOCKED` and zero financial impact.
5. **Statutory Adherence**: Strict calendar math for 60-month continuous coverage moratorium (IRDAI May 2024 / Insurance Act Sec 45), 36-month PED waiting period alignment, Schedule I non-medical exclusions, protected expense shielding (ICU/OT/medicines), and Section 21(4) Mental Healthcare Act 2017 parity.
6. **Zero Facade Tests**: No facade assertions that trivially pass without exercising real business logic. Every test case specifies explicit inputs, authoritative expected outputs, and exact monetary/status invariants.

---

## 2. Feature Inventory Test Mapping (Tiers 1–4)

All 22 features (F01–F22) defined in `PROJECT.md` are mapped across four rigorous verification tiers:

- **Tier 1 (Feature Coverage, $\ge 5$ per feature)**: Isolated, self-contained happy-path and standard validation tests.
- **Tier 2 (Boundary & Corner Cases, $\ge 5$ per feature)**: Edge conditions, off-by-one calendar boundaries, extreme values, format drift, and error paths.
- **Tier 3 (Cross-Feature Combinations, Pairwise)**: Interaction between multiple rules, cascading gates, ordering DAGs, and compound failures.
- **Tier 4 (Real-World Multi-Document Scenarios & Golden UAT)**: High-fidelity multi-document claims connecting hospital bills, policies, rejection letters, and the `data/` synthetic corpus.

| Feature ID | Feature Description | Milestone | Tier 1 (Isolated) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Real-World / UAT) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **F01** | Provenance Type Operability (`__eq__`, arithmetic, string delegation) | M1 | `test_tier1_f11_*` | `test_tier2_f11_*` | Pairwise arithmetic | Scenario S1, S5 |
| **F02** | Standalone Evidence Ledger Schema (`EvidenceLedgerEntry`) | M1 | `test_tier1_f11_*` | `test_tier2_f11_*` | Multi-rule lineage | Scenario S5, UAT-1 |
| **F03** | Calculation Lineage Preservation (`FinancialMath` + Decimal) | M1 | `test_tier1_f07_*` | `test_tier2_f07_*` | DAG accumulation | Scenario S1, S5 |
| **F04** | Document SHA-256 Cryptographic Hashing | M1 | `test_tier1_f11_*` | Challenger-1 | Bundle hash check | UAT-2, Red Team |
| **F05** | Multi-Page PDF Ingestion (All pages parsed) | M2 | Ingestion Unit | Challenger-1 | Document Gate | UAT Multi-page |
| **F06** | Non-Destructive Preprocessing (Preserve digital layer) | M2 | Pipeline Unit | Challenger-1 | Multi-modal OCR/VLM | UAT Scans |
| **F07** | Fail-Closed Extraction Fallback (`EXTRACTION_FAILED`) | M2 | Pipeline Unit | Challenger-1 | Gate Block cascade | Red Team Attack 5 |
| **F08** | Tier 0 Document Arithmetic Gate (Line item balance) | M2 | `test_tier1_f03_*` | `test_tier2_f03_*` | Pairwise 04, 10 | Scenario S1, S5 |
| **F09** | Strict Identity Gate & Insured Members (Fail-closed) | M2 | `test_tier1_f02_*` | `test_tier2_f02_*` | Pairwise 02, 10 | Scenario S4, UAT-3 |
| **F10** | Procedure Sub-Limit Rule (Cataract, Hernia, Cardiac) | M3 | `test_tier1_f07_*` | `test_tier2_f07_*` | Pairwise 09 | Scenario S5 |
| **F11** | Non-Medical Expenses Rule (Schedule I exclusions) | M3 | `test_tier1_f06_*` | `test_tier2_f06_*` | Pairwise 11 | Scenario S1, S5 |
| **F12** | Sum Insured Cap Rule (Expected payable $\le$ SI) | M3 | `test_tier1_f07_*` | `test_tier2_f07_*` | Tail DAG cap | Scenario S5, Red Team |
| **F13** | Proportionate Room Rent Deduction (>1.15 threshold & ICU shield) | M3 | `test_tier1_f05_*`, `f06_*` | `test_tier2_f05_*`, `f06_*` | Pairwise 01, 03 | Scenario S1 |
| **F14** | Moratorium Calendar Math & Phrases (60 months continuous) | M3 | `test_tier1_f08_*` | `test_tier2_f08_*` | Pairwise 01, 07 | Scenario S2 |
| **F15** | Waiting Period Rule Alignment (IRDAI 2024 / Portability) | M3 | `test_tier1_f09_*` | `test_tier2_f09_*` | Pairwise 05, 08 | Scenario S2 |
| **F16** | Eliminate Heuristic Overturn Overrides (Zero arbitrary 70%) | M4 | Appeal Unit | Appeal Adversarial | Decoupled Appeal | Scenario S3 |
| **F17** | Reconcile Financial Gate & State Sync (No run on BLOCKED) | M4 | `test_tier1_f04_*`, `f13_*` | `test_tier2_f04_*`, `f13_*` | Complex Adj | Scenario S3, S4 |
| **F18** | Invariant Financial Equation (Payable - Insurer = Disputed) | M4 | `test_tier1_f13_*` | `test_tier2_f13_*` | Complex Adj | Scenario S1, S5 |
| **F19** | Frontend Mock Leak Elimination (Fail-closed API) | M5 | API Unit | API Timeout / Error | UI Error Barrier | E2E Frontend |
| **F20** | Frontend Data Integrity (No fake patient cards) | M5 | UI Render Unit | Dynamic Prop Check | UI State Sync | E2E Portal |
| **F21** | Portal Enum Synchronization (`CLAIM_SUPPORTED`, `BLOCKED`) | M5 | Portal API Unit | State Mapping Test | DB-Portal Sync | E2E Portal |
| **F22** | Golden UAT Suite & Full Verification | E2E | `test_golden_uat.py` | Stress Permutations | All Pairwise | Full Corpus (40 bills) |

---

## 3. Test Architecture & Directory Layout

The project test suite is structured under `backend/tests/`:

```
backend/tests/
├── conftest.py                          # Global backend fixtures
├── test_rules.py                        # Rule engine unit tests (11 tests)
├── test_forensics.py                    # Forensic analysis unit tests (4 tests)
├── test_new_features.py                 # Multi-modal feature integration tests (15 tests)
├── test_appeal_adversarial.py           # Statutory appeal & contestability adversarial tests (15 tests)
├── test_adversarial_challenger_1.py     # PDF inspector & anomaly scorer boundary stress (18 tests)
├── red_team/                            # Red Team & Independent Audit Suite
│   ├── __init__.py
│   ├── test_red_team_attacks.py         # Cyclic dependencies, leap years, prompt injection (4 tests)
│   └── test_final_acceptance.py         # Double deduction, complex moratorium, mutex policies (4 tests)
└── e2e/                                 # Dedicated 4-Tier E2E Testing Track
    ├── __init__.py
    ├── conftest.py                      # Multi-document factories, Golden UAT loaders, in-memory DB
    ├── run_tests.py                     # Standalone CLI test runner with exit code propagation
    ├── test_tier1_features.py           # Tier 1: Isolated Feature Coverage (65 tests)
    ├── test_tier2_boundaries.py         # Tier 2: Boundary & Corner Cases (65 tests)
    ├── test_tier3_pairwise.py           # Tier 3: Cross-Feature Interactions (15 tests)
    ├── test_tier4_real_world.py         # Tier 4: Multi-document Realistic Claims S1-S5 (5 tests)
    ├── test_golden_uat.py               # Tier 4: Synthetic Corpus Golden UAT Harness (5 tests)
    └── test_phase4_complex_adjudication.py # Tier 3: Complex Multi-Rule Adjudication (1 test)
```

---

## 4. Test Execution & Runner Commands

### Primary Full Test Suite Runner
To execute all 227 tests across the entire repository:
```bash
pytest backend/tests/ -v
```

### Dedicated E2E Track Runner
To execute all E2E Track tests (Tiers 1–4):
```bash
pytest backend/tests/e2e/ -v
```

### Standalone CLI Runner (No pytest dependency required on PATH)
```bash
python backend/tests/e2e/run_tests.py
```

### Tier-Specific Execution Commands
```bash
# Tier 1: Feature Coverage (Isolated happy path)
pytest backend/tests/e2e/test_tier1_features.py -v

# Tier 2: Boundary & Corner Cases
pytest backend/tests/e2e/test_tier2_boundaries.py -v

# Tier 3: Cross-Feature Combinations (Pairwise)
pytest backend/tests/e2e/test_tier3_pairwise.py -v

# Tier 4: Real-World Scenarios (S1-S5)
pytest backend/tests/e2e/test_tier4_real_world.py -v

# Tier 4: Golden UAT Synthetic Corpus
pytest backend/tests/e2e/test_golden_uat.py -v

# Red Team Adversarial Attacks
pytest backend/tests/red_team/ -v
```

### Fast Fail & Diagnostic Flags
```bash
# Exit immediately on first failure with concise traceback
pytest backend/tests/ -x --tb=short

# Run specific feature tests matching keyword filter
pytest backend/tests/e2e/ -k "moratorium or proportionate" -v
```

---

## 5. Coverage Thresholds & Progressive Verification Gates

### Quantitative Test Count Targets
| Test Suite / Track | Scope | Target Threshold | Baseline Count | Current Passing | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **Tier 1 (Isolated Features)** | `test_tier1_features.py` + Unit Tests | $\ge 70$ | 91 | 75 | Progressive (Pending M1-M3) |
| **Tier 2 (Boundary & Corner)** | `test_tier2_boundaries.py` + Challenger | $\ge 70$ | 83 | 77 | Progressive (Pending M1-M3) |
| **Tier 3 (Pairwise & Complex)**| `test_tier3_pairwise.py` + Phase 4 + Red Team | $\ge 20$ | 24 | 18 | Progressive (Pending M1-M3) |
| **Tier 4 (Real-World & UAT)**  | `test_tier4_real_world.py` + Golden UAT + Acceptance | $\ge 10$ | 14 | 14 | **100% PASS** |
| **Total Test Corpus**          | Full Project Repository | **$\ge 200$** | **227** | **201** | **88.5% Passing Baseline** |

### Progressive Verification Policy
Under the Dual-Track testing contract:
1. **Unimplemented Milestone Features**: Tests asserting behavior of planned milestones (e.g. M1 Provenance arithmetic, M2 Identity Gate fail-closed, M3 Proportionate deduction threshold) serve as formal contract gates. They are designed to fail until the respective milestone is completed by the implementing agent.
2. **Completed Milestone Features**: Once a milestone is declared complete, **100% of its associated tests must pass with zero regression**.
3. **Regression Tolerance**: Exactly **0 test failures** are permitted on existing passing features.

---

## 6. Golden UAT Synthetic Corpus Integration

The Golden UAT harness (`backend/tests/e2e/test_golden_uat.py`) directly exercises synthetic claim documents generated under `data/`:
- `data/synthetic_bills/manifest.json`: 40 itemized hospital bills across `correct`, `room_rent_error`, `inflated`, and `mixed` categories.
- `data/synthetic_policies/manifest.json`: 30 insurance policy schedules with diverse room rent caps, co-pays, deductibles, and waiting periods.
- `data/synthetic_rejections/manifest.json`: 30 insurer rejection notices detailing claimed, approved, and deducted amounts.

### High-Fidelity Test Fixtures (`backend/tests/e2e/conftest.py`):
- `golden_manifests`: Session-scoped loader parsing all three synthetic manifests.
- `golden_claim_builder`: Parameterized factory generating matching 3-document bundles (`HospitalBill`, `InsurancePolicy`, `RejectionLetter`) for full-pipeline adjudication.
- `extract_val`: Universal primitive extractor ensuring resilient value assertions across primitive and `Provenance[T]` models.
