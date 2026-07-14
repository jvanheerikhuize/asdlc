# ASDLC Clean-Slate Rebuild — Session State (2026-07-14)

> **Superseded — historical record only.** Current state lives in
> [../PURPOSE.md](../PURPOSE.md); the design this file anticipated has been
> delivered in [design/](design/). Kept for provenance of the Q&A.

Continuation file for the design exercise in `Prompt Clean Slate Rebuild.md`.
State: prompt analysed; clarifying questions researched and **answered below
(user asked the model to propose answers, grounded in web research)**. Next
step: produce the full architecture (§7.2–7.7) against these answers.

New constraint from user: **the framework and all consuming repositories live
on GitHub.** A tech-stack proposal is included below.

To resume: point the model at the prompt file and this file, confirm or amend
the answers, and ask for the full design.

---

## Research findings (July 2026, web-verified)

- **MCP is vendor-neutral now**: donated to the Linux Foundation's Agentic AI
  Foundation Dec 2025 (AWS, Google, Microsoft, OpenAI backing); new spec
  finalises 2026-07-28 (stateless core, Tasks primitive, Extensions). Using MCP
  as the agent interface no longer conflicts with vendor-agnosticism.
- **GitHub enforcement primitives now cover the framework's needs**: artifact
  attestations (Sigstore-signed, in-toto format) with org-level attestation
  policies; required-reviewer ruleset rule GA Feb 2026; Enterprise AI Controls
  + agent control plane GA Feb 2026; GitHub Agentic Workflows public preview
  Jun 2026 (sandboxed agents, read-only defaults, gated "safe outputs").
- **EU AI Act timeline moved**: Digital Omnibus (adopted Jun 2026) deferred
  Annex III high-risk obligations 2026-08-02 → **2027-12-02**; Annex I →
  2028-08-02. Aug 2026 keeps transparency duties; AI-content labeling →
  Dec 2026. **DORA applies since Jan 2025** (tamper-proof audit trails, ~5-yr
  retention, 4h/72h/30d incident reporting) — the operational regime is the
  urgent one.
- **Private-repo attestations** live only in GitHub's private Sigstore
  instance (no public Rekor; Enterprise = private internal store). Tamper-
  evident but retention is GitHub-tied — needs an export path for DORA's
  5-year horizon.

## Answered questions

**1. Trust boundary → platform-enforced (GitHub), orchestrator = ergonomics.**
Gates are GitHub rulesets (required checks, required reviewers, push rules),
required workflows, environment protection — unbypassable at merge/deploy. The
unbypassable check is a **verifier validating the evidence bundle**; the MCP
orchestrator is the easy path that produces evidence, never the source of
truth. Agnosticism preserved: framework owns the *verification contract*
(schemas + policy); GitHub is the shipped *reference binding*; verifier is a
portable CLI so other platforms can bind it.

**2. Scope → full span, unevenly.** DORA forces post-merge coverage while the
AI Act clock moved out. Intent→merge at high resolution; deploy/operate as
first-class contracts (evidence schemas, gate definitions, incident-record
format) with a thin GitHub binding: Environments + required reviewers for
deploy gates, deployments API for release evidence, issue-forms incident
records feeding the 4h/72h/30d clock.

**3. Evidence → in-repo attestations + retention export.** Every control
verdict = signed in-toto attestation (custom predicate, e.g.
`control-verdict/v1`) via GitHub-native Sigstore signing, bound to commit +
workflow identity. Plus a **retention exporter**: scheduled workflow bundles
evidence to adopter-bound WORM storage (object-lock object storage; release
assets as zero-infra default). Repo deletion must not destroy evidence.

**4. Humans → roles as policy data, degrading gracefully.** Approval roles
defined abstractly in governance (which role passes which gate class); GitHub
binding maps them to CODEOWNERS / required-reviewer rules / environment
reviewers. A solo maintainer maps all roles to self and the audit record
states it explicitly — SoD gaps are visible facts, not hidden ones.

**5. Greenfield → clean slate, port concepts not structure.** Carry over the
typed-control taxonomy, classification-driven depth, HALT semantics, knowledge
graph as *content*; four-repo split, manifest format, doc generation are up
for redesign. Migration = content port, no compatibility layer.

**Load-bearing split (confirmed by Q1 answer):** framework defines the
verification contract; adopter/platform supplies the binding; GitHub binding
ships as reference.

## Tech stack proposal

- **Verifier CLI: Go** — static binary, sigstore-go/in-toto/cosign ecosystem;
  wrapped as a GitHub Action for the reference binding.
- **Gate policies: OPA/Rego embedded in the verifier** (no policy server).
- **Schemas: JSON Schema 2020-12** for manifest + all artefact templates.
- **Orchestrator: MCP server in Go** (official Go SDK, single-language
  codebase); TypeScript fallback if SDK gaps appear.
- **Swarm/role definitions: Markdown + YAML frontmatter**, aligned with the
  `.github/agents/*.md` convention (path-protectable via push rules).
- **Knowledge graph: YAML/JSON-LD files in-repo**, schema-validated, no DB;
  optional SQLite cache is derived, never authoritative.
- **Framework content: Markdown + YAML/JSON** with generated human views.

## Remaining deliverables (§7)

2. Proposed architecture — components, responsibilities, boundaries.
3. Key decisions & trade-offs, esp. divergence from §6 prior art.
4. Governance / DORA / EU AI Act mapping to artefacts, controls, gates,
   evidence (use post-Omnibus dates above).
5. Subagent & orchestration model over MCP.
6. Risks, failure modes, open questions.
7. Incremental build plan.

## Key sources

- https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- https://en.wikipedia.org/wiki/Model_Context_Protocol (AAIF donation)
- https://docs.github.com/en/actions/concepts/security/artifact-attestations
- https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/
- https://github.blog/changelog/2026-02-26-enterprise-ai-controls-agent-control-plane-now-generally-available/
- https://github.blog/changelog/2026-06-11-github-agentic-workflows-is-now-in-public-preview/
- https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/
- https://www.insideglobaltech.com/2026/05/28/eu-ai-act-update-timeline-relief-targeted-simplification-and-new-prohibitions/
- https://dorapp.eu/blog/dora-audit-trail-requirements-essential-guidelines/
- https://jfrog.com/blog/navigating-dora-compliance-software-development-requirements-for-financial-services-companies/
