#!/usr/bin/env python3
"""Metrics over the evidence DAG: derived on demand from evidence + git
history, never stored (see metric-* knowledge nodes for definitions).

Usage (from the repo root):
  python3 spec/tools/metrics.py             # markdown report
  python3 spec/tools/metrics.py --json      # machine-readable
  python3 spec/tools/metrics.py --html      # self-contained dashboard page
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


# ---------------------------------------------------------------- dashboard

def bar_path(x0, x1, y, h, r=4):
    """Horizontal bar, flat at the baseline end, 4px-rounded at the data end."""
    if x1 < x0:
        x0, x1 = x1, x0
        flat_right = True
    else:
        flat_right = False
    r = min(r, max(0.5, (x1 - x0)), h / 2)
    if flat_right:  # negative bar: rounded on the left
        return (f"M{x1:.1f},{y:.1f} L{x0 + r:.1f},{y:.1f} Q{x0:.1f},{y:.1f} {x0:.1f},{y + r:.1f} "
                f"L{x0:.1f},{y + h - r:.1f} Q{x0:.1f},{y + h:.1f} {x0 + r:.1f},{y + h:.1f} "
                f"L{x1:.1f},{y + h:.1f} Z")
    return (f"M{x0:.1f},{y:.1f} L{x1 - r:.1f},{y:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} "
            f"L{x1:.1f},{y + h - r:.1f} Q{x1:.1f},{y + h:.1f} {x1 - r:.1f},{y + h:.1f} "
            f"L{x0:.1f},{y + h:.1f} Z")


def render_html(rows):
    merged = [r for r in rows if r["merged_at"]]
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True, cwd=ROOT).stdout.strip()
    gen = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    vals = [v for r in merged for v in (r["lead_time_s"], r["cycle_time_s"]) if v is not None]
    vmin_m = min(0.0, min(vals) / 60) if vals else 0.0
    vmax_m = max(0.0, max(vals) / 60) if vals else 1.0
    span = (vmax_m - vmin_m) or 1.0
    vmin_m -= span * 0.06
    vmax_m += span * 0.06

    # geometry
    label_w, pad_r, bar_h, gap_in, gap_grp, top = 250, 24, 12, 2, 16, 8
    plot_w = 640
    width = label_w + plot_w + pad_r
    grp_h = 2 * bar_h + gap_in
    height = top + len(merged) * (grp_h + gap_grp) + 34

    def X(minutes):
        return label_w + (minutes - vmin_m) / (vmax_m - vmin_m) * plot_w

    step = next((s for s in (1, 2, 5, 10, 15, 30, 60, 120, 240)
                 if (vmax_m - vmin_m) / s <= 8), 480)
    t0 = int(vmin_m // step) * step
    ticks = [t for t in range(t0, int(vmax_m) + step, step) if vmin_m <= t <= vmax_m]

    def tfmt(m):
        return f"{int(m) // 60}h" if abs(m) >= 60 and m % 60 == 0 else f"{int(m)}m"

    svg = []
    axis_y = height - 26
    for t in ticks:
        x = X(t)
        cls = "zero" if t == 0 else "grid"
        svg.append(f'<line class="{cls}" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{axis_y}"/>')
        svg.append(f'<text class="tick" x="{x:.1f}" y="{axis_y + 16}" text-anchor="middle">{tfmt(t)}</text>')

    tip_rows = []
    y = top
    for r in merged:
        name = r["change"].replace("CR-20260714-", "")
        lead_m = (r["lead_time_s"] or 0) / 60
        cycle_m = (r["cycle_time_s"] or 0) / 60
        svg.append(f'<text class="label" x="{label_w - 10}" y="{y + grp_h / 2 + 4}" '
                   f'text-anchor="end">{name}</text>')
        svg.append(f'<path class="s1" d="{bar_path(X(0), X(lead_m), y, bar_h)}"/>')
        svg.append(f'<path class="s2" d="{bar_path(X(0), X(cycle_m), y + bar_h + gap_in, bar_h)}"/>')
        tip_rows.append(
            f'<rect class="hit" x="0" y="{y - gap_grp / 2}" width="{width}" height="{grp_h + gap_grp}" '
            f'data-name="{name}" data-lead="{fmt(datetime.timedelta(seconds=r["lead_time_s"]))}" '
            f'data-cycle="{fmt(datetime.timedelta(seconds=r["cycle_time_s"]))}" '
            f'data-merged="{r["merged_at"][:16]}"/>')
        y += grp_h + gap_grp
    svg += tip_rows  # hit targets on top

    leads = sorted(r["lead_time_s"] for r in merged if r["lead_time_s"] is not None)
    cycles = sorted(r["cycle_time_s"] for r in merged if r["cycle_time_s"] is not None)
    med = lambda xs: fmt(datetime.timedelta(seconds=statistics.median(xs))) if xs else "—"

    table = "\n".join(
        f'<tr><td>{r["change"]}</td><td>{(r["merged_at"] or "in flight")[:16]}</td>'
        f'<td class="num">{fmt(datetime.timedelta(seconds=r["lead_time_s"])) if r["lead_time_s"] is not None else "—"}</td>'
        f'<td class="num">{fmt(datetime.timedelta(seconds=r["cycle_time_s"])) if r["cycle_time_s"] is not None else "—"}</td></tr>'
        for r in rows)

    return HTML_TMPL.format(
        gen=gen, sha=sha, n=len(merged), med_lead=med(leads), med_cycle=med(cycles),
        width=width, height=height, svg="\n".join(svg), table=table)


HTML_TMPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>asdlc · change metrics</title>
<style>
  :root {{
    --surface: #fcfcfb; --text-1: #0b0b0b; --text-2: #52514e;
    --border: #e4e3df; --series-1: #2a78d6; --series-2: #1baf7a;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --surface: #1a1a19; --text-1: #ffffff; --text-2: #c3c2b7;
      --border: #3a3936; --series-1: #3987e5; --series-2: #199e70;
    }}
  }}
  body {{ margin: 0 auto; max-width: 960px; padding: 24px 16px 48px;
         background: var(--surface); color: var(--text-1);
         font: 15px/1.5 system-ui, sans-serif; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .sub {{ color: var(--text-2); font-size: 13px; margin-bottom: 24px; }}
  .sub a {{ color: inherit; }}
  .tiles {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }}
  .tile {{ border: 1px solid var(--border); border-radius: 8px; padding: 12px 18px; min-width: 130px; }}
  .tile b {{ display: block; font-size: 26px; font-weight: 650; }}
  .tile span {{ color: var(--text-2); font-size: 12.5px; }}
  .legend {{ display: flex; gap: 18px; font-size: 13px; color: var(--text-2); margin-bottom: 8px; }}
  .sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }}
  figure {{ margin: 0; position: relative; overflow-x: auto; }}
  svg {{ display: block; }}
  .grid {{ stroke: var(--border); stroke-width: 1; }}
  .zero {{ stroke: var(--text-2); stroke-width: 1.25; }}
  .tick {{ fill: var(--text-2); font-size: 11.5px; }}
  .label {{ fill: var(--text-1); font-size: 12.5px; }}
  .s1 {{ fill: var(--series-1); }} .s2 {{ fill: var(--series-2); }}
  .hit {{ fill: transparent; }}
  .hit:hover {{ fill: color-mix(in srgb, var(--text-2) 7%, transparent); }}
  #tip {{ position: fixed; display: none; pointer-events: none; z-index: 2;
         background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
         box-shadow: 0 2px 10px rgba(0,0,0,.15); padding: 8px 10px; font-size: 12.5px; }}
  #tip b {{ display: block; margin-bottom: 2px; }}
  #tip .r {{ color: var(--text-2); }}
  .note {{ color: var(--text-2); font-size: 12.5px; margin: 10px 0 32px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--text-2); font-weight: 600; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
</style></head><body>
<h1>Change metrics</h1>
<div class="sub">Derived from the evidence DAG + git history of
  <a href="https://github.com/jvanheerikhuize/asdlc">jvanheerikhuize/asdlc</a> —
  computed {gen} at <code>{sha}</code>, never stored.
  Definitions: the <code>metric-*</code> knowledge nodes.</div>
<div class="tiles">
  <div class="tile"><b>{n}</b><span>merged changes</span></div>
  <div class="tile"><b>{med_lead}</b><span>median lead time</span></div>
  <div class="tile"><b>{med_cycle}</b><span>median cycle time</span></div>
</div>
<div class="legend">
  <span><i class="sw" style="background:var(--series-1)"></i>Lead time (intent → merged)</span>
  <span><i class="sw" style="background:var(--series-2)"></i>Cycle time (opened → merged)</span>
</div>
<figure>
<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img"
     aria-label="Grouped bar chart of lead and cycle time per merged change">
{svg}
</svg>
<div id="tip"></div>
</figure>
<p class="note">Negative values are kept deliberately: the 2026-07-14 records carry
hand-authored, future-skewed intent timestamps — the first defect these metrics
caught (see <code>leftover-change-scaffolder</code>).</p>
<table>
<thead><tr><th>Change</th><th>Merged</th><th class="num">Lead</th><th class="num">Cycle</th></tr></thead>
<tbody>
{table}
</tbody>
</table>
<script>
const tip = document.getElementById('tip');
for (const el of document.querySelectorAll('.hit')) {{
  el.addEventListener('mousemove', e => {{
    tip.innerHTML = '<b>' + el.dataset.name + '</b>' +
      '<span class="r">merged ' + el.dataset.merged + '</span><br>' +
      'lead ' + el.dataset.lead + ' · cycle ' + el.dataset.cycle;
    tip.style.display = 'block';
    tip.style.left = Math.min(e.clientX + 14, innerWidth - 240) + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  }});
  el.addEventListener('mouseleave', () => tip.style.display = 'none');
}}
</script>
</body></html>
"""


def main():
    rows = collect()
    merged = [r for r in rows if r["merged_at"]]
    if "--json" in sys.argv:
        print(json.dumps({"changes": rows}, indent=2))
        return
    if "--html" in sys.argv:
        print(render_html(rows))
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
