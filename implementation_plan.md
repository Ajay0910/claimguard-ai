# Diagnostic Report & Remediation Plan

## 1. Structural Discrepancies (Deviations from PDF)
- **Fraud Adjudication Out of Scope**: The architecture PDF explicitly dictates that Tier 2 outputs must strictly be `"FLAGGED FOR REVIEW"` and that the system `"never issues a fraud verdict"`. However, the codebase includes `app/forensics/fraud_scorer.py`, which computes a `CompositeFraudScore`, assigns a `risk_tier` (e.g., "CRITICAL", "HIGH"), and issues a "fraud risk" percentage. This violates the system's "safe-failure" and "non-adjudicating" core principles.
- **Missing `PyMuPDF` implementation for extraction**: The PDF specifies `PyMuPDF` for PDF handling. However, `app/extraction/preprocessor.py` is currently using `pdf2image`, which relies on an external system binary (`poppler`) that is not guaranteed to exist on Windows or Render.

## 2. Critical Error Inventory
- **`PermissionError` on Windows (Runtime Crash)**: In `app/extraction/preprocessor.py`, when OpenCV is unavailable (which is true here since `opencv-python-headless` was removed), it falls back to `PIL.Image.open()`. The code then immediately attempts to `os.remove()` the temporary PDF-extracted images. Because PIL uses lazy loading, it holds the file handle open, causing a `[WinError 32]` crash that aborts the entire extraction pipeline.
- **Pydantic `ValidationError` (Build/Startup Crash)**: If the backend is started without manually copying `.env.example` to `.env` (e.g., bypassing `start.bat`), `uvicorn` instantly crashes with a Pydantic `ValidationError` because `SECRET_KEY` lacks a default value in `config.py`. 
- **OCR Engine Fallback Failure**: The fallback OCR logic in `pipeline.py` populates a dummy `InsurancePolicy` but doesn't actually extract values, meaning any document that fails the VLM step (e.g. missing API keys) will silently pass through as dummy data instead of raising a proper extraction error.

## 3. Remediation Strategy (Step-by-Step)
1. **Fix the File Lock Crash**: Modify `prepare_document` and `preprocess_image` in `preprocessor.py` to call `image.load()` or `image.copy()` before calling `os.remove()`, safely releasing the Windows file handle.
2. **Replace `pdf2image` with `PyMuPDF`**: Migrate the `pdf_to_images` function in `preprocessor.py` to use `fitz` (PyMuPDF) for page rendering. This eliminates the `poppler` system dependency and aligns with the architectural spec.
3. **Refactor Fraud Scorer**: Modify `fraud_scorer.py` and the `CompositeFraudScore` schema to remove explicit fraud percentages and "CRITICAL" risk tiers. Replace these with neutral terminology (e.g., `Anomaly Density`, `Review Priority`) and ensure the final output is bounded to `"FLAGGED FOR REVIEW"`, adhering to the strict safe-failure discipline.
4. **Fix Configuration Bootstrapping**: Add a safe fallback/default for `SECRET_KEY` in `config.py` or catch the error in `main.py` to prevent confusing startup stack traces.
5. **Run Integration Testing**: Run the pipeline directly against the provided test datasets (`media_1789921532889.pdf` and `media_1789921532898.pdf`) to verify end-to-end functionality.

Please provide your explicit approval to begin executing this remediation plan.
