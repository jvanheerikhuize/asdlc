<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Governance, DORA, and EU AI Act mapping (brief §7.4)

How each obligation is satisfied by concrete framework mechanisms and the
evidence they produce. Dates reflect the Digital Omnibus (adopted June 2026):
Annex III high-risk obligations apply 2 Dec 2027; transparency obligations
from Aug 2026; AI-content labelling from 2 Dec 2026. DORA has applied since
17 Jan 2025 and is therefore the *near-term* driver.

## DORA (Regulation (EU) 2022/2554)

| Obligation | Mechanism | Evidence produced |
|---|---|---|
| ICT risk management in every phase | RC controls activated by the P1 risk classification; risk-officer role in the authority matrix | `classification/v1`, RC `control-verdict/v1` per gate |
| Change & release governance, rollback | G4 merge gate (required check + required reviewer); G5 release gate (environment protection); rollback plan is required G5 evidence | `approval/v1`, `deployment/v1` with rollback reference, full gate verdicts |
| Incident handling & reporting (4h/72h/30d) | `incident/v1` records opened in P6 with severity classification; the record schema carries the regulatory clock timestamps; reporting itself is an adopter binding (their competent authority, their format) — the framework guarantees the record exists, is timestamped, and is complete | `incident/v1`, `learning/v1` |
| Resilience & security testing as a gate | SC controls in the required-control set; G4 cannot pass without their verdicts; test depth scales with classification | SC `control-verdict/v1` |
| ICT third-party risk (incl. models/agents) | P0 onboarding inventory treats every external model, agent product, and dependency as an ICT third party; SBOM required as build evidence; inventory drift checked at G4 | inventory baseline, SBOM attestation, RC verdicts |
| Tamper-proof audit trail, ≥5-year retention | DSSE-signed attestations in the platform store **plus** the scheduled retention export to an adopter-bound append-only store | the evidence DAG itself + export receipts |
| Supervisory traceability | The Change Record DAG mechanically reconstructs which controls fired, verdicts, approvers, and artefact lineage | the DAG; a generated human-readable trace report |

## EU AI Act (Regulation (EU) 2024/1689, as amended)

The framework is addressed **twice**, as the brief requires:

### (a) The framework itself is an AI system deploying autonomous agents

| Obligation | Mechanism | Evidence |
|---|---|---|
| Risk-management system across the AI lifecycle | The lifecycle *is* the risk-management system: classification at P1, conditional controls, gated progression, HALT | the evidence DAG per change |
| Record-keeping / logging (tamper-evident) | Every agent action that matters produces a signed attestation; orchestrator session logs are linked as evidence | attestation DAG, session-log references |
| Transparency of AI involvement | `AI-contribution disclosure` is mandatory P3 evidence: which artefacts were AI-generated/-assisted, by which agent identity | disclosure attestation (also serves content-labelling duties from Dec 2026) |
| Human oversight | Gates G4/G5 require platform-enforced human approval; the approver sees a generated evidence summary, not a raw diff dump (anti-rubber-stamp, see risks) | `approval/v1` naming the human identity |
| Accuracy, robustness, cybersecurity | QC + SC control verdicts as gate conditions | `control-verdict/v1` |

### (b) Software built *with* the framework may contain AI

| Obligation | Mechanism | Evidence |
|---|---|---|
| Documented AI classification driving obligations | P1 AI classification (prohibited / high-risk / limited / minimal) is a required, signed artefact; "prohibited" fails G1 outright; "high-risk" activates the full AC/DC battery | `classification/v1` |
| Data & data governance (quality, bias examination) | DC controls activate when the data classification crosses the threshold: data-provenance, quality, and bias-examination verdicts required | DC `control-verdict/v1` |
| Technical documentation & conformity records | Generated from the evidence DAG — the documentation *is* a view over the records, so it cannot drift from reality | generated conformity dossier |
| Bias & fairness above the governed threshold | AC controls (fairness evaluation) in the required set for high-risk AI changes | AC `control-verdict/v1` |
| Human oversight in the built system | An AC control requiring the design evidence (P2) to specify oversight points when AI capability crosses the threshold | design-decision + AC verdict |

## Convergence — one evidence model for both regimes

The regimes overlap on logging, risk management, human oversight, resilience,
and third-party/model risk. The framework deliberately converges them:

- **One evidence spine** serves both — a DORA auditor and an AI Act conformity
  assessor read the same DAG through different generated views.
- **One classification step** (risk × data × AI) feeds both control families;
  no duplicate assessments.
- **One third-party inventory** covers DORA ICT third parties and AI Act
  upstream-model obligations (external models are both).
- **One human-oversight mechanism** (gated approvals) satisfies both.

## Tensions, and how they are resolved

1. **Retention vs. platform-tied storage.** DORA wants ≥5-year tamper-proof
   retention; GitHub's private attestation store is not a WORM guarantee and
   dies with the repo. Resolved by the mandatory retention-export interface —
   the one piece of infrastructure the framework refuses to make optional.
2. **AI Act transparency vs. financial-sector confidentiality.** Disclosure
   attestations are structured so the *fact and extent* of AI involvement is
   separable from the *content* of the change — transparency reports can be
   generated without leaking the codebase.
3. **Meaningful human oversight vs. automation bias.** A gate that shows a
   human 40 green checkmarks produces rubber-stamping, which fails the AI
   Act's "effective" oversight test in spirit. Resolved in the approval
   surface: approvers see the classification, the *exceptions* (waivers, SoD
   exceptions, retry history), and a generated summary of what is unusual —
   friction is spent where attention matters.
4. **AI Act timeline slip vs. DORA now.** Post-Omnibus, high-risk AI
   machinery has runway to Dec 2027, but DORA has applied since Jan 2025. The
   build order (see roadmap) therefore lands DORA-serving mechanisms (change
   governance, audit trail, incident records) before the full AC/DC battery —
   while the predicate family reserves the AI Act's shapes from day one so
   nothing is retrofitted.
