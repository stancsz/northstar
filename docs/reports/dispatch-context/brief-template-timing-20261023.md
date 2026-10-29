# Brief templates: parent-enforced dispatch timing

Goal: [clear, economical subagent dispatch context](../../goal/dispatch-context/GOAL.md). This report is the worker handoff for one bounded documentation increment; it is not an acceptance verdict.

## Changed paths

- `skills/codex-subagents/templates/orchestrator.md`
- `skills/codex-subagents/templates/supervisor.md`
- `docs/reports/dispatch-context/brief-template-timing-20261023.md` (this file)

No other path was written. No commit, push, publish, build, package or cleanup was run. No route, model alias, credential or global setting was changed.

## Increment

Both briefs gained one matching field, placed between `Coordination` and `Handoff`:

> - Dispatch timing: <parent-enforced task-sized checkpoint and hard handoff deadline; longer tasks name the intermediate artifact required at each checkpoint; on a missed checkpoint or deadline the parent stops the worker and decides the next disposition; no universal minute value>

The wording is identical in the orchestrator and supervisor templates, so either parent can fill it the same way.

Acceptance mapping:

- Asks the assigning parent to set a task-sized checkpoint and a hard handoff deadline.
- States that the parent enforces both, and that a missed checkpoint or deadline makes the parent stop the worker and decide the next disposition rather than wait or retry silently.
- Requires longer tasks to name the intermediate artifact required at each checkpoint.
- Names no minute value and sets no universal duration; the checkpoint is sized to the task.
- Adds no generic task approval and no second approval stage.
- Existing fields (Result, Acceptance, Functions and separation, Guidance, Inference route/smoke, Autonomy, Write scope and scratch, Coordination, Handoff) are unchanged by this increment, as are all existing links.

## Checks run

- Exact scoped diff inspected: `git diff -- skills/codex-subagents/templates/orchestrator.md skills/codex-subagents/templates/supervisor.md`.
- `git diff --check` run for those two files only.
- Relative Markdown links in the two templates resolved and confirmed present on disk (6 local links per template, all existing); no link was added or changed by this increment.
- Targeted line-ending and trailing-whitespace check on the two templates and this report (this report is untracked, so `git diff --check` does not cover it).

## Observations and limits

- The scoped diff against HEAD also shows pre-existing unstaged edits in both templates that were already in the working tree before this task: the `Inference` route address `localhost` to `127.0.0.1`, a `Write scope and scratch` field, and `Handoff` wording. They belong to another worker's change and were preserved unchanged; only the `Dispatch timing` line was added here.
- Prose-only change. No test suite, live dispatch trial or behavioral test was run, and none is claimed. `git diff --check` covers whitespace only.
- Independent acceptance remains with the parent; this handoff records what changed and what was actually checked.

## Tooling note

This worker ran inside the delegated CLI session. The native terminal and file-edit tools exposed by that session (`exec_command` for reading, checking and diffing; `apply_patch` for editing) were used directly; no second CLI was launched and no route or credential was touched. The parent invoked the documented `Invoke-CodexChild -UseObservedSubrouteSettings -DisablePlugins` helper with workspace-write, provider `subroute`, alias `default`, Responses, and the loopback endpoint `127.0.0.1:4000/v1`; that configuration was left unchanged.

## Gaps

- No independent acceptance of the new field's wording or effect; the parent owns that.
- Templates are filled by hand per dispatch, so nothing here demonstrates that a real dispatch actually used the field.
