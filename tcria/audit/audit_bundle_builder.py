from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from tcria.models import AuditRecord


def build_audit_bundle(records: list[AuditRecord], input_path: str, strict: bool) -> dict[str, object]:
    classification_counts = Counter(r.classification for r in records)
    route_counts = Counter(
        ((r.interpretation or {}).get("route_selection") or {}).get("selected_route", "UNDETERMINED")
        for r in records
    )
    document_role_counts = Counter(
        ((r.interpretation or {}).get("document_role") or {}).get("value", "UNDETERMINED")
        for r in records
    )
    accusation_set = [r.to_dict() for r in records if r.raises_accusation]
    non_accusation_set = [r.to_dict() for r in records if not r.raises_accusation]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_basis": "TCRIA modular engine audit (prescriptiveGate, complianceGate, traceabilityCheck)",
        "input_path": str(Path(input_path).expanduser().resolve()),
        "mode": "strict-explicit-decision-record" if strict else "default-heuristic",
        "compliance_gate_mode": "strict-explicit-decision-record" if strict else "default-heuristic",
        "total_files_scanned": len(records),
        "accusation_set_count": len(accusation_set),
        "classification_counts": dict(classification_counts),
        "route_counts": dict(route_counts),
        "document_role_counts": dict(document_role_counts),
        "accusation_set": accusation_set,
        "non_accusation_set": non_accusation_set,
    }
