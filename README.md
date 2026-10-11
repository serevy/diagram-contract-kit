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

The motivating bug was an incorrect brief that required a physical tabletop
instrument while the intended deliverable was a software architecture chart.
The generator followed that brief. Our regression blocks the mismatch before
generation; it does not blame the renderer. See [case provenance](THIRD_PARTY_NOTICES.md).

**Structural lint does not understand arbitrary prose contradictions.** Purpose
text is separate from typed renderer directives, and changing it blocks generation
until reconciled with sources. Producers must use the validated `--render-plan`,
never append `brief.use` as a prompt. A wrongly rebound purpose may still pass
lint; unresolved meaning must be clarified before generation.

## Quick start

Python 3.10+ and Git are sufficient. No package installation, browser,
network access or credentials are required after checkout.

```sh
git clone https://github.com/serevy/diagram-contract-kit.git
cd diagram-contract-kit
python3 scripts/validate_contract.py examples/fictional/diagram-contract.json
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

## Use with Codex / Astra Low

Keep this checkout available and install only our skill in the target project's
Codex skill directory. From the target project, replace `/path/to/kit`:

```sh
mkdir -p .agents/skills
cp -R /path/to/kit/skills/diagram-contract .agents/skills/
```

Start or refresh Codex in that project, select **GPT-6 Astra** with **Low**
reasoning effort in the available model controls, and invoke:

```text
Use $diagram-contract from /path/to/kit. Inspect this repo's current README
and architecture docs/ADRs/PDDRs. Make a factual software architecture
contract before rendering. Record source revisions and byte hashes, facts,
assumptions, entity/edge IDs, separate authority boundaries, en/ja labels,
SVG outputs and pending human review gates. Validate it with the kit CLI
using this repository as --root. Stop rendering if the contract fails.
Separate purpose prose from typed rendering.directives; mark unresolved meaning
before generation and use only the validated --render-plan for drawing.
For classification-only flows, do not invent a policy/authorization gate.
Return the contract and validation result; do not publish or merge.
```

For a quick agent smoke exercise, ask it to validate the fictional contract and
the bad physical-instrument fixture, report exit 0 vs 1, and explain which
requirement needs correction. No paid API calls or nested agent runner are
needed. Model availability is supplied by the host; the skill does not select
or install a model. Automated tests cover the skill format and deterministic
workflow, not a measured Astra generation benchmark.

Other Agent Skills-compatible agents can load the same skill directory using
their own installation conventions. This kit follows the
[Agent Skills specification](https://agentskills.io/specification); it does not
require a vendor-specific skill installer.

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
