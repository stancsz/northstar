# Claude bearer auth evidence (2026-10-23)

**Outcome.** The local Subroute route is user-authorized for the active goal; the existing gateway Bearer stayed process-only and local, no new key was created, and no separate credential question remains. A direct Messages request over that Bearer returned HTTP 200 with the unique marker and response model `default`. A Claude Code 2.1.251 text smoke over the same Bearer returned the unique marker with exit 0, but only when the child process overwrote its model variables to `default`; an earlier smoke that inherited non-default overrides exited 1 with `[claude-code:unrecognized_model] {"model":"MiniMax-M2.7[1m]","query_source":"sdk"}`. The first Bearer-backed Read/Edit task then performed its allowed calls and edits (two Read calls, six Edit calls, all inside its assignment, no Bash or other tool call) but stopped at `error_max_turns` (`num_turns=6`, exit 1) before its final handoff. That is capability evidence plus a failed handoff, not an accepted handoff, and it does not establish full Claude CLI reliability. Bearer auth remains an owner-authorized, process-only credential for this exact local gateway. No credential value appears in this report.

## Scope

- Write scope for this reconciliation: this report, plus the credential paragraph of `skills/claude-code-subagents/SKILL.md` at line 15. The credential rules at line 36 were re-checked against the new evidence and stay in force unchanged.
- The parent inspected the target skill paragraph and confirmed this report path was absent before the change.
- No other file was created or edited. This reconciliation performed no network probe, no CLI retry, and no credential creation; the smokes and the Read/Edit task recorded below were run earlier by the parent and by the delegated Read/Edit worker the parent dispatched with the same process-only override bundle.

## Source facts

- Official Claude Code environment variables: `ANTHROPIC_API_KEY` is sent as the `X-Api-Key` header, and `ANTHROPIC_AUTH_TOKEN` is sent as `Authorization: Bearer <value>`. — <https://code.claude.com/docs/en/env-vars>
- Local Subroute README, `D:/github/subroute/README.md:93`: when `GATEWAY_MASTER_KEY` is set, API clients must send `Authorization: Bearer <GATEWAY_MASTER_KEY>`. Cited as plain text because that file lives outside this repository, so no repository link is included.

## Probe results

1. Direct API probe (parent, immediately before this dispatch)
   - Request: `POST http://127.0.0.1:4000/v1/messages`, model `default`, with the existing process-only gateway key sent as `Authorization: Bearer <value>`.
   - Result: HTTP 200 with the unique marker in the response; the response `model` field was `default`.
   - Evidence class: API-level only. It does not prove Claude Code CLI acceptance, a task-scoped virtual key, or any tool-call/tool-result roundtrip. The credential was never printed, stored or persisted.
2. Claude Code CLI smoke, inherited model overrides (Claude Code 2.1.251) — failed
   - Invocation: `--bare --model default --output-format json --max-turns 1 --no-session-persistence`, `ANTHROPIC_BASE_URL=http://127.0.0.1:4000`, model alias `default`, and the same owner-authorized gateway Bearer value supplied as process-only `ANTHROPIC_AUTH_TOKEN`.
   - The parent found that the process environment carried non-default Claude model overrides; this smoke inherited them.
   - Result: exit status 1 with `[claude-code:unrecognized_model] {"model":"MiniMax-M2.7[1m]","query_source":"sdk"}`.
   - A debug-filtered invocation with the same inherited overrides returned the same diagnostic and no request trace, so no request can be tied to it.
   - Limits: the diagnostic's origin is unproven; it is not attributed to auth, to the credential, to that request, or to any provider/model layer.
3. Claude Code CLI smoke, process-only override bundle (Claude Code 2.1.251) — passed
   - Invocation: the same flags (`--bare`, `--model default`, `--output-format json`, `--max-turns 1`, `--no-session-persistence`), `ANTHROPIC_BASE_URL=http://127.0.0.1:4000`, model alias `default`, the same owner-authorized Bearer credential, and these six variables set in the child process only, each to `default`: `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `ANTHROPIC_CUSTOM_MODEL_OPTION`.
   - Result: exit status 0, and the unique marker was returned.
   - Limits: a text response only. It does not establish Claude Code tool use, task completion, or reliability. The run's usage metadata was not retained, so token and cost usage for this smoke is unavailable.
4. Claude Code CLI Read/Edit task over the Bearer path, corrected process environment (Claude Code 2.1.251) — tool events present, handoff failed
   - Invocation: the corrected process environment (all six model variables set to `default` in the child only), the same local Subroute base, the same owner-authorized process-only Bearer, `--tools Read Edit`, `--allowedTools Read Edit`, `--restricted`, `--max-turns 5`.
   - Structured stream: exactly two Read calls and six Edit calls. Every call targeted only the assigned skill paragraph and this report; no Bash or other tool call appeared.
   - Result: `result.subtype=error_max_turns`, `num_turns=6`, exit 1, and no final handoff.
   - Reported metrics for that run: duration 102.1s; 10,772 input tokens plus 50,944 cached input; 10,113 output tokens, of which 7,642 were thinking; reported cost $0.332157.
   - Stderr also contained `[claude-code:unrecognized_model] {"model":"default[1m]","query_source":"sdk"}` with no correlated request sequence. It is unclassified: it is not attributed to auth, to the credential, to model routing, to the provider, or to any request.
   - The parent inspected the actual paths and confirmed the incomplete run edited only within its assignment. That is scope containment, not an accepted complete handoff.
   - Limits: this shows the allowed Read/Edit tools can run and edit under the Bearer path. It does not show a completed task, an accepted handoff, or reliability.
5. Reading the smokes and the task together
   - The failing and passing text smokes differ by one combined change to the model-override bundle. Several variables changed together, so no single variable is identified as the cause and the earlier `unrecognized_model` diagnostic remains unattributed.
   - The passing text smoke and the failed Read/Edit task are complementary: the first shows a routed response, the second shows the tools running and editing. Neither shows an accepted handoff, and neither supports a claim of full Claude CLI reliability.
   - Only the parent can inspect process environment variables; a delegated worker cannot read them. The worker's own CLI process uses this exact process-only override bundle, which is why it can follow the accepted shape without being able to confirm the parent's account of the environment.

## Advisor Council conclusion and usage

- Conclusion: `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are distinct credentials sent under distinct headers (`X-Api-Key` versus `Authorization: Bearer`) and must not be conflated; `ANTHROPIC_AUTH_TOKEN` is admissible as an owner-authorized, process-only credential for this exact local gateway, and the Claude CLI unique-response smoke now passes with it; a gateway master credential is never mapped into `ANTHROPIC_API_KEY`; model alias `default`, the endpoint, the provider, and the existing virtual-key scope and revocation controls stay unchanged; both `unrecognized_model` diagnostics (`MiniMax-M2.7[1m]` and `default[1m]`) stay unclassified and must not be reported as an auth pass, an auth failure, or a proven cause; the passing text smoke plus the failed Read/Edit task are capability evidence only, not a reliability claim, and the task gate stays open.
- Usage: Sol — 1,067 total tokens; Gemini — 3,534 total tokens. That is the advisor council run's own usage; it does not include the Claude CLI run recorded above.

## Guidance changed

`skills/claude-code-subagents/SKILL.md`, credential paragraph at line 15 (the rules at line 36 were re-checked against the new evidence and stay in force unchanged):

- distinguishes `X-Api-Key` (`ANTHROPIC_API_KEY`) from `Authorization: Bearer` (`ANTHROPIC_AUTH_TOKEN`) and cites the official environment-variable reference;
- scopes the "unset `ANTHROPIC_AUTH_TOKEN`" instruction to API-key/virtual-key mode instead of stating it for every mode;
- keeps the task-scoped LiteLLM virtual-key recipe, the model alias `default`, the fixed local endpoint, the provider, and the existing virtual-key scope and revocation controls;
- requires the six model variables to be overwritten to `default` in the child process instead of inherited from the ambient environment, and records that the text smoke passed only with that bundle, while noting that all six changed together, so no single variable is proven as the cause;
- records the Bearer path as an owner-authorized, process-only credential for this exact gateway, gated on a successful Claude Code CLI unique-response smoke, which now passes;
- records the attempted Read/Edit task as capability evidence with a failed handoff (`error_max_turns`, `num_turns=6`, exit 1, no final handoff), not an accepted handoff, and keeps the `default[1m]` stderr diagnostic unclassified;
- does not freeze future CLI work: it forbids repeating the same 5-turn invocation and requires `--max-turns` to cover the Read/Edit work, the final verification, and the handoff;
- keeps the ban on mapping a gateway master credential into `ANTHROPIC_API_KEY`, and keeps the no-secret handling rules (no display, no persistence, no other host, no credentials in arguments, prompts, transcripts, logs or files, no writes to global Claude settings).

## Remaining acceptance gate

The initial bounded Read/Edit implementation run remains a failed handoff: it performed the allowed calls and edits but stopped at `error_max_turns` (`num_turns=6`, exit 1) without a final handoff. A changed, bounded documentation-reconciliation run then completed on the same local Subroute route (`http://127.0.0.1:4000`), alias `default`, and process-only Bearer. Its structured stream recorded 12 Read/Edit calls, all to the two assigned files, followed by final reads; it returned a handoff, `success`, and exit 0. The parent checked the event paths, final handoff, and resulting changes. This accepts that narrow documentation task and closes the Claude CLI text-response and one scoped tool-use/handoff example; it does not prove broad reliability, implementation quality across tasks, or economical delegation. The two `unrecognized_model` diagnostics remain unclassified rather than being reported as auth, model-routing, or provider failures. No further credential work is required: the route is user-authorized, the gateway Bearer stayed process-only and local, and no credential was minted, created, or persisted. The endpoint, model alias, provider, and existing virtual-key scope and revocation controls did not change.

## Checks not run

- Tests and builds: none; the assigned changes were prose only.
- The parent independently parsed the reconciliation receipt: 12 native Read/Edit calls targeted only the two assigned files, final Read calls covered both, the stream returned `success` with a final handoff, and the process exit file is `0`. The returned usage was 16,734 input (123,392 cached), 18,229 output (12,865 thinking), 13 turns, 156,728 ms API duration, and reported cost $0.601091. Parent review and scoped `git diff --check` are recorded in the current continuation entry in `cli-trials.md`.
- The successful reconciliation was a changed task with a larger turn budget; it was not an unchanged retry of the failed five-turn implementation task. It did not run tests/builds or alter the endpoint, model, provider, global settings, or credentials.

