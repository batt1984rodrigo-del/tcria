# TCRIA

legal-tech
document-analysis
forensic-ai

**TCRIA** is a *legal evidence governance scanner*: it ingests a folder of files and produces an audit bundle
(JSON + Markdown + PDF) with *accusation detection*, *traceability signals*, and *governance gates*.

## Why this exists
Most document analyzers extract text and rank files.
TCRIA adds a **governance layer** (gates) so accusatory content does not “pass” unless it carries accountability
metadata (DecisionRecord) and avoids prescriptive/condemnatory language.

## Features (MVP)
- Scan a folder of mixed files (PDF/DOCX/TXT/MD)
- Classify: neutral/context, supporting evidence, relevant evidence, accusatory candidates
- Gates:
  - `prescriptiveGate` (blocks condemnatory language)
  - `complianceGate` (requires DecisionRecord fields in strict mode)
  - `traceabilityCheck` (evidence markers, dates, currency, etc.)
- Outputs: `*.json`, `*.md`, `*.pdf`

## Install (dev)
From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## CLI usage
Run from the repo root (where your existing scripts live):

```bash
tcria scan ~/Downloads -o output/audit --strict
```

If your script is elsewhere:

```bash
tcria scan ~/Downloads --script path/to/audit_accusation_bundle_with_tcr_gateway.py
```

## Web UI (one file)
```bash
streamlit run app.py
```

## DecisionRecord (to avoid compliance blocks in strict mode)
Add a header to the top of accusatory documents:

```text
[TCR-IA DECISION RECORD]
responsibleHuman: Rodrigo Baptista da Silva
declaredPurpose: Auditoria documental e organização de evidências para fins jurídicos
approved: YES
approvedAt: 2026-03-05
[/TCR-IA DECISION RECORD]
```

## What to do next (tomorrow plan)
1. Move repo scripts into `tcria/` as modules (keep CLIs stable).
2. Add sidecar DecisionRecord support (`file.ext.tcria.json`).
3. Add tests (golden outputs) + GitHub Actions.
4. Add a small “case workspace” concept (inputs + outputs + config).
