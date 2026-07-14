#!/usr/bin/env python3
"""Scaffolder: render every human-readable document from the persistent
knowledge base (.asdlc/knowledge). The knowledge nodes are the single source
of truth; generated files carry a banner and must never be edited directly.

Usage (from the repo root):
  python3 spec/tools/scaffold.py            # (re)generate all documents
  python3 spec/tools/scaffold.py --check    # exit 1 if any generated doc drifts
"""
import json
import pathlib
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
KNOWLEDGE = ROOT / ".asdlc" / "knowledge"
SCHEMAS = ROOT / "spec" / "knowledge"

BANNER = (
    "<!-- GENERATED from .asdlc/knowledge — do not edit directly.\n"
    "     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->\n"
)


def fail(msg):
    print(f"scaffold: error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_knowledge():
    node_schema = json.load(open(SCHEMAS / "node.schema.json"))
    doc_schema = json.load(open(SCHEMAS / "doc.schema.json"))
    node_v = Draft202012Validator(node_schema)
    doc_v = Draft202012Validator(doc_schema)

    nodes = {}
    for p in sorted((KNOWLEDGE / "nodes").rglob("*.yaml")):
        n = yaml.safe_load(p.read_text())
        errs = [e.message for e in node_v.iter_errors(n)]
        if errs:
            fail(f"{p}: {errs}")
        if n["id"] in nodes:
            fail(f"duplicate node id {n['id']} ({p})")
        nodes[n["id"]] = n

    docs = []
    for p in sorted((KNOWLEDGE / "docs").glob("*.yaml")):
        d = yaml.safe_load(p.read_text())
        errs = [e.message for e in doc_v.iter_errors(d)]
        if errs:
            fail(f"{p}: {errs}")
        docs.append((p, d))

    # referential integrity: every referenced node and link target exists
    for p, d in docs:
        for s in d["sections"]:
            for nid in [s.get("node")] + list(s.get("items", [])):
                if nid and nid not in nodes:
                    fail(f"{p}: unknown node {nid!r}")
    for n in nodes.values():
        for link in n.get("links", []):
            if link["to"] not in nodes:
                fail(f"node {n['id']}: link to unknown node {link['to']!r}")
    return nodes, docs


def render(doc, nodes):
    out = [BANNER, f"# {doc['title']}\n"]
    if doc.get("preamble"):
        out.append("\n" + doc["preamble"].rstrip() + "\n")
    for s in doc["sections"]:
        if "literal" in s:
            out.append("\n" + s["literal"].rstrip() + "\n")
            continue
        level = s.get("level", 2)
        if "node" in s:
            n = nodes[s["node"]]
            out.append(f"\n{'#' * level} {n['title']}\n\n{n['body'].rstrip()}\n")
        else:
            out.append(f"\n{'#' * level} {s['heading']}\n")
            if s.get("intro"):
                out.append("\n" + s["intro"].rstrip() + "\n")
            for nid in s["items"]:
                n = nodes[nid]
                out.append(f"\n**{n['title']}**\n{n['body'].rstrip()}\n")
    return "".join(out)


def main():
    check = "--check" in sys.argv
    nodes, docs = load_knowledge()
    drift = []
    for p, d in docs:
        target = ROOT / d["output"]
        content = render(d, nodes)
        current = target.read_text() if target.exists() else None
        if content == current:
            continue
        if check:
            drift.append(d["output"])
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            print(f"wrote {d['output']}")
    if check and drift:
        fail(
            "generated docs drift from knowledge: "
            + ", ".join(drift)
            + " — edit .asdlc/knowledge and rerun spec/tools/scaffold.py"
        )
    print(f"scaffold: {len(nodes)} nodes, {len(docs)} documents, "
          + ("no drift" if check else "generated"))


if __name__ == "__main__":
    main()
