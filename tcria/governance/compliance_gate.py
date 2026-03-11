from __future__ import annotations

import re

from tcria.models import GateResult


YES_VALUES = {"YES", "SIM", "TRUE", "APPROVED", "PASS"}


def _extract_decision_record(text: str) -> dict[str, str]:
    match = re.search(
        r"\[TCR-IA DECISION RECORD\](.*?)\[/TCR-IA DECISION RECORD\]",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return {}
    payload: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = value.strip()
    return payload


def evaluate_compliance_gate(text: str, strict: bool = True) -> GateResult:
    record = _extract_decision_record(text)
    if not record:
        if strict:
            return GateResult(
                status="BLOCKED",
                reason="DecisionRecord header not found in strict mode.",
            )
        has_actor = bool(re.search(r"\brespons[áa]vel|autor\s*:", text, flags=re.IGNORECASE))
        has_purpose = bool(re.search(r"\bobjetivo\s*:|\bfinalidade\s*:", text, flags=re.IGNORECASE))
        has_approval = bool(re.search(r"\baprovad[oa]\s*:|\baprovad[oa]\b", text, flags=re.IGNORECASE))
        if has_actor and has_purpose and has_approval:
            return GateResult(
                status="PASS",
                reason="Heuristic compliance indicators found outside explicit DecisionRecord.",
            )
        return GateResult(status="WARN", reason="Compliance indicators are partial in non-strict mode.")

    missing = []
    for required in ("responsibleHuman", "declaredPurpose", "approved"):
        if not record.get(required):
            missing.append(required)
    approved = (record.get("approved") or "").strip().upper()
    if approved and approved not in YES_VALUES:
        missing.append("approved=YES")

    if missing:
        return GateResult(
            status="BLOCKED",
            reason=f"DecisionRecord incomplete (missing {', '.join(missing)}).",
        )
    return GateResult(status="PASS", reason="DecisionRecord requirements satisfied.")
