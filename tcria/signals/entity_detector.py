from __future__ import annotations

import re


EVIDENCE_MARKERS = (
    "prova",
    "provas",
    "comprovante",
    "comprovantes",
    "fatura",
    "faturas",
    "extrato",
    "extratos",
    "timeline",
    "linha do tempo",
    "anexo",
    "anexos",
)

ADMINISTRATIVE_FISCAL_MARKERS = (
    "secretaria de estado de fazenda",
    "secretaria de fazenda",
    "subsecretaria de estado de receita",
    "sefaz",
    "inscrição estadual",
    "inscricao estadual",
    "restituição de indébito",
    "restituicao de indebito",
    "dívida ativa",
    "divida ativa",
    "icms",
    "processo administrativo",
    "recibo eletrônico de protocolo",
    "recibo eletronico de protocolo",
    "despacho",
    "ofício",
    "oficio",
    "certidão",
    "certidao",
    "regularidade fiscal",
    "procuradoria geral do estado",
    "pge",
    "ricms",
    "ricms/rj",
    "decreto nº27.427/2000",
    "decreto no27.427/2000",
    "decreto 27.427/2000",
    "decreto nº 27.427/2000",
    "decreto 48.209",
    "prorrogação do prazo",
    "prorrogacao do prazo",
    "suspensão do icms",
    "suspensao do icms",
    "nota fiscal",
    "danfe",
    "chave de acesso",
    "reparo",
    "conserto",
    "industrialização",
    "industrializacao",
    "cfop",
    "art. 52",
    "art 52",
)

RESTITUTION_REQUEST_MARKERS = (
    "pedido de restituição",
    "pedido de restituicao",
    "solicitação de restituição de indébito",
    "solicitacao de restituicao de indebito",
    "restituição de indébito",
    "restituicao de indebito",
    "repetição de indébito",
    "repeticao de indebito",
    "restituição",
    "restituicao",
    "ressarcimento",
    "icms st",
    "icms/st",
    "difal",
)

LEGAL_BASIS_MARKERS = (
    "lei nº 2.657/1996",
    "lei n° 2.657/1996",
    "lei no 2.657/1996",
    "lei do icms/rj",
    "art. 27",
    "art. 17",
    "art. 18",
    "art. 19",
    "livro ii",
    "ricms",
    "resolução sefaz",
    "resolucao sefaz",
    "tratamento tributário especial",
    "tratamento tributario especial",
    "mandado de segurança",
    "mandado de seguranca",
    "acórdão",
    "acordao",
    "trânsito em julgado",
    "transito em julgado",
    "parecer",
)

ACCOUNTABILITY_SUPPORT_MARKERS = (
    "memória de cálculo",
    "memoria de calculo",
    "planilha",
    "base restituição",
    "base restituicao",
    "comprovante de recolhimento",
    "comprovantes de recolhimento",
    "guia de recolhimento",
    "guias de recolhimento",
    "comprovante de pagamento",
    "comprovação dos dados bancários",
    "comprovacao dos dados bancarios",
    "procuração",
    "procuracao",
    "crédito atualizado",
    "credito atualizado",
    "mapa_restituição",
    "mapa_restituicao",
)

REQUEST_ARGUMENT_MARKERS = (
    "requer",
    "requerimento",
    "solicita",
    "solicitação",
    "solicitacao",
    "pedido",
    "pleiteia",
    "postula",
    "prorrogação",
    "prorrogacao",
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
)

CALCULATION_MARKERS = (
    "planilha",
    "memória de cálculo",
    "memoria de calculo",
    "mapa de restituição",
    "mapa de restituicao",
    "base de cálculo",
    "base de calculo",
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
)

ICMS_SUSPENSION_MARKERS = (
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

TARGET_ENTITIES = (
    "bradesco",
    "vinícius",
    "vinicius",
    "rodrigo baptista",
    "banco",
)

ACCUSATION_TERMS = (
    "fraude",
    "golpe",
    "acusação",
    "acusacao",
    "denúncia",
    "denuncia",
    "ressarcimento",
    "prejuízo",
    "prejuizo",
    "não autorizado",
    "nao autorizado",
)


def _count_hits(text_l: str, terms: tuple[str, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for term in terms:
        hits = text_l.count(term)
        if hits > 0:
            out[term] = hits
    return out


def detect_entity_signals(text: str) -> dict[str, object]:
    text_l = text.lower()
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return {
        "pix_mentions": text_l.count("pix"),
        "email_mentions": len(emails),
        "accusation_keyword_hits": _count_hits(text_l, ACCUSATION_TERMS),
        "evidence_marker_hits": _count_hits(text_l, EVIDENCE_MARKERS),
        "administrative_fiscal_marker_hits": _count_hits(text_l, ADMINISTRATIVE_FISCAL_MARKERS),
        "restitution_request_hits": _count_hits(text_l, RESTITUTION_REQUEST_MARKERS),
        "legal_basis_marker_hits": _count_hits(text_l, LEGAL_BASIS_MARKERS),
        "accountability_support_hits": _count_hits(text_l, ACCOUNTABILITY_SUPPORT_MARKERS),
        "request_argument_hits": _count_hits(text_l, REQUEST_ARGUMENT_MARKERS),
        "defensive_argument_hits": _count_hits(text_l, DEFENSIVE_ARGUMENT_MARKERS),
        "certifying_marker_hits": _count_hits(text_l, CERTIFYING_MARKERS),
        "routing_marker_hits": _count_hits(text_l, ROUTING_MARKERS),
        "decision_marker_hits": _count_hits(text_l, DECISION_MARKERS),
        "calculation_marker_hits": _count_hits(text_l, CALCULATION_MARKERS),
        "investigative_marker_hits": _count_hits(text_l, INVESTIGATIVE_MARKERS),
        "administrative_charge_hits": _count_hits(text_l, ADMINISTRATIVE_CHARGE_MARKERS),
        "icms_suspension_marker_hits": _count_hits(text_l, ICMS_SUSPENSION_MARKERS),
        "target_entity_hits": _count_hits(text_l, TARGET_ENTITIES),
    }
