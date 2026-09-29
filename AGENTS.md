# Working on Northstar

Northstar packages four coordinated skills: Northstar, Codex QA, Codex Subagents and Codex Advisor. Keep engineering judgment, practices, and useful documentation at the center of changes.

## Start here

1. Read [project direction](docs/northstar/README.md).
2. Read the relevant [goal](docs/goal/README.md), its [worker reports](docs/reports/README.md), and [evaluations](docs/evals/README.md).
3. Read the central skill and relevant companion skill: [Northstar](skills/northstar/SKILL.md), [Codex QA](skills/codex-qa/SKILL.md), [Codex Subagents](skills/codex-subagents/SKILL.md), or [Codex Advisor](skills/codex-advisor/SKILL.md).

## Layout and maintenance

- `skills/<name>/SKILL.md` defines one of the four installable skills: `northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`. Install all four sibling directories together. Northstar is the central coordinator; companions can also be invoked directly.
- `skills/codex-advisor/scripts/` contains the migrated Codex Advisor caller and optional reader adapter. Their focused regressions live in `tests/`; the gateway/service implementation stays in Subroute.
- The orchestrator owns and uses `docs/northstar/`: durable direction, owner standards, reference products, and decisions.
- Each supervisor owns and uses its `docs/goal/<goal>/GOAL.md`: outcome, task assignments, execution and acceptance record; maintain its goal index entry and preserve stable paths.
- Each worker produces scoped deliverables and writes `docs/reports/<goal>/<task>.md` for handoff, including partial or blocked work. Supervisors read reports and inspect artifacts before accepting tasks. Follow the [report practice](skills/northstar/SKILL.md#worker-reports-and-handoffs).
- `docs/evals/` records what was inspected, observed results, fixes, and limitations. Link to goals and evaluated revisions.
- `docs/misc/` holds other supporting documentation, including installation guides and translations.
- `tmp/<task-or-agent>/` holds disposable artifacts and is ignored.

The root stays limited to README.md, AGENTS.md, LICENSE, .gitignore, and the necessary directories. The `docs/` directory contains only subdirectories; no loose documents or assets belong directly in it. Keep indexes within their category.

Maintain useful docs during work and before handoff. Preserve historical records as history, not current instructions. Keep shared facts in one place and link to them. Apart from the explicitly requested Codex Advisor helpers and their tests, keep this a Markdown practice package. Do not add unrelated runtime scripts, machine contracts, schemas, validators, or generated reporting machinery.

## Review and Git

There is no build. For documentation changes, inspect the diff, check local Markdown links and installation paths, and run `git diff --check`. For advisor caller changes or relocation, run `python -B -m pytest -q -p no:cacheprovider tests/test_codex_advisor.py` and `node --test tests/test_pi_reader.mjs` with temporary/cache output under the task's `tmp/` directory. These are offline regressions, not live provider proof. After moving files, search for obsolete paths and inspect `git status --short`. Review skill changes against actual user scenarios, and record the limits of that review without claiming behavioral testing that did not occur.

Stage intentional files only. Write focused commits with meaningful subjects and explain non-obvious reasons in the body. Follow the user's requested delivery workflow, including direct commits to main when authorized. Do not create PRs against that preference or treat Git authorization as deployment permission.

## Agents, scratch work, and storage

Give subagents the relevant instructions/docs, a write scope, a scoped scratch directory, and an assigned report path. Workers send proposed changes to direction or goals to the owning role. Supervisors record task decisions and the orchestrator's goal acceptance in `GOAL.md`. Assign one editor to shared indexes during concurrent work. Preserve unrelated and other agents' changes. One agent filling multiple roles follows the same document ownership and reporting practices.

Keep loose artifacts in `tmp/`. Promote necessary evidence or reusable content to its proper location before linking it from durable docs. Maintain scoped ignore rules; do not hide documentation images or other legitimate assets with blanket extension ignores.

The project has a shared **100 GB** artifact ceiling (100,000,000,000 bytes) across all agents. Include ignored files, scratch work, caches, downloads, generated output, and attributable copies/worktrees. Measure before large operations and after substantial growth; account for temporary expansion. Address bloat around 80 GB and pause creation that cannot fit. Clean only owned disposable material when safe; preserve user data, others' work, and necessary evidence. Moving output outside the checkout does not evade the budget.
