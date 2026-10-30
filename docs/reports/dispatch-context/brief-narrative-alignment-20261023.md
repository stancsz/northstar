# Brief narrative alignment

Goal: [dispatch context](../../goal/dispatch-context/GOAL.md). Scope: the "Task brief and handoff" prose in the Codex Subagents skill, reconciled with the manager brief templates.

## Outcome

The skill narrative still asks the assigning agent to "Give each delegate five things" and lists Result, Acceptance, Autonomy, Coordination and Handoff, while the [orchestrator brief](../../../skills/subagent-orchestration/templates/orchestrator.md) and [supervisor brief](../../../skills/subagent-orchestration/templates/supervisor.md) also present Functions and separation, Guidance with an Inference subline, Write scope and scratch, and Dispatch timing. The skill now says which five are the core responsibilities and how each remaining template field makes one of them actionable, so a manager can tell the difference between the five responsibilities and the fields that carry them. This task changed no template, goal, index, evaluation or test file; those paths already carried uncommitted edits from other work and were left untouched.

## Changed paths

- `skills/codex-subagents/SKILL.md` - one added paragraph in the "Task brief and handoff" section.
- `docs/reports/dispatch-context/brief-narrative-alignment-20261023.md` - this handoff.

## Prose added

One paragraph was inserted after the five-bullet list (Result, Acceptance, Autonomy, Coordination, Handoff) and before the existing write-scope paragraph:

> The manager templates realize those five as concrete fields. `Result`, `Acceptance`, `Autonomy`, `Coordination` and `Handoff` carry the five directly; the other fields are how those five become actionable in the brief. `Functions and separation` names the creators, the nonauthor reviewer and the decision owner behind Coordination and Acceptance. `Guidance` carries the applicable repository instructions and the essential source/test facts in the prompt or at their exact path, with links reserved for supporting context. `Write scope and scratch` fixes Autonomy's owned paths and Handoff's required report path. `Dispatch timing` sets the checkpoint and hard handoff deadline that Handoff reports against. `Inference`, nested under Guidance, records the route, model alias and protocol the parent has already verified. Fill them for the task at hand: Guidance, the exact write scope and scratch, dispatch timing and the route context are what make the five enforceable, not decoration to drop. The parent keeps route verification and acceptance; the brief hands over that verified context without transferring the ownership.

## Mapping the paragraph states

| Template field | Core responsibility it carries |
| --- | --- |
| Result | Result |
| Acceptance | Acceptance |
| Functions and separation | Coordination (creators, reviewer conflicts) and Acceptance (nonauthor reviewer, decision owner) |
| Guidance | Result (next action) and Autonomy (applicable repository instructions, essential source/test facts) |
| Write scope and scratch | Autonomy (owned paths) and Handoff (required report path) |
| Dispatch timing | Handoff (checkpoint and hard handoff deadline) |
| Inference (under Guidance) | Autonomy (already-authorized route and source) and the parent's route evidence |
| Coordination | Coordination |
| Handoff | Handoff |

## Scope kept

The five brief elements and the role/accountability rules are unchanged, and the existing write-scope, scratch, exact-path and repair-dispatch paragraphs are untouched. Guidance and source instructions, the exact write scope and scratch, dispatch timing and the route/inference context are described as required content, so the paragraph does not imply any of them can be dropped. Route verification and acceptance stay with the parent. No approval gate, governance layer, prompt-length limit, field or behavioral claim was added.

## Checks

- `git diff --check -- skills/codex-subagents/SKILL.md docs/reports/dispatch-context/brief-narrative-alignment-20261023.md` - exit 0, clean apart from the repository's existing LF/CRLF working-copy warnings. This report is a new untracked file, so `git diff --check` covers the tracked skill file only.
- Scoped diff inspection of `skills/codex-subagents/SKILL.md` confirms this task's change is the single added paragraph; the file's other uncommitted edits predate this task and were left as found.
- Local Markdown link check over both files: `skills/codex-subagents/SKILL.md` has 29 Markdown links and this report has 3; every relative path resolves and every fragment matches a heading in its target file. The added paragraph uses inline code for field names and introduces no new link.
- Scoped `git status --short` on the neighbouring paths confirmed that both templates, `docs/goal/dispatch-context/GOAL.md`, `docs/evals/dispatch-context.md` and `docs/reports/README.md` already carried uncommitted edits from other work; this task did not modify them.
- No test, build, package, network call, cleanup, commit or push was run, and no path outside the two listed above was written. Scratch: none.

## Limits

This is a prose reconciliation only. It was reviewed against the two current templates and the goal, and it was diffed and link-checked, but it was not behaviorally tested: no dispatch was run under the new paragraph, so it is not evidence of clearer briefs, better scope compliance or fewer out-of-scope events. The source-instruction template change recorded in the goal remains unverified in the same way. The parent owns acceptance.

## Parent acceptance and dispatch outcome

The parent reviewed the added paragraph and the worker's mapping table. The field-to-responsibility mapping is coherent and keeps route verification and acceptance with the parent. The assigned source and report were the only paths in the worker's completed `file_change` events. Parent Markdown-link review confirmed the pre-existing Northstar anchor that the worker's first checker had mis-slugged; its corrected check reported both files clean.

This was not a completed worker handoff: the worker returned its required two-minute checkpoint and produced the scoped source paragraph and report, but had no `turn.completed` after the five-minute hard deadline. The parent stopped the process at about 5 minutes 10 seconds. The receipt contains 21 completed `command_execution` calls (42 started/completed lifecycle events), six file-change lifecycle events across the two assigned paths, and no reported usage. Treat the artifact as an independently reviewed partial increment; do not count the dispatch as successful delivery or as evidence of economical execution. The parent separately verified the current Subroute route and a helper-mediated read smoke; their sanitized receipt is `tmp/dispatch-context/continuation-read-smoke-20261023/route-preflight.json`.
