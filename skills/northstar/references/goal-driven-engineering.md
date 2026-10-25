# Goal-driven engineering in Northstar

Adapted from [Goal-Driven Engineering](https://github.com/stancsz/goal-driven-engineering). Follow the [core execution rules](../SKILL.md#deliver-a-usable-mvp-then-improve-in-increments); this page covers goal records, not another review cycle.

## Define the goal

Use the project's existing issue, task file or plan as the goal record; preserve its stable location and ownership. Do not create parallel Northstar records or indexes. If no convention exists and durable state is needed, default to `<project-root>/docs/goal/<goal>/GOAL.md` using the optional [template](../templates/GOAL.md); omit irrelevant sections. A small one-turn task can use its request and handoff. Follow explicit repository requirements.

Record the user, workflow, environment, acceptance, constraints and excluded scope only where not already clear. Link existing product direction. For new product direction, identify expected value, payer or sustainability model, supporting evidence, and the assumption the next delivery will test. Do not repeat discovery already settled in the repository.

Keep current delivery criteria separate from later increments and long-term business claims. Do not reduce explicit requirements. Compare a reference product only where it informs a current decision or requested evaluation; use named tasks and observable results, not an invented overall quality score.

## Keep goal state project-owned

Never store canonical project goals, reports or continuation state in a skill installation directory, including `~/.claude/skills/northstar/goals/`, `~/.codex/skills/` or another host's equivalent. Installation files supply reusable instructions; project state belongs with the project or its existing authorized tracker. For an explicitly requested personal goal outside a project, use an explicit user-owned location such as `~/northstar/goals/`, subject to the host's actual access rules. Do not infer that every sandbox forbids or permits that location.

If a stale project instruction points into an installation tree, inspect the existing record read-only where permitted. Preserve its content and history in the agreed project-owned record; verify that copy before updating the project's pointer. Never edit or delete the installed record as part of this migration. If the source is inaccessible or conflicts with current project state, retain that gap and resolve ownership/content before claiming migration complete.

A write denial is evidence of an access boundary, not a reason to retry the protected installation path or bypass host controls. For a new record with no existing canonical location, select an allowed project-owned path consistent with repository rules. If the established project record itself is denied, preserve its canonical location: do not create a competing goal elsewhere. Continue independent work, retain the proposed update and exact failed path/error in the handoff, and identify the access change or owner action needed to update that record. Claim persistence only after a successful write and read-back; a blocked handoff is not a saved goal.

## Execute and accept

1. The orchestrator assigns the outcome and constraints within the user's mandate.
2. For sustained work, the supervisor records bounded tasks, owners, write scopes, dependencies and acceptance in the existing goal. Assign report paths only when the project/task needs a durable handoff.
3. Workers implement and check their tasks, then return the artifact, results, gaps and next action. Use a concise task handoff for small work; record partial or blocked work durably only when continuation needs it.
4. The supervisor inspects artifacts and applicable evidence, coordinates repairs, and records material task decisions in the existing goal. Use one nonauthor QA/taste review when the shared contract or task requires it; otherwise the commander accepts attributable, low-risk work from relevant evidence. Reuse valid evidence rather than rerunning work per role.
5. The orchestrator inspects the integrated result and accepts or returns it for repair. The supervisor records that decision and updates any existing task index. Obtain human acceptance where required.

Combine compatible roles. Use nonauthor QA only when required by the task/repository or when it can change acceptance; authors cannot certify their own work. If required review is unavailable, leave that acceptance unverified. For small, reversible work, the commander checks the diff and relevant tests; add no goal lifecycle or durable report unless required. Preserve blockers and next action, then deliver accepted work.

## Keep continuation cheap

Maintain the next unmet criterion, material decisions, reusable evidence, and blockers in the same goal. Update the same handoff after repairs and retain material failure history. Keep evaluation details in the existing review/task record with revision/environment and evidence; avoid copying them across records.

For stalled work, carry the [recovery checkpoint](../SKILL.md#recover-from-a-stall) forward. Attempts belong to the unmet criterion, not to a particular agent or approach. Inspect current artifacts before using a checkpoint; resume a blocked investigation only when its unblock condition changes.

Follow the [ownership boundaries](../SKILL.md#ownership-north-star--goals--tasks): one editor per shared document; workers propose changes to its owner. Reuse the core skill's repository, storage, and authorization rules. A handoff should let the next agent continue without reconstructing or repeating completed work.
