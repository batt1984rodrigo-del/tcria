from __future__ import annotations

from io import BytesIO
from pathlib import Path


def _extract_docx_text(source: str | BytesIO, method: str) -> tuple[str, str, str]:
    try:
        from docx import Document as DocxDocument  # type: ignore
    except Exception:
        return "", "error", "python-docx_missing"

    try:
        doc = DocxDocument(source)
    except Exception:
        return "", "error", "python-docx_open_error"

    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    return text, "ok", method


def extract_docx_text(path: Path) -> tuple[str, str, str]:
    return _extract_docx_text(str(path), "python-docx")


def extract_docx_text_from_bytes(raw: bytes) -> tuple[str, str, str]:
    return _extract_docx_text(BytesIO(raw), "python-docx-bytes")
