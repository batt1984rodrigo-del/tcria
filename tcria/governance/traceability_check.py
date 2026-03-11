from __future__ import annotations

from tcria.models import GateResult


def evaluate_traceability_check(signals: dict[str, object]) -> GateResult:
    dates = int(signals.get("dates_found", 0))
    money = int(signals.get("currency_values_found", 0))
    evidence_markers = sum((signals.get("evidence_marker_hits") or {}).values())
    score = (1 if dates > 0 else 0) + (1 if money > 0 else 0) + (1 if evidence_markers > 0 else 0)
    evidence = f"dates={dates}, currency={money}, markers={evidence_markers}"

    if score >= 2:
        return GateResult(status="PASS", reason="Multiple traceability signals found.", evidence=evidence)
    if score == 1:
        return GateResult(status="WARN", reason="Limited traceability signals found.", evidence=evidence)
    return GateResult(status="WARN", reason="No clear traceability signals found.", evidence=evidence)
