# Claude Code Subagents evaluation

Goal: [Claude Code Subagents skill](../goal/claude-code-subagents/GOAL.md)

Source and personal installation were inspected; both files have matching hashes and the installed copy is self-contained. The skill preserves the core Northstar coordination rules and adds Claude Code's distinction between in-session subagents, independent background sessions, and teams. Local Claude Code documentation describes these mechanisms; the CLI reports version `2.1.251`.

Runtime use remains unverified. Four read-only CLI attempts failed before skill invocation or subagent dispatch because configured Sonnet and Haiku model identifiers were reported as unavailable. This is an environment/access blocker, not evidence of skill behavior. No independent verdict or integration result is claimed. See the [implementation handoff](../reports/claude-code-subagents/implementation.md). Reopen runtime evaluation when an accessible model is configured.
