from typing import Optional, Literal, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field

class PDFRevisionInfo(BaseModel):
    revision_count: int = 0
    eof_offsets: List[int] = Field(default_factory=list)
    has_incremental_updates: bool = False
    suspicious_modifications: List[str] = Field(default_factory=list)
    overwritten_objects: List[int] = Field(default_factory=list)

class PDFInspectionResult(BaseModel):
    is_tampered: bool = False
    pdf_tamper_score: float = 0.0  # 0.0 to 1.0
    revisions: PDFRevisionInfo = Field(default_factory=lambda: PDFRevisionInfo(revision_count=0))
    anomalies: List[str] = Field(default_factory=list)
    risk_level: str = "CLEAN"  # "CLEAN" | "SUSPICIOUS" | "TAMPERED"
    details: Dict[str, Any] = Field(default_factory=dict)

class FactorAttribution(BaseModel):
    category: str  # "forensics" | "billing" | "clinical" | "provider"
    factor_name: str
    impact_score: float  # contribution in range [-1.0, 1.0]
    weight: float  # factor weight in overall composite calculation
    description: str

class AnomalyAssessment(BaseModel):
    anomaly_density_score: float  # 0.0 to 100.0
    review_status: str  # "NEEDS_REVIEW" | "FLAGGED FOR REVIEW" | "CLEAN"
    confidence: float  # 0.0 to 1.0
    factor_attributions: List[FactorAttribution] = Field(default_factory=list)
    top_anomalies: List[str] = Field(default_factory=list)
    summary: str = ""

class ELAResult(BaseModel):
    tamper_score: float
    suspicious_regions: list[dict] = []
    heatmap_path: Optional[str] = None
    heatmap_url: Optional[str] = None
    details: str = ""
    assessment: Literal["CLEAN", "SUSPICIOUS", "HIGHLY_SUSPICIOUS"]

class MetadataFlag(BaseModel):
    flag_type: str = ""
    field_name: str = ""
    expected_value: Optional[str] = None
    actual_value: str = ""
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    description: str

class BillAnomalyFlag(BaseModel):
    anomaly_type: Literal["LOS_PADDING", "TARIFF_DEVIATION", "DUPLICATE_BILLING", "ITEMIZATION_MISMATCH"]
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    affected_items: list[str] = []
    benchmark_value: Optional[float] = None
    actual_value: Optional[float] = None

class ConsistencyFlag(BaseModel):
    issue_type: str = ""
    mismatch_type: Optional[Literal["DIAGNOSIS_MEDICINE", "DIAGNOSIS_TEST", "PROCEDURE_BILLING"]] = None
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    details: str = ""

class ForensicsResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    claim_id: str = ""
    ela_result: Optional[ELAResult] = None
    pdf_inspection_result: Optional[PDFInspectionResult] = None
    anomaly_assessment: Optional[AnomalyAssessment] = None
    metadata_flags: list[MetadataFlag] = []
    bill_anomalies: list[BillAnomalyFlag] = []
    bill_anomaly_flags: list[BillAnomalyFlag] = []
    consistency_flags: list[ConsistencyFlag] = []
    overall_risk: Literal["LOW", "MEDIUM", "HIGH"]
    recommendation: str = "No issues detected"
    disclaimer: str = "These are automated flags for human review only. This system does not make fraud determinations."
