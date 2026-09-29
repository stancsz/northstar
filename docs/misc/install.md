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

Start with implementation and relevant verification. Use continuation records for work spanning sessions/handoffs, delegation for useful independent workstreams, and QA for the relevant workflow, visual surface or delivery risk; explicit requirements still apply. Agents choose the necessary process without a user mode-selection step.

Keep the target project's existing issues, task files, plans and review records. Orchestrators own direction, supervisors own goal coordination/integration, and workers own deliverables and handoffs; these responsibilities do not require Northstar directory names. The `docs/northstar/`, `docs/goal/`, `docs/reports/`, and `docs/evals/` layout is an optional fallback. Do not create parallel records, copy this repository's history, or reorganize another project to match it. Explicit repository conventions, including this repository's AGENTS.md, remain binding; external tracker writes still require authorization.

## Northstar QA

For delivery inspections, install [Northstar QA](../../skills/northstar-qa/SKILL.md) alongside Northstar as `northstar-qa`:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\northstar-qa" | Out-Null
Copy-Item -Recurse -Force ".\skills\northstar-qa\*" "$env:USERPROFILE\.agents\skills\northstar-qa"
```

Invoke `$northstar-qa` with the artifact, current criteria, and environment. It plans relevant checks, inspects actual output, and distinguishes READY, NOT READY, and UNVERIFIED. Review-only requests do not authorize edits; implementation requests include repairing material defects and checking the fixes. Install the companion beside Northstar so its relative skill link resolves.

## Codex Subagents

Install [skills/codex-subagents](../../skills/codex-subagents/SKILL.md) as `codex-subagents` when coordinated delegation is useful:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\codex-subagents" | Out-Null
Copy-Item -Recurse -Force ".\skills\codex-subagents\*" "$env:USERPROFILE\.agents\skills\codex-subagents"
```

Invoke it as `$codex-subagents`. Use delegation when the independent work justifies the overhead. Every delegate receives the relevant docs, file ownership, scratch location, and shared project storage limit.

For managing roles, fill the [orchestrator](../../skills/codex-subagents/templates/orchestrator.md) or [supervisor](../../skills/codex-subagents/templates/supervisor.md) brief from known facts: result, acceptance, autonomy, coordination, and handoff. Link existing state/evidence instead of duplicating it. Load only the assigned role; add management only for actual dependencies. Internal design is delegated, shared changes go to affected owners, and missing user authority remains an escalation. Copy the whole skill directory on updates so `templates/` is installed too. These briefs guide behavior; platform approval restrictions still apply.

[Back to Northstar](../../README.md)
