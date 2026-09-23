# Routing rubric

Risk flags are OR conditions. Complexity flags need two positive signals to mark complexity high. Missing `risk` or `complexity` evidence becomes high/high `CHALLENGE`, because unknown is not evidence of safety.

Not every unknown belongs to the user. `ambiguous_goal`, `ambiguous_acceptance`, `implicit_context_or_value_judgment`, and `reasonable_expert_disagreement` signal a decision that may need the product owner. `novel_condition`, `multiple_dependencies`, and `hard_to_verify` are reasons for the AI to research, plan verification, or escalate supervision—not automatic reasons to interrupt the user.

Route high consequence with a clear product direction to `GUARD`; let the AI do bounded preparation and stop before the point of no return. Route unresolved product decisions to `COCREATE` at low consequence and `CHALLENGE` at high consequence. A `HUMAN_ONLY` veto always wins.

Do not treat model capability, a passing smoke test, or prior success as authority to increase autonomy. A request to expand permissions, scope, budget, data access, or external impact is an escalation event.
