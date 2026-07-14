#!/usr/bin/env python3
"""Metrics over the evidence DAG: derived on demand from evidence + git
history, never stored (see metric-* knowledge nodes for definitions).

Usage (from the repo root):
  python3 spec/tools/metrics.py             # markdown report
  python3 spec/tools/metrics.py --json      # machine-readable
"""
import datetime
import json
import pathlib
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHANGES = ROOT / ".asdlc" / "changes"


def merged_at(change_json):
    out = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%cI", "-1", "--",
         str(change_json.relative_to(ROOT))],
        capture_output=True, text=True, cwd=ROOT)
    s = out.stdout.strip()
    return datetime.datetime.fromisoformat(s) if s else None


def fmt(delta):
    m = int(delta.total_seconds() // 60)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"


def collect():
    rows = []
    for d in sorted(CHANGES.iterdir()):
        cj = d / "change.json"
        if not cj.exists():
            continue
        change = json.loads(cj.read_text())
        opened = datetime.datetime.fromisoformat(change["opened_at"])
        intent_at = None
        intent = d / "evidence" / "intent.json"
        if intent.exists():
            intent_at = datetime.datetime.fromisoformat(
                json.loads(intent.read_text())["predicate"]["produced_at"])
        m = merged_at(cj)
        rows.append({
            "change": change["id"],
            "opened_at": change["opened_at"],
            "merged_at": m.isoformat() if m else None,
            "lead_time_s": (m - intent_at).total_seconds() if m and intent_at else None,
            "cycle_time_s": (m - opened).total_seconds() if m else None,
        })
    return rows


def main():
    rows = collect()
    merged = [r for r in rows if r["merged_at"]]
    if "--json" in sys.argv:
        print(json.dumps({"changes": rows}, indent=2))
        return
    print("# Change metrics (derived from evidence + git; see metric-* nodes)\n")
    print("| Change | Merged | Lead time | Cycle time |")
    print("|---|---|---|---|")
    for r in rows:
        lead = fmt(datetime.timedelta(seconds=r["lead_time_s"])) if r["lead_time_s"] else "—"
        cycle = fmt(datetime.timedelta(seconds=r["cycle_time_s"])) if r["cycle_time_s"] else "—"
        state = r["merged_at"][:16] if r["merged_at"] else "in flight"
        print(f"| {r['change']} | {state} | {lead} | {cycle} |")
    leads = [r["lead_time_s"] for r in merged if r["lead_time_s"]]
    cycles = [r["cycle_time_s"] for r in merged if r["cycle_time_s"]]
    if leads:
        print(f"\n**{len(merged)} merged** · median lead "
              f"{fmt(datetime.timedelta(seconds=statistics.median(leads)))} · "
              f"median cycle {fmt(datetime.timedelta(seconds=statistics.median(cycles)))}")


if __name__ == "__main__":
    main()
