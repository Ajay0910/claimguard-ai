import pytest
from app.schemas.analysis_result import RuleVerdict, AnalysisResult
from app.schemas.evidence_ledger import EvidenceLedgerEntry
from app.reports.generator import ReportGenerator
from app.schemas.hospital_bill import HospitalBill
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
from app.extraction.pipeline import ExtractionPipeline
import uuid

def test_point14_safe_failure_on_low_confidence():
    # When evidence is insufficient, do not guess
    # Enforce INSUFFICIENT_EVIDENCE state when confidence drops
    
    # 1. Pipeline should convert low confidence to INSUFFICIENT_EVIDENCE
    class MockExtractionResult:
        extraction_confidence = 0.5
        
    pipeline = ExtractionPipeline(config={"vlm_api_key": ""})
    status, issues = pipeline._validate_extraction('bill', MockExtractionResult())
    assert status == "INSUFFICIENT_EVIDENCE"
    assert "LOW_CONFIDENCE" in issues
    
    # 2. RuleVerdict should convert to INSUFFICIENT_EVIDENCE when confidence < 0.8
    verdict = RuleVerdict(
        rule_name="Test Rule",
        status="FAIL",
        finding="Test finding",
        confidence=0.7,
        evidence_entries=[
            EvidenceLedgerEntry(
                claim_id="test",
                document_id="doc1",
                document_hash="hash",
                page_number=1,
                bounding_box=[0.1, 0.1, 0.2, 0.2],
                source_text="Test",
                value="Test",
                source_document_type="bill",
                model="test_model",
                extraction_confidence=0.7,
                timestamp="2023-01-01T00:00:00Z",
                transformations=["test"]
            )
        ]
    )
    
    assert verdict.status == "INSUFFICIENT_EVIDENCE"
    assert verdict.confidence < 0.8

def test_point15_appeal_integrity():
    # Guarantee the appeal generator is strictly downstream of verified findings.
    # Every appeal statement must provably originate from a validated Evidence Ledger entry.
    generator = ReportGenerator()
    
    bill = HospitalBill(bill_id="b1", total_amount=100.0, hospital_name="Test", patient_name="Test", line_items=[], subtotal=100.0, net_payable=100.0)
    policy = InsurancePolicy(policy_number="p1", sum_insured=1000.0, insurer_name="Test", policyholder_name="Test", policy_holder_name="Test", policy_start_date="2023-01-01", policy_end_date="2024-01-01")
    rejection = RejectionLetter(rejection_id="r1", total_claimed=100.0, reference_number="r1", insurer_name="Test", policyholder_name="Test", policy_number="p1", claim_number="c1", claim_date="2023-01-01", total_approved=0.0, total_deducted=100.0, rejection_reasons=[], settlement_type="FULL_REJECTION")
    
    # AnalysisResult with FAIL but NO evidence entries
    verdict_no_evidence = RuleVerdict(
        rule_name="Test Rule",
        status="FAIL",
        finding="Test finding without evidence",
        confidence=1.0,
        evidence_entries=[]
    )
    
    analysis_no_ev = AnalysisResult(
        claim_id="test_claim",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=[verdict_no_evidence],
        summary="Test summary"
    )
    
    appeal_text1 = generator.generate_appeal_letter(analysis_no_ev, bill, policy, rejection)
    assert "lack sufficient validated evidence ledger entries" in appeal_text1
    
    # AnalysisResult with FAIL AND evidence entries
    verdict_with_evidence = RuleVerdict(
        rule_name="Test Rule",
        status="FAIL",
        finding="Test finding with evidence",
        confidence=1.0,
        evidence_entries=[
            EvidenceLedgerEntry(
                claim_id="test",
                document_id="doc1",
                document_hash="hash",
                page_number=1,
                bounding_box=[0.1, 0.1, 0.2, 0.2],
                source_text="Test",
                value="Test",
                source_document_type="bill",
                model="test_model",
                extraction_confidence=0.9,
                timestamp="2023-01-01T00:00:00Z",
                transformations=["test"]
            )
        ]
    )
    
    analysis_with_ev = AnalysisResult(
        claim_id="test_claim",
        overall_status="MISMATCH_DETECTED",
        rule_verdicts=[verdict_with_evidence],
        summary="Test summary"
    )
    
    appeal_text2 = generator.generate_appeal_letter(analysis_with_ev, bill, policy, rejection)
    assert "lack sufficient validated evidence ledger entries" not in appeal_text2
    assert "Test finding with evidence" in appeal_text2
