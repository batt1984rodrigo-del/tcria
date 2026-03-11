from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


YES_VALUES = {"YES", "TRUE", "APPROVED", "PASS", "SIM"}


@dataclass
class ConclusionQuestion:
    id: str
    question: str
    answer: str  # SIM | NAO | INSUFICIENTE
    confidence: str  # HIGH | MEDIUM | LOW
    rationale: str
    evidence_refs: list[str]


@dataclass
class ConclusionReport:
    overall_answer: str  # SIM | NAO | INSUFICIENTE
    overall_confidence: str
    summary: str
    questions: list[ConclusionQuestion]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _deep_get(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _extract_gate_status(gate_value: Any) -> str:
    if isinstance(gate_value, dict):
        return _norm(gate_value.get("status"))
    if isinstance(gate_value, str):
        return _norm(gate_value)
    return ""


def _collect_gate_statuses(bundle: dict[str, Any], gate_name: str) -> list[str]:
    statuses: list[str] = []

    primary = _deep_get(bundle, "gates", gate_name, "status")
    if primary:
        statuses.append(_norm(primary))

    gates = bundle.get("gates")
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            if _norm(gate.get("name")) == _norm(gate_name):
                status = _norm(gate.get("status"))
                if status:
                    statuses.append(status)

    top_level = bundle.get(gate_name)
    status = _extract_gate_status(top_level)
    if status:
        statuses.append(status)

    accusation_set = bundle.get("accusation_set")
    if isinstance(accusation_set, list):
        for rec in accusation_set:
            if not isinstance(rec, dict):
                continue
            rec_gates = rec.get("gates")
            if not isinstance(rec_gates, dict):
                continue
            rec_status = _extract_gate_status(rec_gates.get(gate_name))
            if rec_status:
                statuses.append(rec_status)

    return statuses


def _find_gate_status(bundle: dict[str, Any], gate_name: str) -> str:
    statuses = _collect_gate_statuses(bundle, gate_name)
    if not statuses:
        return ""

    priorities = ["BLOCKED", "FAIL", "ERROR", "PASS", "WARN", "NOT_APPLICABLE", "NOT_EVALUATED"]
    for priority in priorities:
        if priority in statuses:
            return priority
    return statuses[0]


def _find_decision_record(bundle: dict[str, Any]) -> dict[str, Any]:
    dr = bundle.get("decisionRecord")
    if isinstance(dr, dict):
        return dr

    dr = _deep_get(bundle, "metadata", "decisionRecord")
    if isinstance(dr, dict):
        return dr

    return {}


def _is_approved(value: Any) -> bool:
    return _norm(value) in YES_VALUES


def _decision_record_ok(bundle: dict[str, Any]) -> tuple[bool, str]:
    dr = _find_decision_record(bundle)
    if dr:
        responsible = dr.get("responsibleHuman")
        purpose = dr.get("declaredPurpose")
        approved = dr.get("approved")
        ok = bool(responsible and purpose and _is_approved(approved))
        if ok:
            return True, "DecisionRecord minimo encontrado com responsavel, finalidade e aprovacao."
        return False, "DecisionRecord encontrado, mas incompleto para fechamento conclusivo."

    compliance_statuses = _collect_gate_statuses(bundle, "complianceGate")
    if "PASS" in compliance_statuses:
        return True, "DecisionRecord minimo inferido por evidencia de complianceGate em PASS."
    if compliance_statuses:
        return False, "DecisionRecord minimo nao confirmado; complianceGate sem PASS."

    return False, "DecisionRecord minimo nao pode ser confirmado no bundle final."


def _traceability_ok(bundle: dict[str, Any]) -> tuple[bool, str, str]:
    status = _find_gate_status(bundle, "traceabilityCheck")

    if status == "PASS":
        return True, "HIGH", "TraceabilityCheck retornou PASS."
    if status == "WARN":
        return True, "MEDIUM", "TraceabilityCheck retornou WARN, com lastro parcial aceitavel."
    if status:
        return False, "MEDIUM", f"TraceabilityCheck retornou {status}."
    return False, "LOW", "TraceabilityCheck nao foi localizado no bundle."


def _compliance_ok(bundle: dict[str, Any]) -> tuple[bool, str]:
    status = _find_gate_status(bundle, "complianceGate")

    if status == "PASS":
        return True, "complianceGate retornou PASS."
    if status:
        return False, f"complianceGate retornou {status}."
    return False, "complianceGate nao foi localizado no bundle."


def _prescriptive_block(bundle: dict[str, Any]) -> tuple[bool, str]:
    status = _find_gate_status(bundle, "prescriptiveGate")

    if status in {"BLOCKED", "FAIL", "ERROR"}:
        return True, f"prescriptiveGate retornou {status}."
    if status:
        return False, f"prescriptiveGate retornou {status}."
    return False, "prescriptiveGate nao foi localizado no bundle."


def build_conclusion_report(bundle: dict[str, Any]) -> dict[str, Any]:
    decision_ok, decision_msg = _decision_record_ok(bundle)
    trace_ok, trace_conf, trace_msg = _traceability_ok(bundle)
    compliance_ok, compliance_msg = _compliance_ok(bundle)
    prescriptive_blocked, prescriptive_msg = _prescriptive_block(bundle)

    questions: list[ConclusionQuestion] = [
        ConclusionQuestion(
            id="Q1",
            question="Ha responsavel humano, finalidade declarada e aprovacao minima?",
            answer="SIM" if decision_ok else "INSUFICIENTE",
            confidence="HIGH" if decision_ok else "MEDIUM",
            rationale=decision_msg,
            evidence_refs=["decisionRecord", "gates.complianceGate"],
        ),
        ConclusionQuestion(
            id="Q2",
            question="Ha lastro minimo de rastreabilidade para sustentar fechamento conclusivo?",
            answer="SIM" if trace_ok else "INSUFICIENTE",
            confidence=trace_conf,
            rationale=trace_msg,
            evidence_refs=["gates.traceabilityCheck"],
        ),
        ConclusionQuestion(
            id="Q3",
            question="O conjunto passou pelo regime de compliance do TCRIA?",
            answer="SIM" if compliance_ok else "NAO",
            confidence="HIGH" if compliance_ok else "MEDIUM",
            rationale=compliance_msg,
            evidence_refs=["gates.complianceGate"],
        ),
        ConclusionQuestion(
            id="Q4",
            question="Ha impeditivo prescritivo ou condenatorio no fechamento final?",
            answer="SIM" if prescriptive_blocked else "NAO",
            confidence="HIGH",
            rationale=prescriptive_msg,
            evidence_refs=["gates.prescriptiveGate"],
        ),
    ]

    if compliance_ok and decision_ok and trace_ok and not prescriptive_blocked:
        overall_answer = "SIM"
        overall_confidence = "HIGH"
        summary = (
            "O bundle final sustenta fechamento conclusivo positivo: ha accountability minima, "
            "lastro de rastreabilidade e passagem pelo compliance sem impeditivo prescritivo."
        )
    elif prescriptive_blocked:
        overall_answer = "NAO"
        overall_confidence = "HIGH"
        summary = (
            "O bundle foi processado, mas o fechamento conclusivo final e negativo porque existe "
            "impeditivo prescritivo/condenatorio sinalizado pelo pipeline."
        )
    else:
        overall_answer = "INSUFICIENTE"
        overall_confidence = "MEDIUM"
        summary = (
            "O bundle foi processado ate o fim, mas os elementos disponiveis nao sustentam "
            "fechamento conclusivo forte. O resultado permanece insuficiente, sem travar o fluxo."
        )

    report = ConclusionReport(
        overall_answer=overall_answer,
        overall_confidence=overall_confidence,
        summary=summary,
        questions=questions,
    )
    return asdict(report)


def render_final_conclusions_md(conclusions: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("## Final Conclusions")
    lines.append("")
    lines.append(f"**Overall answer:** {conclusions.get('overall_answer', 'INSUFICIENTE')}")
    lines.append(f"**Overall confidence:** {conclusions.get('overall_confidence', 'LOW')}")
    lines.append("")
    lines.append(str(conclusions.get("summary", "")))
    lines.append("")

    for q in conclusions.get("questions", []):
        lines.append(f"### {q.get('id', '')} - {q.get('question', '')}")
        lines.append(f"- Answer: {q.get('answer', 'INSUFICIENTE')}")
        lines.append(f"- Confidence: {q.get('confidence', 'LOW')}")
        lines.append(f"- Rationale: {q.get('rationale', '')}")
        refs = q.get("evidence_refs", [])
        if refs:
            lines.append(f"- Evidence refs: {', '.join(refs)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
