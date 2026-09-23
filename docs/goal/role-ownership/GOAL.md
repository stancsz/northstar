# Goal: Clear ownership from North Star to tasks

Status: done

## Outcome

Make orchestrator → North Star, supervisor → goal, and worker → task ownership explicit and consistent in the Markdown practices. Preserve [owner standards](../../northstar/README.md) and lightweight documentation.

## Acceptance and result

- Core skill names each role's decisions, documentation, completion responsibility, and escalation boundary.
- Goal lifecycle, goal template, and companion delegation skill use the same mapping.
- Critics and verifiers report findings to the accepting role; workers repair task defects and supervisors own integration repairs.
- Human intent and authorization remain human-owned. Small work can use one agent with concise documentation and no extra management layers.

## Follow-up: durable worker reports

The owner requested that each role own and use its own records. Orchestrators maintain `docs/northstar/`; supervisors maintain their `docs/goal/<goal>/GOAL.md` and index entries; workers produce work and write `docs/reports/<goal>/<task>.md`. Chose `reports` because it accommodates completed, partial, and blocked handoffs.

Task: align the core skill, delegation skill, protocol, lifecycle, template, repository instructions, and guides with those boundaries. The editing agent fills all three roles for this focused Markdown change.

- Worker handoff: [align reporting](../../reports/role-ownership/align-reporting.md).
- Acceptance: each role reads and maintains its assigned records; the worker report path and contents are clear; the supervisor consumes reports and records decisions; evaluations remain distinct; existing hygiene, storage, and human authority boundaries hold.
- Supervisor decision: accepted the reporting task after inspecting the changed instructions, worker report, local links, and repository layout. No remaining integration repairs.
- Orchestrator decision: accepted the aligned ownership and handoff model against the owner's request. All three roles have explicit reading, writing, and acceptance boundaries; the report directory is implemented and linked. Documentation review does not establish behavioral compliance by future agents.

## Ownership and evidence

The editing agent performed orchestrator, supervisor, worker, and documentation review responsibilities in this change. No independent reviewer or delegated execution was used.

Updated the skills, template, and durable direction. See the [documentation review](../../evals/role-ownership.md) for scope and limitations.
