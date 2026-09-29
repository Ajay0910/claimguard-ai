"""
Evidence Ledger Schema for ClaimGuard AI.
Captures end-to-end provenance from document source tokens/bounding boxes
to final deterministic financial calculations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceLedgerEntry(BaseModel):
    """
    Individual evidence entry capturing exact provenance of an extracted
    variable or intermediate calculation.
    """
    model_config = ConfigDict(extra="ignore")

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_id: str
    document_id: str = Field(default="SYSTEM", description="Source document ID or SYSTEM")
    document_hash: str = Field(
        default="SYSTEM_DETERMINISTIC",
        description="SHA-256 hex digest of source document",
    )
    page_number: int = Field(default=1, ge=1, description="1-based page number")
    bounding_box: Optional[List[float]] = Field(
        default=None,
        description="[ymin, xmin, ymax, xmax] normalized coordinates (0.0 to 1.0)",
    )
    section: Optional[str] = Field(
        default=None,
        description="Document section, e.g., 'Room Charges Table' or 'Clause 4.1'",
    )
    source_text: str = Field(
        default="", description="Verbatim text snippet extracted from document"
    )
    extracted_value: Any = Field(default=None, description="Raw extracted value")
    value: Any = Field(default=None, description="Alias for extracted_value")
    normalized_value: Any = Field(
        default=None, description="Standardized value (e.g. Decimal, float, ISO date)"
    )
    source_document_type: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    transformations: List[Any] = Field(default_factory=list)
    rule_id: Optional[str] = Field(
        default=None, description="Associated rule ID if produced or used by a rule"
    )
    formula: Optional[str] = Field(
        default=None, description="Formula representation for derived calculations"
    )
    calculation_inputs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Operand mapping with input values and parent provenance IDs",
    )
    final_output: Optional[Any] = Field(
        default=None, description="Resulting output of calculation"
    )
    calculation_output: Optional[Any] = Field(
        default=None, description="Alias for final output of calculation"
    )
    extraction_confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator("bounding_box")
    @classmethod
    def validate_bounding_box(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 4:
                raise ValueError(
                    "bounding_box must contain exactly 4 coordinates: [ymin, xmin, ymax, xmax]"
                )
            for coord in v:
                if not isinstance(coord, (int, float)):
                    raise ValueError(f"Coordinate {coord} must be a numeric float")
                if coord < 0.0 or coord > 1.0:
                    raise ValueError(
                        f"Coordinate {coord} must be normalized between 0.0 and 1.0"
                    )
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
        section: Optional[str] = None,
    ) -> "EvidenceLedgerEntry":
        """
        Factory helper to bridge a Provenance[T] instance into an EvidenceLedgerEntry.
        """
        doc_id = getattr(prov, "source_document_id", "SYSTEM")
        doc_hash = (
            document_hash
            or getattr(prov, "source_hash", None)
            or "SYSTEM_DETERMINISTIC"
        )

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
                bbox_list = [
                    float(bbox["ymin"]),
                    float(bbox["xmin"]),
                    float(bbox["ymax"]),
                    float(bbox["xmax"]),
                ]
        elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            bbox_list = [float(x) for x in bbox]

        source_txt = (
            getattr(prov, "source_text", None)
            or getattr(prov, "context", "")
            or ""
        )
        extracted_val = getattr(prov, "value", None)
        normalized_val = getattr(prov, "normalized_value", None)
        conf = float(getattr(prov, "extraction_confidence", 1.0))

        calc_in = calculation_inputs if calculation_inputs is not None else getattr(prov, "calculation_inputs", None)
        form = formula if formula is not None else getattr(prov, "formula", None)
        r_id = rule_id if rule_id is not None else getattr(prov, "rule_id", None)
        f_out = (
            final_output
            if final_output is not None
            else getattr(prov, "value", None)
        )
        
        raw_transformations = getattr(prov, "transformations", [])
        clean_transformations = []
        for t in raw_transformations:
            if isinstance(t, (int, float, str, bool, dict, list)):
                clean_transformations.append(t)
            else:
                clean_transformations.append(str(t))

        return cls(
            claim_id=claim_id,
            document_id=str(doc_id) if doc_id else "SYSTEM",
            document_hash=str(doc_hash),
            page_number=page_num,
            bounding_box=bbox_list,
            section=section if section is not None else getattr(prov, "section", None),
            source_text=source_txt,
            extracted_value=extracted_val,
            value=extracted_val,
            normalized_value=normalized_val,
            source_document_type=getattr(prov, "source_document_type", None) or getattr(prov, "source_type", None),
            model=getattr(prov, "extraction_model", None) or getattr(prov, "model", None),
            transformations=clean_transformations,
            timestamp=getattr(prov, "timestamp", None) or datetime.utcnow().isoformat(),
            rule_id=r_id,
            formula=form,
            calculation_inputs=calc_in,
            final_output=f_out,
            calculation_output=f_out,
            extraction_confidence=conf,
            confidence=conf,
        )


class EvidenceLedger(BaseModel):
    """
    Collection of EvidenceLedgerEntries for a claim, providing query,
    indexing, and audit validation methods.
    """
    model_config = ConfigDict(extra="ignore")

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
        confidence: float = 1.0,
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
            confidence=confidence,
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
        confidence: float = 1.0,
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
            calculation_output=final_output,
            value=final_output,
            normalized_value=final_output,
            extracted_value=final_output,
            source_text=f"Formula: {formula}",
            confidence=confidence,
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
        docs = sorted(list({e.document_id for e in self.entries if e.document_id}))
        rules = sorted(list({e.rule_id for e in self.entries if e.rule_id}))
        sections = sorted(list({e.section for e in self.entries if e.section}))
        avg_conf = (
            sum(e.confidence for e in self.entries) / len(self.entries)
            if self.entries
            else 1.0
        )
        return {
            "claim_id": self.claim_id,
            "total_entries": len(self.entries),
            "documents_referenced": docs,
            "rules_referenced": rules,
            "sections_referenced": sections,
            "average_confidence": round(avg_conf, 4),
        }

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def __getitem__(self, index: int) -> EvidenceLedgerEntry:
        return self.entries[index]
