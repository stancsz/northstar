---
name: claude-code-subagents
description: Delegate bounded work from Codex to Claude Code through its CLI, then inspect and integrate the result. Use when Claude Code is requested or adds useful independent capacity.
---

# Claude Code Subagents

Use this skill from Codex when the user asks to have Claude Code do work, or when a separate Claude Code run can make useful independent progress. Codex remains the orchestrator and accepting owner; Claude Code is a delegated worker. This is an optional Codex skill outside Northstar's four-skill package.

## Decide whether to delegate

- Delegate only when a bounded Claude Code task can improve speed, independent review, or focused expertise enough to justify startup, coordination, integration, and model cost.
- Keep simple, sequential, tightly coupled, or one-file work with the current agent unless the user specifically requests Claude Code.
- Check that `claude` is available and inspect its local version/help when the invocation depends on specific CLI options. Do not read or print credentials, tokens, or full provider settings.
- If the CLI or an accessible model is unavailable, report the exact failure and continue directly where useful. Do not change global Claude configuration or cycle through model guesses without authorization and new evidence.

## Give Claude Code a bounded assignment

Before launching it, define the result, observable acceptance, repository/base state, relevant instructions, owned write scope, verification, allowed side effects, and handoff format. Include known facts, unresolved assumptions, existing recovery history, and the next action. Carry the user's existing authority into the assignment; delegation cannot expand it.

Use Claude Code as one worker for one coherent scope. Do not let Codex and Claude Code write the same files at the same time. For shared-checkout work, pause Codex edits until Claude finishes. For parallel work, give each writer a distinct checkout based on the exact state it needs; verify the checkout's base before dispatch, since a CLI worktree option may start from a default branch rather than the current working state. Preserve uncommitted user changes.

For read-only review or investigation, prefer a noninteractive, read-only invocation when the local CLI supports it, for example:

```powershell
claude -p --permission-mode plan --max-turns 8 "Review <scope> against <criteria>. Do not edit files. Return evidence, findings, and remaining uncertainty."
```

For implementation or tasks requiring permission prompts, start Claude Code in the intended working directory with a clear task brief and use the configured permission flow. Never use `--dangerously-skip-permissions` to make delegation convenient. Bound runtime/turns where the chosen invocation supports it; do not assume that a noninteractive flag enforces a task deadline or limits all work.

Claude Code may use its own native subagents for internal parallel work, but Codex still assigns one outcome and write boundary to the Claude Code run. Do not add another management layer unless Claude Code's task genuinely needs one.

## Integrate the handoff

1. Inspect the checkout and current diff before launch so user edits and the delegated base are clear.
2. On return, inspect changed files, command output, and actual checks. A Claude summary is a handoff, not proof.
3. Resolve gaps or conflicts within the mandate, preserving failed attempts. Do not ask Claude Code to retry an unchanged failed approach or treat reassignment as a recovery reset.
4. Integrate the smallest useful result and independently verify material acceptance criteria. If Claude Code authored or repaired the work, it cannot independently accept that same work.
5. Record the artifact, revision/base, checks actually run, observed result, gaps, and next action in the project's existing records. Count Codex setup, Claude usage, review, and rework as total effort; one successful task does not prove savings.

Use `claude -p` output or the interactive session transcript as evidence only for what it shows. Check `git status` after work and keep commits, pushes, publication, deployment, and external contact inside the user's actual authorization.

## Claude Code references

Use local `claude --help` for installed CLI flags and the official [CLI reference](https://code.claude.com/docs/en/cli-reference). The [subagent guide](https://code.claude.com/docs/en/sub-agents) describes Claude Code's internal workers; they are distinct from this Codex-to-Claude delegation pattern.
