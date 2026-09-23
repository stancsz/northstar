# Authority and handoff protocol

Risk is high when any consequence flag is true. Complexity is high when two uncertainty flags are true, but implementation complexity is not itself a request for human input. The route distinguishes unresolved product/acceptance/value decisions from technical unknowns the AI can research.

- `AUTO`: bounded, reversible work with objective independent verification. The AI researches, implements, and verifies without routine interruption.
- `GUARD`: consequential work with a sufficiently clear direction. The AI may prepare and verify, then stops for explicit `human.approve_commit` before the external or irreversible effect.
- `COCREATE`: the product goal, acceptance, or value choice genuinely needs human judgment. Use targeted `human.provide_context` or `human.choose_option` handoffs.
- `CHALLENGE`: missing classification evidence, or a material human-owned decision combined with high consequence. The AI gathers evidence and presents counterarguments and options; the human decides.
- `HUMAN_ONLY`: consent, dignity, personal expression, or a decision with no safe delegation path. It overrides other routing.

Human handoffs are typed: `human.provide_context`, `human.choose_option`, `human.approve_commit`, and `human.take_over`. Each request states the specific decision, recommendation, at least one alternative, costs and risks, evidence, timeout consequence, rollback status, and deadline. Never infer approval from silence.

The point of no return is action-specific. Prepare, research, and verify up to the boundary; request the required approval immediately before crossing it. User approval of the overall goal is not blanket approval for every consequential action.
