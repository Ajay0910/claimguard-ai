# Handoff Report — Explorer M1-2: Evidence Ledger Schema & Document Hashing

**Agent**: Explorer M1-2 (Data Architect & Provenance Schema Specialist)  
**Milestone**: M1 (Type System, Provenance & Evidence Ledger)  
**Target Features**: F02 (Standalone Evidence Ledger Schema), F04 (Document SHA-256 Hashing)  
**Date**: 2026-09-27T06:55:00Z  

---

## 1. Observation

### 1.1 Existing Architecture & File State
1. **Schema Layer (`backend/app/schemas/`)**:
   - `backend/app/schemas/evidence_ledger.py` is absent.
   - `backend/app/schemas/provenance.py` defines `Provenance[T]` (lines 12–28) containing `source_document_id`, `source_hash`, `page`, `section`, `bounding_box`, `source_text`, and `context`. However, it is an in-memory generic wrapper tied to individual Pydantic attributes, lacking a centralized queryable ledger structure.
   - `backend/app/schemas/analysis_result.py` (`RuleVerdict` lines 7–19, `AnalysisResult` lines 20–48) currently lacks any reference or field for `EvidenceLedger` or `evidence_entries`.

2. **Database Models (`backend/app/models/claim.py`)**:
   - In `Document` (lines 28–45):
     ```python
     class Document(Base):
         __tablename__ = "documents"
         id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
         claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"))
         document_type: Mapped[str] = mapped_column(String)
         filename: Mapped[str] = mapped_column(String)
         original_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
         file_path: Mapped[str] = mapped_column(String)
         content_type: Mapped[str] = mapped_column(String)
         file_size_bytes: Mapped[int] = mapped_column()
         extracted_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
         extraction_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
         extraction_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
         created_at: Mapped[datetime] = mapped_column(server_default=func.now())
     ```
     `Document` has no `document_hash` column. Uploaded files do not have their cryptographic digest persisted.
   - There is no `EvidenceLedgerRecord` table. Provenance and calculation evidence cannot currently be queried via SQL or verified against document hashes.

3. **File Handler & Upload Endpoints**:
   - In `backend/app/utils/file_handler.py` (lines 21–39):
     `save_upload` reads 1MB chunks and writes to disk, returning `tuple[str, str, int]` (`file_path, mime_type, size_bytes`). It does not compute a cryptographic hash.
   - In `backend/app/api/upload.py` (lines 66–79):
     `save_upload` is called and `Document` is inserted with `file_size_bytes`, but no hash is recorded or returned in the response.
   - In `backend/app/api/portal.py` (lines 141–158):
     `upload_file.read()` reads file bytes directly and writes to disk, then creates `Document` without computing or storing a hash.

---

## 2. Logic Chain

1. **Observational Basis**:
   - Requirement R5 of `ORIGINAL_REQUEST.md` mandates: "Every finding must carry complete provenance: document ID, page, section, source text, extracted value, normalized value, rule ID, formula, calculation inputs, final output, and confidence."
   - Requirement R4 of `PROJECT.md` Feature F04 requires computing and storing cryptographic hash on document upload.
   - `Document` model in `claim.py` and `save_upload` in `file_handler.py` currently omit SHA-256 hash tracking entirely.

2. **Deduction & Architecture Decision**:
   - **F02 (Evidence Ledger Schema)**:
     - Must define `EvidenceLedgerEntry` as a standalone Pydantic v2 model capturing all 16 required attributes: `entry_id`, `claim_id`, `document_id`, `document_hash`, `page_number`, `bounding_box`, `section`, `source_text`, `extracted_value`, `normalized_value`, `rule_id`, `formula`, `calculation_inputs`, `final_output`, `confidence`, and `created_at`.
     - Must define `EvidenceLedger` as a structured collection model holding `entries: List[EvidenceLedgerEntry]`, equipped with query helpers (`get_by_id`, `filter_by_document`, `filter_by_rule`, `filter_by_section`), factory recorders (`record_extraction`, `record_calculation`), and conversion helpers (`from_provenance`).
     - Must update `RuleVerdict` and `AnalysisResult` in `analysis_result.py` with optional `evidence_entries` and `evidence_ledger` fields with safe defaults (`[]` and `None`) to preserve 100% backward compatibility with all existing tests.
   - **Database Persistence**:
     - Add `document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)` to `Document` in `backend/app/models/claim.py`.
     - Implement `EvidenceLedgerRecord` SQL table inheriting from `Base` with foreign keys to `Claim` (`claims.id`), `AnalysisRun` (`analysis_runs.id`), and `RuleVerdictRecord` (`rule_verdicts.id`), with indexes on `claim_id`, `document_hash`, and `rule_id`.
     - Implement dual persistence:
       1. Relational rows in `evidence_ledger_records` for SQL auditability and foreign-key integrity.
       2. JSON embedding in `AnalysisRun.result_data["evidence_ledger"]` for zero-overhead API serialization.
   - **F04 (Document SHA-256 Hashing)**:
     - Add pure helper `compute_sha256_bytes(data: bytes) -> str` and file streaming helper `compute_sha256_file(file_path: str, chunk_size: int = 65536) -> str` in `backend/app/utils/file_handler.py`.
     - Refactor `save_upload(file: UploadFile, upload_dir: str)` in `file_handler.py` to compute SHA-256 in-flight as chunks are streamed to disk, returning a 4-tuple `(file_path, mime_type, size_bytes, sha256_hash)`.
     - Update `backend/app/api/upload.py` to persist `document_hash` in `Document`, return `document_hash` in JSON response, and include it in `AuditTrail.log`.
     - Update `backend/app/api/portal.py` to compute `compute_sha256_bytes(content)` and persist `document_hash` in `Document` during portal submission.

---

## 3. Caveats

1. **Virtual/Synthetic Documents in Unit Tests**:
   - In unit/synthetic test cases, documents may not exist in the `documents` SQL table. Therefore, in `EvidenceLedgerRecord`, `document_id` must be stored as an indexed `String` rather than a hard foreign key (`ForeignKey("documents.id")`) to prevent foreign key constraint violations when running isolated rule tests. `claim_id` and `analysis_run_id` retain strict foreign keys.
2. **Backward Compatibility of `save_upload`**:
   - Only `backend/app/api/upload.py` currently invokes `save_upload`. Upgrading `save_upload` to return a 4-tuple `(file_path, mime_type, size_bytes, sha256_hash)` is safe and avoids redundant disk reads.
3. **Pydantic v2 Bounding Box Format**:
   - Normalized coordinates `[ymin, xmin, ymax, xmax]` range between `0.0` and `1.0`. Validation should allow `None` (for non-visual or whole-document extractions) and ensure that if supplied, exactly 4 floats are provided.

---

## 4. Conclusion & Concrete Implementation Specifications

### 4.1 Schema Implementation: `backend/app/schemas/evidence_ledger.py`

Create `backend/app/schemas/evidence_ledger.py` with the following implementation:

```python
"""
Evidence Ledger Schema for ClaimGuard AI.
Captures end-to-end provenance from document source tokens/bounding boxes
to final deterministic financial calculations.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
import uuid


class EvidenceLedgerEntry(BaseModel):
    """
    Individual evidence entry capturing exact provenance of an extracted
    variable or intermediate calculation.
    """
    model_config = ConfigDict(extra='ignore')

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_id: str
    document_id: str = Field(default="SYSTEM", description="Source document ID or SYSTEM")
    document_hash: str = Field(default="SYSTEM_DETERMINISTIC", description="SHA-256 hex digest of source document")
    page_number: int = Field(default=1, ge=1, description="1-based page number")
    bounding_box: Optional[List[float]] = Field(
        default=None, 
        description="[ymin, xmin, ymax, xmax] normalized coordinates (0.0 to 1.0)"
    )
    section: Optional[str] = Field(default=None, description="Document section, e.g., 'Room Charges Table' or 'Clause 4.1'")
    source_text: str = Field(default="", description="Verbatim text snippet extracted from document")
    extracted_value: Any = Field(default=None, description="Raw extracted value")
    normalized_value: Any = Field(default=None, description="Standardized value (e.g. Decimal, float, ISO date)")
    rule_id: Optional[str] = Field(default=None, description="Associated rule ID if produced or used by a rule")
    formula: Optional[str] = Field(default=None, description="Formula representation for derived calculations")
    calculation_inputs: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Operand mapping with input values and parent provenance IDs"
    )
    final_output: Optional[Any] = Field(default=None, description="Resulting output of calculation")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('bounding_box')
    @classmethod
    def validate_bounding_box(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 4:
                raise ValueError("bounding_box must contain exactly 4 coordinates: [ymin, xmin, ymax, xmax]")
            for coord in v:
                if not isinstance(coord, (int, float)):
                    raise ValueError(f"Coordinate {coord} must be a numeric float")
                if coord < 0.0 or coord > 1.0:
                    raise ValueError(f"Coordinate {coord} must be normalized between 0.0 and 1.0")
            if v[0] > v[2]:
                raise ValueError(f"ymin ({v[0]}) cannot be greater than ymax ({v[2]})")
            if v[1] > v[3]:
                raise ValueError(f"xmin ({v[1]}) cannot be greater than xmax ({v[3]})")
        return v

    @classmethod
    def from_provenance(
        cls,
        prov: Any,
        claim_id: str,
        document_hash: Optional[str] = None,
        rule_id: Optional[str] = None,
        formula: Optional[str] = None,
        calculation_inputs: Optional[Dict[str, Any]] = None,
        final_output: Optional[Any] = None,
        section: Optional[str] = None
    ) -> "EvidenceLedgerEntry":
        """
        Factory helper to bridge a Provenance[T] instance into an EvidenceLedgerEntry.
        """
        doc_id = getattr(prov, "source_document_id", "SYSTEM")
        doc_hash = document_hash or getattr(prov, "source_hash", None) or "SYSTEM_DETERMINISTIC"
        
        # Parse page number
        raw_page = getattr(prov, "page", 1)
        try:
            page_num = int(raw_page) if raw_page is not None else 1
            if page_num < 1:
                page_num = 1
        except (ValueError, TypeError):
            page_num = 1

        # Parse bounding box
        bbox = getattr(prov, "bounding_box", None)
        bbox_list = None
        if isinstance(bbox, dict):
            if all(k in bbox for k in ["ymin", "xmin", "ymax", "xmax"]):
                bbox_list = [bbox["ymin"], bbox["xmin"], bbox["ymax"], bbox["xmax"]]
        elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            bbox_list = [float(x) for x in bbox]

        source_txt = getattr(prov, "source_text", None) or getattr(prov, "context", "")
        extracted_val = getattr(prov, "value", None)
        normalized_val = getattr(prov, "normalized_value", None)
        conf = float(getattr(prov, "extraction_confidence", 1.0))

        return cls(
            claim_id=claim_id,
            document_id=doc_id,
            document_hash=doc_hash,
            page_number=page_num,
            bounding_box=bbox_list,
            section=section or getattr(prov, "section", None),
            source_text=source_txt,
            extracted_value=extracted_val,
            normalized_value=normalized_val,
            rule_id=rule_id,
            formula=formula,
            calculation_inputs=calculation_inputs,
            final_output=final_output,
            confidence=conf
        )


class EvidenceLedger(BaseModel):
    """
    Collection of EvidenceLedgerEntries for a claim, providing query,
    indexing, and audit validation methods.
    """
    model_config = ConfigDict(extra='ignore')

    claim_id: str
    entries: List[EvidenceLedgerEntry] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"

    def add_entry(self, entry: EvidenceLedgerEntry) -> EvidenceLedgerEntry:
        """Appends an entry and returns it."""
        self.entries.append(entry)
        return entry

    def add_entries(self, new_entries: List[EvidenceLedgerEntry]) -> None:
        """Bulk appends entries."""
        self.entries.extend(new_entries)

    def get_by_id(self, entry_id: str) -> Optional[EvidenceLedgerEntry]:
        """Finds an entry by entry_id."""
        for e in self.entries:
            if e.entry_id == entry_id:
                return e
        return None

    def filter_by_document(self, document_id: str) -> List[EvidenceLedgerEntry]:
        """Filters entries for a specific document ID."""
        return [e for e in self.entries if e.document_id == document_id]

    def filter_by_rule(self, rule_id: str) -> List[EvidenceLedgerEntry]:
        """Filters entries associated with a specific rule ID."""
        return [e for e in self.entries if e.rule_id == rule_id]

    def filter_by_section(self, section: str) -> List[EvidenceLedgerEntry]:
        """Filters entries from a specific document section."""
        return [e for e in self.entries if e.section == section]

    def record_extraction(
        self,
        document_id: str,
        document_hash: str,
        page_number: int,
        source_text: str,
        extracted_value: Any,
        normalized_value: Any = None,
        bounding_box: Optional[List[float]] = None,
        section: Optional[str] = None,
        confidence: float = 1.0
    ) -> EvidenceLedgerEntry:
        """Convenience recorder for document extraction items."""
        entry = EvidenceLedgerEntry(
            claim_id=self.claim_id,
            document_id=document_id,
            document_hash=document_hash,
            page_number=page_number,
            bounding_box=bounding_box,
            section=section,
            source_text=source_text,
            extracted_value=extracted_value,
            normalized_value=normalized_value,
            confidence=confidence
        )
        self.entries.append(entry)
        return entry

    def record_calculation(
        self,
        rule_id: str,
        formula: str,
        calculation_inputs: Dict[str, Any],
        final_output: Any,
        source_document_id: str = "CALCULATED",
        document_hash: str = "SYSTEM_DETERMINISTIC",
        confidence: float = 1.0
    ) -> EvidenceLedgerEntry:
        """Convenience recorder for intermediate or final financial calculation steps."""
        entry = EvidenceLedgerEntry(
            claim_id=self.claim_id,
            document_id=source_document_id,
            document_hash=document_hash,
            rule_id=rule_id,
            formula=formula,
            calculation_inputs=calculation_inputs,
            final_output=final_output,
            source_text=f"Formula: {formula}",
            confidence=confidence
        )
        self.entries.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        """Validates that all entries conform to invariants."""
        for e in self.entries:
            if not e.entry_id or not e.claim_id or not e.document_hash:
                return False
            if e.confidence < 0.0 or e.confidence > 1.0:
                return False
        return True

    def summary(self) -> Dict[str, Any]:
        """Generates summary statistics for UI rendering and auditing."""
        docs = list({e.document_id for e in self.entries if e.document_id})
        rules = list({e.rule_id for e in self.entries if e.rule_id})
        sections = list({e.section for e in self.entries if e.section})
        avg_conf = (
            sum(e.confidence for e in self.entries) / len(self.entries)
            if self.entries else 1.0
        )
        return {
            "claim_id": self.claim_id,
            "total_entries": len(self.entries),
            "documents_referenced": docs,
            "rules_referenced": rules,
            "sections_referenced": sections,
            "average_confidence": round(avg_conf, 4)
        }

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def __getitem__(self, index: int) -> EvidenceLedgerEntry:
        return self.entries[index]
```

### 4.2 Schema Export Updates

1. In `backend/app/schemas/__init__.py`, append:
```python
from .evidence_ledger import EvidenceLedgerEntry, EvidenceLedger
```

2. In `backend/app/schemas/analysis_result.py`:
Update `RuleVerdict` and `AnalysisResult` to optionally reference evidence:
```python
from .evidence_ledger import EvidenceLedgerEntry, EvidenceLedger

class RuleVerdict(BaseModel):
    model_config = ConfigDict(extra='ignore')
    rule_name: str
    rule_description: str = ""
    status: Literal["PASS", "FAIL", "SKIPPED", "NOT_APPLICABLE", "CONFLICT", "NEEDS_REVIEW", "WARNING", "BLOCKED"]
    confidence: float = 1.0
    finding: str
    insurer_calculation: Optional[float] = None
    correct_calculation: Optional[float] = None
    monetary_impact: Optional[float] = None
    regulatory_citation: Optional[str] = None
    appeal_recommendation: Optional[str] = None
    evidence_entry_ids: list[str] = []
    evidence_entries: list[EvidenceLedgerEntry] = []

class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    claim_id: str = ""
    analysis_timestamp: Union[str, datetime] = ""
    documents_analyzed: list[str] = []
    overall_status: Literal["NO_MISMATCH_FOUND", "MISMATCH_DETECTED", "REVIEW_RECOMMENDED", "EXTRACTION_FAILED", "BLOCKED"]
    rule_verdicts: list[RuleVerdict]
    appeal_evaluation: Optional[AppealEvaluationResult] = None
    total_monetary_impact: float = 0.0
    tier1_issues: int = 0
    tier2_flags: int = 0
    summary: str
    evidence_ledger: Optional[EvidenceLedger] = None
```

---

### 4.3 Database Model Updates: `backend/app/models/claim.py`

Update `backend/app/models/claim.py`:
1. Add `document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)` to `Document`.
2. Add relationships on `Claim`, `AnalysisRun`, and `RuleVerdictRecord`.
3. Add `EvidenceLedgerRecord` table.

```python
# In backend/app/models/claim.py:

# Under class Claim:
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )

# Under class Document:
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

# Under class AnalysisRun:
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )

# Under class RuleVerdictRecord:
    evidence_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    evidence_ledger_entries: Mapped[List["EvidenceLedgerRecord"]] = relationship(
        back_populates="rule_verdict", cascade="all, delete-orphan"
    )

# Add new model at end of claim.py:
class EvidenceLedgerRecord(Base):
    __tablename__ = "evidence_ledger_records"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"), index=True)
    analysis_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    rule_verdict_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rule_verdicts.id"), nullable=True, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    document_hash: Mapped[str] = mapped_column(String(64), index=True)
    page_number: Mapped[int] = mapped_column(default=1)
    bounding_box: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_text: Mapped[str] = mapped_column(Text)
    extracted_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    normalized_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    formula: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    calculation_inputs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    final_output: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    claim: Mapped["Claim"] = relationship(back_populates="evidence_ledger_entries")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship(back_populates="evidence_ledger_entries")
    rule_verdict: Mapped[Optional["RuleVerdictRecord"]] = relationship(back_populates="evidence_ledger_entries")
```

---

### 4.4 Hashing Utility Implementation: `backend/app/utils/file_handler.py`

Update `backend/app/utils/file_handler.py`:

```python
import os
import hashlib
import aiofiles
from fastapi import UploadFile

def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hex digest of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()

def compute_sha256_file(file_path: str, chunk_size: int = 65536) -> str:
    """Computes SHA-256 hex digest of a file on disk in streaming chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_mime_from_magic(header: bytes) -> str:
    """Sniffs PDF/JPEG/PNG/TIFF from magic numbers."""
    if header.startswith(b'%PDF'):
        return 'application/pdf'
    elif header.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
        return 'image/tiff'
    return 'application/octet-stream'

def validate_file_size(size: int, max_mb: int) -> bool:
    """Validates if file size in bytes is within the max_mb limit."""
    return size <= (max_mb * 1024 * 1024)

async def save_upload(file: UploadFile, upload_dir: str) -> tuple[str, str, int, str]:
    """
    Saves file, returns (path, mime_type, size_bytes, sha256_hash).
    Validates magic bytes and computes SHA-256 digest in a single streaming pass.
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    # Read first 10 bytes for magic number
    header = await file.read(10)
    await file.seek(0)
    
    mime_type = get_mime_from_magic(header)
    
    file_path = os.path.join(upload_dir, file.filename or "uploaded_file")
    
    size_bytes = 0
    hasher = hashlib.sha256()
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):  # Read 1MB chunks
            size_bytes += len(content)
            hasher.update(content)
            await out_file.write(content)
            
    sha256_hash = hasher.hexdigest()
    return file_path, mime_type, size_bytes, sha256_hash
```

---

### 4.5 API Updates: `backend/app/api/upload.py` and `backend/app/api/portal.py`

#### In `backend/app/api/upload.py`:
Lines 65–91:
```python
    upload_dir = settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else os.path.join("data", "uploads")
    file_path, mime_type, size_bytes, doc_hash = await save_upload(file, upload_dir)

    document_id = str(uuid.uuid4())
    new_doc = Document(
        id=document_id,
        claim_id=claim_id,
        document_type=document_type,
        filename=file.filename or "unknown",
        file_path=file_path,
        content_type=mime_type,
        file_size_bytes=size_bytes,
        document_hash=doc_hash,
        created_at=datetime.utcnow()
    )
    db.add(new_doc)
    
    await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
        "filename": file.filename, 
        "document_type": document_type,
        "document_hash": doc_hash,
        "file_size_bytes": size_bytes
    })
    
    await db.commit()
    
    return {
        "claim_id": claim_id,
        "document_id": document_id,
        "filename": file.filename,
        "document_hash": doc_hash,
        "status": "success"
    }
```
And in `list_documents` (lines 101–111):
```python
    return [
        {
            "id": doc.id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "document_hash": doc.document_hash,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "extracted_data": doc.extracted_data
        }
        for doc in documents
    ]
```

#### In `backend/app/api/portal.py`:
Lines 140–160:
```python
        from ..utils.file_handler import compute_sha256_bytes
        from ..utils.audit_trail import AuditTrail

        content = await upload_file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{doc_type} exceeds 25MB limit.")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        doc_hash = compute_sha256_bytes(content)

        doc = Document(
            id=file_id,
            claim_id=claim_id,
            document_type=doc_type,
            filename=filename,
            original_filename=upload_file.filename,
            file_path=file_path,
            content_type=upload_file.content_type,
            file_size_bytes=len(content),
            document_hash=doc_hash,
        )
        db.add(doc)

        await AuditTrail.log(db, claim_id, "DOCUMENT_UPLOADED", {
            "document_id": file_id,
            "filename": upload_file.filename,
            "document_type": doc_type,
            "document_hash": doc_hash,
            "file_size_bytes": len(content)
        })
```

---

## 5. Verification Method

### 5.1 Verification Commands
The implementing worker must execute:
```powershell
.\venv\Scripts\pytest backend/tests/test_evidence_ledger.py -v
```

### 5.2 Test Suite Specification: `backend/tests/test_evidence_ledger.py`
A test file must be created to verify all aspects of F02 and F04:

```python
import pytest
import hashlib
from app.schemas.evidence_ledger import EvidenceLedgerEntry, EvidenceLedger
from app.schemas.provenance import Provenance
from app.models.claim import Claim, Document, EvidenceLedgerRecord
from app.utils.file_handler import compute_sha256_bytes, compute_sha256_file


def test_evidence_ledger_entry_valid():
    entry = EvidenceLedgerEntry(
        claim_id="CLM-001",
        document_id="DOC-BILL-01",
        document_hash="a" * 64,
        page_number=2,
        bounding_box=[0.1, 0.2, 0.3, 0.4],
        section="Room Charges Table",
        source_text="Room Rent 5 days @ 8000/day = 40000",
        extracted_value=40000.0,
        normalized_value=40000.0,
        rule_id="RULE_ROOM_RENT_CAPPING",
        formula="days * daily_rate",
        calculation_inputs={"days": 5, "daily_rate": 8000},
        final_output=40000.0,
        confidence=0.98
    )
    assert entry.claim_id == "CLM-001"
    assert entry.bounding_box == [0.1, 0.2, 0.3, 0.4]
    assert entry.confidence == 0.98


def test_evidence_ledger_entry_bounding_box_validation():
    # Invalid length
    with pytest.raises(ValueError, match="exactly 4 coordinates"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="test",
            bounding_box=[0.1, 0.2]
        )
    # ymin > ymax
    with pytest.raises(ValueError, match="ymin .* cannot be greater than ymax"):
        EvidenceLedgerEntry(
            claim_id="CLM-001",
            source_text="test",
            bounding_box=[0.8, 0.2, 0.3, 0.4]
        )


def test_evidence_ledger_entry_from_provenance():
    prov = Provenance(
        value=5000.0,
        normalized_value=5000.0,
        source_document_id="DOC-POL-01",
        source_hash="b" * 64,
        page="3",
        section="Schedule of Benefits",
        source_text="Daily room rent capped at 5000 per day",
        extraction_confidence=0.95
    )
    entry = EvidenceLedgerEntry.from_provenance(prov, claim_id="CLM-002", rule_id="RULE_ROOM_RENT")
    assert entry.claim_id == "CLM-002"
    assert entry.document_id == "DOC-POL-01"
    assert entry.document_hash == "b" * 64
    assert entry.page_number == 3
    assert entry.extracted_value == 5000.0
    assert entry.confidence == 0.95
    assert entry.section == "Schedule of Benefits"


def test_evidence_ledger_operations():
    ledger = EvidenceLedger(claim_id="CLM-100")
    
    e1 = ledger.record_extraction(
        document_id="DOC-1",
        document_hash="c" * 64,
        page_number=1,
        source_text="Subtotal: 100000",
        extracted_value=100000,
        section="Summary",
        confidence=0.99
    )
    e2 = ledger.record_calculation(
        rule_id="RULE_PROPORTIONATE_DEDUCTION",
        formula="100000 * (5000 / 8000)",
        calculation_inputs={"eligible": 5000, "billed": 8000},
        final_output=62500.0
    )

    assert len(ledger) == 2
    assert ledger.get_by_id(e1.entry_id) == e1
    assert len(ledger.filter_by_document("DOC-1")) == 1
    assert len(ledger.filter_by_rule("RULE_PROPORTIONATE_DEDUCTION")) == 1
    assert ledger.verify_integrity() is True

    summary = ledger.summary()
    assert summary["total_entries"] == 2
    assert summary["claim_id"] == "CLM-100"


def test_hashing_utilities(tmp_path):
    data = b"Hospital Bill Content for ClaimGuard AI Verification"
    expected_hash = hashlib.sha256(data).hexdigest()
    
    assert compute_sha256_bytes(data) == expected_hash

    test_file = tmp_path / "test_doc.pdf"
    test_file.write_bytes(data)
    assert compute_sha256_file(str(test_file)) == expected_hash


@pytest.mark.asyncio
async def test_database_models_persistence(async_test_db):
    claim = Claim(id="CLM-DB-001", patient_name="Aarav Sharma", status="PENDING")
    async_test_db.add(claim)
    await async_test_db.flush()

    doc = Document(
        id="DOC-DB-001",
        claim_id=claim.id,
        document_type="HOSPITAL_BILL",
        filename="bill.pdf",
        file_path="/tmp/bill.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        document_hash="d" * 64
    )
    async_test_db.add(doc)

    record = EvidenceLedgerRecord(
        id="EV-001",
        claim_id=claim.id,
        document_id=doc.id,
        document_hash=doc.document_hash,
        page_number=1,
        source_text="Patient admitted on 2025-01-01",
        extracted_value="2025-01-01",
        confidence=1.0
    )
    async_test_db.add(record)
    await async_test_db.commit()

    from sqlalchemy import select
    res = await async_test_db.execute(select(Document).where(Document.id == "DOC-DB-001"))
    fetched_doc = res.scalar_one()
    assert fetched_doc.document_hash == "d" * 64

    res2 = await async_test_db.execute(select(EvidenceLedgerRecord).where(EvidenceLedgerRecord.id == "EV-001"))
    fetched_ev = res2.scalar_one()
    assert fetched_ev.document_hash == "d" * 64
    assert fetched_ev.extracted_value == "2025-01-01"
```

### 5.3 Invalidation Conditions
- Any changes that omit the 16 required fields on `EvidenceLedgerEntry`.
- Hashing that requires re-reading file streams from disk after upload rather than streaming calculation.
- Schema changes that break existing `RuleVerdict` or `AnalysisResult` deserialization.
