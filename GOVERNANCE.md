# Governance

## Purpose

TCRIA is a governance gateway for documentary evidence processing.

Its output is designed to preserve traceability, accountability, and auditability before any human legal conclusion is promoted outside the repository.

## Core Guardrails

1. Official outcomes are derived from the governed audit bundle, not from complementary narrative layers.
2. Complementary layers may summarize, prioritize, and organize evidence, but they do not promote blocked artifacts into approved outcomes.
3. Accountability metadata remains mandatory for strict-mode promotion of accusatory material.
4. Human review is required before any petition, accusation, or legal thesis is finalized.

## Governance Gates

- `prescriptiveGate`: blocks condemnatory or prescriptive language that would bypass human legal responsibility.
- `complianceGate`: requires explicit accountability metadata such as `responsibleHuman`, `declaredPurpose`, and `approved`.
- `traceabilityCheck`: evaluates whether the artifact contains enough traceable anchors to support controlled evidentiary handling.

## Release Governance

- `v1.0.0-legal-baseline` marks the first formal baseline of the auditable legal-governance model.
- `v1.0.0-legal-governance` is maintained as an alias for that same baseline to reflect the review wording used during PR discussion.
- `v1.1.0-diagnostic-layer` marks the addition of complementary diagnostic and case-preparation layers without changing the official governance posture.

## Operational Rule

If a new layer changes prioritization, reporting, or case preparation behavior, it must state explicitly whether the change is complementary-only or whether it modifies an official audit outcome.
