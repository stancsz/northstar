---
name: claude-code-subagents
description: Coordinate Claude Code's native subagents for scoped, independent work, with clear ownership, useful handoffs and inspected integration.
---

# Claude Code Subagents

Use this skill when Claude Code is asked to delegate work, run parallel investigations or implementations, or coordinate reviewers. It adapts the Northstar Codex Subagents practice to Claude Code's native tools. This is an optional host-specific skill, separate from Northstar's four-skill package.

## Choose the delegation path

- Use Claude Code's native `Agent` tool for scoped subagents within this session. Let Claude Code choose foreground or background execution based on whether the result is needed immediately.
- Use separate background sessions only when work needs an independently resumable session or several long-running tasks that must be monitored together. They have separate session state and can create more integration work.
- Use agent teams only when workers need to coordinate directly, share a task board, or interact while work is in flight. Team mode has additional coordination cost and may require experimental feature configuration; do not enable it just to get parallel work.
- Work directly for simple, sequential, tightly coupled, or one-file changes where context continuity matters more than isolated context.

Check which tools, agent types, models, permissions, and team features are available in the current Claude Code session. Do not assume that a feature in current online documentation is enabled locally. If native delegation is unavailable, continue directly when useful or state the exact capability gap.

## Assign bounded work

Before dispatch, define the intended result, observable acceptance, owner, allowed write scope, relevant repository instructions, known facts, dependencies, verification, and handoff destination. Carry forward existing user authority and recovery history; delegation does not grant new external permissions or reset failed attempts.

Split only independent work. Give each worker a distinct write scope; agree on shared interfaces before assigning producer and consumer tasks. Keep one integration owner. Assign a nonauthor reviewer for meaningful delivery; reviewers inspect original intent and actual artifacts and do not write the work they accept. A reviewer can be read-only where Claude Code's available tools permit.

Use a small capable model for bounded work when available and fit for the task. Reserve stronger reasoning for direction, hard integration, consequential choices, and demonstrated capability gaps. Consider all agent calls, review and rework in total effort; do not claim savings from a model label or one successful run.

## Coordinate and integrate

1. Inspect current files and existing task records before assigning work. Preserve user edits and follow the repository's instructions.
2. Dispatch only tasks that can make useful progress independently. Make the role, write boundary, expected artifact, acceptance, permissions, and report format explicit.
3. On completion or failure, inspect changed files and check output. Agent summaries are navigation, not proof. Use a bounded wait or completion event instead of repeatedly polling unchanged status.
4. Resolve dependencies, conflicts, stalled work, and integration defects at the lowest responsible level. Preserve failed attempts; reassigning or switching agents does not reset recovery. Stop repeating an approach unless new evidence changes the diagnosis.
5. Integrate the useful increment, inspect the combined workflow, and obtain an independent verdict on material changes. Repair and recheck findings; the repairer does not certify its own change.
6. Update the project's existing goal, issue, or handoff record with artifacts, checks actually run, observations, gaps, owner, and next action. Record a short lesson that changes the next assignment. Do not create a parallel management system.

Keep coordination proportional to risk and dependency. Do not spawn agents merely because the tool is available, create a supervisor layer without a real integration need, or leave the user as a relay between workers. Continue the authorized work without asking again after a handoff or context change. Escalate only a decision outside the user's mandate or a genuine missing human-held dependency.

## Claude Code references

Use the current [Claude Code subagent guide](https://code.claude.com/docs/en/sub-agents) for host behavior and configuration. It covers the `Agent` tool, custom agent definitions, isolation, teams, background execution, and nesting. Use the [Claude Code skills guide](https://code.claude.com/docs/en/skills) for skill loading and invocation. Check local `claude --help` when CLI flags or installed features matter.
