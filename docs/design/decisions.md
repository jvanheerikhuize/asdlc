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
