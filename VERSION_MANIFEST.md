# Version Manifest

## Release Line

| Version | Type | Meaning |
| --- | --- | --- |
| `v1.0.0-legal-baseline` | tag | First formal baseline of the auditable legal-governance model |
| `v1.0.0-legal-governance` | tag alias | Review-aligned alias for the same baseline release |
| `v1.1.0-diagnostic-layer` | tag | Complementary diagnostic, preparation, timeline, and investigation layers |

## Notes

- `v1.0.0-legal-governance` should reference the same commit as `v1.0.0-legal-baseline`.
- Complementary layers introduced after the baseline must not be described as changing official audit outcomes unless the governance gates themselves changed.
- The repository README, governance policy, and release tags should stay aligned when naming a formal milestone.
