from __future__ import annotations

from tcria.models import GateResult


PRESCRIPTIVE_PATTERNS = (
    "você deve",
    "deve-se",
    "é obrigatório",
    "a única solução é",
)


def evaluate_prescriptive_gate(text: str) -> GateResult:
    text_l = text.lower()
    hits = [pattern for pattern in PRESCRIPTIVE_PATTERNS if pattern in text_l]
    if hits:
        return GateResult(
            status="BLOCKED",
            reason="Prescriptive/condemnatory language detected.",
            evidence=", ".join(hits[:5]),
        )
    return GateResult(status="PASS", reason="No prescriptive patterns detected.")
