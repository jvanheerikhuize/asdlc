# Incremental build plan (brief §7.7)

Ordering principle: land the **enforcement spine first** (it is what makes
everything else true), dogfood immediately on these repos themselves, and
sequence regulation-serving mechanisms DORA-first (in force since Jan 2025)
while reserving the AI Act's shapes from day one (Annex III obligations apply
Dec 2027).

## Slice 1 — Walking skeleton (the first thing that is real)

- `asdlc-spec` v0.1: Change Record format, `change-intent/v1`,
  `classification/v1`, `control-verdict/v1`, `approval/v1` predicates; a
  minimal control catalogue (one QC, one SC); **one gate: G4 (merge)** as a
  Rego policy.
- `asdlc-verify` v0.1: validate signatures + evaluate G4 + emit verdict;
  GitHub Action wrapper; `doctor` preflight.
- Reference binding on these repos: required status check + required
  reviewer; approval-transcription workflow.
- **Dogfood**: every change to spec/verify/orchestrator flows through its own
  G4 from this point on. The framework governs its own construction —
  the first audit trail produced is its own.

*Exit criterion*: a PR without valid evidence cannot merge into the
framework's own repos, and the evidence DAG for a merged change is
reconstructable with one CLI command.

## Slice 2 — Authority and fail-safe semantics

- Authority matrix + role bindings in `asdlc.yaml`; signer-identity checks.
- `waiver/v1`, `halt/v1`; monotonic-verdict enforcement (no downgrade).
- Solo-maintainer SoD-exception recording.
- Classification-driven control-set computation (the depth throttle) with the
  fuller control catalogue (QC/SC/RC/GC; AC/DC schemas defined but inactive).

*Exit criterion*: a HALTed change is provably un-mergeable except via new
work or an authorized, recorded waiver.

## Slice 3 — The easy path

- `asdlc-orchestrator` v0.1 (TypeScript MCP server): `change.*`,
  `controls.required`, `evidence.record`, `gate.check`, `approval.request`,
  `playbook.get`; retry counting → HALT.
- First personas (implementer, security-engineer, test-engineer) and
  deterministic squad composition.
- Phase playbooks as served guidance.

*Exit criterion*: an off-the-shelf agent connected only to the MCP server
completes a governed change end-to-end to merge, with a weaker-agent run and a
no-orchestrator run producing byte-equivalent gate outcomes.

## Slice 4 — Release, operate, and the DORA spine

- G5 (environment protection + rollback evidence + `deployment/v1`) and G6
  (`incident/v1` with the 4h/72h/30d clock fields, `learning/v1`).
- **Retention exporter** (scheduled workflow → adopter-bound append-only
  store; release-assets default, object-lock reference).
- Generated human trace report (the supervisory view over the DAG).

*Exit criterion*: a simulated incident produces a complete, exportable,
clock-stamped record; deleting the repo does not delete the evidence.

## Slice 5 — Onboarding and memory

- P0 onboarding: classification baseline, third-party/model inventory
  (SBOM-linked), role bindings; G0 checks.
- Knowledge graph schema + `knowledge.query/propose`; `learning/v1` feeds it.
- AC/DC control activation (AI-contribution disclosure at P3 lands here —
  content-labelling duties bite Dec 2026, ahead of the high-risk battery).

## Slice 6 — Hardening and portability proof

- Conformance test suite: golden evidence bundles per gate (doubles as the
  policy-bug defense, R3).
- Second binding (skeletal local-git/other-CI) to prove the platform seam.
- Verifier SLSA provenance + digest-pinning policy (verify-the-verifier, R4).
- Approval-surface work: exception-oriented summaries (anti-rubber-stamp, R2).
- Persona evaluation harness (open question 5) if warranted by dogfood data.

## What is deliberately *not* scheduled

Multi-repo change federation, evidence privacy tiers, and regulator-format
incident submission (open questions 1, 2, 4) — each needs dogfood evidence
before design, and none blocks the spine.
