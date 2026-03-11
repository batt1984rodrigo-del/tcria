from __future__ import annotations

from io import BytesIO
from pathlib import Path


def _extract_pdf_text(source: str | BytesIO, method: str) -> tuple[str, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", "error", "pypdf_missing"

    try:
        reader = PdfReader(source)
    except Exception:
        return "", "error", "pypdf_open_error"

    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages), "ok", method


def extract_pdf_text(path: Path) -> tuple[str, str, str]:
    return _extract_pdf_text(str(path), "pypdf")


def extract_pdf_text_from_bytes(raw: bytes) -> tuple[str, str, str]:
    return _extract_pdf_text(BytesIO(raw), "pypdf-bytes")
