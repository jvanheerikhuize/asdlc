# Purpose — Clean-Slate Rebuild of the Agentic SDLC Framework

This repository is the working home for a from-first-principles redesign of a
governed, agent- and vendor-agnostic **Agentic Software Development Lifecycle
(ASDLC)** framework: a system in which autonomous AI agents carry a software
change from stated intent to production and operation, with governance,
auditability, and DORA / EU AI Act compliance built in rather than bolted on.

The full design brief is [docs/prompt-clean-slate-rebuild.md](docs/prompt-clean-slate-rebuild.md).
The session state that produced this document is
[docs/session-continuation-2026-07-14.md](docs/session-continuation-2026-07-14.md).

**Ground fact set by the owner:** the framework and all consuming repositories
live on **GitHub**. Enforcement reference bindings may therefore target GitHub
primitives, while the framework's contracts stay platform-neutral.

---

## Where the work stands (2026-07-14)

1. Brief read and analysed; prior-art repos are not on this machine — design
   proceeds from the brief's §6 summary, as intended.
2. Five clarifying questions raised, then researched; proposed answers below.
3. Next deliverable: the proposed architecture (§7.2–7.7 of the brief).

---

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

---

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

---

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

---

## Remaining deliverables (brief §7)

2. Proposed architecture — components, responsibilities, boundaries.
3. Key decisions and trade-offs, especially divergence from the prior art.
4. Governance / DORA / EU AI Act mapping to artefacts, controls, gates, evidence.
5. Subagent and orchestration model over a vendor-neutral interface.
6. Risks, failure modes, open questions.
7. Incremental build plan.
