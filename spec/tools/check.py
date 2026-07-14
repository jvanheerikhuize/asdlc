#!/usr/bin/env python3
"""Spec self-check: schemas are valid, golden bundles satisfy them, and —
when opa is available — the G4 policy yields exactly the expected outcome
for every golden bundle. Exit 0 iff everything holds.

Usage: python3 spec/tools/check.py  (from the repo root)
"""
import json
import pathlib
import shutil
import subprocess
import sys

SPEC = pathlib.Path(__file__).resolve().parent.parent
GOLDEN = SPEC / "examples" / "golden"
failures = []


def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        failures.append(msg)


def schema_checks():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    schemas = {}
    for p in list((SPEC / "predicates").glob("*.json")) + [
        SPEC / "change-record.schema.json",
        SPEC / "manifest.schema.json",
    ]:
        schemas[p.name] = json.load(open(p))
        Draft202012Validator.check_schema(schemas[p.name])
    check(True, f"{len(schemas)} schemas parse and are valid 2020-12 schemas")

    resources = []
    for name, s in schemas.items():
        r = Resource.from_contents(s)
        resources.append((s["$id"], r))
        resources.append((name, r))
    registry = Registry().with_resources(resources)

    by_pt = {
        "change-intent/v1": "change-intent.v1.schema.json",
        "classification/v1": "classification.v1.schema.json",
        "control-verdict/v1": "control-verdict.v1.schema.json",
        "approval/v1": "approval.v1.schema.json",
    }
    for bundle_dir in sorted(GOLDEN.iterdir()):
        bundle = json.load(open(bundle_dir / "input.json"))
        v = Draft202012Validator(schemas["change-record.schema.json"], registry=registry)
        errs = [e.message for e in v.iter_errors(bundle["change"])]
        check(not errs, f"{bundle_dir.name}: change record schema-valid {errs or ''}")
        for s in bundle["statements"]:
            st = s["statement"]
            key = st["predicateType"].rsplit("/predicates/", 1)[1]
            v = Draft202012Validator(schemas[by_pt[key]], registry=registry)
            errs = [e.message for e in v.iter_errors(st)]
            check(not errs, f"{bundle_dir.name}: {key} statement {s['meta']['sha256'][:8]} schema-valid {errs or ''}")


def policy_checks():
    opa = shutil.which("opa")
    if not opa:
        print("skip: opa not on PATH — policy evaluation runs in CI")
        return
    for bundle_dir in sorted(GOLDEN.iterdir()):
        expected = json.load(open(bundle_dir / "expected.json"))
        out = subprocess.run(
            [opa, "eval", "--format=json",
             "-d", str(SPEC / "gates" / "g4-merge.rego"),
             "-i", str(bundle_dir / "input.json"),
             "data.asdlc.gates.g4"],
            capture_output=True, text=True)
        check(out.returncode == 0, f"{bundle_dir.name}: opa eval succeeds ({out.stderr.strip()[:200]})")
        if out.returncode != 0:
            continue
        result = json.loads(out.stdout)["result"][0]["expressions"][0]["value"]
        allow = result.get("allow", False)
        deny = sorted(result.get("deny", []))
        check(allow == expected["allow"],
              f"{bundle_dir.name}: allow={allow}, expected {expected['allow']} (deny: {deny})")
        for must in expected.get("deny_must_include", []):
            check(must in deny, f"{bundle_dir.name}: deny includes {must!r}")
        if expected["allow"]:
            check(deny == [], f"{bundle_dir.name}: no deny reasons on a passing bundle {deny or ''}")


schema_checks()
policy_checks()
print(f"\n{'PASS' if not failures else 'FAIL'}: {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
