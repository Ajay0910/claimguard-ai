import os
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

from typing import Dict, Any

from .preprocessor import prepare_document
from .ocr_engine import OCREngine
from .vlm_extractor import VLMExtractor

class ExtractionPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.ocr_engine = OCREngine()
        self.max_pages = int(config.get("max_document_pages", 30))
        self.max_total_pixels = int(config.get("max_document_total_pixels", 40_000_000))
        
        vlm_provider = config.get("vlm_provider", "openai")
        vlm_api_key = config.get("vlm_api_key", "")
        normalized_key = str(vlm_api_key or "").strip().lower()
        self.use_vlm = bool(normalized_key) and not any(
            marker in normalized_key for marker in ("replace-with", "your-api-key", "changeme", "placeholder")
        )
        
        if self.use_vlm:
            self.vlm_extractor = VLMExtractor(
                provider=vlm_provider,
                api_key=vlm_api_key,
                model=config.get("vlm_model"),
            )
        else:
            self.vlm_extractor = None

    def _convert_image_to_bytes(self, image: Any) -> bytes:
        if not CV2_AVAILABLE:
            import io
            # Fallback to PIL
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            return buf.getvalue()
            
        success, buffer = cv2.imencode('.png', image)
        if not success:
            raise ValueError("Could not encode image to PNG format")
        return buffer.tobytes()

    def _validate_extraction(self, doc_type: str, result: Any) -> tuple[str, list[str]]:
        if not result:
            return "NEEDS_REVIEW", ["NO_DATA_EXTRACTED"]
            
        status = "SUCCESS"
        issues = []
        
        if hasattr(result, 'extraction_confidence') and result.extraction_confidence < 0.7:
            status = "INSUFFICIENT_EVIDENCE"
            issues.append("LOW_CONFIDENCE")
            
        if doc_type == 'bill':
            if hasattr(result, 'arithmetic_verified') and not result.arithmetic_verified:
                status = "NEEDS_REVIEW" if status != "INSUFFICIENT_EVIDENCE" else status
                issues.append("ARITHMETIC_MISMATCH")
            
            total_amount = getattr(result, 'total_amount', None)
            if total_amount is None or (hasattr(total_amount, 'value') and total_amount.value <= 0):
                status = "INSUFFICIENT_EVIDENCE"
                issues.append("MISSING_OR_ZERO_TOTAL_AMOUNT")
                
        elif doc_type == 'policy':
            sum_insured = getattr(result, 'sum_insured', None)
            if sum_insured is None or (hasattr(sum_insured, 'value') and sum_insured.value <= 0):
                status = "INSUFFICIENT_EVIDENCE"
                issues.append("MISSING_SUM_INSURED")
                
        elif doc_type == 'rejection':
            total_claimed = getattr(result, 'total_claimed', None)
            if total_claimed is None or (hasattr(total_claimed, 'value') and total_claimed.value <= 0):
                status = "INSUFFICIENT_EVIDENCE"
                issues.append("MISSING_TOTAL_CLAIMED")
            
        return status, issues

    def process_document(self, file_path: str, expected_type: str = None) -> Dict[str, Any]:
        """Main entry point to process a document."""
        # 1. Prepare document
        pages = prepare_document(
            file_path,
            max_pages=self.max_pages,
            max_total_pixels=self.max_total_pixels,
        )
        if not pages:
            raise ValueError("No pages extracted from document")
            
        full_text = []
        min_conf = 1.0
        has_complex_tables = False
        
        for page in pages:
            text, conf = self.ocr_engine.extract_with_confidence(page)
            full_text.append(text)
            min_conf = min(min_conf, conf)
            
            table = self.ocr_engine.extract_table(page)
            if len(table) > 1:
                has_complex_tables = True

        combined_text = "\n\n".join(full_text)
        
        # Determine strategy
        needs_vlm = True
        
        # 3. If OCR confidence < 70%, fall back to VLM
        if min_conf < 0.7:
            needs_vlm = True
            
        # 4. If VLM available and document is complex (has tables), use VLM
        if has_complex_tables:
            needs_vlm = True
            
        if needs_vlm and self.use_vlm:
            try:
                # 5. Classify document type using the first page
                first_page = pages[0]
                image_bytes = self._convert_image_to_bytes(first_page)
                all_image_bytes = [self._convert_image_to_bytes(page) for page in pages]
                mime_type = "image/png"
                
                if expected_type == 'HOSPITAL_BILL':
                    doc_type = 'bill'
                elif expected_type == 'INSURANCE_POLICY':
                    doc_type = 'policy'
                elif expected_type == 'REJECTION_LETTER':
                    doc_type = 'rejection'
                else:
                    doc_type = self.vlm_extractor.classify_document(image_bytes, mime_type)
                
                # 6. Return structured data as Pydantic model
                if doc_type == 'bill':
                    result = self.vlm_extractor.extract_hospital_bill(all_image_bytes, mime_type)
                elif doc_type == 'policy':
                    result = self.vlm_extractor.extract_insurance_policy(all_image_bytes, mime_type)
                elif doc_type == 'rejection':
                    result = self.vlm_extractor.extract_rejection_letter(all_image_bytes, mime_type)
                else:
                    raise ValueError(f"Unknown document classification: {doc_type}")
                    
                status, issues = self._validate_extraction(doc_type, result)
                return {
                    "source": "vlm",
                    "type": doc_type,
                    "data": result,
                    "ocr_fallback_text": combined_text,
                    "ocr_pages": full_text,
                    "status": status,
                    "issues": issues
                }
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("VLM extraction failed (%s)", type(e).__name__)
                # Fall through to OCR block below

        # OCR text is not structured claim data. Preserve it for review, but do
        # not create an empty model that downstream rules could mistake for an
        # extracted bill, policy, or settlement.
        doc_type = expected_type or "unknown"
        issues = ["NO_STRUCTURED_EXTRACTION"]
        issues.append("VLM_EXTRACTION_FAILED" if self.use_vlm else "VLM_API_KEY_MISSING")

        return {
            "source": "none",
            "type": doc_type,
            "text": combined_text,
            "ocr_pages": full_text,
            "confidence": min_conf,
            "data": None,
            "status": "INSUFFICIENT_EVIDENCE",
            "issues": issues
        }

    def process_claim_documents(self, bill_path: str, policy_path: str, rejection_path: str) -> Dict[str, Any]:
        """Process a complete claim set."""
        results = {}
        
        if bill_path and os.path.exists(bill_path):
            results['bill'] = self.process_document(bill_path, 'HOSPITAL_BILL')
            
        if policy_path and os.path.exists(policy_path):
            results['policy'] = self.process_document(policy_path, 'INSURANCE_POLICY')
            
        if rejection_path and os.path.exists(rejection_path):
            results['rejection'] = self.process_document(rejection_path, 'REJECTION_LETTER')
            
        return results
