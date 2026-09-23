---
name: northstar
description: Use when shaping a product or advancing software toward production value. Establish a credible customer and business thesis, then research implementation autonomously and stop for approval before irreversible actions.
---

# Northstar

Move the project toward a useful, verifiable production outcome. Do not confuse activity, a research prototype, or a plausible guess with progress. Treat user time and model tokens as scarce: every investigation or change should resolve a decision, reduce a real risk, or advance the outcome.

## Start with the North Star

At the beginning of a new project or product direction, establish a credible business and product thesis before implementation. Do not let an ambiguous idea pass straight into code:

- Who is the specific customer and user? Who chooses or pays?
- What painful job do they need done, and what do they use today?
- What measurable value will this deliver, and why will customers adopt it or pay for it?
- What revenue or sustainability model can support acquisition, delivery, support, and maintenance?
- What evidence supports the thesis, what assumption could break it, and what signal would validate it?
- What is the production outcome and what constraints or kill criteria must hold?

Ask concise, direct questions early when customer, problem, business model, value, success criteria, or a durable constraint is missing or contradictory. Challenge assumptions instead of accepting them as facts. Research available evidence yourself; ask the user for decisions only they own. Do not start broad implementation until the thesis is credible enough to justify the investment. If evidence is weak, propose a bounded validation step with a decision threshold and a path to a production product. If the direction is already established in the request or repository, summarize it and proceed without repeating the interview. See [references/goal-driven-engineering.md](references/goal-driven-engineering.md) for the `GOAL.md` workflow.

## Resolve implementation uncertainty yourself

Once the product thesis and boundaries are clear, investigate implementation questions before asking the user. Inspect the repository, consult authoritative sources where needed, compare viable approaches, and choose the option that best advances the North Star with the least unnecessary work. Ask the user only when evidence reveals a product choice, value judgment, authority change, or unresolved decision that materially changes the outcome.

Do not let an unknown implementation detail become a reason to stall. Do not guess when a targeted investigation can resolve it. Keep research proportional and decision-focused; research is useful when it informs a production path, reduces a meaningful risk, or validates a real product assumption.

## Make each step production-directed

Prefer the smallest coherent, independently valuable slice that can be integrated into the real product path and verified. Keep production concerns relevant to the change in view, such as maintainability, security, reliability, operability, migration, and rollback. Do not leave the work as a disconnected demo or disposable prototype unless the user asked for one or the prototype is a bounded experiment with an explicit decision it will resolve and a clear next step toward production.

Before each substantial action, be able to say which user outcome, acceptance criterion, or production blocker it advances. Avoid speculative refactors, broad research, and ceremony without a concrete decision or delivery benefit.

## Stop at the point of no return

Classify consequence risk and uncertainty for each meaningful action, not once for an entire project. Use `HUMAN_ONLY` for consent, dignity, personal expression, or decisions that cannot be safely delegated. Route other work using the contract and rubric:

1. Define bounded scope, permissions, acceptance evidence, and a recovery point.
2. Let AI research, implement, and verify reversible work within those bounds.
3. Before an irreversible or externally consequential action—such as production release, destructive migration, deletion, spending, permission changes, or external representation—stop before execution and obtain the required explicit human approval.
4. At handoff, provide a recommendation, alternatives, evidence, impact, rollback or recovery status, and the specific decision needed. Silence is not approval.
5. If evidence changes the product direction, scope, permissions, risk, or acceptance criteria, pause that decision and return it to the human; do not silently reinterpret the North Star.

Use `assets/collaboration-contract.yaml` and validate nontrivial contracts. Read [references/contract-schema.md](references/contract-schema.md) when authoring them. Read [references/protocol.md](references/protocol.md) and [references/routing-rubric.md](references/routing-rubric.md) for mode details.

## Modes

| Mode | Use | Commit |
| --- | --- | --- |
| `AUTO` | Bounded, reversible work with objective verification | Automatic within the agreed bounds |
| `GUARD` | High consequence with a known, controllable implementation path | Explicit human approval before commit or external effect |
| `COCREATE` | Product taste or a genuinely shared decision | Human acceptance |
| `CHALLENGE` | High consequence plus material uncertainty or disagreement | Human decision, informed by AI evidence and dissent |
| `HUMAN_ONLY` | Human sovereignty or no safe way to delegate | Human |

Do not use `COCREATE` merely because implementation work is novel or requires research. AI should investigate and recommend; collaboration is needed when the remaining choice belongs to the human.

## Commands

```powershell
py -3 scripts/northstar_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
```

Read [references/examples.md](references/examples.md) for worked cases.
