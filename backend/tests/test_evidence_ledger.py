"""
Unit and integration tests for Milestone 1 Features F01-F04:
- F01: Provenance[T] Type Operability (dunders, primitive equality, cross-type coercion, delegation)
- F02: Standalone Evidence Ledger Schema (EvidenceLedgerEntry, EvidenceLedger collection, validators)
- F03: FinancialMath Lineage Preservation & SafeDecimal
- F04: Document SHA-256 Hashing & Database Persistence (Document.document_hash, EvidenceLedgerRecord)
"""

import hashlib
import io
import math
import os
import uuid
from decimal import Decimal
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.engine.adjudication_state import AdjudicationState, LineItemState
from app.engine.calculator import FinancialMath, SafeDecimal
from app.models.claim import Claim, Document, EvidenceLedgerRecord, RuleVerdictRecord
from app.schemas.evidence_ledger import EvidenceLedger, EvidenceLedgerEntry
from app.schemas.provenance import Provenance, Transformation
from app.utils.file_handler import (
    compute_sha256_bytes,
    compute_sha256_file,
    save_upload,
)


# =============================================================================
# Database Fixture for Integration Tests
# =============================================================================

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


# =============================================================================
# F01 Tests: Provenance[T] Operability & Dunder Design
# =============================================================================

def test_provenance_equality_and_ordering():
    p_float = Provenance[float](value=1500.0)
    p_str = Provenance[str](value="MED-TR-10")
    p_int = Provenance[int](value=42)

    # Equality against primitives
    assert p_float == 1500.0
    assert 1500.0 == p_float
    assert p_str == "MED-TR-10"
    assert "MED-TR-10" == p_str
    assert p_int == 42
    assert 42 == p_int

    # Inequality
    assert p_float != 1200.0
    assert p_str != "OTHER"

    # Equality between Provenance instances
    assert p_float == Provenance[float](value=1500.0)
    assert p_str == Provenance[str](value="MED-TR-10")

    # Ordering comparisons
    assert p_float > 1000.0
    assert p_float >= 1500.0
    assert p_float < 2000.0
    assert p_float <= 1500.0
    assert 1000.0 < p_float
    assert 2000.0 > p_float

    # Comparison with Decimal
    assert p_float == Decimal("1500.0")
    assert p_float > Decimal("1000.0")
    assert p_float < Decimal("2000.0")


def test_provenance_arithmetic_operators():
    p1 = Provenance[float](value=100.0)
    p2 = Provenance[float](value=25.0)

    # Standard binary arithmetic
    assert p1 + p2 == 125.0
    assert p1 - p2 == 75.0
    assert p1 * p2 == 2500.0
    assert p1 / p2 == 4.0
    assert p1 // p2 == 4
    assert p1 % p2 == 0.0
    assert p2**2 == 625.0

    # Reverse arithmetic (primitive on left)
    assert 50.0 + p1 == 150.0
    assert 200.0 - p1 == 100.0
    assert 2.0 * p1 == 200.0
    assert 500.0 / p1 == 5.0
    assert 250.0 // p1 == 2.0
    assert 250.0 % p1 == 50.0

    # Unary operators
    assert -p1 == -100.0
    assert +p1 == 100.0

    # Sum across iterable
    items = [Provenance[float](value=10.0), Provenance[float](value=20.0), Provenance[float](value=30.0)]
    assert sum(items) == 60.0


def test_provenance_numeric_conversions_and_formatting():
    p = Provenance[float](value=1234.567)

    # Conversions
    assert float(p) == 1234.567
    assert int(p) == 1234
    assert round(p, 2) == 1234.57
    assert round(p) == 1235
    assert math.floor(p) == 1234
    assert math.ceil(p) == 1235
    assert math.trunc(p) == 1234
    assert abs(Provenance[float](value=-50.0)) == 50.0

    # Boolean logic
    assert bool(Provenance[bool](value=True)) is True
    assert bool(Provenance[bool](value=False)) is False
    assert bool(Provenance[int](value=0)) is False
    assert bool(Provenance[int](value=1)) is True

    # Representations & f-string formatting
    assert str(p) == "1234.567"
    assert "Provenance(1234.567)" in repr(p)
    assert f"₹{p:.2f}" == "₹1234.57"

    # Hashability in sets and dict keys
    s = {p, Provenance[float](value=1234.567)}
    assert len(s) == 1
    d = {p: "amount"}
    assert d[p] == "amount"


def test_provenance_method_and_container_delegation():
    p_name = Provenance[str](value="Apollo Speciality Hospital")

    # String method delegation via __getattr__
    assert p_name.lower() == "apollo speciality hospital"
    assert p_name.upper() == "APOLLO SPECIALITY HOSPITAL"
    assert p_name.startswith("Apollo") is True
    assert p_name.split()[0] == "Apollo"

    # Container operations
    assert "Apollo" in p_name
    assert "Fortis" not in p_name
    assert len(p_name) == len("Apollo Speciality Hospital")
    assert p_name[0:6] == "Apollo"

    # Guard against intercepting private attributes
    with pytest.raises(AttributeError):
        _ = p_name._non_existent_private_attr


def test_provenance_wrap_primitive_no_double_wrapping():
    # Pass primitive
    p1 = Provenance[int].model_validate(100)
    assert p1.value == 100
    assert isinstance(p1.value, int)

    # Pass existing Provenance instance (prevent nesting)
    p2 = Provenance[int].model_validate(p1)
    assert p2.value == 100
    assert not isinstance(p2.value, Provenance)


# =============================================================================
# F02 Tests: Standalone Evidence Ledger Schema
# =============================================================================

def test_evidence_ledger_entry_valid_fields():
    entry = EvidenceLedgerEntry(
        claim_id="CLM-100",
        document_id="DOC-BILL-01",
        document_hash="a" * 64,
        page_number=2,
        bounding_box=[0.1, 0.1, 0.4, 0.5],
        section="Room Charges Table",
        source_text="Room Rent 5 days @ 8000/day = 40000",
        extracted_value=40000.0,
        normalized_value=40000.0,
        rule_id="RULE_ROOM_RENT_CAPPING",
        formula="days * daily_rate",
        calculation_inputs={"days": 5, "daily_rate": 8000},
        final_output=40000.0,
        confidence=0.98
    )

    assert entry.claim_id == "CLM-100"
    assert entry.document_id == "DOC-BILL-01"
    assert entry.document_hash == "a" * 64
    assert entry.page_number == 2
    assert entry.bounding_box == [0.1, 0.1, 0.4, 0.5]
    assert entry.section == "Room Charges Table"
    assert entry.confidence == 0.98
    assert entry.formula == "days * daily_rate"
    assert entry.final_output == 40000.0
    assert entry.entry_id is not None
    assert entry.created_at is not None


def test_evidence_ledger_entry_bounding_box_validation():
    # Length not equal to 4
    with pytest.raises(ValueError, match="exactly 4 coordinates"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="Test",
            bounding_box=[0.1, 0.2, 0.3]
        )

    # Coordinate out of range [0.0, 1.0]
    with pytest.raises(ValueError, match="normalized between 0.0 and 1.0"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="Test",
            bounding_box=[0.1, 0.2, 1.5, 0.4]
        )

    # ymin > ymax
    with pytest.raises(ValueError, match="ymin .* cannot be greater than ymax"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="Test",
            bounding_box=[0.8, 0.2, 0.3, 0.4]
        )

    # xmin > xmax
    with pytest.raises(ValueError, match="xmin .* cannot be greater than xmax"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="Test",
            bounding_box=[0.1, 0.9, 0.3, 0.4]
        )


def test_evidence_ledger_entry_from_provenance():
    prov = Provenance[float](
        value=5000.0,
        normalized_value=5000.0,
        source_document_id="DOC-POL-01",
        source_hash="b" * 64,
        page="3",
        section="Schedule of Benefits",
        source_text="Daily room rent capped at 5000 per day",
        extraction_confidence=0.95,
        bounding_box={"ymin": 0.1, "xmin": 0.2, "ymax": 0.3, "xmax": 0.4}
    )

    entry = EvidenceLedgerEntry.from_provenance(
        prov=prov,
        claim_id="CLM-POL-1",
        rule_id="RULE_ROOM_RENT",
        formula="policy_limit"
    )

    assert entry.claim_id == "CLM-POL-1"
    assert entry.document_id == "DOC-POL-01"
    assert entry.document_hash == "b" * 64
    assert entry.page_number == 3
    assert entry.bounding_box == [0.1, 0.2, 0.3, 0.4]
    assert entry.extracted_value == 5000.0
    assert entry.rule_id == "RULE_ROOM_RENT"
    assert entry.confidence == 0.95


def test_evidence_ledger_collection_and_queries():
    ledger = EvidenceLedger(claim_id="CLM-200")

    e1 = ledger.record_extraction(
        document_id="DOC-BILL-1",
        document_hash="c" * 64,
        page_number=1,
        source_text="Total Billed: 100000",
        extracted_value=100000.0,
        section="Bill Summary",
        confidence=0.99
    )

    e2 = ledger.record_calculation(
        rule_id="RULE_PROPORTIONATE_DEDUCTION",
        formula="100000 * (4000 / 6000)",
        calculation_inputs={"eligible": 4000, "billed": 6000},
        final_output=66666.67
    )

    assert len(ledger) == 2
    assert ledger.get_by_id(e1.entry_id) == e1
    assert len(ledger.filter_by_document("DOC-BILL-1")) == 1
    assert len(ledger.filter_by_rule("RULE_PROPORTIONATE_DEDUCTION")) == 1
    assert len(ledger.filter_by_section("Bill Summary")) == 1
    assert ledger.verify_integrity() is True

    summary = ledger.summary()
    assert summary["claim_id"] == "CLM-200"
    assert summary["total_entries"] == 2
    assert "DOC-BILL-1" in summary["documents_referenced"]
    assert "RULE_PROPORTIONATE_DEDUCTION" in summary["rules_referenced"]
    assert summary["average_confidence"] > 0.95

    # Indexing and iteration
    items = [entry for entry in ledger]
    assert len(items) == 2
    assert ledger[0] == e1


# =============================================================================
# F03 Tests: SafeDecimal and FinancialMath Lineage
# =============================================================================

def test_safe_decimal_cross_type_arithmetic():
    sd = SafeDecimal("100.50")

    # Interoperability with float literals
    res_add = sd + 2.5
    assert isinstance(res_add, SafeDecimal)
    assert res_add == SafeDecimal("103.00")

    res_radd = 2.5 + sd
    assert isinstance(res_radd, SafeDecimal)
    assert res_radd == SafeDecimal("103.00")

    res_mul = sd * 1.15
    assert isinstance(res_mul, SafeDecimal)
    assert res_mul.round_currency() == SafeDecimal("115.58")

    res_rsub = 200.0 - sd
    assert isinstance(res_rsub, SafeDecimal)
    assert res_rsub == SafeDecimal("99.50")

    res_div = sd / 2.0
    assert isinstance(res_div, SafeDecimal)
    assert res_div == SafeDecimal("50.25")

    # String currency cleaning
    sd_curr = SafeDecimal(" ₹ 1,50,000.00 ")
    assert sd_curr == SafeDecimal("150000.00")

    # Pydantic v2 core schema serialization
    class MockModel(BaseModel):
        amount: SafeDecimal

    m = MockModel(amount=SafeDecimal("25000.75"))
    assert m.amount == SafeDecimal("25000.75")
    d = m.model_dump()
    assert d["amount"] == Decimal("25000.75")


def test_financial_math_operations_and_lineage():
    p_billed = Provenance[float](
        value=6000.0,
        source_document_id="DOC-BILL-101",
        source_hash="hash_bill_1",
        source_text="Room charges: 6000/day"
    )
    p_limit = Provenance[float](
        value=4000.0,
        source_document_id="DOC-POL-202",
        source_hash="hash_pol_2",
        source_text="Room rent limit: 4000/day"
    )
    p_days = Provenance[int](
        value=4,
        source_document_id="DOC-BILL-101",
        source_hash="hash_bill_1",
        source_text="Stay length: 4 days"
    )

    # 1. Subtraction with lineage capture
    excess = FinancialMath.sub(
        p_billed, p_limit, formula="actual_rate - limit", var_a="actual_rate", var_b="limit", rule_id="RULE_ROOM_RENT"
    )
    assert excess.value == SafeDecimal("2000.00")
    assert excess.source_document_id == "DOC-BILL-101, DOC-POL-202"
    assert len(excess.transformations) == 1
    assert "actual_rate" in excess.__dict__["calculation_inputs"]["operands"]
    assert "limit" in excess.__dict__["calculation_inputs"]["operands"]

    # 2. Multiplication chaining prior lineage
    total_excess = FinancialMath.mul(
        excess, p_days, formula="excess_per_day * stay_days", var_a="excess_per_day", var_b="stay_days"
    )
    assert total_excess.value == SafeDecimal("8000.00")
    assert total_excess.source_document_id == "DOC-BILL-101, DOC-POL-202"
    # Preserves 2-step transformation DAG
    assert len(total_excess.transformations) == 2
    assert total_excess.transformations[0].operation == "SUBTRACT"
    assert total_excess.transformations[1].operation == "MULTIPLY"

    # 3. Sum over items
    p_ot = Provenance[float](value=30000.0, source_document_id="DOC-BILL-101")
    p_pharm = Provenance[float](value=12000.0, source_document_id="DOC-BILL-101")
    tot = FinancialMath.sum([p_ot, p_pharm])
    assert tot.value == SafeDecimal("42000.00")

    # 4. Percentage calculation
    copay = FinancialMath.calculate_percentage(tot, 10.0)
    assert copay.value == SafeDecimal("4200.00")

    # 5. Min / Max
    m_val = FinancialMath.min(tot, 50000.0)
    assert m_val.value == SafeDecimal("42000.00")


def test_financial_math_evidence_ledger_bridge():
    p_base = Provenance[float](
        value=50000.0,
        source_document_id="DOC-BILL-1",
        source_hash="h1" * 32
    )
    calc_res = FinancialMath.calculate_percentage(
        p_base, 15.0, formula="50000 * 15%", rule_id="RULE_COPAY"
    )

    ledger = EvidenceLedger(claim_id="CLM-BRIDGE-1")
    entry = FinancialMath.record_in_ledger(ledger, calc_res, claim_id="CLM-BRIDGE-1", rule_id="RULE_COPAY")

    assert len(ledger) == 1
    assert entry.rule_id == "RULE_COPAY"
    assert entry.formula == "50000 * 15%"
    assert entry.final_output == SafeDecimal("7500.00")
    assert "base_amount" in entry.calculation_inputs["operands"]


def test_adjudication_state_reconciliation_exact_paise():
    state = AdjudicationState(claim_id="CLM-RECON-1")
    state.line_items["R1"] = LineItemState(
        item_code="R1", category="ROOM", original_amount=10000.0, remaining_balance=10000.0
    )
    state.line_items["O1"] = LineItemState(
        item_code="O1", category="OT", original_amount=25000.0, remaining_balance=25000.0
    )

    # Apply deduction
    adj1 = state.apply_deduction(
        rule_id="RULE_ROOM_RENT",
        target_item_codes=["R1"],
        deduction_amount=SafeDecimal("2500.00"),
        formula="Excess room rent"
    )
    assert adj1 is not None
    assert state.get_balance("R1") == SafeDecimal("7500.00")

    # Verify reconciliation passes
    assert state.verify_reconciliation() is True


# =============================================================================
# F04 Tests: Document SHA-256 Hashing Utilities & Persistence
# =============================================================================

def test_hashing_utilities(tmp_path):
    data = b"ClaimGuard AI Test Hospital Bill Verification Payload"
    expected_hash = hashlib.sha256(data).hexdigest()

    # Byte computation
    assert compute_sha256_bytes(data) == expected_hash

    # Streaming file computation
    file_path = tmp_path / "test_doc.bin"
    file_path.write_bytes(data)
    assert compute_sha256_file(str(file_path)) == expected_hash


@pytest.mark.asyncio
async def test_save_upload_streaming_hash(tmp_path):
    data = b"%PDF-1.4 Mock PDF Content for In-Flight SHA256 Verification"
    expected_hash = hashlib.sha256(data).hexdigest()

    upload = UploadFile(
        file=io.BytesIO(data),
        filename="test_upload.pdf",
        headers={"content-type": "application/pdf"}
    )

    upload_dir = str(tmp_path / "uploads")
    path, mime, size, sha256_hash = await save_upload(upload, upload_dir)

    assert os.path.exists(path)
    assert mime == "application/pdf"
    assert size == len(data)
    assert sha256_hash == expected_hash


@pytest.mark.asyncio
async def test_database_persistence_of_document_hash_and_evidence_ledger(async_db: AsyncSession):
    claim = Claim(id="CLM-SQL-01", patient_name="Priya Sharma", status="PENDING")
    async_db.add(claim)
    await async_db.flush()

    doc_hash = hashlib.sha256(b"Document Content").hexdigest()
    doc = Document(
        id="DOC-SQL-01",
        claim_id=claim.id,
        document_type="HOSPITAL_BILL",
        filename="bill.pdf",
        file_path="/tmp/bill.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        document_hash=doc_hash
    )
    async_db.add(doc)

    ev_record = EvidenceLedgerRecord(
        id="EV-SQL-01",
        claim_id=claim.id,
        document_id=doc.id,
        document_hash=doc_hash,
        page_number=1,
        source_text="Room charges: Rs. 5000",
        extracted_value=5000.0,
        normalized_value=5000.0,
        rule_id="RULE_ROOM_RENT",
        formula="daily_rate",
        confidence=0.99
    )
    async_db.add(ev_record)
    await async_db.commit()

    # Query Document and verify document_hash
    doc_res = await async_db.execute(select(Document).where(Document.id == "DOC-SQL-01"))
    fetched_doc = doc_res.scalar_one()
    assert fetched_doc.document_hash == doc_hash
    assert fetched_doc.claim_id == claim.id

    # Query EvidenceLedgerRecord and verify fields
    ev_res = await async_db.execute(select(EvidenceLedgerRecord).where(EvidenceLedgerRecord.id == "EV-SQL-01"))
    fetched_ev = ev_res.scalar_one()
    assert fetched_ev.document_hash == doc_hash
    assert fetched_ev.extracted_value == 5000.0
    assert fetched_ev.rule_id == "RULE_ROOM_RENT"
    assert fetched_ev.confidence == 0.99
