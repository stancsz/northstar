# Northstar direction

## Purpose

Help an owner turn ambiguous intent into useful, economically sustainable products that meet their quality standards, while reducing routine supervision.

The target user is an owner or developer working with AI agents who needs initiative and reliable completion. The pain is convenient shortcuts: an agent appears finished while integration, UX, failure handling, or other essential work is missing.

## Confirmed owner expectations

- Maximize useful accepted outcomes with the least elapsed time and total tokens, including rework. Lean first, functioning first: the leanest, cleanest product, no spaghetti code, maximum practical reuse, and top-class design that stays inexpensive to extend. Remove unnecessary machinery and duplication; keep wording as short as the task allows. Preserve readability and credible extension paths without speculative frameworks or unmeasured savings claims. See [design guidance](../../skills/northstar/SKILL.md#excellent-design-with-minimal-machinery).
- Deliver a usable MVP quickly, then build on accepted work in small increments. Bound each delivery, reuse applicable evidence, and change approach when retries stop producing information. Long-term quality requirements remain visible without making every future feature a prerequisite for the current slice. See the [delivery rules](../../skills/northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments).
- Challenge the customer, problem, commercial value, and production direction early. Research facts independently and ask for decisions the owner actually needs to make.
- Use reference products to resolve specific design questions or evaluate a requested comparison. Name the workflows and observable criteria; do not impose default parity targets or invent overall quality percentages.
- Write concise instructions that tell agents what to do, when to repeat work, when to ask, and when to finish. Express quality standards as inspectable behavior rather than slogans.
- Preserve existing authorization across context changes and delegation; do not require approval to continue already-requested work. Managing agents resolve ordinary decisions, dependencies, overlap and stalls, then inspect the integrated workflow. Use short [role briefs and a coordination loop](../../skills/codex-subagents/SKILL.md#coordinate-to-a-working-result); status relay alone is insufficient. Platform permission blocks remain distinct from missing user authorization.
- Recover stalled work using a persistent checkpoint and bounded investigation: count evidence-backed progress against the unmet criterion across agents and context changes. Validate recovery guidance with scoped execution trials, while distinguishing those trials from long-session reliability or enforced limits.
- Critics and verifiers use the owner's standards and inspect actual results. Fix shortcuts and recheck rather than merely listing defects.
- Use concise QA to prevent sloppy delivery: plan visible work, inspect rendered results and real workflows, challenge readiness with relevant failure cases, and verify repairs. Distinguish material defects from preference changes, missing evidence from a pass, and AI review from human approval. See [Northstar QA](../../skills/northstar-qa/SKILL.md).
- Visible deliveries need screenshots actually viewed, concrete visual observations, and executed functional checks; a bare LGTM is insufficient. Keep routine QA fast with representative evidence and targeted rechecks, expanding only for requirements or observed risk.
- Keep Northstar as Markdown engineering methods and practices under `skills/`. Avoid executable enforcement and machine-contract machinery.
- Use `docs/northstar/`, `docs/goal/`, `docs/reports/`, and `docs/evals/` as shared memory. Keep only subdirectories directly under `docs/`; other supporting documentation belongs in `docs/misc/`. Keep a useful `AGENTS.md`, scoped scratch work in `tmp/`, appropriate ignore rules, and meaningful commits.
- Keep total project artifacts below 100 GB across agents, including ignored and project-attributable working data.
- Use explicit ownership: the orchestrator owns and uses `docs/northstar/` and is accountable for the integrated product outcome; supervisors own and use their `docs/goal/<goal>/GOAL.md` and index entries; workers produce work and write `docs/reports/<goal>/<task>.md`. Supervisors read reports and inspect artifacts before task acceptance. Critics and verifiers provide independent review where available. See the [role boundaries](../../skills/northstar/SKILL.md#ownership-north-star--goals--tasks).

## Product assumptions and open questions

The above requirements come from the owner's instructions in this project. Demand beyond this use case, a commercial model for Northstar itself, and comparative performance against other engineering skills have not been validated. No leading equivalent has yet been selected through a comparative evaluation. Do not claim profitability or competitive parity without that work.

Goal-Driven Engineering supplies the goal-oriented practice adapted by Northstar; this methodological source is not evidence of competitive superiority.

## Navigation

- [Skills and use](../../README.md)
- [Goals](../goal/README.md)
- [Worker reports](../reports/README.md)
- [Evaluations](../evals/README.md)
- [Repository instructions](../../AGENTS.md)
