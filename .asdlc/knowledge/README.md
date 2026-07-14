<!-- GENERATED from .asdlc/knowledge — do not edit directly.
     Edit the knowledge nodes, then run: python3 spec/tools/scaffold.py -->
# Persistent knowledge base

The repo's memory: everything the prose used to say, as typed, addressable
knowledge. Generated documents are views; this directory is the truth.

## How this knowledge base works

- **Nodes** (`nodes/<type>/<id>.yaml`, schema
  `spec/knowledge/node.schema.json`) are the single source of truth: one
  addressable fact, decision, risk, obligation, convention, roadmap item,
  or status record each. Agents read nodes as context; link them with
  typed edges (`links:`) as relationships emerge.
- **Doc manifests** (`docs/*.yaml`, schema
  `spec/knowledge/doc.schema.json`) compose nodes into the human-readable
  documents; `python3 spec/tools/scaffold.py` renders them, `--check`
  (wired into the spec-check workflow) fails CI on drift.
- **Never edit a generated `.md`** — they carry a banner and CI rejects
  hand edits. Edit the node, regenerate, commit both.
- Knowledge changes ride PRs like everything else, so the knowledge base
  has the same provenance as the code it describes.
