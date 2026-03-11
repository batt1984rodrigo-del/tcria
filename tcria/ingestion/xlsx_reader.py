from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile


NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("main:si", NS):
        parts = [node.text or "" for node in si.findall(".//main:t", NS)]
        strings.append("".join(parts))
    return strings


def _sheet_text(zf: zipfile.ZipFile, shared_strings: list[str]) -> str:
    lines: list[str] = []
    sheet_names = sorted(
        name for name in zf.namelist() if name.startswith("xl/worksheets/") and name.endswith(".xml")
    )
    for name in sheet_names:
        root = ET.fromstring(zf.read(name))
        for row in root.findall(".//main:row", NS):
            values: list[str] = []
            for cell in row.findall("main:c", NS):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", NS)
                inline_node = cell.find("main:is", NS)
                value = ""
                if cell_type == "s" and value_node is not None and value_node.text:
                    idx = int(value_node.text)
                    if 0 <= idx < len(shared_strings):
                        value = shared_strings[idx]
                elif inline_node is not None:
                    texts = [node.text or "" for node in inline_node.findall(".//main:t", NS)]
                    value = "".join(texts)
                elif value_node is not None and value_node.text:
                    value = value_node.text
                if value:
                    values.append(value)
            if values:
                lines.append(" | ".join(values))
    return "\n".join(lines)


def _extract_xlsx(raw: bytes, method: str) -> tuple[str, str, str]:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            shared = _shared_strings(zf)
            text = _sheet_text(zf, shared)
            return text, "ok", method
    except Exception:
        return "", "error", f"{method}-open-error"


def extract_xlsx_text(path: Path) -> tuple[str, str, str]:
    return _extract_xlsx(path.read_bytes(), "xlsx-xml")


def extract_xlsx_text_from_bytes(raw: bytes) -> tuple[str, str, str]:
    return _extract_xlsx(raw, "xlsx-xml-bytes")
