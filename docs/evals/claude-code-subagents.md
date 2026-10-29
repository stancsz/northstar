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

## Bounded read-only and token check (2026-10-14)

Current evidence supersedes the historical authentication blocker: shell/settings agree on the Badlands endpoint, auth status selects `apiKeyHelper`, and two CLI calls on configured `anthropic/claude-sonnet-5` succeeded. Both exited 0, returned their exact requested markers, and had empty stderr. No host/model fallback or saved settings change occurred. Base revision, safe launch controls, measured usage and findings are in the [implementation handoff](../reports/claude-code-subagents/implementation.md#bounded-read-only-and-token-check-2026-10-14).

The source-excerpt review took 22.54 seconds and reported 5,474 tokens including cache reads, estimated $0.0222056. The smaller drafting task took 4.95 seconds and reported 1,703 tokens, estimated $0.004313. These are CLI-reported counts/list-price estimates, not verified gateway invoices; parent Codex work is additional and unmeasured. Different tasks do not establish comparative savings.

Primary inspected the responses: one review suggestion was supported, another contradicted the source and was rejected. The smaller draft was partly useful but missed its requested cost-bound point and word limit. No proposed skill text was integrated. The distinct Claude worker did not author the reviewed source, but this narrow check is not whole-package QA or independent acceptance of the primary's new documentation.

Scope verified: read-only delegation with supplied context, bounded runtime, response handoff and usage reporting. Tool-driven source inspection, file-writing implementation, tests, integration, independent implementation acceptance and repair remain unverified. Existing unrelated edits were preserved. Documentation changes passed scoped local-link inspection and `git diff --check`.

## Subroute resumption (2026-10-22)

The owner explicitly selected local Subroute `http://127.0.0.1:4000` and alias `default`. User Claude settings now match that route and alias, with no secret stored. The exact Claude CLI smoke failed with 401 because `GATEWAY_MASTER_KEY` was rejected where LiteLLM requires an inference virtual key; the CLI also normalized the alias to `default[1m]`. No Claude tool call or worker task followed, so Claude Code is not currently usable through Subroute.

Codex CLI's existing Subroute profile did pass a unique response and emitted a completed read-only `command_execution` event. Its startup also reported that optional MCP service `127.0.0.1:9010` was unavailable. Codex then produced a scoped edit to the Claude routing skill; parent review and `git diff --check` passed, but the worker's final handoff was not captured and no second independent reviewer was used. This establishes a useful Codex CLI/Subroute path with a local MCP warning, not successful Claude delegation or broad CLI effectiveness. Reopen Claude acceptance when an already-authorized inference virtual key is available locally to `ANTHROPIC_API_KEY`.

A separate read-only Codex CLI review found three inconsistencies in the first skill edit; primary repaired them, and the same nonauthor reviewer confirmed all three resolved with no remaining material findings. The final scoped diff check and the trial-record link target passed. This is independent review of the documentation change, not runtime acceptance.

A final review caught route-fallback wording that still conflicted with the fixed Subroute/default requirement. That wording now requires explicit owner authorization before any alternative route; the reviewer confirmed no remaining material findings. The canonical skill and personal installed copy now match at SHA-256 `ECD50F8679A4D2C7A3D9F1C8CF4565BEFDA3A0AE701BEF2CE35600E50457A6DC`.

## 2026-10-23 process-level Claude auth check

Current process values and safe CLI auth metadata were rechecked without reading or printing any key: the process has neither `ANTHROPIC_API_KEY` nor `ANTHROPIC_AUTH_TOKEN`, points `ANTHROPIC_BASE_URL` at `https://api.badlandslabs.com` and `ANTHROPIC_MODEL` at `anthropic/claude-sonnet-5`, while `claude auth status --json` reports `api_key_helper` / `apiKeyHelper`. No settings or credentials were changed and no request was sent. This establishes no usable process-scoped Subroute credential; it does not prove the final effective settings-file precedence. The local Subroute path still needs an already-authorized LiteLLM inference virtual key as process-only `ANTHROPIC_API_KEY` plus a new unique-response smoke against `127.0.0.1:4000`. Do not remap the existing Badlands helper credential or substitute the gateway master or Expert key.
