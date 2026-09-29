"""
Shared fixtures and test data factories for ClaimGuard AI E2E testing suite.
Provides realistic hospital bills, policy schedules, rejection letters,
and helper builders complying with Pydantic schemas.
"""

import pytest
import pytest_asyncio
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.schemas.hospital_bill import HospitalBill, BillLineItem
from app.schemas.insurance_policy import InsurancePolicy, WaitingPeriodConfig, SubLimit, ProportionateDeductionRuleConfig
from app.schemas.rejection_letter import RejectionLetter, RejectionReason
from app.schemas.provenance import Provenance
from app.schemas.analysis_result import RuleVerdict, AnalysisResult
from app.rules.engine import RuleEngine
from app.rules.clinical_firewall import check_clinical_firewall
from app.rules.identity_gate import check_identity_gate
from app.rules.document_integrity import check_document_integrity
from app.models.claim import Base as ClaimBase


@pytest.fixture
def rule_engine() -> RuleEngine:
    return RuleEngine()


def make_line_item(
    description: str,
    category: str = "ROOM",
    quantity: float = 1.0,
    unit_rate: float = 5000.0,
    amount: Optional[float] = None,
    is_room_linked: bool = False,
    item_code: Optional[str] = None
) -> BillLineItem:
    calc_amount = amount if amount is not None else float(quantity * unit_rate)
    return BillLineItem(
        item_code=item_code,
        description=description,
        category=category,
        quantity=float(quantity),
        unit_rate=float(unit_rate),
        amount=calc_amount,
        total=calc_amount,
        is_room_linked=is_room_linked
    )


def make_bill(
    hospital_name: str = "Apollo Speciality Hospital",
    patient_name: str = "Rajesh Sharma",
    line_items: Optional[List[BillLineItem]] = None,
    admission_date: str = "2025-01-10",
    discharge_date: str = "2025-01-15",
    total_amount: Optional[float] = None,
    bill_id: str = "BILL-2025-001",
    diagnosis: str = "Acute Appendicitis",
    tax_amount: float = 0.0,
    discount: float = 0.0
) -> HospitalBill:
    if line_items is None:
        line_items = [
            make_line_item("Standard Private Room", "ROOM", 5, 4000.0, 20000.0, is_room_linked=True),
            make_line_item("Nursing Care Charges", "NURSING", 5, 1000.0, 5000.0, is_room_linked=True),
            make_line_item("Surgical Consultation Fee", "CONSULTATION", 1, 15000.0, 15000.0, is_room_linked=False),
            make_line_item("Operation Theatre Charges", "OT", 1, 25000.0, 25000.0, is_room_linked=False),
            make_line_item("Pharmacy & Post-Op Antibiotics", "PHARMACY", 1, 10000.0, 10000.0, is_room_linked=False)
        ]
    subtotal = sum(item.amount.value if hasattr(item.amount, 'value') else item.amount for item in line_items)
    tot = total_amount if total_amount is not None else subtotal + tax_amount - discount
    net = tot
    return HospitalBill(
        bill_id=bill_id,
        total_amount=tot,
        hospital_name=hospital_name,
        patient_name=patient_name,
        admission_date=admission_date,
        discharge_date=discharge_date,
        diagnosis=diagnosis,
        line_items=line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount=discount,
        net_payable=net
    )


def make_policy(
    policy_number: str = "POL-2024-HDF-9988",
    insurer_name: str = "HDFC ERGO General Insurance",
    policyholder_name: str = "Rajesh Sharma",
    policy_start_date: str = "2025-01-01",
    policy_end_date: str = "2025-12-31",
    sum_insured: float = 500000.0,
    room_rent_limit_per_day: Optional[float] = 5000.0,
    copay_percentage: float = 0.0,
    deductible: float = 0.0,
    inception_date: Optional[str] = "2020-01-01",
    moratorium_period_months: int = 60,
    portability_credits_months: int = 0,
    covers_mental_health: bool = True,
    waiting_periods: Optional[List[WaitingPeriodConfig]] = None,
    sub_limits: Optional[List[SubLimit]] = None
) -> InsurancePolicy:
    if waiting_periods is None:
        waiting_periods = [
            WaitingPeriodConfig(category="INITIAL", duration_days=30, applicable_conditions=["All illnesses except accidents"]),
            WaitingPeriodConfig(category="SPECIFIC_DISEASE", duration_days=730, applicable_conditions=["Hernia", "Cataract", "Joint Replacement"]),
            WaitingPeriodConfig(category="PED", duration_days=1095, applicable_conditions=["Pre-existing conditions"])
        ]
    if sub_limits is None:
        sub_limits = []
    return InsurancePolicy(
        policy_number=policy_number,
        insurer_name=insurer_name,
        policyholder_name=policyholder_name,
        policy_holder_name=policyholder_name,
        policy_start_date=policy_start_date,
        policy_end_date=policy_end_date,
        sum_insured=sum_insured,
        room_rent_limit_per_day=room_rent_limit_per_day,
        copay_percentage=copay_percentage,
        deductible=deductible,
        inception_date=inception_date,
        original_inception_date=inception_date,
        moratorium_period_months=moratorium_period_months,
        portability_credits_months=portability_credits_months,
        covers_mental_health=covers_mental_health,
        waiting_periods=waiting_periods,
        sub_limits=sub_limits,
        proportionate_deduction_rule=ProportionateDeductionRuleConfig(
            threshold_value=Provenance(value=1.0, source_type="POLICY"),
            threshold_operator=Provenance(value=">", source_type="POLICY"),
            threshold_source_type=Provenance(value="POLICY", source_type="POLICY")
        )
    )


def make_rejection(
    reference_number: str = "REJ-2025-00129",
    insurer_name: str = "HDFC ERGO General Insurance",
    policyholder_name: str = "Rajesh Sharma",
    policy_number: str = "POL-2024-HDF-9988",
    claim_number: str = "CLM-2025-0099",
    claim_date: str = "2025-01-12",
    total_claimed: float = 75000.0,
    total_approved: float = 50000.0,
    total_deducted: float = 25000.0,
    rejection_reasons: Optional[List[RejectionReason]] = None,
    settlement_type: str = "PARTIAL_SETTLEMENT",
    remarks: Optional[str] = None
) -> RejectionLetter:
    if rejection_reasons is None:
        rejection_reasons = []
    return RejectionLetter(
        reference_number=reference_number,
        insurer_name=insurer_name,
        policyholder_name=policyholder_name,
        policy_number=policy_number,
        claim_number=claim_number,
        claim_date=claim_date,
        total_claimed=total_claimed,
        total_approved=total_approved,
        approved_amount=total_approved,
        total_deducted=total_deducted,
        rejection_reasons=rejection_reasons,
        reasons=rejection_reasons,
        settlement_type=settlement_type,
        remarks=remarks
    )


@pytest.fixture
def base_bill() -> HospitalBill:
    return make_bill()


@pytest.fixture
def base_policy() -> InsurancePolicy:
    return make_policy()


@pytest.fixture
def base_rejection() -> RejectionLetter:
    return make_rejection()


@pytest_asyncio.fixture
async def async_test_db():
    """In-memory async SQLite session for testing database & audit trail models."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(ClaimBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()


# ============================================================================
# Golden UAT Corpus Fixtures & Helpers
# ============================================================================

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


def extract_val(obj: Any, attr: Optional[str] = None, default: Any = None) -> Any:
    """
    Universally extracts underlying primitive values from Provenance[T],
    Pydantic models, or raw Python primitives.
    """
    target = getattr(obj, attr, default) if attr is not None else obj
    if target is None:
        return default
    if hasattr(target, 'value'):
        return target.value
    return target


def get_data_dir() -> Path:
    """Returns absolute path to the project root data/ directory."""
    return Path(__file__).resolve().parent.parent.parent.parent / "data"


@pytest.fixture(scope="session")
def golden_manifests() -> Dict[str, List[Dict[str, Any]]]:
    """Loads all synthetic datasets from data/ for Golden UAT scenarios."""
    data_dir = get_data_dir()
    bills_manifest = data_dir / "synthetic_bills" / "manifest.json"
    policies_manifest = data_dir / "synthetic_policies" / "manifest.json"
    rejections_manifest = data_dir / "synthetic_rejections" / "manifest.json"
    
    bills = json.loads(bills_manifest.read_text(encoding="utf-8")) if bills_manifest.exists() else []
    policies = json.loads(policies_manifest.read_text(encoding="utf-8")) if policies_manifest.exists() else []
    rejections = json.loads(rejections_manifest.read_text(encoding="utf-8")) if rejections_manifest.exists() else []
    
    return {
        "bills": bills,
        "policies": policies,
        "rejections": rejections
    }


@pytest.fixture
def golden_claim_builder(golden_manifests):
    """
    Factory fixture to construct end-to-end claim bundles from golden manifests.
    Enables parameterized multi-document testing across synthetic data scenarios.
    """
    def _build(patient_name: str) -> Dict[str, Any]:
        bill_entry = next((b for b in golden_manifests["bills"] if b.get("patient") == patient_name), None)
        policy_entry = next((p for p in golden_manifests["policies"] if p.get("patient") == patient_name), None)
        rej_entry = next((r for r in golden_manifests["rejections"] if r.get("patient") == patient_name), None)
        
        bill_amt = bill_entry.get("total_amount", 50000.0) if bill_entry else 50000.0
        hosp_name = bill_entry.get("hospital", "Apollo Hospitals") if bill_entry else "Apollo Hospitals"
        
        ins_name = policy_entry.get("insurer", "HDFC ERGO General Insurance") if policy_entry else "HDFC ERGO General Insurance"
        sum_ins = float(policy_entry.get("sum_insured", 500000.0)) if policy_entry else 500000.0
        room_limit = float(policy_entry.get("room_rent_limit", 5000.0)) if policy_entry and policy_entry.get("room_rent_limit") is not None else 5000.0
        copay = float(policy_entry.get("copay_percent", 0.0)) if policy_entry else 0.0
        
        claimed = float(rej_entry.get("claimed_amount", bill_amt)) if rej_entry else bill_amt
        approved = float(rej_entry.get("approved_amount", bill_amt)) if rej_entry else bill_amt
        deducted = float(rej_entry.get("deducted_amount", 0.0)) if rej_entry else 0.0
        
        return {
            "patient_name": patient_name,
            "bill_meta": bill_entry,
            "policy_meta": policy_entry,
            "rejection_meta": rej_entry,
            "bill": make_bill(patient_name=patient_name, hospital_name=hosp_name, total_amount=bill_amt),
            "policy": make_policy(policyholder_name=patient_name, insurer_name=ins_name, sum_insured=sum_ins, room_rent_limit_per_day=room_limit, copay_percentage=copay),
            "rejection": make_rejection(policyholder_name=patient_name, total_claimed=claimed, total_approved=approved, total_deducted=deducted)
        }
    return _build
