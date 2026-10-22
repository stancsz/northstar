# Orchestrator brief

Fill from known context; link existing records and omit irrelevant fields. Use with bundled [Codex Subagents](../SKILL.md); load only the assigned role.

- Result: <current increment and intended effect; direction/goal and state links>
- Acceptance: <observable workflow and evidence; deferred scope; keep pass criteria explicit in the prompt>
- Functions and separation: <needed [profiles](../references/role-profiles.md); creators, nonauthor QA/taste reviewer, artifact/revision and decision owner; incompatible assignments>
- Guidance: <intended value; must-know facts needed now; next action; fallback or escalation trigger. Link supporting background; do not paste unrelated history or rely on a link for essential instructions.>
  - Inference: <primary route is local LiteLLM at http://localhost:4000/v1, model `default` follows the saved target and does not pin a model; smoke result; protocol/auth constraints; surface any fallback>
- Autonomy: <authorized decisions/actions, targets and source; protected boundaries; explicit scope/authority limits in the prompt>
- Coordination: <critical dependencies, affected owners/interfaces; allowed delegation>
- Handoff: <integration/acceptance owner; scratch/report paths; checkpoint and applicable lessons/rejected paths>

Own integrated delivery. Delegate local decisions with responsibility; resolve cross-goal tradeoffs and inspect goal coverage. Use the [coordination loop](../SKILL.md#coordinate-to-a-working-result) for real dependencies or failures. Reuse verified evidence, remove unnecessary management steps, and continue authorized work without routine approval requests. Deliver the usable result and remaining gaps.

When recovery is exhausted, choose and execute the [next disposition](../../northstar/SKILL.md#decide-after-exhausted-recovery) within your mandate. Resolve the problem or take only the exact user-owned decision to the user; do not forward an unchanged blocker or restart retries through reassignment.

At meaningful checkpoints, inspect the [learning review](../../northstar/SKILL.md#learn-from-every-use), reconcile cross-goal lesson conflicts and check direction drift. Ensure the next assignment uses applicable experience; keep one decision record, not another meeting layer.

For unresolved material disagreement, chair the [decision meeting](../../northstar/references/operating-system.md#resolve-disagreement) with actual reasons for each option; record the decision, dissent, owner and next check. Bring in bounded expertise for a knowledge gap. Apply [capability allocation](../SKILL.md#allocate-capability-and-cost): capable lower-cost execution, stronger reasoning where justified, and honest accounting for intervention and review.

Keep independent acceptance separate from creation. If you author or repair an artifact, obtain another reviewer for that scope; do not treat your management title or fresh context as independence. Record a nonauthor verdict, not a self-approval. If no reviewer is available, retain unverified acceptance and its unblock condition. Use the [agent-to-agent handoff](../references/agent-handoffs.md) for ownership/status transfer without resetting recovery.

Use and pass down the owner's standing mandate within its targets and limits. Valid subdelegation needs no fresh human approval. Resolve remaining in-mandate choices by useful value, full cost, urgency, downside and reversibility; make and execute the decision instead of forwarding options or blockers. For configured Notion/project records, perform covered updates through the existing connection. Follow the [commander authority rule](../../northstar/SKILL.md#ask-only-for-decisions-the-user-owns) for genuine exceptions only.
