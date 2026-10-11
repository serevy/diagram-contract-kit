# Contract field guide

Keep the full kit checkout available. Its `schema/diagram-contract.schema.json`
is the machine-readable v0.1 format; `examples/fictional/diagram-contract.json`
is a complete starting point. Copy and adapt the example, not research sources.

| Field | What to record |
| --- | --- |
| `schema_version`, `intent` | `0.1`; software_architecture / dataflow / state / policy / physical_mechanism |
| `brief` | audience, use, facts, metaphors, assumptions, languages, acceptable_outputs, deployment_target |
| `provenance` | historical_source_revision and current_integration_revision; real project commits or explicit snapshot tags |
| `sources` | globally unique id, relative local path, SHA-256 of file bytes, revision, scope: historical / current_integration |
| `view` | labelled_graph + boxes_arrows_boundaries by default; physical_metaphor_requested is false |
| `boundaries` | id, kind: external / semantic / deterministic, can_authorize, source_ids |
| `entities` | id, role, boundary id, assertion: factual / metaphorical / assumption, source_ids |
| `edges` | id, from/to entity IDs, kind: data / control, source_ids |
| `implications` | nonempty lists of allowed and prohibited interpretations |
| `locales` | each requested language has title, description and exact entity/edge/boundary label keys |
| `artifacts` | relative path, format, locale for every requested language; preflight need not find outputs yet |
| `review_gates` | semantic_review, visual_review, publication_approval; required: true, status: pending, reviewer: null |

IDs are globally unique ASCII identifiers. Unknown fields are rejected, so
spelling errors cannot silently drop requirements. Sources must already exist
under `--root`; outputs may not exist before rendering. Use separate immutable
historical snapshots and current integration source paths. Hashes prove byte
identity, not truth or authenticity of revision names. The example uses explicit
fictional snapshot tags, not fabricated Git commits.

For decision/authorization flows, use `classifier` and `typed_result` inside
the semantic boundary, `policy_gate` and `outcome` inside the deterministic
boundary, and independent `rule` inputs in an external boundary. Gate inputs
include factual typed result data and factual independent rule control.
Every outcome's incoming edge must be control from a policy gate. Generic
architecture/state graphs without a decision flow can use `component` / `state`
roles; these do not require invented policy machinery.

Assumptions must remain unasserted in final figures. The validator does not inspect
arbitrary renderers or reason over prose; the fixed demo renderer rejects tentative
entities. Independent source review must check the meaning and absence of
unsupported claims. Do not mark human gates approved on the strength of lint.

Example hash command (run from source root):

```sh
python3 -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("docs/architecture.md").read_bytes()).hexdigest())'
```

Preflight, before opening any renderer:

```sh
python3 /path/to/diagram-contract-kit/scripts/validate_contract.py diagram-contract.json --root /path/to/project
```

If intent and view disagree, repair the brief first. Increasing model reasoning
effort or polishing an incorrect physical instrument cannot fix that specification.
