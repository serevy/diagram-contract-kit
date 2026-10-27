# diagram-contract-kit

A minimal Agent Skill and offline verification kit for **diagram requirements
before rendering**. Write a source-backed contract, lint it deterministically,
then draw and independently review it. This is an agent-facing specification
kit; it does not call an image model or authorize publication.

[日本語](README.ja.md) · [Skill](skills/diagram-contract/SKILL.md) ·
[Schema](schema/diagram-contract.schema.json) · [CI policy](docs/ci.md)

Architecture, dataflow, state and policy diagrams default to factual labelled
boxes, arrows and boundaries. A physical mechanism is allowed only as a
separately and explicitly requested metaphor. Semantic judgments remain
advisory data; independent deterministic policy controls authorization.

An example regression covers an incorrect brief that required a physical
tabletop instrument when the intended deliverable was a software architecture
chart. The validator blocks the typed requirement mismatch before rendering;
it does not blame the renderer. See [provenance notes](THIRD_PARTY_NOTICES.md).

**Structural lint does not understand arbitrary prose contradictions.** Purpose
text is separate from typed renderer directives, and changing it blocks generation
until reconciled with sources. Producers must use the validated `--render-plan`,
never append `brief.use` as a prompt. A wrongly rebound purpose may still pass
lint; unresolved meaning must be clarified before generation.

## Quick start (offline demo)

Python 3.10+ and Git are sufficient. No additional Python packages, browser,
network access or credentials are required after checkout. These commands check
the **bundled fictional example**, its tests and its committed SVGs; they do
not generate a diagram contract for your own project.

```sh
git clone https://github.com/serevy/diagram-contract-kit.git
cd diagram-contract-kit
python3 scripts/validate_contract.py examples/fictional/diagram-contract.json
# Optional: run the regression suite and check committed SVGs
python3 -m unittest discover -s tests -v
python3 scripts/render_example.py --check
```

On Windows, use `python` in place of `python3`. The same suite runs on Linux and
Windows CI. `.gitattributes` preserves LF source/SVG bytes on either platform;
symlink tests skip only when Windows lacks symlink support/privileges.

Expected valid-contract output (exit 0):

```text
PASS: structural contract checks only; semantic/visual review and publication approval remain independent.
Review gates: semantic_review=pending, visual_review=pending, publication_approval=pending
```

The invalid fixture intentionally exits **1**:

```sh
python3 scripts/validate_contract.py tests/fixtures/bad-physical-instrument.json
```

```text
FAIL: contract blocked before rendering
VIEW_MISMATCH: software_architecture requires labelled boxes/arrows/boundaries; remove the physical instrument requirement BEFORE rendering. An explicitly requested metaphor belongs in a separate physical_mechanism contract.
VIEW_MISMATCH: factual intent cannot require a physical metaphor; use a separate teaching view
RENDER_MISMATCH: software_architecture renderer directives must be ['boundaries', 'directed_edges', 'labelled_entities']; reconcile the authorized deliverable and rendering instructions BEFORE generation
```

`tests/fixtures/ambiguous-authority.json` also fails: its integration revision
disagrees with its source record and its policy gate is an assumption.
Malformed/unreadable input, duplicate JSON keys and NaN/Infinity exit **2**.
Diagnostics are stable in schema/graph order and contain no timestamps.
The CLI reads local files and writes no artifacts or approval state.

For **your own repository**, use the
[field guide](skills/diagram-contract/references/contract-guide.md) and
[fictional example](examples/fictional/diagram-contract.json) to author a new
`diagram-contract.json`. Replace the example's sources, revisions, hashes and
diagram facts with real local files; the fictional contract is not a drop-in
template that validates arbitrary projects. Then run from your project root:

```sh
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root .
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root . --render-plan
```

The `--render-plan` command emits validated typed rendering data only.
Structural PASS is not permission to publish a diagram.

## Use with an Agent Skills-compatible assistant (optional)

The offline CLI works without any AI assistant. An assistant can help create a
contract from your project's sources and review the resulting diagram, but the
validator itself does not call an AI service.

1. Keep a local checkout of this kit so the Python validator and references
   remain accessible.
2. Install [the diagram-contract skill](skills/diagram-contract/SKILL.md) using
   your assistant host's Agent Skills installation instructions. For example,
   hosts that use a project-level `.agents/skills/` directory can run:

   ```sh
   mkdir -p .agents/skills
   cp -R /path/to/kit/skills/diagram-contract .agents/skills/
   ```

   Installation locations and invocation syntax vary by host. If your host
   does not support skills, read the skill instructions directly.
3. From the target repository, adapt this request for your assistant:

   ```text
   Use the diagram-contract skill from /path/to/kit.
   Inspect this project's current README, architecture docs, and relevant
   ADRs/PDDRs. Before drawing, create a source-backed diagram-contract.json.
   Record real source revisions and SHA-256 hashes, facts versus assumptions,
   stable entity/edge IDs, requested locales and pending human review gates.
   Separate the purpose text from typed rendering directives. Do not invent
   policy gates for read-only flows or treat semantic output as authorization.
   Validate the contract with /path/to/kit/scripts/validate_contract.py,
   using this project as --root. Stop if validation fails or intent is unclear.
   Draw only from the validated --render-plan and independently review the
   semantics and visual result. Return the contract, checks and open reviews;
   do not publish or merge without approval.
   ```

Any Agent Skills-compatible assistant may follow this workflow; compatibility
depends on the host's skill-loading conventions. There is no required model,
provider or reasoning-effort setting. The deterministic tests do not benchmark
any model's diagram quality. AI-assisted steps may have costs set by your host;
the offline CLI does not.

## Contract and validation

Use the [field guide](skills/diagram-contract/references/contract-guide.md) and
[complete example contract](examples/fictional/diagram-contract.json).
For another repository, use an explicit local root:

```sh
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root /path/to/project
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root /path/to/project --render-plan
```

`intent` records the user-authorized deliverable. `rendering.directives` records
bounded producer commands: factual views require `labelled_entities`,
`directed_edges`, `boundaries`; physical views require `physical_mechanism`,
`isometric_machine`. Their disagreement is a pre-generation failure.
`rendering.purpose_sha256` binds the UTF-8 bytes of `brief.use`, so the review's
free-text-only mutation ("Explain the software architecture; build a physical
tabletop instrument") fails `PURPOSE_CHANGED`. After source inspection resolves
the purpose and directives, record a new binding; do not just hash the confusing
text to bypass review. If ambiguity remains, set `rendering.ambiguity` to
`unresolved` and obtain human clarification. This fails `RENDER_AMBIGUOUS`.
The JSON plan excludes purpose prose and only supplies typed directions plus
graph/label data. This prevents purpose prose from becoming renderer commands;
it does not perform generic NLP or prove that recorded intent is truthful.

The bundled JSON Schema (Draft 2020-12) defines fields and types. The stdlib
validator implements exactly its used vocabulary: `$ref` to local `$defs`,
`type`, `required`, `properties`, `additionalProperties`, `items`, `minItems`,
`uniqueItems`, `minProperties`, `minLength`, `pattern`, `const`, and `enum`.
It is not a general JSON Schema engine. A test prevents unsupported vocabulary
from silently entering our schema. Text fields additionally reject whitespace
only values. Unknown contract fields fail, so misspelled requirements cannot
silently disappear. JSON only; there is no YAML parser.

Additional checks cover globally unique IDs, existing graph endpoints and
boundaries, source references and SHA-256, revision/scope agreement, locale key
parity, safe relative artifact/source paths, and explicit review gates.
Read-only input → classifier → typed result diagrams need no policy gate.
Gate checks apply when a factual graph models `policy_gate`, protected `outcome`,
or a boundary with `can_authorize: true`. Such flows require independent rule
control; flows modelling semantic classification also require factual typed
result data into the gate. Semantic outputs cannot control/authorize protected
outcomes or bypass the gate. Generic graphs can use `component` and `state`
roles and ordinary control edges outside the semantic boundary. `outcome` means
a protected action/eligibility result, not an arbitrary data output.

[The classifier-only fixture](tests/fixtures/classifier-only.json) is a positive
read-only dataflow with no protected action, no invented gate and no fabricated
historical baseline. Its output paths are future artifacts, not committed demos.

Historical sources and current integration sources are separate local records.
The demo stores immutable historical and current snapshots with explicit
fictional version tags. For real work use frozen source snapshots and real
commit/revision identifiers. On integration drift, review a **new** current
revision; never rewrite historical hashes to make a failing check pass.
The validator verifies local byte identity and recorded revision agreement;
it cannot authenticate a Git revision name or prove source correctness.
For a greenfield project with no historical baseline, use
`historical_source_revision: null` and omit historical source records. Current
integration source files, revision and hashes remain required. Null plus existing
historical records is rejected, as is a non-null historical revision without
historical sources. Existing frozen snapshots and SVGs are preserved unchanged.

The pre-merge v0.1 format now requires `rendering`; contracts from the initial PR
commit must add it after reconciling their purpose and directives. All bundled
examples and negative fixtures have been updated to the same schema.

## Fictional demo and outputs

The invented flow is request → classification → typed result → independent
deterministic policy → hold / review / eligible. Eligible is a simulated
candidate, not dispatch. No provider thresholds or research results are used.

Open [English SVG](examples/fictional/architecture.en.svg) or
[Japanese SVG](examples/fictional/architecture.ja.svg) locally. The static
figures have title/description, labelled boundaries, directed arrows and a
solid/dashed data/control distinction. They need no JavaScript or motion.

To reproduce these two fixed demos:

```sh
python3 scripts/render_example.py
python3 scripts/render_example.py --check
```

The renderer validates before writing. Its fixed layout is only for this example,
not arbitrary contracts. `--check` requires **all committed outputs to exist**
and match; it does not recreate missing files. For your own diagrams, choose a
small native SVG or an existing renderer after preflight, preserve IDs, leave
assumptions unasserted, then compare the result with its sources.

## Limits and review

Lint is necessary but cannot prove conceptual correctness, multilingual meaning,
readability, source ownership or authenticity. Free-text allowed/prohibited
implications need independent source review. A renderer can still misrepresent
a valid contract; only the fixed demo's byte reproduction, IDs and labels are
checked here. Humans must independently review semantics and visuals and
approve publication. Reset approvals when sources, contracts or artifacts change.
Nothing here publishes, merges, dispatches real actions or calls paid models.

Original contributor-owned files are explicitly MIT licensed; see [LICENSE](LICENSE).
[Anatomy and Yomiyasu](THIRD_PARTY_NOTICES.md) are optional references with
separate upstream copyrights. No upstream skill/code or non-licensed research
source is copied. Adapters, browser QA, interactive previews and deployments
are outside v0.1.
