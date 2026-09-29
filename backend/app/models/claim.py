import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import ForeignKey, func, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

class Claim(Base):
    __tablename__ = "claims"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_name: Mapped[str] = mapped_column(String)
    patient_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    patient_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portal_token: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=lambda: str(uuid.uuid4()))
    policy_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    claim_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)  # Enum: PENDING, EXTRACTING, ANALYZING, COMPLETED, FAILED
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    documents: Mapped[List["Document"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    analysis_runs: Mapped[List["AnalysisRun"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(back_populates="claim", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"))
    document_type: Mapped[str] = mapped_column(String)  # Enum: HOSPITAL_BILL, INSURANCE_POLICY, REJECTION_LETTER
    filename: Mapped[str] = mapped_column(String)
    original_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    file_size_bytes: Mapped[int] = mapped_column()
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    extracted_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    extraction_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    claim: Mapped["Claim"] = relationship(back_populates="documents")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"))
    status: Mapped[str] = mapped_column(String)  # RUNNING, COMPLETED, FAILED
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    forensics_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    overall_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_monetary_impact: Mapped[float] = mapped_column(default=0.0)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    claim: Mapped["Claim"] = relationship(back_populates="analysis_runs")
    rule_verdicts: Mapped[List["RuleVerdictRecord"]] = relationship(back_populates="analysis_run", cascade="all, delete-orphan")
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(back_populates="analysis_run", cascade="all, delete-orphan")

class RuleVerdictRecord(Base):
    __tablename__ = "rule_verdicts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"))
    rule_name: Mapped[str] = mapped_column(String)
    rule_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)  # PASS, FAIL, SKIPPED, NEEDS_REVIEW
    confidence: Mapped[float] = mapped_column()
    finding: Mapped[str] = mapped_column(Text)
    insurer_calculation: Mapped[Optional[float]] = mapped_column(nullable=True)
    correct_calculation: Mapped[Optional[float]] = mapped_column(nullable=True)
    monetary_impact: Mapped[Optional[float]] = mapped_column(nullable=True)
    regulatory_citation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    appeal_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    
    actual_claim_fact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applicable_policy_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    insurer_applied_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difference: Mapped[Optional[float]] = mapped_column(nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    analysis_run: Mapped["AnalysisRun"] = relationship(back_populates="rule_verdicts")
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(back_populates="rule_verdict", cascade="all, delete-orphan")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    claim_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String, default="system")
    details: Mapped[Dict[str, Any]] = mapped_column(JSON)
    previous_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    entry_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EvidenceLedgerRecord(Base):
    __tablename__ = "evidence_ledger_records"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), index=True)
    analysis_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    rule_verdict_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rule_verdicts.id"), nullable=True, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    document_hash: Mapped[str] = mapped_column(String(64), index=True)
    page_number: Mapped[int] = mapped_column(default=1)
    bounding_box: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_text: Mapped[str] = mapped_column(Text)
    extracted_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    normalized_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    formula: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    calculation_inputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    final_output: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    claim: Mapped["Claim"] = relationship(back_populates="evidence_ledger_entries")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship(back_populates="evidence_ledger_entries")
    rule_verdict: Mapped[Optional["RuleVerdictRecord"]] = relationship(back_populates="evidence_ledger_entries")
