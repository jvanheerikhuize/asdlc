<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Incremental build plan (brief §7.7)

Ordering principle: land the **enforcement spine first** (it is what makes
everything else true), dogfood immediately on these repos themselves, and
sequence regulation-serving mechanisms DORA-first (in force since Jan 2025)
while reserving the AI Act's shapes from day one (Annex III obligations apply
Dec 2027).

## Priority 0 — Knowledge-first documentation (owner directive, 2026-07-14)

All prose in this repo is maintained as typed knowledge nodes under
`.asdlc/knowledge/` (schemas: `spec/knowledge/`); every human-readable
document — README, PURPOSE, the design docs — is **generated** from them by
`spec/tools/scaffold.py`, and `spec-check` fails CI when a generated doc
drifts from its knowledge. Rationale: the docs folder was prose-as-context
for agents; nodes make each decision, risk, obligation, and status fact
individually addressable (low context cost, brief §8), while humans keep
full documents as views — D9 applied to the framework's own words.

Delivered in the first cut (CR-20260714-knowledge-architecture): node +
doc-manifest schemas, the scaffolder with `--check` CI gate, and the full
decomposition of README, PURPOSE, and all six design docs (56 nodes).
Follow-ups, in later slices: bring `spec/README.md`,
`bindings/github/README.md`, and `asdlc-verify`'s README under
generation — the latter from its own repo-scoped knowledge via a
pinned spec tag (see D13); enrich typed links between
nodes; serve nodes over the orchestrator's `knowledge.query` (slice 3);
join generated evidence-trace reports to the same view layer (slice 4).

*Exit criterion*: editing any generated `.md` directly is caught by CI, and
an agent can answer "why does decision D2 exist" by reading one node
instead of one document.

## Priority 1 — Metrics over the evidence DAG (owner directive, 2026-07-14)

The framework produces a timestamped evidence DAG for every change —
metrics are **views over that DAG, computed on demand, never separately
tracked** (the same single-source move as D9). First two, per owner
directive: [[metric-lead-time]] and [[metric-cycle-time]].

Delivered in the first cut (CR-20260714-metrics): the metric definitions
as knowledge nodes, `spec/tools/metrics.py` (markdown/JSON, computed from
evidence + git history), and a `metrics` workflow that publishes the
report to the run's job summary and a JSON artifact on every push to
main. Second cut (CR-20260714-metrics-dashboard): a self-contained
dashboard ([[metrics-dashboard]]) deployed to GitHub Pages per main push
— grouped lead/cycle bars, median tiles, table view, light/dark,
validated palette. Third cut (CR-20260714-token-metric):
[[metric-token-usage]] — `agent-usage/v1` evidence self-reported from
the agent harness's transcript, with its own chart, tile, and table
column.

Follow-ups, as the evidence grows richer: **approval latency**
(gate-deny to approval comment — makes rubber-stamping drift visible,
feeding R2) and **waiver rate** (feeding R8) once waivers exist
(slice 2); per-gate durations; lead time extended to the deploy boundary
at G5; publication into the retention store / dashboards (slice 4).

## Priority 2 — Metrics integrity (owner directive, 2026-07-15)

Owner audit (2026-07-15) of [[roadmap-priority-1-metrics]]'s delivered
metrics found the dashboard reads as wrong even though each number is
individually computed as designed — three distinct defects, all ahead of
everything else on the roadmap:

1. **Token-usage evidence collection is broken for the current workflow.**
   `bindings/claude-code/usage.py`'s `newest_transcript()` hardcodes the
   session-transcript directory as `~/.claude/projects/-home-jerry-Repos`,
   but every change since the worktree-per-change convention took hold
   lives under a different, worktree-qualified directory name. Result: 10
   of 12 Change Records — including the entire 2026-07-15 leftover
   sweep — have no `usage.json` at all, leaving the dashboard's token
   totals built from a 2-row, non-random, earliest-day-only sample. The
   absence is silent (no CI hook calls `usage.py`; nothing fails), and
   [[metric-token-usage]]'s own caveat misattributes the gap to "predates
   the predicate" rather than a live collection bug.
2. **Where token evidence does exist, it isn't scoped to the change.**
   `cache_read_input_tokens` is summed across every transcript line inside
   the window, and Claude Code re-reads the full accumulated session
   context from cache on every turn — so the total scales with turns ×
   accumulated context, not with work actually done for that change. The
   two recorded rows show this directly: cache-read tokens more than
   double between them purely from context growth, not effort.
3. **Lead/cycle time charts share one linear axis across all rows.**
   `render_html()` derives `vmin_m`/`vmax_m` from every merged row's raw
   lead and cycle time, so the acknowledged bootstrap negative-time rows
   (~-42 min, see [[metric-lead-time]]'s v1 caveat) and a genuine
   overnight-gap row (~+1020 min, `CR-20260714-009-change-numbering`)
   stretch the axis to a ~1060-minute span. The other 9 of 12 rows, all
   within roughly ±6 minutes, render as slivers near-indistinguishable
   from zero — the chart looks broken even though each bar's underlying
   value is arithmetically correct. Separately, cycle time as defined
   doesn't distinguish active work from idle/overnight pauses, so a
   change merged the next afternoon scores ~170x "slower" than one merged
   promptly regardless of actual effort.

None of these are errors in `collect()`'s date arithmetic or in the
`window.from == opened_at` token-window definition — both verified
correct against the evidence on disk. The defects are in what feeds the
computation (broken evidence collection) and in how correct numbers are
presented (a shared axis and a token total with no per-change
normalization). *Exit criterion*: `usage.py` locates the right transcript
for any worktree session without a manual `--transcript` flag, every
merged Change Record after that fix carries usage evidence, the token
metric is normalized to a work-scoped figure (not cumulative cache reads),
and the lead/cycle chart either splits or clips outliers so the common
case stays legible.

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
