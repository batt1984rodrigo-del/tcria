#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def safe_text(value: Any) -> str:
    text = str(value)
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    return text.encode("latin-1", "replace").decode("latin-1")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="TitleX",
            parent=s["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
    )
    s.add(
        ParagraphStyle(
            name="BodyX",
            parent=s["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        )
    )
    s.add(
        ParagraphStyle(
            name="SubtleX",
            parent=s["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.2,
            textColor=colors.HexColor("#64748b"),
        )
    )
    s.add(
        ParagraphStyle(
            name="H2X",
            parent=s["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    return s


def build_kv(rows: List[List[str]], widths: List[float]) -> Table:
    t = Table(rows, colWidths=widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.1),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbe2ea")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def outcome_color(value: str):
    v = (value or "").lower()
    if "blocked" in v:
        return colors.HexColor("#b91c1c")
    if "partial_pass" in v:
        return colors.HexColor("#b45309")
    return colors.HexColor("#166534")


def build_doc(audit: Dict[str, Any], blocked: Dict[str, Any], out_path: Path, title: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=safe_text(title),
        author="OpenAI Codex",
    )
    s = styles()
    story: List[Any] = []

    accusation_set = audit.get("accusation_set") or []
    blocked_items = blocked.get("blocked_artifacts_review") or []
    outcome_counts = Counter((x.get("overall_outcome") or "UNKNOWN") for x in accusation_set)

    story.append(Paragraph(safe_text(title), s["TitleX"]))
    story.append(Paragraph("Unified governance report: official gate outcomes + complementary blocked-artifact diagnostics.", s["BodyX"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Official audit generated: {safe_text(audit.get('generated_at', '-'))}", s["SubtleX"]))
    story.append(Paragraph(f"Blocked diagnostics generated: {safe_text(blocked.get('generated_at', '-'))}", s["SubtleX"]))
    story.append(Paragraph(safe_text(blocked.get("note", "")), s["SubtleX"]))
    story.append(Spacer(1, 8))

    summary_rows = [
        ["Total scanned", str(audit.get("total_files_scanned", 0))],
        ["Accusation set", str(audit.get("accusation_set_count", 0))],
        ["Blocked in official outcome", str(sum(1 for x in accusation_set if "BLOCKED" in str(x.get("overall_outcome", ""))))],
        ["Blocked diagnostics count", str(blocked.get("blocked_count", 0))],
        ["Compliance mode", safe_text(audit.get("compliance_gate_mode", "-"))],
    ]
    story.append(Paragraph("Executive Summary", s["H2X"]))
    story.append(build_kv(summary_rows, [2.2 * inch, 4.6 * inch]))
    story.append(Spacer(1, 8))

    outcome_rows = [["Outcome", "Count"]]
    for k, v in sorted(outcome_counts.items(), key=lambda kv: kv[0]):
        outcome_rows.append([safe_text(k), str(v)])
    story.append(Paragraph("Official Outcome Distribution", s["H2X"]))
    story.append(build_kv(outcome_rows, [4.6 * inch, 1.0 * inch]))
    story.append(Spacer(1, 8))

    table_rows = [["File", "Outcome", "Compliance", "Traceability"]]
    for rec in accusation_set:
        gates = rec.get("gates") or {}
        table_rows.append(
            [
                safe_text(rec.get("file_name", ""))[:40],
                safe_text(rec.get("overall_outcome", "-"))[:42],
                safe_text((gates.get("complianceGate") or {}).get("status", "-")),
                safe_text((gates.get("traceabilityCheck") or {}).get("status", "-")),
            ]
        )
    t = Table(table_rows, colWidths=[2.8 * inch, 2.4 * inch, 0.9 * inch, 0.9 * inch], repeatRows=1)
    ts = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.6),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
    )
    for i, rec in enumerate(accusation_set, start=1):
        ts.add("TEXTCOLOR", (1, i), (1, i), outcome_color(str(rec.get("overall_outcome", ""))))
    t.setStyle(ts)
    story.append(Paragraph("Official Accusation Set", s["H2X"]))
    story.append(t)

    story.append(PageBreak())
    story.append(Paragraph("Blocked Artifact Diagnostics", s["H2X"]))
    story.append(
        Paragraph(
            "Complementary diagnostics only. This section does not modify official gate outcomes or promote blocked artifacts.",
            s["BodyX"],
        )
    )
    story.append(Spacer(1, 6))

    if not blocked_items:
        story.append(Paragraph("No blocked artifacts found in complementary review.", s["BodyX"]))
    else:
        for idx, rec in enumerate(blocked_items, start=1):
            review = rec.get("blockedArtifactReview") or {}
            guardrails = rec.get("diagnostic_guardrails") or {}
            story.append(Paragraph(f"{idx}. {safe_text(rec.get('file_name', '-'))}", s["BodyX"]))
            detail_rows = [
                ["Official outcome", safe_text(rec.get("official_outcome", "-"))],
                ["Blocked gate", safe_text(rec.get("blocked_gate", "-"))],
                ["Blocked reason", safe_text(rec.get("blocked_reason", "-"))],
                ["Document kind", safe_text(review.get("document_kind", "-"))],
                ["Theme related", safe_text(review.get("theme_related", "-"))],
                ["Organizational issue", safe_text(review.get("organizational_issue", "-"))],
                ["Potential case impact", safe_text(review.get("potential_case_impact", "-"))],
            ]
            story.append(build_kv(detail_rows, [1.8 * inch, 5.0 * inch]))
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"Content summary: {safe_text(review.get('content_summary', '-'))}", s["SubtleX"]))
            story.append(Paragraph(f"Recommended action: {safe_text(review.get('recommended_action', '-'))}", s["SubtleX"]))
            story.append(
                Paragraph(
                    "Guardrails: "
                    f"review_mode={safe_text(guardrails.get('review_mode', '-'))}, "
                    f"changes_official_outcome={safe_text(guardrails.get('changes_official_outcome', '-'))}, "
                    f"eligible_for_promotion={safe_text(guardrails.get('eligible_for_promotion', '-'))}, "
                    f"requires_human_re_audit_for_status_change={safe_text(guardrails.get('requires_human_re_audit_for_status_change', '-'))}",
                    s["SubtleX"],
                )
            )
            story.append(Spacer(1, 8))

    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a single PDF with official audit and blocked-artifact diagnostics.")
    parser.add_argument("--audit-json", required=True, help="Official audit JSON path.")
    parser.add_argument("--blocked-json", required=True, help="Blocked artifacts review JSON path.")
    parser.add_argument("--output", required=True, help="Output PDF path.")
    parser.add_argument("--title", default="Unified Governance Audit Report")
    args = parser.parse_args()

    audit_json = Path(args.audit_json).expanduser().resolve()
    blocked_json = Path(args.blocked_json).expanduser().resolve()
    out_pdf = Path(args.output).expanduser().resolve()

    if not audit_json.exists():
        raise SystemExit(f"Missing audit JSON: {audit_json}")
    if not blocked_json.exists():
        raise SystemExit(f"Missing blocked review JSON: {blocked_json}")

    audit = load_json(audit_json)
    blocked = load_json(blocked_json)
    build_doc(audit, blocked, out_pdf, args.title)

    print(f"Unified PDF report: {out_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
