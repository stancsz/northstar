# Codex Subagents brief write scope and scratch

## Problem

Root `AGENTS.md` requires every subagent assignment to carry a write scope, a scoped scratch directory and an assigned report path. The prior Codex Subagents brief and handoff practice had no dedicated field carrying those together, so an assignment could name exact writable paths in prose while leaving scratch and report setup unassigned, and the prior templates gave no combined write-scope/scratch field to fill. The helper-test brief is the concrete case: it authorized only `tests/test_codex_subagents_helper.py`, prohibited other paths, and assigned neither a task-owned scratch directory nor a report path. Its structured CLI events recorded transient add/update events for `tmp/probe/env-probe.ps1` and `tmp/probe/mutation_check.py`, and the parent later verified those exact files were absent. The worker was not scope-compliant, but two distinct causes must not be conflated: the worker made direct out-of-scope writes that violated the file-only scope it was given, and the orchestrator brief omitted the scratch directory and report path that root `AGENTS.md` required it to assign, because the prior templates had no dedicated combined write-scope/scratch field to make that setup explicit. With no field naming the one scratch directory a task owns, a worker needing scratch space can pick a shared name such as `tmp/probe`, and two concurrent assignments can land on the same shared scratch name.

## Change

Added one required field to every assignment: the write scope, naming the exact writable paths and the task-owned scratch directory.

- `skills/codex-subagents/SKILL.md` (Task brief and handoff): every assignment states a write scope before the work starts — the exact writable source, test and report paths, and either a unique task-owned scratch directory `tmp/<task-id>/` or the literal `scratch none`. A scratch allowance covers only its named directory; shared names such as `tmp/probe` are not scratch allowances; with `scratch none` the delegate writes only the paths named in the write scope. The `Autonomy` bullet now points at that write scope, and `Handoff` takes the required report path from it instead of carrying a separate scratch/report path list.
- `skills/codex-subagents/templates/orchestrator.md`: exposes the same field under the same name, `Write scope and scratch`, with the same wording; `Handoff` takes the required report path from it.
- `skills/codex-subagents/templates/supervisor.md`: same field, same name, same wording; `Handoff` takes the required report path from it and `Autonomy` takes owned paths from it, so one field is the single source for both.

No validator, script, schema, or generated reporting machinery was added. The change is prose in the skill and the two templates.

## Changed paths

- `skills/codex-subagents/SKILL.md`
- `skills/codex-subagents/templates/orchestrator.md`
- `skills/codex-subagents/templates/supervisor.md`
- `docs/reports/dispatch-context/codex-brief-scratch-scope-20261023.md` (this report)

No scratch directory was created. This was a prose change that needed no temporary files, so the assigned `tmp/dispatch-context/codex-brief-scratch-worker-20261023/` path was left unused rather than created to demonstrate it exists.

## Checks

- `git diff --check -- skills/codex-subagents/SKILL.md skills/codex-subagents/templates/orchestrator.md skills/codex-subagents/templates/supervisor.md` returned exit 0 with no whitespace errors; the only output was the pre-existing LF-to-CRLF working-copy warning for those three files.
- Re-read the edited brief section and both template field lists to confirm the field name, wording, and placement match across the three files, and that no other scratch instruction in them contradicts the new field.
- `git status --short` scoped to the three files plus `docs/reports/dispatch-context/` confirms those three files are modified and that this report is the only file this task added.

## Remaining limits

- Prose only. The rule is a clarity requirement in the brief, not an enforced boundary: nothing prevents a worker from writing outside its declared paths, and no runtime check compares a dispatch's actual writes against the declared write scope.
- It covers briefs built from this skill and its templates. An assignment written elsewhere, or dispatched without filling the new field, is unaffected.
- The three edited files already carried unrelated uncommitted changes in the working tree before this task (the loopback route address text, the `Invoke-CodexChild` helper, and other brief additions). That work was left untouched, so the diff for these files mixes pre-existing changes with this task's three edits.
- No behavioral test was run. The original failure was reported from an earlier accepted test task; confirming that a worker now honors the scratch field would need a new dispatch and acceptance run, which this task did not authorize.
