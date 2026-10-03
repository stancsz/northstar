# Goal: Claude Code Subagents skill

Status: skill created and installed; Claude Code use blocked by model access

## Outcome

Create and install a Codex skill that delegates bounded work to Claude Code through its CLI, and exercise it on a bounded assignment.

## Acceptance

- The source is a Markdown skill outside the four-skill Northstar bundle and is installed in the personal Codex skills directory.
- Guidance makes Codex the accountable orchestrator and Claude Code a bounded CLI worker, while preserving scope, authority, independent acceptance, integration, and learning.
- Codex can discover/invoke the skill and complete a bounded Claude Code assignment when the local CLI and an accessible model are available.
- Record the actual usage, evidence, and limits in the linked report and evaluation; inspect diffs and local links and run `git diff --check`.

## Constraints

Preserve existing working-tree changes. Do not add this adapter as a fifth Northstar package skill or imply Northstar package acceptance includes it. Do not change Claude's provider/model configuration without authorization.

## Task and decision

Primary owns the source skill, personal Codex install, invoking Claude Code, evidence, indexes, and integration. [Implementation report](../../reports/claude-code-subagents/implementation.md); [evaluation](../../evals/claude-code-subagents.md).

The initial version was mistakenly installed as a Claude Code skill. The corrected Codex-oriented source and installation supersede it. Claude Code CLI `2.1.251` reported its configured `claude-sonnet-5` and explicit `claude-haiku-4-5` models unavailable before the delegated task began. Preserve runtime use as unverified; reopen when the configured provider can serve an accessible model.
