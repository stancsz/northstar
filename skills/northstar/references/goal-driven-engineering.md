# Goal-driven engineering in Northstar

Adapted from [Goal-Driven Engineering](https://github.com/stancsz/goal-driven-engineering). Follow the [core execution rules](../SKILL.md#deliver-a-usable-mvp-then-improve-in-increments); this page covers goal records, not another review cycle.

## Define the goal

Use the project's existing issue, task file or plan as the goal record; preserve its stable location and ownership. Do not create parallel Northstar records or indexes. If no convention exists and durable state is needed, the optional [template](../templates/GOAL.md) can live at `docs/goal/<goal>/GOAL.md`; omit irrelevant sections. A small one-turn task can use its request and handoff. Follow explicit repository requirements.

Record the user, workflow, environment, acceptance, constraints and excluded scope only where not already clear. Link existing product direction. For new product direction, identify expected value, payer or sustainability model, supporting evidence, and the assumption the next delivery will test. Do not repeat discovery already settled in the repository.

Keep current delivery criteria separate from later increments and long-term business claims. Do not reduce explicit requirements. Compare a reference product only where it informs a current decision or requested evaluation; use named tasks and observable results, not an invented overall quality score.

## Execute and accept

1. The orchestrator assigns the outcome and constraints within the user's mandate.
2. The supervisor records bounded tasks, owners, write scopes, dependencies, acceptance, and report paths.
3. Workers implement and check their tasks, then update their [reports](../SKILL.md#worker-reports-and-handoffs), including blocked or partial results.
4. The supervisor reads reports, inspects artifacts and applicable evidence, coordinates repairs, and records task decisions. Obtain the nonauthor QA/taste verdict against the user's criteria and actual behavior; reuse valid evidence rather than rerunning work per role.
5. The orchestrator inspects the integrated result and accepts or returns it for repair. The supervisor records that decision and updates any existing task index. Obtain human acceptance where required.

One agent may combine compatible management/building responsibilities and record one decision based on a separate nonauthor reviewer's evidence. It cannot supply independent QA or taste approval for its own work. If no independent reviewer is available, acceptance remains unverified; do not simulate sequential approvals between titles. For a small single-agent change, update the active goal rather than starting a new lifecycle; a separate handoff report is needed only when repository instructions require it. Preserve unmet criteria when blocked; record the precise dependency and next action. After acceptance, deliver the slice and proceed only to remaining authorized work.

## Keep continuation cheap

Maintain the next unmet criterion, material decisions, reusable evidence, and blockers in the same goal. Update the same handoff after repairs and retain material failure history. Keep evaluation details in the existing review/task record with revision/environment and evidence; avoid copying them across records.

For stalled work, carry the [recovery checkpoint](../SKILL.md#recover-from-a-stall) forward. Attempts belong to the unmet criterion, not to a particular agent or approach. Inspect current artifacts before using a checkpoint; resume a blocked investigation only when its unblock condition changes.

Follow the [ownership boundaries](../SKILL.md#ownership-north-star--goals--tasks): one editor per shared document; workers propose changes to its owner. Reuse the core skill's repository, storage, and authorization rules. A handoff should let the next agent continue without reconstructing or repeating completed work.
