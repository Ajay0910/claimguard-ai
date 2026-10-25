import os
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

from typing import Dict, Any, Optional, Tuple

from .preprocessor import prepare_document
from .ocr_engine import OCREngine
from .vlm_extractor import VLMExtractor
from ..utils.text_matching import strip_honorifics, levenshtein_similarity, match_names

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
            try:
                self.vlm_extractor = VLMExtractor(
                    provider=vlm_provider,
                    api_key=vlm_api_key,
                    model=config.get("vlm_model"),
                )
            except Exception:
                self.vlm_extractor = None
                self.use_vlm = False
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
            line_items = getattr(result, 'line_items', [])
            total_amount = getattr(result, 'total_amount', None)
            total_val = total_amount.value if hasattr(total_amount, 'value') else total_amount
            
            # Arithmetic reconciliation: Sum(line items) == Gross Billed
            if line_items and total_val is not None and float(total_val) > 0:
                line_sum = sum(
                    float(getattr(item.amount, 'value', getattr(item, 'amount', 0.0)) or 0.0)
                    for item in line_items
                )
                if abs(line_sum - float(total_val)) > 1.0:
                    setattr(result, 'arithmetic_verified', False)
                    status = "NEEDS_REVIEW" if status != "INSUFFICIENT_EVIDENCE" else status
                    if "ARITHMETIC_MISMATCH" not in issues:
                        issues.append("ARITHMETIC_MISMATCH")
                else:
                    setattr(result, 'arithmetic_verified', True)
            elif hasattr(result, 'arithmetic_verified') and not result.arithmetic_verified:
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
        doc_type = None
        if expected_type == 'HOSPITAL_BILL':
            doc_type = 'bill'
        elif expected_type == 'INSURANCE_POLICY':
            doc_type = 'policy'
        elif expected_type == 'REJECTION_LETTER':
            doc_type = 'rejection'

        # 1. Prepare document
        try:
            pages = prepare_document(
                file_path,
                max_pages=self.max_pages,
                max_total_pixels=self.max_total_pixels,
            )
            if not pages:
                raise ValueError("No pages extracted from document")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Document preparation failed for %s: %s", file_path, e)
            return {
                "source": "none",
                "type": doc_type or expected_type or "unknown",
                "text": "",
                "ocr_pages": [],
                "confidence": 0.0,
                "data": None,
                "status": "INSUFFICIENT_EVIDENCE",
                "issues": ["DOCUMENT_CORRUPTED_OR_UNREADABLE", str(e)]
            }
            
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
            
        doc_type = None
        if expected_type == 'HOSPITAL_BILL':
            doc_type = 'bill'
        elif expected_type == 'INSURANCE_POLICY':
            doc_type = 'policy'
        elif expected_type == 'REJECTION_LETTER':
            doc_type = 'rejection'

        if needs_vlm and self.use_vlm:
            try:
                # 5. Classify document type using the first page if not already known
                first_page = pages[0]
                image_bytes = self._convert_image_to_bytes(first_page)
                all_image_bytes = [self._convert_image_to_bytes(page) for page in pages]
                mime_type = "image/png"
                
                if not doc_type:
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
                # Fall through to PDF fallback or OCR block below

        # Deterministic PDF text fallback for digital/machine-readable PDFs
        if file_path and file_path.lower().endswith('.pdf'):
            try:
                from .pdf_parser_fallback import parse_hospital_bill_pdf, parse_insurance_policy_pdf, parse_rejection_letter_pdf
                parsed_model = None
                target_type = doc_type
                if not target_type:
                    try:
                        import pymupdf
                        _d = pymupdf.open(file_path)
                        _pdf_txt = "\n".join(_p.get_text() for _p in _d).lower()
                    except Exception:
                        _pdf_txt = combined_text.lower()
                    if "bill" in _pdf_txt or "hospital" in _pdf_txt or "discharge" in _pdf_txt:
                        target_type = 'bill'
                    elif "policy" in _pdf_txt or "sum insured" in _pdf_txt or "waiting period" in _pdf_txt:
                        target_type = 'policy'
                    elif "rejection" in _pdf_txt or "repudiat" in _pdf_txt or "disallow" in _pdf_txt or "settlement" in _pdf_txt:
                        target_type = 'rejection'

                if target_type == 'bill':
                    parsed_model = parse_hospital_bill_pdf(file_path)
                elif target_type == 'policy':
                    parsed_model = parse_insurance_policy_pdf(file_path)
                elif target_type == 'rejection':
                    parsed_model = parse_rejection_letter_pdf(file_path)

                if parsed_model is not None:
                    status, issues = self._validate_extraction(target_type, parsed_model)
                    try:
                        import pymupdf
                        _d = pymupdf.open(file_path)
                        _pdf_pages = [p.get_text() for p in _d]
                    except Exception:
                        _pdf_pages = full_text
                    return {
                        "source": "pdf_text",
                        "type": target_type,
                        "data": parsed_model,
                        "ocr_fallback_text": "\n\n".join(_pdf_pages) if _pdf_pages else combined_text,
                        "ocr_pages": _pdf_pages if _pdf_pages else full_text,
                        "status": status,
                        "issues": issues
                    }
            except Exception as ex:
                import logging
                logging.getLogger(__name__).warning("PDF text fallback failed: %s", ex)

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

    def normalize_identity(self, name: Optional[str]) -> str:
        """Normalizes a person's name by stripping honorifics and extraneous whitespace."""
        if not name:
            return ""
        return strip_honorifics(str(name)).strip()

    def compare_identities(self, name1: Optional[str], name2: Optional[str]) -> Tuple[float, bool]:
        """
        Computes normalized Levenshtein similarity and matching verdict for two names.
        Returns (similarity_score, is_match) where is_match requires threshold >= 0.80 or token overlap.
        """
        if not name1 or not name2:
            return 1.0, True
        n1 = self.normalize_identity(name1)
        n2 = self.normalize_identity(name2)
        if not n1 or not n2:
            return 1.0, True
        sim = levenshtein_similarity(n1, n2)
        is_match = match_names(n1, n2, threshold=0.75) or (sim >= 0.80)
        return sim, is_match

    def reconcile_identities(self, bill_data: Any, policy_data: Any, rejection_data: Any) -> Dict[str, Any]:
        """
        Performs Levenshtein identity normalization and cross-document verification
        across hospital bill, insurance policy, and insurer rejection letter.
        """
        def _extract_name(obj, *attrs):
            for attr in attrs:
                val = getattr(obj, attr, None)
                if val is not None:
                    return val.value if hasattr(val, 'value') else str(val)
            return None

        bill_patient = _extract_name(bill_data, 'patient_name')
        pol_holder = _extract_name(policy_data, 'policyholder_name', 'policy_holder_name')
        rej_patient = _extract_name(rejection_data, 'patient_name', 'insured_name')
        rej_holder = _extract_name(rejection_data, 'policyholder_name')
        if not rej_patient and rej_holder:
            rej_patient = rej_holder
        if not rej_holder and rej_patient:
            rej_holder = rej_patient

        norm_bill_patient = self.normalize_identity(bill_patient)
        norm_pol_holder = self.normalize_identity(pol_holder)
        norm_rej_patient = self.normalize_identity(rej_patient)
        norm_rej_holder = self.normalize_identity(rej_holder)

        similarities: Dict[str, float] = {}
        conflicts: list[str] = []

        # 1. Patient matching: Bill Patient vs Rejection Patient
        if norm_bill_patient and norm_rej_patient:
            sim_br, match_br = self.compare_identities(norm_bill_patient, norm_rej_patient)
            similarities["bill_patient_vs_rejection"] = sim_br
            if not match_br:
                conflicts.append(
                    f"Patient identity discrepancy: Bill ('{norm_bill_patient}') vs Rejection ('{norm_rej_patient}') "
                    f"(Levenshtein similarity: {sim_br:.2f} < 0.80)"
                )

        # 2. Policyholder matching: Policy Policyholder vs Rejection Policyholder
        if norm_pol_holder and norm_rej_holder:
            sim_pr, match_pr = self.compare_identities(norm_pol_holder, norm_rej_holder)
            similarities["policyholder_vs_rejection"] = sim_pr
            if not match_pr:
                conflicts.append(
                    f"Policyholder identity discrepancy: Policy ('{norm_pol_holder}') vs Rejection ('{norm_rej_holder}') "
                    f"(Levenshtein similarity: {sim_pr:.2f} < 0.80)"
                )

        # 3. Informational similarity between Bill Patient and Policyholder
        if norm_bill_patient and norm_pol_holder:
            sim_bp, _ = self.compare_identities(norm_bill_patient, norm_pol_holder)
            similarities["bill_patient_vs_policyholder"] = sim_bp

        is_verified = len(conflicts) == 0
        return {
            "is_verified": is_verified,
            "normalized_names": {
                "bill_patient": norm_bill_patient,
                "policyholder": norm_pol_holder,
                "rejection_patient": norm_rej_patient,
                "rejection_policyholder": norm_rej_holder,
            },
            "similarities": similarities,
            "conflicts": conflicts
        }

    def process_claim_documents(self, bill_path: str, policy_path: str, rejection_path: str) -> Dict[str, Any]:
        """Process a complete claim set with arithmetic and Levenshtein identity reconciliation."""
        results: Dict[str, Any] = {}
        
        if bill_path and os.path.exists(bill_path):
            results['bill'] = self.process_document(bill_path, 'HOSPITAL_BILL')
            
        if policy_path and os.path.exists(policy_path):
            results['policy'] = self.process_document(policy_path, 'INSURANCE_POLICY')
            
        if rejection_path and os.path.exists(rejection_path):
            results['rejection'] = self.process_document(rejection_path, 'REJECTION_LETTER')
            
        results['identity_reconciliation'] = self.reconcile_identities(
            results.get('bill', {}).get('data'),
            results.get('policy', {}).get('data'),
            results.get('rejection', {}).get('data')
        )
        return results
