from __future__ import annotations

import re


def count_currency_values(text: str) -> int:
    if not text:
        return 0
    hits_brl = re.findall(r"R\$\s*[\d\.,]+", text)
    hits_usd = re.findall(r"US\$\s*[\d\.,]+", text)
    return len(hits_brl) + len(hits_usd)
