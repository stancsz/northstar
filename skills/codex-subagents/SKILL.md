---
name: codex-subagents
description: Coordinate bounded agent work when delegation helps; define ownership, authority, handoffs, and integration.
---

# Codex subagents

Use this skill in other agents too; the Codex name is not a usage restriction. Follow the bundled [host adaptation guidance](../northstar/SKILL.md#use-with-other-agents).

Bundled Northstar skill. Contents: [team](#plan-the-team), [capability/cost](#allocate-capability-and-cost), [capacity](#configure-codex-thread-capacity-and-delegation-depth), [authority](#roles-and-authority), [briefs](#task-brief-and-handoff), [coordination](#coordinate-to-a-working-result), [records](#documentation-and-repository-hygiene), [recovery](#failure-retries-and-final-integration).

Use one owner by default. Follow Northstar's review threshold; do not spawn a reviewer for every sequential task. Delegate builders or reviewers only when required or when their value exceeds coordination, integration and token cost. Keep simple or tightly coupled work with the primary. When delegation is justified, use three reporting levels: one **Orchestrator**, zero or more **Supervisors**, and **Workers**. The number of supervisors and workers follows actual coordination needs, not a fixed headcount.

## Plan the team

1. Define the requested outcome, constraints, and completion evidence before assigning work.
2. Split the work into bounded deliverables that can proceed with minimal overlap. Each worker owns one task and one write scope; give each task its own acceptance criteria and verification method.
3. Create a supervisor only for a workstream whose dependencies or integration need a dedicated coordinator. The primary can directly manage a builder and independent reviewer; product and architecture can remain compatible functions of an existing agent. The hierarchy describes accountability, not mandatory staffed layers. Remove a temporary coordinator when its coordination need ends.
4. Apply Northstar's reviewer trigger. The commander accepts attributable, low-risk, reversible work from relevant evidence; use one nonauthor verdict when required. Add builders only for independent workstreams. Keep coupled changes with one owner; do not add an agent or approval chain per edit.

Use the [functional profiles](references/role-profiles.md) to cover product/outcomes, architecture/interfaces, implementation, independent QA, experience/taste, operations and expertise. Roles are functions, not seven standing agents. Name creators, reviewer, decision owner and artifact scope before dispatch; combine only compatible functions. Use the [agent-to-agent handoff practice](references/agent-handoffs.md) for peer coordination or remote agents.

## Allocate capability and cost

For shared workflow expectations, see the [Northstar delivery contract](../northstar/SKILL.md#delivery-contract).

Choose models by task difficulty, consequence and observed capability. Default to a capable lower-cost model for bounded execution; reserve stronger reasoning for direction, difficult integration, consequential decisions or a specific specialist gap. Respect the user's specified models and actual runtime availability. More capable models may be needed for some worker tasks; explain the evidence rather than silently making every worker the strongest model.

Keep provider routing and client setup owned by the commander. Verify any new or reconfigured route before dispatch, preserve explicit model/provider constraints and credential boundaries, and disclose unavailable routes rather than silently changing providers. Do not repeat an already-confirmed route smoke for each worker; pass its evidence in the brief. The Advisor's route remains independent and does not authorize implementation or acceptance.

For CLI workers, consult [the local CLI dispatch reference](references/cli-dispatch.md) when dispatching. One existing commander owns approvals; workers may make local implementation decisions within the assigned scope and acceptance criteria without a round trip. The commander records acceptance from evidence and records a nonauthor verdict when independent review applies; it cannot certify its own authored scope as independent.

Give workers enough context and authority to solve the task and challenge a flawed brief. Their handoff should identify a failed criterion and evidence of the gap. Improve an ambiguous brief, access or task boundary before treating every failure as a model problem. Escalate a genuine capability gap through [Codex Advisor](../codex-advisor/SKILL.md) when its setup fits, another authorized bounded expert consultation, or stronger worker assignment; preserve scope, rejected paths and all recovery counts. Unavailable model selection must be disclosed, not presented as a cheaper-model run.

For an effectiveness trial, record actual model/role, reasoning effort when exposed, task/criteria, accepted and rejected outcomes, wall time, attempts, interventions and expert use. Include commander, workers, consultation, review and rework in any total token/cost comparison. Use runtime usage and current applicable rates when available; label missing usage/cost unknown. No invented estimates presented as measured savings. Compare matched tasks with unchanged acceptance and comparable starting conditions before claiming efficiency. A single mixed-capability run supports feasibility only; all-strong-model success cannot validate economical execution. Manager takeover counts as rescue, not worker success.

For matched configuration/effectiveness experiments only, use the [comparison notes](references/cli-dispatch.md#configuration-comparisons). Do not load trial history for ordinary dispatch.

## Configure Codex thread capacity and delegation depth

Use the host's existing capacity. Change it only for an authorized task that needs more useful parallel work; a ceiling is not a staffing target. Host-specific settings are in the [CLI reference](references/cli-dispatch.md#optional-host-capacity). Never edit global settings merely to start a routine task.

## Roles and authority

As part of [Northstar](../northstar/SKILL.md#ownership-north-star--goals--tasks), use **orchestrator → direction, supervisor → one goal, worker → one task**. Map these responsibilities to existing project records; Northstar's directory layout is optional unless the repository requires it. Supervisors own coordination, integration and task acceptance; workers own scoped deliverables and handoffs. The orchestrator inspects the integrated result before goal acceptance; the supervisor records that decision. Product and consequential decisions covered by the owner's standing mandate belong to the commander; only retained or out-of-mandate decisions remain with the user. Carry granted subdelegation to supervisors and workers without requiring duplicate user approval.

When required, independent review stays outside authorship; a new context or stronger model does not erase conflict. A repairing reviewer cannot recheck that scope. Reuse one reviewer and evidence. If required review is unavailable, leave acceptance unverified; otherwise the commander accepts attributable work from direct evidence.

### Orchestrator

- Owns the user's intent, scope, cross-goal interfaces and tradeoffs, team shape, and integrated result. Delegate local design choices with the task.
- Assigns bounded workstreams to supervisors and may assign bounded tasks directly to workers.
- Sets each delegate's allowed and forbidden paths or systems, acceptance criteria, verification, and side-effect limits.
- Resolves cross-workstream conflicts and approves scope changes only within the user's mandate. Uses the standing grant for covered external or irreversible actions and delegates their bounded execution. Escalates only an actual missing authority or owner-retained decision, not consequence alone. Delegation never expands the user's authorization or the tools' actual permissions.
- Integrates the work, independently inspects material changes and evidence, completes final verification, and reports the result and remaining limitations.

### Supervisors

- Own one workstream assigned by the orchestrator. They clarify its task boundaries, track dependencies, and may assign its bounded tasks to workers when the orchestrator has authorized that delegation.
- Keep worker write scopes disjoint, preserve shared changes, and review each handoff against its acceptance criteria.
- Decide implementation and internal design within the assigned goal. Coordinate shared interface changes with affected owners within their existing authority; bring unresolved cross-goal tradeoffs or changes beyond the mandate to the orchestrator with evidence and a recommendation.
- May pass down the authority and bounded side effects inherited from the commander when subdelegation is granted. Do not expand that authority, resource envelope, assigned workstream or allowed delegation depth; no new human approval is needed for a covered assignment.

### Workers

- Complete exactly one assigned task within its stated scope, using only the available permissions and authorized side effects.
- Do not spawn or delegate to other agents, change another worker's files or systems, broaden the objective, or commit, publish, deploy, or contact others unless covered by the task's inherited user mandate and permitted delegation depth. The commander's valid subdelegation supplies that authority; do not demand a second personal grant from the user.
- Choose implementation, internal refactoring, and checks within the task's bounds. If one part is blocked, report its precise dependency and continue independent assigned work. Return the artifact, evidence, remaining gaps, and next action.

Keep one accountable accepting role; workers may directly clarify interfaces with affected peers using authorized communication tools. Record material agreements once for the responsible supervisor. Peer agreement cannot expand authority or transfer write ownership by itself. Route a material unresolved conflict to the single approval owner using the shortest useful [decision exchange](../northstar/references/operating-system.md#resolve-disagreement). Workers supply reasons for and against options; the chair decides within authority, preserves dissent and assigns the next check. Consult [expertise](../northstar/references/operating-system.md#bring-in-expertise) for material competence gaps. Permission violations require immediate attention.

## Task brief and handoff

Make assignments self-contained: state result and why it matters, first action, current context, acceptance/evidence (including the baseline failure for repairs), exact writable paths, task-owned scratch path when needed, authority/limits, applicable instructions and dependencies. Name the accepting role. Assign a durable report path only when the project or task requires one; otherwise the worker's concise final handoff carries the result. Links do not replace essential facts. The parent integrates and accepts; independent review applies only when required. Covered actions are pre-authorized; routine choices need no approval round trip.

The parent also supplies any already-verified route/client evidence, the next checkpoint and a firm handoff deadline. Workers do not repeat route setup or checks already established. Give the worker room to investigate directly relevant unknowns and choose methods within scope; when the brief is sufficient, avoid broad project/history rediscovery and proceed. Do not assign nested workers unless delegation is explicitly part of the task.

Codex CLI workers use their own native tools for assigned work; do not launch a nested CLI or ask the parent to perform it. Higher-priority host and repository instructions still apply. If required capability/context is missing, report the gap instead of switching tool class or widening scope. Handoffs name artifact, changes, checks, unmet criteria and next action; preserve failure history and recovery limits. The parent inspects and accepts; worker claims alone do not prove required independent review. See [local CLI dispatch](references/cli-dispatch.md) for host limits.

## Coordinate to a working result

1. **Schedule the next usable increment.** Identify the dependency that controls delivery and name its integration owner. Apply Northstar's [focus rule](../northstar/SKILL.md#focus-effort-before-expanding-work): give that dependency priority, assign supporting work for a concrete contribution, and leave capacity for integration and repair. Agree on shared inputs/outputs before splitting producers and consumers. Start only work that can proceed usefully now and be reviewed promptly; defer speculative parallel branches. Keep one writer per scope rather than concentrating agents on the same files.
2. **React to evidence.** On a handoff, failure, dependency change, or bounded wait expiry, inspect the changed artifact or check result. Use completion notifications or bounded waits, not repeated unchanged status requests. While waiting, advance independent work. Reports and agent activity alone do not establish progress.
3. **Resolve at the lowest responsible level.** Workers own local implementation choices; supervisors resolve goal-level dependencies; orchestrators resolve cross-goal tradeoffs. Before escalating to the commander, inspect the problem and propose a remedy. The commander decides unresolved in-mandate tradeoffs by useful value, full cost, urgency, downside and reversibility; do not forward them to the human by default. Apply Northstar's [proportionate process](../northstar/SKILL.md#match-process-to-the-work) and [authorization rules](../northstar/SKILL.md#ask-only-for-decisions-the-user-owns). Remove temporary oversight once its specific failure is resolved.
4. **Intervene in stalled or overlapping work.** Inspect the failed criterion and inherited recovery history first. If its recovery is not exhausted, give the next bounded correction; otherwise apply Northstar's [decision after exhausted recovery](../northstar/SKILL.md#decide-after-exhausted-recovery) immediately. Choose and execute a remedy within your mandate instead of forwarding status or giving a new worker fresh retries. Narrow the implementation, never the promised acceptance. Stop or redirect duplicate work. Before transferring write ownership, confirm the old writer has stopped and inspect its diff; preserve useful partial work.
5. **Integrate and accept.** Use one nonauthor verdict when required, inspecting the combined workflow and intended environment. The commander accepts directly inspectable, low-risk work. Return false completion claims for concrete repair; do not weaken criteria. Recheck material fixes, reuse evidence and deliver only when accepted. Continue authorized unmet work without asking whether to continue.
6. **Learn at the checkpoint.** Apply Northstar's [self-learning loop](../northstar/SKILL.md#learn-from-every-use). Workers contribute evidence of what worked/failed through existing handoffs; the accepting owner inspects it, resolves conflicting lessons, checks intent/acceptance drift and records one next-action decision. Carry applicable lessons and rejected paths into the next assignment. Record only decisions or lessons that change the next action; no extra retrospective is needed for routine success. The approval owner resolves material disagreement without resetting recovery history.

Keep task owner, write scope, dependency/interface, next action, evidence, and any blocker in the existing goal; separate observed facts from assumptions and update on material changes, not every poll. Give affected owners the same current evidence rather than filtered chains of status summaries. At a context change, restore this state and existing authorization before dispatching more work. If nothing can advance, report the exact unmet criterion and unblock condition. Instructions cannot enforce runtime timeouts or guarantee future compliance.

## Documentation and repository hygiene

Read applicable `AGENTS.md` and task-relevant direction, goal, reports, and evaluations before editing. Follow Northstar's [repository and storage rules](../northstar/SKILL.md#keep-records-and-the-repository-small): scoped scratch, durable evidence, one shared-document editor, protected user work, and the shared 100 GB ceiling. Update existing records at material decisions and handoff, not each tool call. Inspect status/diffs before returning work; commit only when authorized. Shared documentation is memory, not a second implementation task.

## Failure, retries, and final integration

When using Northstar, apply its [delivery rules](../northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments) and [stall recovery procedure](../northstar/SKILL.md#recover-from-a-stall). Pass acceptance, deferred scope, artifacts, applicable evidence, and the current recovery checkpoint to delegates. Attempts and remaining investigation windows follow the unmet criterion across reassignment. Reviewers inspect evidence independently and rerun checks for a coverage gap or relevant change; a new agent is not a reason to repeat completed work or rejected approaches.

Apply the intervention step above when a delegate fails; stop reassigning the same failed approach without new evidence. Preserve specified tool/model/environment constraints. If delegation is unavailable, continue directly within authority or report the exact blocker. The accepting role owns the combined result: workers check their changes, supervisors inspect integration, and the orchestrator verifies goal coverage. Reuse valid checks across roles; rerun only for relevant change, contradictory evidence, or a coverage gap. Keep the original criteria and report remaining limitations.
