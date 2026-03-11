from __future__ import annotations

from dataclasses import asdict, dataclass

from tcria.models import Document


REQUEST_ARGUMENT_MARKERS = (
    "requer",
    "requerimento",
    "requer a",
    "requer o",
    "solicita",
    "solicitação",
    "solicitacao",
    "pedido",
    "pleiteia",
    "postula",
    "pretende",
    "prorrogação",
    "prorrogacao",
    "restituição",
    "restituicao",
    "indébito",
    "indebito",
)

DEFENSIVE_ARGUMENT_MARKERS = (
    "defesa",
    "contestação",
    "contestacao",
    "impugna",
    "impugnação",
    "impugnacao",
    "justifica",
    "esclarece",
    "rebate",
)

CERTIFYING_MARKERS = (
    "certifico",
    "certidão",
    "certidao",
    "atesto",
    "comprovante",
    "recibo",
    "identidade",
    "procuração",
    "procuracao",
    "contrato social",
    "cadastro nacional da pessoa jurídica",
    "cnpj",
)

ROUTING_MARKERS = (
    "encaminhamento",
    "encaminho",
    "remessa",
    "protocolo",
    "trâmite",
    "tramite",
    "despacho",
    "ofício",
    "oficio",
    "recebimento",
)

DECISION_MARKERS = (
    "defiro",
    "indefiro",
    "decido",
    "decisão",
    "decisao",
    "parecer",
    "acórdão",
    "acordao",
    "voto",
    "julgo",
    "conclusão",
    "conclusao",
)

CALCULATION_MARKERS = (
    "planilha",
    "memória de cálculo",
    "memoria de calculo",
    "mapa de restituição",
    "mapa de restituicao",
    "base de cálculo",
    "base de calculo",
    "valor total",
    "cfop",
)

INVESTIGATIVE_MARKERS = (
    "investigação",
    "investigacao",
    "apuração",
    "apuracao",
    "indício",
    "indicio",
    "evidência",
    "evidencia",
    "responsabilização",
    "responsabilizacao",
)

ADMINISTRATIVE_CHARGE_MARKERS = (
    "não faz jus",
    "nao faz jus",
    "sem direito",
    "sem amparo legal",
    "ausência de comprovação",
    "ausencia de comprovacao",
    "não comprovado",
    "nao comprovado",
    "irregularidade",
    "intempestivo",
    "intempestiva",
    "indevido",
    "não autorizado",
    "nao autorizado",
)

SUSPENSION_EXTENSION_MARKERS = (
    "suspensão do icms",
    "suspensao do icms",
    "prorrogação do prazo",
    "prorrogacao do prazo",
    "reparo",
    "conserto",
    "industrialização",
    "industrializacao",
    "nota fiscal",
    "danfe",
    "chave de acesso",
    "art. 52",
    "art 52",
)


def _count_hits(text_l: str, keywords: tuple[str, ...]) -> int:
    return sum(text_l.count(keyword) for keyword in keywords)


def _score_to_confidence(score: int) -> str:
    if score >= 6:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def _route_confidence(selected_score: int, runner_up_score: int) -> str:
    margin = selected_score - runner_up_score
    if selected_score >= 6 and margin >= 2:
        return "HIGH"
    if selected_score >= 3 and margin >= 1:
        return "MEDIUM"
    return "LOW"


@dataclass(frozen=True)
class RouteHypothesis:
    route: str
    score: int
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def interpret_document(document: Document, signals: dict[str, object]) -> dict[str, object]:
    text_l = document.text.lower()
    name_l = f"{document.path.name} {document.relative_path}".lower()

    request_hits = _count_hits(text_l, REQUEST_ARGUMENT_MARKERS)
    defensive_hits = _count_hits(text_l, DEFENSIVE_ARGUMENT_MARKERS)
    certifying_hits = _count_hits(text_l, CERTIFYING_MARKERS)
    routing_hits = _count_hits(text_l, ROUTING_MARKERS)
    decision_hits = _count_hits(text_l, DECISION_MARKERS)
    calculation_hits = _count_hits(text_l, CALCULATION_MARKERS)
    investigative_hits = _count_hits(text_l, INVESTIGATIVE_MARKERS)
    admin_charge_hits = _count_hits(text_l, ADMINISTRATIVE_CHARGE_MARKERS)
    suspension_hits = _count_hits(text_l, SUSPENSION_EXTENSION_MARKERS)

    restitution_hits = sum((signals.get("restitution_request_hits") or {}).values())
    legal_basis_hits = sum((signals.get("legal_basis_marker_hits") or {}).values())
    evidence_hits = sum((signals.get("evidence_marker_hits") or {}).values())
    admin_hits = sum((signals.get("administrative_fiscal_marker_hits") or {}).values())
    target_hits = sum((signals.get("target_entity_hits") or {}).values())
    accusation_hits = sum((signals.get("accusation_keyword_hits") or {}).values())
    support_hits = sum((signals.get("accountability_support_hits") or {}).values())

    role_scores = {
        "PROCEDURAL_REQUEST": request_hits * 2 + restitution_hits + int("petição" in name_l or "peticao" in name_l or "pedido" in name_l),
        "ARGUMENTATIVE_FILING": request_hits + defensive_hits + legal_basis_hits + decision_hits,
        "SUPPORTING_PROOF": evidence_hits + support_hits + int("anexo" in name_l or "comprovante" in name_l or "danfe" in name_l),
        "IDENTIFICATION_OR_AUTHORIZATION": certifying_hits + int("identidade" in name_l or "procur" in name_l or "contrato_social" in name_l),
        "ADMINISTRATIVE_ROUTING": routing_hits * 2 + admin_hits + int("despacho" in name_l or "oficio" in name_l or "ofício" in name_l or "recibo" in name_l),
        "CALCULATION_SHEET": calculation_hits * 2 + support_hits + int("planilha" in name_l or "mapa" in name_l),
        "DECISION_OR_OPINION": decision_hits * 2 + legal_basis_hits + int("parecer" in name_l or "decis" in name_l),
        "ANALYTICAL_SUMMARY": investigative_hits + int("relatorio" in name_l or "relatório" in name_l or "timeline" in name_l or "dossie" in name_l or "dossiê" in name_l),
    }
    role, role_score = max(role_scores.items(), key=lambda item: item[1])
    role_reasons = [
        f"request_hits={request_hits}",
        f"routing_hits={routing_hits}",
        f"certifying_hits={certifying_hits}",
        f"decision_hits={decision_hits}",
        f"calculation_hits={calculation_hits}",
        f"evidence_hits={evidence_hits}",
    ]
    if role_score <= 1:
        role = "UNDETERMINED"

    posture_scores = {
        "REQUESTIVE": request_hits + restitution_hits,
        "DEFENSIVE": defensive_hits,
        "ACCUSATORY": accusation_hits + admin_charge_hits + investigative_hits + target_hits,
        "JUSTIFICATORY": legal_basis_hits + support_hits,
        "CERTIFYING": certifying_hits + support_hits,
        "ROUTING": routing_hits,
        "DECISIONAL": decision_hits,
        "ANALYTICAL": investigative_hits + calculation_hits,
    }
    posture, posture_score = max(posture_scores.items(), key=lambda item: item[1])
    if posture_score == 0:
        posture = "NEUTRAL_OR_UNCLEAR"
    posture_reasons = [
        "Discursive posture is inferential and never treated as objective fact.",
        f"request_hits={request_hits}",
        f"defensive_hits={defensive_hits}",
        f"accusation_hits={accusation_hits}",
        f"administrative_charge_hits={admin_charge_hits}",
        f"legal_basis_hits={legal_basis_hits}",
    ]

    tone_scores = {
        "FORMAL_ASSERTIVE": request_hits + legal_basis_hits,
        "CONTESTING": defensive_hits + admin_charge_hits,
        "CERTIFYING": certifying_hits + routing_hits,
        "ANALYTICAL": calculation_hits + investigative_hits,
    }
    tone, tone_score = max(tone_scores.items(), key=lambda item: item[1])
    if tone_score == 0:
        tone = "INDETERMINATE"

    route_hypotheses = [
        RouteHypothesis(
            route="ADMINISTRATIVE_RESTITUTION_ACCOUNTABILITY",
            score=restitution_hits * 3 + legal_basis_hits * 2 + support_hits + admin_hits,
            reasons=[
                f"restitution_hits={restitution_hits}",
                f"legal_basis_hits={legal_basis_hits}",
                f"support_hits={support_hits}",
                f"admin_hits={admin_hits}",
            ],
        ),
        RouteHypothesis(
            route="ADMINISTRATIVE_ICMS_SUSPENSION",
            score=suspension_hits * 3 + admin_hits * 2 + support_hits,
            reasons=[
                f"suspension_hits={suspension_hits}",
                f"admin_hits={admin_hits}",
                f"support_hits={support_hits}",
            ],
        ),
        RouteHypothesis(
            route="CIVIL_CRIMINAL_INVESTIGATIVE",
            score=accusation_hits * 3 + investigative_hits * 2 + target_hits + evidence_hits,
            reasons=[
                f"accusation_hits={accusation_hits}",
                f"investigative_hits={investigative_hits}",
                f"target_hits={target_hits}",
                f"evidence_hits={evidence_hits}",
            ],
        ),
        RouteHypothesis(
            route="ADMINISTRATIVE_FISCAL_GENERAL",
            score=admin_hits * 2 + routing_hits + certifying_hits + support_hits,
            reasons=[
                f"admin_hits={admin_hits}",
                f"routing_hits={routing_hits}",
                f"certifying_hits={certifying_hits}",
                f"support_hits={support_hits}",
            ],
        ),
        RouteHypothesis(
            route="EVIDENTIARY_SUPPORT_GENERAL",
            score=evidence_hits * 2 + support_hits * 2 + calculation_hits + certifying_hits,
            reasons=[
                f"evidence_hits={evidence_hits}",
                f"support_hits={support_hits}",
                f"calculation_hits={calculation_hits}",
                f"certifying_hits={certifying_hits}",
            ],
        ),
    ]
    route_hypotheses.sort(key=lambda item: item.score, reverse=True)
    selected_route = route_hypotheses[0]
    runner_up = route_hypotheses[1]
    route_confidence = _route_confidence(selected_route.score, runner_up.score)
    if selected_route.score <= 1:
        selected_route = RouteHypothesis(
            route="UNDETERMINED",
            score=selected_route.score,
            reasons=["No semantic route achieved enough structured support."],
        )
        route_confidence = "LOW"

    legal_basis_expected = role in {"PROCEDURAL_REQUEST", "ARGUMENTATIVE_FILING", "DECISION_OR_OPINION"} and selected_route.route in {
        "ADMINISTRATIVE_RESTITUTION_ACCOUNTABILITY",
        "ADMINISTRATIVE_ICMS_SUSPENSION",
        "CIVIL_CRIMINAL_INVESTIGATIVE",
    }
    factual_support_expected = role in {
        "PROCEDURAL_REQUEST",
        "ARGUMENTATIVE_FILING",
        "SUPPORTING_PROOF",
        "CALCULATION_SHEET",
        "DECISION_OR_OPINION",
    }
    traceability_expected = role in {
        "SUPPORTING_PROOF",
        "IDENTIFICATION_OR_AUTHORIZATION",
        "ADMINISTRATIVE_ROUTING",
        "CALCULATION_SHEET",
    }
    expectation_reasons = []
    if legal_basis_expected:
        expectation_reasons.append("This role normally carries thesis, request, or decisional grounding.")
    if factual_support_expected:
        expectation_reasons.append("This role should connect to factual or documentary support within its route.")
    if traceability_expected:
        expectation_reasons.append("This role is expected to preserve process traceability or documentary provenance.")
    if not expectation_reasons:
        expectation_reasons.append("No strong route-specific expectation could be imposed safely.")

    imputation_target = "NONE"
    imputation_reasons = []
    has_material_imputation = False
    if accusation_hits > 0 or admin_charge_hits > 0:
        has_material_imputation = True
        if selected_route.route.startswith("ADMINISTRATIVE_") and posture in {"REQUESTIVE", "JUSTIFICATORY"}:
            imputation_target = "PUBLIC_ADMINISTRATION_OR_TAX_ENTITLEMENT"
            imputation_reasons.append("The text appears to advance or defend an entitlement before the public administration.")
        elif target_hits > 0 or selected_route.route == "CIVIL_CRIMINAL_INVESTIGATIVE":
            imputation_target = "THIRD_PARTY_OR_IDENTIFIED_TARGET"
            imputation_reasons.append("The text contains accusatory/investigative cues tied to a target or dispute context.")
        else:
            imputation_target = "DOCUMENT_INTERNAL_ASSERTION"
            imputation_reasons.append("The text carries contesting or exclusionary assertions without a stable target.")
    else:
        imputation_reasons.append("No material imputation cue passed the minimum threshold.")

    comparative_reasons = [
        f"Selected route {selected_route.route} scored {selected_route.score}; runner-up {runner_up.route} scored {runner_up.score}.",
        "Route selection is based on structured comparison of competing semantic hypotheses.",
    ]
    comparative_reasons.extend(selected_route.reasons)

    return {
        "document_role": {
            "value": role,
            "confidence": _score_to_confidence(role_score),
            "reasons": role_reasons,
        },
        "discursive_posture": {
            "value": posture,
            "confidence": _score_to_confidence(posture_score),
            "reasons": posture_reasons,
        },
        "rhetorical_tone": {
            "value": tone,
            "confidence": _score_to_confidence(tone_score),
            "reasons": [
                "Rhetorical tone is an interpretive aid only and never an objective factual conclusion.",
                f"tone_score={tone_score}",
            ],
        },
        "route_selection": {
            "selected_route": selected_route.route,
            "confidence": route_confidence,
            "reasons": comparative_reasons,
            "runner_up_route": runner_up.route,
            "runner_up_score": runner_up.score,
            "hypotheses": [hypothesis.to_dict() for hypothesis in route_hypotheses],
        },
        "support_expectation": {
            "legal_basis_expected": legal_basis_expected,
            "factual_support_expected": factual_support_expected,
            "traceability_expected": traceability_expected,
            "reasons": expectation_reasons,
        },
        "imputation_profile": {
            "has_material_imputation": has_material_imputation,
            "target": imputation_target,
            "reasons": imputation_reasons,
        },
    }
