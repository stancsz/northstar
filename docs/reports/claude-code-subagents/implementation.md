# Claude Code Subagents implementation handoff

Status: Codex skill source, five-skill package integration and personal installation complete; delegated Claude Code run blocked by the configured gateway rejecting its API key (401)

Deliverable: [Claude Code Subagents Codex skill](../../../skills/claude-code-subagents/SKILL.md), now maintained as the fifth sibling in Northstar's package. The prior personal installation remains at `~/.codex/skills/claude-code-subagents/SKILL.md`.

Installed at `~/.codex/skills/claude-code-subagents/SKILL.md`; SHA-256 matches the source (`C0D418BBB0E51E93E8820EBF39AB6EEC41A81C948AB57AFDB2ECF0EC6C75DA6B`). The skill makes Codex the orchestrator and Claude Code a bounded CLI worker.

Earlier Claude Code use attempts, before correcting the skill's intended host, stopped before any skill invocation or agent dispatch:

- Default model selected `claude-sonnet-5`; CLI reported that it did not exist or was unavailable to this account.
- `--model sonnet` resolved to the same unavailable configured model.
- Explicit `--model claude-haiku-4-5` returned the same model availability error. A retry with a task-local settings file overriding only `ANTHROPIC_MODEL` and the Sonnet default returned that Haiku error too.

Follow-up diagnosis: the configured `ANTHROPIC_BASE_URL` targets `127.0.0.1:4000`. A read-only `GET /v1/models` returned no Claude model IDs, explaining why the configured Sonnet and Haiku requests fail on that route. A process-only direct Anthropic test with user settings excluded reported `Not logged in`; a second test with a temporary official-endpoint override and blank credential environment variables also reported `Not logged in`. No saved provider/auth configuration was changed and no gateway credential was sent to Anthropic.

No successful delegated work, skill discovery by Claude Code, or independent verdict is claimed. To complete the runtime criterion, Claude Code needs either valid first-party Anthropic authentication for the official endpoint or a Claude model exposed by the configured gateway. Temporary settings and outputs are in ignored `tmp/claude-code-subagents/`.

## Package integration follow-up (2026-10-03)

Following the owner's direction, moved the canonical entrypoint into `skills/claude-code-subagents/SKILL.md` as the fifth packaged skill. Updated the English and Chinese READMEs, installation guide, central skill routing, repository direction, contributor instructions, goal index and this handoff. The prior `docs/misc/claude-code-subagents/SKILL.md` entrypoint was removed to leave one canonical source. The skill's delegation guidance is unchanged; its package-boundary sentence now identifies it as the fifth sibling. The personal installation was refreshed from the canonical source.

Package-path, local-link and content checks plus `git diff --check` are recorded in [the evaluation follow-up](../../evals/claude-code-subagents.md#package-integration-follow-up-2026-10-03). Runtime delegation remains blocked by the documented provider/auth dependency; packaging does not establish Claude CLI operation.

## Deep runtime test follow-up (2026-10-03)

Current-state inspection found Claude Code CLI `2.1.251`. Its help exposes the tested `-p`, `--model`, `--permission-mode`, `--max-turns` and `--no-session-persistence` flags. Process environment and `~/.claude/settings.json` differed; the [official precedence guidance](https://code.claude.com/docs/en/env-vars#precedence) says settings-file `env` values override inherited shell values in most sessions. The smoke test therefore used the configured settings model and route, without printing credentials or changing settings.

An unauthenticated model-catalog request returned 401. The read-only CLI smoke request used the configured exact model with `--permission-mode plan`, `--max-turns 1` and `--no-session-persistence`. It exited 1 after about 2.5 minutes with `Failed to authenticate. API Error: 401 API key is not authorized for this gateway.` A subsequent local-only `claude auth status --json` inspection showed the CLI selected `ANTHROPIC_API_KEY` from the process environment even though an OAuth login also exists. The effective base URL came from user settings while the inherited shell configured a different base URL, so the intended pairing of this key with the settings-file host is not established. The failed request was sent to that effective configured host; its key was not displayed. Stop further provider calls until the owner confirms/fixes the intended route and auth pairing. No alternate endpoint/model was tried and no bounded worker task was dispatched. Captured stdout/stderr are in ignored `tmp/claude-code-subagents-deep-20261003/`.

The long failed smoke exposed that `--max-turns` does not bound API wait/retry time. Updated the skill to require a wall-clock bound, recommend invocation-local `API_TIMEOUT_MS`/`CLAUDE_CODE_MAX_RETRIES` limits without changing saved settings, check the auth source as well as host/model, and stop when their intended pairing is unclear. The personal Codex installation was refreshed from source. These edits were made by the primary; no independent review or successful provider execution is claimed. The owner must confirm/fix the configured gateway and credential pairing before delegated file work, handoff inspection, and integration can be tested.
