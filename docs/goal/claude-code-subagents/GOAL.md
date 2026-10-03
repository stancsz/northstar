# Goal: Claude Code Subagents skill

Status: skill created and installed; Claude Code use blocked by model access

## Outcome

Create and install a concise Claude Code-specific delegation skill based on Codex Subagents, and exercise it on a bounded independent review in Claude Code.

## Acceptance

- The source is a Markdown skill outside the four-skill Northstar bundle and is installed as a personal Claude Code skill.
- Guidance uses Claude Code's native delegation model, distinguishes subagents from independent sessions and teams, and preserves scope, authority, independent acceptance, integration, and learning.
- A Claude Code session can discover/invoke it and completes a bounded task using native delegation where available.
- Record the actual usage, evidence, and limits in the linked report and evaluation; inspect diffs and local links and run `git diff --check`.

## Constraints

Preserve existing working-tree changes. Do not add this adapter as a fifth Northstar package skill or imply Northstar package acceptance includes it. Do not commit, publish, or incur external side effects beyond the requested local Claude Code use.

## Task and decision

Primary owns the source skill, personal install, invoking Claude Code, evidence, indexes, and integration. The independent skill-use review is assigned to Claude Code through its native subagent tools. [Implementation report](../../reports/claude-code-subagents/implementation.md); [evaluation](../../evals/claude-code-subagents.md).

The source and personal installation are complete. Claude Code CLI `2.1.251` is authenticated, but its configured `claude-sonnet-5` and explicit `claude-haiku-4-5` invocations both report that the model does not exist or is unavailable to the account. One retry with temporary task-local model settings produced the same Haiku error. Preserve this as an incomplete runtime acceptance criterion; reopen when an accessible model is configured.
