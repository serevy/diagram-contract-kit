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
```

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
parity, safe relative artifact/source paths, and explicit review gates. Decision
flows require factual typed result data plus independent rule control into a
deterministic policy gate; semantic outputs cannot control/authorize outcomes
or bypass that gate. Generic graphs can use `component` and `state` roles
without inventing authorization machinery.

Historical sources and current integration sources are separate local records.
The demo stores immutable historical and current snapshots with explicit
fictional version tags. For real work use frozen source snapshots and real
commit/revision identifiers. On integration drift, review a **new** current
revision; never rewrite historical hashes to make a failing check pass.
The validator verifies local byte identity and recorded revision agreement;
it cannot authenticate a Git revision name or prove source correctness.

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
