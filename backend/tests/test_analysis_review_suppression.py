from app.api.analysis import suppress_financial_conclusion_when_review_needed
from app.schemas.analysis_result import AnalysisResult, RuleVerdict


def test_review_needed_verdict_hides_all_financial_conclusions():
    result = AnalysisResult(
        claim_id="claim-review",
        overall_status="MISMATCH_DETECTED",
        summary="A difference was found.",
        rule_verdicts=[RuleVerdict(
            rule_name="Low confidence rule",
            status="NEEDS_REVIEW",
            confidence=0.5,
            finding="Evidence needs verification.",
            monetary_impact=5000,
        )],
        total_monetary_impact=5000,
        expected_admissible_amount=10000,
        insurer_approved_amount=5000,
        billed_amount=12000,
        total_disallowed=7000,
        legitimate_deduction=2000,
        approved_pct=41.6,
        recoverable_pct=41.6,
        legitimate_pct=16.6,
        recovery_yield="100%",
    )

    suppress_financial_conclusion_when_review_needed(result)

    assert result.overall_status == "REVIEW_RECOMMENDED"
    assert result.total_monetary_impact is None
    assert result.expected_admissible_amount is None
    assert result.billed_amount is None
    assert result.recovery_yield is None
    assert result.rule_verdicts[0].monetary_impact is None
    assert result.rule_verdicts[0].insurer_calculation is None


def test_extraction_failure_status_is_preserved():
    result = AnalysisResult(
        claim_id="claim-failed",
        overall_status="EXTRACTION_FAILED",
        summary="Extraction failed.",
        rule_verdicts=[RuleVerdict(
            rule_name="Extraction",
            status="INSUFFICIENT_EVIDENCE",
            confidence=0.0,
            finding="No structured data.",
        )],
    )

    suppress_financial_conclusion_when_review_needed(result)

    assert result.overall_status == "EXTRACTION_FAILED"
