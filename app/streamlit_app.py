from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from tcria.engine import TCRIAEngine
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
