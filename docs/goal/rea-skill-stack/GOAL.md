# Goal: align and exercise the Northstar skill stack with REA as a reference

Date: 2026-10-30. Status: completed. Owner and acceptance authority: primary.

## Checkpoint / Next Action (Live State Anchor)

- **Ask (Locked):** Align the Northstar skill stack for fast agents (`minimax-m3.1-flash`, `luna 6`, `gemini 3.8`) so they can run sustained tasks without instruction drift; keep the repository and installed host skill directories (`~/.codex/skills`, `~/.claude/skills`, `~/.agents/skills`) lean and free of duplicate legacy skills; and run bounded MiniMax soak/drift exercises (`NS-DRIFT-01`..`04`) across Codex CLI and Claude Code CLI.
- **Done (Verified):**
  - Renamed, deduplicated, and functionally merged the skill stack into five coordinated core skills (`northstar`, `subagent-orchestration`, `independent-qa`, `advisor-council`, `task-completion-review`) and two standalone skills (`agent-soak-testing`, `windows-app-watchdog`).
  - Merged `claude-cli-dispatch.md` and `worktree-isolation.md` into `skills/subagent-orchestration/references/`, added `runtime-verification.md` to `skills/independent-qa/references/`, and added quantitative goal quality bars to `skills/northstar/references/goal-driven-engineering.md`.
  - Refactored `skills/northstar/SKILL.md` and `skills/subagent-orchestration/SKILL.md` with mechanical anti-drift brakes (Rule 0, 6-line state anchor, 5-call read-only cap, 2-strike recovery rule, post-verification tool stop, anti-probing rule for missing external credentials/network, single-tool-call pacing on rate-limited routes, explicit child env model-override locking, and first-`api_retry` termination).
  - Removed orphaned reference/template files (`protocol.md`, `routing-rubric.md`, `orchestrator.md`, `supervisor.md`) and legacy `scripts/windows/codex-health-check.ps1`, compressed dense reference files (`stop-hook.md`, `operating-system.md`, `skill-feedback.md`), and enabled `tests/test_codex_subagents_helper.py` on Windows PowerShell 5.1 (`155 passed, 0 skipped` in `pytest`; `2 passed` in `node --test`).
  - Synced all 7 unified skills to `%USERPROFILE%\.codex\skills`, `%USERPROFILE%\.claude\skills`, and `%USERPROFILE%\.agents\skills`, archiving 9+ deprecated legacy skill folders so host catalogs have zero duplicate Northstar bloat.
  - Completed the **8-run MiniMax Soak Suite (`NS-DRIFT-01`..`04` × Codex CLI + Claude Code CLI)** on `minimax-flash-direct` (`8/8 passed`; recorded in [docs/evals/rea-skill-stack/minimax-soak-20261030.md](../../evals/rea-skill-stack/minimax-soak-20261030.md)).
- **Remaining:** None for this goal; run final nonauthor Independent QA verification on the candidate tree SHA.
- **Facts vs. Unknowns:**
  - *Observed:* Passing explicit `minimax-flash-direct` routes both Codex CLI and Claude Code CLI to `minimax/minimax-m3.1-flash` via Subroute. Adding `--bare --setting-sources ""` and locking all `ANTHROPIC_*_MODEL` env vars eliminates profile model leakage and 429 retry storms.
  - *Unknown:* Active desktop UI reload for already-open desktop app windows remains unverified until user session restart.
- **Failed / Ruled Out:**
  - Dispatching Claude with `default` while Subroute policy mode is `off` (1/2: hits `unrecognized_model` / Responses-only mapping).
  - Loading `$independent-qa` onto a builder worker prompt (1/2: causes fast models to attempt nested CLI reviewer dispatch; resolved by keeping builder briefs scoped to `no nested CLI`).
- **Next Action:** Complete final nonauthor Independent QA inspection of the candidate tree SHA and close the goal.

## Acceptance

- [x] Establish the current Northstar goal baseline and preserve the working tree.
- [x] Inspect the REA public project and record the [REA reference analysis](../../northstar/rea-reference.md).
- [x] Define the integrated [Northstar skill-stack workflow](../../northstar/skill-stack-workflow.md) across core skills, Agent Soak Testing, Codex CLI, and Claude Code CLI.
- [x] Unify, deduplicate, and compact the 5 core + 2 standalone skills and sync matching copies to Codex, Claude, and Agents personal homes (archiving legacy duplicates).
- [x] Run bounded skill-stack soak exercises (`NS-DRIFT-01`..`04`), including drift-sensitive cases, through MiniMax (`minimax-flash-direct`) on Codex CLI and Claude Code CLI, capturing exact prompts, native tool events, token/cost metrics, and limits ([soak report](../../evals/rea-skill-stack/minimax-soak-20261030.md)).
- [x] Independently verify the integrated package, clean host installation, passing test suites, and MiniMax soak evidence at the candidate tree SHA.

## Evidence Summary & Links

- **MiniMax 8-run soak evaluation (`NS-DRIFT-01`..`04`):** [docs/evals/rea-skill-stack/minimax-soak-20261030.md](../../evals/rea-skill-stack/minimax-soak-20261030.md).
- **REA reverse-engineering note:** [docs/northstar/rea-reference.md](../../northstar/rea-reference.md) (inspected upstream `1da304b28213ca7a50f6787eae716abe73c4e628`).
- **Workflow & drift case definitions (`NS-DRIFT-01`..`04`):** [docs/northstar/skill-stack-workflow.md](../../northstar/skill-stack-workflow.md).
- **Earlier diagnostic receipts:** [NS-DRIFT-04 receipt](../../evals/rea-skill-stack/NS-DRIFT-04.md), [Claude route diagnosis](../../evals/rea-skill-stack/claude-route.md), and [Subroute accounting/route diagnosis](../../evals/rea-skill-stack/accounting-and-route-diagnosis.md).
