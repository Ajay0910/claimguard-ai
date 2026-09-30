import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app.extraction.pipeline import ExtractionPipeline
from app.schemas.hospital_bill import HospitalBill

def test_new_document_missing_optional_fields():
    # If a document misses an optional field, the schema should gracefully accept it
    # without raising ValidationError.
    raw_data = {
        "bill_id": {"value": "123", "extraction_confidence": 0.9, "source_document_id": "test"},
        "total_amount": {"value": 5000.0, "extraction_confidence": 0.9, "source_document_id": "test"},
        # hospital_name is completely missing in this dict
        "line_items": []
    }
    
    # Should not raise exception
    bill = HospitalBill.model_validate(raw_data)
    assert bill.hospital_name is None
    assert bill.bill_id.value == "123"

def test_pipeline_no_dummy_data_leakage():
    # Test that the pipeline does not inject "Mr. Ramesh Kulkarni" when fallback is used
    pipeline = ExtractionPipeline(config={"use_vlm": True})
    
    # Mock VLM extractor to raise ValueError
    with patch.object(pipeline, 'vlm_extractor') as mock_vlm, \
         patch('app.extraction.pipeline.prepare_document', return_value=[MagicMock()]) as mock_prep:
        mock_vlm.extract_hospital_bill.side_effect = ValueError("Simulated VLM failure")
        mock_vlm.classify_document.return_value = "bill"
        
        # Test process_document
        res = pipeline.process_document("dummy.pdf", expected_type="HOSPITAL_BILL")
        
        # Should return an empty HospitalBill, not Ramesh Kulkarni
        assert res["status"] == "INSUFFICIENT_EVIDENCE"
        data = res["data"]
        assert data.patient_name is None
        assert data.hospital_name is None
