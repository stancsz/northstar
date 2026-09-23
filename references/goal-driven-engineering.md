# Goal-driven engineering in Northstar

Northstar incorporates the useful Goal-Driven Engineering operating model from [stancsz/goal-driven-engineering](https://github.com/stancsz/goal-driven-engineering): durable product intent sits above a self-contained `GOAL.md`; an agent owns the implementation path and evidence until the goal is proven complete. Product direction and acceptance belong to the Steward (the user or an explicitly authorized product owner). The Builder may choose and change implementation details autonomously within that contract. Northstar extends this model with an explicit business-viability gate and point-of-no-return approval rules.

## Shape a viable goal before building

At project start, establish a North Star and a credible product thesis before creating a large implementation plan. Ask only for missing decisions, but do not skip the questions that determine whether the work can create durable value:

- **Customer and user:** Who has the problem, who uses the product, and who decides or pays?
- **Pain and alternatives:** What costly or frequent job is not being done well today? What do users do instead?
- **Value and differentiation:** What measurable improvement will the product deliver, and why would users switch, adopt, or pay for it?
- **Business viability:** How does value become revenue or a sustainable operating outcome? What are the cost to acquire, deliver, support, and maintain it? Which assumptions could make the economics fail?
- **Evidence and production path:** What existing evidence supports the thesis? What is the cheapest credible way to validate the riskiest assumption, and how will that validation lead to a production-capable product?

Challenge unsupported claims with targeted research, customer or market evidence, and explicit assumptions. Do not treat enthusiasm, a feature list, a successful demo, or technical feasibility as proof of demand or viability. If the thesis is not credible yet, define a bounded validation goal with a decision it will resolve. Do not silently turn that experiment into the end product.

If the user explicitly has a non-commercial mission, replace revenue with a clear, durable value and sustainability model. Otherwise, treat customer demand and economic viability as part of the product's acceptance—not optional polish.

## GOAL.md lifecycle

Use one active `GOAL.md` for a coherent outcome unless the user asks for parallel goals. Make it self-contained enough that a fresh agent can continue from the repository and the goal file.

1. **Steward shapes the contract:** record North Star, target customer, problem, value thesis, supporting evidence and assumptions, outcome, source of truth, acceptance criteria, constraints, non-goals, and escalation conditions.
2. **Builder executes:** inspect current reality, choose the highest-value next step, research implementation unknowns, implement a coherent slice, verify it, and record decisions and evidence in `GOAL.md`.
3. **Builder verifies:** map each acceptance criterion to concrete evidence; include real integration/runtime or operational evidence when the claim requires it.
4. **Steward closes:** accept, reject, split, or supersede the goal. Product intent, viability assumptions, acceptance, and authority cannot be weakened by the Builder to make a goal pass.

Keep implementation detail below the goal contract. Do not create extra task lists or planning layers unless they solve a concrete coordination problem. Read [assets/GOAL.template.md](../assets/GOAL.template.md) when creating a durable goal.

## Production-value execution

Prefer the next step that unlocks a real user capability, validates a critical business assumption, removes a production blocker, or materially reduces a risk. Research technical choices independently and record only conclusions that change a decision. A prototype is justified only as an explicit, bounded experiment with a success signal, a decision threshold, and a route to production.

Separate product uncertainty from implementation uncertainty:

- **Product or business uncertainty** (customer, pain, value, positioning, willingness to pay, economics, durable constraints) must be surfaced to the Steward early. AI can gather evidence and recommend, but cannot invent the answer.
- **Implementation uncertainty** (libraries, APIs, architecture within approved constraints, debugging, test design) is Builder work. Research and decide autonomously within the goal and permissions.
- **Point-of-no-return action** (release, destructive migration/deletion, spending, permission change, external commitment) is governed by the collaboration contract. Prepare and verify first; get explicit approval before crossing it.

GDE's conceptual roles map to Northstar modes by decision rights, not by fixed persona: product intent and major value tradeoffs remain human-owned; reversible research and implementation are usually `AUTO`; high-impact execution is `GUARD`; high-impact unresolved product or architectural choices are `CHALLENGE`; human-sovereignty decisions use `HUMAN_ONLY`.
