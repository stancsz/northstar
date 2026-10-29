# Goal: Claude Code Subagents skill

Status: source and installed skill updated; Codex CLI/Subroute implementation and independent source review succeeded. Current Claude process environment points to Badlands with `apiKeyHelper`; no process-scoped Subroute inference key is present, so Claude implementation acceptance remains unverified.

## Outcome

Create and install a Codex skill that delegates bounded work to Claude Code through its CLI, and exercise it on a bounded assignment.

## Acceptance

- The source is a Markdown skill at `skills/claude-code-subagents/SKILL.md`, installed with the four other sibling skills and in the personal Codex skills directory.
- The root README, central skill, installation guide and contributor instructions identify this as the fifth package skill and preserve the Claude Code-specific host prerequisite.
- Guidance makes Codex the accountable orchestrator and Claude Code a bounded CLI worker, while preserving scope, authority, independent acceptance, integration, and learning.
- Codex can discover/invoke the skill, resolve the effective model/host/auth pairing without exposing credentials, and receive an exact-response smoke result from the configured CLI route.
- Complete a bounded read-only review task with source-backed findings, then a distinct bounded implementation task in a scratch checkout or fixture. Inspect the resulting diff, verify scope and run the task's relevant checks.
- Have a separate nonauthor reviewer inspect the implementation and its evidence; repair material findings and independently recheck them.
- Exercise a denied/unavailable route and verify a visible failure, no fallback to another host/model, and no saved provider/auth changes.
- Record the actual usage, evidence, and limits in the linked report and evaluation; inspect diffs and local links and run `git diff --check`.

## Constraints

Preserve unrelated working-tree changes. Do not change Claude's provider/model configuration without authorization. Keep the documented runtime-use limitation explicit.

## Task and decision

Primary owns the source skill, package and personal Codex installs, invoking Claude Code, evidence, indexes, and integration. [Implementation report](../../reports/claude-code-subagents/implementation.md); [evaluation](../../evals/claude-code-subagents.md).

The initial version was mistakenly installed as a Claude Code skill. The corrected Codex-oriented source and installation supersede it. Earlier Claude Code CLI `2.1.251` attempts reported unavailable models on a prior route. On 2026-10-03, the current CLI accepted the configured model and flags but its read-only smoke request failed with `401 API key is not authorized for this gateway`. Local auth status showed that noninteractive mode selected a process API key while user settings supplied a different base URL. The key/host pairing is unconfirmed, so no more provider calls may be made until the owner confirms the intended route or updates the configuration. The negative path showed a visible error and no fallback/settings change. None of the successful task, handoff, independent-review or repair criteria have yet run.

On 2026-10-22, the owner explicitly requested restoring Claude Code to local Subroute at `http://127.0.0.1:4000` with model alias `default`. The matching user-level route/model fields were updated without storing a credential. A bounded read-only CLI smoke reached Subroute but failed: Claude sent `default[1m]`, and LiteLLM rejected the supplied `GATEWAY_MASTER_KEY` as the wrong credential type, requiring an inference virtual key. No Claude tool work was dispatched. Runtime acceptance remains blocked pending an already-authorized Subroute inference key supplied only to the child process. The source and personal installed skill now match at SHA-256 `ECD50F8679A4D2C7A3D9F1C8CF4565BEFDA3A0AE701BEF2CE35600E50457A6DC`. See the [current implementation handoff](../../reports/claude-code-subagents/implementation.md#subroute-resumption-2026-10-22).

On 2026-10-14, the owner requested a current meaningful-work and token-cost check. The environment and settings now agree on `https://api.badlandslabs.com`, and local auth status selects `apiKeyHelper`, with no inherited API key/token. This changed configuration supersedes the prior route blocker. Two bounded, tool-disabled CLI requests succeeded using the configured `anthropic/claude-sonnet-5`: a source-excerpt review and a smaller wording draft. Primary inspected both responses; only part of the review was supported, and the draft missed some requested constraints. This establishes scoped read-only delegation, not implementation or complete acceptance. See the [current evaluation](../../evals/claude-code-subagents.md#bounded-read-only-and-token-check-2026-10-14).

## 2026-10-23 current process-auth recheck

A safe process-only inspection found `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` absent; `ANTHROPIC_BASE_URL` is `https://api.badlandslabs.com`, `ANTHROPIC_MODEL` is `anthropic/claude-sonnet-5`, and `claude auth status --json` reports `loggedIn=true`, `authMethod=api_key_helper`, `apiKeySource=apiKeyHelper`. Secret values and the raw auth response were suppressed. This does not verify the credential's effective source under settings precedence and does not authorize sending it to Subroute. No Claude request or setting change occurred. The Subroute acceptance requirement remains an already-authorized LiteLLM inference virtual key supplied only to the worker process as `ANTHROPIC_API_KEY`, with a fresh exact-host/default unique-response smoke; the gateway master key and Expert service key are not substitutes. Continue Codex work while that external key is unavailable.
