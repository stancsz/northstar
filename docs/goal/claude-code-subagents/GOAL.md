# Goal: Claude Code Subagents skill

Status: fifth package skill created and installed; end-to-end run blocked because the configured gateway rejects its API key (401)

## Outcome

Create and install a Codex skill that delegates bounded work to Claude Code through its CLI, and exercise it on a bounded assignment.

## Acceptance

- The source is a Markdown skill at `skills/claude-code-subagents/SKILL.md`, installed with the four other sibling skills and in the personal Codex skills directory.
- The root README, central skill, installation guide and contributor instructions identify this as the fifth package skill and preserve the Claude Code-specific host prerequisite.
- Guidance makes Codex the accountable orchestrator and Claude Code a bounded CLI worker, while preserving scope, authority, independent acceptance, integration, and learning.
- Codex can discover/invoke the skill and complete a bounded Claude Code assignment when the local CLI and an accessible model are available.
- Record the actual usage, evidence, and limits in the linked report and evaluation; inspect diffs and local links and run `git diff --check`.

## Constraints

Preserve unrelated working-tree changes. Do not change Claude's provider/model configuration without authorization. Keep the documented runtime-use limitation explicit.

## Task and decision

Primary owns the source skill, package and personal Codex installs, invoking Claude Code, evidence, indexes, and integration. [Implementation report](../../reports/claude-code-subagents/implementation.md); [evaluation](../../evals/claude-code-subagents.md).

The initial version was mistakenly installed as a Claude Code skill. The corrected Codex-oriented source and installation supersede it. Earlier Claude Code CLI `2.1.251` attempts reported unavailable models on a prior route. On 2026-10-03, the current CLI accepted the configured model and flags but its read-only smoke request failed with `401 API key is not authorized for this gateway`. Do not change the configured endpoint or auth path. Preserve end-to-end delegation as unverified; reopen after the gateway accepts the configured API key or the owner supplies a working configured route.
