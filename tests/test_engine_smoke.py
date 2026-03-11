from __future__ import annotations

from pathlib import Path

import pytest

from tcria.engine import TCRIAEngine
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
    assert bundle["accusation_set_count"] == 1
    assert Path(artifacts["json"]).exists()
    assert Path(artifacts["markdown"]).exists()


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
