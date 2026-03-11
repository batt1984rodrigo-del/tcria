from __future__ import annotations

from tcria.classification.interpretation import interpret_document
from tcria.models import Document


HIGH_SEVERITY_ACCUSATION_KEYWORDS = (
    "fraude",
    "golpe",
    "acusação",
    "acusacao",
    "denúncia",
    "denuncia",
    "não autorizado",
    "nao autorizado",
)

LOW_SEVERITY_LEGAL_DISPUTE_TERMS = (
    "ressarcimento",
    "prejuízo",
    "prejuizo",
    "indevido",
)

ADMINISTRATIVE_FILE_MARKERS = (
    "recibo_eletronico_de_protocolo",
    "despacho",
    "oficio",
    "ofício",
    "certidao",
    "certidão",
    "comprovante",
    "contrato_social",
    "identidade",
    "inscricao_estadual",
    "divida_ativa",
    "dívida_ativa",
    "processo",
    "danfe",
    "nota_fiscal",
    "planilha",
    "peticao",
    "prorrogacao",
    "prorrogação",
)


def _count_hits(text_l: str, keywords: tuple[str, ...]) -> int:
    return sum(text_l.count(keyword) for keyword in keywords)


def classify_artifact(document: Document, signals: dict[str, object]) -> tuple[str, bool, list[str], dict[str, object]]:
    if document.extraction_status == "unsupported":
        return "UNSUPPORTED", False, ["Unsupported file type."], {}
    if document.extraction_status != "ok":
        return "UNREADABLE", False, [f"Text extraction status: {document.extraction_status}."], {}
    if not document.text.strip():
        return "UNREADABLE_OR_EMPTY", False, ["No extractable content."], {}

    interpretation = interpret_document(document, signals)
    text_l = document.text.lower()
    high_severity_hits = _count_hits(text_l, HIGH_SEVERITY_ACCUSATION_KEYWORDS)
    low_severity_hits = _count_hits(text_l, LOW_SEVERITY_LEGAL_DISPUTE_TERMS)
    target_hits = sum((signals.get("target_entity_hits") or {}).values())
    evidence_hits = sum((signals.get("evidence_marker_hits") or {}).values())
    admin_hits = sum((signals.get("administrative_fiscal_marker_hits") or {}).values())
    restitution_hits = sum((signals.get("restitution_request_hits") or {}).values())
    legal_basis_hits = sum((signals.get("legal_basis_marker_hits") or {}).values())
    accountability_support_hits = sum((signals.get("accountability_support_hits") or {}).values())
    administrative_charge_hits = sum((signals.get("administrative_charge_hits") or {}).values())
    suspension_hits = sum((signals.get("icms_suspension_marker_hits") or {}).values())
    request_hits = sum((signals.get("request_argument_hits") or {}).values())
    investigative_hits = sum((signals.get("investigative_marker_hits") or {}).values())

    name_l = f"{document.path.name} {document.relative_path}".lower()
    admin_file_context = any(marker in name_l for marker in ADMINISTRATIVE_FILE_MARKERS)
    administrative_context = admin_hits >= 2 or admin_file_context

    route = ((interpretation.get("route_selection") or {}).get("selected_route")) or "UNDETERMINED"
    route_confidence = ((interpretation.get("route_selection") or {}).get("confidence")) or "LOW"
    role = ((interpretation.get("document_role") or {}).get("value")) or "UNDETERMINED"
    posture = ((interpretation.get("discursive_posture") or {}).get("value")) or "NEUTRAL_OR_UNCLEAR"
    expectation = interpretation.get("support_expectation") or {}
    imputation = interpretation.get("imputation_profile") or {}
    has_material_imputation = bool(imputation.get("has_material_imputation"))

    base_reasons = [
        f"Audit route={route} ({route_confidence})",
        f"Document role={role}",
        f"Discursive posture={posture}",
    ]

    if route == "ADMINISTRATIVE_RESTITUTION_ACCOUNTABILITY":
        if role in {"PROCEDURAL_REQUEST", "ARGUMENTATIVE_FILING", "DECISION_OR_OPINION"} and restitution_hits > 0:
            if expectation.get("legal_basis_expected") and legal_basis_hits == 0:
                return "ACCUSATORY_CANDIDATE", True, base_reasons + [
                    f"Restitution request markers={restitution_hits}",
                    "Legal basis markers=0",
                    f"Accountability support markers={accountability_support_hits}",
                    "This route treats unsupported entitlement requests as imputative against public-administration entitlement rules.",
                ], interpretation
            if expectation.get("factual_support_expected") and accountability_support_hits == 0 and evidence_hits == 0:
                return "ACCUSATORY_CANDIDATE", True, base_reasons + [
                    f"Restitution request markers={restitution_hits}",
                    f"Legal basis markers={legal_basis_hits}",
                    "Accountability support markers=0",
                    "The request advances entitlement without minimum calculation or documentary support markers.",
                ], interpretation
            return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                f"Restitution request markers={restitution_hits}",
                f"Legal basis markers={legal_basis_hits}",
                f"Accountability support markers={accountability_support_hits}",
            ], interpretation

        if role in {"SUPPORTING_PROOF", "CALCULATION_SHEET", "IDENTIFICATION_OR_AUTHORIZATION"}:
            return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                "Document role is evidentiary or traceability support inside a restitution route.",
                f"Evidence markers={evidence_hits}",
                f"Accountability support markers={accountability_support_hits}",
            ], interpretation

    if route == "ADMINISTRATIVE_ICMS_SUSPENSION":
        if role in {"PROCEDURAL_REQUEST", "ARGUMENTATIVE_FILING"} and request_hits > 0:
            if expectation.get("legal_basis_expected") and legal_basis_hits == 0 and suspension_hits > 0:
                return "ACCUSATORY_CANDIDATE", True, base_reasons + [
                    f"Suspension-extension markers={suspension_hits}",
                    "Legal basis markers=0",
                    "The request appears route-specific but does not expose the normative basis expected for this filing role.",
                ], interpretation
            if expectation.get("factual_support_expected") and evidence_hits == 0 and accountability_support_hits == 0:
                return "ACCUSATORY_CANDIDATE", True, base_reasons + [
                    f"Suspension-extension markers={suspension_hits}",
                    "Support markers=0",
                    "The request appears route-specific but lacks minimum documentary support markers.",
                ], interpretation
            return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                f"Suspension-extension markers={suspension_hits}",
                f"Legal basis markers={legal_basis_hits}",
                f"Evidence markers={evidence_hits}",
            ], interpretation

        if role in {"SUPPORTING_PROOF", "CALCULATION_SHEET", "ADMINISTRATIVE_ROUTING", "IDENTIFICATION_OR_AUTHORIZATION"}:
            if evidence_hits > 0 or accountability_support_hits > 0 or administrative_context:
                return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                    "Document supports an ICMS suspension-extension route without independently carrying the claim burden.",
                    f"Evidence markers={evidence_hits}",
                    f"Administrative/fiscal context markers={admin_hits}",
                ], interpretation

    if route == "CIVIL_CRIMINAL_INVESTIGATIVE":
        if (high_severity_hits >= 1 or investigative_hits > 0) and (target_hits > 0 or evidence_hits > 0 or has_material_imputation):
            return "ACCUSATORY_CANDIDATE", True, base_reasons + [
                f"High-severity accusation terms={high_severity_hits}",
                f"Investigative markers={investigative_hits}",
                f"Target entity hits={target_hits}",
                f"Evidence markers={evidence_hits}",
            ], interpretation
        if evidence_hits > 0 or target_hits > 0:
            return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                f"Target entity hits={target_hits}",
                f"Evidence markers={evidence_hits}",
            ], interpretation

    if has_material_imputation and administrative_charge_hits > 0 and role in {"PROCEDURAL_REQUEST", "ARGUMENTATIVE_FILING", "DECISION_OR_OPINION"}:
        return "ACCUSATORY_CANDIDATE", True, base_reasons + [
            f"Administrative charge markers={administrative_charge_hits}",
            "The document carries a material contestation or exclusionary assertion within its selected route.",
        ], interpretation

    if low_severity_hits > 0 and administrative_context and high_severity_hits == 0 and route != "CIVIL_CRIMINAL_INVESTIGATIVE":
        if evidence_hits > 0 or target_hits > 0 or accountability_support_hits > 0:
            return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
                f"Administrative/fiscal context markers={admin_hits}",
                f"Weak dispute terms suppressed={low_severity_hits}",
                f"Target entity hits={target_hits}",
                f"Evidence/support markers={evidence_hits + accountability_support_hits}",
            ], interpretation
        return "NEUTRAL_OR_CONTEXT", False, base_reasons + [
            f"Administrative/fiscal context markers={admin_hits}",
            f"Weak dispute terms suppressed={low_severity_hits}",
        ], interpretation

    if role in {"SUPPORTING_PROOF", "CALCULATION_SHEET", "IDENTIFICATION_OR_AUTHORIZATION"} and (
        evidence_hits > 0 or accountability_support_hits > 0 or administrative_context
    ):
        return "SUPPORTING_EVIDENCE_RELEVANT", False, base_reasons + [
            f"Evidence markers={evidence_hits}",
            f"Accountability support markers={accountability_support_hits}",
            f"Administrative/fiscal context markers={admin_hits}",
        ], interpretation

    if role == "ADMINISTRATIVE_ROUTING":
        return "NEUTRAL_OR_CONTEXT", False, base_reasons + [
            "Document role is administrative routing/traceability rather than a claim-bearing artifact.",
            f"Administrative/fiscal context markers={admin_hits}",
        ], interpretation

    if document.suffix == ".csv":
        return "SUPPORTING_EVIDENCE", False, base_reasons + ["Tabular dataset treated as supporting evidence."], interpretation

    return "NEUTRAL_OR_CONTEXT", False, base_reasons + ["No route-specific accusatory threshold was satisfied."], interpretation


def infer_artifact_type(document: Document) -> tuple[str, str]:
    name_l = document.path.name.lower()
    if any(k in name_l for k in ("dossie", "dossiê", "timeline", "sumario", "sumário", "relatorio", "relatório", "analise", "análise")):
        return "ANALYTICAL_ARTIFACT", "Filename matches analytical markers."
    if any(k in name_l for k in ("recibo", "despacho", "oficio", "ofício", "certidao", "certidão", "comprovante")):
        return "ADMINISTRATIVE_RECORD", "Filename matches administrative process records."
    if any(k in name_l for k in ("anexo", "danfe", "planilha", "nota")):
        return "FISCAL_SUPPORT_RECORD", "Filename matches fiscal support records."
    if any(k in name_l for k in ("contrato_social", "identidade", "procuracao", "procuração")):
        return "AUTHORIZATION_OR_REGISTRY_RECORD", "Filename matches authorization or registry records."
    if any(k in name_l for k in ("peticao", "petição", "recurso", "pedido", "manifestacao", "manifestação")):
        return "PROCEDURAL_FILING", "Filename matches procedural filing markers."
    return "DECISION_ARTIFACT", "Fallback artifact typing."
