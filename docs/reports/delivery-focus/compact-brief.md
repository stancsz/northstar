# Compact task-brief guidance

## Ask

Replace the obsolete task-brief mapping and brittle command blacklist in the Codex Subagents skill with a short, self-contained assignment contract. Keep reusable Windows CLI quoting and read-isolation limits in the dispatch reference where absent.

## Acceptance

- The brief covers result/current state, observable acceptance and relevant baseline failure, exact write/scratch/report paths, authority/limits, available instructions/context, parent-owned route/checkpoint/deadline, native tools, no unassigned nested workers, partial/blocked reporting, independent acceptance, and inherited recovery.
- Higher-priority host/repository rules remain controlling; task text is not presented as filesystem isolation. Worker initiative is preserved for relevant investigation without repeating broad rediscovery once context is sufficient.
- Obsolete field mapping and per-command blacklist are removed; only reusable host-specific quoting/isolation guidance is placed in the existing CLI reference.
- Existing headings/anchors and executable helper bytes remain unchanged.

## Changes and checks

- Replaced only `Task brief and handoff` in `skills/codex-subagents/SKILL.md` with a compact contract. Kept its heading/anchor.
- Added concise Windows path-quoting and read-isolation caveats outside the helper in `skills/codex-subagents/references/cli-dispatch.md`.
- Reviewed the edited section against `tmp/prompt-reliability-20261024/baseline` and ran scoped `git diff --check` for the two skill documents; no whitespace errors were reported.
- Did not run the full test suite, helper-equality or link checks, per the assignment; the parent owns helper equality and broader integration review.

## Remaining

Independent acceptance is pending with the parent. This prose review does not establish runtime compliance, filesystem isolation, or reduced command/token use. No other criterion is known unresolved; helper-byte equality and repository link validation remain for the parent.
