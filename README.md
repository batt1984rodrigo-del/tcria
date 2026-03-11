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

Optional OpenAI integration:

```bash
cp .env.example .env
# edit .env and set your real OpenAI key
```

Example `.env`:

```bash
OPENAI_API_KEY="sk-..."
TCRIA_OPENAI_MODEL="gpt-4.1-mini"
TCRIA_ALLOWED_INPUT_ROOTS="/srv/tcria/cases,/srv/tcria/uploads"
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
- `GET /capabilities`
- `POST /audit` (modular engine)
- `POST /audit/official-pipeline` (scripted governance pipeline)
- `GET /responses/audit-types` (available Responses API prompt presets)
- `POST /responses/audit` (modular audit + Responses API analysis)
- `POST /audit/openai-summary` (backward-compatible alias to `/responses/audit`)
- `POST /cases/init` (initialize case workspace)
- `POST /cases/run` (run official case pipeline + blocked/preparation/timeline layers)
- `POST /cases/investigate` (generate final investigation report from case artifacts)
- `POST /investigations/full-run` (initialize case if needed, run full investigative pipeline, return outputs, optional Responses API analysis)
- `POST /conclusions/from-bundle` (build gateway-style final conclusions from an audit bundle)
- `POST /gateways/legacy-accusation-audit` (run the legacy civil/criminal accusation gateway script)

Security defaults for API usage:

- Input paths are restricted to `TCRIA_ALLOWED_INPUT_ROOTS` (comma-separated absolute paths).
- If `TCRIA_ALLOWED_INPUT_ROOTS` is not set, only the server current working directory is allowed.
- Request payload supports scan limits: `max_files` and `max_total_bytes`.

Example:

```bash
uvicorn api.api:app --host 127.0.0.1 --port 8000
```

Responses API preset example:

```bash
curl -X POST http://127.0.0.1:8000/responses/audit \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/srv/tcria/cases/demo",
    "strict": true,
    "output_stem": "demo_audit",
    "include_pdf": false,
    "audit_type": "restitution_accountability",
    "model": "gpt-4.1-mini",
    "user_context": "Explain this restitution bundle for an accountability reviewer."
  }'
```

List available audit types:

```bash
curl http://127.0.0.1:8000/responses/audit-types
```

Case workspace example:

```bash
curl -X POST http://127.0.0.1:8000/cases/init \
  -H "Content-Type: application/json" \
  -d '{"case":"demo_case","root":"cases"}'

curl -X POST http://127.0.0.1:8000/cases/run \
  -H "Content-Type: application/json" \
  -d '{"case":"demo_case","root":"cases","strict":true}'

curl -X POST http://127.0.0.1:8000/cases/investigate \
  -H "Content-Type: application/json" \
  -d '{"case":"demo_case","root":"cases"}'
```

Full investigation run example:

```bash
curl -X POST http://127.0.0.1:8000/investigations/full-run \
  -H "Content-Type: application/json" \
  -d '{
    "case":"demo_case",
    "root":"cases",
    "strict":true,
    "paths":["/srv/tcria/cases/demo_case/input"],
    "top_k":10,
    "audit_type":"civil_criminal_investigative",
    "analyze_with_openai":true,
    "model":"gpt-4.1-mini"
  }'
```

Gateway conclusions example:

```bash
curl -X POST http://127.0.0.1:8000/conclusions/from-bundle \
  -H "Content-Type: application/json" \
  -d '{"bundle_json_path":"output/audit/audit_strict.json"}'
```

Legacy accusation gateway example:

```bash
curl -X POST http://127.0.0.1:8000/gateways/legacy-accusation-audit \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/srv/tcria/cases/civil_or_criminal_bundle",
    "strict": true,
    "output_dir": "output/audit",
    "output_stem": "legacy_gateway_run"
  }'
```

## Web interface

```bash
streamlit run app.py
```

If `OPENAI_API_KEY` is configured, the Streamlit app can run preset Responses API analyses after the audit completes.

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
