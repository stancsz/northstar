# Pragmatic Software Architect

For substantive work, use `/northstar` and its [delivery contract](skills/northstar/SKILL.md#delivery-contract); load only the companion that applies. It governs focus-first delivery, diminishing-returns stopping, delegated authority, and CLI/council routing. Keep architecture choices subordinate to the smallest complete result. Repository-specific rules start below; actual platform limits and decisions expressly retained by the owner remain binding.

---

# Working on Northstar

Northstar's core package has five coordinated skills: Northstar, Subagent Orchestration, Independent QA, Advisor Council, and Task Completion Review. It also ships the standalone Agent Soak Testing skill and Windows App Watchdog utility. Keep engineering judgment, practices, and useful documentation at the center of changes.

Keep this repository skills-only. Prioritize concise skill instructions, examples, necessary supporting tools and skill validation. Application code, interfaces, app specifications, deployment plans and app-specific execution records belong in separate repositories. Do not turn this package into an application or runtime platform.

## Start here

1. Start from the current task state and [Northstar](skills/northstar/SKILL.md); take its next useful action.
2. For sustained Northstar work, use the [active goal](docs/goal/README.md). Read project direction, linked evidence or companion guidance only when it can change scope, the next action, or acceptance; a small one-turn task can proceed from its request.

## Layout and maintenance

- `skills/<name>/SKILL.md` defines an installable skill. Install the five coordinated core directories together: `northstar`, `subagent-orchestration`, `independent-qa`, `advisor-council`, and `task-completion-review`. `agent-soak-testing` and `windows-app-watchdog` are independent optional skills and can be installed separately. Northstar is the central coordinator; core companions can also be invoked directly. Subagent Orchestration covers multi-agent delegation across native subagents, Codex CLI workers (`references/cli-dispatch.md`), Claude Code CLI workers (`references/claude-cli-dispatch.md`), and Git worktree isolation (`references/worktree-isolation.md`). Agent Soak Testing guidance does not include or install the separate Soak framework.
- `skills/advisor-council/scripts/` contains the Advisor Council caller and optional reader adapter. Their focused regressions live in `tests/`.
- Keep skills model-agnostic and provider-agnostic: do not put API provider endpoints, gateways, or vendor-pinned models inside shared skill instructions.
- The orchestrator owns and uses `docs/northstar/`: durable direction, owner standards, reference products, and decisions.
- For sustained work that needs durable cross-turn state, the supervisor maintains the existing project goal record and its index entry. Small one-turn tasks use the request and a concise handoff; do not create a goal record just to follow this layout.
- Workers return the artifact, checks, gaps and next action in a concise handoff. Write `docs/reports/<goal>/<task>.md` only when the task or repository explicitly requires a durable report, or when a partial/blocked result needs continuation. Supervisors inspect artifacts and evidence before accepting work. Follow the [handoff practice](skills/northstar/SKILL.md#worker-reports-and-handoffs).
- `docs/evals/` records what was inspected, observed results, fixes, and limitations. Link to goals and evaluated revisions.
- `docs/misc/` holds other supporting documentation, including installation guides and translations.
- `tmp/<task-or-agent>/` holds disposable artifacts and is ignored.

The root stays limited to README.md, AGENTS.md, LICENSE, .gitignore, the owner-requested AGENTS.md.bak backup, and the necessary directories. Treat the backup as historical content, not active instructions. The `docs/` directory contains only subdirectories; no loose documents or assets belong directly in it. Keep indexes within their category.

Maintain useful docs during work and before handoff. Preserve historical records as history, not current instructions. Keep shared facts in one place and link to them. Keep the coordinated workflow package Markdown-first. Task Completion Review has one narrowly scoped, opt-in Stop-hook reviewer adapter; it does not grant platform privileges or install hook configuration automatically. The standalone Windows watchdog skill has a narrowly scoped PowerShell helper because its scheduled check requires executable support; do not add unrelated runtime scripts, machine contracts, schemas, validators, or generated reporting machinery.

## Review and Git

There is no build. For documentation changes, inspect the diff, check local Markdown links and installation paths, and run `git diff --check`. For advisor caller changes or relocation, run `python -B -m pytest -q -p no:cacheprovider tests/test_codex_advisor.py` and `node --test tests/test_pi_reader.mjs` with temporary/cache output under the task's `tmp/` directory. These are offline regressions, not live provider proof. After moving files, search for obsolete paths and inspect `git status --short`. Review skill changes against actual user scenarios, and record the limits of that review without claiming behavioral testing that did not occur.

Stage intentional files only. Write focused commits with meaningful subjects and explain non-obvious reasons in the body. Follow the user's requested delivery workflow, including direct commits to main when authorized. Do not create PRs against that preference or treat Git authorization as deployment permission.

## Agents, scratch work, and storage

Give subagents the relevant instructions/docs, a write scope, and task-owned scratch only when needed. Assign a durable report path only when the task requires one; otherwise a concise final handoff is enough. Workers send proposed changes to direction or goals to the owning role. For sustained goals, supervisors record material task decisions and the orchestrator's acceptance in the existing `GOAL.md`. Assign one editor to shared indexes during concurrent work. Preserve unrelated and other agents' changes. One agent filling multiple roles follows the same document ownership and reporting practices.

Keep loose artifacts in `tmp/`. Promote necessary evidence or reusable content to its proper location before linking it from durable docs. Maintain scoped ignore rules; do not hide documentation images or other legitimate assets with blanket extension ignores.

The project has a shared **100 GB** artifact ceiling (100,000,000,000 bytes) across all agents. Include ignored files, scratch work, caches, downloads, generated output, and attributable copies/worktrees. Measure before large operations and after substantial growth; account for temporary expansion. Address bloat around 80 GB and pause creation that cannot fit. Clean only owned disposable material when safe; preserve user data, others' work, and necessary evidence. Moving output outside the checkout does not evade the budget.
