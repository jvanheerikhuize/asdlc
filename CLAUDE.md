<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Instructions for agents working in this repo

Auto-loaded by Claude Code at the start of every session rooted here.
Generated from the knowledge base like every other document in this repo —
edit the node, then run `python3 spec/tools/scaffold.py`.

## How an agent optimizes its work-scoped token usage

Guidance for agents working in this repo, written against
[[metric-token-usage]]'s work-scoped figure (`input + output +
cache_creation`; cache reads are free by construction). Ordered by
leverage, largest first.

**1. cache_creation dominates — control what enters context.** Every
byte of tool output ingested is context written to cache once and then
carried. Read files selectively (offset/limit, targeted greps) instead
of whole-file reads; never re-read a file already in context; keep
shell output terse (`head`, `--oneline`, `--quiet`); prefer one
precise query over three broad ones.

**2. Offload noisy exploration to subagents.** Broad grep sweeps, log
trawls, and open-ended searches belong in a sidechain that returns only
findings — the exploration bulk never enters main-thread context. Net
win only when raw exploration output is much larger than the findings;
a subagent spawned for a single targeted lookup costs more than it
saves (it re-derives context from cold).

**3. Batch turns.** Independent tool calls go in one message, in
parallel. Turn count drives context growth (each turn's results,
reasoning, and narration accrete) even though cached re-reads
themselves are excluded from the headline.

**4. Don't re-derive.** Facts already established in the conversation,
the knowledge graph, or memory are settled — act on them. Re-verifying
what a previous turn already verified is pure spend.

**5. Output is spend too.** Concise final messages; never paste large
file contents or full command output back into a response the reader
can get from the artifact itself.

**6. Open the Change Record promptly and record usage last.** The
measurement window runs `opened_at` → statement production. Scaffolding
late under-attributes exploration; recording usage before the final
commit truncates the tail. Both make the number a lie, not an
optimization.

**Anti-Goodhart guardrails — these dominate everything above.** Never
skip verification (tests, `spec/tools/check.py`, reading a file before
editing it) to save tokens; never thin out evidence, commit messages,
or PR bodies for the metric; never avoid legitimate re-reads — the
metric is work-scoped precisely so that consulting existing context is
free. A cheap wrong change costs strictly more than an expensive right
one: the rework re-spends the tokens and adds a defect. The metric
exists to expose waste (bloated reads, unbatched turns, governance
overhead), not to pressure correctness. When granular breakdowns land
([[roadmap-priority-3-token-granularity]]), optimize the by_tool and
by_phase buckets — that is where waste is visible — not the total.
