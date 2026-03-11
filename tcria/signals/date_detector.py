from __future__ import annotations

import re


def count_dates(text: str) -> int:
    if not text:
        return 0
    ddmmyyyy = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text)
    iso = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    return len(ddmmyyyy) + len(iso)
