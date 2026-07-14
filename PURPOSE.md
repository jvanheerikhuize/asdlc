<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Purpose — Clean-Slate Rebuild of the Agentic SDLC Framework

This repository is the working home for a from-first-principles redesign of a
governed, agent- and vendor-agnostic **Agentic Software Development Lifecycle
(ASDLC)** framework: a system in which autonomous AI agents carry a software
change from stated intent to production and operation, with governance,
auditability, and DORA / EU AI Act compliance built in rather than bolted on.

The full design brief lives in the knowledge base, verbatim, as the
`brief-s0`…`brief-s9` reference nodes
(`.asdlc/knowledge/nodes/reference/`).
The session-state file that preceded this document was retired once its
content was fully absorbed here (it remains in git history).

**Ground fact set by the owner:** the framework and all consuming repositories
live on **GitHub**. Enforcement reference bindings may therefore target GitHub
primitives, while the framework's contracts stay platform-neutral.

## Where the work stands (2026-07-14, end of session)

1. Brief read and analysed; prior-art repos are not on this machine — design
   proceeds from the brief's §6 summary, as intended.
2. Five clarifying questions raised, researched, and answered below; the
   owner accepted the proposed answers.
3. **All design deliverables (§7.2–7.7) are done** — see
   [docs/design/](docs/design/): `architecture.md`, `decisions.md`,
   `compliance.md`, `agents.md`, `risks.md`, `roadmap.md`. The README indexes
   them. Central reframe: an evidence-state machine — gates are policies over
   signed attestations, platform-enforced; the orchestrator is optional
   ergonomics; three repos (spec / verify / orchestrator) instead of four.
4. This repo was created as `asdlc-rebuild`, then renamed to `asdlc`
   (GitHub redirects the old name). Currently **private**; flip with
   `gh repo edit jvanheerikhuize/asdlc --visibility public` when ready.

**Current step: slice 1 of [docs/design/roadmap.md](docs/design/roadmap.md)
— in progress.** The repo-layout question is decided (D12 in decisions.md):
this repo *is* the spec repo. Done so far (2026-07-14):

- **`spec/` v0.1 exists**: Change Record + manifest schemas, the four slice-1
  predicate schemas over a shared in-toto statement base, the minimal control
  catalogue (QC-01, SC-01), the G4 merge-gate policy
  (`spec/gates/g4-merge.rego`), and four golden evidence bundles
  (`spec/examples/golden/`) pinning G4's behavior (1 pass, 3 fail).
- **Self-check runs**: `python3 spec/tools/check.py` validates schemas +
  golden bundles everywhere and evaluates the Rego policy when `opa` is on
  PATH; `.github/workflows/spec-check.yml` runs both layers in CI (no opa/go
  on the local machine — CI is where the policy is actually exercised).

**spec-check is green in CI** (run 29354999276, 2026-07-14): `opa check`
passes and all four golden bundles evaluate to exactly their expected
allow/deny outcomes — the G4 policy is exercised, not just authored.

**`asdlc-verify` exists and is green** (2026-07-14):
https://github.com/jvanheerikhuize/asdlc-verify — Go CLI with `gate`
(policy evaluation over a prepared input or a Change Record directory) and
`doctor` (manifest preflight, recorded SoD exception). Its CI compiles,
vets, tests, and reproduces all four spec golden-bundle outcomes
(conformance test). v0.1 honesty: only `--dev-unsigned` evidence mode —
DSSE/Sigstore verification is the next verifier milestone; the policy input
shape is final so the gate contract won't change. `testdata/spec-0.1.0/` is
a pinned fixture copy, to be replaced by a tag fetch once spec releases are
tagged.

**Both repos are public and gate-protected** (owner decision, 2026-07-14).
Active branch rulesets on `main` of both repos (no bypass, PR flow forced):
`asdlc` requires the `spec-check` check (ruleset 18946796); `asdlc-verify`
requires `ci` (ruleset 18946806). From this point every change to the
framework flows through its own gates — direct pushes to main are blocked,
including for the owner.

**The GitHub binding is live** (2026-07-14, PRs asdlc-verify#1 + asdlc#2):
the verifier ships as a composite Action; the `g4-gate` workflow detects a
PR's Change Record, produces QC-01/SC-01 verdicts, transcribes
`/asdlc approve <head-sha>` comments from bound release-approvers into
`approval/v1`, evaluates G4 via the verifier (dev-unsigned), and uploads
the evidence bundle as a run artifact. Conventions and their successors:
`bindings/github/README.md`. Owner authorized agent-merge of green PRs in
both repos (solo-maintainer SoD reality, recorded).

**This very text was merged as the first governed change**
(`CR-20260714-dogfood-proof`, PR #3): gate denied pre-approval, passed
after the approval comment, evidence bundle archived on the run.

Slice 1 remaining: (a) add `g4-gate` to the main ruleset's required checks
(the exit-criterion flip); (b) DSSE/Sigstore verification in the verifier,
replacing dev-unsigned; (c) tag spec v0.1.0 and pin the verifier's
fixtures to the tag.

**Knowledge-first documentation is live** (2026-07-14,
CR-20260714-knowledge-architecture): all prose in this repo is generated
from typed knowledge nodes in `.asdlc/knowledge/` by
`spec/tools/scaffold.py`; CI fails on drift. Edit nodes, never the
generated files. See roadmap Priority 0.

**Metrics v1 live** (2026-07-14, CR-20260714-metrics): lead time and
cycle time derived from evidence + git by `spec/tools/metrics.py`;
published per main-push by the `metrics` workflow (job summary + JSON
artifact). Definitions: the `metric-*` knowledge nodes; roadmap
Priority 1. A leftovers registry also exists (`LEFTOVERS.md`, generated)
for owner-triggered sweep changes.

**Brief absorbed into knowledge** (2026-07-14,
CR-20260714-brief-to-knowledge): the original design prompt lives
verbatim as the `brief-s0`…`brief-s9` reference nodes; the loose files
`docs/prompt-clean-slate-rebuild.md` and
`docs/session-continuation-2026-07-14.md` are removed (git history keeps
them). `docs/` now contains only generated documents.

**Metrics dashboard live** (2026-07-14, CR-20260714-metrics-dashboard):
https://jvanheerikhuize.github.io/asdlc/ — deployed to GitHub Pages by
the `metrics` workflow on every main push. See [[metrics-dashboard]].

## Clarifying questions — researched, proposed answers

### Q1. Where must governance be unbypassable?

**Proposed answer: platform-enforced gates, with a cooperative runtime in
front.** The prior art enforces through an MCP orchestrator that agents
*choose* to call — a non-compliant agent routes around it, and an audit trail
of voluntary self-reports is weak supervisory evidence. Since the estate lives
on GitHub, the unbypassable layer binds to GitHub primitives: repository
rulesets and required status checks, the required-reviewer rule (GA Feb 2026),
environment protection rules, and org-level artifact-attestation policies.
A thin, dumb verifier runs as a required check at the merge/deploy boundary and
validates that the evidence bundle exists, is signed, and satisfies policy —
regardless of which agent produced it. The orchestrator remains valuable for
ergonomics, coordination, and recording, but is never the source of truth.

The framework itself stays platform-neutral by defining the *verification
contract* (what evidence must exist, its schema, how it is checked) and
shipping the GitHub binding as the reference implementation; other platforms
are adopter-supplied bindings.

### Q2. How far does the lifecycle reach?

**Proposed answer: full span (intent → operation), unevenly resolved.**
High-resolution design to merge/release; contract-level resolution for deploy
and operate. DORA makes the operate phase non-optional: incident handling
carries hard reporting timelines (initial notification ~4h, intermediate 72h,
final 30d) and resilience testing must be required and recorded as a gate. A
build-time-only framework cannot evidence those obligations.

### Q3. Where does audit evidence live?

**Proposed answer: platform-native attestations plus an adopter-bound
retention export.** Evidence is produced as signed in-toto attestations (DSSE
envelopes, Sigstore signing) attached to commits/artifacts — on GitHub this is
the artifact-attestation store (private repos use GitHub's private Sigstore
instance; no public transparency log; Enterprise keeps attestations in an
internal private database). That is strong for integrity and lineage, but DORA
expects tamper-proof audit data retained ≥5 years — repos get deleted and the
platform store is not a WORM guarantee. So the framework defines an **evidence
export interface**: bundles are mirrored to an append-only retention store the
adopter binds (object-lock storage, private Rekor, or a GRC system).

### Q4. Who are the humans?

**Proposed answer: design standalone and portable, with explicit adapter
seams.** Role separation (product / architecture / security / risk approvers)
is expressed abstractly in the framework's control definitions and mapped, in
the GitHub reference binding, onto CODEOWNERS, required reviewers, and
environment approvals. Nothing assumes an incumbent GRC stack, but control
definitions carry stable IDs so an enterprise can map them into an existing
risk register without tearing anything out.

### Q5. Greenfield or migration?

**Proposed answer: clean slate, no compatibility obligation** — that is the
explicit spirit of the brief. Concepts from the prior art that survive on
merit (classification-driven conditional controls, bounded-retries-then-HALT,
machine-readable manifest as single source of truth, typed controls) are kept
by argument, not by inheritance.

## Research findings the design must account for (July 2026)

- **EU AI Act — timelines moved.** The Digital Omnibus (provisionally agreed
  7 May 2026; Parliament 16 June; Council final approval 29 June 2026) defers
  Annex III high-risk obligations from 2 Aug 2026 to **2 Dec 2027**, and
  Annex I product-regulated systems to 2 Aug 2028. Still active: chatbot
  transparency obligations from Aug 2026; AI-generated-content labelling
  deferred only to 2 Dec 2026. Design consequence: transparency/labelling
  controls are near-term; high-risk conformity machinery has runway but should
  be designed in now.
- **DORA — in force since 17 Jan 2025.** Tamper-proof audit trails with ≥5-year
  retention; formal change management with documented approval; incident
  reporting at 4h/72h/30d; resilience and security testing as recorded gates;
  external models/agents/tools treated as ICT third parties (inventory, SBOM,
  monitoring).
- **MCP is now genuinely vendor-neutral.** Anthropic donated MCP to the Linux
  Foundation's Agentic AI Foundation in Dec 2025 (backed by AWS, Google,
  Microsoft, OpenAI, Bloomberg, Cloudflare). Next spec finalises 28 July 2026
  (stateless core, Extensions, Tasks, authorization hardening). MCP is a safe
  choice as the framework's agent-facing interface without violating
  vendor-agnosticism.
- **GitHub now ships the enforcement primitives natively.** Artifact
  attestations (Sigstore/in-toto) with org-level attestation policies and a
  Kubernetes admission controller; rulesets with required checks and the
  required-reviewer rule (GA Feb 2026); Enterprise AI Controls + agent control
  plane (GA Feb 2026), including push rules protecting `.github/agents/*.md`;
  GitHub Agentic Workflows (public preview June 2026) — markdown-defined,
  agent-agnostic (Copilot/Claude/Gemini/Codex), sandboxed, with gated "safe
  outputs". The reference binding should compose these rather than rebuild them.
- **SLSA / in-toto is the evidence lingua franca.** Provenance as in-toto
  statements in DSSE envelopes, signed by the build platform; policy layers
  (layouts, admission controllers, deploy gates) verify programmatically.
  The framework's evidence schema should be an in-toto predicate family, not a
  bespoke format.

Sources: [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) ·
[GitHub Enterprise Cloud attestations](https://docs.github.com/en/enterprise-cloud@latest/actions/concepts/security/artifact-attestations) ·
[Required-reviewer rule GA](https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/) ·
[Enterprise AI Controls GA](https://github.blog/changelog/2026-02-26-enterprise-ai-controls-agent-control-plane-now-generally-available/) ·
[Agentic Workflows public preview](https://github.blog/changelog/2026-06-11-github-agentic-workflows-is-now-in-public-preview/) ·
[EU AI Act implementation timeline](https://artificialintelligenceact.eu/implementation-timeline/) ·
[Gibson Dunn on the Omnibus deferrals](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/) ·
[Latham & Watkins AI Act update](https://www.lw.com/en/insights/ai-act-update-eu-resolves-to-change-rules-and-extend-deadlines) ·
[JFrog on DORA for software delivery](https://jfrog.com/blog/navigating-dora-compliance-software-development-requirements-for-financial-services-companies/) ·
[DORA audit-trail requirements](https://dorapp.eu/blog/dora-audit-trail-requirements-essential-guidelines/) ·
[MCP 2026-07-28 spec release candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) ·
[MCP — Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol) ·
[in-toto and SLSA](https://slsa.dev/blog/2023/05/in-toto-and-slsa)

## Suggested tech stack (where code is needed)

| Component | Suggestion | Why |
|---|---|---|
| Evidence format | in-toto statements in DSSE envelopes, custom predicate family | Industry lingua franca; verifiable with existing tooling |
| Signing | Sigstore (GitHub `actions/attest` in the reference binding; cosign elsewhere) | Keyless OIDC signing; native on GitHub |
| Schemas / contracts | JSON Schema (2020-12), optionally CUE for authoring | Machine-readable single source of truth; generated human views |
| Verifier | **Go** CLI (single static binary), wrapped as a GitHub Action for the reference binding | sigstore-go / in-toto-golang ecosystem; runs identically in any CI |
| Policy evaluation | OPA/Rego evaluated by the verifier over evidence bundles | Declarative, testable, decoupled from binding |
| Orchestrator | MCP server in **TypeScript** (official SDK) | Most mature SDK; MCP now LF-governed and vendor-neutral |
| Knowledge/memory | In-repo JSON(-LD) documents validated by the schemas | Portable, diffable, low agent-context cost |
| Docs | Generated from the manifest (any static generator) | No hand-maintained duplication |

## Deliverables (brief §7) — all delivered

| § | Deliverable | Location |
|---|---|---|
| 7.1 | Clarifying questions + answers | this file, above |
| 7.2 | Proposed architecture | [docs/design/architecture.md](docs/design/architecture.md) |
| 7.3 | Key decisions and trade-offs vs prior art | [docs/design/decisions.md](docs/design/decisions.md) |
| 7.4 | DORA / EU AI Act mapping | [docs/design/compliance.md](docs/design/compliance.md) |
| 7.5 | Subagent and orchestration model | [docs/design/agents.md](docs/design/agents.md) |
| 7.6 | Risks, failure modes, open questions | [docs/design/risks.md](docs/design/risks.md) |
| 7.7 | Incremental build plan | [docs/design/roadmap.md](docs/design/roadmap.md) |
