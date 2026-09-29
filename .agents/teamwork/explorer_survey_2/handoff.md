# Survey Report: Extraction Layer, VLM Cross-Verification, and Ubiquitous Evidence Ledger

**Specialist**: Explorer Survey 2 (Extraction Layer, VLM Cross-Verification, and Evidence Ledger Specialist)  
**Date**: 2026-09-27  
**Scope**: Read-only codebase investigation covering extraction pipeline, OCR, VLM extractors, prompt structures, cross-verification, confidence calculation, mathematical validation/rejection gates, and evidence ledger provenance in ClaimGuard AI against requirements R3 and R5.

---

## 1. Observation

### 1.1 Document Extraction Pipeline & Ingestion Architecture
- **Multi-Document Ingestion**:
  - `backend/app/api/upload.py` lines 17–91: Single-file upload endpoint `/api/upload` accepts `file`, `document_type`, `claim_id`, saving via `save_upload()`.
  - `backend/app/api/portal.py` lines 85–181: Multi-document endpoint `/api/portal/submit` accepts `hospital_bill`, `insurance_policy`, and `rejection_letter` simultaneously, writes them to disk under `settings.UPLOAD_DIR/<claim_id>/`, saves `Document` records in the database, and schedules `_trigger_analysis()`.
  - `backend/app/utils/file_handler.py` lines 21–39: `save_upload()` validates magic bytes (`%PDF`, `\xff\xd8`, `\x89PNG`, `II*` / `MM*`), chunks file content to disk, and returns `(file_path, mime_type, size_bytes)`. **Zero cryptographic hash (e.g. SHA-256) is computed, verified, or stored during upload.**
  - `backend/app/models/claim.py` lines 28–45: The `Document` database model defines `file_path`, `content_type`, `file_size_bytes`, `extracted_data` (JSON), `extraction_confidence`, and `extraction_method`. It **lacks** a `document_hash` / `sha256_hash` column.

- **PDF Parsing and Preprocessing (`backend/app/extraction/preprocessor.py`)**:
  - Lines 70–84 (`pdf_to_images`): Uses PyMuPDF (`fitz.open(pdf_path)`) to rasterize PDF pages to temporary PNG images at 150 DPI (`pix = page.get_pixmap(dpi=150)`).
  - Lines 86–100 (`prepare_document`): Calls `preprocess_image(path)` on each rasterized page, immediately deletes the temporary PNGs (`os.remove(path)`), and returns the preprocessed image objects.
  - Lines 14–68 (`preprocess_image`): Converts image to grayscale, applies deskew via `cv2.minAreaRect`, applies CLAHE (`clipLimit=2.0`), bilateral filtering (`cv2.bilateralFilter`), adaptive Gaussian thresholding (`cv2.adaptiveThreshold`), and morphological closing (`cv2.morphologyEx`).
  - **Critical Flaw**:
    1. It **completely ignores the native digital PDF text layer**. PDFs with embedded selectable text, character font metrics, and exact coordinate bounding boxes (`fitz.Page.get_text("words")` or `fitz.Page.get_text("blocks")`) are forcibly rasterized to 150 DPI bitmaps.
    2. It subjects image data to aggressive binary thresholding and morphological closing before sending to the Vision-Language Model. VLMs lose fine visual details, font weight differentiation, and grayscale boundaries.

- **Pipeline Coordination & Single-Page Truncation Bug (`backend/app/extraction/pipeline.py`)**:
  - Lines 54–62: In `process_document()`, the pipeline loops over `pages` to run OCR:
    ```python
    for page in pages:
        text, conf = self.ocr_engine.extract_with_confidence(page)
        full_text.append(text)
        min_conf = min(min_conf, conf)
        table = self.ocr_engine.extract_table(page)
        if len(table) > 1:
            has_complex_tables = True
    ```
  - Lines 68–74: If `min_conf < 0.7` or `has_complex_tables`, `needs_vlm = True`.
  - Lines 78–82: When invoking the VLM:
    ```python
    first_page = pages[0]
    image_bytes = self._convert_image_to_bytes(first_page)
    mime_type = "image/png"
    ...
    if doc_type == 'bill':
        result = self.vlm_extractor.extract_hospital_bill(image_bytes, mime_type)
    ```
    **Critical Flaw**: For any multi-page document (almost all Indian hospital IPD summary bills and insurance policy schedules run 2 to 10+ pages), `pipeline.py` **only passes the first page (`pages[0]`) to the VLM**! All subsequent pages (OT charges, pharmacy line items, consumables, deductions, taxes, and final payable summaries) are completely omitted.

- **Synthetic Dummy Fallback Data Injection (`backend/app/extraction/pipeline.py`)**:
  - Lines 112–133: If VLM is disabled or throws an exception, the OCR fallback block executes:
    ```python
    if expected_type == 'HOSPITAL_BILL':
        dummy_data = HospitalBill(bill_id="OCR_FALLBACK", total_amount=0.0, hospital_name="Unknown", patient_name="Unknown", line_items=[], subtotal=0.0, net_payable=0.0)
    elif expected_type == 'INSURANCE_POLICY':
        dummy_data = InsurancePolicy(policy_number="OCR_FALLBACK", insurer_name="Unknown", policyholder_name="Unknown", policy_holder_name="Unknown", policy_start_date="2023-01-01", policy_end_date="2024-01-01", sum_insured=0.0)
    elif expected_type == 'REJECTION_LETTER':
        dummy_data = RejectionLetter(rejection_id="OCR_FALLBACK", reference_number="Unknown", insurer_name="Unknown", policyholder_name="Unknown", policy_number="Unknown", claim_number="Unknown", claim_date="2023-01-01", total_claimed=0.0, total_approved=0.0, total_deducted=0.0, rejection_reasons=[], settlement_type="FULL_REJECTION")
    ```
    **Critical Flaw**: The pipeline fabricates fake 0.0 values, dummy dates ("2023-01-01"), and strings ("Unknown") instead of returning `extraction_status="FAILED"`. These dummy objects flow directly into downstream rule evaluation in `backend/app/api/analysis.py` lines 32–55.

- **Prompt Structures (`backend/app/extraction/prompts.py`)**:
  - Lines 1–7: `PROVENANCE_INSTRUCTION` instructs:
    ```
    Every extracted field must be returned as a nested object. It should map the required keys according to the schema (e.g. value, context, source_document_id).
    - "value": The actual extracted value (e.g., 5000, "John Doe", true).
    - "context": The exact page number and text snippet proving the value (e.g., "Page 1 - Room Rent: Rs 5000").
    ```
  - Lines 18–52: Prompts define general role descriptions (`BILL_EXTRACTION_PROMPT`, `POLICY_EXTRACTION_PROMPT`, `REJECTION_EXTRACTION_PROMPT`).
  - **Critical Flaw**:
    1. The prompts do not request bounding box coordinates (`[ymin, xmin, ymax, xmax]`), document hashes, or section identifiers.
    2. In `vlm_extractor.py`, Anthropic structured tool output (`schema_class.model_json_schema()`) and OpenAI `beta.chat.completions.parse(response_format=schema_class)` pass the Pydantic schema directly. Because Pydantic schemas in `schemas/provenance.py` have `wrap_primitive` validators, the models often output flat primitives that get silently wrapped with default synthetic values.

- **Zero Test Coverage**:
  - Ripgrep search across `backend/tests/` for `ExtractionPipeline`, `VLMExtractor`, and `OCREngine` yielded **0 matches**. The entire extraction package is completely untested by unit or integration tests.

---

### 1.2 VLM Cross-Verification & Confidence Scoring
- **Single Model Architecture (`backend/app/extraction/vlm_extractor.py`)**:
  - Lines 11–28: `VLMExtractor` initializes a single client based on `config.vlm_provider` (`openai`, `anthropic`, or `gemini`).
  - Line 15: Sets Gemini model to `"gemini-3.5-flash-lite"` (a non-existent model name; standard is `gemini-1.5-flash` or `gemini-2.0-flash`).
  - Lines 35–146: Each extraction method (`extract_hospital_bill`, `extract_insurance_policy`, `extract_rejection_letter`) calls only that single provider.
  - **Critical Flaw**: There is **zero cross-model verification**. No ensemble execution, no secondary VLM pass, no cross-checking between independent model families (e.g. Anthropic Claude vs OpenAI GPT-4o vs Google Gemini).

- **Zero Multi-Modal (VLM vs OCR) Cross-Verification**:
  - In `pipeline.py` line 106, when VLM succeeds, the OCR text is stored as `"ocr_fallback_text": combined_text` and discarded.
  - In `backend/app/api/analysis.py` lines 32–47, `extracted.get("data")` is used directly. No cross-verification occurs between OCR-extracted figures (room rent, total amount, deductions) and VLM-extracted figures.

- **Uncalculated Confidence Scores**:
  - `vlm_extractor.py` does not request or extract field-level logprobs, per-field confidence, or uncertainty estimates.
  - `backend/app/schemas/provenance.py` line 23: `extraction_confidence: float = 1.0` defaults to 1.0.
  - `backend/app/schemas/hospital_bill.py` line 39: `extraction_confidence: float = 1.0`.
  - `backend/app/schemas/insurance_policy.py`: Lacks document-level confidence entirely.
  - `backend/app/schemas/rejection_letter.py` line 29: `extraction_confidence: float = 1.0`.
  - `backend/app/rules/analysis_result.py` line 12: `RuleVerdict.confidence: float = 1.0`.
  - **Critical Flaw**: Confidence is universally hardcoded to `1.0` regardless of image resolution, OCR blur, extraction ambiguity, or missing fields.

---

### 1.3 Validation and Rejection Mechanisms
- **Hospital Bill Arithmetic Validation (`backend/app/schemas/hospital_bill.py`)**:
  - Lines 41–45:
    ```python
    @model_validator(mode='after')
    def verify_arithmetic(self) -> 'HospitalBill':
        total = sum(item.amount.value for item in self.line_items)
        self.arithmetic_verified = abs(total - self.subtotal.value) <= 1.0
        return self
    ```
  - **Critical Flaw**:
    1. If `arithmetic_verified` evaluates to `False`, the model **does not raise a `ValueError` or reject the extraction**. It silently records `False` and returns the invalid bill object.
    2. If `line_items` is empty and `subtotal.value = 0.0` (as produced by `dummy_data`), `total = 0.0`, so `self.arithmetic_verified` becomes `True`!
    3. It does not check line-item arithmetic: `quantity * unit_rate == amount`.
    4. It does not check net payable consistency: `subtotal + tax_amount - discount == net_payable`.
    5. It does not check whether `room_charges_per_day * length_of_stay == room_total`.

- **Rejection Letter Validation (`backend/app/schemas/rejection_letter.py`)**:
  - Lines 12–39: No validator exists to verify that:
    $$\text{total\_claimed} = \text{total\_approved} + \text{total\_deducted}$$
  - Lines 22–24: Conflicting fields `total_approved` and `approved_amount` coexist without reconciliation.

- **Document Integrity Gate Placement (`backend/app/rules/document_integrity.py`)**:
  - Lines 8–13:
    ```python
    @register_rule(
        name="Document Arithmetic Integrity",
        description="Validates if the sum of itemized hospital bill line items matches the stated gross bill total.",
        tier=1,
        regulatory_citation=None
    )
    ```
  - Lines 28–39: If `difference > 10.0`, it returns `status="WARNING"`.
  - **Critical Flaw**: In `PROJECT.md` (lines 12–16), `Document Integrity & Forensics Gate` is specified as a **Tier 0 Safety Gate** whose failure must set `status="BLOCKED"` and abort downstream financial calculations. Instead, it is registered as `tier=1` and returns `WARNING`, allowing downstream financial rules to execute on corrupt arithmetic.
  - Lines 19–26: If `not line_items`, it returns `status="SKIPPED"`, silently ignoring bills without itemization.

- **Forensics Disconnection from Adjudication (`backend/app/api/analysis.py`)**:
  - Lines 50–61: `RuleEngine.run_all_rules()` executes and completes before `ForensicsEngine.run()` is even instantiated.
  - Forensic flags (tampering, metadata anomalies, itemization mismatch) are stashed in `analysis_run.result_data["forensics"]` and have **zero impact** on rule verdicts or safety gate blocking.

---

### 1.4 Ubiquitous Evidence Ledger & Provenance Schema
- **Provenance Wrapper Schema (`backend/app/schemas/provenance.py`)**:
  - Lines 12–28:
    ```python
    class Provenance(BaseModel, Generic[T]):
        value: T
        normalized_value: Optional[T] = None
        source_document_id: str = Field(default="System/Mock")
        source_document_type: str = Field(default="System/Mock")
        source_hash: Optional[str] = None
        page: Optional[str] = None
        section: Optional[str] = None
        bounding_box: Optional[Dict[str, float]] = None
        source_text: Optional[str] = None
        context: str = Field(default="Generated")
        extraction_confidence: float = 1.0
        extraction_model: str = "System"
        model_version: str = "1.0"
        timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        transformations: list[Transformation] = []
    ```
  - Lines 29–40 (`wrap_primitive`):
    ```python
    @model_validator(mode='before')
    @classmethod
    def wrap_primitive(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        return {
            "value": data,
            "source_document_id": "System/Mock",
            "source_document_type": "System/Mock",
            "context": "Generated"
        }
    ```

- **Pydantic Schema & Test Breakage from Direct Wrapping**:
  - In `HospitalBill`, `InsurancePolicy`, and `RejectionLetter`, every primitive attribute was converted to `Provenance[T]`.
  - When running pytest on the test suite (`.\venv\Scripts\pytest.exe backend\tests\`), 32 tests fail. Key failures directly caused by `Provenance[T]`:
    - `backend/tests/e2e/test_tier1_features.py::test_tier1_f11_evidence_line_item_provenance_retention`:
      ```python
      assert item.item_code == "MED-TR-10"
      ```
      Fails because `Provenance[str](value="MED-TR-10", ...) != "MED-TR-10"`.
    - `backend/tests/e2e/test_tier4_real_world.py:286`:
      ```python
      assert bill.total_amount == 415000.0
      ```
      Fails because `Provenance[float](value=415000.0, ...) != 415000.0`.
  - `Provenance[T]` does not implement `__eq__`, `__hash__`, `__repr__`, or numeric dunder methods (`__float__`, `__int__`, `__add__`, etc.).

- **Calculation Provenance Severing in FinancialMath (`backend/app/engine/calculator.py`)**:
  - Lines 12–34:
    ```python
    @staticmethod
    def _merge_provenance(op: str, a: Any, b: Any, result: float) -> Provenance[float]:
        sources = []
        if isinstance(a, Provenance):
            sources.append(a.source_document_id)
        if isinstance(b, Provenance):
            sources.append(b.source_document_id)
            
        trans = Transformation(
            operation=op,
            timestamp=datetime.utcnow().isoformat(),
            details=f"Calculated {result} from operands"
        )
        return Provenance(
            value=result,
            source_document_id="Engine",
            source_document_type="Calculated",
            context=f"Result of {op}",
            extraction_model="Deterministic Engine",
            transformations=[trans]
        )
    ```
  - **Critical Flaw**:
    1. The local variable `sources` is populated at lines 16–18, but **never assigned or referenced in the returned `Provenance` object**.
    2. Input operand values, variable names, and formulas are discarded.
    3. The return value hardcodes `source_document_id="Engine"`, severing the provenance link back to the originating bill or policy document.
    4. Computations use 64-bit IEEE-754 floats (`float(obj)`), introducing floating-point precision drift instead of fixed-point `decimal.Decimal`.

- **Missing Evidence Ledger Entities**:
  - In `backend/app/schemas/analysis_result.py`: Neither `RuleVerdict` nor `AnalysisResult` includes an `EvidenceLedger` or a list of `EvidenceProvenance` items.
  - In `backend/app/models/claim.py`: There is no `EvidenceLedger` database table. `RuleVerdictRecord` stores only strings and floats.
  - Requirement R5 states: *"Every finding must carry complete provenance: document ID, page, section, source text, extracted value, normalized value, rule ID, formula, calculation inputs, final output, and confidence."* This data structure does not exist anywhere in the codebase.

---

### 1.5 Hardcoded Heuristics, Hallucination Risks, and Contract Mismatches
- **Arbitrary Appeal Overturn Probability (`backend/app/rules/appeal_evaluator.py`)**:
  - Lines 184–214:
    ```python
    base_overturn = 25.0
    if has_ped_denial and elapsed_months >= moratorium_months:
        base_overturn += 62.0
    if has_mental_health_denial or (diagnosis_mh and has_ped_denial):
        base_overturn += 58.0
    if has_proportionate_deduction:
        base_overturn += 45.0
    if is_emergency and has_waiting_period_denial:
        base_overturn += 52.0
    if has_vague_denial:
        base_overturn += 30.0
    if tat_days > 30:
        base_overturn += 15.0
    if is_cosmetic:
        base_overturn -= 40.0
    overturn_prob = max(5.0, min(96.0, round(base_overturn, 1)))
    ```
  - **Violation**: Requirement R1 and R3 explicitly mandate that *"Generic heuristics (e.g., 70% appeal probability) must never override deterministic verification"* and *"No heuristic or ML probability score overrides a deterministic financial calculation."*

- **Fail-Open Name and ID Matching (`backend/app/utils/text_matching.py`)**:
  - Lines 9–13 (`match_ids`):
    ```python
    if not id1 or not id2:
        return True # Cannot evaluate, assume pass
    ```
  - Lines 26–37 (`match_names`):
    ```python
    if not name1 or not name2:
        return True # Cannot evaluate
    ```
  - **Violation**: If extraction fails to extract a patient name or policy number from one document, `text_matching` returns `True`, allowing mismatched documents to pass the identity check without verification.

- **Frontend & API Enum Contradictions**:
  - `backend/app/schemas/analysis_result.py` line 25:
    `overall_status: Literal["NO_MISMATCH_FOUND", "MISMATCH_DETECTED", "REVIEW_RECOMMENDED", "EXTRACTION_FAILED", "BLOCKED"]`
  - `backend/app/api/portal.py` lines 259–277:
    `_generate_plain_summary()` tests for `"CLAIM_SUPPORTED"`, `"PARTIAL_DISPUTE"`, `"CLAIM_DISPUTED"`. Because none of these match `AnalysisResult.overall_status`, the function permanently falls into the generic default fallback branch.

---

## 2. Logic Chain

1. **Premise 1 (Single Page Truncation)**: Because `ExtractionPipeline.process_document()` in `pipeline.py` line 79 selects only `first_page = pages[0]` for VLM extraction, all multi-page hospital bills (which contain 80%+ of line items on subsequent pages) have their items dropped.
2. **Premise 2 (Destructive Image Preprocessing)**: Because `preprocessor.py` applies adaptive binarization and morphological closing (`cv2.morphologyEx`) before VLM conversion, fine font lines, fractional digits, decimal points, and column borders are degraded, causing severe VLM OCR hallucinations.
3. **Premise 3 (Synthetic Dummy Data Infiltration)**: Because `pipeline.py` lines 120–126 instantiates dummy models with `0.0` totals and `"OCR_FALLBACK"` strings instead of raising a structured extraction failure, unverified fallback objects bypass safety filters and enter the deterministic adjudication engine.
4. **Premise 4 (Lack of Cross-Verification & Confidence)**: Because `VLMExtractor` operates only a single model with no multi-model consensus, and discards OCR output without comparison, there is zero mathematical or semantic cross-verification. Because confidence is hardcoded to `1.0` in schemas, the system cannot distinguish between verified extractions and high-risk hallucinations.
5. **Premise 5 (Non-blocking Mathematical Gates)**: Because `HospitalBill.verify_arithmetic` does not raise an exception, and `Document Arithmetic Integrity` is registered as `tier=1` with `status="WARNING"`, claims with corrupted arithmetic, fabricated line items, or missing totals are never blocked from financial processing.
6. **Premise 6 (Broken Provenance Coupling & Severed Lineage)**: Because `Provenance[T]` wraps primitives without equality overrides, unit/E2E test assertions fail. Furthermore, because `FinancialMath` drops operand source IDs, calculation lineage is lost midway through adjudication, violating requirement R5.
7. **Conclusion**: To fulfill Requirements R3 and R5, the extraction and provenance layers must be redesigned from the ground up: (1) native multi-page PDF/OCR ingestion with dual-track cross-verification, (2) strict pre-adjudication mathematical and confidence rejection gates, (3) a decoupled, ubiquitous `EvidenceLedger` schema that tracks every variable from pixel bounding box to final statutory payout without breaking Pydantic data types.

---

## 3. Caveats

- **No Caveats**: The investigation spanned all extraction, preprocessing, VLM prompting, schema definition, forensics, rules orchestration, calculator math, and API endpoint files. Full file contents were inspected directly.

---

## 4. Conclusion

The ClaimGuard extraction and provenance architecture currently suffers from five critical architectural failures that prevent compliance with Requirements R3 and R5:
1. **Truncation and Destruction**: Ingestion truncates multi-page bills to page 1 for VLM and degrades image readability via aggressive OpenCV binarization.
2. **Fail-Open Fallbacks**: OCR fallback injects dummy models with `0.0` values and `"Unknown"` strings into the rule engine instead of failing closed with `EXTRACTION_FAILED`.
3. **Zero Cross-Verification & Confidence Blindness**: No cross-model or VLM-vs-OCR verification exists; confidence defaults unconditionally to `1.0`.
4. **Toothless Arithmetic Gates**: Document integrity is relegated to Tier 1 as a `WARNING`, allowing mathematically impossible bills to proceed to financial adjudication.
5. **Severed Evidence Ledger**: Provenance tracking is implemented via a leaky Pydantic generic wrapper that breaks primitive comparisons, lacks bounding box data, and discards operand lineages in `FinancialMath`.

---

## 5. Verification Method & Proposed Architecture

### 5.1 Verification Commands
- Check current test suite failures:
  ```powershell
  .\venv\Scripts\pytest.exe backend\tests\
  ```
- Specific tests demonstrating Provenance and arithmetic failures:
  ```powershell
  .\venv\Scripts\pytest.exe backend\tests\e2e\test_tier1_features.py -k "test_tier1_f11_evidence_line_item_provenance_retention"
  .\venv\Scripts\pytest.exe backend\tests\e2e\test_tier4_real_world.py -k "test_tier4_scenario_s5_high_value_cardiac_surgery_copay_sublimit"
  .\venv\Scripts\pytest.exe backend\tests\test_rules.py -k "test_proportionate_deduction_no_cap"
  ```

### 5.2 Required Architectural Redesign for R3 (Extraction & Cross-Verification)
1. **Multi-Page & Native PDF Ingestion**:
   - In `preprocessor.py`: Check if PDF has native digital text via `fitz.Page.get_text("words")`. If native words are present with high density, extract text tokens and bounding boxes directly.
   - For image rendering, render all pages at 300 DPI in RGB/grayscale without destructive binarization.
   - For multi-page bills, process all pages through VLM or page-by-page table parser, aggregating line items into a unified collection.
2. **Dual-Track Cross-Verification Engine**:
   - Run primary extraction (e.g. VLM) and secondary extraction (high-accuracy OCR / alternative VLM).
   - Compare critical financial anchors: `gross_total`, `subtotal`, `net_payable`, `room_charges_per_day`, `sum_insured`, `total_claimed`, `total_approved`, `total_deducted`.
   - Calculate field-level agreement score:
     $$\text{agreement} = 1.0 - \frac{|\text{val}_{\text{vlm}} - \text{val}_{\text{ocr}}|}{\max(\text{val}_{\text{vlm}}, \text{val}_{\text{ocr}})}$$
   - If critical field agreement $< 0.95$ or confidence $< 0.85$, reject output and return `status="NEEDS_REVIEW"` or `extraction_status="FAILED"`.
3. **Fail-Closed Validation & Rejection Gates**:
   - Enforce bill arithmetic invariant before adjudication:
     $$\sum \text{line\_items.amount} = \text{subtotal}$$
     $$\text{subtotal} + \text{tax} - \text{discount} = \text{net\_payable}$$
     $$\text{quantity} \times \text{unit\_rate} = \text{amount} \quad (\pm 1.0 \text{ INR})$$
   - Enforce rejection letter invariant:
     $$\text{total\_claimed} = \text{total\_approved} + \text{total\_deducted} \quad (\pm 1.0 \text{ INR})$$
   - If any arithmetic invariant fails, the extraction pipeline must return `extraction_status="FAILED"` and abort downstream adjudication.
   - Promote `Document Arithmetic Integrity` to **Tier 0 Gatekeeper** (`tier=0`) with `status="BLOCKED"`.
4. **Eliminate Synthetic Dummy Data**:
   - On extraction or OCR failure, never construct `HospitalBill(bill_id="OCR_FALLBACK", total_amount=0.0)`. Return a structured error response with `overall_status="EXTRACTION_FAILED"`.

### 5.3 Required Architectural Redesign for R5 (Ubiquitous Evidence Ledger)
1. **Decouple Provenance from Pydantic Primitive Types**:
   - Do NOT wrap primitives in `Provenance[T]`. Restore clean Pydantic fields (`total_amount: Decimal`, `quantity: Decimal`, `unit_rate: Decimal`, `patient_name: str`).
   - Implement `__eq__` on `Provenance[T]` if provenance objects must be used, or store provenance references via an attribute `provenance_id: str` pointing to the central ledger.
2. **Ubiquitous Evidence Ledger Schema**:
   Define a standalone schema and database model `EvidenceLedgerEntry`:
   ```python
   class EvidenceLedgerEntry(BaseModel):
       entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
       claim_id: str
       document_id: str
       document_hash: str  # SHA-256 hash of source document
       page_number: int    # 1-based page index
       bounding_box: Optional[List[float]] = None  # [ymin, xmin, ymax, xmax] normalized (0.0 to 1.0)
       section: Optional[str] = None               # e.g., "Room Charges Table", "Clause 4.2"
       source_text: str                           # Verbatim extracted text snippet
       extracted_value: Any                       # Value as extracted from document
       normalized_value: Any                      # Standardized value (Decimal, ISO date, etc.)
       rule_id: Optional[str] = None              # Applicable rule ID if produced by a rule
       formula: Optional[str] = None              # e.g., "expected_payable - insurer_payable"
       calculation_inputs: Optional[Dict[str, Any]] = None  # Operand dictionary with input provenance IDs
       final_output: Optional[Any] = None         # Computed result
       confidence: float                          # Calibrated confidence (0.0 to 1.0)
       created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
   ```
3. **Preserve Lineage Across Math & Adjudication**:
   - Update `FinancialMath` to use `decimal.Decimal` and store the list of parent `EvidenceLedgerEntry` IDs in `calculation_inputs`.
   - Update `RuleVerdict` and `RuleVerdictRecord` to include `evidence_entries: List[EvidenceLedgerEntry]`.
   - Compute SHA-256 upon file receipt in `api/upload.py` and `api/portal.py`, storing `document_hash` in `Document` model.
