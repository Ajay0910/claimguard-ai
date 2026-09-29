from pydantic import BaseModel, Field
from typing import List

class AppealEvaluationResult(BaseModel):
    appeal_viability: str  # "STRONG" | "MODERATE" | "LOW"
    statutory_conflicts_detected: List[str] = Field(default_factory=list)
    key_legal_precedents: List[str] = Field(default_factory=list)
    recommended_appeal_grounds: List[str] = Field(default_factory=list)
    suggested_action_plan: List[str] = Field(default_factory=list)
