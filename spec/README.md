<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# asdlc spec v0.1 (slice 1 — walking skeleton)

The machine-readable single source of truth. Human documents are views over
these files; when they disagree, these files win.

| Path | What it defines |
|---|---|
| `manifest.schema.json` | `asdlc.yaml` — the one file a consuming repo carries |
| `change-record.schema.json` | the Change Record, the unit of governance |
| `predicates/statement.base.schema.json` | the in-toto statement envelope all evidence shares |
| `predicates/*.v1.schema.json` | the four slice-1 evidence predicate types |
| `controls/catalogue.yaml` | the typed control catalogue (slice 1: QC-01, SC-01) |
| `gates/g4-merge.rego` | the G4 (merge) gate policy |
| `examples/golden/` | evidence bundles that MUST pass / MUST fail G4 — the policy's conformance fixtures |

## Slice-1 scope notes

- **Predicate type URIs** are versioned identifiers under
  `https://github.com/jvanheerikhuize/asdlc/spec/predicates/…` — identifiers,
  not resolvable endpoints (in-toto convention).
- **Signatures**: evidence travels as in-toto statements; DSSE/Sigstore
  signature verification is the verifier's job (`asdlc-verify`). The gate
  policy receives statements the verifier has already
  signature-checked, annotated under `_meta` (digest, signer identity, role,
  verified flag). Golden bundles model that post-verification shape.
- **Only G4 (merge) exists.** Other gates, the waiver/halt predicates, and the
  full authority matrix are slice 2+ (see `../docs/design/roadmap.md`).
- Evidence for a change lives at `.asdlc/changes/<change-id>/` in the
  consuming repo: `change.json` plus `evidence/*.json`.
