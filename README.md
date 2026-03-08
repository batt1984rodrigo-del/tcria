# TCRIA — Legal Evidence Chain-of-Custody and Governance System

TCRIA is a governance gateway for documentary evidence pipelines.

It processes heterogeneous document collections and produces an auditable bundle that records classification, traceability signals, governance gates, and accountability metadata.

Its role is not to write legal pleadings or decide legal theses. It preserves a controlled documentary chain of custody before human legal decision-making.

## Purpose

Legal cases often begin with large collections of mixed documents:

- PDF files
- DOCX files
- notes
- reports
- emails
- drafts
- contextual material

Most tools only extract text or rank files.

TCRIA adds a governance layer so that:

- accusatory narratives are not promoted without accountability
- documentary evidence remains traceable
- responsibility for narrative promotion is explicit
- mixed archives are processed without uncontrolled conclusions

## Why this exists

Document analysis without governance can produce conclusions that are hard to audit.

TCRIA introduces governance gates before narrative promotion. The result is a controlled evidentiary trail that is inspectable by legal, audit, and risk teams.

Quick framing:

```text
Problem: document analysis without governance control
Solution: governance gateway before narrative promotion
Outcome: auditable chain-of-custody bundle (JSON / Markdown / PDF)
```

## Architecture overview

```text
Documents
   ↓
TCRIA Engine
   ↓
Governance Gates
   ↓
Audit Bundle
   ↓
Reports / API / UI
```

## Core concept: documentary chain of custody

```text
document ingestion
        ↓
classification
        ↓
traceability signals
        ↓
governance gates
        ↓
audit bundle
```

This produces a controlled evidentiary trail before human interpretation.

## Features (MVP)

- Scan folders of mixed files: `PDF`, `DOCX`, `TXT`, `MD`
- Classify artifacts as:
  - neutral / context
  - supporting evidence
  - relevant evidence
  - accusatory candidates
- Apply governance gates:
  - `prescriptiveGate`: blocks condemnatory or prescriptive language
  - `complianceGate`: requires explicit accountability metadata in strict mode
  - `traceabilityCheck`: detects dates, references, evidentiary markers, and currency indicators
- Generate outputs: `*.json`, `*.md`, `*.pdf`

Blocked artifacts are not promoted to the official accusation bundle. They can generate a complementary diagnostic report for evidentiary review without narrative promotion.

## Accountability metadata (DecisionRecord)

To promote accusatory content through the compliance gate, a document must include a DecisionRecord header.

Example:

```text
[TCR-IA DECISION RECORD]
responsibleHuman: Rodrigo Baptista da Silva
declaredPurpose: Auditoria documental e organizacao de evidencias para fins juridicos
approved: YES
approvedAt: 2026-03-05
[/TCR-IA DECISION RECORD]
```

This keeps responsibility for narrative promotion human-declared.

## What TCRIA does NOT do

TCRIA intentionally does not:

- generate legal pleadings
- write accusations
- construct legal theses
- produce petitions automatically

Those activities require human legal judgment and responsibility.

## Repository structure

```text
tcria/
├── tcria/
│   ├── ingestion/
│   ├── signals/
│   ├── classification/
│   ├── governance/
│   ├── audit/
│   ├── engine.py
│   └── cli.py
├── api/
│   └── api.py
├── app/
│   └── streamlit_app.py
├── cases/
├── scripts/
└── run_governance_pipeline.py
```

## Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## CLI usage

Legacy compatibility command:

```bash
tcria scan ~/Downloads --strict
```

Modular product engine command:

```bash
tcria product-audit ~/Downloads --strict --out-dir output/audit --output-stem audit
```

Official pipeline mode (existing scripts):

```bash
tcria product-audit ~/Downloads --strict --official-pipeline --output-stem my_case
```

Direct pipeline command (modular engine by default, legacy optional):

```bash
python3 run_governance_pipeline.py --path ~/Downloads --strict --output-stem my_case
python3 run_governance_pipeline.py --path ~/Downloads --strict --legacy-audit-script --output-stem my_case
```

Case workspace flow:

```bash
tcria case init complice
tcria case run complice --strict
tcria investigate complice
```

## API

Run API:

```bash
uvicorn api.api:app --reload
```

Main endpoints:

- `GET /health`
- `POST /audit` (modular engine)
- `POST /audit/official-pipeline` (scripted governance pipeline)

## Web interface

```bash
streamlit run app.py
```

## Outputs

Modular engine run output:

```text
output/audit/
    audit.json
    audit.md
    audit_report.pdf
```

Case workspace output:

```text
cases/<case_id>/
    input/
    audit/
    blocked/
    preparation/
    timeline/
    report/
    case_manifest.json
```

## Roadmap

- move remaining scripts into `tcria/` modules
- add DecisionRecord sidecar support (`file.ext.tcria.json`)
- expand automated tests with golden outputs
- strengthen CI pipelines
- evolve case workspace management

## Summary

TCRIA is not a legal decision engine.

It is a chain-of-custody governance system for legal document collections, designed to ensure evidence and narratives are handled with traceability, accountability, and procedural discipline before human legal action.
