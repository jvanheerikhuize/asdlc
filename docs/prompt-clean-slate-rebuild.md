# Prompt — Clean-Slate Rebuild of the Agentic SDLC Framework

> *How to use this prompt:* Paste it into any capable AI model or agent. It is
> deliberately vendor-neutral and free of tool-, model-, or product-specific
> assumptions. It states a purpose and a set of goals; it does *not* hand you a
> solution to copy. Where a current implementation is mentioned, it is prior art
> for context only — you are explicitly invited to diverge from it.

---

## 1. Your task

Design — *from first principles* — the architecture for a governed, agent- and
vendor-agnostic *Agentic Software Development Lifecycle (ASDLC)* framework:
a system in which autonomous AI agents can carry a software change from stated
intent all the way to production and operation, with governance, auditability,
and regulatory compliance built in rather than bolted on.

A working version of this framework already exists (summarised in §6). **Do not
treat it as authoritative.** The whole point of this exercise is to see what a
model would design today, unanchored. Challenge every assumption. If you would
structure it completely differently, do so — and justify it. If parts of the
prior art are genuinely sound, say why you'd keep them.

Before proposing a design, *ask me any clarifying questions* that would
materially change your approach. Then produce the deliverables in §7.

---

## 2. Purpose (the "why")

I want any capable agent — single-agent or multi-agent, from any vendor — to be
able to execute a software feature end-to-end under governance that a regulated
enterprise can trust and audit. The framework must make the governed path the
easy path: correctness, security, risk, and AI-specific controls should be
intrinsic to the workflow, not optional add-ons. Humans stay in control at the
decisions that matter; everything an agent does is recorded and reconstructable.

The framework must be *agnostic*: nothing may depend on a specific agent
product, foundation model, orchestration library, or CI/CD vendor. Concrete tool
bindings belong to each consuming repository, never to the framework itself.

---

## 3. Capabilities the system must provide

Describe how you would deliver these — do not assume the current structure.

1. *A governed lifecycle.* A defined progression from intent → design →
   implementation → verification → deployment → operation (or whatever set of
   phases you judge correct), with explicit entry/exit criteria, gated quality/
   security/risk/AI checks, and clear hand-offs between phases.
2. *A reusable governance/reference layer.* Canonical, machine-readable
   definitions of the artefacts to produce, the schemas they must satisfy, and
   the typed controls to enforce — decoupled from any single project so many
   repositories can consume the same governance.
3. *Orchestration.* A way to drive agents through the lifecycle, coordinate
   work, enforce gates, capture approvals, and expose this to agents through a
   standard, interoperable interface (e.g. a tool/skill/service protocol).
4. *A subagent "swarm".* A model for specialised subagents with distinct
   personalities, roles, and expertise (e.g. product, architecture, security,
   testing, operations), how they are selected and composed, how they
   collaborate, and how responsibility/authority is assigned and recorded.
5. *Persistent memory & knowledge.* Repository-scoped baselines and a
   knowledge graph (or your preferred representation) that agents read for
   context and update as they learn.
6. *Auditable evidence.* Every scan, assessment, decision, and hand-off leaves
   a durable, traceable record — a verdict without a record does not exist.

---

## 4. Non-negotiable principles

Treat these as requirements the design must satisfy; you may realise them however
you see fit:

- *Agent/vendor agnosticism.* No dependency on a specific model, agent
  product, or CI vendor. Portable by construction.
- *Human oversight by design.* Irreversible or high-risk decisions require an
  explicit human gate. Agents never silently route themselves backwards across a
  phase boundary or downgrade a stop to a warning.
- *Fail-safe control flow.* Bounded retries, then a terminal, escalated stop
  ("HALT") that finalises records and hands to a human. Defects route back only
  to the phase authorised to fix them, by human decision.
- *Classification-driven depth.* Classify risk, data sensitivity, and AI usage
  once, early; let those classifications automatically trigger the right depth of
  downstream controls (e.g. sensitive-data handling, AI fairness/oversight).
- *Records always written.* Continuous provenance, an append-only audit trail,
  and an end-to-end traceability spine that reconstructs which controls fired,
  their verdicts, and the lineage of every artefact.
- *Separation of authority.* Clear boundaries on which actor/phase may write
  what; earlier outputs are read-only to later phases.

---

## 5. Regulatory context — DORA and the EU AI Act

The solution operates inside a *regulated financial-services / ICT context* and
must be designed so that compliance is a first-class, built-in property, not a
later audit exercise. Two regimes apply:

*Digital Operational Resilience Act (DORA, Regulation (EU) 2022/2554).*
Design for operational resilience, and make the following demonstrable with
evidence the framework produces automatically:
- *ICT risk management* integrated into every phase (identify, protect,
  detect, respond, recover).
- *Change and release governance* with rollback/recovery paths and evidence.
- *Incident handling & reporting* — detect, classify, record, and route
  operational/ICT incidents; support post-incident learning.
- *Digital operational resilience testing* — the framework should require and
  record appropriate testing (including security testing) as a gate.
- *ICT third-party risk* — treat external models, agents, tools, and
  dependencies as ICT third parties: inventory them, assess and monitor their
  risk, and record it (e.g. SBOM, supply-chain and dependency controls).
- *Traceability & auditability* sufficient for a supervisory review.

*EU Artificial Intelligence Act (Regulation (EU) 2024/1689).*
The framework is itself an AI system that deploys autonomous agents, and it is
used to build software that may contain AI. Address both. Assume that some uses
fall in the *high-risk* category and design to meet, and evidence:
- *Risk-management system* across the AI lifecycle; a documented, risk-based
  *AI classification* (prohibited / high-risk / limited / minimal) driving
  obligations.
- *Data & data governance* for any AI features (quality, relevance, bias
  examination).
- *Technical documentation & record-keeping / logging* — automatic, tamper-
  evident logs of agent actions and decisions sufficient for conformity and
  traceability.
- *Transparency* — clear disclosure of AI involvement and of AI-generated or
  AI-assisted outputs.
- *Human oversight* — effective, meaningful human control at defined points.
- *Accuracy, robustness, and cybersecurity* — tested and evidenced.
- *Bias & fairness* evaluation where AI capability crosses a governed
  threshold.

Where DORA and the AI Act overlap (logging, risk management, resilience,
third-party/model risk, human oversight), converge them into a single coherent
evidence and control model rather than duplicating effort. Call out any tension
between them and how you resolve it.

---

## 6. Prior art — the current implementation (context only; do not be bound by it)

The framework exists today as *four repositories. This is *one prior solution,
provided so you understand the problem space — not a template to reproduce:

1. *Lifecycle* — a six-stage governed SDLC (intent → system design → coding →
   testing/documentation → deployment* → observability*, with a pre-lifecycle
   onboarding step; reserved). Each stage has a procedural *playbook, a binding
   contract, and a flow diagram. Controls are typed:
   QC quality · SC security · RC risk · AC AI · DC data (conditional) ·
   GC governance (continuous). A single machine-readable manifest is the entry
   point and single source of truth; documents are generated from it.
2. *Governance* — a separate reference library of canonical artefact templates
   (+ JSON schemas) and typed control definitions, plus onboarding baselines and
   a knowledge-graph schema, consumed by the lifecycle at runtime.
3. *Orchestrator* — the runtime that drives agents through the lifecycle,
   exposed as a *Model Context Protocol (MCP) server* (start/approve stages,
   query the squad, ask members, record observations, etc.).
4. *Swarm / squad* — definitions of subagent *personalities and expertise*
   (the specialised roles the orchestrator composes for each stage).

Cross-cutting ideas in the current design: classification-driven conditional
controls; a continuous governance track (provenance, audit trail, end-to-end
trace); bounded retries then HALT; an in-repo knowledge graph; and strict
vendor/agent agnosticism. You may keep, reshape, merge, split, or discard any of
this — including the four-repo split itself.

---

## 7. What I want from you

1. *Clarifying questions first* — anything that would change your design.
2. *A proposed architecture* for the framework, described so an engineer could
   start building: the major components, their responsibilities, boundaries, and
   how they interact.
3. *Key decisions and trade-offs* — especially anywhere you **diverge from the
   prior art in §6**, with your reasoning. Explicitly note what you kept and why.
4. *How governance, DORA, and the EU AI Act obligations are satisfied* — mapped
   to concrete artefacts, controls, gates, and evidence the system produces.
5. *The subagent/orchestration model* — how specialised agents are defined,
   selected, coordinated, and held accountable, over a vendor-neutral interface.
6. *Risks, failure modes, and open questions* in your design.
7. *An incremental build plan* — a sensible first slice and the order to grow.

---

## 8. Constraints & out of scope

- Remain *agent-, model-, and vendor-agnostic* throughout. Do not hardcode a
  specific product, model, orchestration library, or CI system.
- Prefer *machine-readable single sources of truth* with generated,
  human-readable views over hand-maintained duplication.
- Optimise for *auditability and low agent-context cost* (the framework is read
  by LLM agents; token footprint and clear structure matter).
- You are designing the *framework*, not any one consuming project; concrete
  tool bindings live in the consuming repositories.

---

## 9. Success criteria

A strong answer would let a regulated organisation adopt the framework and have
*any* capable agent execute a change end-to-end, produce a complete,
reconstructable audit trail, demonstrably satisfy the DORA and EU AI Act
obligations in §5, keep humans in control at the right moments — and do so
without being tied to any particular AI vendor. It should also make a clear,
reasoned case for wherever it departs from today's implementation.
