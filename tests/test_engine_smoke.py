from __future__ import annotations

from pathlib import Path

import pytest

from tcria.engine import TCRIAEngine
from tcria.institutional_output import build_institutional_output, build_institutional_output_from_bundle
from tcria.ingestion.file_loader import load_documents


def test_engine_run_audit_smoke(tmp_path: Path) -> None:
    input_dir = tmp_path / "docs"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "note.txt").write_text(
        "\n".join(
            [
                "[TCR-IA DECISION RECORD]",
                "responsibleHuman: Test Owner",
                "declaredPurpose: Governed evidence organization",
                "approved: YES",
                "[/TCR-IA DECISION RECORD]",
                "",
                "Fraude em transacao PIX no valor de R$ 1.000,00 em 05/03/2026.",
                "Anexo com comprovantes e extratos.",
            ]
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    engine = TCRIAEngine(repo_root=tmp_path)
    result = engine.run_audit(
        input_path=str(input_dir),
        strict=True,
        out_dir=str(out_dir),
        output_stem="smoke",
        include_pdf=False,
    )

    bundle = result["bundle"]
    artifacts = result["artifacts"]
    assert bundle["total_files_scanned"] == 1
    assert bundle["accusation_set_count"] >= 0
    assert "institutional_output" in result
    assert Path(artifacts["json"]).exists()
    assert Path(artifacts["markdown"]).exists()
    assert Path(artifacts["institutional_markdown"]).exists()


def test_load_documents_respects_max_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "docs"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "a.txt").write_text("ok", encoding="utf-8")
    (input_dir / "b.txt").write_text("ok", encoding="utf-8")

    with pytest.raises(ValueError, match="max_files"):
        load_documents(str(input_dir), max_files=1)


def test_load_documents_respects_max_total_bytes(tmp_path: Path) -> None:
    input_dir = tmp_path / "docs"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "a.txt").write_text("0123456789", encoding="utf-8")

    with pytest.raises(ValueError, match="max_total_bytes"):
        load_documents(str(input_dir), max_total_bytes=5)


def test_build_institutional_output_prefers_specialized_remessa() -> None:
    output = build_institutional_output(
        {
            "process_number": "SEI-000000/000000/2026",
            "process_type": "principal",
            "interested_party": "Empresa XPTO",
            "subject": "pedido de inscrição estadual",
            "stage": "análise inicial",
            "documents_present": ["petição inicial", "comprovante cadastral"],
            "documents_missing": ["comprovante idôneo de recolhimento"],
            "inconsistencies": ["divergência entre CNPJ da petição e do cadastro"],
            "legal_basis": ["Aplica-se o rito de saneamento prévio da instrução."],
            "competence_notes": ["Compete à unidade especializada a análise temática do pedido."],
            "specialized_unit": "Cefage",
        }
    )

    assert output["tipo_de_ato_sugerido"] == "remessa"
    assert "Cefage" in output["conclusao_operacional"]
    assert "encaminhem-se os autos à Cefage." in output["minuta_sugerida"]
    assert output["qualificacao_do_problema"]["ha_unidade_especializada"] == "sim"


def test_build_institutional_output_from_bundle_marks_preliminary_source() -> None:
    output = build_institutional_output_from_bundle(
        {
            "audit_basis": "Base de auditoria TCRIA.",
            "compliance_gate_mode": "strict-explicit-decision-record",
            "route_counts": {"FISCAL_SUPPORT": 2},
            "accusation_set_count": 0,
            "accusation_set": [],
            "non_accusation_set": [
                {
                    "file_name": "doc1.pdf",
                    "classification": "SUPPORTING_EVIDENCE_RELEVANT",
                }
            ],
        }
    )

    assert output["metadados_da_saida"]["fonte"] == "bundle_tcria"
    assert output["metadados_da_saida"]["trata_se_de_leitura_preliminar"] == "sim"
    assert output["identificacao_do_caso"]["tema"] == "matéria não detalhada no bundle TCRIA"
