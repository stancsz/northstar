# Current Codex CLI native-tool gate

Status: On 2026-10-23, direct Subroute `default`/Responses unique response, forced function call, and stateless function/result roundtrip passed; the documented helper also passed a read-only smoke with native command events and the exact marker. A scoped narrative-alignment worker produced a reviewed partial artifact but missed its five-minute deadline without `turn.completed` (21 command calls; usage unknown). A subsequent exact-path Guidance-template worker completed within deadline with 14 native command calls, confined file changes and `turn.completed`; usage was 334,809 input (300,643 cached), 8,887 output and 5,097 reasoning tokens. This is mixed live task evidence, not proof of reliability or economical delegation. A rendered-brief test task has since completed, but this single run does not prove the template caused the result, repeated reliability, or economical execution.

## Route evidence

The gateway at `http://127.0.0.1:4000/v1/responses` returned an exact unique response for model alias `default`. The first function-result attempt supplied only `previous_response_id`; LiteLLM returned HTTP 400 because its stateless endpoint did not associate the tool result with the call. The corrected follow-up replayed the actual `function_call` item, paired it with a `function_call_output` carrying that exact `call_id`, and included the requested user echo. The final response returned the exact marker. Safe receipt: `tmp/dispatch-context/current-route-preflight/receipt-20261023.json`. The current `/v1/models` catalog advertises `default`; it does not identify the dynamic target currently selected behind that alias.

## Codex CLI evidence

Codex CLI 0.154.0 ran via the documented `Invoke-CodexChild` helper, profile `subroute-subagents`, alias `default`, Responses, process-only loopback override `http://127.0.0.1:4000/v1`, read-only sandbox, and the five recorded shell/apps/remote-plugin/multi-agent/browser MCP settings. It exited 0 and returned `turn.completed`, but its JSONL had no `command_execution` or `file_change`. It returned an error item about shortened skill descriptions, then reasoning and an agent message stating that it had no native local command tool and would not use the parent `functions.exec` wrapper. The child made no change. Usage was 18,185 input (3,072 cached), 294 output and 236 reasoning tokens. Stderr also recorded PowerShell snapshot unavailability, plugin metadata warnings and fallback model-metadata warnings; these do not establish the cause. Raw JSONL and stderr: `tmp/dispatch-context/current-cli-smoke-20261023/`.

Earlier accepted fixture trials in this repository record native command and file-change events under the same documented helper path. Current evidence therefore shows a run-specific or environment/route-dependent gap, not a general conclusion that Codex CLI cannot work. Do not loosen the wrapper boundary or switch the model alias, endpoint, credential source, user/global settings or sandbox to make this smoke pass.

A single Advisor Council invocation was attempted with the bounded evidence packet in `tmp/dispatch-context/advisor-codex-native-tool-gate-20261023.md`, but no response or receipt was captured and no advisor process remains live. Treat advice as unavailable; do not claim a verdict. No provider/model target, credential, saved setting, production source, package, cleanup, commit or push changed.

## Next action

Reproduce the verified smoke through the documented [`Invoke-CodexChild`](../../../skills/codex-subagents/SKILL.md) helper, which now applies the process-only Windows home fallback, with the route, model alias, credential source and sandbox unchanged. Resume write assignments only after a fresh helper-mediated smoke returns the exact marker through a structured native `command_execution`; preserve the fixed route and all recorded credential boundaries.
## Live route and second-repository diagnosis

A read-only `GET http://127.0.0.1:4000/api/active-model` confirmed the current selection is `minimax-flash`, `force`, policy version 115. The `/v1/models` catalog advertises `default`, while the live route state identifies its current target; the alias remains `default` in all worker requests. On that same alias, a direct Responses `tool_choice=auto` probe selected the harmless `report_marker` function and returned its exact synthetic argument (634 total tokens). The earlier stateless function-call/result exchange also passed when the emitted call item was replayed. This confirms current direct function calling, not Codex shell-schema compatibility.

The documented helper smoke was repeated from the product repository, `C:/Users/stanc/github/liquor-ordering-poc`, with a read-only hash task. It again exited 0 with no `command_execution` or `file_change`, reporting the native local command tool unavailable (17,760 input, 87 output, 59 reasoning). A changed process-only diagnostic added `features.plugins=false`; it also emitted no native command/file-change event and gave the same tool-unavailable result (16,486 input, 117 output, 88 reasoning). The earlier Northstar-root smoke had the same result (18,185 input, 294 output, 236 reasoning). No child used the parent wrapper or changed files.

A bounded Codex Advisor Council reviewed this evidence. It recommends inspecting one already-correlated request/response trace for the `tools` declaration; if absent, the CLI did not provide the shell capability, and if present, inspect schema handling without assuming translation failure. The raw CLI JSONL contains no request ID or tools payload. Existing Subroute gateway logs for the smoke window contain no matching prompt marker/path, so there is no correlated payload to inspect. Following the Council's stop condition, no tracing was enabled, no request was replayed, and no route/configuration was changed. Council usage was Gemini 3,465 and Sol 1,027 tokens (4,492 total); advice is recorded in `tmp/dispatch-context/advisor-codex-tool-exposure-followup-20261023.md`.

At this point the cause was narrowed but unproven: direct tools worked on the active target, while the current Codex CLI invocation supplied no observable native command event, and the missing outbound `tools` evidence prevented distinguishing CLI registration from downstream shell-schema handling. That diagnosis required an existing correlated trace or authorization for a one-request redacted diagnostic recording tool names/types and response event types only, without request text, headers or credentials; no such trace was enabled, no request was replayed and no route or configuration was changed. Claude remains unavailable without an already-authorized task-scoped inference key accepted by the Messages route; no new credential was made.

## Windows sandbox home root cause and verified smoke

A later diagnostic identified the actual blocker behind the missing native events, so the "narrowed but unproven" conclusion above is superseded. The Codex CLI sandbox on Windows requires a resolvable home directory. A run with no `HOME` registered still registered `exec_command`, but the Windows sandbox refused to start and the run ended with `windows sandbox failed: no home dir`. The missing `command_execution` in the earlier smokes was therefore a sandbox startup failure, not absent tool registration and not route behavior.

A later CLI run used the same route, model alias `default`, profile `subroute-subagents`, Responses protocol and read-only sandbox, with process-only `HOME=%USERPROFILE%`; the successful invocation also used a shorter one-command assignment, low reasoning effort, and disabled the configured BrowserOS MCP server. It exited 0, emitted exactly one `command_execution` and one `turn.completed`, and returned the synthetic marker. Because more than one invocation detail changed, this was not a one-variable causal comparison.

Verified facts for that direct run: the Subroute preflight passed for `http://127.0.0.1:4000/v1` with alias `default`, including a unique response and full stateless function-call/result round-trip; the live route was `minimax-flash`, mode `force`, policy 115; usage was 258,061 input and 4,860 output tokens, with total usage absent. No route, model, credential or global setting changed.

The updated helper was then exercised from a caller process with `HOME` absent. It used the existing `USERPROFILE` only for the child, returned the exact synthetic marker, emitted one native `command_execution` and one `turn.completed`, exited 0, and restored `HOME` to absent. That helper-mediated run used 53,559 input and 382 output tokens; total usage was absent. The assigned write worker used the same route/profile with process-only `HOME`, completed with 40 `command_execution`, five `file_change` events (two scoped durable files), and `turn.completed`; it used 2,427,889 input and 38,322 output tokens, with total usage absent. The worker also made many redundant context reads, so this is operational evidence but weak context economy. No route, model, credential or global setting changed. The helper fallback is process-only and restores the caller's exact prior `HOME` state. Retained smoke artifacts are under `tmp/dispatch-context/native-gate-smoke/`; the write-worker JSONL and stderr are under `tmp/dispatch-context/native-home-fix-worker2/`.

**Limitation** — the helper has passed once in read-only mode and once in `workspace-write`, both with caller `HOME` absent. These two runs do not establish repeated reliability, other working directories/hosts, Claude Code's Messages-protocol path, or lower-cost task execution. Keep assignments exact-path and bounded, review every handoff, and retain the route/credential/sandbox boundaries.

## Operator recipe: helper-mediated smoke, then bounded write

The helper flow has now passed once in each mode: the read-only marker smoke returned the exact marker, and a following `workspace-write` worker changed only this report. The write worker exited 0, emitted 18 `command_execution` events, one `file_change` for the assigned report, and `turn.completed`; caller `HOME` remained absent after return. It used 330,757 input and 8,898 output tokens; total usage was absent. These observed runs support the recipe but do not establish repeatability or cost efficiency. The sample paths below are reusable examples, not the literal targets used in both trials.

Both steps go through the documented [`Invoke-CodexChild`](../../../skills/codex-subagents/SKILL.md) helper with the route, model alias `default`, profile `subroute-subagents`, credential source and sandbox policy unchanged. `HOME` stays process-only: the helper uses an existing `USERPROFILE` for the child only when `HOME` is missing or does not resolve to an existing directory, and it restores the caller's exact prior `HOME` state afterwards. Do not set `HOME` yourself, and never set a user-level or machine-level `HOME` to work around a missing home directory.

### 1. Synthetic read-only marker smoke

```powershell
$marker = 'northstar-native-tool-marker'
$assignment = "Run one native read-only shell command that prints the exact marker $marker, then report that marker."
Invoke-CodexChild -Assignment $assignment -WorkingDirectory 'D:\github\northstar' -Sandbox read-only -UseObservedSubrouteSettings
```

### 2. Exact-path bounded write assignment

Run this step only after step 1 is accepted.

```powershell
New-Item -ItemType Directory -Force -Path 'D:\github\northstar\tmp\dispatch-context\native-gate-write-probe' | Out-Null
$target = 'D:\github\northstar\tmp\dispatch-context\native-gate-write-probe\probe.txt'
$assignment = "Write the single line probe to exactly $target and change no other path."
Invoke-CodexChild -Assignment $assignment -WorkingDirectory 'D:\github\northstar' -Sandbox workspace-write -UseObservedSubrouteSettings
```

`-UseObservedSubrouteSettings` reproduces the observed child overrides. `-DisablePlugins` is a separate opt-in for assignments that do not rely on plugin-provided integrations; omit it otherwise.

### Acceptance

Accept a step only when all of the following hold, judged from the structured JSONL events rather than from the model's prose:

- exit code 0
- a `turn.completed` event
- a successful `command_execution` event
- for the write step, additionally a `file_change` event whose path is confined to the assigned file

Keep stdout (JSONL) and stderr separate. Stop the run when the native events are missing, when a change lands outside the assigned path, or when the child reaches for the parent's `functions.exec` wrapper; that wrapper is never the worker shell.

## 2026-10-22 local / 2026-10-23 UTC: repeated CLI command-process failure

A fresh direct Subroute `default`/Responses preflight passed both the unique-response check and complete function-call/result exchange. The following Codex CLI 0.154.0 read-only smoke used the dedicated `subroute-subagents` profile, process-only HOME fallback, explicit `http://127.0.0.1:4000/v1` override and the documented shell/plugin/MCP overrides. The CLI attempted its native command path, but Windows returned `CreateProcessWithLogonW failed: 267`; there was no successful command result or completed handoff to accept. The exact read-only CLI process tree remained alive after the 30-second bound and was stopped. No task worker or file change followed; usage is unknown. This is a CLI process-creation failure, distinct from raw route transport and from the earlier `no home dir` failure. Keep write dispatch closed until a fresh native-command smoke completes; do not retry this unchanged invocation.

## Advisor-directed cwd diagnostic — 2026-10-22 local / 2026-10-23 UTC

Advisor GPT-6.1 Sol (709 reported total tokens) judged `CreateProcessWithLogonW failed: 267` most likely a local Windows sandbox child-launch/working-directory failure. It recommended one read-only diagnostic using `C:\` for the CLI cwd and an explicit absolute `cmd.exe /d /c` directory command. That distinct probe used the same `default` Subroute profile, process-only HOME fallback, explicit loopback URL override and read-only sandbox, but produced no command result within 45 seconds; the exact probe was interrupted. The cwd hypothesis remains unverified. `decision_changed=true`: this consultation caused one changed-cwd diagnostic instead of another identical attempt. No successful CLI tool handoff, worker write or route/config change followed. Keep write dispatch closed until a fresh native-command smoke completes.

## 2026-10-23: closed-stdin Subroute helper verified end to end

Local `codex exec --help` states that, when stdin is piped together with a positional prompt, the CLI appends stdin as a `<stdin>` block. That explains the non-TTY invocation's "Reading additional input from stdin..." stall. The skill now sends the full assignment on stdin using `codex exec ... -`, including the `Invoke-CodexChild` helper and its write, read-only and observed-path examples. It also uses the proven loopback IP `127.0.0.1`; prior Northstar trial evidence records that `localhost` did not connect while the loopback IP did.

Parent acceptance extracted the updated helper from `SKILL.md` and ran it in a non-TTY PowerShell process with caller `HOME` absent and a sentinel caller stop-hook variable. Through the Subroute `default`/Responses profile and process-only overrides it returned one successful native `command_execution` with exact marker `UPDATED_HELPER_NATIVE_OK`, one `turn.completed`, and exit 0. The helper restored both caller variables exactly. Reported usage was 53,400 input and 265 output tokens; total usage unknown. Raw sanitized JSONL/stderr are under `tmp/dispatch-context/updated-helper-e2e-20261023/`.

One bounded write worker changed only `skills/codex-subagents/SKILL.md` and completed with 17 native command events, `turn.completed`, exit 0, 555,616 input and 20,830 output tokens. Its JSONL contained **no `file_change` event**. The parent reviewed the real diff and independently verified the updated helper; the artifact is useful, but this worker run does not count as proof of structured file-change acceptance. The preceding plugin-enabled worker attempt waited 120 seconds without modifying the target and was stopped; the subsequent scoped run used `features.plugins=false` because this documentation task needed no plugin integrations. This is observed performance, not evidence that plugin disabling caused the difference.

Earlier read-only diagnostics also distinguished the causes: no-TTY prompt-plus-pipe can stall; with a PTY, a command completed but the child entered its stop-review hook because the child-only marker was omitted. The verified helper path fixes both by using `-` and its conditional process-only `DONT_STOP_EARLY_REVIEW_CHILD` marker. It does not establish general reliability or accepted write evidence. Next: run one exact-path write task through this helper that uses the CLI's native file-edit tool and emits a confined `file_change` event; independently review and test that result. Claude's Messages route and actual Windows product delivery remain open.

## 2026-10-23: native file-change write path verified once

After the updated helper passed its live read-only smoke, a separate `workspace-write` Codex CLI probe used the same stdin `-` transport, process-only Subroute profile, `HOME` fallback, child-only stop-hook marker and plugin-disabled setting. The JSONL completed with exit 0 and `turn.completed`; it contained four `file_change` lifecycle events (add/update, each in-progress/completed), all confined to `tmp/dispatch-context/native-file-change-proof-20261023.md`, and zero shell command events. Parent inspection confirmed the exact one-line synthetic file. Worker-reported usage: 227,037 input and 7,917 output tokens; total unknown. The disposable fixture is retained as lightweight dispatch evidence.

This establishes one current successful native-file-edit write on this host with the corrected stdin/hook setup. It does not prove repeated reliability, production implementation quality, Claude Code compatibility, economical token use, or broader host portability. Preserve the earlier shell-written skill edit as a distinct partial handoff lacking `file_change`; do not merge its evidence with this probe.

## 2026-10-23 continuation: current route/read proof and two Guidance iterations

The current parent preflight used `http://127.0.0.1:4000/v1/responses`, model alias `default`, Responses protocol, and the process-provided `GATEWAY_MASTER_KEY` without recording its value. A fresh unique response passed; a forced `confirm_marker` call returned the exact marker; replaying a stateless `function_call` with its matching `function_call_output` and user echo returned the same marker. A helper-mediated read-only Codex CLI smoke returned one exact marker using two `command_execution` lifecycle events (one native call), zero file changes, `turn.completed`, and exit 0. Sanitized receipt: `tmp/dispatch-context/continuation-read-smoke-20261023/route-preflight.json`; raw CLI JSONL: `tmp/dispatch-context/continuation-read-smoke-20261023/worker.jsonl`.

The first exact-path narrative-alignment write used the documented helper and produced a plausible mapping paragraph and report. Its parent-supplied brief included the relevant source facts and a hard deadline. The worker returned the two-minute checkpoint, but after 21 native command calls (42 lifecycle events) it had no `turn.completed`; the parent stopped it after about 5 minutes 10 seconds. Six file-change lifecycle events covered only `skills/codex-subagents/SKILL.md` and its assigned report. The artifact is accepted as partial source work, not as a completed worker handoff; usage is unknown.

Advisor Council then recommended tighter exact-section input, a named existing check or parent-owned validation, explicit excluded reads, and the unchanged five-minute deadline; it rejected an unsupported command-count cap. Advice changed the next dispatch brief. A second worker edited only the Guidance bullets in the orchestrator and supervisor templates and its assigned report. It used the specified two template paths and parent-owned link review, completed with 14 native command calls, six file-change lifecycle events confined to the three authorized paths, `turn.completed`, and exit 0. Usage was 334,809 input (300,643 cached), 8,887 output, 5,097 reasoning; cost unknown. Parent review found both bullets identical, local links resolving, and no whitespace errors. One task completion demonstrates feasibility with a tightly scoped brief; it does not establish that the templates caused the result, repeated reliability, or economical context use. See [narrative report](brief-narrative-alignment-20261023.md), [Guidance bounds report](guidance-bounds-20261023.md), and the [trial log](cli-trials.md#2026-10-23-exact-range-guidance-iteration-after-narrative-worker-timeout).

## 2026-10-23: corrected helper smoke and source-instruction brief update

After a fresh unique-response and complete function-call/result preflight, one helper smoke was stopped by the parent before a native command event appeared. It is recorded as an intervention, not an accepted failed worker run. A corrected read-only helper smoke then passed with one successful `command_execution`, exact marker `NS_HELPER_READ_CORRECTED_c31701f765c3431d9921a30c197c6f19`, `turn.completed`, exit 0 and no file changes. Receipt: `tmp/dispatch-context/helper-read-smoke-corrected-20261023/worker.jsonl`.

A bounded `workspace-write` worker edited only the Guidance placeholders in `skills/codex-subagents/templates/orchestrator.md` and `supervisor.md` plus its assigned report. Structured JSONL recorded 13 completed command events, three confined file-change events, `turn.completed` and exit 0. The text now requires repository instructions and essential source/test facts in the prompt or by exact path; links are supporting context, and required instructions must not be waived. Parent review found nine unique local links in each template and two links in the report, all resolving; scoped diff and untracked-report whitespace checks passed. Worker usage was 530,912 input (485,888 cached), 13,077 output, 8,306 reasoning; cost unknown. This source increment remains untested behaviorally, and its context use is high. Do not claim improved scope compliance until a later real implementation dispatch is independently inspected. See the [brief guidance report](brief-source-instructions-20261023.md) and [trial record](cli-trials.md#2026-10-23-source-instruction-guidance-added-to-both-codex-briefs).

## 2026-10-23: rendered-brief HOME regression completes with high usage

The parent rendered the updated orchestrator template for a real bounded test task. The assignment named AGENTS.md sections, helper lines 157-165, test lines 458-469, the existing focused pytest command, exact write/report paths, parent acceptance, and excluded broad reads. It omitted the shared test-harness lines and did not expressly prohibit an unscoped `rg -l` search or reading the full target test file; the worker made those additional reads. It did not write outside the assigned test and report paths.

The worker added a parametrized synthetic test for a regular-file `USERPROFILE` with `HOME` absent or set to a missing path. It verifies the Codex stub is never invoked, the file remains unchanged, and caller `HOME`/`USERPROFILE` state is restored. Baseline was 15 passing tests; worker final run passed 17, and the parent independently reran the full focused suite with 17 passed in 9.02s. Structured events show exit 0, `turn.completed`, 13 completed native command calls and four file-change lifecycle events confined to the two assigned paths. Elapsed time 203.8 seconds. Usage: 618,703 input (578,733 cached), 10,954 output, 4,959 reasoning; cost unknown. Receipt: `tmp/dispatch-context/userprofile-file-home-guard-20261023/worker.jsonl`; parent-rendered brief: `tmp/dispatch-context/userprofile-file-home-guard-20261023/rendered-brief.md`.

This is one useful test handoff using the revised brief structure. It is not evidence that the template alone caused the result, nor that delegation is economical or repeatable. The parent must include all relevant harness ranges and explicitly forbid repository-wide text searches when they cannot affect acceptance. See the [handoff](userprofile-file-home-guard-20261023.md) and [evaluation](../../evals/dispatch-context.md).

