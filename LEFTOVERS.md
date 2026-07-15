<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Leftovers — small known debts

Generated view of the `leftover` knowledge nodes (see
[the convention](.asdlc/knowledge/nodes/convention/convention-leftovers.yaml)):
small, well-understood stand-ins awaiting a **leftover sweep** — a dedicated
governed change that fixes them and marks them done. Design-sized work
lives on the roadmap instead, never in both places.

## Resolved

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

Done: `spec/tools/new-change.py` scaffolds all three files with clock
`produced_at` values, mints the per-date sequence, and prompts for
human-authored fields.

**Bring spec/README.md and bindings/github/README.md under generation**
Both are still hand-maintained prose; decompose them into knowledge
nodes and doc manifests like everything else. (asdlc-verify's README
follows separately via the D13 pinned-spec path once
leftover-verify-fixtures-pin establishes it.)

Done: `spec/README.md` and `bindings/github/README.md` are now generated
from `spec-readme-scope-notes`, `spec-readme.yaml`,
`github-readme-governed-change-flow`, and `github-readme.yaml`.

**asdlc-verify: commit go.sum (stop tidying in CI)**
No Go toolchain existed on the dev machine, so CI runs `go mod tidy`
before build — meaning dependency versions float per run. Generate go.sum
once (in CI, committed back via PR), drop the tidy step, and turn on
setup-go caching.

Done: a Go toolchain is now available; `go.sum` is generated and
committed (asdlc-verify#2), the `go mod tidy` step is dropped from
`ci.yml` and the composite `action.yml`, both now resolve their Go
version from `go.mod` via `go-version-file` (tidy bumped the `go`
directive to 1.25.0 to satisfy `open-policy-agent/opa v1.18.2`), and
setup-go caching is on.

**Bump GitHub Actions pinned to Node 20-deprecated majors**
Every workflow run warns that actions/checkout@v4, setup-python@v5,
setup-go@v5, and setup-opa@v2 target the deprecated Node 20 runtime.
Bump to the current majors across both repos when convenient.

Partly done: this repo's own workflows (`g4-gate.yml`, `spec-check.yml`,
`metrics.yml`) now use `actions/checkout@v7` and `actions/setup-python@v6`.
`open-policy-agent/setup-opa@v2` was already current (latest release is
v2.4.0 — no v3 major exists yet). `setup-go` isn't used in this repo.
The `asdlc-verify` repo's workflows (including its own `setup-go` pin)
still need the same bump — outside this change's reach.

Done: `asdlc-verify`'s `ci.yml` and composite `action.yml` now use
`actions/checkout@v7` and `actions/setup-go@v6` (asdlc-verify#2),
closing the gap left by the earlier partial fix.

**asdlc-verify: fetch spec conformance fixtures from the pinned tag**
`asdlc-verify/testdata/spec-0.1.0/` is a hand-copied snapshot of the
spec's gate policy and golden bundles. Replace it with a CI checkout of
`jvanheerikhuize/asdlc` at the tag named by a pin file, so conformance
always tests the spec version the verifier claims to support (both repos
are public; cross-checkout works with the default token).

Done: `asdlc-verify` now has `spec.pin` (currently `spec-v0.4.0`) and
`scripts/fetch-fixtures.sh`, which clones `jvanheerikhuize/asdlc` at the
pinned tag and copies its gate policy and golden bundles into the
gitignored `testdata/spec-pinned/`. CI runs the fetch script before
`go test`; the hand-copied `testdata/spec-0.1.0/` is removed. Fixtures at
the pinned tag are byte-identical to the ones they replace, so this is a
mechanism change with no behavior change. asdlc-verify#3.
