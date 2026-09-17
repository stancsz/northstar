# Protocol

Risk is high when any listed consequence flag is true. Complexity is high when two uncertainty flags are true. `HUMAN_ONLY` overrides the matrix. An AI may ask for a stricter mode, never relax one.

`AUTO` needs bounded scope, objective independent verification, reversibility, and no external irreversible effect. `GUARD` lets AI prepare and execute but stops at `human.approve_commit`. `COCREATE` preserves human acceptance and final taste. `CHALLENGE` makes the human decision-maker while AI supplies counterevidence, alternatives, failure scenarios, and unresolved dissent.

Human handoffs are typed: `human.provide_context`, `human.choose_option`, `human.approve_commit`, and `human.take_over`. Each request states the decision, recommendation, at least one alternative, costs and risks, evidence, timeout consequence, rollback status, and deadline.
