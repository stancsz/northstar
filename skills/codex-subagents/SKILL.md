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

For skill-effectiveness trials and total-effort claims, use the [compact QA receipt](../codex-qa/references/skill-effectiveness.md). For matched CLI configuration comparisons, use the [comparison notes](references/cli-dispatch.md#configuration-comparisons). Do not load trial history for ordinary dispatch.

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

1. **Split only useful independent work.** Name the integration owner, shared interfaces and one writer per scope. Start supporting assignments only when each has a concrete result and can proceed without unsafe overlap.
2. **Follow evidence, not status.** At handoff or bounded wait, inspect the artifact and actual check result; use completion signals instead of repeated polling and advance independent work while waiting.
3. **Resolve and recover at the right level.** Workers own local choices, supervisors resolve workstream dependencies, and the commander resolves cross-workstream tradeoffs. Carry the same recovery history, stop duplicate work, and confirm the old writer stopped before transferring scope.
4. **Integrate against full acceptance.** Inspect the combined workflow, use one nonauthor verdict only when Northstar's review trigger applies, repair material failures without narrowing the outcome, and record lessons only when they change the next action.

Maintain one current checkpoint in the existing task/goal: owner, scope, interfaces, next action, evidence, blocker and inherited authority. Update on material changes or handoffs, not every poll; restore that state before dispatch after a context change. Skill text cannot enforce runtime timeouts.

## Documentation and repository hygiene

Read applicable `AGENTS.md` and task-relevant direction, goal, reports, and evaluations before editing. Follow Northstar's [repository and storage rules](../northstar/SKILL.md#keep-records-and-the-repository-small): scoped scratch, durable evidence, one shared-document editor and protected user work; follow repository-specific storage limits. Update existing records at material decisions and handoff, not each tool call. Inspect status/diffs before returning work; commit only when authorized. Shared documentation is memory, not a second implementation task.

## Failure, retries, and final integration

Delegation never changes acceptance or resets recovery history. If delegation fails or is unavailable, continue directly within the same authority and scope, or report the exact blocker. For full delivery and exhausted-recovery rules, use Northstar's [delivery loop](../northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments) and [stall recovery](../northstar/SKILL.md#recover-from-a-stall).
