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
    reference_number: Provenance[str]
    insurer_name: Provenance[str]
    tpa_name: Optional[Provenance[str]] = None
    policyholder_name: Provenance[str]
    policy_number: Provenance[str]
    claim_number: Provenance[str]
    claim_date: Provenance[str]
    total_claimed: Provenance[float]
    total_approved: Provenance[float]
    approved_amount: Provenance[float] = Provenance(value=0.0)
    total_deducted: Provenance[float]
    rejection_reasons: list[RejectionReason] = []
    reasons: list[RejectionReason] = []
    settlement_type: Provenance[Literal["FULL_REJECTION", "PARTIAL_SETTLEMENT", "FULL_SETTLEMENT"]]
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
