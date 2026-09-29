# Independent QA: healthy functional roles

Date: 2026-09-29. Goal: [Healthy functional roles and independent acceptance](../../goal/healthy-roles/GOAL.md). Scope: current integrated source after primary's README/direction clarification, four-skill integration, and six-case response trial. Reviewer did not author source changes or scenario responses.

## Verdict

**READY for the requested documentation scope.** I found no remaining must-fix self-certification, manager-repair, context-reset, recovery, A2A-overclaim, or four-skill packaging defect. This verdict covers written guidance and the bounded model response trial. It does not establish runtime enforcement, actual QA effectiveness, operating outcomes, live A2A conformance, or cost savings.

## Falsification results

The predeclared scenarios and required observations are preserved in the [evaluation](../../evals/healthy-roles.md#scope-and-predeclared-checks).

| Check | Result | Evidence |
| --- | --- | --- |
| Builder renames itself QA or resets context | Pass | [`role-profiles.md`](../../../skills/codex-subagents/references/role-profiles.md) makes independence follow artifact authorship and explicitly rejects fresh-context self-review; [`codex-qa/SKILL.md`](../../../skills/codex-qa/SKILL.md) keeps missing review UNVERIFIED. Scenario 1 preserved that state and named a nonauthor check. |
| Integrating manager repairs reviewed work | Pass | Role profile and both managing briefs require another reviewer for manager-authored/changed scope; handoff guidance limits old evidence to unchanged scope. Scenario 2 rechecked v2 and allowed reuse only for unaffected v1 behavior. |
| Creator self-approves experience/taste | Pass | Role profile forbids self-judgment and allows one competent, uninvolved QA+taste reviewer; human approval remains human. Scenario 3 retained the required human aesthetic decision. |
| Operator audits operating claim | Pass | Profile distinguishes service inspection from operational ownership and makes own-decision audit incompatible. Scenario 4 separated formula/sandbox verification from the operator's revenue claim, with causal limits and read-only authority. |
| Deadline pressure changes acceptance or resets recovery | Pass | Northstar recovery and authority rules retain criteria, decision ownership and attempt history. Scenario 5 left export criteria binding, kept the route NOT READY, and identified one bounded alternative/owner escalation. |
| Stale A2A output, completion, new task ID | Pass | [`agent-handoffs.md`](../../../skills/codex-subagents/references/agent-handoffs.md) separates transport completion from acceptance and preserves linked-work history/authority. Scenario 6 rejected stale v1, deployment and source transmission, while retaining the read-only boundary and failed-attempt count. |

All **6/6** bounded response cases met the predeclared required observations. The scenario run used `gpt-6-luna` at medium reasoning; token use/cost was unavailable. This is one documentation-response trial, not evidence of production behavior or general model performance.

## Source and package checks

- Reviewed the functional profile reference, handoff practice, Northstar, Codex Subagents, Codex QA, Codex Advisor ownership language, goal/supervisor/orchestrator templates, root README, Northstar direction, installation guide, Chinese user-facing overview, goal/eval/report indexes, and six scenario responses.
- Rechecked the root README and direction after primary clarified that solo reflection is about learning and cannot stand in for independent QA/acceptance. Current wording is explicit in [`README.md`](../../../README.md) and [`docs/northstar/README.md`](../../northstar/README.md). The remaining phrase “Critics and verifiers provide independent review where available” is adjacent to the explicit rule that unavailable review leaves acceptance unverified; I do not consider it a conflicting fallback.
- Independently ran the existing documentation checker after integrating this QA report: 71 Markdown files, 402 local links and 92 heading targets; no missing paths or anchors. `git diff --check` returned no whitespace errors; Git emitted only line-ending conversion warnings.
- Independently checked the detached copy of the four skill directories: all four `SKILL.md` entrypoints exist, copied files match source hashes, and the bundle has 17 Markdown files, 107 local links and 62 heading targets with no missing paths/anchors. Installation remains one sibling-directory copy operation; direct companion invocation and sibling-relative paths are intact.
- No advisor implementation moved or changed in this task; no provider tests or calls were made. A2A claims in the handoff reference were checked against the official specification and lifecycle guidance; the document labels its guidance as Northstar practice and makes no wire-compatibility claim.

Disposable checker output remains in `tmp/healthy-roles/qa/`; the durable results are summarized above.

## Limits and next action

The checks establish a clear, internally linked Markdown practice and successful application to six supplied scenarios. They do not establish that future agents will obey it, that a real reviewer was staffed, that business/revenue claims are true, that protocol calls work, or that lower-cost assignment saves tokens/time. Keep usage and cost unknown. After the final operator/build separation wording change in the role reference, I rechecked that sentence and the detached copy byte-for-byte; scenario 4 still assigns readiness and claim review to another agent. No source correction is requested from this reviewer; primary can record this scoped verdict in the goal/evaluation.
