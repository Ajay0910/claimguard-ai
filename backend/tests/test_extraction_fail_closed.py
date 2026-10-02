from app.extraction import pipeline as extraction_module
from app.extraction.pipeline import ExtractionPipeline


def _stub_document(monkeypatch, pipeline):
    limits = {}

    def fake_prepare_document(path, *, max_pages=None, max_total_pixels=None):
        limits["max_pages"] = max_pages
        limits["max_total_pixels"] = max_total_pixels
        return [object()]

    monkeypatch.setattr(extraction_module, "prepare_document", fake_prepare_document)
    monkeypatch.setattr(pipeline.ocr_engine, "extract_with_confidence", lambda _page: ("recognized text", 1.0))
    monkeypatch.setattr(pipeline.ocr_engine, "extract_table", lambda _page: [])
    monkeypatch.setattr(pipeline, "_convert_image_to_bytes", lambda _page: b"page")
    return limits


def test_missing_vlm_key_does_not_return_empty_typed_bill(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": ""})
    limits = _stub_document(monkeypatch, pipeline)

    result = pipeline.process_document("bill.pdf", expected_type="HOSPITAL_BILL")

    assert limits == {"max_pages": 30, "max_total_pixels": 40_000_000}

    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["source"] != "ocr"
    assert result["data"] is None


def test_vlm_exception_does_not_return_empty_typed_policy(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "configured"})
    limits = _stub_document(monkeypatch, pipeline)

    class BrokenVLM:
        def extract_insurance_policy(self, image_bytes, mime_type):
            raise RuntimeError("provider unavailable")

    pipeline.vlm_extractor = BrokenVLM()
    result = pipeline.process_document("policy.pdf", expected_type="INSURANCE_POLICY")

    assert limits == {"max_pages": 30, "max_total_pixels": 40_000_000}
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["source"] != "ocr"
    assert result["data"] is None


def test_pipeline_uses_configured_gemini_model(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    captured = {}

    class VLMStub:
        def __init__(self, *, provider, api_key, model):
            captured.update(provider=provider, api_key=api_key, model=model)

    monkeypatch.setattr(extraction_module, "VLMExtractor", VLMStub)

    ExtractionPipeline(config={
        "vlm_provider": "gemini",
        "vlm_api_key": "configured",
        "vlm_model": "configured-model",
    })

    assert captured["model"] == "configured-model"


def test_placeholder_api_key_is_treated_as_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    pipeline = ExtractionPipeline(config={
        "vlm_provider": "gemini",
        "vlm_api_key": "replace-with-your-gemini-api-key",
    })

    assert pipeline.use_vlm is False


def test_vlm_receives_every_page_of_a_pdf(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    captured = {}
    pages = [object(), object()]
    limits = {}

    def fake_prepare_document(path, *, max_pages=None, max_total_pixels=None):
        limits["max_pages"] = max_pages
        limits["max_total_pixels"] = max_total_pixels
        return pages
    monkeypatch.setattr(extraction_module, "prepare_document", fake_prepare_document)

    class OCREngineStub:
        def extract_with_confidence(self, _page):
            return "page text", 1.0

        def extract_table(self, _page):
            return []

    class VLMStub:
        def __init__(self, *, provider, api_key, model):
            self.provider = provider
            self.api_key = api_key
            self.model = model

        def extract_hospital_bill(self, image_bytes, _mime_type):
            captured["pages"] = image_bytes
            from app.schemas.hospital_bill import HospitalBill
            return HospitalBill(total_amount=100)

    monkeypatch.setattr(extraction_module, "VLMExtractor", VLMStub)
    pipeline = ExtractionPipeline(config={"vlm_provider": "openai", "vlm_api_key": "configured"})
    pipeline.ocr_engine = OCREngineStub()
    pipeline._convert_image_to_bytes = lambda _page: b"page"

    result = pipeline.process_document("two-page-bill.pdf", expected_type="HOSPITAL_BILL")

    # This fixture omits line items/subtotal, so extraction must still require review.
    assert result["status"] == "NEEDS_REVIEW"
    assert captured["pages"] == [b"page", b"page"]
    assert limits == {"max_pages": 30, "max_total_pixels": 40_000_000}
