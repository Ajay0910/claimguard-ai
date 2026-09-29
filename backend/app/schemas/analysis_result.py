from pydantic import BaseModel, model_validator, ConfigDict
from typing import Optional, Literal, Union
from datetime import datetime

from .appeal_evaluation import AppealEvaluationResult
from .evidence_ledger import EvidenceLedgerEntry, EvidenceLedger

class RuleVerdict(BaseModel):
    model_config = ConfigDict(extra='ignore')
    rule_name: str
    rule_description: str = ""
    status: Literal["PASS", "FAIL", "SKIPPED", "NOT_APPLICABLE", "CONFLICT", "NEEDS_REVIEW", "WARNING", "BLOCKED", "INSUFFICIENT_EVIDENCE"]
    confidence: float = 1.0
    finding: str
    finding_type: Optional[str] = None
    source_type: Optional[str] = None
    insurer_approved_amount: Optional[float] = None
    expected_admissible_amount: Optional[float] = None
    monetary_impact: Optional[float] = None
    regulatory_citation: Optional[str] = None
    appeal_recommendation: Optional[str] = None
    evidence_entry_ids: list[str] = []
    evidence_entries: list[EvidenceLedgerEntry] = []
    
    actual_claim_fact: Optional[str] = None
    applicable_policy_rule: Optional[str] = None
    insurer_applied_action: Optional[str] = None
    expected_action: Optional[str] = None
    expected_admissible_amount: Optional[float] = None
    insurer_calculation: Optional[float] = None
    correct_calculation: Optional[float] = None
    difference: Optional[float] = None
    evidence: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def set_source_type(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "source_type" not in data and "finding_type" in data:
                ft = data["finding_type"]
                if ft in ["REGULATORY_CONFLICT", "REGULATION_CONFLICT", "STATUTORY_CONFLICT"]:
                    data["source_type"] = "REGULATION"
                elif ft in ["POLICY_MISMATCH", "NO_ISSUE", "NEEDS_REVIEW", "CLINICAL_REJECTION", "WAITING_PERIOD_ACTIVE"]:
                    data["source_type"] = "POLICY"
                elif ft in ["FINANCIAL_DISCREPANCY", "PROPORTIONATE_DEDUCTION"]:
                    data["source_type"] = "CALCULATION"
                elif ft in ["DOCUMENT_INCONSISTENCY", "IDENTITY_CONFLICT", "EXTRACTION_CONFLICT", "FRAUD_SIGNAL"]:
                    data["source_type"] = "DOCUMENT_CONSISTENCY"
                elif "POLICY" in ft and "REGULATION" in ft:
                    data["source_type"] = "POLICY + REGULATION"
                else:
                    if "POLICY" in ft:
                        data["source_type"] = "POLICY"
                    elif "REGULATION" in ft:
                        data["source_type"] = "REGULATION"
        return data

    @model_validator(mode='after')
    def enforce_evidence_ledger(self) -> 'RuleVerdict':
        # Skip evidence requirements for non-findings
        if self.status in ["BLOCKED", "SKIPPED", "NOT_APPLICABLE"]:
            return self
            
        if not self.evidence_entries:
            self.confidence = min(self.confidence, 0.5)
            return self

        complete = True
        for ev in self.evidence_entries:
            # required fields for Point 13: value, normalized_value, source_document_id, source_document_type, 
            # source_hash, page, section, bounding_box, source_text, extraction_confidence, model, 
            # timestamp, transformations, rule_id, formula, calculation_inputs, calculation_output
            
            is_calc = bool(ev.rule_id or ev.formula or ev.calculation_output is not None)
            
            if is_calc:
                if not ev.formula or ev.calculation_output is None or ev.calculation_inputs is None or not ev.rule_id:
                    complete = False
            else:
                if (ev.source_text is None or ev.source_text == "" or 
                    ev.value is None or ev.bounding_box is None or ev.page_number is None or 
                    not ev.source_document_type or not ev.model or 
                    ev.extraction_confidence is None):
                    complete = False
            
            if not ev.document_id or ev.document_id == "SYSTEM" or not ev.document_hash or ev.document_hash == "SYSTEM_DETERMINISTIC":
                if not is_calc:  # For purely extracted values, document_id and hash must be valid
                    complete = False
                    
            if not ev.timestamp or getattr(ev, "transformations", None) is None:
                complete = False
                
        if not complete:
            self.confidence = min(self.confidence, 0.79)
            if self.status not in ["NEEDS_REVIEW", "CONFLICT", "BLOCKED", "INSUFFICIENT_EVIDENCE", "SKIPPED", "NOT_APPLICABLE"]:
                self.status = "INSUFFICIENT_EVIDENCE"
        elif self.confidence < 0.8:
            if self.status not in ["NEEDS_REVIEW", "CONFLICT", "BLOCKED", "INSUFFICIENT_EVIDENCE", "SKIPPED", "NOT_APPLICABLE"]:
                self.status = "INSUFFICIENT_EVIDENCE"
                
        return self

class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    claim_id: str = ""
    analysis_timestamp: Union[str, datetime] = ""
    documents_analyzed: list[str] = []
    overall_status: Literal["NO_MISMATCH_FOUND", "MISMATCH_DETECTED", "REVIEW_RECOMMENDED", "EXTRACTION_FAILED", "BLOCKED", "INSUFFICIENT_EVIDENCE"]
    rule_verdicts: list[RuleVerdict]
    appeal_evaluation: Optional[AppealEvaluationResult] = None
    total_monetary_impact: Optional[float] = None
    expected_admissible_amount: Optional[float] = None
    insurer_approved_amount: Optional[float] = None
    billed_amount: Optional[float] = None
    total_disallowed: Optional[float] = None
    legitimate_deduction: Optional[float] = None
    approved_pct: Optional[float] = None
    recoverable_pct: Optional[float] = None
    legitimate_pct: Optional[float] = None
    recovery_yield: Optional[str] = None
    tier1_issues: int = 0
    tier2_flags: int = 0
    summary: str
    evidence_ledger: Optional[EvidenceLedger] = None

    @model_validator(mode='after')
    def compute_aggregates(self) -> 'AnalysisResult':
        t1 = 0
        t2 = 0
        for rv in self.rule_verdicts:
            if rv.status == "FAIL":
                t1 += 1
            elif rv.status == "NEEDS_REVIEW":
                t2 += 1
                
        self.tier1_issues = t1
        self.tier2_flags = t2
        return self
