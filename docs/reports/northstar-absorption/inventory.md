# Northstar absorption inventory

Date: 2026-10-22. Role: read-only inventory for the Northstar direction decision. I inspected the current project direction, next-proof brief, core skill instructions and selected recent goal/evaluation records. This is a worker handoff, not an Advisor verdict, product benchmark, or comparative effectiveness study.

## Finding

Northstar already contains a broad operating model for owner-aligned delivery. Its stated outcome is more real work accepted to owner standards with less total effort and owner rescue. The current direction identifies practical-effectiveness evidence as the constraint and says to add process only for observed friction. The best next absorption is therefore **proof discipline from the current next-proof plan**, not another generalized framework.

The recently reviewed task-changeset SCM design adds exact base/candidate identity, durable checkpoints, dirty-state and overlap handling, stale-review invalidation, and integration provenance. It should remain a workflow hypothesis until its real-task falsification pilot runs. A compact task graph inspired by Smartlog may be useful later, but only if observed work shows that current records hide dependencies, candidate state, or recovery information. Generate such a view from existing records and Git rather than creating a second source of truth.

## Existing Northstar mechanisms

| Mechanism already present | Evidence in Northstar | Interpretation |
| --- | --- | --- |
| Owner intent through task acceptance and integrated inspection | [Project direction](../../northstar/README.md); [Northstar skill](../../../skills/northstar/SKILL.md#ownership-north-star--goals--tasks); [subagent coordination](../../../skills/subagent-orchestration/SKILL.md#coordinate-to-a-working-result) | The project already links outcomes, bounded assignments, handoffs and acceptance instead of treating agent status as completion. |
| Authority and bounded autonomy | [Project direction](../../northstar/README.md); [role ownership](../../../skills/subagent-orchestration/SKILL.md#roles-and-authority) | Workers can resolve in-scope choices while managers retain integration and acceptance responsibility. |
| Independent review and repair | [Codex QA](../../../skills/independent-qa/SKILL.md); [Task Completion Review](../../../skills/task-completion-review/SKILL.md#decide-from-current-evidence) | Review is distinct from authorship; actual criteria/artifacts and unmet outcomes matter. |
| Durable handoff and recovery | [Northstar worker-report practice](../../../skills/northstar/SKILL.md#worker-reports-and-handoffs); [SCM design](../../northstar/adhoc-scm.md) | Checkpoints, stable revision identity, next action and recovery history are already central; worktree paths alone are not durable identity. The SCM extension has not been piloted. |
| Proportionate, flexible process | [Project direction](../../northstar/README.md); [Northstar process guidance](../../../skills/northstar/SKILL.md#coordinate-proportionately) | Add only needed roles/records and remove temporary oversight after the cause passes. |
| Measured real-task validation as next priority | [Next-proof brief](../../northstar/next-proof.md) | It defines a matched cohort, quality bar, effort accounting and decision rules; it is a proposal, not an executed experiment. |

## Evidence inspected and limits

- The [dogfood evaluation](../../evals/dogfood-review.md) recommends a frozen, matched cohort with a direct-agent baseline and separate outcome, effort, owner-burden and learning measures. It states that this pilot has not run.
- The [operating-system evaluation](../../evals/operating-system.md) records bounded local fixture and synthetic planning/dissent exercises. It explicitly leaves long-duration drift, real business operation and economics unproven.
- The [product-delivery goal](../../goal/product-delivery/GOAL.md) records source-level closure repairs while leaving real intended-environment product delivery unresolved.
- The [SCM review](./../adhoc-scm/spec-review.md) judges the workflow specification READY only; its real-task pilot is pending. The [SCM design](../../northstar/adhoc-scm.md) is a hypothesis, not an implemented tool or demonstrated efficiency gain.
- The external comparison evidence is selectively researched, not a comparative benchmark. The [SCM reference report](../adhoc-scm/reference-research.md) describes Scion's atypical scale, treats Google's monorepo paper as broad context, flags the supplied Piper mechanics as secondary-source material, and records the X post as inaccessible. Sapling's compact graph/stack affordances are inspiration, not proof of Northstar fit.

These records prove that specified instructions, narrow exercises and review events exist. They do **not** prove Northstar beats another product, reduces effort, improves accepted outcomes in real projects, or provides sustained business value.

## Recommendations

1. **Execute the already specified real-task cohort before expanding process.** Keep criteria, starting state, permissions and acceptance quality comparable; record full commander/worker/advisor/reviewer/rework effort and owner rescue. Treat missing usage as unknown, not zero. The [next-proof brief](../../northstar/next-proof.md) already defines the comparison and its decision rules.
2. **Pilot the task-changeset protocol on real concurrent work before tooling it.** Test a shared-interface pair, dirty/untracked input preservation, base movement after review, stale approval, and recovery after interruption. Stop or narrow the design if existing Git and project records cannot keep the states aligned without duplication.
3. **Defer a task graph/UI until evidence identifies a visibility problem.** If the pilot shows that dependencies or candidate status are hard to see, try a derived relevant-work view from existing task records and Git. Do not create an independently updated graph/ledger.
4. **Do not import scale-specific machinery absent a matching bottleneck.** A monorepo mandate, online centralized VCS service, global locks/merge queue, duplicate metadata database, added approval layer, or broad reporting framework has no demonstrated Northstar net benefit and would add cost/process.

## Handoff

Conclusion for the Advisor packet: Northstar's current direction already absorbs many useful engineering/product practices. Its clearest improvement opportunity is to produce real comparative evidence and then change only the friction that evidence reveals. Keep the SCM protocol as a testable, bounded candidate, not the answer to an unmeasured general problem.
