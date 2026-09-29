---
name: codex-subagents
description: Plan and coordinate complex work through a three-layer hierarchy of orchestrators, supervisors, and workers, with dynamic team size and clear authority boundaries.
---

# Codex subagents

Default to one agent. Do not spawn subagents just because this skill is available or a task could theoretically be split. First decide whether parallel work is likely to materially improve speed or quality after accounting for coordination, integration, token cost, and tool limits. Use this skill's delegation process only when the task has multiple independent, reviewable workstreams and the expected benefit justifies the overhead. Keep simple, sequential, or tightly coupled work with the primary agent. When delegation is justified, use three reporting levels: one **Orchestrator**, zero or more **Supervisors**, and **Workers**. The number of supervisors and workers is chosen for the task; the hierarchy defines responsibility and reporting, not a fixed headcount.

## Plan the team

1. Define the requested outcome, constraints, and completion evidence before assigning work.
2. Split the work into bounded deliverables that can proceed with minimal overlap. Each worker owns one task and one write scope; give each task its own acceptance criteria and verification method.
3. Create a supervisor for each workstream that needs coordination, shared context, or first-pass integration. For a small task, the orchestrator can supervise workers directly. Do not add a supervisor when it creates more coordination than it removes.
4. Add workers only when their tasks are sufficiently independent to run in parallel. Keep tightly coupled changes with one worker or the orchestrator.

Treat roughly 20 agents as a possible scale, not a target or limit. Include the orchestrator when estimating total headcount. A small request may need no sub-agents; a broad request may need more or fewer than 20 depending on independent work, tool limits, cost, time, and review capacity. Stop adding agents when coordination and integration would outweigh the parallel progress.

## Configure Codex thread capacity and delegation depth

In Codex, set the subagent concurrency ceiling in `~/.codex/config.toml` for a user-wide default, or `<repo>/.codex/config.toml` for a trusted project:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 20
```

`max_concurrent_threads_per_session` caps concurrently open spawned-agent threads and excludes the primary thread. It sets capacity; it does not make Codex spawn that many agents. Thus `20` allows up to 20 subagent threads plus the Orchestrator thread. If the desired ceiling is 20 total units including the Orchestrator, set it to `19`. The older `agents.max_threads` key is an alias; use the current key and do not set both.

Current Codex configuration documentation does not list a `max_depth` setting. Enforce a two-edge delegation depth in the task instructions: **depth 0:** Orchestrator; **depth 1:** Supervisors spawned by the Orchestrator; **depth 2:** Workers spawned by Supervisors. Workers must not spawn agents. Include a direct instruction such as: “Use three reporting levels with maximum delegation depth 2: Orchestrator → Supervisors → Workers. Do not create another level. Stay within the configured concurrent-thread cap; 20 includes only subagent threads, so use 19 if the cap must include the Orchestrator.”

See [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and the [configuration reference](https://developers.openai.com/codex/config-reference/) for current key names and behavior.

## Roles and authority

With [Northstar](../northstar/SKILL.md#ownership-north-star--goals--tasks), use **orchestrator → direction, supervisor → one goal, worker → one task**. Map these responsibilities to existing project records; Northstar's directory layout is optional unless the repository requires it. Supervisors own coordination, integration and task acceptance; workers own scoped deliverables and handoffs. The orchestrator inspects the integrated result before goal acceptance; the supervisor records that decision. Human product decisions and consequential authorization remain with the user.

Critic and verifier are review assignments within this structure. Give reviewers direct access to original intent and actual artifacts, and let them report independently to the accepting supervisor or orchestrator. Assign repairs and recheck material findings; adding reviewers never transfers accountability for the goal.

### Orchestrator

- Owns the user's intent, scope, cross-goal interfaces and tradeoffs, team shape, and integrated result. Delegate local design choices with the task.
- Assigns bounded workstreams to supervisors and may assign bounded tasks directly to workers.
- Sets each delegate's allowed and forbidden paths or systems, acceptance criteria, verification, and side-effect limits.
- Resolves cross-workstream conflicts and approves scope changes only within the user's mandate. Checks whether external or irreversible actions are already authorized; obtains missing human authorization before execution. Delegation never expands the user's authorization or the tools' actual permissions.
- Integrates the work, independently inspects material changes and evidence, completes final verification, and reports the result and remaining limitations.

### Supervisors

- Own one workstream assigned by the orchestrator. They clarify its task boundaries, track dependencies, and may assign its bounded tasks to workers when the orchestrator has authorized that delegation.
- Keep worker write scopes disjoint, preserve shared changes, and review each handoff against its acceptance criteria.
- Decide implementation and internal design within the assigned goal. Coordinate shared interface changes with affected owners within their existing authority; bring unresolved cross-goal tradeoffs or changes beyond the mandate to the orchestrator with evidence and a recommendation.
- Do not grant permissions, expand the assigned workstream, authorize external side effects, or create another delegation layer.

### Workers

- Complete exactly one assigned task within its stated scope, using only the available permissions and authorized side effects.
- Do not spawn or delegate to other agents, change another worker's files or systems, broaden the objective, or commit, publish, deploy, or contact others unless explicitly authorized in the task and by the user.
- Choose implementation, internal refactoring, and checks within the task's bounds. If one part is blocked, report its precise dependency and continue independent assigned work. Return the artifact, evidence, remaining gaps, and next action.

Keep one accountable accepting role; workers may directly clarify interfaces with affected peers using authorized communication tools. Record material agreements once for the responsible supervisor. Peer agreement cannot expand authority or transfer write ownership by itself. Escalate unresolved conflicts, not every technical question; permission violations require immediate attention.

## Task brief and handoff

When assigning a managing role, fill the [orchestrator brief](templates/orchestrator.md) or [supervisor brief](templates/supervisor.md). Load only the needed role. Use these alongside this skill, not as additional management layers. The assigning agent supplies known facts rather than sending placeholders or asking the user to repeat them.

Give each delegate five things; link known context rather than copying it:

- **Result:** the usable outcome and relevant goal/current state.
- **Acceptance:** observable behavior and required evidence; let the worker choose ordinary checks.
- **Autonomy:** owned paths, local design choices, already-authorized actions and source, explicit limits, and applicable repository instructions.
- **Coordination:** dependencies/interface examples, affected owners, and changes requiring agreement or escalation.
- **Handoff:** accepting role, integration owner, scratch/report paths, existing evidence and recovery checkpoint when relevant.

Reports cover completed, partial, or blocked work; follow Northstar's [handoff practice](../northstar/SKILL.md#worker-reports-and-handoffs). Keep them proportional: artifact, actual verification, remaining gap. Preserve meaningful failure history. Supervisors inspect the work and record one task decision in the goal; link evidence rather than copying it into a second report. Workers propose changes to shared direction through its owner.

## Coordinate to a working result

1. **Schedule the next usable increment.** Identify the dependency that controls delivery and name its integration owner. Agree on shared inputs/outputs before splitting producers and consumers. Start only work that can proceed usefully now and be reviewed promptly; defer speculative parallel branches.
2. **React to evidence.** On a handoff, failure, dependency change, or bounded wait expiry, inspect the changed artifact or check result. Use completion notifications or bounded waits, not repeated unchanged status requests. While waiting, advance independent work. Reports and agent activity alone do not establish progress.
3. **Resolve at the lowest responsible level.** Workers own local implementation choices; supervisors resolve goal-level dependencies; orchestrators resolve cross-goal tradeoffs. Before escalating, inspect the problem and propose a remedy. Apply Northstar's [proportionate process](../northstar/SKILL.md#match-process-to-the-work) and [authorization rules](../northstar/SKILL.md#ask-only-for-decisions-the-user-owns). Remove temporary oversight once its specific failure is resolved.
4. **Intervene in stalled or overlapping work.** Identify whether the cause is implementation, missing evidence, a dependency, or tool/permission failure. Give one bounded correction with the failed criterion and next distinguishing check. After repeated failure, narrow, reassign, or take over using the existing recovery history. Stop or redirect duplicate work. Before transferring write ownership, confirm the old writer has stopped and inspect its diff; preserve useful partial work.
5. **Integrate and accept.** Verify the combined user workflow in the intended environment, not just each worker's isolated checks. Reuse applicable evidence and target interface gaps or changed behavior. A false completion claim returns the task for a concrete repair; do not weaken criteria or tests. Preserve the best verified baseline. When current acceptance passes, deliver; while authorized outcomes remain actionable, continue without requiring a 'continue' prompt.

Keep task owner, write scope, dependency/interface, next action, evidence, and any blocker in the existing goal; update on material changes, not every poll. At a context change, restore this state and existing authorization before dispatching more work. If nothing can advance, report the exact unmet criterion and unblock condition. Instructions cannot enforce runtime timeouts or guarantee future compliance.

## Documentation and repository hygiene

Read applicable `AGENTS.md` and task-relevant direction, goal, reports, and evaluations before editing. Follow Northstar's [repository and storage rules](../northstar/SKILL.md#keep-records-and-the-repository-small): scoped scratch, durable evidence, one shared-document editor, protected user work, and the shared 100 GB ceiling. Update existing records at material decisions and handoff, not each tool call. Inspect status/diffs before returning work; commit only when authorized. Shared documentation is memory, not a second implementation task.

## Failure, retries, and final integration

When using Northstar, apply its [delivery rules](../northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments) and [stall recovery procedure](../northstar/SKILL.md#recover-from-a-stall). Pass acceptance, deferred scope, artifacts, applicable evidence, and the current recovery checkpoint to delegates. Attempts and remaining investigation windows follow the unmet criterion across reassignment. Reviewers inspect evidence independently and rerun checks for a coverage gap or relevant change; a new agent is not a reason to repeat completed work or rejected approaches.

Apply the intervention step above when a delegate fails; stop reassigning the same failed approach without new evidence. Preserve specified tool/model/environment constraints. If delegation is unavailable, continue directly within authority or report the exact blocker. The accepting role owns the combined result: workers check their changes, supervisors inspect integration, and the orchestrator verifies goal coverage. Reuse valid checks across roles; rerun only for relevant change, contradictory evidence, or a coverage gap. Keep the original criteria and report remaining limitations.
