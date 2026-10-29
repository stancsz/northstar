# Guidance bounds for dispatch briefs

Goal: dispatch-context. Task: bound the Guidance placeholder in the Codex Subagents brief templates so a future task brief names exact inputs, states validation ownership, and excludes broad reads that cannot affect acceptance.

## Changes

- [orchestrator.md](../../../skills/codex-subagents/templates/orchestrator.md), Guidance bullet (line 8) only. The placeholder now requires the brief to name the exact path **plus the relevant heading or line range** for applicable repository instructions and source/test facts; to name the existing validation command to run **or** state that validation is parent-owned; and to list the concrete unrelated reads and tools excluded because they cannot affect acceptance, asking the parent for a missing exact input instead of starting broad discovery.
- [supervisor.md](../../../skills/codex-subagents/templates/supervisor.md), Guidance bullet (line 8) only. Same wording; the two bullets are byte-identical.
- This report: `docs/reports/dispatch-context/guidance-bounds-20261023.md`.

No other file was created or edited. No new brief field, approval step, agent layer, or command-count cap was added. Scratch: none.

## Preserved

- The brief responsibilities stay in the same order and wording: intended value, must-know facts needed now, next action, fallback or escalation trigger, and the source-instruction rule (repository instructions and essential source/test facts go in the prompt, or are named by exact path).
- The supporting-background-only clause and the never-tell-a-worker-to-skip-required-instructions clause are unchanged.
- The role/accountability model (the orchestrator and supervisor body text, including the differing Autonomy wording) is untouched.
- No arbitrary length limit was introduced and no existing clause was removed; the added text constrains input specificity and ownership, not brief size.
- Pre-existing dirty work in both templates (the Inference route wording, Write scope and scratch, Dispatch timing, and Handoff bullets, plus the earlier Guidance wording) was left exactly as found; only the Guidance bullet was edited.

## Checks

- `git diff --check -- skills/codex-subagents/templates/orchestrator.md skills/codex-subagents/templates/supervisor.md` → exit 0, no whitespace errors. The `LF will be replaced by CRLF` warning is repo-wide and pre-existing; the same warning appears for files this task never touched, and both templates remain wholly LF (26 lines each).
- Scoped diff review of the two templates confirmed the edit is confined to the Guidance bullet; no line-ending churn and no other hunk was introduced by this task.
- Re-read line 8 of both templates after editing and confirmed the two bullets are identical.

## Unverified and parent-owned

- The parent owns the final Markdown link/fragment check and the untracked-report whitespace check. No ad-hoc link or fragment validator was created or run here, and no `GOAL.md` or `SKILL.md` content was read.
- The revised placeholder is template wording only. It was not exercised by a live dispatch, so the behavioral claim that a worker skips a full-file read, names the validation command, or asks the parent for a missing input remains untested by this change.
- No goal, skill prose, index, test, route, model alias, provider, credential, global setting, or sandbox change was made, and no commit or push was attempted.

## Parent acceptance

The parent independently confirmed both Guidance bullets are identical, all nine local template links resolve to files, both templates have no trailing whitespace, and the report's two relative links resolve with no trailing whitespace. Scoped `git diff --check` passed for the templates. The report's template links were normalized from absolute Windows paths to repository-relative paths for portability.

The worker completed within the five-minute deadline with exit 0, `turn.completed`, 14 completed native command calls, and six file-change lifecycle events confined to the two template bullets and this report. Usage was 334,809 input tokens (300,643 cached), 8,887 output, and 5,097 reasoning; cost unknown. This one completion shows a bounded brief can produce a scoped doc handoff on the configured route, but does not establish that the template caused the improvement or that delegation is economical. The exact template has not yet been used to generate and dispatch a subsequent task brief.
