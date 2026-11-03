# Advisor-council long-running review — completed 2026-11-03

Status: **READY for the tested local workflow.** Fresh Goal `g-44c4057270364fb2acf228cf490114c8` completed at 02:27:30 UTC. The separate framework reviewer returned READY for source identity `45baccb235f20e9f28a52760eeb88f4257d4327b96601951947a0205987b5928` (41 file hashes, locally recomputed; not a Goal-MCP freeze receipt).

## Delivered behavior

Human sets each Goal and reads reports through MCP. Claude Code main chooses a template or custom A2A team, delegates implementation, runs checks, obtains independent review, and recovers the current Goal. COMPLETE ends that controller and waits for the human's next Goal. There are no self-imposed budget, turn, total-runtime or retry-count caps. Existing permissions and acceptance remain binding.

[Setup and MCP commands](../../../a2a-stack/docs/SETUP.md) describe the installed service. Daily use is `set_goal` → `get_goal_report`; no manual role dispatch or recurring task restart is required. The host's existing Windows Scheduled Task performs logon/one-minute health recovery. The optional fixed scheduler and old Codex backup automations remain paused.

## Exact acceptance

| Criterion | Observed result |
| --- | --- |
| Actual delivery | Added atomic `enqueue_many` to a working SQLite task ledger/JSON CLI |
| Product candidate | `01fa04015c422244d41c71516f2111f6c9da123ed89b5a07a2328156deb8ce81` |
| Ledger SHA-256 | `632953b68bddc8d8276eabaa0d99f9efef2e88dc508c9263fc4541826cb563e9` |
| Immutable contract | Four tests passed: CLI/persistence, concurrent exactly-once claims, idempotency, recovery/ownership |
| Endurance | **7200.553 credited seconds, 11,764 rounds, 282,336 completed tasks** |
| Endurance input identity | `ebdc45476ad11ad002113753fc53deb90d318fda37becdb52470ec997619c351`, binding ledger + both checkers |
| Separate product reviewer | `dac6e070-b6d4-4e43-9651-be451fc32cab`, READY for that exact product candidate |
| Program acceptance | Both registered checks exit 0; accepted receipt binds implementation producer, independent reviewer and candidate |
| Final Goal | COMPLETE, native exit 0, owner null, formal controller_running=false; recorded coder/verifier/reviewer processes absent |
| Frozen inputs | All seven framework/check/registry hashes unchanged during the fresh trial |
| Framework independent QA | 41 source hashes match; 63 offline tests passed (agent22 + autonomy33 + runtime8); final READY reuses unchanged-source evidence |

The final host endurance recheck reused completed coverage only after exact input-hash, duration, round-count and database-integrity validation. It did not substitute a short smoke test for two hours of real work. Eleven checker process sessions include the final cached recheck; they do not mean eleven simultaneous workers.

## Recovery without corrective operator actions

The fresh trial retained Goal, native session `21a4dcef-4cd5-42b4-92bc-22ecfe9cb693`, and spec digest `14ac14bc8db547da7c1e1e629a8d454266d45471ffc17c793c33f20f59c4b724` throughout:

1. Planned host termination plus MCP outage during implementation: ten local readiness probes failed while MCP was unavailable, without a model-call loop. Automatic host recovery restored tools. The interrupted coder was terminalized FAILED; its continuation delivered under the same Goal/session.
2. Planned midpoint host termination after 600.953 credited seconds: health recovery restarted the host, reconciled the interrupted checker, and resumed the same manifest-bound workload.
3. Transient Windows progress-file replacement failures: unsuccessful verifier attempts truthfully retained failed receipts. Main autonomously retried the original checks and retained checkpointed work until success. The cause of `WinError 5` is **unknown**. The native summary's concurrent-reader explanation is not established evidence.

Root made no corrective Goal dispatch/resume/cancel or framework/check/registry edits in this fresh trial. Fault injections were the planned adversarial test, not rescue. Earlier diagnostic Goal `g-24f186b05bc14f76bcc743622a04c796` did require operator source upgrades and provisional QA; it remains **assisted diagnostic evidence**, not the unattended acceptance run.

## Repairs prompted by council and diagnostics

The default advisor route returned HTTP400 (`model=default` absent). At the user's direction, actual Subroute configuration and live model discovery selected `codex-gpt-6.1-sol-advisor`, with independent `gemini-4-argon-advisor`. No global model, auth or Subroute configuration changed. Both advisors required infrastructure faults and a multi-hour workload beyond the prior smoke evidence. [Council response](council-response.json) and [handoff advice](council-handoff-advice.json) preserve their inputs; advice itself is not QA.

Repairs before the frozen fresh trial added actual MCP required-tool readiness and same-session capability reconnection; clarified leaf handoff/main ownership of independent QA; prohibited child CLI ceilings; required fresh formal task status instead of stale logs; and clarified final structured-output fields without weakening the schema. All four changed framework files were independently reviewed.

## Durable evidence and limits

[Runtime acceptance](council-runtime-acceptance.json), [formal terminal report](council-formal-terminal-report.json), [final framework review](council-final-independent-review.json), [source manifest](council-current-source-manifest.json), [source-test results](council-source-checks-ready.json), [frozen inputs](council-frozen-inputs.json), [first fault](council-first-fault-observation.json), [midpoint fault](council-midpoint-fault-observation.json), and [retry observation](council-verifier-retry-observation.json) preserve lightweight evidence. Raw private execution logs remain under ignored `tmp/a2a-stack/`.

This acceptance covers the observed local Windows/Claude Code/A2A/MCP environment and workload. It is not a full A2A conformance suite, whole-OS reboot test, cross-platform guarantee, native Codex timed-trigger test, or completion of the separate Instacart application. Current host workspace is `D:/github/northstar`. No commit, push or production deployment was requested or performed. No further Goal is automatically submitted after completion.

## Post-completion reconciliation

The parent executor rechecked the original Goal and acceptance in the owning Northstar workspace after completion review: live MCP still returned COMPLETE, accepted=true and controller_running=false; 41 source hashes and seven frozen inputs matched. Live discover_agent and get_task traversed the existing MCP/A2A route and returned the reviewer Agent Card and completed reviewer artifact. Current Windows host schedule and Docker gateway state agree with the limited scheduling claims above. No Goal or workload was restarted. [Read-only reconciliation receipt](council-post-completion-reconciliation.json).

## Requirement reconciliation: scheduling, supervision and QA

The original request explored two Codex scheduled tasks. Later owner instructions expressly allowed changing the design, rejected a fixed/static agent stack, required the main agent to decide which team to start, and retained human goal-setting/report-reading through MCP. Under that design-change authorization, the current implementation replaces the two recurring business prompts with one continuous per-Goal owner plus a persistent host health schedule. This is an implementation decision preserving the original outcomes; it is not a claim that the owner separately approved or that we tested a Codex-native timer. There is no new Goal until the human submits one.

| Required outcome | Exact evidence and boundary |
| --- | --- |
| Actual scheduled work rather than a saved cron definition | Historical [scheduler receipt](scheduler-evidence.json): timed A2A task `fa110bfb-6e80-4080-998c-d93ae97fffd9` survived scheduler restart and produced an artifact; timed Claude task `1e35a647-52f3-4d48-9816-69df45c77b6a` changed runtime code and completed with native exit0. This proves that earlier timer route actually executed work; it is historical, not approval of current source. |
| Current scheduling advances the active Goal | Existing Windows logon/PT1M indefinite health schedule restarts only the missing host. [Midpoint fault](council-midpoint-fault-observation.json) records no manual restart, new host/owner identities, same Goal/session/spec, old checker terminal failure, then continuation `48ba79ac-4c2e-4727-8d60-b8902a645f42` advancing real work from600.953s to665.609s; final accepted workload reached7200.553s. This is scheduled recovery that leads to actual progress, not a health check alone. |
| Claude Code work handoff | [First-fault receipt](council-first-fault-observation.json): interrupted coder `5d8faf41-1bc0-439e-a3c2-4b4d42ffcb0b` failed; continuation `01ab51fc-7acb-425d-81cd-8257ec1a97c9` exited0 and is the producer bound in the [accepted receipt](council-runtime-acceptance.json). |
| Supervision and ordinary-error recovery | [Verifier retry receipt](council-verifier-retry-observation.json) and final checks distinguish failed attempts from success. The Goal main retained the same spec/checkpoint, dispatched continuations, and reached accepted completion without corrective operator Goal actions. Infrastructure outage waited locally until actual MCP capabilities recovered; it did not ask the user to rescue it. |
| Independent QA | Final verifier `c44de7a9-e7eb-4886-be19-ef54c71d6cbf` passed original checks; separate reviewer `dac6e070-b6d4-4e43-9651-be451fc32cab` returned READY for product01fa0401... . [Framework final QA](council-final-independent-review.json) independently binds41source files/63offline tests and seven unchanged frozen inputs. |
| Real protocol interoperability | Official SDK acceptance covers discover/send/get/artifacts/error/cancel on the local MCP/A2A route; current [post-completion reconciliation](council-post-completion-reconciliation.json) additionally read the role Agent Card and completed reviewer task artifact through that existing route. No plain subprocess handoff is being counted as protocol proof. |
| Completion boundary | [Current formal report](council-formal-terminal-report.json): COMPLETE, accepted=true, controller_running=false. Human sets the next Goal. |
| Codex-native timed triggering | **Unverified, not part of this current implementation's required mechanism.** The outcome is provided by continuous Goal ownership and actual Windows timed recovery above. No Codex timer pass is claimed; none was silently enabled to duplicate the owner. |

The migration checkpoint's actual scheduling/restart requirement is retained and mapped above. Its outcomes were not dropped. No concrete new implementation defect was found in this reconciliation, so no additional CLI worker or duplicate Goal was dispatched. Full protocol conformance, whole-OS reboot and arbitrary other-project acceptance remain outside the tested envelope.

## Completion audit in the owning repository

The installed Task Completion Review guard was invoked in its documented direct mode with repo `D:/github/northstar`, the existing configured native executable/model, read-only child containment and a brief carrying the original outcome and retained limits. Unlike the prior event-mode audits confined to the Instacart chat directory, this reviewer actually read the Goal and seven designated evaluation records. It returned **complete**, confirming the scheduling redesign, original checks, source/product binding, independent READY, protocol evidence, recovery and controller exit. [Exact completion-audit result](council-completion-audit.json). Global hooks/configuration and business runtime were not changed.
