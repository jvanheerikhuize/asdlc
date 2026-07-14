<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Risks, failure modes, open questions (brief §7.6)

## Design-level risks

**R1 — Goodhart's law: agents optimize for passing gates, not for quality.**
The gate checks that evidence exists and satisfies policy; an agent can
produce technically-valid, substantively-hollow evidence (a threat model that
lists nothing, tests that assert nothing). *Mitigation*: controls whose
verdicts are produced by *independent* personas (the authority matrix forbids
the implementer signing its own security verdict); spot-check controls that
sample evidence quality; and the human approval surface highlights thin
evidence. *Residual*: real — this is the field's open problem, and the design
treats independent-signer separation as the main structural defense.

**R2 — Rubber-stamping / automation bias at human gates.**
If approvals
degrade to clicking through green checks, both DORA change governance and AI
Act "effective oversight" fail in substance while passing in form.
*Mitigation*: the approval surface is exception-oriented (see compliance.md
§tension 3); approval latency and waiver rates are themselves recorded and
reportable, so drift toward rubber-stamping is visible in evidence.

**R3 — Policy bugs become false assurance.**
A wrong Rego policy silently
passes changes that should have been stopped — worse than no framework,
because it *certifies* the gap. *Mitigation*: policies ship with a conformance
test suite (golden evidence bundles that must pass/fail); policy changes in
the spec are themselves high-risk governed changes; verifier and spec versions
are pinned and attested in every verdict.

**R4 — The verifier is the supply-chain crown jewel.**
Compromise the
verifier (or the approval-transcription workflow) and every gate lies.
*Mitigation*: both are small and boring by design; built with SLSA provenance
and attested; the reference binding pins them by digest, not tag; org-level
attestation policies verify the verifier itself before it runs. Verifying the
verifier bottoms out in the platform's trust root — stated honestly rather
than hidden.

**R5 — GitHub coupling creep.**
Convenience will keep tempting gate logic
into GitHub-specific config until portability is fiction. *Mitigation*: hard
rule — anything that decides pass/fail lives in spec policies evaluated by
the portable verifier; platform config may only *invoke* the verifier and
enforce human review. The conformance suite doubles as the portability test: a
second binding (even a skeletal local-git one) is built early to keep the seam
honest.

**R6 — Evidence volume vs. agent context cost.**
A high-risk change
accumulates dozens of attestations; forcing agents to read raw DSSE JSON
burns tokens. *Mitigation*: `change.status` returns a compact computed
summary (what exists, what the next gate lacks); raw evidence is fetched only
when needed. The spec is written for machine consumption first (brief §8).

**R7 — Orchestrator/reality drift.**
The cooperative layer's view of the
change can diverge from the actual evidence (crashed sessions, parallel
agents). *Mitigation*: the orchestrator holds no authoritative state — every
answer it gives is derived from the evidence bundle on read. Statelessness is
the design principle; the MCP Tasks state is convenience cache only.

**R8 — Waiver misuse.**
Waivers are the designed escape valve and therefore
the designed loophole. *Mitigation*: waivers are signed, role-checked,
per-control, per-change (never blanket), carry mandatory rationale, and are
first-class reportable evidence — a waiver-rate dashboard is a supervisory
artefact, and heavy waiver use is *visible* pressure on management, which is
where that problem belongs.

## Failure modes (operational)

- **Platform outage / attestation store unavailable** → gates fail closed;
  changes queue. Accepted: availability is traded for integrity at the gate.
- **Signing identity misconfiguration** → verifier rejects valid work;
  detectable via a `doctor` command in the CLI (preflight the manifest).
- **Retention export target unreachable** → export retries with alerting;
  evidence is not lost (still in platform store) but the compliance clock on
  retention lag is recorded.
- **Agent produces attestations outside a Change Record** → orphan evidence
  is ignored by gates and flagged by the verifier as an anomaly record.

## Open questions

1. **Multi-repo changes.** A feature spanning three consuming repos needs a
   cross-repo Change Record or a federation convention — current design
   handles single-repo changes cleanly; the ID scheme reserves space for a
   parent-change reference, but the coordination gate is undesigned.
2. **Evidence privacy tiers.** Some evidence (threat models, incident
   details) is sensitive; who may read the DAG, and should the retention
   store support field-level encryption? Currently: repo-visibility inherited,
   which is coarse.
3. **Cost model.** Every gate run costs CI minutes and agent tokens; the
   classification throttle bounds it, but no measured baseline exists yet —
   the dogfood phase (roadmap slice 1) must produce one.
4. **Incident-report *submission*.** The framework guarantees the incident
   record's existence, completeness, and clock; actually filing with a
   competent authority in their format is adopter territory. Is a reference
   exporter (e.g. to the ESAs' harmonised template) worth shipping?
5. **Persona quality drift.** Personas are governed content, but nothing yet
   measures whether a persona's verdicts remain *good* as models change
   underneath it — an evaluation harness per persona is plausibly slice-6
   work.
