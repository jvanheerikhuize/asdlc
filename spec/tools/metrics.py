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
import re
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


def afmt(seconds):
    """Agent-cycle durations are often sub-hour; keep sub-minute precision."""
    m = seconds / 60
    return f"{int(m) // 60}h {int(m) % 60:02d}m" if m >= 60 else f"{m:.1f}m"


def tfmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def fmt_by_model(by_model):
    if not by_model:
        return "n/a"
    return " · ".join(f"{m} {tfmt_tokens(n)}" for m, n in sorted(by_model.items(), key=lambda kv: -kv[1]))


def fmt_governance_ratio(r):
    if r is None:
        return "n/a"
    return f"{r * 100:.0f}%"


def collect():
    rows = []
    for d in sorted(CHANGES.iterdir()):
        cj = d / "change.json"
        if not cj.exists():
            continue
        change = json.loads(cj.read_text())
        opened = datetime.datetime.fromisoformat(change["opened_at"])
        m = merged_at(cj)
        lead_time_s = (m - opened).total_seconds() if m else None
        # Agent cycle time comes from agent-activity/v1 evidence: transcripts
        # are not committed, so active time only exists if it was captured at
        # collection time. No backfill — rows predating the predicate stay
        # n/a forever, matching the token-metric precedent.
        activity = None
        activity_path = d / "evidence" / "activity.json"
        if activity_path.exists():
            ap = json.loads(activity_path.read_text())["predicate"]
            activity = {
                "active_s": ap["active_seconds"],
                "sessions": ap["session_count"],
                "idle_threshold_s": ap["idle_threshold_seconds"],
            }
        tokens = None
        usage = d / "evidence" / "usage.json"
        if usage.exists():
            tokens = dict(json.loads(usage.read_text())["predicate"]["tokens"])
            # Work-scoped figure (finding 2, roadmap-priority-2-metrics-integrity):
            # cache_read scales with turns x accumulated session context, not
            # with work done for this change, so it's excluded from the
            # headline total. Derived here, not stored — the raw breakdown
            # (including cache_read) stays in the evidence for transparency.
            tokens["work_tokens"] = (
                tokens.get("input", 0) + tokens.get("output", 0) + tokens.get("cache_creation", 0))
        usage_v2 = None
        usage_v2_path = d / "evidence" / "usage.v2.json"
        if usage_v2_path.exists():
            v2p = json.loads(usage_v2_path.read_text())["predicate"]
            by_model = {m_name: v["total"] for m_name, v in v2p["by_model"].items()}
            gov_total = v2p["by_phase"]["governance_overhead"]["total"]
            v2_total = v2p["tokens"]["total"]
            usage_v2 = {
                "by_model": by_model,
                # roadmap-priority-3-token-granularity exit criterion: fraction
                # of a change's tokens spent after the first implementation
                # commit (evidence pinning, PR description, etc.) rather than
                # on exploration/implementation itself.
                "governance_ratio": (gov_total / v2_total) if v2_total else None,
            }
        rows.append({
            "change": change["id"],
            "opened_at": change["opened_at"],
            "merged_at": m.isoformat() if m else None,
            "lead_time_s": lead_time_s,
            # A negative lead time is arithmetically impossible for a real
            # opened-to-merged measurement; the 2026-07-14 rows hit this from
            # hand-authored, future-skewed opened_at timestamps (see
            # metric-lead-time.yaml). Flag rather than hide: the chart still
            # plots the raw value as the honest record of that bug, but
            # summary figures (table, markdown) render it as n/a.
            "lead_time_inaccurate": lead_time_s is not None and lead_time_s < 0,
            "agent_active_s": activity["active_s"] if activity else None,
            "agent_sessions": activity["sessions"] if activity else None,
            "idle_threshold_s": activity["idle_threshold_s"] if activity else None,
            "tokens": tokens,
            "usage_v2": usage_v2,
        })
    rows.sort(key=lambda r: (r["merged_at"] is None, r["merged_at"] or "", r["change"]))
    # Merge-order number: makes same-day changes orderable even for legacy
    # ids without the per-date seq (grandfathered pre-0.5.0, see D14).
    for i, r in enumerate(rows, 1):
        r["order"] = i if r["merged_at"] else None
    return rows


def short_name(r):
    """Chart/table label: merge-order number + slug (date prefix stripped)."""
    slug = re.sub(r"^CR-[0-9]{8}-", "", r["change"])
    return f"{r['order']} · {slug}" if r["order"] else slug


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

    # geometry shared by all charts
    label_w, pad_r, bar_h, top = 250, 24, 12, 8
    plot_w = 640
    width = label_w + plot_w + pad_r

    def tfmt(m):
        return f"{int(m) // 60}h" if abs(m) >= 60 and m % 60 == 0 else f"{int(m)}m"

    # ---- lead time: axis capped at the p90 so one calendar-time outlier
    # (an overnight gap) can't squash the ±6-minute majority into slivers ----
    lead_vals = [r["lead_time_s"] / 60 for r in merged]
    if len(lead_vals) >= 2:
        cap = statistics.quantiles(lead_vals, n=10, method="inclusive")[8]
    else:
        cap = lead_vals[0] if lead_vals else 1.0
    cap = max(cap, 1.0)
    vmin_m = min(0.0, min(lead_vals)) if lead_vals else 0.0
    vmax_m = cap
    span = (vmax_m - vmin_m) or 1.0
    vmin_m -= span * 0.06
    vmax_m += span * 0.06

    height = top + len(merged) * (bar_h + 10) + 34
    axis_y = height - 26

    def X(minutes):
        return label_w + (minutes - vmin_m) / (vmax_m - vmin_m) * plot_w

    step = next((s for s in (1, 2, 5, 10, 15, 30, 60, 120, 240)
                 if (vmax_m - vmin_m) / s <= 8), 480)
    t0 = int(vmin_m // step) * step
    ticks = [t for t in range(t0, int(vmax_m) + step, step) if vmin_m <= t <= vmax_m]

    svg = []
    for t in ticks:
        x = X(t)
        cls = "zero" if t == 0 else "grid"
        svg.append(f'<line class="{cls}" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{axis_y}"/>')
        svg.append(f'<text class="tick" x="{x:.1f}" y="{axis_y + 16}" text-anchor="middle">{tfmt(t)}</text>')

    hits = []
    y = top
    for r in merged:
        name = short_name(r)
        lead_m = r["lead_time_s"] / 60
        lead_txt = fmt(datetime.timedelta(seconds=r["lead_time_s"]))
        svg.append(f'<text class="label" x="{label_w - 10}" y="{y + bar_h / 2 + 4}" '
                   f'text-anchor="end">{name}</text>')
        if lead_m > vmax_m:
            # Past the p90 cap: bar runs to the plot edge, an axis-break
            # chevron marks the cut, and the exact value is labeled on the
            # bar so the cap never hides information.
            x_end = label_w + plot_w
            svg.append(f'<path class="s1" d="{bar_path(X(0), x_end, y, bar_h)}"/>')
            cx = x_end - 14
            svg.append(f'<path class="cut" d="M{cx:.1f},{y - 2} l-5,{bar_h + 4} '
                       f'm9,-{bar_h + 4} l-5,{bar_h + 4}"/>')
            svg.append(f'<text class="barlabel" x="{cx - 10:.1f}" y="{y + bar_h / 2 + 4}" '
                       f'text-anchor="end">{lead_txt}</text>')
        else:
            svg.append(f'<path class="s1" d="{bar_path(X(0), X(lead_m), y, bar_h)}"/>')
        hits.append(
            f'<rect class="hit" x="0" y="{y - 5}" width="{width}" height="{bar_h + 10}" '
            f'data-name="{name}" data-lead="{lead_txt}" '
            f'data-merged="{r["merged_at"][:16]}"/>')
        y += bar_h + 10
    svg += hits  # hit targets on top

    leads = [r["lead_time_s"] for r in merged if not r["lead_time_inaccurate"]]
    med_lead = fmt(datetime.timedelta(seconds=statistics.median(leads))) if leads else "n/a"

    # ---- agent cycle time: active minutes from agent-activity/v1 ----
    act_rows = [r for r in rows if r["agent_active_s"] is not None]
    activity_section = ""
    act_tile = ""
    if act_rows:
        med_act = statistics.median([r["agent_active_s"] for r in act_rows])
        act_tile = (f'<div class="tile"><b>{afmt(med_act)}</b>'
                    f'<span>median agent cycle time ({len(act_rows)} recorded)</span></div>')
        amax = max(r["agent_active_s"] for r in act_rows) / 60 * 1.06 or 1.0
        h3 = top + len(act_rows) * (bar_h + 10) + 34
        ax3 = h3 - 26

        def X3(minutes):
            return label_w + minutes / amax * plot_w

        step3 = next((s for s in (1, 2, 5, 10, 15, 30, 60, 120, 240)
                      if amax / s <= 7), 480)
        svg3 = []
        t = step3
        while t <= amax:
            svg3.append(f'<line class="grid" x1="{X3(t):.1f}" y1="{top}" x2="{X3(t):.1f}" y2="{ax3}"/>')
            svg3.append(f'<text class="tick" x="{X3(t):.1f}" y="{ax3 + 16}" '
                        f'text-anchor="middle">{tfmt(t)}</text>')
            t += step3
        svg3.append(f'<line class="zero" x1="{X3(0)}" y1="{top}" x2="{X3(0)}" y2="{ax3}"/>')
        yy = top
        hits3 = []
        for r in act_rows:
            name = short_name(r)
            active_m = r["agent_active_s"] / 60
            svg3.append(f'<text class="label" x="{label_w - 10}" y="{yy + bar_h / 2 + 4}" '
                        f'text-anchor="end">{name}</text>')
            svg3.append(f'<path class="s2" d="{bar_path(X3(0), X3(active_m), yy, bar_h)}"/>')
            hits3.append(
                f'<rect class="hit" x="0" y="{yy - 5}" width="{width}" height="{bar_h + 10}" '
                f'data-name="{name}" data-active="{afmt(r["agent_active_s"])} active" '
                f'data-detail="{r["agent_sessions"]} session(s) · '
                f'idle threshold {r["idle_threshold_s"]:g}s"/>')
            yy += bar_h + 10
        svg3 += hits3
        act_na = len(rows) - len(act_rows)
        na_note = (f' {act_na} of {len(rows)} changes predate this evidence and stay '
                   f'<b>n/a</b> — no backfill, matching the token-metric '
                   f'precedent.') if act_na else ""
        activity_section = f"""
<h2>Agent cycle time per change</h2>
<div class="sub">How long the agent actively worked, sessionized from the
harness transcript's per-message timestamps (<code>agent-activity/v1</code>
evidence): a gap longer than the recorded idle threshold closes an active
span, and active time sums the spans — nights and manual repo work don't
count. Recorded from <code>CR-20260716-003-agent-activity-evidence</code>
onward.{na_note}</div>
<figure>
<svg viewBox="0 0 {width} {h3}" width="{width}" height="{h3}" role="img"
     aria-label="Bar chart of agent active working time per recorded change">
{chr(10).join(svg3)}
</svg>
</figure>
"""

    # ---- agent tokens: different unit, its own plot and axis ----
    tok_rows = [r for r in rows if r["tokens"]]
    tokens_section = ""
    tok_tile = ""
    if tok_rows:
        total = sum(r["tokens"]["work_tokens"] for r in tok_rows)
        tok_tile = (f'<div class="tile"><b>{tfmt_tokens(total)}</b>'
                    f'<span>agent tokens, work-scoped ({len(tok_rows)} recorded)</span></div>')
        tmax = max(r["tokens"]["work_tokens"] for r in tok_rows) * 1.06
        h2 = top + len(tok_rows) * (bar_h + 10) + 34
        ax2 = h2 - 26

        def X2(v):
            return label_w + v / tmax * plot_w

        step2 = next((s for s in (1e3, 2e3, 5e3, 1e4, 2.5e4, 5e4, 1e5, 2.5e5,
                                  5e5, 1e6, 2e6, 5e6) if tmax / s <= 7), 1e7)
        svg2 = []
        t = step2
        while t <= tmax:
            svg2.append(f'<line class="grid" x1="{X2(t):.1f}" y1="{top}" x2="{X2(t):.1f}" y2="{ax2}"/>')
            svg2.append(f'<text class="tick" x="{X2(t):.1f}" y="{ax2 + 16}" '
                        f'text-anchor="middle">{tfmt_tokens(int(t))}</text>')
            t += step2
        svg2.append(f'<line class="zero" x1="{X2(0)}" y1="{top}" x2="{X2(0)}" y2="{ax2}"/>')
        yy = top
        hits2 = []
        for r in tok_rows:
            name = short_name(r)
            tk = r["tokens"]
            svg2.append(f'<text class="label" x="{label_w - 10}" y="{yy + bar_h / 2 + 4}" '
                        f'text-anchor="end">{name}</text>')
            svg2.append(f'<path class="s1" d="{bar_path(X2(0), X2(tk["work_tokens"]), yy, bar_h)}"/>')
            hits2.append(
                f'<rect class="hit" x="0" y="{yy - 5}" width="{width}" height="{bar_h + 10}" '
                f'data-name="{name}" data-tokens="{tfmt_tokens(tk["work_tokens"])} work-scoped" '
                f'data-detail="in {tfmt_tokens(tk["input"])} · out {tfmt_tokens(tk["output"])} · '
                f'cache write {tfmt_tokens(tk["cache_creation"])} · '
                f'cache read {tfmt_tokens(tk["cache_read"])} (excluded, scales with context not work) · '
                f'gross total {tfmt_tokens(tk["total"])}"/>')
            yy += bar_h + 10
        svg2 += hits2
        tok_na = len(rows) - len(tok_rows)
        na_note = (f' {tok_na} of {len(rows)} changes have no recorded usage evidence (n/a, '
                   f'not shown below).') if tok_na else ""
        tokens_section = f"""
<h2>Agent tokens per change</h2>
<div class="sub">Self-reported by the agent from its harness transcript
(<code>agent-usage/v1</code> evidence); recorded from
<code>CR-20260714-token-metric</code> onward. Work-scoped: excludes
cache-read tokens, which scale with turns &times; accumulated session
context rather than work done for the change.{na_note} The table's
<b>By model</b> and <b>Governance overhead</b> columns come from
<code>agent-usage/v2</code> evidence (recorded from
<code>roadmap-priority-3-token-granularity</code> onward); changes with
only v1 evidence show <b>n/a</b> there. Governance overhead is the
share of a change's tokens spent after its first implementation commit
(evidence pinning, PR description, etc.) rather than on exploration and
implementation itself.</div>
<figure>
<svg viewBox="0 0 {width} {h2}" width="{width}" height="{h2}" role="img"
     aria-label="Bar chart of agent tokens per recorded change">
{chr(10).join(svg2)}
</svg>
</figure>
"""

    def lead_cell(r):
        if r["lead_time_s"] is None:
            return "n/a"
        if r["lead_time_inaccurate"]:
            return '<span title="hand-authored, future-skewed opened_at timestamp — see the note below">n/a</span>'
        return fmt(datetime.timedelta(seconds=r["lead_time_s"]))

    def act_cell(r):
        if r["agent_active_s"] is None:
            return '<span title="predates agent-activity/v1 evidence — no backfill">n/a</span>'
        return afmt(r["agent_active_s"])

    table = "\n".join(
        f'<tr><td class="num">{r["order"] or "n/a"}</td>'
        f'<td>{r["change"]}</td><td>{(r["merged_at"] or "in flight")[:16]}</td>'
        f'<td class="num">{lead_cell(r)}</td>'
        f'<td class="num">{act_cell(r)}</td>'
        f'<td class="num">{tfmt_tokens(r["tokens"]["work_tokens"]) if r["tokens"] else "n/a"}</td>'
        f'<td>{fmt_by_model(r["usage_v2"]["by_model"]) if r["usage_v2"] else "n/a"}</td>'
        f'<td class="num">{fmt_governance_ratio(r["usage_v2"]["governance_ratio"]) if r["usage_v2"] else "n/a"}</td></tr>'
        for r in rows)

    return HTML_TMPL.format(
        gen=gen, sha=sha, n=len(merged), med_lead=med_lead,
        width=width, height=height, svg="\n".join(svg), table=table,
        act_tile=act_tile, activity_section=activity_section,
        tok_tile=tok_tile, tokens_section=tokens_section)


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
  h2 {{ font-size: 16px; margin: 34px 0 4px; }}
  .sub {{ color: var(--text-2); font-size: 13px; margin-bottom: 24px; }}
  .sub a {{ color: inherit; }}
  .tiles {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }}
  .tile {{ border: 1px solid var(--border); border-radius: 8px; padding: 12px 18px; min-width: 130px; }}
  .tile b {{ display: block; font-size: 26px; font-weight: 650; }}
  .tile span {{ color: var(--text-2); font-size: 12.5px; }}
  figure {{ margin: 0; position: relative; overflow-x: auto; }}
  svg {{ display: block; }}
  .grid {{ stroke: var(--border); stroke-width: 1; }}
  .zero {{ stroke: var(--text-2); stroke-width: 1.25; }}
  .tick {{ fill: var(--text-2); font-size: 11.5px; }}
  .label {{ fill: var(--text-1); font-size: 12.5px; }}
  .s1 {{ fill: var(--series-1); }} .s2 {{ fill: var(--series-2); }}
  .cut {{ stroke: var(--surface); stroke-width: 3; fill: none; }}
  .barlabel {{ fill: #ffffff; font-size: 11px; }}
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
  {act_tile}
  {tok_tile}
</div>
<h2>Lead time per merged change</h2>
<div class="sub">Change opened (<code>change.json</code> <code>opened_at</code>)
to merged into <code>main</code> — calendar time, nights and manual work
included. The axis is capped at the p90 so one outlier can't squash the
rest: bars past the cap run to the plot edge, an axis-break chevron marks
the cut, and the exact value is labeled on the bar.</div>
<figure>
<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img"
     aria-label="Bar chart of lead time per merged change, axis capped at the 90th percentile">
{svg}
</svg>
<div id="tip"></div>
</figure>
<p class="note">The chart keeps negative bars deliberately: the 2026-07-14 records carry
hand-authored, future-skewed <code>opened_at</code> timestamps — the first defect these
metrics caught (see <code>leftover-change-scaffolder</code>) — and the chart is the
honest historical record. The table below shows <b>n/a</b> for those same rows'
lead time, since a negative duration isn't a meaningful summary answer.</p>
{activity_section}
{tokens_section}
<table>
<thead><tr><th class="num">#</th><th>Change</th><th>Merged</th><th class="num">Lead</th><th class="num">Agent cycle</th><th class="num">Tokens</th><th>By model</th><th class="num">Governance overhead</th></tr></thead>
<tbody>
{table}
</tbody>
</table>
<script>
const tip = document.getElementById('tip');
for (const el of document.querySelectorAll('.hit')) {{
  el.addEventListener('mousemove', e => {{
    tip.innerHTML = el.dataset.tokens
      ? '<b>' + el.dataset.name + '</b>' + el.dataset.tokens +
        '<br><span class="r">' + el.dataset.detail + '</span>'
      : el.dataset.active
      ? '<b>' + el.dataset.name + '</b>' + el.dataset.active +
        '<br><span class="r">' + el.dataset.detail + '</span>'
      : '<b>' + el.dataset.name + '</b>' +
        '<span class="r">merged ' + el.dataset.merged + '</span><br>' +
        'lead ' + el.dataset.lead;
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
    print("| # | Change | Merged | Lead time | Agent cycle | Agent tokens | By model | Governance overhead |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if r["lead_time_s"] is None:
            lead = "n/a"
        elif r["lead_time_inaccurate"]:
            lead = "n/a (negative — see metric-lead-time caveat)"
        else:
            lead = fmt(datetime.timedelta(seconds=r["lead_time_s"]))
        cycle = afmt(r["agent_active_s"]) if r["agent_active_s"] is not None else "n/a"
        state = r["merged_at"][:16] if r["merged_at"] else "in flight"
        toks = tfmt_tokens(r["tokens"]["work_tokens"]) if r["tokens"] else "n/a"
        v2 = r["usage_v2"]
        by_model = fmt_by_model(v2["by_model"]) if v2 else "n/a"
        gov = fmt_governance_ratio(v2["governance_ratio"]) if v2 else "n/a"
        print(f"| {r['order'] or 'n/a'} | {r['change']} | {state} | {lead} | {cycle} | {toks} | {by_model} | {gov} |")
    leads = [r["lead_time_s"] for r in merged if not r["lead_time_inaccurate"] and r["lead_time_s"]]
    acts = [r["agent_active_s"] for r in rows if r["agent_active_s"] is not None]
    if leads:
        line = (f"\n**{len(merged)} merged** · median lead "
                f"{fmt(datetime.timedelta(seconds=statistics.median(leads)))}")
        if acts:
            line += f" · median agent cycle {afmt(statistics.median(acts))} ({len(acts)} recorded)"
        print(line)


if __name__ == "__main__":
    main()
