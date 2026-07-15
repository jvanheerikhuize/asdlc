<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Key decisions and trade-offs (brief §7.3)

Each decision states the divergence from (or retention of) the prior art in
the brief's §6, and the trade-off accepted.

## D1 — Declarative gates over prescriptive playbooks **(diverge)**

Prior art: procedural playbooks + binding contracts per stage. This design:
gates are policies over evidence; playbooks are optional guidance.

*Why*: contracts binding agents to procedure are unenforceable against a
non-compliant agent and over-constrain a compliant one. Evidence requirements
are enforceable (a required check either passes or doesn't) and leave agents
free to work in whatever shape their vendor gave them — which is what
agent-agnosticism actually requires. *Trade-off*: less step-by-step hand-holding
for weak agents; mitigated by the orchestrator serving playbooks as guidance.

## D2 — Enforcement at the platform boundary, orchestrator demoted **(diverge)**

Prior art: the MCP orchestrator is the runtime that drives and gates the
lifecycle. This design: GitHub rulesets / required checks / environment
protection are the gates; the orchestrator is optional ergonomics.

*Why*: an audit trail assembled from voluntary self-reports through a service
an agent can bypass is weak supervisory evidence. A required check cannot be
bypassed by any agent, from any vendor, however misaligned. *Trade-off*: the
reference binding is GitHub-coupled. Contained by keeping every contract
(schemas, policies, predicate types) platform-neutral and the verifier a
portable CLI — a GitLab binding is configuration plus a thin wrapper, not a
redesign.

## D3 — Three repositories, not four **(diverge)**

Prior art: lifecycle / governance / orchestrator / swarm. This design:
**spec** (all governance content, personas included) / **verify** (enforcement
code) / **orchestrator** (optional ergonomics code).

*Why*: lifecycle definitions, governance references, and persona definitions
are all versioned *content* consumed together — splitting them across three
repos created version-skew risk with no isolation benefit. Code is split from
content because it releases on a different cadence and the verifier must be
independently attestable. *Trade-off*: a fatter spec repo; acceptable because
it is all generated-view content with one semver line.

## D4 — Evidence as in-toto attestations, not bespoke records **(diverge)**

Prior art: manifest-driven documents and records in framework-specific shapes.
This design: every record is an in-toto statement in a DSSE envelope, signed
via Sigstore, in a custom predicate family.

*Why*: tamper-evidence, signer identity, and artifact binding come free from
an ecosystem regulators and platforms already understand (SLSA, GitHub
attestations, admission controllers), instead of being reimplemented and then
defended in an audit. *Trade-off*: DSSE/Sigstore tooling is a real dependency;
accepted since it is open, multi-vendor, and Linux-Foundation-governed.

## D5 — Human decisions captured from platform events **(new)**

Approvals are enforced by the platform (PR review, environment approval) and
transcribed into signed `approval/v1` attestations by a trusted workflow —
rather than asking humans to sign attestations directly.

*Why*: humans will not run cosign; they will click "Approve" where they
already work. Enforcement must live where the human actually acts, and the
durable record must be derivable from it. *Trade-off*: the transcription
workflow becomes trusted infrastructure; it is small, spec-owned, and its own
builds are attested.

## D6 — Classification-driven conditional depth **(keep, from prior art)**

Classify risk, data sensitivity, and AI usage once at intent; the verifier
*computes* the required-control set from it. Kept because it is the correct
answer to the central adoption problem — uniform heavyweight governance gets
bypassed, uniform lightweight governance fails audits. Hardened here: the
computation is deterministic policy, so control scoping is never a judgment
call made under delivery pressure, and a misclassification is itself a
recorded, reviewable artefact (the classification attestation names its
signer).

## D7 — Bounded retries → HALT with monotonic verdicts **(keep, hardened)**

Kept from prior art. Hardened: HALT and verdicts are attestations, and the
verifier enforces that they are superseded only by new work or an authorized
waiver — the no-silent-downgrade rule is machine-checked rather than asserted.

## D8 — Typed control taxonomy **(keep)**

QC/SC/RC/AC/DC/GC is retained on merit: the types map cleanly onto distinct
regulatory regimes (SC/RC→DORA, AC/DC→AI Act, GC→both), distinct authority
roles, and distinct activation logic. Stable control IDs are kept so
enterprises can map controls into an existing risk register (adapter seam).

## D9 — Machine-readable single source of truth **(keep)**

The prior art's strongest idea. Retained and extended: the spec is the SSoT
for *all* governance content, human documents are generated, and consuming
repos interact with exactly one manifest file (`asdlc.yaml`).

## D10 — MCP as the agent-facing interface **(keep, now vendor-neutral)**

Prior art chose MCP when it was an Anthropic protocol; since December 2025 it
is Linux-Foundation-governed with all major vendors aboard. What was a
pragmatic bet is now the compliant choice — kept, with the July 2026 spec's
Tasks primitive as the natural fit for long-running gated phases.

## D11 — Full lifecycle span, unevenly resolved **(diverge)**

Prior art reserved deployment and observability. This design specifies them as
first-class contracts (deployment/incident/learning predicates, G5/G6 gates)
with thin reference bindings, because DORA — in force since January 2025 —
puts hard obligations (incident clocks, resilience testing, rollback evidence)
precisely there. *Trade-off*: contract-level resolution means adopters do more
binding work post-merge; better an honest thin contract than a pretended deep
implementation.

## D12 — This repo *is* `asdlc-spec` (decided at slice 1 start, 2026-07-14)

The open question from PURPOSE.md, resolved: the spec repo is not created
separately — `asdlc` becomes it. The design docs already here are exactly the
human views the spec carries, and a governance-content repo with the design
rationale in `docs/` and the machine-readable truth in `spec/` is the intended
shape. `asdlc-verify` still starts as its own repo when the Go code lands
(D3's code/content split stands). *Trade-off*: the repo name doesn't say
"spec"; acceptable — it is the framework's front door.

## D13 — Knowledge content is repo-scoped; the mechanism is spec-owned (2026-07-14)

Raised by the owner after the knowledge-first migration: should the
knowledge architecture propagate to `asdlc-verify` (and future repos), or
stay single-sourced here?

Decision, in two halves:

- **The mechanism is single-sourced in the spec repo.** The node and
  doc-manifest schemas (`spec/knowledge/`) and the scaffolder
  (`spec/tools/scaffold.py`) are spec content; other repos consume them
  from a **pinned spec tag**, never copy them. A copied schema or tool is
  the version-skew failure D3/D9 exist to prevent.
- **Knowledge *content* is repo-scoped.** Each consuming repo's
  `.asdlc/knowledge/` describes that repo and nothing else. Framework
  knowledge (decisions, risks, compliance, roadmap) lives here,
  permanently, and is **never mirrored** into another repo — two knowledge
  bases describing the same framework would disagree within a month.
  Cross-repo references cite a node id or URL instead of restating.

Consequences: `asdlc-verify` gets nothing now; its README is regenerated
from its own (small) knowledge base only when the fetch-pinned-spec-in-CI
path is built — the same path its golden fixtures already need (replacing
the copied `testdata/spec-0.1.0/`), which turns that follow-up into the
first proof that a consuming repo can use spec tooling from a version pin.
*Trade-off*: until then, verify's README stays hand-maintained; accepted
for one small file over premature plumbing.

## D14 — Change Record IDs carry a per-date sequence (2026-07-14)

Raised by the owner after one day produced eight Change Records: the id
scheme `CR-<yyyymmdd>-<slug>` gives no way to tell, from the id alone,
which record on a given date came first.

Decision: from spec 0.5.0 the id is **`CR-<yyyymmdd>-<seq>-<slug>`** —
a 3-digit, zero-padded, per-date sequence minted at open time
(`CR-20260714-009-change-numbering` is the first). The future change
scaffolder ([[leftover-change-scaffolder]]) mints the next number by
listing `.asdlc/changes/` for the date; until it exists, whoever opens
the record does the same by hand.

The eight pre-0.5.0 records are **grandfathered, never renamed**:
their ids are embedded in immutable evidence statements (D4 — renaming
would falsify the record), in merge-commit messages, and in PR titles.
Their order is still visible: the metrics dashboard numbers every
merged change in merge order (derived from git, never stored — same
philosophy as the metrics themselves).

*Trade-off*: two ordering numbers coexist — the minted per-date seq
(stable at open time) and the dashboard's merge-order number (derived,
can differ when changes merge out of open order). Accepted: the seq
answers "which was opened first", the dashboard answers "which landed
first", and both questions are real.

## D15 — Agent context is purged between changes (2026-07-14)

The first real read of the metrics dashboard showed lead and cycle time
climbing across the day's successive changes: the agent session carried
the accumulated context of every earlier change into the next one
(visible in [[metric-token-usage]] — 4.8M tokens on the day's last
change). This is [[risk-r6-evidence-volume-vs-agent]] observed in
practice, on the framework's own repo.

Decision, owner-directed: **one change ≈ one context.** Agent context
is purged after every completed change instead of accumulating across
a session.

Enforcement lives in the operator's harness (Claude Code, 2026-07-14):
forced auto-compaction at a 100k-token window with precomputed
summaries, plus an end-of-turn reminder to compact or clear. The
framework's part is observability, not enforcement: the token metric
and the dashboard are what made the accumulation visible, and what
will show whether the purge policy bends the curve.

*Trade-off*: a purge discards session context that the next change
might have reused; recovering it costs re-reading knowledge nodes.
Accepted — that is exactly what the persistent knowledge base is for
(D9, knowledge-first): context worth keeping belongs in nodes, not in
a session transcript.
