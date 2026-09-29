---
name: northstar
description: Deliver a useful MVP, then improve it in verified increments. Use for product and engineering work that needs clear scope, clean reusable code, and efficient execution.
---

# Northstar

Deliver the most useful working result with the least time, tokens, and future rework. Lean first. Functioning first. Keep code clean and easy to extend. Say only what helps the user act.

Default to direct implementation and relevant verification. Maintain continuation state when work spans sessions or handoffs; use stall recovery when progress stops. Load delegation only for worthwhile independent workstreams, and QA for the changed workflow, visible artifact, or material delivery risk. Choose this yourself; do not ask the user to select a process mode. Explicit task and repository requirements still apply.

## Deliver a usable MVP, then improve in increments

1. **Resume.** Read applicable `AGENTS.md` and relevant existing task records/evidence. Inspect existing work. Continue the next unmet criterion; do not restart because the conversation or agent changed, or create missing Northstar folders just to begin.
2. **Define this delivery.** Make the useful workflow, environment, acceptance and excluded scope clear in the existing task record; the request and handoff may suffice for a small one-turn change. Preserve explicit requirements. For new products, identify the problem, expected value, and riskiest assumption; use a bounded MVP to test uncertainty rather than delaying all implementation.
3. **Choose and build.** Implement the smallest complete workflow that advances the goal. Reuse existing code and tools. Research only decisions needed now; choose ordinary implementation details yourself. Use a reference product when it resolves a specific design question, not as a prerequisite for every task.
4. **Verify and simplify.** Exercise the actual user workflow and relevant failure cases. Inspect changed code for duplication, tangled logic, unnecessary layers, and missing integration. Fix material findings and recheck affected behavior. A build, HTTP 200, or worker's claim alone is insufficient.
5. **Deliver.** When current criteria pass, provide the usable result, checks performed, limitations, and next increment. Put optional improvements in later work. Continue only toward remaining outcomes already authorized by the user; do not expand endlessly or abandon a larger request after its first slice.

Preserve security, privacy, data integrity, necessary failure handling, and agreed quality within the delivery. A local MVP does not establish release readiness or business viability. Keep unproven requirements pending.

For changed user workflows or visible artifacts, use [Northstar QA](../northstar-qa/SKILL.md) to set a brief quality plan and inspect functional, rendered visual, adversarial, and structural evidence before handoff. If the companion is unavailable, perform those relevant checks directly and disclose gaps; missing QA tooling never turns an unverified result into a pass.

## Match process to the work

Protect the user's outcome, acceptance, data, explicit budgets, authorization, and active ownership boundaries. Within those boundaries, choose implementation, internal structure, debugging order, and verification methods without permission. Coordinate shared interface changes with affected owners; escalate unresolved cross-goal tradeoffs or missing user authority.

Use the least process that supports a reliable handoff. A small local change needs implementation, relevant checks, and a short result; reuse the active goal instead of creating another project lifecycle. Add coordination for actual dependencies and independent review for substantial or consequential work. Tighten oversight around an observed failure, then remove the extra checks when it is resolved. Explicit user/repository requirements still apply.

Templates, default investigation windows, and review timing are guidance. Adapt them when evidence warrants and briefly record material deviations; they cannot waive requirements, restart exhausted recovery, or override explicit limits. One agent filling several roles makes one acceptance decision; multiple roles reuse applicable evidence instead of repeating the same checks.

## Avoid repeated work

- Reopen accepted work only for a new requirement, relevant change, contradictory evidence, or coverage gap. State the reason.
- Reuse checks while their code, dependencies, configuration, environment, and claims remain applicable. Rerun affected checks after changes; broaden testing for integration risk or repository requirements.
- Count progress as an acceptance criterion satisfied, a reproducible failure narrowed, or a hypothesis eliminated by evidence that changes the next action. More logs, theories, searches, or rewritten plans alone do not count. Use the recovery procedure below when progress stalls.
- Batch independent inspections. Default to one agent; delegate only when independent work repays coordination and integration cost. Give each delegate a bounded task, write scope, relevant docs, scratch location, report path, and acceptance criteria.

## Recover from a stall

1. **Bound the investigation.** Name the unmet criterion and a check that distinguishes plausible causes. Default to reassessing after five investigative tool calls or ten minutes, whichever comes first, including searches and polls. This is a decision checkpoint, not an automatic approval request: evidence-backed progress may justify another bounded step; no progress triggers recovery below. Respect explicit limits. A long-running operation needs an expected completion signal and a bounded wait.
2. **Preserve state.** Identify the last verified behavior and preserve the current diff before experimenting; never reset others' changes. Test one causal change at a time. Remove only your disproven experimental change, retaining useful work and evidence.
3. **Trigger recovery.** After two attempts without progress, or at the window boundary, compare the result with the criterion. Count against that same criterion across approaches, agents, and context resets. Renaming the task or producing incidental information does not reset the count. If unfinished, choose the next bounded check only when the evidence justifies it; otherwise enter recovery.
4. **Isolate.** Stop speculative edits. Reproduce the smallest failing case, inspect the failure at its source, and test one distinguishing hypothesis or simpler implementation within one recovery window. Do not repeat a rejected approach without evidence that invalidates its earlier result.
5. **Exit deliberately.** Resume implementation when evidence identifies a viable next step. If recovery still cannot advance the criterion, checkpoint it as blocked with the precise missing evidence, dependency, or intervention; continue independent authorized work. Do not claim completion, invent an external cause, or reenter the same blocked investigation without a changed condition.

Keep a short checkpoint in the existing goal (workers use their task report): **criterion; verified state and current diff; attempts/results and ruled-out paths; remaining window; next distinguishing check or unblock condition**. Update it at the window boundary, before a handoff/context switch, and when a finding changes the next action. On continuation, verify the checkpoint against current files, then resume it. Do not create a separate log for every tool call.

Only a failed current criterion or a concrete material risk justifies blocking delivery for cleanup or redesign. Preference-driven refactoring goes into later work. This procedure guides the agent; it is not an external watchdog that can enforce execution limits.

## Excellent design with minimal machinery

- **Reuse first:** inspect existing implementations and supported library capabilities. Keep shared business rules in one place. Extract shared behavior, not merely similar syntax.
- **Keep flow obvious:** use focused functions/modules, explicit inputs/outputs, clear names, and directional dependencies. Avoid hidden shared state, circular dependencies, tangled conditionals, and unrelated responsibilities.
- **Fix causes:** do not stack special-case patches. Remove code made obsolete by this change; preserve unrelated work.
- **Keep extension paths open:** consider data ownership, permissions, public interfaces, and provider lock-in before committing. Inspect how one or two credible next features would fit. Use small replaceable boundaries; record material migration costs. Do not prebuild unused frameworks or backends.
- **Subtract:** remove unnecessary code, dependencies, indirection, and duplication from the changed scope. Prefer readable direct solutions over clever one-liners. Comments explain non-obvious reasons.

Judge quality by observable behavior: the intended user completes the workflow, failures are handled, code is understandable, and credible extensions have a clear place to fit. Do not invent percentage scores or require competitor parity by default. If the user requests a comparison, name the reference, tasks, and measurements; report observed results and unknowns.

## Ask only for decisions the user owns

Resolve ordinary implementation choices yourself. Before asking, check the current request, prior decisions, and existing authorization. Do not ask whether to start or continue work already requested. Ask only when missing product intent, a consequential tradeoff, or authorization prevents a sound decision; state the exact missing decision, its impact, and your recommendation. Continue useful work that does not depend on the answer.

Use existing authorization. Prepare and verify before requesting missing approval for deployment, destructive changes, spending, permission changes, or external representation. Approval of a goal is not blanket permission for those actions. Silence is not approval.

Carry the authorized actions, targets, limits, and their source through checkpoints and delegation; a new agent or context window does not invalidate them. Distinguish a missing user decision from a tool-enforced permission block. For the latter, name the rejected action and restriction; use an allowed equivalent when available, without bypassing controls or asking for broader access by default.

For action-specific modes, read [the protocol](references/protocol.md) and [routing rubric](references/routing-rubric.md) when needed. Human consent and personal expression remain human-owned.

## Ownership: North Star → goals → tasks

These are responsibilities, not required agent counts. One agent may fill all roles and inspect once for multiple responsibilities; disclose when review is not independent.

Use the project's existing issues, task files, plans and review records as the source of truth. In this skill, "goal", "report" and "evaluation" describe information and ownership, not mandatory files. Add only missing information; use a durable record for continuation/handoff. The `docs/northstar/`, `docs/goal/`, `docs/reports/` and `docs/evals/` layout is an optional fallback where no convention exists. Do not duplicate records or create parallel indexes. Follow explicit repository paths when required; writing to an external tracker still needs appropriate authorization.

| Role | Owns and does |
| --- | --- |
| Orchestrator | Owns intent, standards, decisions and assumptions in existing direction records. Assigns goals within the user's mandate; inspects integrated results before accepting them. Takes decisions beyond that mandate to the user. |
| Supervisor | Maintains the assigned goal's tasks, owners, criteria, status, evidence links and decisions. Reads handoffs, inspects artifacts, coordinates repairs, and records task decisions and final acceptance. |
| Worker | Produces one scoped deliverable and a concise handoff in the assigned record, including partial/blocked work. Proposes shared-record changes to the owner. Does not broaden scope, weaken acceptance, close the goal, or delegate further. |

Critics inspect the result against user intent and criteria; verifiers check claimed behavior. Findings go directly to the accepting role. Workers repair task defects; supervisors own integration repairs. Use independent review for substantial work when available; otherwise make a fresh review pass and state the limitation. Obtain human acceptance where required.

For delegated work, use the [coordination loop](../codex-subagents/SKILL.md#coordinate-to-a-working-result) and load only the relevant [orchestrator](../codex-subagents/templates/orchestrator.md) or [supervisor](../codex-subagents/templates/supervisor.md) brief. Managers resolve dependencies and inspect integrated behavior; relaying status alone is not progress.

## Worker reports and handoffs

For a delegated task, update one report: goal link, author/date/status, artifact paths/revision, checks and observations, gaps, and next action. Preserve material failed checks and identify ownership changes. A few lines suffice for small work. The supervisor reads the report and inspects the work before accepting it. For a single-agent change, use one entry in the existing goal for handoff and acceptance unless the repository requires a separate report. Link evidence; do not duplicate it across role records.

Record review conclusions in the existing review/task record: goal, revision/environment, observations, repairs, limitations, and reviewer independence. Report only checks actually performed. Do not claim measured savings, scale, or quality without evidence.

## Keep records and the repository small

- Update existing records at material decisions and handoff; do not create a document per retry or status update. Keep each fact in one place and assign one editor per shared document.
- Keep `AGENTS.md` concise: reading order, actual layout, commands, and constraints. Preserve the project's documentation convention; create structure only when needed. In the optional Northstar layout, keep category indexes and supporting docs within their subdirectories.
- Use `tmp/<task-or-agent>/` for disposable artifacts. Preserve durable evidence before cleanup. Ignore real caches/build output/secrets, not whole extensions that hide legitimate assets.
- Inspect status and diffs before handoff. Preserve others' work, stage only intentional files, and follow the user's commit/branch/PR workflow with meaningful commit messages.
- Share a **100 GB** ceiling (100,000,000,000 bytes) across agents, including ignored files, caches, and attributable copies/worktrees. Measure before large operations and after substantial growth; account for temporary expansion. Address bloat around 80 GB and pause growth that cannot fit. Clean only owned disposable material; moving it elsewhere does not reset the budget.

Use the [goal lifecycle](references/goal-driven-engineering.md), [goal template](templates/GOAL.md), [examples](references/examples.md), or [delegation skill](../codex-subagents/SKILL.md) only when needed. If one sentence is enough, use one.
