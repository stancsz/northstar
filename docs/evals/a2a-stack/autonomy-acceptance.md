# Autonomous Goal acceptance — 2026-11-02

This is the earlier accepted increment. Subsequent [advisor-council long-running review](council-long-running-review.md) found a native MCP capability-recovery defect and changed the runner; that newer long-running acceptance completed on 2026-11-03 with independent READY for the current source identity. Earlier READY remains historical evidence for its own source.

Current operating boundary: human sets a Goal and reads reports through MCP; the native Claude Code main agent chooses a dynamic A2A team, delivers and verifies that Goal, then waits for the next human instruction. It does not invent subsequent project goals.

## Verified behavior

| Evidence | Actual result |
| --- | --- |
| [Goal 1 report](autonomy-goal-1.json) | COMPLETE, retained after host restart. Coder, trusted verifier and separate read-only reviewer; first verifier returned exit 75, main retried successfully, original host check and exact-candidate READY passed. |
| [Goal 2 report](autonomy-goal-2.json) | COMPLETE after one injected controller failure; same Goal and native Claude session resumed, host_restart_count=1; both original checks and separate READY passed. |
| [Fault receipt](autonomy-fault.json) | One identity-checked controller termination, no corrective intervention after injection. Native journal subsequently contained 11 intermediate HTTP 429 api_retry events and continued to accepted completion. |
| [Core independent review](autonomy-core-review.json) / [manifest](autonomy-core-candidate.json) | 59/59 isolated offline tests; guards cover immutable acceptance, completed coder provenance, independent candidate review, verified external escalation and durable process/task recovery. |
| [MCP acceptance](autonomy-mcp-acceptance.json) | Real MCP SDK transport, task artifacts, error and cancellation/process-exit checks. Gateway additionally exposes human Goal and dynamic stack tools (17 total). |

Both completed controllers exited; neither initiated another Goal. The final documentation/instruction-only rebind is recorded in final-candidate.json and final-review.json alongside this file. Earlier core-candidate.json/core-independent-review.json and scheduler-evidence.json are historical increments, not current whole-stack approval.

## Deployment and limits

Windows host retains native Claude authentication; Docker Compose runs the loopback-only MCP gateway without credentials or repository mounts. Official A2A SDK handlers use per-role SQLite task stores. Windows Scheduled Task health triggers recover the host process; old fixed scheduler and backup Codex automations are paused. Codex MCP connection northstar_a2a is configured at http://127.0.0.1:18892/mcp. See [setup](../../../a2a-stack/docs/SETUP.md).

Accepted for this local, current-workspace execution increment and these observed faults. This is not full A2A conformance, multi-host certification, all-failure recovery or a promise of unlimited provider availability. No arbitrary project acceptance follows from the framework tests; Instacart T103/render-comparison and capture restrictions remain unchanged. No public push, production deployment or transaction occurred.
