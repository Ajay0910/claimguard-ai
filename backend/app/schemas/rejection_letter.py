from pydantic import BaseModel, computed_field
from typing import Optional, Literal
from .provenance import Provenance

class RejectionReason(BaseModel):
    code: Provenance[str]
    description: Provenance[str]
    details: Optional[Provenance[str]] = None
    clause_cited: Optional[Provenance[str]] = None
    category: Provenance[Literal["PROPORTIONATE_DEDUCTION", "WAITING_PERIOD", "PRE_EXISTING", "EXCLUSION", "DOCUMENT_INCOMPLETE", "MENTAL_HEALTH", "OTHER", "Non-Medical", "Sub-limit Exhausted", "Waiting Period"]]

class RejectionLetter(BaseModel):
    rejection_id: Optional[Provenance[str]] = None
    reference_number: Optional[Provenance[str]] = None
    insurer_name: Optional[Provenance[str]] = None
    tpa_name: Optional[Provenance[str]] = None
    policyholder_name: Optional[Provenance[str]] = None
    policy_number: Optional[Provenance[str]] = None
    claim_number: Optional[Provenance[str]] = None
    claim_date: Optional[Provenance[str]] = None
    total_claimed: Optional[Provenance[float]] = None
    total_approved: Optional[Provenance[float]] = None
    approved_amount: Provenance[float] = Provenance(value=0.0)
    total_deducted: Optional[Provenance[float]] = None
    rejection_reasons: list[RejectionReason] = []
    reasons: list[RejectionReason] = []
    settlement_type: Optional[Provenance[Literal["FULL_REJECTION", "PARTIAL_SETTLEMENT", "FULL_SETTLEMENT"]]] = None
    remarks: Optional[Provenance[str]] = None
    extraction_confidence: float = 1.0

    @computed_field
    @property
    def deduction_percentage(self) -> float:
        claimed = self.total_claimed.value if hasattr(self.total_claimed, 'value') else 0.0
        deducted = self.total_deducted.value if hasattr(self.total_deducted, 'value') else 0.0
        if claimed > 0:
            return (deducted / claimed) * 100.0
        return 0.0
