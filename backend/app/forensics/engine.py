import os
from typing import Optional, List, Any
from .ela_detector import ELADetector
from .metadata_checker import MetadataChecker
from .bill_anomaly import BillAnomalyDetector
from .consistency_checker import ConsistencyChecker
from .pdf_inspector import PDFInspector, PDFInspectionResult
from .fraud_scorer import AnomalyScorer, AnomalyAssessment
from ..schemas.hospital_bill import HospitalBill
from ..schemas.forensics_result import ForensicsResult, ELAResult

class ForensicsEngine:
    def __init__(self):
        self.ela_detector = ELADetector()
        self.metadata_checker = MetadataChecker()
        self.bill_anomaly_detector = BillAnomalyDetector()
        self.consistency_checker = ConsistencyChecker()
        self.pdf_inspector = PDFInspector()
        self.fraud_scorer = AnomalyScorer()
    
    def run_all_checks(self, file_path: str, bill: Optional[HospitalBill] = None) -> ForensicsResult:
        """
        Run all forensic checks on a document.
        """
        ela_result = ELAResult(
            tamper_score=0.0, 
            assessment="CLEAN", 
            heatmap_url=None, 
            suspicious_regions=[],
            details="Not analyzed"
        )
        pdf_inspection_result: Optional[PDFInspectionResult] = None

        ext = os.path.splitext(file_path)[1].lower() if file_path else ""
        if ext in ['.jpg', '.jpeg', '.png']:
            ela_result = self.ela_detector.analyze(file_path)
        elif ext == '.pdf':
            pdf_inspection_result = self.pdf_inspector.inspect_file(file_path)
            
        metadata_flags = self.metadata_checker.analyze(file_path) if file_path and os.path.exists(file_path) else []
        
        bill_flags = []
        consistency_flags = []
        if bill:
            bill_flags = self.bill_anomaly_detector.analyze(bill)
            consistency_flags = self.consistency_checker.analyze(bill)
            
        high_risk_count = sum(1 for f in metadata_flags if f.severity == "HIGH") + \
                          sum(1 for f in bill_flags if f.severity == "HIGH") + \
                          sum(1 for f in consistency_flags if f.severity == "HIGH")
                          
        med_risk_count_init = 0
        if ela_result.assessment == "HIGHLY_SUSPICIOUS":
            high_risk_count += 2
        elif ela_result.assessment == "SUSPICIOUS":
            med_risk_count_init = 1

        if pdf_inspection_result:
            if pdf_inspection_result.risk_level == "TAMPERED":
                high_risk_count += 2
            elif pdf_inspection_result.risk_level == "SUSPICIOUS":
                med_risk_count_init += 1
            
        med_risk_count = med_risk_count_init + \
                         sum(1 for f in metadata_flags if f.severity == "MEDIUM") + \
                         sum(1 for f in bill_flags if f.severity == "MEDIUM") + \
                         sum(1 for f in consistency_flags if f.severity == "MEDIUM")
            
        overall_risk = "LOW"
        if high_risk_count > 0:
            overall_risk = "HIGH"
        elif med_risk_count > 1 or (med_risk_count == 1 and high_risk_count == 0):
            overall_risk = "MEDIUM"
            
        # Compute calibrated explainable composite fraud score
        anomaly_assessment = self.fraud_scorer.compute_score(
            forensics_result={
                "ela_result": ela_result.model_dump() if hasattr(ela_result, "model_dump") else (ela_result.dict() if hasattr(ela_result, "dict") else ela_result),
                "pdf_inspection_result": pdf_inspection_result.model_dump() if (pdf_inspection_result and hasattr(pdf_inspection_result, "model_dump")) else (pdf_inspection_result.dict() if (pdf_inspection_result and hasattr(pdf_inspection_result, "dict")) else pdf_inspection_result),
            },
            bill_anomalies=bill_flags,
            clinical_consistency=consistency_flags,
            metadata_flags=metadata_flags,
        )

        if anomaly_assessment.review_status in ["CRITICAL", "HIGH"]:
            overall_risk = "HIGH"
        elif anomaly_assessment.review_status == "MEDIUM" and overall_risk == "LOW":
            overall_risk = "MEDIUM"

        if overall_risk == "HIGH":
            recommendation = "Reject or escalate for manual review immediately. Strong forensic indicators of manipulation or fraud."
        elif overall_risk == "MEDIUM":
            recommendation = "Review carefully. Some anomalies detected."
        else:
            recommendation = "Appears standard. No major forensic anomalies detected."
            
        from ..rules import get_val
        claim_id_val = get_val(bill, 'bill_id', 'unknown_claim') if bill else 'unknown_claim'
        
        return ForensicsResult(
            claim_id=claim_id_val,
            overall_risk=overall_risk,
            recommendation=recommendation,
            ela_result=ela_result,
            pdf_inspection_result=pdf_inspection_result,
            anomaly_assessment=anomaly_assessment,
            metadata_flags=metadata_flags,
            bill_anomalies=bill_flags,
            bill_anomaly_flags=bill_flags,
            consistency_flags=consistency_flags,
            disclaimer="This is an automated analysis. Final decisions should always involve human review."
        )

    def run(self, documents: List[Any], bill: Optional[HospitalBill] = None) -> ForensicsResult:
        """
        Backwards-compatible batch entry point for list of documents.
        """
        if not documents:
            return self.run_all_checks("", bill=bill)

        # Look for primary document to check (e.g. HOSPITAL_BILL or first available file)
        target_path = ""
        for doc in documents:
            doc_path = getattr(doc, "file_path", None) or (doc.get("file_path") if isinstance(doc, dict) else "")
            doc_type = getattr(doc, "document_type", None) or (doc.get("document_type") if isinstance(doc, dict) else "")
            if doc_path and os.path.exists(doc_path):
                if doc_type == "HOSPITAL_BILL" or not target_path:
                    target_path = doc_path

        if not target_path and documents:
            first_doc = documents[0]
            target_path = getattr(first_doc, "file_path", None) or (first_doc.get("file_path") if isinstance(first_doc, dict) else "")

        return self.run_all_checks(target_path or "", bill=bill)
