# Install and use

This repository contains Markdown skills. Copy the skill directory you want to your agent's skills directory, then invoke it by name.

## Northstar

Install [skills/northstar](../../skills/northstar/SKILL.md) as `northstar`.

For a personal installation in PowerShell, from the repository root:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\northstar" | Out-Null
Copy-Item -Recurse -Force ".\skills\northstar\*" "$env:USERPROFILE\.agents\skills\northstar"
```

Use `$northstar` with your product idea, current project, or outcome. It should read the project's instructions and docs, resolve important ambiguity early, research implementation choices, and critique and verify the real result.

For long sessions, keep the recovery checkpoint in the active goal (or worker report). On continuation: "Use Northstar. Read the active goal and recovery checkpoint, verify current files, and continue the next unmet criterion. Preserve rejected approaches and remaining investigation limits." See [stall recovery](../../skills/northstar/SKILL.md#recover-from-a-stall). Recopy updated skill files to refresh an existing installation; already-running chats may retain earlier instructions, so explicitly reload the file or start a new chat. This is agent guidance, not an enforced runtime watchdog.

In the project being worked on, the orchestrator owns and uses `docs/northstar/`; supervisors own their `docs/goal/<goal>/GOAL.md` and goal index entries; workers produce deliverables and write handoffs in `docs/reports/<goal>/<task>.md`. Supervisors inspect reports and work before recording task acceptance, and the orchestrator accepts integrated goals. Review evidence belongs in `docs/evals/`, other supporting documentation in `docs/misc/`. Only subdirectories belong directly in `docs/`. Northstar helps maintain those records and a concise project-specific `AGENTS.md`. These are the target project's records; do not copy this repository's own goal history into it.

## Codex Subagents

Install [skills/codex-subagents](../../skills/codex-subagents/SKILL.md) as `codex-subagents` when coordinated delegation is useful:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\codex-subagents" | Out-Null
Copy-Item -Recurse -Force ".\skills\codex-subagents\*" "$env:USERPROFILE\.agents\skills\codex-subagents"
```

Invoke it as `$codex-subagents`. Use delegation when the independent work justifies the overhead. Every delegate receives the relevant docs, file ownership, scratch location, and shared project storage limit.

[Back to Northstar](../../README.md)
