from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent

RUN_PIPELINE_SCRIPT = REPO_ROOT / "run_governance_pipeline.py"
PREPARATION_SCRIPT = REPO_ROOT / "generate_case_preparation_summary.py"
TIMELINE_SCRIPT = REPO_ROOT / "generate_case_timeline.py"
UNIFIED_PDF_SCRIPT = REPO_ROOT / "generate_unified_governance_report_pdf.py"
INVESTIGATION_SCRIPT = REPO_ROOT / "scripts" / "generate_investigation_report.py"


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if cp.stdout:
        print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="", file=sys.stderr)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)
    return cp


def extract_line_value(text: str, label: str) -> Optional[Path]:
    m = re.search(rf"^{re.escape(label)}\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return None
    return Path(m.group(1).strip()).expanduser().resolve()


def resolve_case_dir(case_arg: str, root: str) -> Path:
    raw = Path(case_arg).expanduser()
    if raw.is_absolute() or "/" in case_arg or case_arg.startswith("."):
        return raw.resolve()
    return (Path(root).expanduser().resolve() / case_arg).resolve()


def ensure_case_structure(case_dir: Path) -> None:
    for rel in ["input", "audit", "blocked", "preparation", "timeline", "report"]:
        (case_dir / rel).mkdir(parents=True, exist_ok=True)


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def to_rel(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path.resolve())


def update_manifest_latest_outputs(case_dir: Path, updates: Dict[str, Path]) -> None:
    manifest_path = case_dir / "case_manifest.json"
    manifest = load_manifest(manifest_path)
    if not manifest:
        manifest = {
            "case_id": case_dir.name,
            "label": case_dir.name,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "workspace": {
                "input_dir": "input",
                "audit_dir": "audit",
                "blocked_dir": "blocked",
                "preparation_dir": "preparation",
                "timeline_dir": "timeline",
                "report_dir": "report",
            },
            "latest_outputs": {},
            "guardrails": {
                "official_outcome_changes_allowed": False,
                "diagnostic_layers_are_complementary": True,
            },
        }
    latest = manifest.setdefault("latest_outputs", {})
    for k, v in updates.items():
        latest[k] = to_rel(v, case_dir)
    save_manifest(manifest_path, manifest)


def copy_into_case(case_dir: Path, src: Path, subdir: str) -> Path:
    target_dir = case_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / src.name
    shutil.copy2(src, dst)
    return dst


def case_init(case_dir: Path) -> int:
    ensure_case_structure(case_dir)
    manifest_path = case_dir / "case_manifest.json"
    manifest = {
        "case_id": case_dir.name,
        "label": case_dir.name,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "workspace": {
            "input_dir": "input",
            "audit_dir": "audit",
            "blocked_dir": "blocked",
            "preparation_dir": "preparation",
            "timeline_dir": "timeline",
            "report_dir": "report",
        },
        "latest_outputs": {},
        "guardrails": {
            "official_outcome_changes_allowed": False,
            "diagnostic_layers_are_complementary": True,
        },
    }
    save_manifest(manifest_path, manifest)
    print(f"Case initialized: {case_dir}")
    print(f"Manifest: {manifest_path}")
    return 0


def case_run(case_dir: Path, strict: bool, paths: list[str], top_k: int, output_stem: Optional[str]) -> int:
    ensure_case_structure(case_dir)

    if not RUN_PIPELINE_SCRIPT.exists():
        raise SystemExit(f"Missing script: {RUN_PIPELINE_SCRIPT}")
    if not PREPARATION_SCRIPT.exists():
        raise SystemExit(f"Missing script: {PREPARATION_SCRIPT}")
    if not TIMELINE_SCRIPT.exists():
        raise SystemExit(f"Missing script: {TIMELINE_SCRIPT}")
    if not UNIFIED_PDF_SCRIPT.exists():
        raise SystemExit(f"Missing script: {UNIFIED_PDF_SCRIPT}")

    run_paths = paths[:] if paths else [str(case_dir / "input")]
    stem = output_stem or f"{case_dir.name}_{datetime.now().strftime('%Y%m%d')}"

    cmd = [
        sys.executable,
        str(RUN_PIPELINE_SCRIPT),
        "--repo-root",
        str(REPO_ROOT),
        "--output-stem",
        stem,
    ]
    if strict:
        cmd.append("--strict")
    for p in run_paths:
        cmd.extend(["--path", p])

    pipeline_cp = run_command(cmd, cwd=REPO_ROOT)
    out = pipeline_cp.stdout or ""

    audit_json = extract_line_value(out, "[pipeline] Official audit JSON:")
    blocked_json = extract_line_value(out, "[pipeline] Blocked review JSON:")
    blocked_md = extract_line_value(out, "[pipeline] Blocked review MD:")
    audit_md = extract_line_value(out, "Markdown report:")
    if not audit_json or not blocked_json:
        raise SystemExit("Could not parse official outputs from pipeline run.")
    if not audit_md:
        audit_md = audit_json.with_suffix(".md")
    if not blocked_md:
        blocked_md = blocked_json.with_suffix(".md")

    prep_cp = run_command(
        [
            sys.executable,
            str(PREPARATION_SCRIPT),
            "--audit-json",
            str(audit_json),
            "--blocked-json",
            str(blocked_json),
            "--top-k",
            str(top_k),
        ],
        cwd=REPO_ROOT,
    )
    prep_out = prep_cp.stdout or ""
    prep_json = extract_line_value(prep_out, "JSON summary:")
    prep_md = extract_line_value(prep_out, "Markdown summary:")
    if not prep_json or not prep_md:
        raise SystemExit("Could not parse case preparation outputs.")

    timeline_cp = run_command(
        [
            sys.executable,
            str(TIMELINE_SCRIPT),
            "--audit-json",
            str(audit_json),
            "--top-k",
            str(max(top_k, 20)),
        ],
        cwd=REPO_ROOT,
    )
    timeline_out = timeline_cp.stdout or ""
    timeline_json = extract_line_value(timeline_out, "Timeline JSON:")
    timeline_md = extract_line_value(timeline_out, "Timeline Markdown:")
    if not timeline_json or not timeline_md:
        raise SystemExit("Could not parse timeline outputs.")

    unified_pdf = audit_json.parent / f"{stem}_unificado.pdf"
    run_command(
        [
            sys.executable,
            str(UNIFIED_PDF_SCRIPT),
            "--audit-json",
            str(audit_json),
            "--blocked-json",
            str(blocked_json),
            "--output",
            str(unified_pdf),
            "--title",
            f"Relatorio Unificado - {case_dir.name}",
        ],
        cwd=REPO_ROOT,
    )

    copied: Dict[str, Path] = {}
    copied["official_audit_json"] = copy_into_case(case_dir, audit_json, "audit")
    copied["official_audit_md"] = copy_into_case(case_dir, audit_md, "audit")
    copied["unified_pdf"] = copy_into_case(case_dir, unified_pdf, "audit")
    copied["blocked_review_json"] = copy_into_case(case_dir, blocked_json, "blocked")
    copied["blocked_review_md"] = copy_into_case(case_dir, blocked_md, "blocked")
    copied["case_preparation_json"] = copy_into_case(case_dir, prep_json, "preparation")
    copied["case_preparation_md"] = copy_into_case(case_dir, prep_md, "preparation")
    copied["timeline_json"] = copy_into_case(case_dir, timeline_json, "timeline")
    copied["timeline_md"] = copy_into_case(case_dir, timeline_md, "timeline")
    update_manifest_latest_outputs(case_dir, copied)

    print(f"Case run completed: {case_dir}")
    for k, v in copied.items():
        print(f"- {k}: {v}")
    return 0


def find_latest_json(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def investigate(case_dir: Path, audit: Optional[str], blocked: Optional[str], preparation: Optional[str], timeline: Optional[str]) -> int:
    ensure_case_structure(case_dir)
    if not INVESTIGATION_SCRIPT.exists():
        raise SystemExit(f"Missing script: {INVESTIGATION_SCRIPT}")

    audit_path = Path(audit).expanduser().resolve() if audit else find_latest_json(case_dir / "audit", "*_strict.json")
    blocked_path = (
        Path(blocked).expanduser().resolve()
        if blocked
        else find_latest_json(case_dir / "blocked", "*_blocked_artifacts_review.json")
    )
    preparation_path = (
        Path(preparation).expanduser().resolve()
        if preparation
        else find_latest_json(case_dir / "preparation", "*_case_preparation_summary.json")
    )
    timeline_path = Path(timeline).expanduser().resolve() if timeline else find_latest_json(case_dir / "timeline", "*_timeline.json")

    if not audit_path or not blocked_path or not preparation_path or not timeline_path:
        raise SystemExit("Missing inputs for investigation. Provide paths explicitly or run `tcria case run` first.")

    report_dir = case_dir / "report"
    run_command(
        [
            sys.executable,
            str(INVESTIGATION_SCRIPT),
            "--audit",
            str(audit_path),
            "--blocked",
            str(blocked_path),
            "--preparation",
            str(preparation_path),
            "--timeline",
            str(timeline_path),
            "--output-dir",
            str(report_dir),
        ],
        cwd=REPO_ROOT,
    )

    outputs = {
        "investigation_report_json": report_dir / "investigation_report.json",
        "investigation_report_md": report_dir / "investigation_report.md",
        "investigation_report_pdf": report_dir / "investigation_report.pdf",
    }
    update_manifest_latest_outputs(case_dir, outputs)
    print(f"Investigation completed: {case_dir}")
    for k, v in outputs.items():
        print(f"- {k}: {v}")
    return 0


def scan_compat(input_path: str, strict: bool, output_stem: Optional[str]) -> int:
    temp_case = (REPO_ROOT / "cases" / "__scan_temp").resolve()
    return case_run(temp_case, strict=strict, paths=[input_path], top_k=10, output_stem=output_stem)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tcria", description="TCRIA — Legal evidence governance scanner.")
    sub = p.add_subparsers(dest="cmd", required=True)

    case = sub.add_parser("case", help="Case workspace commands")
    case_sub = case.add_subparsers(dest="case_cmd", required=True)

    case_init_cmd = case_sub.add_parser("init", help="Initialize case workspace")
    case_init_cmd.add_argument("case", help="Case id or case directory path")
    case_init_cmd.add_argument("--root", default="cases", help="Root dir for case ids (default: cases)")

    case_run_cmd = case_sub.add_parser("run", help="Run case pipeline layers")
    case_run_cmd.add_argument("case", help="Case id or case directory path")
    case_run_cmd.add_argument("--root", default="cases", help="Root dir for case ids (default: cases)")
    case_run_cmd.add_argument("--strict", action="store_true", help="Run strict mode")
    case_run_cmd.add_argument("--path", action="append", dest="paths", help="Input path (repeatable). Defaults to case input dir.")
    case_run_cmd.add_argument("--top-k", type=int, default=10, help="Top K for summary layers")
    case_run_cmd.add_argument("--output-stem", default=None, help="Output stem for official audit")

    inv = sub.add_parser("investigate", help="Generate final investigation report for a case")
    inv.add_argument("case", help="Case id or case directory path")
    inv.add_argument("--root", default="cases", help="Root dir for case ids (default: cases)")
    inv.add_argument("--audit", default=None, help="Audit JSON path (optional)")
    inv.add_argument("--blocked", default=None, help="Blocked review JSON path (optional)")
    inv.add_argument("--preparation", default=None, help="Preparation JSON path (optional)")
    inv.add_argument("--timeline", default=None, help="Timeline JSON path (optional)")

    scan = sub.add_parser("scan", help="Compatibility command: run pipeline for one input")
    scan.add_argument("input", help="File/folder input")
    scan.add_argument("--strict", action="store_true", help="Run strict mode")
    scan.add_argument("--output-stem", default=None, help="Output stem")

    args = p.parse_args(argv)

    if args.cmd == "case":
        case_dir = resolve_case_dir(args.case, args.root)
        if args.case_cmd == "init":
            return case_init(case_dir)
        if args.case_cmd == "run":
            return case_run(case_dir, strict=args.strict, paths=args.paths or [], top_k=args.top_k, output_stem=args.output_stem)
        raise SystemExit(2)

    if args.cmd == "investigate":
        case_dir = resolve_case_dir(args.case, args.root)
        return investigate(case_dir, args.audit, args.blocked, args.preparation, args.timeline)

    if args.cmd == "scan":
        return scan_compat(args.input, strict=args.strict, output_stem=args.output_stem)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
