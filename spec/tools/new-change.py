#!/usr/bin/env python3
"""Scaffold a new Change Record: change.json + evidence/intent.json +
evidence/classification.json, with real clock timestamps and a minted
per-date sequence (D14, spec 0.5.0).

The id's 3-digit sequence is minted by listing .asdlc/changes/ for
today's date — never hand-guessed, so it can never predate the record
it orders (the defect leftover-change-scaffolder exists to close).

Usage (from the repo root):
  python3 spec/tools/new-change.py "Title of the change"
  python3 spec/tools/new-change.py "Title" --slug my-slug \
      --problem "..." --acceptance "criterion one" --acceptance "criterion two" \
      --risk low --data none --ai-usage generated --ai-system-tier none \
      --rationale "..." --identity github:jvanheerikhuize --role intent-owner

Any human-authored field omitted on the command line is prompted for
interactively. Run non-interactively by passing every field as a flag.
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHANGES = ROOT / ".asdlc" / "changes"
MANIFEST = ROOT / "asdlc.yaml"


def fail(msg):
    print(f"new-change: error: {msg}", file=sys.stderr)
    sys.exit(1)


def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if not slug or not slug[0].isalnum():
        fail(f"could not derive a slug from title {title!r}; pass --slug")
    return slug


def mint_seq(date):
    prefix = f"CR-{date}-"
    existing = sorted(p.name for p in CHANGES.iterdir() if p.name.startswith(prefix))
    seqs = []
    for name in existing:
        m = re.match(rf"^CR-{date}-(\d{{3}})-", name)
        if m:
            seqs.append(int(m.group(1)))
    return max(seqs, default=0) + 1


def prompt(label, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val or default


def prompt_list(label):
    print(f"{label} (one per line, blank line to finish):")
    items = []
    while True:
        line = input("  - ").strip()
        if not line:
            break
        items.append(line)
    return items


def load_manifest():
    if not MANIFEST.exists():
        fail(f"{MANIFEST} not found — run from a repo that carries asdlc.yaml")
    return yaml.safe_load(MANIFEST.read_text())


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title")
    ap.add_argument("--slug")
    ap.add_argument("--problem")
    ap.add_argument("--acceptance", action="append", default=[], help="repeatable; at least one required")
    ap.add_argument("--out-of-scope", action="append", default=[])
    ap.add_argument("--risk", choices=["low", "medium", "high"])
    ap.add_argument("--data", choices=["none", "internal", "personal", "sensitive"])
    ap.add_argument("--ai-usage", choices=["none", "assisted", "generated"])
    ap.add_argument("--ai-system-tier", choices=["none", "minimal", "limited", "high-risk", "prohibited"])
    ap.add_argument("--rationale")
    ap.add_argument("--role", default="intent-owner")
    ap.add_argument("--identity")
    ap.add_argument("--kind", choices=["human", "agent", "ci"], default="human")
    ap.add_argument("--agent-vendor")
    ap.add_argument("--agent-model")
    args = ap.parse_args()

    manifest = load_manifest()
    spec_version = manifest["spec_version"]
    default_identity = (manifest.get("role_bindings", {}).get(args.role) or [None])[0]

    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    seq = mint_seq(date)
    slug = args.slug or slugify(args.title)
    change_id = f"CR-{date}-{seq:03d}-{slug}"

    change_dir = CHANGES / change_id
    if change_dir.exists():
        fail(f"{change_dir} already exists")

    identity = args.identity or prompt("Identity (role_bindings[{}])".format(args.role), default_identity)
    if not identity:
        fail("identity is required (--identity or a role_bindings default)")

    problem = args.problem or prompt("Problem (independent of any solution)")
    if not problem:
        fail("problem is required")

    acceptance = args.acceptance or prompt_list("Acceptance criteria")
    if not acceptance:
        fail("at least one acceptance criterion is required")

    out_of_scope = args.out_of_scope

    risk = args.risk or prompt("Risk (low/medium/high)", "low")
    data = args.data or prompt("Data (none/internal/personal/sensitive)", "none")
    ai_usage = args.ai_usage or prompt("AI usage (none/assisted/generated)", "generated")
    ai_system_tier = args.ai_system_tier or prompt("AI system tier (none/minimal/limited/high-risk/prohibited)", "none")
    rationale = args.rationale or prompt("Classification rationale")
    if not rationale:
        fail("rationale is required")

    kind = args.kind
    agent = None
    if kind == "agent":
        vendor = args.agent_vendor or prompt("Agent vendor")
        model = args.agent_model or prompt("Agent model")
        if not (vendor and model):
            fail("--agent-vendor and --agent-model are required when --kind agent")
        agent = {"vendor": vendor, "model": model}

    produced_by = {"role": args.role, "kind": kind, "identity": identity}
    if agent:
        produced_by["agent"] = agent

    timestamp = now()

    change = {
        "id": change_id,
        "title": args.title,
        "opened_at": timestamp,
        "opened_by": identity,
        "spec_version": spec_version,
    }

    intent = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": "0" * 40}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/change-intent/v1",
        "predicate": {
            "change_id": change_id,
            "title": args.title,
            "problem": problem,
            "acceptance_criteria": acceptance,
            **({"out_of_scope": out_of_scope} if out_of_scope else {}),
            "produced_by": produced_by,
            "produced_at": timestamp,
        },
    }

    classification = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "change", "digest": {"gitCommit": "0" * 40}}],
        "predicateType": "https://github.com/jvanheerikhuize/asdlc/spec/predicates/classification/v1",
        "predicate": {
            "change_id": change_id,
            "risk": risk,
            "data": data,
            "ai_usage": ai_usage,
            "ai_system_tier": ai_system_tier,
            "rationale": rationale,
            "produced_by": produced_by,
            "produced_at": timestamp,
            "refs": [],
        },
    }

    evidence_dir = change_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    (change_dir / "change.json").write_text(json.dumps(change, indent=2) + "\n")
    (evidence_dir / "intent.json").write_text(json.dumps(intent, indent=2) + "\n")
    (evidence_dir / "classification.json").write_text(json.dumps(classification, indent=2) + "\n")

    print(f"scaffolded {change_dir.relative_to(ROOT)}")
    print("subject.digest.gitCommit is a placeholder (all-zero) — set it to the "
          "actual commit once the change is committed, before evidence is signed.")
    if kind != "ci":
        print("\nBefore opening the PR, record usage evidence for this change "
              "(roadmap-priority-2-metrics-integrity: every merged Change Record "
              "should carry usage evidence) by running, once the implementation "
              "is committed:\n"
              f"  python3 bindings/claude-code/usage.py \\\n"
              f"      --change-id {change_id} --opened-at {timestamp} \\\n"
              f"      --head <commit-sha> --out {evidence_dir.relative_to(ROOT)}\n"
              "If evidence collection is broken or unavailable, that's fine — "
              "the dashboard shows the metric as n/a rather than a misleading "
              "value; it's just skippable, not required.")


if __name__ == "__main__":
    main()
