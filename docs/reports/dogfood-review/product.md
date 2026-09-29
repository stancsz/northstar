# Product review: where Northstar should aim next

## Judgment

**Target user/job:** an owner or developer who delegates meaningful work to AI agents and wants a usable, standards-compliant result without routine handholding. The current direction names this user and the failure clearly: apparent completion that omits integration, UX, or failure handling ([direction](../../northstar/README.md), lines 3–7). The job is broader than software delivery today: it also covers projects and business operations.

**Proposed North Star:** *Help owner-builders get more of their AI-delegated work accepted as useful, complete outcomes, while reducing the time and supervision needed to reach them.* This keeps the current value promise, but makes acceptance and user effort the product outcome; “least total time, tokens and future rework” remains an efficiency constraint to measure, not a promise that the product already saves them ([Northstar skill](../../../skills/northstar/SKILL.md), lines 8–9).

**Strongest asset:** the package joins execution, QA, coordination, and bounded advice under one operating principle, and explicitly makes companions conditional rather than mandating four-agent ceremony. Its clearest differentiator is the evidence-and-authority discipline: verify the actual workflow, preserve acceptance and authorization, and report unknowns honestly. The recent local trials show that this practice can guide specific bounded tasks: simple UI defects were detected with browser evidence, and two synthetic recovery fixtures ended in a repair or a truthful missing-input block. Those are concrete examples, not broad superiority claims ([QA evaluation](../../evals/qa-suite.md), lines 11–37; [recovery evaluation](../../evals/stall-recovery-trials.md), lines 7–10 and 50–54).

**Biggest constraint:** effectiveness and demand are still unproven at the level the product promises. Existing evidence is mostly documentation inspection, narrow fixtures and synthetic handoffs. The evaluations explicitly lack a matched old/new task comparison, measured full-task cost, long-session evidence, and live-business outcomes ([incremental evaluation](../../evals/incremental-delivery.md), lines 26–27; [coordination evaluation](../../evals/coordinated-delivery.md), lines 35–37; [direction](../../northstar/README.md), lines 36–39). The four-skill package is locally verified as installable, but package correctness does not show that a user gets better work or chooses to keep using it ([package evaluation](../../evals/central-package.md), lines 11–18 and 26–30).

## Measures that would make the next claim testable

Run matched, real owner-builder tasks with Northstar and a clearly named baseline (for example, the same agent setup without these skills). Keep the task mix and acceptance criteria visible. Report each measure separately; do not turn them into a blended score:

- Share of tasks accepted against predeclared criteria, with defects and severity recorded by an independent reviewer.
- Elapsed time from task start to accepted result, including repair cycles.
- Total model tokens and billed cost across coordinator, workers, review, consultation, and rework; mark unavailable usage as unknown.
- Number of owner interventions needed and time spent by the owner.
- For demand, whether participating users voluntarily reuse the package on another eligible task; this is a separate adoption signal, not proof of task quality.

The goal need not set numeric thresholds before any pilot data exists. It should define task inclusion, baseline, acceptance rubric, accounting boundary, and a decision rule before comparing results. Do not claim savings from selecting a lower-cost model or from a successful isolated fixture.

## Ordered next actions

1. **Validate first with owner-builders delegating bounded software changes.** Keep the owner-required business scope and four-skill package intact; this is sequencing for learning, not a scope-removal proposal. The cohort uses an audience already identified in the direction and a domain with observable acceptance criteria.
2. **Run a small matched pilot on actual eligible tasks, with consent and no external side effects.** Predeclare acceptance and capture the separate outcome, quality, latency, cost, rework, and owner-effort measures above. Include the full management/review work in the accounting. The next decision is whether Northstar improves accepted outcomes or user effort enough to justify its added process; if outcomes are unchanged and effort rises, simplify or reposition rather than broaden.
3. **Use the pilot to simplify invocation and test repeat use.** Preserve the four-skill package while clarifying when each companion helps, and ask users whether they would use it again on comparable work. Seek willingness-to-repeat evidence before investing in commercial positioning or claims of competitive advantage; both demand and commercial model are currently stated as unvalidated ([direction](../../northstar/README.md), lines 38–43).

## Checkpoint self-review

What worked: the assigned source set made it possible to distinguish the stated user/job from what the evaluations actually establish; package checks and behavioral fixtures were not treated as outcome or economic proof. What remains unknown: there is no observed user interview, real-work task comparison, task-level usage accounting, or adoption result in the reviewed evidence. Next action: the primary should compare this narrow-proof recommendation with the usability and QA handoffs, resolve only material differences, and set the first pilot's owner, task set, baseline, and stop/reopen rule. No advisor call is warranted for this product judgment: the next uncertainty is empirical and can be tested with an authorized local pilot, while the review goal says not to call an advisor merely to exercise the skill. Per-task elapsed time and token usage for this review were not exposed to me.



## Peer exchange

**Routine-task routing before the first comparison:** I agree with the usability review that the low-ceremony route should be easier to find; the current entrypoint makes learning/review prominent while the small-task allowance is deeper in the skill. This is a discoverability correction, not a new process rule. Make the route visible, then freeze and identify that package/document version before recruiting pilot tasks so the comparison tests the intended first-use path. QA found no documentation/evidence defect and likewise points to matched held-out tasks; it does not argue for freezing an obscure first-use presentation. If a newcomer check shows the route is already reliably found, or the added prompt causes required checks to be skipped, I would defer or revise the presentation change.

**Bounded software cohort, with business operations retained for a separate cohort:** I still favor software first as a sequencing choice, while preserving the owner-required scope and four-skill package. The usability review proposes a useful spread—routine work, a multi-part task where delegation may help, and a real failure/integration issue—which can all fit within that first software cohort. QA's recommendation for held-out matched tasks with unchanged acceptance also fits. This makes the first comparison interpretable without implying software proves business value; a later, separately measured business-operations cohort is still needed before broadening claims. I would reorder if owner priorities or eligible task access show a business workflow is the more consequential and measurable first test, or if the software results expose no meaningful product uncertainty while a concrete business case does.

There is no material disagreement with either reviewer on the need for real matched evidence, honest missing-usage accounting, or the distinction between package correctness and task effectiveness. The primary owns the final sequence and pilot boundary.
