from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Document:
    path: Path
    relative_path: str
    suffix: str
    size_bytes: int
    sha256: str
    text: str
    extraction_status: str
    extraction_method: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


@dataclass
class GateResult:
    status: str
    reason: str
    evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditRecord:
    document: Document
    classification: str
    artifact_type: str
    artifact_type_reason: str
    interpretation: dict[str, Any] | None
    raises_accusation: bool
    classification_reasons: list[str]
    signals: dict[str, Any]
    gates: dict[str, dict[str, Any]] | None
    overall_outcome: str | None

    def to_dict(self) -> dict[str, Any]:
        text_chars = len(self.document.text or "")
        return {
            "file_name": self.document.path.name,
            "file_path": str(self.document.path),
            "suffix": self.document.suffix,
            "size_bytes": self.document.size_bytes,
            "sha256": self.document.sha256,
            "extraction_status": self.document.extraction_status,
            "extraction_method": self.document.extraction_method,
            "text_chars": text_chars,
            "text_quality": _classify_text_quality(text_chars, self.document.suffix),
            "sensitive_handling": "normal",
            "document": self.document.to_dict(),
            "classification": self.classification,
            "artifact_type": self.artifact_type,
            "artifact_type_reason": self.artifact_type_reason,
            "interpretation": self.interpretation,
            "raises_accusation": self.raises_accusation,
            "classification_reasons": self.classification_reasons,
            "key_signals": self.signals,
            "gates": self.gates,
            "overall_outcome": self.overall_outcome,
        }


def _classify_text_quality(chars: int, suffix: str) -> str:
    if chars == 0:
        return "none"
    thresholds = {
        ".csv": (600, 150),
        ".txt": (1200, 250),
        ".docx": (1200, 300),
        ".md": (1000, 200),
        ".html": (1200, 300),
        ".htm": (1200, 300),
        ".pdf": (1000, 250),
    }
    hi, mid = thresholds.get(suffix, (1000, 250))
    if chars >= hi:
        return "high"
    if chars >= mid:
        return "medium"
    return "low"
