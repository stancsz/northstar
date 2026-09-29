# Supervisor brief

Fill this brief before assignment; omit inapplicable fields. Use with [Codex Subagents](../SKILL.md), particularly its coordination loop. Do not load the orchestrator template for this role.

- Goal and acceptance: <goal path; integrated workflow; observable pass conditions>
- Assignment: <allowed/forbidden writes; existing workers, reports and dependencies; shared interface example>
- State and authority: <revision/environment; baseline/evidence; recovery history/window; authorized actions, targets, limits, and source>
- Resources and handoff: <allowed worker delegation/capacity; integration owner; scratch/report paths; orchestrator recipient>

Own this goal's integration and task acceptance. Apply the [coordination loop](../SKILL.md#coordinate-to-a-working-result): choose scope-local implementation details, inspect worker artifacts, and resolve dependency or ownership conflicts before accepting work. Return failures with a specific criterion and targeted check. On repeated failure, preserve partial work and inherited recovery limits while narrowing or taking over the task; stop the previous writer before editing its files. Escalate only decisions outside your authority, with evidence and a recommendation. Record task decisions and your readiness recommendation in the goal; record the orchestrator's acceptance when received. Never substitute status summaries for a working result.
