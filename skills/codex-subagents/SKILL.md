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

When working with [Northstar](../northstar/SKILL.md#ownership-north-star--goals--tasks), use **orchestrator → North Star, supervisor → one goal, worker → one task**. A workstream below means the supervisor's assigned goal. The orchestrator reads and maintains `docs/northstar/`; the supervisor owns `docs/goal/<goal>/GOAL.md`, its goal index entry, task coordination, integration, and evaluation coverage; each worker owns scoped deliverables and `docs/reports/<goal>/<task>.md`. The supervisor accepts tasks and recommends goal readiness. The orchestrator inspects the integrated result before accepting the goal within the user's mandate; the supervisor records that decision. Human product decisions and consequential authorization remain with the user.

Critic and verifier are review assignments within this structure. Give reviewers direct access to original intent and actual artifacts, and let them report independently to the accepting supervisor or orchestrator. Assign repairs and recheck material findings; adding reviewers never transfers accountability for the goal.

### Orchestrator

- Owns the user's intent, scope, architecture, dependency decisions, team shape, and final result.
- Assigns bounded workstreams to supervisors and may assign bounded tasks directly to workers.
- Sets each delegate's allowed and forbidden paths or systems, acceptance criteria, verification, and side-effect limits.
- Resolves cross-workstream conflicts and approves scope changes only within the user's mandate. Checks whether external or irreversible actions are already authorized; obtains missing human authorization before execution. Delegation never expands the user's authorization or the tools' actual permissions.
- Integrates the work, independently inspects material changes and evidence, completes final verification, and reports the result and remaining limitations.

### Supervisors

- Own one workstream assigned by the orchestrator. They clarify its task boundaries, track dependencies, and may assign its bounded tasks to workers when the orchestrator has authorized that delegation.
- Keep worker write scopes disjoint, preserve shared changes, and review each handoff against its acceptance criteria.
- Report status, evidence, blockers, risks, and any needed decision to the orchestrator. They may recommend a scope or architecture change but cannot approve it themselves.
- Do not grant permissions, expand the assigned workstream, authorize external side effects, or create another delegation layer.

### Workers

- Complete exactly one assigned task within its stated scope, using only the available permissions and authorized side effects.
- Do not spawn or delegate to other agents, change another worker's files or systems, broaden the objective, or commit, publish, deploy, or contact others unless explicitly authorized in the task and by the user.
- Return a concise handoff with status, changed files or artifacts, verification evidence, assumptions, blockers, and next action. If blocked or the task no longer fits its scope, stop and report to the supervisor.

Authority flows down the hierarchy as bounded task instructions; findings and decisions flow up through the reporting chain. A worker reports to its assigned supervisor, and the supervisor reports to the orchestrator. When there is no supervisor, workers report directly to the orchestrator. Escalate urgent blockers or suspected permission violations immediately; do not use escalation to bypass a normal decision.

## Task brief and handoff

Give every delegate a brief that states:

- **Outcome:** one concrete deliverable and its acceptance criteria.
- **Scope:** allowed paths or systems, forbidden areas, and ownership boundaries.
- **Context:** only the information and dependencies needed for that deliverable.
- **Repository practices:** applicable root/nested `AGENTS.md`, relevant durable docs, a scoped `tmp/<task-or-agent>/` location, and responsibility for documentation updates.
- **Verification:** observable checks and the command or method to run, if applicable.
- **Side effects:** what may be changed or contacted; explicitly prohibit anything outside the user's authorization.
- **Handoff:** whom to report to, the assigned report path, and how to raise blockers. With Northstar, assign `docs/reports/<goal>/<task>.md` to the worker and link it from the supervisor's goal.

Workers report: **status; changed files/artifacts; verification and result; assumptions; blockers; next action.** Supervisors consolidate these into workstream status and distinguish verified evidence from claims or unresolved issues.

With Northstar, workers follow the [worker report practice](../northstar/SKILL.md#worker-reports-and-handoffs): write a durable Markdown report for completed, partial, or blocked work and send its link to the supervisor. Update that task's report after repairs. Supervisors read reports and inspect the artifacts, then record task acceptance or repair requests in `GOAL.md`. Workers propose shared direction/goal updates through their reports; they do not take over those documents. Give concurrent workers distinct report paths and coordinate goal-index edits through one owner.

## Documentation and repository hygiene

Every delegate reads the applicable `AGENTS.md` and relevant project docs before editing. When using Northstar, share links to direction in `docs/northstar/`, the assigned `docs/goal/<goal>/GOAL.md`, relevant prior worker reports in `docs/reports/`, and `docs/evals/`. Keep durable findings in the repository as well as the handoff; assign one owner for shared docs and send proposed updates to that owner.

Keep `docs/` limited to subdirectories. Use `docs/misc/` for documentation outside the direction, goal, worker report, and evaluation categories. Put indexes inside their category and update affected links.

Keep loose scripts, downloads, debug output, temporary screenshots, and experiments under the assigned `tmp/` directory. Follow and maintain appropriate ignore rules; do not hide useful source or documentation assets with broad extension patterns. Promote evidence needed for lasting conclusions to a documented location. Never remove or overwrite another agent's scratch work, source changes, or notes.

When using Northstar, the project has one shared 100 GB artifact limit across all agents, including ignored output, caches, downloads, and project-attributable copies. Report expected storage before large operations and actual growth afterward; include temporary extraction/build space. Coordinate with the orchestrator as total usage approaches 80 GB, and pause artifact creation that would exceed 100 GB. Do not move files elsewhere to evade accounting or remove another agent's data to free space.

Before returning work, inspect status and diffs for unintended files, update docs in your write scope, and report any integration or cleanup still needed. Commit only when authorized; use a focused, meaningful message describing the change. Supervisors reconcile goal records with worker reports and evaluations; the orchestrator updates direction when needed and inspects the combined result before delivery.

## Failure, retries, and final integration

If a delegate fails, times out, produces an incomplete result, or misses acceptance criteria, the supervisor or orchestrator identifies the specific gap and gives a bounded correction request. Retry only when there is a concrete correction path; keep attempts limited and proportional to task risk, cost, and time. After repeated failure, stop delegating that task and escalate it to the orchestrator with the failure history and any usable partial result. Do not silently switch tools, models, or execution environments when the user or task constraints specify one. If delegation is unavailable, the orchestrator may continue directly only when that respects the user's intent, permissions, and any tool constraints; otherwise report the blocker and request a decision.

The orchestrator remains accountable for the complete outcome. Before declaring completion, inspect the integrated artifacts and relevant diffs, resolve conflicts, and verify the original acceptance criteria across workstreams. Do not treat a supervisor's review or a worker's claim as final verification. Clearly report what was completed, what was verified, and any remaining limitation.
