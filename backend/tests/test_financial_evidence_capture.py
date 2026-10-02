from types import SimpleNamespace

from app.schemas.evidence_ledger import EvidenceLedger
from app.schemas.provenance import Provenance
from app.utils.evidence_capture import validate_and_record_financial_evidence


def test_financial_evidence_is_bound_to_uploaded_document_and_ledger():
    bill = SimpleNamespace(
        total_amount=Provenance(
            value=1250.0,
            source_text="Net Total Rs 1,250",
            page="1",
            extraction_confidence=0.94,
        ),
        subtotal=None,
        line_items=[],
    )
    document = SimpleNamespace(
        id="doc-1",
        document_type="HOSPITAL_BILL",
        document_hash="a" * 64,
    )
    ledger = EvidenceLedger(claim_id="claim-1")

    issues = validate_and_record_financial_evidence(
        bill, document, "NET TOTAL Rs 1,250", ledger
    )

    assert issues == []
    assert bill.total_amount.source_document_id == "doc-1"
    assert bill.total_amount.source_hash == "a" * 64
    assert len(ledger.entries) == 1
    assert ledger.entries[0].document_id == "doc-1"
    assert ledger.entries[0].extracted_value == 1250.0


def test_unverifiable_financial_value_blocks_evidence_capture():
    bill = SimpleNamespace(
        total_amount=Provenance(value=1250.0),
        subtotal=None,
        line_items=[],
    )
    document = SimpleNamespace(
        id="doc-1",
        document_type="HOSPITAL_BILL",
        document_hash="a" * 64,
    )
    ledger = EvidenceLedger(claim_id="claim-1")

    issues = validate_and_record_financial_evidence(
        bill, document, "NET TOTAL Rs 1,250", ledger
    )

    assert "MISSING_SOURCE_TEXT:total_amount" in issues
    assert ledger.entries == []


def test_amount_substring_must_match_complete_numeric_token_and_claimed_page():
    document = SimpleNamespace(id="doc-1", document_type="HOSPITAL_BILL", document_hash="a" * 64)
    ledger = EvidenceLedger(claim_id="claim-1")
    bill = SimpleNamespace(
        total_amount=Provenance(value=12.0, source_text="Total due Rs 1200", page="1", extraction_confidence=0.95),
        subtotal=None,
        line_items=[],
    )

    issues = validate_and_record_financial_evidence(bill, document, ["Total due Rs 1200", ""], ledger)

    assert "SOURCE_TEXT_NOT_VERIFIED:total_amount" in issues
    assert ledger.entries == []


def test_amount_citation_on_wrong_page_is_not_accepted():
    document = SimpleNamespace(id="doc-1", document_type="HOSPITAL_BILL", document_hash="a" * 64)
    ledger = EvidenceLedger(claim_id="claim-1")
    bill = SimpleNamespace(
        total_amount=Provenance(value=1250.0, source_text="Net Total Rs 1,250", page="2", extraction_confidence=0.95),
        subtotal=None,
        line_items=[],
    )

    issues = validate_and_record_financial_evidence(bill, document, ["Net Total Rs 1,250", "Other page"], ledger)

    assert "SOURCE_TEXT_NOT_VERIFIED:total_amount" in issues
    assert ledger.entries == []


def test_total_amount_requires_a_total_field_label_not_an_unrelated_payment():
    document = SimpleNamespace(id="doc-1", document_type="HOSPITAL_BILL", document_hash="a" * 64)
    ledger = EvidenceLedger(claim_id="claim-1")
    bill = SimpleNamespace(
        total_amount=Provenance(
            value=1200.0,
            source_text="Advance payment Rs 1,200",
            page="1",
            extraction_confidence=0.95,
        ),
        subtotal=None,
        line_items=[],
    )

    issues = validate_and_record_financial_evidence(
        bill, document, ["Advance payment Rs 1,200. Amount due Rs 9,800."], ledger
    )

    assert "SOURCE_FIELD_NOT_VERIFIED:total_amount" in issues
    assert ledger.entries == []


def test_policy_clause_requires_matching_page_snippet_and_is_recorded():
    clause = Provenance(value="Room rent is limited to 1% of sum insured", source_text="Room rent is limited to 1% of sum insured", page="2", extraction_confidence=0.92)
    policy = SimpleNamespace(
        sum_insured=None,
        room_rent_limit_per_day=None,
        copay_percentage=None,
        deductible=None,
        proportionate_deduction_rule=SimpleNamespace(policy_clause=clause, threshold_value=None, source_text=None),
        sub_limits=[],
        waiting_periods=[],
        deduction_order_clause=None,
    )
    document = SimpleNamespace(id="policy-1", document_type="INSURANCE_POLICY", document_hash="b" * 64)
    ledger = EvidenceLedger(claim_id="claim-1")

    issues = validate_and_record_financial_evidence(policy, document, ["Other coverage", "Room rent is limited to 1% of sum insured"], ledger)

    assert issues == []
    assert clause.source_document_id == "policy-1"
    assert ledger.entries[0].page_number == 2
