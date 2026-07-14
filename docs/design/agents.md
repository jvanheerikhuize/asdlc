# Subagent and orchestration model (brief §7.5)

## Personas are content, not code

A subagent persona is a Markdown file with YAML frontmatter, versioned in the
spec repo:

```markdown
---
id: security-engineer
role: security-reviewer          # authority-matrix role it may exercise
phases: [design, verify]         # where it is composable
activates: classification.risk >= medium || classification.data >= sensitive
signs: [control-verdict/v1]      # predicate types it may produce
model_requirements: none         # vendor-agnostic by construction
---
You are the security engineer of the squad. Your remit is …
```

Any vendor's agent can load a persona — it is a system-prompt fragment plus
declared authority, nothing more. In the GitHub reference binding these files
follow the `.github/agents/*.md` convention, so Enterprise push rules can
protect their integrity: **persona definitions are themselves governed
artefacts** (an agent cannot quietly edit its own authority).

## Composition: the squad is computed, not configured

For each Change Record, the squad is derived the same way the control set is:
`phase × classification → personas`. A minimal-risk change composes a
solo implementer persona; a high-risk AI change composes product, architect,
security, risk, test, and AI-fairness personas. Composition is deterministic
policy in the spec — auditable, and identical regardless of which vendor's
agents fill the seats.

Responsibility assignment is recorded, not assumed: when a persona is
instantiated, the orchestrator records which underlying agent identity
(vendor, model, version — from the P0 third-party inventory) filled which
seat. Every attestation produced carries both the persona and the concrete
agent identity in its predicate. Accountability is therefore two-layer: the
*role* that had authority, and the *system* that exercised it.

## Orchestration over MCP

The orchestrator is an MCP server (TypeScript, official SDK; MCP is
Linux-Foundation-governed since Dec 2025, so this stays vendor-neutral).
Core tools:

| Tool | Purpose |
|---|---|
| `change.open / change.status` | create a Change Record; read its evidence state and what the next gate still requires |
| `controls.required` | the computed control set for this change (from classification) |
| `evidence.record` | produce and sign an attestation via the verifier's flow |
| `gate.check` | dry-run the gate policy locally (the real gate is the platform check) |
| `squad.compose / squad.consult` | instantiate the computed squad; ask a persona for its assessment |
| `approval.request` | route a human approval to the platform surface (PR review / environment) |
| `knowledge.query / knowledge.propose` | read the repo's knowledge graph; propose an update (lands as a reviewed PR) |
| `playbook.get` | phase guidance — the easy path, never the enforced path |

Long-running phases map onto the MCP Tasks primitive (July 2026 spec):
a phase is a task the agent can resume, and a HALT is a terminal task state.

## Collaboration model

Deliberately simple: **shared evidence, not shared conversation.** Personas
collaborate by reading the Change Record's accumulated evidence and the
knowledge graph, and by producing their own attestations. There is no
framework-level inter-agent chat protocol — vendors differ wildly there, and
the evidence DAG is the interoperable medium. A security persona "responds" to
a design by attesting a verdict that references the design-decision
attestation. This keeps multi-vendor squads possible (Claude architect, Codex
implementer, local-model scribe) with zero protocol coupling beyond MCP.

## Degraded modes (by design)

- **No orchestrator**: any agent reads the spec, works, and produces evidence
  via the verifier CLI. Gates behave identically. The orchestrator adds
  convenience, retry counting, and squad ergonomics — never validity.
- **No agents at all**: humans produce the same evidence through the same
  gates. The framework governs *changes*, not *agents* — an all-human change
  is just a squad of size zero. This is also the escape hatch when agents are
  down or distrusted.

## Memory and knowledge

The knowledge graph lives in the consuming repo (`.asdlc/knowledge/`,
schema-validated YAML nodes and edges): architectural facts, past incident
learnings, decision rationales. Agents read it for context (files, low token
cost) and *propose* updates that land as reviewed PRs — so even the
framework's memory has provenance. P6 `learning/v1` evidence feeds it: the
post-incident loop DORA asks for is the same loop that makes the next squad
smarter.
