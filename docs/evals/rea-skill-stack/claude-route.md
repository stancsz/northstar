# Claude Code Subroute preflight receipt

Date: 2026-10-29. Purpose: test whether Claude Code can use the current local Subroute endpoint using its native Anthropic protocol, then attempt one bounded review after the tool gate passed. The first preflight stopped before dispatch; a later run passed the tool gate but did not complete a worker handoff.

## Configuration and result

- CLI: Claude Code `2.1.251`; endpoint `http://127.0.0.1:4000`; model alias `default`.
- Isolated empty `CLAUDE_CONFIG_DIR`, `--bare`, empty setting sources, process-scoped `ANTHROPIC_API_KEY`; inherited `ANTHROPIC_AUTH_TOKEN` removed.
- One task alias, `northstar-rea-claude-review-20261029`: `default` only, max budget USD 0.50, one parallel request, 20-minute duration and budget duration. It was deleted and alias absence confirmed.
- Initial smoke failed before inference because inherited `ANTHROPIC_DEFAULT_OPUS_MODEL=MiniMax-M2.7` caused the CLI to request `MiniMax-M2.7[1m]`, rejected as `unrecognized_model` under the scoped key. No route substitution occurred.
- After setting all child-only Claude default model overrides to `default`, disabling 1M context and setting the configured 256000-token limit, the CLI text smoke exited 0 with `subtype=success`, `is_error=false`, and exact marker `CLAUDE_SUBROUTE_SMOKE_20261029`. The CLI result reported USD 0.008085, 1,537 input tokens and 16 output tokens.
- Direct Anthropic Messages tool-use preflight was rejected twice by `max_parallel_requests`, remaining 0. The gateway reset timestamps advanced from `2026-10-29 19:44:02 UTC` to `19:44:34 UTC`, so the condition did not clear after the bounded wait. No tool-use/result continuation completed and no Claude review worker was started.

## First attempt decision

The native Claude text smoke passed, but the required tool-use/result gate failed. Preserve this as a preflight failure. Do not retry or dispatch until the concurrency behavior and aggregate budget are independently resolved. This result does not prove Claude skill discovery, independent review or case performance. Raw CLI and protocol response receipts are retained in ignored `tmp/rea-skill-stack/claude-review/`; no credential is stored there.

## Later bounded tool gate and worker attempt

After preparing a read-only diagnostic plan, a corrected local controller created one fresh task-scoped key restricted to `default`, with a USD 0.25 key ceiling, parallel limit 2, and 20-minute duration. Two earlier key-creation requests returned HTTP 422 because the controller omitted `Content-Type: application/json`; no keys were created by those requests. The corrected request succeeded. The key was mapped locally to truncated digest `c0514301fbc3`; the secret was not saved or passed outside the Claude child.

The controller sent one forced `emit_marker` tool request and then one serial `tool_result` continuation. Both returned HTTP 200. The first returned the exact unique tool input with `stop_reason=tool_use`; the second returned the exact final marker with `stop_reason=end_turn`. Usage was 195 input / 29 output tokens and 280 input / 21 output tokens. Before worker dispatch, ordinary key metadata reported the configured cap and parallel limit and `spend=0.0`.

One write-enabled Claude CLI worker then started with `--max-budget-usd 0.20`, a fresh isolated profile containing the hash-matched Soak skill, `Read` and `Write` tools, and task-scratch-only write scope. The completed native stream shows the worker read the isolated `soak-testing/SKILL.md` and the bounded evidence packet, confirming discovery/use in that isolated profile. It did not produce a review artifact or final handoff. The CLI stream recorded ten automatic `api_retry` events, each for HTTP 429 `rate_limit`; gateway logs report `max_parallel_requests`, current limit 2, remaining 0. Stderr also reports `unrecognized_model` for `default`. Compared with the passing text smoke, this child omitted `--setting-sources ""` and added `--effort low`; this is a concrete local configuration difference to correct, not a proven cause of the 429s. The task-scratch controller was updated to match the smoke's setting-source/model shape and to terminate on the first future `api_retry`, but that corrected path has not been run. The parent stopped the CLI child after the repeated 429s, before its 180-second wall cap, and the wrapper revoked the key and confirmed alias absence. The process therefore has an interrupted exit (`4294967295` from explicit termination), not a natural successful or failed terminal result. The parent wrapper's task-scratch receipt is the complete lifecycle evidence.

Read-only key metadata reported zero gateway spend at the post-preflight check, and the matching key digest produced no standard LiteLLM spend-log rows for this attempt. The direct Messages responses lacked dollar-cost fields, so provider cost is unknown; the USD 0.25 figure remains the maximum key exposure, not actual cost. No second worker, route change, retry by the parent, or Soak framework run occurred.

**Case verdict: incomplete / not accepted.** Claude skill reading is confirmed only for the fresh isolated profile used in this run. The worker never completed the assigned evidence review. Codex CLI prompt construction separately lists the installed skill, but model invocation/use is unverified. Raw prompts, responses, native CLI events, stderr, key metadata and process receipts are retained under ignored `tmp/rea-skill-stack/claude-exercise/`.
