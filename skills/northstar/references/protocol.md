# Authority and handoff protocol

Choose the working mode from the actual consequences, unresolved decisions, and existing authorization. Implementation complexity calls for investigation; product direction and value tradeoffs may require the owner. Record only the boundaries useful to the work in the goal: scope, permissions, data access, recovery, and relevant cost or retry limits. Delegation may narrow these boundaries but cannot expand them.

Use the [role ownership](../SKILL.md#ownership-north-star--goals--tasks) and [worker handoff](../SKILL.md#worker-reports-and-handoffs) practices for agent coordination. The orchestrator owns and uses `docs/northstar/`; supervisors own and use their `docs/goal/<goal>/GOAL.md`; workers produce deliverables and write `docs/reports/<goal>/<task>.md`. Supervisors inspect those reports and artifacts, record task decisions in the goal, and recommend goal readiness to the orchestrator. Modes govern the authority of each action across all three roles; they do not replace document ownership or human authorization.

- `AUTO`: bounded, reversible work with objective independent verification. The AI researches, implements, and verifies without routine interruption.
- `GUARD`: consequential work with a sufficiently clear direction. The AI prepares and verifies, and obtains explicit approval for the external or irreversible action within its scope.
- `COCREATE`: the product goal, acceptance, or value choice genuinely needs human judgment. Ask for the specific missing context or decision.
- `CHALLENGE`: material uncertainty or a human-owned decision combined with high consequence. The AI gathers evidence and presents counterarguments and options; the human decides.
- `HUMAN_ONLY`: consent, dignity, personal expression, or a decision with no safe delegation path. It overrides other routing.

At a human handoff, say whether you need missing context, a product choice, approval for a consequential action, or human intervention. Explain the decision, recommendation, alternatives, supporting evidence, impact, and recovery where relevant. Include a deadline only when one actually matters. Keep the request proportional and never infer approval from silence.

The point of no return is action-specific. Prepare, research, and verify up to the boundary. Use authorization already given for that action and scope; request a decision when authorization is missing or the consequences materially change. Approval of an overall goal does not automatically authorize every external action.
