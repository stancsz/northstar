# Goal-driven engineering in Northstar

Northstar incorporates the useful Goal-Driven Engineering operating model from [stancsz/goal-driven-engineering](https://github.com/stancsz/goal-driven-engineering): durable product intent sits above a self-contained `GOAL.md`; an agent owns the implementation path and evidence until the goal is proven complete. Northstar uses explicit operational ownership: **orchestrator owns the North Star, supervisor owns a goal, worker owns a task**. The human retains product intent and authorization; agents choose implementation details within that mandate. See [ownership and decision boundaries](../SKILL.md#ownership-north-star--goals--tasks). Northstar adds early discussion of business viability and explicit decisions before irreversible actions.

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

Use `docs/goal/<goal>/GOAL.md` for a coherent outcome, with one active goal unless the user asks for parallel goals. Track status in the file and link it from `docs/goal/README.md`; keeping the path stable preserves links from evaluations and commits. Make it self-contained enough that a fresh agent can continue from the repository and linked documentation.

1. **Orchestrator shapes and assigns the goal:** connect the North Star, customer, value thesis, evidence and assumptions to an outcome, acceptance criteria, constraints, non-goals, and escalation conditions. Resolve missing human decisions and name the supervisor.
2. **Supervisor plans; workers execute:** the supervisor maintains `GOAL.md`, assigns bounded tasks and write scopes, and tracks dependencies. Workers inspect reality, research implementation unknowns, implement coherent slices, check their work, and return evidence. The supervisor accepts task handoffs and integrates the result.
3. **Critic challenges completion:** inspect the actual artifact and diff against the original intent, owner quality examples, and acceptance criteria. Identify substitutions, weakened requirements, and hidden work left for the user. Report actionable findings directly to the accepting supervisor or orchestrator.
4. **Verifier checks:** exercise the real behavior and relevant failure cases, including integration/runtime or operational paths when the claim requires them. Use an independent reviewer for substantial work when available; otherwise perform a fresh verification pass and state the limitation. The supervisor ensures the goal's evidence covers the integrated outcome.
5. **Workers repair; supervisor integrates:** fix blocking findings within the agreed scope and submit the updated artifact for review again. Preserve finding history and update evidence after changes. The supervisor owns integration repairs and recommends readiness only after material findings are resolved and rechecked.
6. **Orchestrator accepts the goal:** inspect the integrated result and evidence against the original goal, owner standards, and reference product. Close when agreed behavior works and material findings are fixed, with human acceptance where required. Report what was actually checked and any remaining limitations. No agent may weaken product intent, viability assumptions, acceptance, or authority to make a goal pass.

Keep implementation detail below the goal. Do not create extra task lists or planning layers unless they solve a concrete coordination problem. Use [the Markdown goal template](../templates/GOAL.md) when creating a durable goal.

Keep review proportional and practical. Use the actual code, product, and concise notes in the goal. An engineering review should find and fix weaknesses, not become a separate reporting project.

## Durable documentation and handoffs

Use `docs/northstar/` for durable direction and standards, `docs/goal/` for execution, and `docs/evals/` for what review and verification actually found. Maintain a short README index in each directory once it contains useful material. Keep each fact in one authoritative place and cross-link it.

Only subdirectories belong directly under `docs/`. Put supporting documentation outside those three categories in `docs/misc/`, including installation guides and translations. Keep each index inside its category, and update links when moving existing material.

At the start of work, read the root and relevant nested `AGENTS.md`, then the linked North Star, active goal, and applicable evaluations. At meaningful decision points, update the appropriate document. Before a context switch, delegation handoff, or completion, reconcile the goal's status and remaining work with the repository. Record failures and limitations alongside successes. Do not rely on chat history as the only record.

An evaluation should make its conclusion reproducible: link the goal and artifact revision, state the environment and method, describe observed results and relevant evidence, and identify unresolved issues. Keep durable evidence with its evaluation or at a stable artifact link. Temporary logs in `tmp/` alone are insufficient for a long-lived claim; preserve the useful excerpt or promote the necessary artifact.

Keep `AGENTS.md` concise and specific: reading order, repository map, working commands, important constraints, and contribution practices. Update it when these change, preserve existing project rules, and use nested instructions only for genuine local differences. Avoid copying the product specification or a generic handbook into it.

Agents and subagents use `tmp/<task-or-agent>/` for disposable files and respect the project's `.gitignore`. Each delegate receives the relevant docs, its write scope, documentation responsibility, and scratch location. Shared docs have one editing owner; other agents send findings to that owner. Before committing, inspect the diff and staged paths, preserve unrelated work, and use a meaningful message that describes the change and its reason.

The entire project shares a 100 GB artifact ceiling, including ignored files and attributable caches or copies outside the main checkout. Check current usage and expected peak growth before artifact-heavy work, recheck after large output, and address bloat around 80 GB. Include each delegate's expected storage use in its brief. Reuse data and remove only your own disposable output when safe; preserve source, user data, other agents' work, and required evidence. Stop new artifact growth that cannot fit instead of silently exceeding the cap.

## Product reference and quality expectations

Research a leading comparable product for the same customer and workflow. Record why it is the reference, the source/date, and the actual behaviors worth matching or improving. Compare UI/UX, look and feel, usefulness, task effectiveness, reliability, simplicity, and maintainability where observable. Refresh the comparison when the product direction changes or new evidence matters.

Use concrete owner examples to explain acceptable quality and unacceptable shortcuts. Turn competitive gaps into useful work: a confusing checkout, missing recovery behavior, or an incomplete integration matters more than superficial feature counts. Test a stated 98% parity target against defined comparable tasks and measurements; do not fabricate a universal quality score. Keep unknown competitor internals and untested behavior explicit.

## Production-value execution

Prefer the next step that unlocks a real user capability, validates a critical business assumption, removes a production blocker, or materially reduces a risk. Research technical choices independently and record only conclusions that change a decision. A prototype is justified only as an explicit, bounded experiment with a success signal, a decision threshold, and a route to production.

Separate product uncertainty from implementation uncertainty:

- **Product or business uncertainty** (customer, pain, value, positioning, willingness to pay, economics, durable constraints) goes to the orchestrator early, and to the human when it needs an owner decision. AI can gather evidence and recommend, but cannot invent the answer.
- **Implementation uncertainty** (libraries, APIs, architecture within approved constraints, debugging, test design) belongs to the worker for its task and the supervisor for goal integration. Research and decide autonomously within the goal and permissions.
- **Point-of-no-return action** (release, destructive migration/deletion, spending, permission change, external commitment) depends on the user's authorization. Prepare and verify first, and obtain the required approval before crossing it.

GDE's conceptual roles map to Northstar modes by decision rights, not by fixed persona: product intent and major value tradeoffs remain human-owned; reversible research and implementation are usually `AUTO`; high-impact execution is `GUARD`; high-impact unresolved product or architectural choices are `CHALLENGE`; human-sovereignty decisions use `HUMAN_ONLY`.
