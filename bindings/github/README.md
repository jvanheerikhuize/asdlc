# GitHub reference binding — v0.1 conventions

How the spec's contracts map onto GitHub primitives in this first, honest
iteration. Every convention below is a stand-in with a named successor;
none changes the policy contract when replaced.

| Contract | v0.1 binding | Real thing (later slice) |
|---|---|---|
| G4 enforcement | `g4-gate` workflow; added to the main ruleset's required checks once proven | same, kept |
| Evidence signing | `--dev-unsigned`: statements are plain JSON, identity trusted from the statement's own claim, roles resolved via `asdlc.yaml` | DSSE + Sigstore verification in asdlc-verify |
| Evidence storage | authored statements (intent, classification) live in-branch under `.asdlc/changes/<id>/evidence/`; CI-produced statements (verdicts, approval) are produced in-workspace and uploaded as a run artifact | platform attestation store + retention exporter (slice 4) |
| Human review approval | `/asdlc approve <head-sha-prefix>` PR comment by an identity bound to `release-approver`; transcribed to `approval/v1`. Sha-bound: new commits void the approval | PR-review transcription (needs a second identity: GitHub forbids approving your own PR) plus environment approvals for G5 |
| Approval re-check | `approval-rerun` workflow re-runs `g4-gate` when an approve comment lands | evidence-store webhook |
| Ungoverned changes | PRs touching no Change Record pass the gate vacuously (visible notice in the run) | closed in slice 2, when classification-driven depth makes small changes cheap enough to always require a CR |

## The governed-change flow (solo-maintainer reality)

1. Author `change.json`, `evidence/intent.json`, `evidence/classification.json`
   under `.asdlc/changes/<CR-id>/` on your branch, plus the actual change.
2. Open the PR. `g4-gate` runs: produces QC-01/SC-01 verdicts, finds no
   approval → **denies** with reasons on the check.
3. Comment `/asdlc approve <head-sha>`. `approval-rerun` re-runs the gate,
   which transcribes the approval and re-evaluates → green if all evidence
   holds.
4. Merge. The evidence bundle for the run is attached as an artifact.

The same account authoring and approving is the standing separation-of-duty
exception the manifest records; the framework's job is to make that fact
visible, not to pretend otherwise.
