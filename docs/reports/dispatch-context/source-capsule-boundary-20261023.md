# Source capsule boundary probe — 2026-10-23

## Result

A Codex CLI worker completed one bounded documentation edit through the configured Subroute profile (`http://127.0.0.1:4000/v1`, Responses, model alias `default`). The parent performed the route preflight first: unique response, forced function call, and stateless replay of the function call plus its matching tool result all returned the expected marker. No provider, model, route, credential, or global setting changed.

The worker edited only the capsule copy of `skills/codex-subagents/SKILL.md` and created its assigned handoff. Parent comparison found exactly one inserted paragraph and no other content changes. The paragraph records the key boundary: a source capsule and `--cd` narrow task context, but do not isolate reads. The CLI offers `read-only`, `workspace-write`, and `danger-full-access` sandbox modes but no per-path read allowlist. Parent's synthetic canary outside `%TEMP%` was readable from the capsule run, so the tested setup does not isolate reads. Probe canaries on the actual host before making a boundary claim: a readable canary disproves isolation for that path, while a denied canary supports only the tested boundary. When reads outside scope are possible, the parent audits output and integrates it as untrusted work.

## Reproduction and limits

The final worker completed with `turn.completed`, exit 0, a file-change event for the capsule skill, and a handoff. Its reported usage was 277,430 input tokens (246,521 cached), 7,234 output and 3,246 reasoning tokens; cost unknown. Two earlier capsule attempts were stopped after tool-contract confusion and made no file changes. The successful edit shows this narrow operation can complete after correction; it does not show reliable dispatch or economical context use. The input cost is high for a one-paragraph edit.

GPT-6.1 Sol and Gemini Advisor Council advised using only tools exposed by the CLI runtime, requiring a native command event before editing, and treating capsules as context scoping rather than access control. Council use was 936 Sol and 3,263 Gemini tokens; cost unknown. The parent independently checked the capsule diff and canary; the worker itself did not rerun the canary. The actual capsule and raw receipts remain under `tmp/dispatch-context/source-capsule-finaltry-20261023/` and the capsule path recorded in the parent turn.

Claude CLI remains unverified: the task-scoped inference key was not available, and the control-plane `GATEWAY_MASTER_KEY` must not be repurposed as `ANTHROPIC_API_KEY`. This increment did not compile, package, clean artifacts, commit, or push. The broader goal remains Active.
