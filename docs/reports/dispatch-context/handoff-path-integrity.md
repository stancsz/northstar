# Handoff path integrity

Updated `skills/codex-subagents/SKILL.md` in “Task brief and handoff” with a concise requirement to use an orchestrator-assigned exact report/handoff path, avoid substituting another location, and report the precise failure if blocked.

Check: `git diff --check -- skills/codex-subagents/SKILL.md docs/reports/dispatch-context/handoff-path-integrity.md` — passed (exit 0; Git emitted only an LF-to-CRLF working-copy warning for the skill file). No tests, builds, or global changes were run.
