# Plugin-disabled helper option

## Matched evidence supplied for this change

Two byte-matched Node `parseQuantity` fixture tasks used the same prompt and acceptance criteria. The baseline settings reported 373,344 input, 5,912 output, and 3,107 reasoning tokens. The treatment added only process-local `features.plugins=false` and reported 286,726 input, 3,263 output, and 1,609 reasoning tokens. Both workers exited 0 and passed all 4/4 specified tests; parent cross-variant checks passed 42 assertions. The treatment's reported input was 23.20% lower.

Both workers still read global `MEMORY.md` and the full Northstar skill, and total usage remains high. This is one matched synthetic observation, not a general savings guarantee. It does not establish cost savings or causal reliability beyond this pair.

## Scoped implementation and check

In `skills/codex-subagents/SKILL.md`, `Invoke-CodexChild` now accepts separate `[switch] $DisablePlugins`. When present it appends exactly one `-c features.plugins=false`; when absent the existing child arguments are unchanged. It is independent of `-UseObservedSubrouteSettings` and documented for tasks that do not rely on plugin-provided integrations. Task-brief guidance also states that a running Codex CLI process is already the delegated worker and should use its own native tool path, not launch a nested CLI unless explicitly assigned.

Stubbed-`codex` argument check passed: default invocation had no `features.plugins=false`; `-DisablePlugins` added it exactly once; combining it with `-UseObservedSubrouteSettings` preserved the loopback base URL and each existing observed setting exactly once.

## Live synthetic write through the helper

On 2026-10-23, the parent rechecked the configured Subroute `default`/Responses route with a unique response and full function-call/result roundtrip, then ran a read-only helper smoke. The smoke returned the exact marker with one native `command_execution`, no `file_change`, `turn.completed`, and exit 0. A bounded `workspace-write` worker then repaired a synthetic `parseQuantity` fixture through the extracted helper with `-UseObservedSubrouteSettings -DisablePlugins`.

The first implementation passed the four existing tests but accepted numeric literal `1.2345`. The parent's independent 23-case check caught the gap. A subsequent handoff claimed the repair although source inspection showed the original implementation unchanged, so that handoff was rejected and the repair was re-dispatched. The accepted second repair changed only fixture `src/quantity.js` and `handoff.md`; structured JSONL recorded four `command_execution` events, two `file_change` events for those exact paths, `turn.completed`, a concise final handoff, and exit 0. Reported usage was 141,772 input (67,840 cached), 2,324 output and 840 reasoning tokens; cost was not returned.

The parent independently reran `node --test test/quantity.test.js` (4/4), the 23-case parent acceptance probe, and five actual numeric-literal probes: `1.234`, `1234`, and `0.001` were accepted; `1.2345` and `0.0001` were rejected. String parsing, negative inputs and non-finite rejection remain covered by the original suite. This is one successful synthetic helper-mediated repair after a parent-detected defect; it does not establish repeated reliability, general task quality, production correctness or savings. The worker's own final Git-scope command failed because its shell resolved the enclosing Northstar root instead of the untracked fixture directory; the parent therefore used structured file-change events, direct source inspection and isolated tests for acceptance. No production source, commit, push, build, package or cleanup changed.
