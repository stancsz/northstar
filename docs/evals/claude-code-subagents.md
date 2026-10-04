# Claude Code Subagents evaluation

Goal: [Claude Code Subagents skill](../goal/claude-code-subagents/GOAL.md)

The initial draft incorrectly guided Claude Code to orchestrate its own subagents. User clarification established the intended use: Codex orchestrates and delegates a bounded worker task to Claude Code through its CLI. The source now reflects that direction and is installed as a personal Codex skill.

Runtime use remains unverified. The configured local endpoint at `127.0.0.1:4000` advertises no Claude models. Direct first-party tests with temporary settings stopped at missing authentication, and saved configuration was not changed. This is a provider/auth dependency, not evidence of skill behavior. See the [implementation handoff](../reports/claude-code-subagents/implementation.md). Reopen runtime evaluation when an accessible Claude model and valid authentication are available.

## Package integration follow-up (2026-10-03)

The owner directed that Claude Code Subagents be included under `skills/` as a packaged skill. The canonical entrypoint is now [skills/claude-code-subagents/SKILL.md](../../skills/claude-code-subagents/SKILL.md), alongside the other four skills. The old duplicate source under `docs/misc/` was removed. Current installation guidance copies all five sibling directories; the skill's host-specific Codex-to-Claude CLI prerequisite remains explicit.

The evaluation inspected README and skill routing, package copy instructions, and local Markdown links; checked that all five installation paths resolve and that the moved entrypoint is present; and ran `git diff --check`. These checks cover documentation and packaging only. No Claude provider call or delegated runtime task succeeded, so runtime use remains unverified as described above. The [implementation report](../reports/claude-code-subagents/implementation.md) records the changed source and limits.
