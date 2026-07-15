#!/usr/bin/env python3
"""Claude Code agent binding: emit an agent-usage/v1 statement by summing
token usage from the local session transcript for a time window.

This is a vendor-specific adapter (D13: adapters are bindings) — another
agent harness supplies its own equivalent; the statement shape is the
vendor-neutral contract.

  python3 bindings/claude-code/usage.py \
      --change-id CR-... --opened-at 2026-07-14T20:40:20Z \
      --head <sha> --out .asdlc/changes/CR-.../evidence \
      [--transcript <path.jsonl>] [--model claude-fable-5]
"""
import argparse
import datetime
import json
import pathlib


def transcript_dir():
    """Claude Code stores each session's transcripts under a directory named
    after the absolute cwd it was launched from, with every '/' and '.'
    replaced by '-' (so a worktree checkout gets its own directory, distinct
    from the main checkout's)."""
    cwd = pathlib.Path.cwd().resolve()
    name = str(cwd).replace("/", "-").replace(".", "-")
    proj = pathlib.Path.home() / ".claude" / "projects" / name
    if not proj.is_dir():
        raise SystemExit(f"no session transcript directory for cwd {cwd} (looked in {proj})")
    return proj


def newest_transcript():
    proj = transcript_dir()
    files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit(f"no session transcript found in {proj}")
    return files[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change-id", required=True)
    ap.add_argument("--opened-at", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--identity", default="github:jvanheerikhuize")
    ap.add_argument("--vendor", default="Anthropic")
    ap.add_argument("--model", default="claude-fable-5")
    a = ap.parse_args()

    since = datetime.datetime.fromisoformat(a.opened_at)
    now = datetime.datetime.now(datetime.timezone.utc)
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    path = pathlib.Path(a.transcript) if a.transcript else newest_transcript()
    for line in open(path):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = (d.get("message") or {}).get("usage")
        ts = d.get("timestamp")
        if not u or not ts:
            continue
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if not (since <= t <= now):
            continue
        tokens["input"] += u.get("input_tokens", 0)
        tokens["output"] += u.get("output_tokens", 0)
        tokens["cache_read"] += u.get("cache_read_input_tokens", 0)
        tokens["cache_creation"] += u.get("cache_creation_input_tokens", 0)
    tokens["total"] = sum(tokens.values())

    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    st = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": a.head}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/agent-usage/v1",
        "predicate": {
            "change_id": a.change_id,
            "source": "claude-code session transcript",
            "window": {"from": a.opened_at, "to": stamp},
            "tokens": tokens,
            "produced_by": {
                "role": "implementer", "kind": "agent", "identity": a.identity,
                "agent": {"vendor": a.vendor, "model": a.model},
            },
            "produced_at": stamp,
        },
    }
    out = pathlib.Path(a.out) / "usage.json"
    out.write_text(json.dumps(st, indent=2) + "\n")
    print(f"wrote {out}: {tokens['total']:,} tokens "
          f"(in {tokens['input']:,} · out {tokens['output']:,} · "
          f"cache read {tokens['cache_read']:,} · cache write {tokens['cache_creation']:,})")


if __name__ == "__main__":
    main()
