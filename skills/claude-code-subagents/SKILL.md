---
name: claude-code-subagents
description: Delegate bounded work from Codex to Claude Code CLI. Use when requested or when independent capacity helps; inspect and integrate the result.
---

# Claude Code Subagents

Follow the shared [Northstar delivery contract](../northstar/SKILL.md#delivery-contract). Codex is the commander and accepting owner; Claude Code is a bounded CLI worker. Load this skill only when Claude Code is requested or adds clear independent value.

## Decide and assign

Group related criteria into one coherent, bounded assignment with disjoint writable files (never let Codex and Claude edit the same file concurrently). Pass inherited authority, exact write scope, baseline context, verification command, and wall-clock deadline in a self-contained brief. Stop optional delegation once required acceptance passes.

## Verify the route before use

Route local Subroute inference through `http://127.0.0.1:4000` (`/v1/messages`). Select any endpoint-supported model ID or alias via `NORTHSTAR_SUBROUTE_MODEL` (defaulting to `default`); never pin a vendor model in shared docs or silently switch providers/protocols.

Run these gates in order before dispatching a worker:

1. **Read-only model & protocol resolution gate:** Verify that the selected model/alias resolves to a target compatible with Anthropic Messages and tool use. When `NORTHSTAR_SUBROUTE_MODEL` is `default`, inspect `GET /api/active-model` and configured deployment mapping first: if Subroute policy mode is `off`, `default` passes through to LiteLLM's static `default` deployment (which may be a Responses-only Codex model) rather than the saved active target. If `default` resolves to an incompatible protocol in `off` mode, either pass the explicit Messages-compatible alias configured on Subroute (e.g. via `NORTHSTAR_SUBROUTE_MODEL`) when authorized, or report the route mismatch—never mutate shared gateway routing policy from a skill task.
2. **Process-scoped credential setup:**
   - Pass only an authorized inference key in the child environment as `ANTHROPIC_API_KEY` (`X-Api-Key`), explicitly unset `ANTHROPIC_AUTH_TOKEN`, and keep `GATEWAY_MASTER_KEY` and `EXPERTS_API_KEY` out of the child.
   - If Subroute delegation is mandated and no inference key exists, create one task-scoped LiteLLM virtual key via the local control API: unique alias, restricted to the selected model ID/alias, `duration` and `budget_duration` $\le$ `20m`, `max_budget` $\le$ `0.5` (or stricter task cap), and `max_parallel_requests` = `2`. Keep the plaintext `key` in memory only, pass it only to the child process, and always revoke the alias in a `finally` block (verifying absence afterward).
3. **Bounded CLI & tool-use smoke:**
   - Isolate the child with a fresh empty `CLAUDE_CONFIG_DIR`, `--bare`, and `--setting-sources ""` (when no isolated skill/settings are needed).
   - Clear inherited model overrides in the child environment (`ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`) by setting them to the selected model ID/alias so user-profile defaults (like `MiniMax-M2.7[1m]`) cannot leak into the child request.
   - Confirm a text smoke exits `0` with the exact marker, and for tool-using work confirm one sequential forced `tool_use` $\rightarrow$ `tool_result` continuation returns its exact marker before launching the worker.

## Run bounded work

- **Never use `--dangerously-skip-permissions`.** Use read-only/plan mode for audits, or explicitly enable only the native tools needed (`Read`, `Edit`, `Write`, `Bash`) for scoped implementation.
- **Bound wall-clock time and stop on retry storms:** Enforce a parent wall-clock timeout alongside `--max-turns` and `--max-budget-usd`. Stream output with `--output-format stream-json` (or `json`) keeping stdout and stderr in separate task-scratch files. **Terminate the child immediately on the first native `api_retry` (HTTP 429) or `unrecognized_model` event** rather than burning budget in retry loops.
- **Inspect only after process exit:** Wait for the child process to exit before reading the captured JSONL stream and checking diffs. Require native tool events (`Read`/`Write`/`Edit`/`Bash`), a final handoff, and exit code `0`.

## Accept and integrate

1. Inspect `git status` and diffs before and after dispatch; reject any out-of-scope file edits.
2. Independently run the verification check and inspect the actual artifact. Claude cannot certify its own authored work as independent QA.
3. Record the artifact, check results, usage/cost metrics actually returned, remaining gaps, and next action in the project's existing record.

See local `claude --help`, the official [CLI reference](https://code.claude.com/docs/en/cli-reference), and [environment variables](https://code.claude.com/docs/en/env-vars).
