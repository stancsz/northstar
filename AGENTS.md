# Working on Northstar

Northstar is a Markdown skill collection. Keep engineering judgment, practices, and useful documentation at the center of changes.

## Start here

1. Read [project direction](docs/northstar/README.md).
2. Read the relevant [goal](docs/goal/README.md) and [evaluations](docs/evals/README.md).
3. Read the skill being changed: [Northstar](skills/northstar/SKILL.md) or [Codex Subagents](skills/codex-subagents/SKILL.md).

## Layout and maintenance

- `skills/<name>/SKILL.md` is the installable entrypoint. Supporting practices and templates are Markdown in that skill's directory.
- `docs/northstar/` owns durable direction, owner standards, reference products, and decisions.
- `docs/goal/<goal>/GOAL.md` owns the outcome and execution record; update the goal index and preserve stable paths.
- `docs/evals/` records what was inspected, observed results, fixes, and limitations. Link to goals and evaluated revisions.
- `docs/misc/` holds other supporting documentation, including installation guides and translations.
- `tmp/<task-or-agent>/` holds disposable artifacts and is ignored.

The root stays limited to README.md, AGENTS.md, LICENSE, .gitignore, and the necessary directories. The `docs/` directory contains only subdirectories; no loose documents or assets belong directly in it. Keep indexes within their category.

Maintain useful docs during work and before handoff. Preserve historical records as history, not current instructions. Keep shared facts in one place and link to them. Do not add runtime scripts, machine contracts, schemas, validators, or generated reporting machinery to this skill collection.

## Review and Git

There is no build or executable test suite. For documentation changes, inspect the diff, check local Markdown links and installation paths, and run `git diff --check`. After moving files, search for obsolete paths and inspect `git status --short`. Review skill changes against actual user scenarios, and record the limits of that review without claiming behavioral testing that did not occur.

Stage intentional files only. Write focused commits with meaningful subjects and explain non-obvious reasons in the body. Follow the user's requested delivery workflow, including direct commits to main when authorized. Do not create PRs against that preference or treat Git authorization as deployment permission.

## Agents, scratch work, and storage

Give subagents the relevant instructions/docs, a write scope, a scoped scratch directory, and responsibility for updating or handing off durable findings. Assign one owner to shared docs. Preserve unrelated and other agents' changes.

Keep loose artifacts in `tmp/`. Promote necessary evidence or reusable content to its proper location before linking it from durable docs. Maintain scoped ignore rules; do not hide documentation images or other legitimate assets with blanket extension ignores.

The project has a shared **100 GB** artifact ceiling (100,000,000,000 bytes) across all agents. Include ignored files, scratch work, caches, downloads, generated output, and attributable copies/worktrees. Measure before large operations and after substantial growth; account for temporary expansion. Address bloat around 80 GB and pause creation that cannot fit. Clean only owned disposable material when safe; preserve user data, others' work, and necessary evidence. Moving output outside the checkout does not evade the budget.
