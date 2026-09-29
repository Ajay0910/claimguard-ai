import pytest
from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.extraction.pipeline import ExtractionPipeline
from app.rules.engine import RuleEngine

def test_point5_extraction_validation_arithmetic():
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "dummy"})
    
    # Missing arithmetic_verified should result in NEEDS_REVIEW
    bill = HospitalBill(
        bill_id="B1",
        total_amount=100.0,
        hospital_name="H1",
        patient_name="P1",
        line_items=[],
        subtotal=100.0,
        net_payable=100.0,
        arithmetic_verified=False
    )
    
    status, issues = pipeline._validate_extraction('bill', bill)
    assert status == "NEEDS_REVIEW"
    assert "ARITHMETIC_MISMATCH" in issues

def test_point5_extraction_validation_low_confidence():
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "dummy"})
    
    bill = HospitalBill(
        bill_id="B1",
        total_amount=100.0,
        hospital_name="H1",
        patient_name="P1",
        line_items=[],
        subtotal=100.0,
        net_payable=100.0,
        arithmetic_verified=True,
        extraction_confidence=0.5
    )
    
    status, issues = pipeline._validate_extraction('bill', bill)
    assert status == "INSUFFICIENT_EVIDENCE"
    assert "LOW_CONFIDENCE" in issues

def test_point10_cross_document_adjudication():
    engine = RuleEngine()
    
    bill = HospitalBill(
        bill_id="B1",
        total_amount=15000.0,
        hospital_name="H1",
        patient_name="P1",
        line_items=[BillLineItem(item_code="L1", description="Room", category="ROOM", quantity=1.0, unit_rate=15000.0, amount=15000.0, total=15000.0)],
        subtotal=15000.0,
        net_payable=15000.0,
        arithmetic_verified=True
    )
    
    policy = InsurancePolicy(
        policy_number="POL123",
        insurer_name="Insurer X",
        policyholder_name="P1",
        policy_start_date="2023-01-01",
        policy_end_date="2024-01-01",
        sum_insured=500000.0
    )
    
    rejection = RejectionLetter(
        reference_number="REF123",
        insurer_name="Insurer X",
        policyholder_name="P1",
        policy_number="POL123",
        claim_number="C1",
        claim_date="2023-06-01",
        total_claimed=15000.0,
        total_approved=10000.0,
        total_deducted=5000.0,
        settlement_type="PARTIAL_SETTLEMENT",
        rejection_reasons=[RejectionReason(code="R1", description="Non-medical", category="Non-Medical")]
    )
    
    verdict = engine.run_all_rules(bill, policy, rejection)
    cross_doc_verdict = next((v for v in verdict.rule_verdicts if v.rule_name == "Cross-Document Adjudication"), None)
    
    assert cross_doc_verdict is not None
    assert cross_doc_verdict.actual_claim_fact == "Patient billed 15000.0, but insurer approved only 10000.0."
    assert cross_doc_verdict.difference == 5000.0
    assert "Non-Medical" in cross_doc_verdict.applicable_policy_rule
    assert cross_doc_verdict.status == "NEEDS_REVIEW"
