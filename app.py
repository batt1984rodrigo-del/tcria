import os
import pathlib
import subprocess
import sys
import streamlit as st

st.set_page_config(page_title="TCRIA", layout="wide")
st.title("TCRIA — Legal Evidence Governance Scanner")

st.markdown("Upload a ZIP of documents **or** point to a local folder (if running locally).")

mode = st.radio("Input mode", ["Local folder", "ZIP upload"], horizontal=True)

repo_root = st.text_input("Repo root (where the audit script lives)", value=str(pathlib.Path.cwd()))
script = st.text_input("Audit script", value="audit_accusation_bundle_with_tcr_gateway.py")
strict = st.checkbox("Strict compliance mode (explicit DecisionRecord required)", value=True)
out_dir = st.text_input("Output directory", value="output/audit")

input_path = None

if mode == "Local folder":
    input_path = st.text_input("Folder to scan", value=str(pathlib.Path.home() / "Downloads"))
else:
    up = st.file_uploader("Upload ZIP", type=["zip"])
    if up is not None:
        work = pathlib.Path("output/_uploads")
        work.mkdir(parents=True, exist_ok=True)
        zip_path = work / up.name
        zip_path.write_bytes(up.getbuffer())
        extract_dir = work / (zip_path.stem + "_extracted")
        if extract_dir.exists():
            import shutil
            shutil.rmtree(extract_dir)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
        input_path = str(extract_dir)
        st.success(f"Extracted to: {input_path}")

if st.button("Run scan", type="primary", disabled=not bool(input_path)):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(pathlib.Path(repo_root) / script), str(pathlib.Path(input_path)), str(out)]
    if strict:
        cmd.append("--strict")
    st.code(" ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    st.subheader("stdout")
    st.code(p.stdout or "(empty)")
    st.subheader("stderr")
    st.code(p.stderr or "(empty)")

    # Try to surface the expected outputs
    st.subheader("Outputs")
    for name in ["*.json", "*.md", "*.pdf"]:
        for fp in sorted(out.glob(name)):
            st.write(fp.name)
            if fp.suffix == ".pdf":
                st.download_button(f"Download {fp.name}", data=fp.read_bytes(), file_name=fp.name)
            else:
                st.download_button(f"Download {fp.name}", data=fp.read_bytes(), file_name=fp.name)
