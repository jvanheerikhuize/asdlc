<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Architecture (brief §7.2)

## The central reframe: an evidence-state machine, not a process playbook

The prior art models the lifecycle as a sequence of *activities* (playbooks per
stage, contracts binding agents to procedure). This design inverts that: the
framework governs **states of evidence**, not sequences of work.

- The unit of governance is a **Change Record** — one governed change, from
  intent to operation, identified by a stable ID.
- A Change Record accumulates **signed attestations** (in-toto statements in
  DSSE envelopes) as work happens: intent, classification, design decisions,
  control verdicts, approvals, deployments, incidents.
- A **phase boundary is a gate, and a gate is a policy** (Rego) evaluated over
  the Change Record's attestation set. The gate does not care *how* the
  evidence was produced — by one agent, a swarm, or a human — only that it
  exists, is validly signed by an authorized identity, and satisfies policy.

This is what makes the framework agent- and vendor-agnostic *by construction*:
there is no procedure to comply with, only evidence to produce. Playbooks
survive — but demoted to *guidance* served by the orchestrator (the easy path),
never enforcement.

## Components (three repositories, down from four)

### 1. `asdlc-spec` — the governance content (the single source of truth)

Machine-readable, semver-versioned definitions; human documents are generated,
never hand-maintained. Contains:

- **Lifecycle definition** — phases, gates, and the policy for each gate.
- **Artefact schemas** — JSON Schema (2020-12) for every artefact type.
- **Control catalogue** — typed controls (QC quality · SC security · RC risk ·
  AC AI · DC data · GC governance), each with a stable ID (`SC-03`), the
  evidence predicate it requires, an **activation condition** (an expression
  over the classifications), the gate where it is checked, and the role
  authorized to waive it.
- **Evidence predicate family** — the in-toto predicate types (see below).
- **Authority matrix** — which role may sign which predicate type at which
  phase; the machine-readable form of "separation of authority".
- **Persona definitions** — subagent roles as Markdown + YAML frontmatter
  (aligned with the `.github/agents/*.md` convention; see `agents.md`).
- **Knowledge-graph schema** and onboarding baseline templates.

Consuming repositories pin a spec version; governance upgrades are explicit,
reviewable diffs.

### 2. `asdlc-verify` — the enforcement point

A Go CLI (single static binary) that, given a Change Record's evidence bundle
and a pinned spec version:

1. validates every attestation's signature and signer identity (Sigstore),
2. checks signer identity against the authority matrix and role bindings,
3. computes the **required-control set** from the classification attestations
   (deterministically — same inputs, same controls),
4. evaluates the gate's Rego policy over the evidence,
5. emits a verdict — itself an attestation.

Shipped wrapped as a GitHub Action for the reference binding, but runnable
identically in any CI. This is the *only* component that must be trusted, so it
is small, dumb, and attests its own builds (SLSA provenance; see `risks.md`).

### 3. `asdlc-orchestrator` — the ergonomics layer (optional)

A TypeScript MCP server that makes the governed path the easy path: drives
agents through phases, composes squads from personas, serves playbook guidance,
counts retries, records evidence via the verifier's signing flow, and requests
human approvals. **Optional by design**: a bare agent with the CLI and the spec
can complete a fully governed change. The orchestrator can never open a gate.

### The consuming repository

Carries exactly one framework file and one directory:

- **`asdlc.yaml`** — the manifest: pinned spec version, repo-level
  classification baseline, role→identity bindings, binding configuration
  (which gates map to which platform primitives), retention-export target.
- **`.asdlc/`** — Change Records, evidence bundles, knowledge graph.

## Lifecycle: seven evidence states

| Phase | Evidence that must exist to leave it (gate) |
|---|---|
| **P0 Onboard** (once per repo) | classification baseline; third-party/model inventory; role bindings (G0) |
| **P1 Intent** | change-intent; per-change classification (risk, data, AI) (G1) |
| **P2 Design** | design decisions; threat model / DPIA / AI impact **at the depth the classification activates** (G2) |
| **P3 Build** | SLSA build provenance; AI-contribution disclosure (G3) |
| **P4 Verify** | control verdicts for the full required-control set; human review approval (G4 = merge boundary) |
| **P5 Release** | release approval; rollback plan; deployment record (G5 = deploy boundary) |
| **P6 Operate** | monitoring confirmation; incident records if any; post-incident learning (G6 = closure) |

Classification at P1 is the *depth throttle*: a low-risk, no-data, no-AI change
activates a minimal control set and flows through gates almost frictionlessly;
a high-risk AI change activates the full battery. Same lifecycle, different
weight — governance depth is a computed property, never a judgment call made
under delivery pressure.

## Where enforcement actually bites (GitHub reference binding)

| Gate | Unbypassable primitive |
|---|---|
| G4 (merge) | required status check (verifier) + required-reviewer ruleset rule |
| G5 (deploy) | environment protection rules: required reviewers + verifier check |
| Evidence integrity | artifact attestations, org-level attestation policies |
| Persona/spec integrity | push rules protecting `.asdlc/` policy paths and `.github/agents/*.md` |
| G1–G3 | verifier checks at G4 that earlier-phase evidence exists and predates later evidence (phase ordering is enforced *retrospectively but unbypassably* at the first platform boundary) |

G1–G3 deserve honesty: nothing physically stops an agent writing code before
declaring intent. What the platform *does* stop is any of that work landing —
G4 requires the full evidence chain in correct causal order (attestation
timestamps and subject digests), so skipping early gates produces work that
cannot merge. Enforcement is placed where the platform is strong instead of
pretending the framework can police an agent's local working tree.

## Evidence model

Predicate family (in-toto statement types, subjects are commit SHAs or
artifact digests):

`change-intent/v1 · classification/v1 · design-decision/v1 ·
control-verdict/v1 · approval/v1 · waiver/v1 · halt/v1 · deployment/v1 ·
incident/v1 · learning/v1`

- **CI-produced evidence** is signed keylessly via the platform's OIDC
  identity (GitHub Actions → Sigstore).
- **Human decisions** are captured where the platform enforces them (PR
  review, environment approval) and *transcribed* into `approval/v1`
  attestations by a trusted required workflow — the platform event is the
  enforcement, the attestation is the durable, portable record.
- **Traceability spine**: every attestation carries the Change Record ID and
  references its parent attestations, forming a DAG from which the complete
  history — which controls fired, their verdicts, who approved what, artefact
  lineage — is mechanically reconstructable.
- **Retention**: evidence lives in the platform attestation store *and* is
  exported on a schedule to an adopter-bound append-only store (object-lock
  storage, private Rekor, or a GRC system) to satisfy supervisory retention
  (≥5 years) independent of repository lifetime.

## Fail-safe control flow

- Retries are counted by the orchestrator (cooperative); exhaustion produces a
  `halt/v1` attestation.
- A HALT **hard-closes the gate**. The verifier enforces monotonicity: a
  failed control verdict or HALT can only be superseded by (a) a new verdict
  on a *new commit*, or (b) a signed `waiver/v1` from the role the authority
  matrix authorizes — never overwritten, never downgraded, never silently
  routed around. Defect routing backwards across a phase boundary is a human
  decision recorded as an attestation.

## Separation of authority

Roles (intent-owner, design-authority, security-reviewer, risk-officer,
release-approver, incident-manager) are spec-defined. The authority matrix
says which role signs what, when. The consuming repo's manifest binds roles to
identities (GitHub users/teams in the reference binding). The verifier rejects
evidence signed outside the matrix. A solo maintainer binds every role to one
identity — and the verifier records a standing separation-of-duty exception as
a fact in the evidence, visible to any auditor, rather than hiding it.
