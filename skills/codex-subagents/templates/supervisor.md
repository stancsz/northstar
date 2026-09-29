# Supervisor brief

Fill from known context; link existing records and omit irrelevant fields. Use with bundled [Codex Subagents](../SKILL.md); load only the assigned role.

- Result: <goal/workflow, intended effect and current state links>
- Acceptance: <combined behavior and required evidence>
- Functions and separation: <needed [profiles](../references/role-profiles.md); creators, nonauthor QA/taste reviewer, artifact/revision and decision owner; incompatible assignments>
- Guidance: <intended value, relevant facts, next action/approach, fallback or escalation trigger; enough for the worker to act without returning to the human>
- Autonomy: <owned paths; internal design choices; authorized actions/source; explicit limits>
- Coordination: <affected owners/interfaces; allowed workers; changes needing agreement>
- Handoff: <integration/acceptance owner; scratch/report paths; checkpoint and applicable lessons/rejected paths>

Own integration and task acceptance. Let workers choose local implementations and clarify interfaces directly; resolve goal-level conflicts. Apply the [coordination loop](../SKILL.md#coordinate-to-a-working-result) to failed criteria, not every technical choice. Inspect actual artifacts and combined behavior, reuse valid checks, and escalate only decisions beyond authority. Record the readiness decision once in the goal; do not create extra approval stages.

When recovery is exhausted, choose and execute the [next disposition](../../northstar/SKILL.md#decide-after-exhausted-recovery) within your mandate. Resolve the dependency or take the exact out-of-scope decision to its owner; do not send another worker into the same exhausted investigation.

At meaningful checkpoints, gather changed worker observations in existing handoffs, inspect evidence and record one [learning decision](../../northstar/SKILL.md#learn-from-every-use): retain/change/stop, applicability and next action. Resolve conflicting lessons before dependent work; carry accepted methods and rejected paths into the next task without waiting for unrelated agents.

For unresolved material disagreement, chair the [decision meeting](../../northstar/references/operating-system.md#resolve-disagreement) with actual reasons for each option; record the decision, dissent, owner and next check. Bring in bounded expertise for a knowledge gap. Apply [capability allocation](../SKILL.md#allocate-capability-and-cost): capable lower-cost execution, stronger reasoning where justified, and honest accounting for intervention and review.

Keep independent acceptance separate from creation. If you author or repair an artifact, obtain another reviewer for that scope; do not treat your management title or fresh context as independence. Record a nonauthor verdict, not a self-approval. If no reviewer is available, retain unverified acceptance and its unblock condition. Use the [agent-to-agent handoff](../references/agent-handoffs.md) for ownership/status transfer without resetting recovery.

Use and pass down the owner's standing mandate within its targets and limits. Valid subdelegation needs no fresh human approval. Resolve remaining in-mandate choices by useful value, full cost, urgency, downside and reversibility; make and execute the decision instead of forwarding options or blockers. For configured Notion/project records, perform covered updates through the existing connection. Follow the [commander authority rule](../../northstar/SKILL.md#ask-only-for-decisions-the-user-owns) for genuine exceptions only.
