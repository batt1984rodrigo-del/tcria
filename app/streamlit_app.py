from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from tcria.engine import TCRIAEngine
from tcria.institutional_output import build_institutional_output, render_institutional_markdown
from tcria.openai_responses import list_audit_prompt_presets, run_audit_prompt
from tcria.settings import load_env


load_env()


def render() -> None:
    st.set_page_config(page_title="TCRIA", layout="wide")
    st.title("TCRIA — Legal Evidence Governance Platform")
    st.caption("Engine + Governance Gates + Audit Bundle")

    engine = TCRIAEngine()

    input_path = st.text_input("Document folder path", value=str(Path.home() / "Downloads"))
    out_dir = st.text_input("Output folder", value="output/audit")
    output_stem = st.text_input("Output name", value="audit")
    strict = st.checkbox("Strict compliance mode", value=True)
    include_pdf = st.checkbox("Generate PDF report", value=True)
    use_official_pipeline = st.checkbox("Use official governance pipeline scripts", value=False)
    use_openai_summary = st.checkbox("Run Responses API analysis", value=False)
    institutional_input = st.text_area(
        "Structured institutional data (JSON)",
        value="",
        help=(
            "Optional. Paste `audit_data` here to generate a client-ready institutional document "
            "with process metadata richer than the raw bundle."
        ),
    )

    presets = list_audit_prompt_presets()
    preset_map = {preset["label"]: preset for preset in presets}
    preset_labels = list(preset_map)
    selected_preset_label = st.selectbox(
        "Audit prompt preset",
        preset_labels,
        index=0,
        disabled=not use_openai_summary,
    )
    selected_preset = preset_map[selected_preset_label]
    st.caption(selected_preset["description"])
    openai_model = st.text_input("OpenAI model", value="gpt-4.1-mini", disabled=not use_openai_summary)
    openai_context = st.text_area(
        "Override prompt context",
        value="",
        disabled=not use_openai_summary,
        help="Optional. Leave empty to use the preset default prompt.",
    )

    if st.button("Run TCRIA Audit", type="primary"):
        try:
            with st.spinner("Running..."):
                if use_official_pipeline:
                    result = engine.run_official_pipeline(
                        input_path=input_path,
                        strict=strict,
                        output_stem=output_stem,
                    )
                else:
                    result = engine.run_audit(
                        input_path=input_path,
                        strict=strict,
                        out_dir=out_dir,
                        output_stem=output_stem,
                        include_pdf=include_pdf,
                    )
        except Exception as exc:
            st.error(f"Audit failed: {exc}")
            return

        st.success("Audit completed.")

        institutional_override = None
        if institutional_input.strip():
            try:
                parsed_institutional_input = json.loads(institutional_input)
                if not isinstance(parsed_institutional_input, dict):
                    raise ValueError("The JSON must be an object.")
                institutional_override = build_institutional_output(parsed_institutional_input)
            except Exception as exc:
                st.warning(f"Structured institutional data ignored: {exc}")

        tab_summary, tab_institutional, tab_bundle = st.tabs(
            ["Resumo executivo", "Saída institucional", "Bundle bruto"]
        )

        with tab_summary:
            bundle = result.get("bundle") if isinstance(result, dict) else None
            if isinstance(bundle, dict):
                col1, col2, col3 = st.columns(3)
                col1.metric("Arquivos auditados", bundle.get("total_files_scanned", 0))
                col2.metric("Registros acusatórios", bundle.get("accusation_set_count", 0))
                col3.metric("Modo", bundle.get("mode", "não informado"))
                st.write("**Classificações**")
                st.json(bundle.get("classification_counts", {}))
                st.write("**Rotas identificadas**")
                st.json(bundle.get("route_counts", {}))
            else:
                st.info("O bundle não foi retornado em formato estruturado.")

        with tab_institutional:
            institutional_output = institutional_override or (result.get("institutional_output") if isinstance(result, dict) else None)
            if isinstance(institutional_output, dict):
                identification = institutional_output.get("identificacao_do_caso", {})
                qualification = institutional_output.get("qualificacao_do_problema", {})
                metadata = institutional_output.get("metadados_da_saida", {})
                st.subheader("Identificação do caso")
                st.table(
                    [
                        {"Campo": "Processo", "Valor": identification.get("processo")},
                        {"Campo": "Tipo", "Valor": identification.get("tipo")},
                        {"Campo": "Interessado", "Valor": identification.get("interessado")},
                        {"Campo": "Tema", "Valor": identification.get("tema")},
                        {"Campo": "Unidade de origem", "Valor": identification.get("unidade_origem")},
                        {"Campo": "Fase", "Valor": identification.get("fase")},
                        {
                            "Campo": "Unidade competente sugerida",
                            "Valor": identification.get("unidade_competente_sugerida"),
                        },
                    ]
                )

                for title, key in [
                    ("Achados objetivos", "achados_objetivos"),
                    ("Enquadramento", "enquadramento"),
                    ("Riscos ou lacunas", "riscos_ou_lacunas"),
                ]:
                    st.subheader(title)
                    for item in institutional_output.get(key, []):
                        st.markdown(f"- {item}")

                st.subheader("Qualificação do problema")
                st.table(
                    [
                        {"Campo": "Natureza do vício", "Valor": qualification.get("natureza_do_vicio")},
                        {
                            "Campo": "Maturidade decisória",
                            "Valor": qualification.get("nivel_de_maturidade_decisoria"),
                        },
                        {"Campo": "Há unidade especializada", "Valor": qualification.get("ha_unidade_especializada")},
                        {
                            "Campo": "Depende de processo principal",
                            "Valor": qualification.get("depende_de_processo_principal"),
                        },
                        {"Campo": "Ato recomendado", "Valor": qualification.get("ato_recomendado")},
                    ]
                )

                st.subheader("Conclusão operacional")
                st.write(institutional_output.get("conclusao_operacional"))
                st.caption(f"Ato sugerido: {institutional_output.get('tipo_de_ato_sugerido')}")

                st.subheader("Minuta sugerida")
                st.code(institutional_output.get("minuta_sugerida", ""), language="markdown")
                st.download_button(
                    "Baixar saída institucional (.md)",
                    data=render_institutional_markdown(institutional_output),
                    file_name=f"{output_stem}_institutional.md",
                    mime="text/markdown",
                )
                st.write("**JSON estruturado**")
                st.json(institutional_output)
                if metadata:
                    st.caption(
                        f"Fonte: {metadata.get('fonte')} | "
                        f"Leitura preliminar: {metadata.get('trata_se_de_leitura_preliminar')}"
                    )
            else:
                st.info("A saída institucional não foi gerada para este resultado.")

        with tab_bundle:
            st.subheader("Result")
            st.json(result)

        if not use_official_pipeline:
            artifacts = result.get("artifacts", {})
            st.subheader("Artifacts")
            for label, path_value in artifacts.items():
                path = Path(str(path_value))
                st.write(f"{label}: {path}")
                if path.exists():
                    st.download_button(
                        f"Download {path.name}",
                        data=path.read_bytes(),
                        file_name=path.name,
                        key=f"dl-{label}-{path.name}",
                    )

            bundle = result.get("bundle")
            if isinstance(bundle, dict):
                st.subheader("Bundle summary")
                st.code(json.dumps(
                    {
                        "total_files_scanned": bundle.get("total_files_scanned"),
                        "accusation_set_count": bundle.get("accusation_set_count"),
                        "classification_counts": bundle.get("classification_counts"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ))

                if use_openai_summary:
                    st.subheader("Responses API Analysis")
                    try:
                        with st.spinner("Running preset analysis with OpenAI..."):
                            responses_result = run_audit_prompt(
                                bundle,
                                audit_type=selected_preset["slug"],
                                model=openai_model,
                                user_context=openai_context or None,
                            )
                    except Exception as exc:
                        st.error(f"Responses API analysis failed: {exc}")
                    else:
                        st.write(responses_result["response_text"])
                        st.caption(
                            f"audit_type={responses_result['audit_type']} | "
                            f"model={responses_result['response_metadata'].get('model')}"
                        )


if __name__ == "__main__":
    render()
