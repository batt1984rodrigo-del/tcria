from __future__ import annotations

import hashlib
from io import BytesIO
import zipfile
from pathlib import Path
from typing import Optional

from tcria.ingestion.docx_reader import extract_docx_text
from tcria.ingestion.docx_reader import extract_docx_text_from_bytes
from tcria.ingestion.html_reader import extract_html_text
from tcria.ingestion.pdf_reader import extract_pdf_text
from tcria.ingestion.pdf_reader import extract_pdf_text_from_bytes
from tcria.ingestion.xlsx_reader import extract_xlsx_text
from tcria.ingestion.xlsx_reader import extract_xlsx_text_from_bytes
from tcria.models import Document


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".csv", ".html", ".htm", ".zip", ".xlsx"}
ARCHIVE_ENTRY_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".csv", ".html", ".htm", ".zip", ".xlsx"}


def _decode_text(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin1", errors="replace"), "latin1-replace"


def _extract_text(path: Path) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".docx":
        return extract_docx_text(path)
    if suffix == ".xlsx":
        return extract_xlsx_text(path)
    if suffix in {".html", ".htm"}:
        return extract_html_text(path.read_bytes())
    if suffix in {".txt", ".md", ".csv"}:
        text, encoding = _decode_text(path.read_bytes())
        return text, "ok", encoding
    return "", "unsupported", "none"


def _extract_text_from_bytes(raw: bytes, suffix: str) -> tuple[str, str, str]:
    if suffix == ".pdf":
        return extract_pdf_text_from_bytes(raw)
    if suffix == ".docx":
        return extract_docx_text_from_bytes(raw)
    if suffix == ".xlsx":
        return extract_xlsx_text_from_bytes(raw)
    if suffix in {".html", ".htm"}:
        return extract_html_text(raw)
    if suffix in {".txt", ".md", ".csv"}:
        text, encoding = _decode_text(raw)
        return text, "ok", encoding
    return "", "unsupported", "none"


def _iter_supported_files(root: Path, max_files: Optional[int] = None) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_SUFFIXES else []
    files: list[Path] = []
    for child in sorted(root.rglob("*")):
        if child.is_symlink():
            continue
        if child.is_file() and child.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(child)
            if max_files is not None and len(files) > max_files:
                raise ValueError(f"Input exceeds max_files={max_files}.")
    return files


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_documents_from_zip(path: Path) -> list[Document]:
    return _load_documents_from_zip_raw(path.read_bytes(), path.name, path)


def _load_documents_from_zip_raw(raw_zip: bytes, label: str, source_path: Path | None = None) -> list[Document]:
    documents: list[Document] = []
    with zipfile.ZipFile(BytesIO(raw_zip)) as zf:
        for info in sorted(zf.infolist(), key=lambda item: item.filename.lower()):
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix not in ARCHIVE_ENTRY_SUFFIXES:
                continue
            raw = zf.read(info)
            if suffix == ".zip":
                nested_label = f"{label}/{info.filename}"
                documents.extend(_load_documents_from_zip_raw(raw, nested_label, source_path))
                continue
            text, extraction_status, extraction_method = _extract_text_from_bytes(raw, suffix)
            base_path = source_path if source_path is not None else Path(label)
            virtual_path = Path(f"{base_path}!/{info.filename}")
            documents.append(
                Document(
                    path=virtual_path,
                    relative_path=f"{label}/{info.filename}",
                    suffix=suffix,
                    size_bytes=info.file_size,
                    sha256=_sha256_bytes(raw),
                    text=text,
                    extraction_status=extraction_status,
                    extraction_method=f"zip:{extraction_method}",
                )
            )
    return documents


def load_documents(
    input_path: str,
    *,
    max_files: Optional[int] = None,
    max_total_bytes: Optional[int] = None,
) -> list[Document]:
    root = Path(input_path).expanduser().resolve()
    if not root.exists():
        raise ValueError(f"Input path does not exist: {root}")
    if not root.is_file() and not root.is_dir():
        raise ValueError(f"Input path must be a file or directory: {root}")
    if max_files is not None and max_files <= 0:
        raise ValueError("max_files must be greater than zero.")
    if max_total_bytes is not None and max_total_bytes <= 0:
        raise ValueError("max_total_bytes must be greater than zero.")

    files = _iter_supported_files(root, max_files=max_files)
    documents: list[Document] = []
    total_bytes = 0
    for fp in files:
        file_documents: list[Document]
        if fp.suffix.lower() == ".zip":
            file_documents = _load_documents_from_zip(fp)
        else:
            size_bytes = fp.stat().st_size
            text, extraction_status, extraction_method = _extract_text(fp)
            rel = str(fp.relative_to(root)) if root.is_dir() else fp.name
            file_documents = [
                Document(
                    path=fp,
                    relative_path=rel,
                    suffix=fp.suffix.lower(),
                    size_bytes=size_bytes,
                    sha256=_sha256_file(fp),
                    text=text,
                    extraction_status=extraction_status,
                    extraction_method=extraction_method,
                )
            ]

        for doc in file_documents:
            total_bytes += doc.size_bytes
            if max_total_bytes is not None and total_bytes > max_total_bytes:
                raise ValueError(f"Input exceeds max_total_bytes={max_total_bytes}.")
            documents.append(doc)
            if max_files is not None and len(documents) > max_files:
                raise ValueError(f"Input exceeds max_files={max_files}.")
    return documents
