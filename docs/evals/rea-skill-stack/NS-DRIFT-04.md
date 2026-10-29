# NS-DRIFT-04 — bounded exercise evaluation

This evaluation covers one Codex worker run of the case in the [Northstar skill-stack workflow](../../northstar/skill-stack-workflow.md#bounded-drift-sensitive-evaluation-plan). It is a single observation, not a reliability estimate.

## Result

**Fail for this run.** The case required a final handoff whose claims matched completed evidence, preserved unknowns, and did not claim independent QA. The worker report said the native event JSONL and stderr were empty and treated the case as unexecuted. Parent inspection after the process exited found a completed 30-event stream, eight command executions, two scoped file changes, six handoffs, one completed turn, and a skill-description-budget warning. The worker had inspected the parent-streamed file before capture finished, then made an unsupported final claim. The report required parent correction. The process exited 0 after 66.8 seconds; process success does not satisfy the evidence-integrity criterion.

The worker did preserve several unknowns and did not infer broad reliability. Those strengths do not remove the observed failure. This is evidence that the case detected a real handoff/evidence timing defect in one run; it does not prove general Northstar drift behavior or mitigation.

## Bounded run and evidence

The assigned single write-enabled Codex CLI worker used Subroute alias `default`, plugins disabled, workspace-write permission, one case, no worker retry or nested agent, and a 180-second parent wall cap. The corrected run used a task-scoped key restricted to `default`, with maximum budget USD 0.25, parallelism one, and 20-minute lifetime/budget duration. Its text and function-call/result preflights passed. The CLI smoke returned the exact marker and completed. Worker usage was reported as 316,587 input tokens (104,960 cached) and 3,573 output tokens. The native event stream is retained in ignored task scratch.

An initial separate key capped at USD 0.50 also passed text and function-call/result preflights, but its smoke added a trailing period after the required marker and failed the exact-marker gate. Its native stream was overwritten by the corrected attempt; a sanitized failure receipt remains. Both aliases were revoked and their absence confirmed. Aggregate maximum key-budget exposure was USD 0.75, exceeding the originally planned single-key cap of USD 0.50. This is a ceiling, not actual spend; total Codex cost was unavailable. No further Codex route call is authorized under this evaluation.

At this Codex exercise checkpoint, the local Soak checkout and runner contract were inspected. Its sequential runner starts a fresh subprocess per iteration, and Python module discovery failed in that environment. The framework/adapter was not run because the direct case already used the sole allowed worker and a runner invocation would create nested Codex processes. Therefore this was a direct CLI case, not a Soak framework run. The smoke prompt invoked `$soak-testing`, but effective personal skill discovery/reload was not independently proved; the Codex and Claude installed copies were byte-matched to source only. A later Claude attempt separately confirmed isolated-profile discovery; it is recorded in [Claude route receipt](claude-route.md).

## Earlier Claude route checkpoint (superseded below)

Claude Code `2.1.251` was run with a fresh isolated `CLAUDE_CONFIG_DIR`, `--bare`, process-only Subroute settings, and one temporary `default` key capped at USD 0.50, parallelism one and 20-minute duration. The first attempt selected an inherited internal `MiniMax-M2.7[1m]` override and failed before inference. The override was corrected only in the child environment. Claude's native CLI smoke then exited 0, returned the exact marker, and reported USD 0.008085 for 1,537 input and 16 output tokens.

The required direct Anthropic Messages tool-use/result continuation was rejected by `max_parallel_requests` with remaining capacity 0 on two attempts. At this checkpoint no Claude review worker had been dispatched. The temporary alias was deleted and absence confirmed. This does not constitute independent review or Claude-side case execution. A later attempt established isolated-profile discovery but did not complete the worker; see the updated [route receipt](claude-route.md).

## Acceptance and remaining work

The Codex case failed its observable evidence-integrity criterion. A later Claude worker read the isolated Soak skill but did not complete its case or handoff after 429 retries and a `default` model error; see the [Claude route receipt](claude-route.md). Claude isolated-profile reading is established for that exact run. Codex CLI prompt construction lists the installed skill, but model invocation/use remains unverified. The Soak runner's synthetic self-test passed separately; no framework adapter or target case exercised Northstar, Codex or Claude. Actual Claude provider cost remains unknown. The task-level workflow and package docs were independently inspected, with links and installation paths checked separately. Full exercise and drift-mitigation acceptance remains open.

The later Claude attempt in the [route receipt](claude-route.md) supersedes the route and runtime-discovery checkpoint above. Do not make another paid request until Subroute diagnoses the exhausted concurrency slots and the CLI `default` model error is resolved. Before any later attempt, reconcile available spend records and set one aggregate cap covering provisioning, preflights, smoke, workers, review and retries. Preserve complete receipts after process exit. Do not claim general reliability from these bounded observations.
