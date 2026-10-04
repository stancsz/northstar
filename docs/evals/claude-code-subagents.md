# Claude Code Subagents evaluation

Goal: [Claude Code Subagents skill](../goal/claude-code-subagents/GOAL.md)

The initial draft incorrectly guided Claude Code to orchestrate its own subagents. User clarification established the intended use: Codex orchestrates and delegates a bounded worker task to Claude Code through its CLI. The source now reflects that direction and is installed as a personal Codex skill.

Runtime use remains unverified. The configured local endpoint at `127.0.0.1:4000` advertises no Claude models. Direct first-party tests with temporary settings stopped at missing authentication, and saved configuration was not changed. This is a provider/auth dependency, not evidence of skill behavior. See the [implementation handoff](../reports/claude-code-subagents/implementation.md). Reopen runtime evaluation when an accessible Claude model and valid authentication are available.

## Package integration follow-up (2026-10-03)

The owner directed that Claude Code Subagents be included under `skills/` as a packaged skill. The canonical entrypoint is now [skills/claude-code-subagents/SKILL.md](../../skills/claude-code-subagents/SKILL.md), alongside the other four skills. The old duplicate source under `docs/misc/` was removed. Current installation guidance copies all five sibling directories; the skill's host-specific Codex-to-Claude CLI prerequisite remains explicit.

The evaluation inspected README and skill routing, package copy instructions, and local Markdown links; checked that all five installation paths resolve and that the moved entrypoint is present; and ran `git diff --check`. These checks cover documentation and packaging only. No Claude provider call or delegated runtime task succeeded, so runtime use remains unverified as described above. The [implementation report](../reports/claude-code-subagents/implementation.md) records the changed source and limits.

## Deep runtime test follow-up (2026-10-03)

The current CLI is present at version `2.1.251`; help confirms the read-only invocation flags. A catalog request without credentials and a CLI smoke request returned HTTP 401. The CLI's exact error was `API key is not authorized for this gateway` (exit 1); the key was not inspected or printed. A local-only auth-status query showed both an OAuth login and `ANTHROPIC_API_KEY` as the selected source. User settings and inherited process environment configured different base URLs, so the intended pairing of the selected key and settings-file host is unestablished. The failed smoke request used that effective CLI route; no additional requests should be made until the owner confirms/fixes the pairing. No model response, delegated task, file handoff, or integration result was produced, so the end-to-end acceptance criterion remains unverified.

The runtime smoke took about 2.5 minutes despite `--max-turns 1`, showing that turn bounds do not cap network wait/retry duration. Updated the source skill with process-level timeout guidance, settings precedence and credential-source/host matching. Documentation/link/package checks and `git diff --check` pass; this is not independent review, and no behavioral pass is claimed. See the [runtime test report](../reports/claude-code-subagents/implementation.md#deep-runtime-test-follow-up-2026-10-03). Reopen after the owner confirms/fixes the intended auth route; do not route those credentials to another host or substitute another model.
