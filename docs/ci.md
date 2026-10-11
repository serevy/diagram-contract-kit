# CI and review policy

One workflow, `contract-checks.yml`, runs a two-platform job matrix on
`ubuntu-latest` and `windows-latest`, with read-only repository permissions.
It uses Python 3.10 (the minimum supported runtime); local work can
also use newer Python. Actions are pinned by full commit SHA, checkout does not
persist credentials, and there are no secrets, pip dependencies, caches, browser
downloads, paid models, deployment jobs or PR/comment write permissions.
Caching adds no value for this stdlib-only suite.

| Event / change | Expected behavior |
| --- | --- |
| PR to main: scripts, schema, skills, examples, tests, docs, README, license/notices, .gitattributes or this workflow | Run both `deterministic-validation (ubuntu-latest)` and `deterministic-validation (windows-latest)` |
| PR to main: unrelated paths only | Skip this path-scoped workflow |
| Push to main, including a future merge | No automatic run or deployment |
| Manual workflow_dispatch | Run the same offline suite at the selected ref |

The suite lints the positive contract, runs negative regression/graph/provenance
tests, and checks committed SVGs **without regeneration**. Missing/stale SVGs
fail, rather than being recreated and accidentally passing. It also checks Skill
metadata, SVG titles/descriptions, identifiers and locale labels.
It also tests classification without dispatch, generic control/state flows,
greenfield provenance, changed purpose bindings, contradictory typed directives
and unresolved pre-render ambiguity. Existing negative gate/bypass tests remain.
The checkout enforces LF with `.gitattributes` for exact byte hashes/reproduction.
Tests use portable temporary directories. Symlink cases run on Windows when
supported and skip only if the OS denies support/privileges; Linux still runs them.
JSON render-plan output escapes Unicode for portable Windows subprocess decoding.

Path-scoped checks must not be made unconditional branch-required checks: on an
unrelated PR they would remain pending. This repository does not modify branch
rulesets; maintainers should keep that limitation in mind if adding requirements.
There is no `pull_request_target` or privileged writer. Superseded PR runs are
cancelled using a concurrency group. A manual run is available for reproduction.

Reproduce the CI job locally from the checkout root:

```sh
python3 scripts/validate_contract.py examples/fictional/diagram-contract.json
python3 -m unittest discover -s tests -v
python3 scripts/render_example.py --check
git diff --check
```

Use `python` instead of `python3` on Windows. The CI matrix tests the same code
and fixtures on each OS; Linux results alone do not establish Windows support.

Structural PASS does not approve the graph's meaning, visuals or a release.
Human semantic/visual review and explicit publication/merge approval remain
separate. PR creation is review preparation; no auto-merge is configured.
