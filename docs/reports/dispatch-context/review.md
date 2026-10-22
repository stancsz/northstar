# Independent review: dispatch context

Status: accepted for documentation scope. Reviewer: independent Codex subagent.

## Verdict

The change makes assignment context more actionable without adding an arbitrary prompt cap or a routine extra approval turn. It preserves the existing five brief elements, role ownership, and independent acceptance rules. No material defect found in the reviewed scenarios.

## Scenario inspection

- **Clear single-step task:** `skills/codex-subagents/SKILL.md:108` explicitly skips the understanding check, avoiding an unnecessary acknowledgment. The opener at line 100 still requires the assigned result and next action.
- **Substantial ambiguous multi-step task:** lines 100 and 108 require current decision-relevant facts, explicit unknowns, and a short restatement of result, acceptance, and first action. A manager can correct a mismatch before it compounds; a clear assignment proceeds without another approval turn.
- **Missing essential input:** line 100 says not to substitute background links for essential instructions/evidence and to name consequential unknowns. Existing worker guidance at line 92 says to report the precise dependency if blocked and continue independent assigned work; Northstar's recovery instructions cover the exact unblock condition. This is sufficient without duplicating a new missing-input rule here.
- **Large unrelated background:** line 100 directs the sender to link supporting background rather than paste unrelated history, while retaining essential facts in the prompt. Removing context that cannot change the next action or acceptance gives the sender a practical relevance test without a word/line quota.

## Scope and limits

The manager templates at `skills/codex-subagents/templates/orchestrator.md:8` and `skills/codex-subagents/templates/supervisor.md:8` make the same context distinction and request a next action. The neighboring inference subfield is present in both templates but was outside this change's scope; the existing instruction to omit irrelevant fields applies.

This was a source/document scenario review only. No failed dispatch transcript or live agent behavior was available, so the review cannot establish that the guidance prevents drift or saves tokens in use. No runtime testing was performed.

## Follow-up review — 2026-10-22

The latest wording closes a useful ambiguity: the task brief now says acceptance criteria and scope/authority constraints belong explicitly in the prompt, not only in linked background (`skills/codex-subagents/SKILL.md:115`); the orchestrator and supervisor templates call out pass criteria and scope/authority limits (`skills/codex-subagents/templates/orchestrator.md:6,10`; `skills/codex-subagents/templates/supervisor.md:6,10`). This is concise and directly actionable, and it retains the earlier distinction between must-know facts and supporting links. I found no added process or authority conflict.

I inspected the three paired trial reports and their fixture/output artifacts under `tmp/dispatch-context-trials-2026-10-22/`. Each condition used one GPT-6 Luna low-effort agent; fixture inputs were identical by hash. Outcomes were correct across the pairs: inventory summaries included only available SKUs in ascending order and totaled 3 items/9 units; missing-input tasks left July totals unknown and named the absent source. One original control had a conflicting estimate instruction, which weakens that pair's comparison. In the final neutral missing-input pair, control and treatment accessed the same source files; both correctly reported the figures unknown.

The evidence remains **inconclusive** about whether the wording improves dispatch outcomes relative to control. The trials show the guidance can accompany correct results in these scenarios, but correctness was already achieved in controls. Per-agent token and time metrics were unavailable. The shorter treatment outputs in some reports are not measures of prompt context or inference cost. One agent per condition and the conflicting original control instruction also limit causal attribution. Do not claim measured token savings or general drift reduction from these trials.

## Follow-up review — 2026-10-22 (CLI trial evidence)

I checked the updated brief guidance, goal, evaluation, `cli-trials.md`, and the referenced scratch transcripts. The added direction to state acceptance criteria and scope/authority limits directly in the prompt is concise and actionable; the templates make both obligations visible. No new authority or role conflict found.

The matched Claude replication supports a **limited response-completion advantage in this one scenario**. The transcripts show both conditions read the same three source files from byte-identical fixtures. Control made a fourth Read call on the fixture directory, received `EISDIR`, and ended at `max_turns` without a handoff. Treatment returned the correct inventory summary in four turns. The saved receipts support the report's per-run usage and duration values (treatment 1,106 input / 341 output / 2,138 cache-read tokens and 5.3 s; control 1,168 / 501 / 1,792 and 10.6 s). This is one matched pair, so it cannot establish typical savings or broad drift prevention. The non-blocking `default[1m]` title diagnostic appeared in both.

Correction: I conflated the earlier native-trial fixture with this CLI replication. The CLI scratch README contains the inventory acceptance criteria, and the CLI trial report says both prompts requested a three-line text handoff; neither required creating `summary.md`. The read-only boundary is consistent with that text-response task, so the treatment's correct response supports the report's limited completion claim. This pair does not test file creation. The prompt text itself is not preserved in the raw CLI transcript, so I rely on the trial report for the three-line-format requirement.

The Codex CLI non-result is accurately reported at a high level: both conditions drifted from the inventory task into tool troubleshooting, and neither inspected the fixture or returned a task result, so these runs do not compare brief styles. The low-level failures differ: control records repeated JavaScript wrapper/input parsing confusion but no completed task-tool call; treatment shows that confusion followed by `exec_command` process-creation denials under policy for PowerShell, `cmd.exe` and `bash.exe`, then a malformed `apply_patch` probe. This is a tool/runtime access failure mixed with wrapper misuse, not evidence that either brief caused drift. No per-run usage receipt was available. Keep Codex CLI effectiveness unresolved and avoid attributing its failures solely to dispatch wording.
