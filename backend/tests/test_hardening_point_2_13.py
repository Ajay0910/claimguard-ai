import pytest
from app.schemas.analysis_result import RuleVerdict, AnalysisResult
from app.schemas.evidence_ledger import EvidenceLedgerEntry
from app.forensics.fraud_scorer import AnomalyScorer
from app.schemas.provenance import Provenance

def test_point_2_source_type_mapping():
    # POLICY_MISMATCH should map to POLICY
    v1 = RuleVerdict(rule_name="T1", status="FAIL", finding="Policy mismatch", finding_type="POLICY_MISMATCH")
    assert v1.source_type == "POLICY"
    
    # REGULATORY_CONFLICT should map to REGULATION
    v2 = RuleVerdict(rule_name="T2", status="FAIL", finding="Reg conflict", finding_type="REGULATORY_CONFLICT")
    assert v2.source_type == "REGULATION"

    # FINANCIAL_DISCREPANCY should map to CALCULATION
    v3 = RuleVerdict(rule_name="T3", status="FAIL", finding="Fin discrepancy", finding_type="FINANCIAL_DISCREPANCY")
    assert v3.source_type == "CALCULATION"

def test_point_2_financial_discrepancy_not_fraud():
    scorer = AnomalyScorer()
    
    # Financial discrepancy (billing anomaly) without forensics/metadata tampering
    billing_flags = [{"anomaly_type": "TARIFF_DEVIATION", "severity": "HIGH", "description": "Overcharged"}]
    
    res = scorer.compute_score(
        forensics_result=None,
        bill_anomalies=billing_flags,
        clinical_consistency=None,
        metadata_flags=None
    )
    
    # Must not trigger high fraud alert automatically if forensics are clean
    assert res.review_status in ["CLEAN", "NEEDS_REVIEW", "FLAGGED FOR REVIEW"] 
    # Because we capped billing at 0.25 (25% + base 2%), overall score should be around 27-30%, not >50% (FLAGGED FOR REVIEW is <75% and NEEDS_REVIEW is <50%).
    # Specifically, with base_risk = 2.0, b_score_clean = 0.25, weight = 0.30 -> +7.5% -> 9.5%
    # So review_status should be "CLEAN".
    assert res.anomaly_density_score < 30.0

def test_point_13_evidence_ledger_completeness_check():
    # Complete evidence
    complete_ev = EvidenceLedgerEntry(
        claim_id="C1",
        document_id="doc1",
        document_hash="hash1",
        page_number=1,
        section="Sec1",
        source_text="some text",
        extracted_value="value",
        value="value",
        normalized_value="value",
        source_document_type="Bill",
        model="gemini-pro",
        bounding_box=[0.1, 0.1, 0.2, 0.2]
    )
    v1 = RuleVerdict(rule_name="T1", status="FAIL", finding="F1", evidence_entries=[complete_ev])
    # Should maintain high confidence
    assert v1.confidence == 1.0

    # Incomplete evidence (missing bounding box)
    incomplete_ev = EvidenceLedgerEntry(
        claim_id="C1",
        document_id="doc1",
        document_hash="hash1",
        page_number=1,
        section="Sec1",
        source_text="some text",
        extracted_value="value",
        value="value",
        normalized_value="value",
        source_document_type="Bill",
        model="gemini-pro"
    )
    v2 = RuleVerdict(rule_name="T2", status="FAIL", finding="F2", evidence_entries=[incomplete_ev])
    # Should downgrade confidence
    assert v2.confidence < 0.8
    
    # Calculation evidence missing formula
    calc_ev = EvidenceLedgerEntry(
        claim_id="C1",
        document_id="SYSTEM",
        document_hash="SYSTEM_DETERMINISTIC",
        rule_id="R1",
        calculation_output=100.0,
        formula="" # Missing
    )
    v3 = RuleVerdict(rule_name="T3", status="FAIL", finding="F3", evidence_entries=[calc_ev])
    assert v3.confidence < 0.8

def test_point_13_from_provenance_extraction():
    prov = Provenance(
        value="123",
        normalized_value=123,
        source_document_id="doc_xyz",
        source_document_type="Invoice",
        source_hash="abcd",
        page="2",
        section="Totals",
        bounding_box={"ymin": 0.1, "xmin": 0.2, "ymax": 0.3, "xmax": 0.4},
        source_text="Total: 123",
        extraction_confidence=0.99,
        extraction_model="test-model"
    )
    
    ev = EvidenceLedgerEntry.from_provenance(prov, claim_id="C_999")
    assert ev.value == "123"
    assert ev.normalized_value == 123
    assert ev.document_id == "doc_xyz"
    assert ev.source_document_type == "Invoice"
    assert ev.document_hash == "abcd"
    assert ev.page_number == 2
    assert ev.section == "Totals"
    assert ev.bounding_box == [0.1, 0.2, 0.3, 0.4]
    assert ev.source_text == "Total: 123"
    assert ev.extraction_confidence == 0.99
    assert ev.model == "test-model"
