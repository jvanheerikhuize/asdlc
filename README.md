<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# asdlc

Clean-slate redesign of a governed, agent- and vendor-agnostic Agentic
Software Development Lifecycle (ASDLC) framework, for a regulated
(DORA / EU AI Act) context, hosted on GitHub.

Start with [PURPOSE.md](PURPOSE.md) — the state of the work, the researched
design positions, and the original brief (in [docs/](docs/)).

All documents in this repo (this file included) are generated from the
knowledge base in `.asdlc/knowledge/` — edit nodes, then run
`python3 spec/tools/scaffold.py`.

## The design (brief §7 deliverables)

| Doc | Contents |
|---|---|
| [architecture.md](docs/design/architecture.md) | The evidence-state machine, the three components, lifecycle, gates, evidence model, authority |
| [decisions.md](docs/design/decisions.md) | Eleven key decisions with trade-offs — what diverges from the prior art and what is kept, and why |
| [compliance.md](docs/design/compliance.md) | DORA and EU AI Act obligations mapped to mechanisms and evidence; converged model; tensions resolved |
| [agents.md](docs/design/agents.md) | Personas as governed content, computed squads, MCP orchestration, degraded modes |
| [risks.md](docs/design/risks.md) | Design risks, operational failure modes, open questions |
| [roadmap.md](docs/design/roadmap.md) | Six build slices, dogfood-first, DORA-first sequencing |

The one-sentence design: **a change is a Change Record that accumulates signed
attestations, a gate is a policy over those attestations enforced at the
platform boundary, and everything else — orchestrator, personas, playbooks —
is the easy path, never the source of truth.**
