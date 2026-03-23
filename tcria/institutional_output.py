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


def _clean_text(value: Any, *, default: str = "Não informado.") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _clean_list(items: Any) -> list[str]:
    if not items:
        return []
    cleaned: list[str] = []
    iterable = items if isinstance(items, (list, tuple, set)) else [items]
    for item in iterable:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _join_labels(values: dict[str, Any]) -> str:
    if not values:
        return "Não identificado nos autos auditados."
    ordered = [f"{key}: {value}" for key, value in sorted(values.items()) if value]
    return "; ".join(ordered) if ordered else "Não identificado nos autos auditados."


def _normalize_action(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace("ç", "c").replace("ã", "a")
    mapping = {
        "exigência": "exigencia",
        "encaminhamento": "encaminhamento",
        "saneamento": "exigencia",
        "vinculacao": "juntada",
        "vinculação": "juntada",
    }
    text = mapping.get(text, text)
    if text in KNOWN_ACTIONS:
        return text
    return None


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
    if specialized_unit:
        return "remessa"
    if documents_missing:
        return "exigencia"
    if inconsistencies:
        return "encaminhamento"
    return "encaminhamento"


def build_institutional_output(audit_data: dict[str, Any]) -> dict[str, Any]:
    process_number = _clean_text(audit_data.get("process_number"), default="Não identificado nos autos auditados.")
    process_type = _clean_text(audit_data.get("process_type"), default="Não identificado.")
    interested_party = _clean_text(audit_data.get("interested_party"), default="Não identificado nos autos auditados.")
    subject = _clean_text(audit_data.get("subject"), default="Matéria não identificada nos autos auditados.")
    stage = _clean_text(audit_data.get("stage"), default="Fase processual não identificada.")
    specialized_unit = _clean_text(audit_data.get("specialized_unit"), default="Não indicada.")

    documents_present = _clean_list(audit_data.get("documents_present"))
    documents_missing = _clean_list(audit_data.get("documents_missing"))
    inconsistencies = _clean_list(audit_data.get("inconsistencies"))
    legal_basis = _clean_list(audit_data.get("legal_basis"))
    competence_notes = _clean_list(audit_data.get("competence_notes"))

    achados: list[str] = []
    if documents_present:
        achados.extend(f"Consta {item}." for item in documents_present)
    if documents_missing:
        achados.extend(f"Não consta {item}." for item in documents_missing)
    if inconsistencies:
        achados.extend(f"Verifica-se {item}." for item in inconsistencies)
    if not achados:
        achados.append("Não foram informados achados objetivos suficientes para conclusão de mérito.")

    enquadramento: list[str] = []
    if legal_basis:
        enquadramento.extend(legal_basis)
    if competence_notes:
        enquadramento.extend(competence_notes)
    if audit_data.get("depends_on_main_process"):
        enquadramento.append("O exame depende de processo principal para conclusão de mérito.")
    if specialized_unit and specialized_unit != "Não indicada.":
        enquadramento.append(f"A matéria indica atuação da unidade especializada {specialized_unit}.")
    if not enquadramento:
        enquadramento.append("O enquadramento normativo e procedimental depende de complementação dos dados estruturados.")

    riscos_ou_lacunas: list[str] = []
    if documents_missing:
        riscos_ou_lacunas.extend(f"Ausência de {item}." for item in documents_missing)
    if inconsistencies:
        riscos_ou_lacunas.extend(f"Inconsistência identificada: {item}." for item in inconsistencies)
    if audit_data.get("depends_on_main_process"):
        riscos_ou_lacunas.append("Dependência de processo principal para exame conclusivo do mérito.")
    if not riscos_ou_lacunas:
        riscos_ou_lacunas.append("Sem lacunas materiais explicitamente informadas no objeto de auditoria.")

    action = infer_recommended_action(audit_data)
    action_titles = {
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
    action_text = action_titles[action]

    conclusion_map = {
        "juntada": "Recomenda-se a juntada ou vinculação ao processo principal, com preservação da análise de mérito para os autos de referência.",
        "remessa": f"Recomenda-se a remessa dos autos à unidade competente ({specialized_unit}) para análise temática, diante da especialização indicada.",
        "exigencia": "Recomenda-se a expedição de exigência para saneamento das lacunas documentais antes de apreciação conclusiva.",
        "apensamento": "Recomenda-se o apensamento dos autos correlatos para instrução conjunta e racionalização do fluxo processual.",
        "sobrestamento": "Recomenda-se o sobrestamento do feito até a superação da condição processual pendente expressamente identificada.",
        "indeferimento": "Estando completa a instrução e ausente suporte mínimo para acolhimento, recomenda-se o indeferimento do pedido.",
        "deferimento": "Estando observados os requisitos mínimos informados, recomenda-se o deferimento do pedido, com os registros de praxe.",
        "arquivamento": "Não subsistindo providência útil imediata, recomenda-se o arquivamento dos autos, com as anotações cabíveis.",
        "encaminhamento": "Não há elementos suficientes para despacho final de mérito. Recomenda-se o encaminhamento dos autos para análise técnica e saneamento do que foi apontado.",
    }
    conclusion = conclusion_map[action]

    minuta_templates = {
        "juntada": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Considerando a natureza intercorrente do expediente e a dependência de apreciação nos autos principais, "
            "junte-se o presente expediente ao processo de referência, com a devida vinculação."
        ),
        "remessa": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            f"Considerando a especialidade da matéria e a necessidade de análise técnica própria, encaminhem-se os autos à {specialized_unit}."
        ),
        "exigencia": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Verifica-se insuficiência de instrução documental para apreciação conclusiva. "
            "Expeça-se exigência para apresentação dos elementos faltantes, com posterior retorno para análise."
        ),
        "apensamento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Verificada a correlação material com autos conexos, apense-se o presente expediente para processamento conjunto."
        ),
        "sobrestamento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Considerando a pendência processual prejudicial ao exame de mérito, sobreste-se o feito até ulterior regularização."
        ),
        "indeferimento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Ausentes os pressupostos necessários ao acolhimento do pedido, indefiro o pleito, nos termos da fundamentação aplicável."
        ),
        "deferimento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Atendidos os requisitos mínimos informados para apreciação do pedido, defiro o pleito, com as providências subsequentes."
        ),
        "arquivamento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Ausente providência útil imediata, arquivem-se os autos, observadas as cautelas de praxe."
        ),
        "encaminhamento": (
            f"Trata-se do processo {process_number}, relativo a {subject.lower()}. "
            "Verificam-se pendências que impedem, por ora, a apreciação conclusiva do mérito. "
            "Encaminhem-se os autos para análise técnica e saneamento das inconsistências apontadas."
        ),
    }

    return {
        "identificacao_do_caso": {
            "processo": process_number,
            "tipo": process_type,
            "interessado": interested_party,
            "tema": subject,
            "fase": stage,
            "unidade_competente_sugerida": specialized_unit,
        },
        "achados_objetivos": achados,
        "enquadramento": enquadramento,
        "riscos_ou_lacunas": riscos_ou_lacunas,
        "conclusao_operacional": conclusion,
        "tipo_de_ato_sugerido": action_text,
        "minuta_sugerida": minuta_templates[action],
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

    legal_basis = [
        _clean_text(bundle.get("audit_basis"), default=""),
        f"Modo de compliance: {_clean_text(bundle.get('compliance_gate_mode'), default='não informado')}",
    ]
    legal_basis = [item for item in legal_basis if item]

    route_counts = bundle.get("route_counts") if isinstance(bundle.get("route_counts"), dict) else {}
    competence_notes = [
        f"Distribuição de rotas identificada na auditoria: {_join_labels(route_counts)}."
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
    if unreadable:
        recommended_action = "exigencia"
    elif blocked:
        recommended_action = "remessa"

    audit_data = {
        "process_number": bundle.get("process_number") or bundle.get("input_path"),
        "process_type": "auditoria documental",
        "interested_party": bundle.get("interested_party") or "Não identificado nos autos auditados.",
        "subject": "auditoria de governança documental",
        "stage": "análise automatizada inicial",
        "documents_present": documents_present,
        "documents_missing": [f"leitura válida do arquivo '{name}'" for name in unreadable],
        "inconsistencies": inconsistencies,
        "legal_basis": legal_basis,
        "competence_notes": competence_notes,
        "depends_on_main_process": False,
        "specialized_unit": "Revisão humana especializada" if blocked else "",
        "recommended_action": recommended_action,
    }
    return build_institutional_output(audit_data)


def render_institutional_markdown(output: dict[str, Any]) -> str:
    identification = output.get("identificacao_do_caso") or {}
    lines = ["# TCRIA Institutional Output", ""]
    lines.append("## IDENTIFICAÇÃO DO CASO")
    lines.append("")
    for label, key in [
        ("Processo", "processo"),
        ("Tipo", "tipo"),
        ("Interessado", "interessado"),
        ("Tema", "tema"),
        ("Fase", "fase"),
        ("Unidade competente sugerida", "unidade_competente_sugerida"),
    ]:
        lines.append(f"- **{label}:** {identification.get(key, 'Não informado.')}")
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
    lines.append(f"**Tipo de ato sugerido:** {output.get('tipo_de_ato_sugerido', 'Não informado.')}\n")
    lines.append("## MINUTA SUGERIDA")
    lines.append("")
    lines.append(output.get("minuta_sugerida", "Não informada."))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"
