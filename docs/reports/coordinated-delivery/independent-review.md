# Coordinated delivery: independent documentation review

- Goal: [Coordinated delivery](../../goal/coordinated-delivery/GOAL.md)
- Author/date: independent review agent, 2026-09-29
- Status: complete; no material actionable findings in this bounded pass
- Reviewed revision: working tree based on `5f0f860ec40541e3f6c5b5c1e95484719ed89b07`; includes uncommitted coordinated-delivery instructions and templates

## Scope and observations

Read repository instructions, direction, goal, report/evaluation indexes, [Northstar](../../../skills/northstar/SKILL.md), [Codex Subagents](../../../skills/codex-subagents/SKILL.md), and both [orchestrator](../../../skills/codex-subagents/templates/orchestrator.md) and [supervisor](../../../skills/codex-subagents/templates/supervisor.md) briefs. Inspected the skill diff. Considered these concrete scenarios against the written instructions:

- **An authorized repair resumes under a new supervisor.** Northstar preserves actions, targets, limits, and authorization source; task briefs carry these facts explicitly. The supervisor may resolve local implementation choices without asking the user to authorize the same repair again.
- **A tool rejects an otherwise authorized action.** The decision guidance separates a user decision from a platform restriction, requires identifying the rejected action, and permits an allowed equivalent without bypassing controls. Existing authorization does not enlarge tool permissions.
- **Two inherited assignments overlap.** Coordination requires stopping or redirecting duplicate work, confirming the former writer has stopped, inspecting its diff, and preserving useful partial work before transferring ownership. The supervisor remains within its assigned goal; cross-goal conflicts belong to the orchestrator.
- **A worker claims completion while its consumer still fails.** Supervisors inspect artifacts and the combined workflow; a false claim receives a specific repair rather than weaker criteria. The orchestrator must inspect integrated evidence before goal acceptance.
- **A failing task is reassigned or resumed after context loss.** Recovery history and remaining investigation windows follow the unmet criterion. Reassignment does not restart the retry allowance; an unchanged blocked condition does not justify another investigation.

Both templates ask for acceptance, current state, authority, integration ownership, and handoff. Their instructions tell the assigning agent to supply known facts and omit inapplicable fields, making them usable without an additional approval or reporting layer. Role briefs link to the coordination loop rather than duplicating its procedure.

## Limits and handoff

This was an independent documentation review, not an execution trial or evidence of long-session reliability. No tools, agents, or fixtures were exercised under the proposed guidance. Configuration claims, global link validation, installed copies, and trial outcomes were outside this assigned review. I did not implement or edit the reviewed instructions.

Only this report was written. The primary agent owns goal/index updates, inspection of execution-trial evidence, and final acceptance. No repair is requested by this review; continue those checks before accepting the goal.
