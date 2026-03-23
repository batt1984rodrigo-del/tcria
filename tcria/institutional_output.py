from __future__ import annotations

from typing import Any


KNOWN_ACTIONS = {
    "juntada",
    "remessa",
    "exigencia",
    "apensamento",
    "sobrestamento",
    "indeferimento",
    "deferimento",
    "arquivamento",
    "encaminhamento",
}

ACTION_LABELS = {
    "juntada": "juntada/vinculação",
    "remessa": "remessa",
    "exigencia": "exigência",
    "apensamento": "apensamento",
    "sobrestamento": "sobrestamento",
    "indeferimento": "indeferimento",
    "deferimento": "deferimento",
    "arquivamento": "arquivamento",
    "encaminhamento": "encaminhamento",
}


def _clean_text(value: Any, *, default: str = "Não informado.") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _clean_list(items: Any) -> list[str]:
    if not items:
        return []
    iterable = items if isinstance(items, (list, tuple, set)) else [items]
    cleaned: list[str] = []
    for item in iterable:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _compact_dict(values: dict[str, Any]) -> str:
    if not values:
        return "Não identificado nos autos auditados."
    parts = [f"{key}: {value}" for key, value in sorted(values.items()) if value]
    return "; ".join(parts) if parts else "Não identificado nos autos auditados."


def _normalize_action(value: Any) -> str | None:
    if value is None:
        return None
    text = (
        str(value)
        .strip()
        .lower()
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("ê", "e")
    )
    aliases = {
        "exigencia": "exigencia",
        "exigência": "exigencia",
        "saneamento": "exigencia",
        "vinculacao": "juntada",
        "vinculação": "juntada",
        "encaminhamento": "encaminhamento",
    }
    normalized = aliases.get(text, text)
    return normalized if normalized in KNOWN_ACTIONS else None


def infer_recommended_action(audit_data: dict[str, Any]) -> str:
    explicit = _normalize_action(audit_data.get("recommended_action"))
    if explicit:
        return explicit

    process_type = _clean_text(audit_data.get("process_type"), default="").lower()
    documents_missing = _clean_list(audit_data.get("documents_missing"))
    inconsistencies = _clean_list(audit_data.get("inconsistencies"))
    specialized_unit = _clean_text(audit_data.get("specialized_unit"), default="")
    depends_on_main = bool(audit_data.get("depends_on_main_process"))

    if process_type == "intercorrente" and depends_on_main:
        return "juntada"
    if depends_on_main and not documents_missing and not inconsistencies:
        return "sobrestamento"
    if specialized_unit and (documents_missing or inconsistencies):
        return "remessa"
    if documents_missing:
        return "exigencia"
    if inconsistencies:
        return "encaminhamento"
    return "encaminhamento"


def _sentence(prefix: str, value: str) -> str:
    value = value.strip().rstrip(".")
    return f"{prefix} {value}."


def _classify_issue(audit_data: dict[str, Any], action: str) -> dict[str, str]:
    documents_missing = _clean_list(audit_data.get("documents_missing"))
    inconsistencies = _clean_list(audit_data.get("inconsistencies"))
    depends_on_main = bool(audit_data.get("depends_on_main_process"))
    specialized_unit = _clean_text(audit_data.get("specialized_unit"), default="")

    if depends_on_main:
        nature = "vício sanável com dependência de autos principais"
        maturity = "providência intermediária"
    elif documents_missing:
        nature = "insuficiência de instrução documental sanável"
        maturity = "providência intermediária"
    elif inconsistencies:
        nature = "inconsistência material ou cadastral ainda saneável"
        maturity = "providência intermediária"
    elif action in {"indeferimento", "deferimento", "arquivamento"}:
        nature = "instrução apta a desfecho"
        maturity = "despacho final"
    else:
        nature = "instrução incompleta para fechamento conclusivo"
        maturity = "providência intermediária"

    return {
        "natureza_do_vicio": nature,
        "nivel_de_maturidade_decisoria": maturity,
        "ha_unidade_especializada": "sim" if specialized_unit and specialized_unit != "Não indicada." else "não",
        "depende_de_processo_principal": "sim" if depends_on_main else "não",
        "ato_recomendado": ACTION_LABELS[action],
    }


def _build_conclusion(action: str, *, specialized_unit: str) -> str:
    conclusions = {
        "juntada": "Recomenda-se a juntada ou vinculação ao processo principal, preservando-se a apreciação de mérito nos autos de referência.",
        "remessa": f"Recomenda-se a remessa dos autos à unidade competente ({specialized_unit}) para análise temática e saneamento do que foi apontado.",
        "exigencia": "Recomenda-se a expedição de exigência para saneamento das lacunas documentais antes de qualquer apreciação conclusiva.",
        "apensamento": "Recomenda-se o apensamento dos autos correlatos para instrução conjunta e racionalização do fluxo processual.",
        "sobrestamento": "Recomenda-se o sobrestamento do feito até a superação da dependência processual expressamente identificada.",
        "indeferimento": "Estando completa a instrução e ausente suporte mínimo para acolhimento, recomenda-se o indeferimento do pedido.",
        "deferimento": "Estando observados os requisitos mínimos informados, recomenda-se o deferimento do pedido, com os registros de praxe.",
        "arquivamento": "Não subsistindo providência útil imediata, recomenda-se o arquivamento dos autos, com as anotações cabíveis.",
        "encaminhamento": "Não há elementos suficientes para despacho final de mérito. Recomenda-se o encaminhamento dos autos para análise técnica e saneamento do que foi apontado.",
    }
    return conclusions[action]


def _build_minuta(action: str, *, process_number: str, subject: str, specialized_unit: str) -> str:
    normalized_subject = subject.strip().rstrip(".").lower()
    templates = {
        "juntada": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Considerando a natureza intercorrente do expediente e a dependência de apreciação nos autos principais, "
            "junte-se o presente expediente ao processo de referência, com a devida vinculação."
        ),
        "remessa": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            f"Considerando a especialidade da matéria e a necessidade de análise técnica própria, encaminhem-se os autos à {specialized_unit}."
        ),
        "exigencia": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Verifica-se insuficiência de instrução documental para apreciação conclusiva. "
            "Expeça-se exigência para apresentação dos elementos faltantes, com posterior retorno para análise."
        ),
        "apensamento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Verificada a correlação material com autos conexos, apense-se o presente expediente para processamento conjunto."
        ),
        "sobrestamento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Considerando a dependência de autos principais para o exame de mérito, sobreste-se o feito até ulterior regularização."
        ),
        "indeferimento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Ausentes os pressupostos necessários ao acolhimento do pedido, indefiro o pleito, nos termos da fundamentação aplicável."
        ),
        "deferimento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Atendidos os requisitos mínimos informados para apreciação do pedido, defiro o pleito, com as providências subsequentes."
        ),
        "arquivamento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Ausente providência útil imediata, arquivem-se os autos, observadas as cautelas de praxe."
        ),
        "encaminhamento": (
            f"Trata-se do processo {process_number}, relativo a {normalized_subject}. "
            "Verificam-se pendências que impedem, por ora, a apreciação conclusiva do mérito. "
            "Encaminhem-se os autos para análise técnica e saneamento das inconsistências apontadas."
        ),
    }
    return templates[action]


def build_institutional_output(
    audit_data: dict[str, Any],
    *,
    source: str = "audit_data_estruturado",
) -> dict[str, Any]:
    process_number = _clean_text(audit_data.get("process_number"), default="Não identificado nos autos auditados.")
    process_type = _clean_text(audit_data.get("process_type"), default="Não identificado.")
    interested_party = _clean_text(audit_data.get("interested_party"), default="Não identificado nos autos auditados.")
    subject = _clean_text(audit_data.get("subject"), default="Matéria não identificada nos autos auditados.")
    stage = _clean_text(audit_data.get("stage"), default="Fase processual não identificada.")
    origin_unit = _clean_text(audit_data.get("origin_unit"), default="Não identificada.")
    specialized_unit = _clean_text(audit_data.get("specialized_unit"), default="Não indicada.")

    documents_present = _clean_list(audit_data.get("documents_present"))
    documents_missing = _clean_list(audit_data.get("documents_missing"))
    inconsistencies = _clean_list(audit_data.get("inconsistencies"))
    legal_basis = _clean_list(audit_data.get("legal_basis"))
    competence_notes = _clean_list(audit_data.get("competence_notes"))

    achados: list[str] = []
    achados.extend(_sentence("Consta", item) for item in documents_present)
    achados.extend(_sentence("Não consta", item) for item in documents_missing)
    achados.extend(_sentence("Verifica-se", item) for item in inconsistencies)
    if not achados:
        achados.append("Não foram informados achados objetivos suficientes para conclusão de mérito.")

    enquadramento: list[str] = []
    enquadramento.extend(item.rstrip(".") + "." for item in legal_basis)
    enquadramento.extend(item.rstrip(".") + "." for item in competence_notes)
    if audit_data.get("depends_on_main_process"):
        enquadramento.append("O exame depende de processo principal para conclusão de mérito.")
    if specialized_unit != "Não indicada.":
        enquadramento.append(f"A matéria indica atuação da unidade especializada {specialized_unit}.")
    if not enquadramento:
        enquadramento.append("O enquadramento normativo e procedimental depende de complementação dos dados estruturados.")

    riscos_ou_lacunas: list[str] = []
    riscos_ou_lacunas.extend(_sentence("Ausência de", item) for item in documents_missing)
    riscos_ou_lacunas.extend(_sentence("Inconsistência identificada:", item) for item in inconsistencies)
    if audit_data.get("depends_on_main_process"):
        riscos_ou_lacunas.append("Dependência de processo principal para exame conclusivo do mérito.")
    if not riscos_ou_lacunas:
        riscos_ou_lacunas.append("Sem lacunas materiais explicitamente informadas no objeto de auditoria.")

    action = infer_recommended_action(audit_data)
    qualificacao = _classify_issue(audit_data, action)

    source_notes = {
        "fonte": source,
        "trata_se_de_leitura_preliminar": "sim" if source != "audit_data_estruturado" else "não",
    }
    if source != "audit_data_estruturado":
        source_notes["observacao"] = (
            "Saída derivada de bundle TCRIA. Campos processuais ausentes no bundle foram preservados como não identificados."
        )

    return {
        "identificacao_do_caso": {
            "processo": process_number,
            "tipo": process_type,
            "interessado": interested_party,
            "tema": subject,
            "unidade_origem": origin_unit,
            "fase": stage,
            "unidade_competente_sugerida": specialized_unit,
        },
        "achados_objetivos": achados,
        "enquadramento": enquadramento,
        "qualificacao_do_problema": qualificacao,
        "riscos_ou_lacunas": riscos_ou_lacunas,
        "conclusao_operacional": _build_conclusion(action, specialized_unit=specialized_unit),
        "tipo_de_ato_sugerido": ACTION_LABELS[action],
        "minuta_sugerida": _build_minuta(
            action,
            process_number=process_number,
            subject=subject,
            specialized_unit=specialized_unit,
        ),
        "metadados_da_saida": source_notes,
    }


def build_institutional_output_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    accusation_set = bundle.get("accusation_set") or []
    non_accusation_set = bundle.get("non_accusation_set") or []
    all_records = [*accusation_set, *non_accusation_set]

    documents_present = [
        f"documento '{record.get('file_name')}' classificado como {record.get('classification')}"
        for record in all_records[:6]
        if record.get("file_name") and record.get("classification")
    ]
    unreadable = [
        record.get("file_name")
        for record in all_records
        if record.get("classification") in {"UNREADABLE", "UNREADABLE_OR_EMPTY"} and record.get("file_name")
    ]
    blocked = [
        record.get("file_name")
        for record in accusation_set
        if isinstance(record.get("overall_outcome"), str) and "BLOCKED" in record.get("overall_outcome", "") and record.get("file_name")
    ]

    inconsistencies: list[str] = []
    if blocked:
        inconsistencies.append("bloqueio de governança em " + ", ".join(blocked))
    if unreadable:
        inconsistencies.append("impossibilidade de leitura integral em " + ", ".join(unreadable))

    route_counts = bundle.get("route_counts") if isinstance(bundle.get("route_counts"), dict) else {}
    legal_basis = [
        _clean_text(bundle.get("audit_basis"), default=""),
        f"Modo de compliance: {_clean_text(bundle.get('compliance_gate_mode'), default='não informado')}",
    ]
    legal_basis = [item for item in legal_basis if item]

    competence_notes = [
        f"Distribuição de rotas identificada na auditoria: {_compact_dict(route_counts)}."
    ]
    if bundle.get("accusation_set_count"):
        competence_notes.append(
            "Os registros classificados como acusatórios exigem validação humana antes de qualquer fechamento prescritivo."
        )
    else:
        competence_notes.append(
            "Não foram identificados registros classificados como acusatórios no recorte auditado."
        )

    recommended_action = "encaminhamento"
    if blocked:
        recommended_action = "remessa"
    elif unreadable:
        recommended_action = "exigencia"

    audit_data = {
        "process_number": bundle.get("process_number") or "Não identificado no bundle TCRIA.",
        "process_type": "auditoria documental derivada de bundle",
        "interested_party": bundle.get("interested_party") or "Não identificado no bundle TCRIA.",
        "subject": bundle.get("subject") or "matéria não detalhada no bundle TCRIA",
        "origin_unit": bundle.get("origin_unit") or "Não identificada no bundle TCRIA.",
        "stage": bundle.get("stage") or "análise automatizada inicial",
        "documents_present": documents_present,
        "documents_missing": [f"leitura válida do arquivo '{name}'" for name in unreadable],
        "inconsistencies": inconsistencies,
        "legal_basis": legal_basis,
        "competence_notes": competence_notes,
        "depends_on_main_process": False,
        "specialized_unit": "Revisão humana especializada" if blocked else "",
        "recommended_action": recommended_action,
    }
    return build_institutional_output(audit_data, source="bundle_tcria")


def render_institutional_markdown(output: dict[str, Any]) -> str:
    identification = output.get("identificacao_do_caso") or {}
    qualificacao = output.get("qualificacao_do_problema") or {}
    metadata = output.get("metadados_da_saida") or {}

    lines = ["# TCRIA Institutional Output", ""]

    sections = [
        (
            "IDENTIFICAÇÃO DO CASO",
            [
                ("Processo", "processo"),
                ("Tipo", "tipo"),
                ("Interessado", "interessado"),
                ("Tema", "tema"),
                ("Unidade de origem", "unidade_origem"),
                ("Fase", "fase"),
                ("Unidade competente sugerida", "unidade_competente_sugerida"),
            ],
            identification,
        ),
        (
            "QUALIFICAÇÃO DO PROBLEMA",
            [
                ("Natureza do vício", "natureza_do_vicio"),
                ("Maturidade decisória", "nivel_de_maturidade_decisoria"),
                ("Há unidade especializada", "ha_unidade_especializada"),
                ("Depende de processo principal", "depende_de_processo_principal"),
                ("Ato recomendado", "ato_recomendado"),
            ],
            qualificacao,
        ),
        (
            "METADADOS DA SAÍDA",
            [
                ("Fonte", "fonte"),
                ("Leitura preliminar", "trata_se_de_leitura_preliminar"),
                ("Observação", "observacao"),
            ],
            metadata,
        ),
    ]

    for title, rows, data in sections:
        lines.append(f"## {title}")
        lines.append("")
        for label, key in rows:
            value = data.get(key)
            if value:
                lines.append(f"- **{label}:** {value}")
        lines.append("")

    for title, key in [
        ("ACHADOS OBJETIVOS", "achados_objetivos"),
        ("ENQUADRAMENTO", "enquadramento"),
        ("RISCOS OU LACUNAS", "riscos_ou_lacunas"),
    ]:
        lines.append(f"## {title}")
        lines.append("")
        for item in output.get(key, []) or ["Não informado."]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## CONCLUSÃO OPERACIONAL")
    lines.append("")
    lines.append(output.get("conclusao_operacional", "Não informada."))
    lines.append("")
    lines.append(f"**Tipo de ato sugerido:** {output.get('tipo_de_ato_sugerido', 'Não informado.')}")
    lines.append("")
    lines.append("## MINUTA SUGERIDA")
    lines.append("")
    lines.append(output.get("minuta_sugerida", "Não informada."))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"
