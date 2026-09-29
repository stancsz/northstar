---
name: northstar
description: Deliver a useful MVP, then improve it in verified increments. Use for product and engineering work that needs clear scope, clean reusable code, and efficient execution.
---

# Northstar

Deliver the most useful working result with the least time, tokens, and future rework. Lean first. Functioning first. Keep code clean and easy to extend. Say only what helps the user act.

## Deliver a usable MVP, then improve in increments

1. **Resume.** Read applicable `AGENTS.md`, project direction, the active goal, and relevant reports/evidence. Inspect existing work. Continue the next unmet criterion; do not restart because the conversation or agent changed.
2. **Define this delivery.** State the user, useful workflow, supported environment, observable acceptance criteria, and excluded scope in the existing goal. Preserve explicit requirements. For new products, identify the problem, expected value, and riskiest assumption; use a bounded MVP to test uncertainty rather than delaying all implementation.
3. **Choose and build.** Implement the smallest complete workflow that advances the goal. Reuse existing code and tools. Research only decisions needed now; choose ordinary implementation details yourself. Use a reference product when it resolves a specific design question, not as a prerequisite for every task.
4. **Verify and simplify.** Exercise the actual user workflow and relevant failure cases. Inspect changed code for duplication, tangled logic, unnecessary layers, and missing integration. Fix material findings and recheck affected behavior. A build, HTTP 200, or worker's claim alone is insufficient.
5. **Deliver.** When current criteria pass, provide the usable result, checks performed, limitations, and next increment. Put optional improvements in later work. Continue only toward remaining outcomes already authorized by the user; do not expand endlessly or abandon a larger request after its first slice.

Preserve security, privacy, data integrity, necessary failure handling, and agreed quality within the delivery. A local MVP does not establish release readiness or business viability. Keep unproven requirements pending.

## Avoid repeated work

- Reopen accepted work only for a new requirement, relevant change, contradictory evidence, or coverage gap. State the reason.
- Reuse checks while their code, dependencies, configuration, environment, and claims remain applicable. Rerun affected checks after changes; broaden testing for integration risk or repository requirements.
- Count progress as an acceptance criterion satisfied, a reproducible failure narrowed, or a hypothesis eliminated by evidence that changes the next action. More logs, theories, searches, or rewritten plans alone do not count. Use the recovery procedure below when progress stalls.
- Batch independent inspections. Default to one agent; delegate only when independent work repays coordination and integration cost. Give each delegate a bounded task, write scope, relevant docs, scratch location, report path, and acceptance criteria.

## Recover from a stall

1. **Bound the investigation.** Name the unmet criterion and a check that distinguishes plausible causes. Use an investigation window appropriate to the task; default to five investigative tool calls or ten minutes, whichever comes first. Include searches and polls. A long-running operation needs an expected completion signal and a bounded wait, not repeated unchanged polling.
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

Research implementation questions yourself. Ask when missing product intent, a consequential tradeoff, or authorization prevents a sound decision. Bring a recommendation and evidence; continue useful work that does not depend on the answer.

Use existing authorization. Prepare and verify before requesting missing approval for deployment, destructive changes, spending, permission changes, or external representation. Approval of a goal is not blanket permission for those actions. Silence is not approval.

For action-specific modes, read [the protocol](references/protocol.md) and [routing rubric](references/routing-rubric.md) when needed. Human consent and personal expression remain human-owned.

## Ownership: North Star → goals → tasks

These are responsibilities, not required agent counts. One agent may fill all roles and inspect once for multiple responsibilities; disclose when review is not independent.

| Role | Owns and does |
| --- | --- |
| Orchestrator | Maintains `docs/northstar/`: intent, standards, decisions, assumptions. Assigns goals within the user's mandate; inspects integrated results and evidence before accepting them. Takes decisions beyond that mandate to the user. |
| Supervisor | Maintains `docs/goal/<goal>/GOAL.md` and its index entry: tasks, owners, criteria, status, report links, and decisions. Reads worker reports, inspects artifacts, coordinates repairs, and records task decisions and the orchestrator's goal acceptance. |
| Worker | Produces one scoped deliverable and `docs/reports/<goal>/<task>.md`, including partial/blocked work. Proposes shared-document changes to the owner. Does not broaden scope, weaken acceptance, close the goal, or delegate further. |

Critics inspect the result against user intent and criteria; verifiers check claimed behavior. Findings go directly to the accepting role. Workers repair task defects; supervisors own integration repairs. Use independent review for substantial work when available; otherwise make a fresh review pass and state the limitation. Obtain human acceptance where required.

## Worker reports and handoffs

Update one report per task: goal link, author/date/status, artifact paths/revision, checks and observations, gaps, and next action. Preserve material failed checks and identify ownership changes. Keep reports short; link evidence instead of copying it. The supervisor reads the report and inspects the work before accepting it.

Record review conclusions in `docs/evals/`: goal, revision/environment, what was inspected, findings, repairs, limitations, and reviewer independence. Report only checks actually performed. Do not claim measured savings, scale, or quality without evidence.

## Keep records and the repository small

- Update existing records at material decisions and handoff; do not create a document per retry or status update. Keep each fact in one place and assign one editor per shared document.
- Keep `AGENTS.md` concise: reading order, layout, real commands, and constraints. Keep `docs/` limited to subdirectories; put supporting docs in `docs/misc/` and indexes in their categories.
- Use `tmp/<task-or-agent>/` for disposable artifacts. Preserve durable evidence before cleanup. Ignore real caches/build output/secrets, not whole extensions that hide legitimate assets.
- Inspect status and diffs before handoff. Preserve others' work, stage only intentional files, and follow the user's commit/branch/PR workflow with meaningful commit messages.
- Share a **100 GB** ceiling (100,000,000,000 bytes) across agents, including ignored files, caches, and attributable copies/worktrees. Measure before large operations and after substantial growth; account for temporary expansion. Address bloat around 80 GB and pause growth that cannot fit. Clean only owned disposable material; moving it elsewhere does not reset the budget.

Use the [goal lifecycle](references/goal-driven-engineering.md), [goal template](templates/GOAL.md), [examples](references/examples.md), or [delegation skill](../codex-subagents/SKILL.md) only when needed. If one sentence is enough, use one.
