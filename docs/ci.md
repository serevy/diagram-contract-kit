# CI and review policy

One workflow, `contract-checks.yml`, runs one small job with read-only repository
permissions. It uses Python 3.10 (the minimum supported runtime); local work can
also use newer Python. Actions are pinned by full commit SHA, checkout does not
persist credentials, and there are no secrets, pip dependencies, caches, browser
downloads, paid models, deployment jobs or PR/comment write permissions.
Caching adds no value for this stdlib-only suite.

| Event / change | Expected behavior |
| --- | --- |
| PR to main: scripts, schema, skills, examples, tests, docs, README, license/notices or this workflow | Run `Contract checks / deterministic-validation` |
| PR to main: unrelated paths only | Skip this path-scoped workflow |
| Push to main, including a future merge | No automatic run or deployment |
| Manual workflow_dispatch | Run the same offline suite at the selected ref |

The suite lints the positive contract, runs negative regression/graph/provenance
tests, and checks committed SVGs **without regeneration**. Missing/stale SVGs
fail, rather than being recreated and accidentally passing. It also checks Skill
metadata, SVG titles/descriptions, identifiers and locale labels.

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

Structural PASS does not approve the graph's meaning, visuals or a release.
Human semantic/visual review and explicit publication/merge approval remain
separate. PR creation is review preparation; no auto-merge is configured.
