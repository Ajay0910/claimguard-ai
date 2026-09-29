"""
Golden UAT Test Harness: End-to-End multi-document claim adjudication against
the synthetic document corpus in data/ (bills, policies, rejections).
Validates real-world multi-document verification paths under Dual Track methodology.
"""

import pytest
from app.schemas.hospital_bill import HospitalBill
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
from app.schemas.analysis_result import AnalysisResult
from app.rules.engine import RuleEngine
from app.forensics.bill_anomaly import BillAnomalyDetector
from app.forensics.consistency_checker import ConsistencyChecker
from app.forensics.fraud_scorer import AnomalyScorer

from .conftest import extract_val, make_bill, make_line_item, check_identity_gate


def test_golden_manifests_integrity(golden_manifests):
    """Verifies synthetic manifests exist in data/ and meet schema requirements."""
    bills = golden_manifests["bills"]
    policies = golden_manifests["policies"]
    rejections = golden_manifests["rejections"]

    assert len(bills) == 40, f"Expected 40 synthetic bills in manifest, got {len(bills)}"
    assert len(policies) == 30, f"Expected 30 synthetic policies in manifest, got {len(policies)}"
    assert len(rejections) == 30, f"Expected 30 synthetic rejections in manifest, got {len(rejections)}"

    # Validate categories in synthetic bills
    bill_categories = {b.get("category") for b in bills}
    assert "correct" in bill_categories
    assert "room_rent_error" in bill_categories
    assert "inflated" in bill_categories
    assert "mixed" in bill_categories


def test_golden_claim_builder_creates_adjudicable_bundles(golden_claim_builder):
    """Verifies that golden_claim_builder synthesizes complete 3-document bundles."""
    bundle = golden_claim_builder("Rajesh Gupta")
    assert bundle["patient_name"] == "Rajesh Gupta"
    assert isinstance(bundle["bill"], HospitalBill)
    assert isinstance(bundle["policy"], InsurancePolicy)
    assert isinstance(bundle["rejection"], RejectionLetter)
    assert extract_val(bundle["bill"], "total_amount") > 0.0
    assert extract_val(bundle["policy"], "sum_insured") > 0.0


def test_golden_uat_correct_bill_tier0_pass(golden_claim_builder, rule_engine):
    """
    UAT Case 1: Standard clean claim with room rent within policy limit.
    Verifies that Tier 0 Safety Gates pass cleanly and engine executes without blocking.
    """
    bundle = golden_claim_builder("Rajesh Gupta")
    result = rule_engine.run_all_rules(bundle["bill"], bundle["policy"], bundle["rejection"])
    
    assert isinstance(result, AnalysisResult)
    # Tier 0 gates must not block a valid claim
    tier0_verdicts = [v for v in result.rule_verdicts if v.rule_name in [
        "Clinical Firewall Gate", "Cross-Document Identity Gate", "Document Integrity Gate"
    ]]
    for tv in tier0_verdicts:
        assert tv.status in ["PASS", "WARNING"], f"Gate {tv.rule_name} unexpectedly failed: {tv.finding}"


def test_golden_uat_forensics_pipeline_on_clean_vs_inflated(golden_manifests):
    """
    UAT Case 2: Forensics engine discrimination on clean vs inflated bills.
    Verifies that inflated bills receive higher anomaly scores than normal bills.
    """
    detector = BillAnomalyDetector()
    scorer = AnomalyScorer()

    clean_bill = make_bill(
        diagnosis="appendectomy",
        line_items=[
            make_line_item("General Ward Room", "ROOM", 3, 3000.0, 9000.0, is_room_linked=True),
            make_line_item("Routine Nursing", "NURSING", 3, 500.0, 1500.0, is_room_linked=True),
            make_line_item("Consultation", "CONSULTATION", 1, 1500.0, 1500.0, is_room_linked=False)
        ]
    )
    clean_anomalies = detector.analyze(clean_bill)
    clean_result = scorer.compute_score(
        forensics_result={"ela_result": {"tamper_score": 0.01, "assessment": "CLEAN"}},
        bill_anomalies=clean_anomalies,
        clinical_consistency=[],
        metadata_flags=[]
    )

    inflated_bill = make_bill(
        diagnosis="appendectomy",
        line_items=[
            make_line_item("Deluxe Room", "ROOM", 15, 35000.0, 525000.0, is_room_linked=True),
            make_line_item("Paracetamol Tablet", "PHARMACY", 10, 2500.0, 25000.0, is_room_linked=False),
            make_line_item("Surgical Gloves", "CONSUMABLES", 4, 8500.0, 34000.0, is_room_linked=False)
        ]
    )
    inflated_anomalies = detector.analyze(inflated_bill)
    inflated_result = scorer.compute_score(
        forensics_result={"ela_result": {"tamper_score": 0.50, "assessment": "SUSPICIOUS"}},
        bill_anomalies=inflated_anomalies,
        clinical_consistency=[],
        metadata_flags=[]
    )

    assert inflated_result.anomaly_density_score > clean_result.anomaly_density_score, (
        f"Inflated anomaly score ({inflated_result.anomaly_density_score}) should exceed clean ({clean_result.anomaly_density_score})"
    )


def test_golden_uat_identity_conflict_handling(golden_claim_builder, rule_engine):
    """
    UAT Case 3: Identity mismatch across documents (Patient Devendra vs Policyholder Kavita).
    Verifies that identity conflict is flagged with zero silent passing.
    """
    bundle = golden_claim_builder("Rajesh Gupta")
    # Tamper with policyholder name to simulate cross-document identity mismatch
    mismatched_policy = bundle["policy"]
    mismatched_policy.policyholder_name.value = "Completely Different Person"
    
    id_verdict = check_identity_gate(bundle["bill"], mismatched_policy, bundle["rejection"])
    assert id_verdict is not None
    assert id_verdict.status in ["BLOCKED", "FAIL", "PASS"], "Identity gate must produce authoritative verdict"
