---
name: claude-code-subagents
description: Delegate bounded work from Codex to Claude Code CLI. Use when requested or when independent capacity helps; inspect and integrate the result.
---

# Claude Code Subagents

Follow the shared [Northstar delivery contract](../northstar/SKILL.md#delivery-contract). Codex remains the commander and accepting owner; Claude Code is a bounded worker. Load this skill only when Claude Code is requested or can materially improve the work.

## Decide and assign

Delegate one coherent task when an explicit user or repository instruction requires it, or when a bounded Claude run is likely to improve speed, independent review, or focused expertise enough to justify coordination and integration cost. A mandate does not require one worker per criterion or parallel work: group related criteria into one assignment where practical. Respect diminishing returns once required acceptance is met; do not add optional delegation or review chains.

The commander owns decisions and approvals. Pass existing authority and its limits to the worker; do not seek repeated approval for covered actions or let delegation expand scope. Before dispatch, define the outcome, observable acceptance, relevant instructions and baseline, exact write scope, allowed side effects, verification, deadline, and handoff. Give each writer distinct files or a distinct checkout based on the required state. Preserve user changes and do not have Codex and Claude edit the same files concurrently.

## Verify the route before use

For local Subroute inference, use `http://127.0.0.1:4000/v1` by default. Select any model ID or alias supported by that endpoint through `NORTHSTAR_SUBROUTE_MODEL`; when unset, use the gateway's `default` alias, whose target remains controlled by Subroute. This is the primary inference route, not merely a tool endpoint. Do not pin a backend model, substitute `localhost`, or silently switch provider, endpoint, model selection, or protocol. If the route is unavailable, stop that route and report the exact gap; use another route only when already authorized.

Before any Claude route smoke or dispatch, verify that the selected model resolves to a target compatible with Claude's Anthropic Messages protocol and required tool flow. For `default`, inspect the live routing mode and configured default deployment: in `off` mode the routing hook passes `default` through to LiteLLM, so it resolves the configured `default` deployment rather than the saved active target. Do not treat the alias name, `/v1/models` listing, saved active target, or a different-protocol smoke as proof of Messages compatibility. If the effective target is incompatible or cannot be established read-only, do not dispatch or change shared routing policy; report the route gap.

When Claude or its local route is new or reconfigured, first run one bounded Claude CLI smoke with `--bare`, a fresh empty isolated `CLAUDE_CONFIG_DIR`, the local endpoint and selected model ID or alias (from `NORTHSTAR_SUBROUTE_MODEL`, defaulting to `default`). Use the CLI's actual protocol. Accept the smoke only when the CLI exits successfully and returns the requested unique marker. For tool-using work, also require a bounded Anthropic Messages `tool_use` / `tool_result` continuation through the same route and confirm its marker before dispatch. Preserve the native blocks. A response, HTTP status, open port, model listing, or Codex smoke alone does not pass these gates. Reuse passing evidence while effective route configuration is unchanged; do not repeat setup inside the worker.

Keep authentication separate from routing and process-scoped. Use only an already-authorized inference credential for this exact host. With an API virtual key, pass it only to the Claude child as `ANTHROPIC_API_KEY` (`X-Api-Key`), explicitly unset `ANTHROPIC_AUTH_TOKEN`, and keep `GATEWAY_MASTER_KEY` and `EXPERTS_API_KEY` out of the child. Never map a gateway master credential into `ANTHROPIC_API_KEY`. A distinct `ANTHROPIC_AUTH_TOKEN` Bearer path is allowed only when explicitly owner-authorized for this host and only after its own successful CLI smoke; it does not establish tool-use acceptance. Never expose, log, persist, or use credentials against another host, and do not read unrelated credential stores or modify global settings. For an isolated CLI config, inspect only that config and safe effective environment values; never fall back to the user's normal profile.

If the owner explicitly mandates Subroute delegation and no suitable authorized inference key exists, the commander may create one task-scoped LiteLLM virtual key through the local control API. Give it a unique task alias restricted to the selected model ID or alias (the gateway's `default` alias when no selection is set), `duration` and `budget_duration` no greater than 20 minutes, `max_budget` no greater than 0.5, and `max_parallel_requests` 2. Read only the response's plaintext `key` field, pass it only as the child's process-scoped `ANTHROPIC_API_KEY`, and revoke only the alias created for this task in a `finally` path. Confirm that exact alias is absent afterward; leave pre-existing credentials untouched. Keep the key out of command arguments, prompts, transcripts, logs, and files. If a smoke rejects a credential, stop and inspect only redacted diagnostics and that key's metadata for the effective auth source. Do not retry blindly; allow at most one corrected retry after identifying and correcting a concrete source mismatch.

If the CLI reports a pre-inference failure, including that the base request was not sent, do not launch a worker, repeat the same request, or substitute credentials/routes. Preserve the exact failure and continue only with independent authorized work.

## Run bounded work

Check `claude --help` and the local version when needed for installed flags. Never use `--dangerously-skip-permissions`. For read-only work, use a supported plan/read-only mode. For implementation, select the native tools the assignment needs and use the configured permission flow. Bound wall-clock time independently of `--max-turns`; turns do not bound API waits or retries. Apply any timeout/retry controls only in the child process. Keep stdout and stderr separate. Prefer JSON output for a final-answer/usage handoff; use incrementally captured `stream-json` when native tool lifecycle evidence is required, preserving partial receipts as incomplete if interrupted. Record only metrics actually returned.

For local Subroute, set `ANTHROPIC_BASE_URL=http://127.0.0.1:4000` and choose `ANTHROPIC_MODEL` from `NORTHSTAR_SUBROUTE_MODEL` (default `default`) in the child process; Claude's Messages requests use the `/v1/messages` route. Use that same selection for smoke and task dispatch. Isolate the child with a fresh `CLAUDE_CONFIG_DIR`; use `--bare` for the route smoke. If inherited model overrides could affect the CLI, explicitly set its model override variables to the selected model ID or alias in that process rather than changing saved settings. Pass the successful smoke evidence and necessary task context into the assignment.

Native tool events establish only the actions they show. For an implementation handoff, require the relevant native read/write/test events, a final handoff, successful process exit, and parent inspection of the actual diff against the assignment. A worker claim, text smoke, or artifact alone is not acceptance. If turn or wall-clock bounds expire before handoff, classify the handoff as incomplete even if the parent can independently inspect the artifact.

## Accept and integrate

1. Inspect repository status, relevant diffs, and the intended base before dispatch; preserve unrelated work.
2. On return, inspect changed paths, native event evidence, outputs, checks and the handoff. Reject scope expansion and unsupported claims.
3. Independently verify material acceptance criteria and repair concrete gaps within the mandate. Claude cannot accept its own authored work. Do not restart an unchanged failed approach.
4. Record the artifact/base, actual checks and results, remaining gaps, and next action in the project's existing record. Count setup, worker effort, review and rework as total effort; one successful task proves neither savings nor reliability.
5. Keep commits, pushes, publication, deployment and external contact within the user's authorization.

Claude Code may use its native subagents internally, but Codex assigns one outcome and write boundary to the Claude run. Do not add another management layer unless the task needs it. Use local `claude --help` and the official [CLI reference](https://code.claude.com/docs/en/cli-reference); Claude's internal [subagents](https://code.claude.com/docs/en/sub-agents) are distinct from this Codex-to-Claude delegation pattern. See the official [environment-variable reference](https://code.claude.com/docs/en/env-vars) for CLI configuration details.
