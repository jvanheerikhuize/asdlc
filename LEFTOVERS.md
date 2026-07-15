<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Leftovers — small known debts

Generated view of the `leftover` knowledge nodes (see
[the convention](.asdlc/knowledge/nodes/convention/convention-leftovers.yaml)):
small, well-understood stand-ins awaiting a **leftover sweep** — a dedicated
governed change that fixes them and marks them done. Design-sized work
lives on the roadmap instead, never in both places.

## Active

**Scaffold Change Records with clock timestamps, not authored ones**
The first metrics run exposed negative lead times: early Change Records
carried hand-authored, future-guessed timestamps, so the merge landed
"before" the intent. Evidence timestamps must come from a clock. Add a
small `spec/tools/new-change.py` that scaffolds change.json + intent +
classification with real `produced_at` values (and prompts for the
human-authored fields). It must also mint the id's 3-digit per-date
sequence (D14, spec 0.5.0) by listing `.asdlc/changes/` for the date.
Past evidence stays as-is — immutable, and the
negative numbers are the honest record of the defect.

**asdlc-verify: fetch spec conformance fixtures from the pinned tag**
`asdlc-verify/testdata/spec-0.1.0/` is a hand-copied snapshot of the
spec's gate policy and golden bundles. Replace it with a CI checkout of
`jvanheerikhuize/asdlc` at the tag named by a pin file, so conformance
always tests the spec version the verifier claims to support (both repos
are public; cross-checkout works with the default token).

**asdlc-verify: commit go.sum (stop tidying in CI)**
No Go toolchain existed on the dev machine, so CI runs `go mod tidy`
before build — meaning dependency versions float per run. Generate go.sum
once (in CI, committed back via PR), drop the tidy step, and turn on
setup-go caching.

**Bring spec/README.md and bindings/github/README.md under generation**
Both are still hand-maintained prose; decompose them into knowledge
nodes and doc manifests like everything else. (asdlc-verify's README
follows separately via the D13 pinned-spec path once
leftover-verify-fixtures-pin establishes it.)

**Bump GitHub Actions pinned to Node 20-deprecated majors**
Every workflow run warns that actions/checkout@v4, setup-python@v5,
setup-go@v5, and setup-opa@v2 target the deprecated Node 20 runtime.
Bump to the current majors across both repos when convenient.
