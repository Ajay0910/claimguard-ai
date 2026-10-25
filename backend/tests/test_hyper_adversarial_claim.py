"""
End-to-End Architectural Hardening Test for Hyper-Adversarial Medical Claim.

Validates:
1. Universal Table Row Parser without naive substring drops or summary leaks.
2. Full disaggregation of statutory deduction heads into 4 discrete actionable violations.
3. Complete 5 Forensic Pillars on every actionable card.
4. Exact mathematical recovery yield: Gross (11,68,500) - Approved (4,80,000) - Legitimate List I (6,500) = Rs. 6,82,000.00.
"""

import os
import pytest
from app.extraction.pdf_parser_fallback import (
    parse_hospital_bill_pdf,
    parse_insurance_policy_pdf,
    parse_rejection_letter_pdf,
    SUMMARY_ROW_PATTERN
)
from app.rules.engine import RuleEngine
from app.rules import get_val

TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_docs", "hyper_adversarial_claim_case")
BILL_PDF = os.path.join(TEST_DIR, "apollo_hospital_bill.pdf")
POLICY_PDF = os.path.join(TEST_DIR, "icici_lombard_policy.pdf")
REJECTION_PDF = os.path.join(TEST_DIR, "mediassist_rejection_letter.pdf")


def test_summary_row_pattern_precision():
    """Verify SUMMARY_ROW_PATTERN anchors cleanly without dropping clinical procedures or narrative clauses."""
    # Clinical rows that must NOT match summary pattern
    assert not SUMMARY_ROW_PATTERN.match("Total Knee Arthroplasty (Bilateral)")
    assert not SUMMARY_ROW_PATTERN.match("Total (Bilateral) Knee Arthroplasty")
    assert not SUMMARY_ROW_PATTERN.match("Total - Left Hip Replacement")
    assert not SUMMARY_ROW_PATTERN.match("Total (Direct) Bilirubin")
    assert not SUMMARY_ROW_PATTERN.match("Total (Serum) Protein")
    assert not SUMMARY_ROW_PATTERN.match("Total (Free) T4")
    assert not SUMMARY_ROW_PATTERN.match("Total Bilirubin")
    assert not SUMMARY_ROW_PATTERN.match("Total Leucocyte Count (TLC)")
    assert not SUMMARY_ROW_PATTERN.match("Total Parenteral Nutrition")
    assert not SUMMARY_ROW_PATTERN.match("Total - Laparoscopic Cholecystectomy")
    assert not SUMMARY_ROW_PATTERN.match("Total: Robotic Knee Surgery")
    assert not SUMMARY_ROW_PATTERN.match("Total (Robotic Surgery) Sub-Limit Disallowance")
    assert not SUMMARY_ROW_PATTERN.match("Total - Uncapped Single Private Room Deductions")
    assert not SUMMARY_ROW_PATTERN.match("Total robotic suite, implants (Rs. 3.6L) and OT charges")
    assert not SUMMARY_ROW_PATTERN.match("Gross hematuria post-operative monitoring")
    assert not SUMMARY_ROW_PATTERN.match("Subtotal colectomy surgical procedure")
    assert not SUMMARY_ROW_PATTERN.match("1. Robotic Surgery & Navigational Suite Sub-Limit Capping")
    assert not SUMMARY_ROW_PATTERN.match("3. Synthetic Room Rent Benchmark & Proportionate Deduction totaling Rs. 1,77,000.00")
    assert not SUMMARY_ROW_PATTERN.match("Combined Spinal-Epidural Neuroaxial Anesthesia Protocol")

    # Financial summary and settlement headers that MUST match
    assert SUMMARY_ROW_PATTERN.match("TOTAL")
    assert SUMMARY_ROW_PATTERN.match("TOTAL:")
    assert SUMMARY_ROW_PATTERN.match("TOTAL -")
    assert SUMMARY_ROW_PATTERN.match("TOTAL CLAIM BILLED AMOUNT:")
    assert SUMMARY_ROW_PATTERN.match("TOTAL DISALLOWED / DEDUCTED AMOUNT:")
    assert SUMMARY_ROW_PATTERN.match("TOTAL RECONCILIATION")
    assert SUMMARY_ROW_PATTERN.match("TOTAL RECONCILIATION:")
    assert SUMMARY_ROW_PATTERN.match("TOTAL (in INR):")
    assert SUMMARY_ROW_PATTERN.match("TOTAL (Rs.):")
    assert SUMMARY_ROW_PATTERN.match("TOTAL: Rs. 11,68,500.00")
    assert SUMMARY_ROW_PATTERN.match("TOTAL (Rs. 11,68,500.00)")
    assert SUMMARY_ROW_PATTERN.match("TOTAL CLAIM BILLED AMOUNT: Rs. 11,68,500.00")
    assert SUMMARY_ROW_PATTERN.match("NET APPROVED & TRANSMITTED AMOUNT (NEFT/RTGS):")
    assert SUMMARY_ROW_PATTERN.match("GRAND TOTAL")
    assert SUMMARY_ROW_PATTERN.match("GROSS BILL AMOUNT:")
    assert SUMMARY_ROW_PATTERN.match("NET PAYABLE:")
    assert SUMMARY_ROW_PATTERN.match("Sub-Total Amount:")
    assert SUMMARY_ROW_PATTERN.match("Less Advance Paid:")
    assert SUMMARY_ROW_PATTERN.match("Bank Transaction Reference:")
    assert SUMMARY_ROW_PATTERN.match("Bank Transaction Reference: AXIS992384")


def test_hyper_adversarial_extraction():
    """Verify extraction of bill, policy, and rejection letter without hardcoding or data loss."""
    assert os.path.exists(BILL_PDF), f"Missing test fixture: {BILL_PDF}"
    assert os.path.exists(POLICY_PDF), f"Missing test fixture: {POLICY_PDF}"
    assert os.path.exists(REJECTION_PDF), f"Missing test fixture: {REJECTION_PDF}"

    bill = parse_hospital_bill_pdf(BILL_PDF)
    assert bill is not None
    assert bill.total_amount.value == 1168500.0
    assert bill.subtotal.value == 1168500.0
    assert bill.arithmetic_verified is True
    assert len(bill.line_items) == 31

    policy = parse_insurance_policy_pdf(POLICY_PDF)
    assert policy is not None
    assert policy.base_sum_insured.value == 1000000.0
    assert policy.cumulative_bonus.value == 500000.0
    assert policy.sum_insured.value == 1500000.0
    assert policy.portability_credits_months is not None
    assert policy.portability_credits_months.value == 48
    assert policy.room_category_entitled.value == "SINGLE_PRIVATE_AC_ROOM"

    rej = parse_rejection_letter_pdf(REJECTION_PDF)
    assert rej is not None
    assert rej.total_claimed.value == 1168500.0
    assert rej.total_approved.value == 480000.0
    assert rej.total_deducted.value == 688500.0
    assert len(rej.rejection_reasons) == 6

    # Verify each discrete disallowance head was extracted
    reasons_by_amt = {r.amount.value: r for r in rej.rejection_reasons if r.amount}
    assert 250000.0 in reasons_by_amt  # Modern treatment
    assert 175000.0 in reasons_by_amt  # Moratorium / PED repudiation
    assert 177000.0 in reasons_by_amt  # Proportionate room rent
    assert 48000.0 in reasons_by_amt   # Floseal
    assert 32000.0 in reasons_by_amt   # PCA Pump
    assert 6500.0 in reasons_by_amt    # Legitimate non-medical comfort items


def test_hyper_adversarial_rule_disaggregation_and_pillars():
    """Verify all 4 discrete regulatory rules fire independently with all 5 Forensic Pillars."""
    bill = parse_hospital_bill_pdf(BILL_PDF)
    policy = parse_insurance_policy_pdf(POLICY_PDF)
    rejection = parse_rejection_letter_pdf(REJECTION_PDF)

    engine = RuleEngine()
    result = engine.run_all_rules(bill, policy, rejection)

    assert result.overall_status == "MISMATCH_DETECTED"
    assert result.total_monetary_impact == 682000.0

    fail_verdicts = {v.rule_name: v for v in result.rule_verdicts if v.status == "FAIL"}
    assert len(fail_verdicts) == 4, f"Expected exactly 4 distinct FAIL rules, got {list(fail_verdicts.keys())}"

    # 1. Modern Treatment Rule
    assert "Modern Treatment Inpatient Protection Rule" in fail_verdicts
    v_mod = fail_verdicts["Modern Treatment Inpatient Protection Rule"]
    assert v_mod.monetary_impact == 250000.0
    assert "IRDAI Master Circular" in v_mod.regulatory_citation
    assert "Para 5.4" in v_mod.regulatory_citation

    # 2. Moratorium & Continuity Rule (Clause Timeline Rule)
    assert "Clause Timeline Rule" in fail_verdicts
    v_time = fail_verdicts["Clause Timeline Rule"]
    assert v_time.monetary_impact == 175000.0
    assert "IRDAI Master Circular" in v_time.regulatory_citation
    assert "Para 5.3" in v_time.regulatory_citation
    assert "Regulation 17" in v_time.regulatory_citation

    # 3. Proportionate Deduction Rule
    assert "Proportionate Deduction Rule" in fail_verdicts
    v_prop = fail_verdicts["Proportionate Deduction Rule"]
    assert v_prop.monetary_impact == 177000.0
    assert "Uncapped Room Entitlement Bars Proportionate Deduction" in v_prop.regulatory_citation

    # 4. Non-Payable Items Rule
    assert "Non-Payable Items Rule" in fail_verdicts
    v_np = fail_verdicts["Non-Payable Items Rule"]
    assert v_np.monetary_impact == 80000.0
    assert "List III" in v_np.regulatory_citation

    # Validate 5 Forensic Pillars on every actionable card
    for name, v in fail_verdicts.items():
        assert v.actual_claim_fact, f"Missing actual_claim_fact in {name}"
        assert v.applicable_policy_rule, f"Missing applicable_policy_rule in {name}"
        assert v.insurer_applied_action, f"Missing insurer_applied_action in {name}"
        assert v.expected_action, f"Missing expected_action in {name}"
        assert v.monetary_impact is not None and v.monetary_impact > 0, f"Missing or zero monetary impact in {name}"
        assert v.regulatory_citation, f"Missing regulatory_citation in {name}"
        assert "nan" not in str(v.actual_claim_fact).lower(), f"NaN in actual_claim_fact of {name}"
        assert "undefined" not in str(v.actual_claim_fact).lower(), f"undefined in actual_claim_fact of {name}"

    # Mathematical Reconciliation
    gross_bill = 1168500.0
    insurer_approved = 480000.0
    legitimate_list_i = 6500.0
    expected_recoverable = gross_bill - insurer_approved - legitimate_list_i
    assert expected_recoverable == 682000.0
    assert result.total_monetary_impact == expected_recoverable


def test_portal_status_disaggregation_and_pillars():
    """Verify portal response produces exactly 4 distinct cards with 5 Forensic Pillars and 0 NaNs."""
    from unittest.mock import MagicMock
    from app.api.portal import _extract_violation_discrepancy, _generate_plain_summary

    bill = parse_hospital_bill_pdf(BILL_PDF)
    policy = parse_insurance_policy_pdf(POLICY_PDF)
    rejection = parse_rejection_letter_pdf(REJECTION_PDF)

    engine = RuleEngine()
    analysis_run = engine.run_all_rules(bill, policy, rejection)
    result_data = analysis_run.model_dump()
    verdicts = result_data.get("rule_verdicts", [])

    violations = [v for v in verdicts if v.get("status") in ("FAIL", "NEEDS_REVIEW")]
    monetary = analysis_run.total_monetary_impact
    estimated_discrepancy = monetary

    fail_violations = [v for v in violations if v.get("status") == "FAIL"]
    fail_total = sum(_extract_violation_discrepancy(v) or 0.0 for v in fail_violations)
    if estimated_discrepancy and fail_total >= (estimated_discrepancy - 1.0):
        active_violations = [v for v in violations if v.get("rule_name") != "Cross-Document Adjudication"]
    else:
        active_violations = violations

    enriched_violations = []
    for v in active_violations:
        v_rec = _extract_violation_discrepancy(v)
        rule_name = v.get("rule_name", "")
        fact = v.get("actual_claim_fact") or v.get("finding", "")
        rule_text = v.get("applicable_policy_rule") or v.get("regulatory_citation", "")
        applied_action = v.get("insurer_applied_action") or f"Disallowance of Rs. {v_rec:,.2f}"
        expected_action = v.get("expected_action") or f"Reimburse Rs. {v_rec:,.2f}"
        citation = v.get("regulatory_citation") or "IRDAI Master Circular 2024"
        appeal_rec = v.get("appeal_recommendation") or "File grievance"

        enriched_violations.append({
            "rule": rule_name,
            "description": v.get("rule_description", ""),
            "finding": v.get("finding", ""),
            "status": v.get("status", ""),
            "finding_type": v.get("finding_type", ""),
            "recoverable": v_rec,
            "difference": v_rec,
            "citation": citation,
            "appeal_recommendation": appeal_rec,
            "legal_track": v.get("legal_track", "TRACK_B_STATUTORY_BREACH"),
            "actual_claim_fact": fact,
            "applicable_policy_rule": rule_text,
            "insurer_applied_action": applied_action,
            "expected_action": expected_action,
            "evidence": v.get("evidence", "")
        })

    # Exactly 4 discrete actionable cards (not collapsed into 2, nor diluted by catch-all)
    assert len(enriched_violations) == 4

    card_rules = {c["rule"]: c for c in enriched_violations}
    assert "Modern Treatment Inpatient Protection Rule" in card_rules
    assert "Clause Timeline Rule" in card_rules
    assert "Proportionate Deduction Rule" in card_rules
    assert "Non-Payable Items Rule" in card_rules

    # Verify each card has all 5 Forensic Pillars with 0 NaN, 0 undefined
    total_card_recoverable = 0.0
    for c in enriched_violations:
        assert c["actual_claim_fact"] and len(c["actual_claim_fact"]) > 10
        assert c["applicable_policy_rule"] and len(c["applicable_policy_rule"]) > 10
        assert c["insurer_applied_action"] and len(c["insurer_applied_action"]) > 10
        assert c["expected_action"] and len(c["expected_action"]) > 10
        assert c["recoverable"] is not None and c["recoverable"] > 0
        assert c["citation"] and len(c["citation"]) > 10
        assert "nan" not in str(c["recoverable"]).lower()
        assert "undefined" not in str(c["recoverable"]).lower()
        total_card_recoverable += c["recoverable"]

    assert total_card_recoverable == 682000.0


def test_hyper_adversarial_live_fastapi_portal_ingestion(tmp_path, monkeypatch):
    """End-to-end live FastAPI submission and processing of hyper-adversarial claim bundle."""
    import asyncio
    import json
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.database import Base, get_db
    import app.database as database_module
    import app.api.analysis as analysis_module
    from app.api import portal
    from app.api.analysis import run_analysis_pipeline
    from app.models.claim import AnalysisRun
    from sqlalchemy import select

    db_path = tmp_path / "test_hyper_live.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    async def init_schema():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_schema())
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with sessions() as s:
            yield s

    app = FastAPI()
    app.include_router(portal.router)
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(analysis_module, "AsyncSessionLocal", sessions)

    client = TestClient(app)

    with open(BILL_PDF, "rb") as f_b, open(POLICY_PDF, "rb") as f_p, open(REJECTION_PDF, "rb") as f_r:
        files = {
            "hospital_bill": ("apollo_hospital_bill.pdf", f_b, "application/pdf"),
            "insurance_policy": ("icici_lombard_policy.pdf", f_p, "application/pdf"),
            "rejection_letter": ("mediassist_rejection_letter.pdf", f_r, "application/pdf"),
        }
        data = {
            "patient_name": "Dr. Suniti Mukherjee",
            "patient_email": "suniti.mukherjee@example.com",
            "patient_phone": "+919876543210"
        }
        headers = {
            "X-Portal-Secret": "secret_hyper_adversarial_verification_token_1234"
        }
        resp = client.post("/api/portal/submit", data=data, files=files, headers=headers)
        assert resp.status_code == 200, f"Submit failed: {resp.text}"
        submit_data = resp.json()

    claim_id = submit_data["claim_id"]
    portal_secret = submit_data["portal_secret"]

    async def execute_pipeline():
        async with sessions() as db:
            ar_res = await db.execute(select(AnalysisRun).where(AnalysisRun.claim_id == claim_id))
            ar = ar_res.scalar_one()
            ar_id = ar.id
        await run_analysis_pipeline(claim_id, ar_id)

    asyncio.run(execute_pipeline())

    status_resp = client.get(f"/api/portal/status/{claim_id}", headers={"X-Portal-Secret": portal_secret})
    assert status_resp.status_code == 200, f"Status failed: {status_resp.text}"
    status_data = status_resp.json()
    assert status_data.get("status") == "COMPLETED"

    result = status_data.get("result")
    assert result is not None
    assert result.get("overall_status") == "MISMATCH_DETECTED"
    assert result.get("recoverable_amount") == 682000.0
    assert result.get("estimated_discrepancy") == 682000.0
    assert result.get("violations_found") == 4

    violations = result.get("violations", [])
    assert len(violations) == 4

    card_rules = {c["rule"]: c for c in violations}
    assert "Modern Treatment Inpatient Protection Rule" in card_rules
    assert "Clause Timeline Rule" in card_rules
    assert "Proportionate Deduction Rule" in card_rules
    assert "Non-Payable Items Rule" in card_rules

    total_rec = 0.0
    for card in violations:
        assert card.get("actual_claim_fact") and len(card.get("actual_claim_fact")) > 10
        assert card.get("applicable_policy_rule") and len(card.get("applicable_policy_rule")) > 10
        assert card.get("insurer_applied_action") and len(card.get("insurer_applied_action")) > 10
        assert card.get("expected_action") and len(card.get("expected_action")) > 10
        assert card.get("citation") and len(card.get("citation")) > 10
        assert card.get("recoverable") is not None and card.get("recoverable") > 0
        total_rec += card.get("recoverable")

        card_str = json.dumps(card).lower()
        assert "nan" not in card_str
        assert "undefined" not in card_str

    assert total_rec == 682000.0


