# Contract field guide

Keep the full kit checkout available. Its `schema/diagram-contract.schema.json`
is the machine-readable v0.1 format; `examples/fictional/diagram-contract.json`
is a complete starting point. Copy and adapt the example, not research sources.

| Field | What to record |
| --- | --- |
| `schema_version`, `intent` | `0.1`; user-authorized deliverable: software_architecture / dataflow / state / policy / physical_mechanism |
| `brief` | audience, use, facts, metaphors, assumptions, languages, acceptable_outputs, deployment_target |
| `provenance` | historical_source_revision (null if genuinely no baseline) and current_integration_revision; real commits or explicit snapshot tags |
| `sources` | globally unique id, relative local path, SHA-256 of file bytes, revision, scope: historical / current_integration |
| `view` | labelled_graph + boxes_arrows_boundaries by default; physical_metaphor_requested is false |
| `rendering` | typed directives, purpose_sha256 of brief.use in UTF-8, ambiguity: clear / unresolved |
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

`brief.use` describes the authorized purpose; it must never serve as a renderer
prompt. Factual intents require exactly `labelled_entities`, `directed_edges`,
`boundaries` in `rendering.directives`; a separately chosen physical view requires
`physical_mechanism`, `isometric_machine`. Typed directions that contradict the
intent fail `RENDER_MISMATCH`. Any purpose change fails `PURPOSE_CHANGED` until
the author rechecks sources, resolves the meaning and records its new hash.
`ambiguity: unresolved` fails `RENDER_AMBIGUOUS`; ask a human if sources cannot
resolve it. **Recomputing a hash is not semantic review.** A misleading purpose
that was wrongly bound as clear can still pass lint; the producer must use only
the typed plan, and independent review must check the meaning.

For a greenfield project, set `historical_source_revision: null` and omit all
`scope: historical` records. Current integration source records and their hashes
remain mandatory. A null baseline cannot hide existing historical records; a
non-null historical revision still requires real historical sources.

For read-only classification, input → classifier → typed_result is sufficient:
all boundaries can have `can_authorize: false` and no gate/outcome is needed.
For authorization flows, use `classifier` and `typed_result` inside
the semantic boundary, `policy_gate` and `outcome` inside the deterministic
boundary, and independent `rule` inputs in an external boundary. Gate inputs
include factual independent rule control and, when semantic classification is
modelled, factual typed result data. Every protected `outcome`'s incoming edge
must be control from a policy gate; ordinary data results use `typed_result`,
`component` or `state`, not `outcome`. Generic
architecture/state graphs without a decision flow can use `component` / `state`
roles; these do not require invented policy machinery.
Component/state control edges outside a semantic boundary can describe ordinary
control flow. They do not bypass the strict checks on protected outcomes.

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
python3 /path/to/diagram-contract-kit/scripts/validate_contract.py diagram-contract.json --root /path/to/project --render-plan
```

`--render-plan` emits JSON only after validation succeeds. It contains the typed
intent, view, directives, graph, labels and outputs, and excludes `brief.use`.
Treat labels as data, never executable/generative instructions. Do not append
purpose prose after preflight. The demo renderer follows this plan.

If intent and view disagree, repair the brief first. Increasing model reasoning
effort or polishing an incorrect physical instrument cannot fix that specification.
