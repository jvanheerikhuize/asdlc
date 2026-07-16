#!/usr/bin/env python3
"""Claude Code agent binding: emit agent-usage/v1, agent-usage/v2, and
agent-activity/v1 statements from the local session transcript for a time
window — token sums for the usage statements, sessionized active working
time for the activity statement.

This is a vendor-specific adapter (D13: adapters are bindings) — another
agent harness supplies its own equivalent; the statement shape is the
vendor-neutral contract.

  python3 bindings/claude-code/usage.py \
      --change-id CR-... --opened-at 2026-07-14T20:40:20Z \
      --head <sha> --out .asdlc/changes/CR-.../evidence \
      [--transcript <path.jsonl>] [--model claude-fable-5] \
      [--idle-threshold 300]

v2 adds five breakdown dimensions (by_model, by_thread, by_phase, by_tool,
turn_shape), all derived from fields already present in the transcript —
see .asdlc/knowledge/nodes/roadmap-item/roadmap-priority-3-token-granularity.yaml.
"""
import argparse
import datetime
import json
import pathlib
import subprocess


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


def empty_tokens():
    return {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}


def add_usage(tokens, u):
    tokens["input"] += u.get("input_tokens", 0)
    tokens["output"] += u.get("output_tokens", 0)
    tokens["cache_read"] += u.get("cache_read_input_tokens", 0)
    tokens["cache_creation"] += u.get("cache_creation_input_tokens", 0)


def totaled(tokens):
    tokens = dict(tokens)
    tokens["total"] = tokens["input"] + tokens["output"] + tokens["cache_read"] + tokens["cache_creation"]
    return tokens


def phase_boundary(head, since):
    """First commit reachable from `head` whose author date is >= `since`
    (the change's opened_at) — the first implementation commit. Falls back
    to (head, now) when none is found, e.g. run before any commit lands."""
    try:
        out = subprocess.run(
            ["git", "log", head, "--reverse", "--format=%H,%aI",
             f"--since={since.isoformat()}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        out = ""
    if out:
        sha, iso = out.splitlines()[0].split(",", 1)
        return sha, datetime.datetime.fromisoformat(iso)
    return head, datetime.datetime.now(datetime.timezone.utc)


def result_size(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(json.dumps(c)) for c in content)
    return len(json.dumps(content)) if content is not None else 0


def sessionize(events, threshold):
    """Group sorted event timestamps into active spans: a gap longer than
    `threshold` seconds closes the current span. A lone event contributes a
    zero-length span; a single tool run longer than the threshold counts as
    idle — documented, accepted error."""
    spans = []
    for t in sorted(events):
        if spans and (t - spans[-1][1]).total_seconds() <= threshold:
            spans[-1][1] = t
        else:
            spans.append([t, t])
    return spans


def collect(path, since, now):
    tokens = empty_tokens()
    by_model = {}
    by_thread = {"main": empty_tokens(), "subagent": empty_tokens()}
    by_phase_boundary_at = None  # set by caller after computing boundary
    by_tool = {}
    turn_count = 0
    peak_context = 0
    marginal_sum = 0
    eph_5m = 0
    eph_1h = 0
    turns = []  # (timestamp, is_subagent, cache_creation) for phase split
    events = []  # every timestamped line in the window, for sessionization

    tool_names = {}       # tool_use_id -> tool name
    pending_results = []  # [(tool name, result size)] since last turn

    for line in open(path):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = d.get("timestamp")
        if not ts:
            continue
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if not (since <= t <= now):
            continue
        events.append(t)

        message = d.get("message") or {}
        content = message.get("content")

        if d.get("type") == "user" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    name = tool_names.get(c.get("tool_use_id"), "other")
                    pending_results.append((name, result_size(c.get("content"))))
            continue

        u = message.get("usage")
        if not u:
            continue

        # Record this turn's tool_use calls for the *next* turn's attribution.
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    tool_names[c.get("id")] = c.get("name", "unknown")

        add_usage(tokens, u)

        model = message.get("model", "unknown")
        add_usage(by_model.setdefault(model, empty_tokens()), u)

        thread = "subagent" if d.get("isSidechain") else "main"
        add_usage(by_thread[thread], u)

        turn_count += 1
        peak_context = max(peak_context, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0))
        marginal_sum += u.get("input_tokens", 0) + u.get("output_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        cc = u.get("cache_creation") or {}
        eph_5m += cc.get("ephemeral_5m_input_tokens", 0)
        eph_1h += cc.get("ephemeral_1h_input_tokens", 0)

        this_turn_cache = u.get("cache_creation_input_tokens", 0)
        if pending_results and this_turn_cache:
            total_size = sum(size for _, size in pending_results) or 1
            for name, size in pending_results:
                by_tool[name] = by_tool.get(name, 0) + round(this_turn_cache * size / total_size)
        elif this_turn_cache:
            by_tool["other"] = by_tool.get("other", 0) + this_turn_cache
        pending_results = []

        turns.append((t, this_turn_cache, u))

    return {
        "tokens": tokens,
        "by_model": by_model,
        "by_thread": by_thread,
        "by_tool": by_tool,
        "turn_count": turn_count,
        "peak_context": peak_context,
        "marginal_sum": marginal_sum,
        "eph_5m": eph_5m,
        "eph_1h": eph_1h,
        "turns": turns,
        "events": events,
    }


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
    ap.add_argument("--idle-threshold", type=float, default=300.0,
                    help="gap in seconds that closes an active span (default 300)")
    a = ap.parse_args()

    since = datetime.datetime.fromisoformat(a.opened_at)
    now = datetime.datetime.now(datetime.timezone.utc)
    path = pathlib.Path(a.transcript) if a.transcript else newest_transcript()
    data = collect(path, since, now)

    tokens = totaled(data["tokens"])
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    produced_by = {
        "role": "implementer", "kind": "agent", "identity": a.identity,
        "agent": {"vendor": a.vendor, "model": a.model},
    }

    v1 = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": a.head}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/agent-usage/v1",
        "predicate": {
            "change_id": a.change_id,
            "source": "claude-code session transcript",
            "window": {"from": a.opened_at, "to": stamp},
            "tokens": tokens,
            "produced_by": produced_by,
            "produced_at": stamp,
        },
    }
    out_dir = pathlib.Path(a.out)
    (out_dir / "usage.json").write_text(json.dumps(v1, indent=2) + "\n")
    print(f"wrote {out_dir / 'usage.json'}: {tokens['total']:,} tokens "
          f"(in {tokens['input']:,} · out {tokens['output']:,} · "
          f"cache read {tokens['cache_read']:,} · cache write {tokens['cache_creation']:,})")

    boundary_sha, boundary_at = phase_boundary(a.head, since)
    expl_impl = empty_tokens()
    governance = empty_tokens()
    for t, _cc, u in data["turns"]:
        bucket = expl_impl if t <= boundary_at else governance
        add_usage(bucket, u)

    turn_count = data["turn_count"] or 1
    v2 = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": a.head}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/agent-usage/v2",
        "predicate": {
            "change_id": a.change_id,
            "source": "claude-code session transcript",
            "window": {"from": a.opened_at, "to": stamp},
            "tokens": tokens,
            "by_model": {m: totaled(v) for m, v in data["by_model"].items()},
            "by_thread": {k: totaled(v) for k, v in data["by_thread"].items()},
            "by_phase": {
                "exploration_and_implementation": totaled(expl_impl),
                "governance_overhead": totaled(governance),
                "boundary_commit": boundary_sha,
                "boundary_at": boundary_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "by_tool": data["by_tool"],
            "turn_shape": {
                "turn_count": data["turn_count"],
                "peak_context_tokens": data["peak_context"],
                "mean_marginal_work_tokens": data["marginal_sum"] / turn_count,
                "cache_creation_ephemeral_5m": data["eph_5m"],
                "cache_creation_ephemeral_1h": data["eph_1h"],
            },
            "produced_by": produced_by,
            "produced_at": stamp,
        },
    }
    (out_dir / "usage.v2.json").write_text(json.dumps(v2, indent=2) + "\n")
    print(f"wrote {out_dir / 'usage.v2.json'}: {data['turn_count']} turns, "
          f"peak context {data['peak_context']:,}, "
          f"{len(data['by_model'])} model(s), "
          f"governance/{'total' if tokens['total'] else 'n/a'} split at {boundary_sha[:8]}")

    events = data["events"]
    if not events:
        print("no timestamped events in window; skipping activity.json")
        return
    fmt = lambda dt: dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    spans = sessionize(events, a.idle_threshold)
    active = sum((e - s).total_seconds() for s, e in spans)
    activity = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": a.head}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/agent-activity/v1",
        "predicate": {
            "change_id": a.change_id,
            "source": "claude-code session transcript",
            "window": {"from": a.opened_at, "to": stamp},
            "idle_threshold_seconds": a.idle_threshold,
            "active_seconds": round(active, 1),
            "event_count": len(events),
            "session_count": len(spans),
            "first_event_at": fmt(min(events)),
            "last_event_at": fmt(max(events)),
            "sessions": [
                {"from": fmt(s), "to": fmt(e),
                 "active_seconds": round((e - s).total_seconds(), 1)}
                for s, e in spans
            ],
            "produced_by": produced_by,
            "produced_at": stamp,
        },
    }
    (out_dir / "activity.json").write_text(json.dumps(activity, indent=2) + "\n")
    wall = (max(events) - min(events)).total_seconds()
    print(f"wrote {out_dir / 'activity.json'}: {active / 60:.1f} active min "
          f"across {len(spans)} session(s), {len(events):,} events, "
          f"wall clock {wall / 60:.1f} min, idle threshold {a.idle_threshold:g}s")


if __name__ == "__main__":
    main()
