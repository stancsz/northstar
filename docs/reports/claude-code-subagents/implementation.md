# Claude Code Subagents implementation handoff

Status: Codex skill source and personal installation complete; delegated Claude Code run blocked by model access

Deliverable: [Claude Code Subagents Codex skill](../../misc/claude-code-subagents/SKILL.md), maintained outside Northstar's four-skill package.

Installed at `~/.codex/skills/claude-code-subagents/SKILL.md`; SHA-256 matches the source (`C0D418BBB0E51E93E8820EBF39AB6EEC41A81C948AB57AFDB2ECF0EC6C75DA6B`). The skill makes Codex the orchestrator and Claude Code a bounded CLI worker.

Earlier Claude Code use attempts, before correcting the skill's intended host, stopped before any skill invocation or agent dispatch:

- Default model selected `claude-sonnet-5`; CLI reported that it did not exist or was unavailable to this account.
- `--model sonnet` resolved to the same unavailable configured model.
- Explicit `--model claude-haiku-4-5` returned the same model availability error. A retry with a task-local settings file overriding only `ANTHROPIC_MODEL` and the Sonnet default returned that Haiku error too.

Follow-up diagnosis: the configured `ANTHROPIC_BASE_URL` targets `127.0.0.1:4000`. A read-only `GET /v1/models` returned no Claude model IDs, explaining why the configured Sonnet and Haiku requests fail on that route. A process-only direct Anthropic test with user settings excluded reported `Not logged in`; a second test with a temporary official-endpoint override and blank credential environment variables also reported `Not logged in`. No saved provider/auth configuration was changed and no gateway credential was sent to Anthropic.

No successful delegated work, skill discovery by Claude Code, or independent verdict is claimed. To complete the runtime criterion, Claude Code needs either valid first-party Anthropic authentication for the official endpoint or a Claude model exposed by the configured gateway. Temporary settings and outputs are in ignored `tmp/claude-code-subagents/`.
