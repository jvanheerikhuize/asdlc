#!/usr/bin/env python3
"""Produce ASDLC evidence statements — GitHub binding, v0.1 (dev-unsigned).

Statements are written as plain JSON files into the Change Record's
evidence directory in the CI workspace; the verifier reads them in
--dev-unsigned mode. DSSE/Sigstore signing replaces this writer without
changing any statement's shape.
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

PT = "https://github.com/jvanheerikhuize/asdlc/spec/predicates"


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def statement(head, ptype, predicate):
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "head", "digest": {"gitCommit": head}}],
        "predicateType": f"{PT}/{ptype}",
        "predicate": predicate,
    }


def cmd_verdict(a):
    pred = {
        "change_id": a.change_id,
        "control_id": a.control,
        "verdict": a.verdict,
        "summary": a.summary,
        "produced_by": {"role": a.role, "kind": "ci", "identity": "github:github-actions"},
        "produced_at": now(),
    }
    if a.details_uri:
        pred["details_uri"] = a.details_uri
    out = pathlib.Path(a.out) / f"{a.control.lower()}-verdict.json"
    out.write_text(json.dumps(statement(a.head, "control-verdict/v1", pred), indent=2) + "\n")
    print(f"wrote {out} ({a.verdict})")


def cmd_approval(a):
    """Transcribe a '/asdlc approve <head-sha-prefix>' comment by a bound
    release-approver into approval/v1. The sha binding means new commits
    void the approval — re-approval is deliberate, not an oversight."""
    import yaml

    manifest = yaml.safe_load(open(a.manifest))
    approvers = set(manifest["role_bindings"].get("release-approver", []))
    comments = json.loads(
        subprocess.check_output(
            ["gh", "api", f"repos/{a.repo}/issues/{a.pr}/comments", "--paginate"]
        )
    )
    pat = re.compile(r"^/asdlc approve ([0-9a-f]{7,40})\b")
    found = None
    for c in comments:
        m = pat.match(c["body"].strip())
        if not m:
            continue
        if not a.head.startswith(m.group(1)):
            continue
        if f"github:{c['user']['login']}" not in approvers:
            print(f"ignoring approval by {c['user']['login']}: not a bound release-approver")
            continue
        found = c
    if not found:
        print("no valid approval comment for this head sha; gate will deny")
        return
    pred = {
        "change_id": a.change_id,
        "approval_type": "review",
        "approver": {
            "role": "release-approver",
            "identity": f"github:{found['user']['login']}",
        },
        "platform_event": {
            "provider": "github",
            "kind": "approval_comment",
            "url": found["html_url"],
            "event_id": str(found["id"]),
        },
        "produced_by": {
            "role": "transcription-workflow",
            "kind": "ci",
            "identity": "github:github-actions",
        },
        "produced_at": now(),
    }
    out = pathlib.Path(a.out) / "approval-review.json"
    out.write_text(json.dumps(statement(a.head, "approval/v1", pred), indent=2) + "\n")
    print(f"wrote {out} (approved by {found['user']['login']})")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verdict")
    v.add_argument("--control", required=True)
    v.add_argument("--verdict", required=True, choices=["pass", "fail"])
    v.add_argument("--summary", required=True)
    v.add_argument("--role", required=True)
    v.add_argument("--change-id", required=True)
    v.add_argument("--head", required=True)
    v.add_argument("--out", required=True)
    v.add_argument("--details-uri")
    v.set_defaults(fn=cmd_verdict)

    ap = sub.add_parser("approval")
    ap.add_argument("--change-id", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default="asdlc.yaml")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", required=True)
    ap.set_defaults(fn=cmd_approval)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
