# Skill learning and feedback

Use the [Northstar self-learning loop](../SKILL.md#learn-from-every-use): retrieve experience, act, inspect a checkpoint, retain or revise lessons, and apply them next time. Public feedback is a separate optional contribution path. These are Markdown practices, not background telemetry, model training or an automatic memory service.

## Keep one useful local record

Use the active project's existing goal, worker report, or evaluation. The worker records observations; the accepting role checks evidence and owns follow-up. One agent can do both. Keep a short current lesson summary in that record, with links to material history; update rather than creating a file per checkpoint. Keep sensitive material out of tracked records and use a sanitized summary when needed.

A compact entry can read:

> **Checkpoint — task/revision and intended result:** expected versus observed result; evidence and limits. **Use again:** method and applicable conditions, or none observed. **Do not repeat unchanged:** failed approach, failure and reopening condition, or none observed. **Drift/decision:** compare current intent/acceptance/authority; retain/change/stop; next action, owner and judging check. Link earlier evidence and superseded advice instead of copying it.

For routine completion, one sentence can cover this with a link and "no new lesson." These are information needs, not mandatory form fields. Record a candidate as unverified when the cause is only suspected. A checked success can become the preferred method for that situation; wider reuse requires matching conditions, not a confidence score or arbitrary number of successes. If later evidence contradicts it, narrow or supersede it and show why. Never erase a failure to make the history look successful.

## Review checkpoints without bureaucracy

At the core loop's checkpoint triggers, answer: what were we trying to achieve, what actually happened, what should we repeat/avoid, and what do we do next? Tie each answer to the artifact or observation. Record the decision before dependent work continues; executing it and checking the result closes the loop. If the next action belongs to a future session or an external dependency, retain it as pending with its owner/unblock condition rather than claiming the loop executed.

- **Solo:** inspect your own result against intent and evidence, then update the same task record. Do not simulate a dialogue between invented reviewers or call self-review independent.
- **Team:** affected workers supply observations through their existing reports. The accepting owner compares evidence, resolves inconsistent applicability and records one shared decision. Do not vote on facts or copy every report into meeting minutes. For unresolved material disagreement after one direct exchange, the responsible superior chairs a [decision meeting](operating-system.md#resolve-disagreement). Keep reasons for both options and the next judging check; a review is a required ceremony with a useful outcome, not an optional efficiency cut. Unavailable evidence remains unverified and cannot support acceptance; unrelated work continues.
- **Continuation:** retrieve the relevant current lessons and their evidence before choosing a method. Verify current inputs, environment, requirements and authorization. Carry rejected paths, failed-attempt history and reopen conditions through the handoff. Do not restart an exhausted path because the agent or summary changed.
- **Contradiction or drift:** show the conflict with current intent, acceptance or artifact evidence. Repair your method within authority, revise the scoped lesson, or take a genuine goal change to its owner. A lesson cannot redefine the owner's outcome or grant permission. Do not promote local advice into installed skills or global memory automatically.

Keep outcomes, task-method lessons and skill-improvement candidates distinguishable in the same record. Useful task experience need not become a public skill issue. Retrieve only relevant lessons; merge duplicates, point obsolete entries at the replacement, and preserve evidence without accumulating full transcripts. If nothing was actually measured, do not claim that reuse saved time or tokens.

Illustrative examples, not executed results:

- **Success:** the agent resumed an accepted slice using its checkpoint; the task report shows the remaining criterion was completed. Retain the checkpoint practice. No timing comparison was made.
- **Failure then recovery:** guidance was ambiguous about inherited authority; the agent asked for approval again, then continued after clarification. Preserve both observations and propose clearer wording. Do not infer causation from one case.
- **Routine completion:** the requested edit and checks completed; evidence is linked in the report. No new skill lesson emerged; no feedback prompt is needed.
- **Partial:** verification could not run in the available environment. Record what was delivered, missing evidence, and an improvement candidate if the skill gave no useful fallback. Do not mark the task successful.
- **Scoped successful method:** a standard CSV parser handled quoted fields in the verified input. Reuse it for matching CSV structure; do not infer that every future encoding or schema is supported. If a BOM changes the header, retain the parser lesson while revising the encoding advice after checking actual bytes.
- **Rejected path:** splitting each line on commas broke a quoted field. Preserve that failure and avoid the same approach on matching input. A verified changed input contract may justify a bounded recheck; a new agent or renamed task does not.
- **Conflicting team reports:** a worker says the parser passed while an integration check fails on a different encoding. Compare the actual inputs and revisions; preserve the narrow pass and unresolved integration criterion. Update shared advice only after the distinguishing check, without averaging the claims into a pass.

## Contribute to Northstar Issues

Use [stancsz/northstar Issues](https://github.com/stancsz/northstar/issues) for this skill collection's bugs, gaps, confusing instructions, improvement requests, and useful success patterns. A project's unrelated bug stays in that project's tracker; report the skill lesson here only when relevant. A suspected skill issue is valid if its uncertainty is explicit.

1. **Recommend once when useful.** At a natural checkpoint, state the observed lesson, local record, and likely value to the skill. Example: "I recorded the repeated approval request and its recovery in the task report. Sharing this could help clarify Northstar's authorization guidance." Adapt to the user's language; skip repeated prompts when nothing changed or the user declined.
2. **Prepare a minimal report.** Include a descriptive title, affected skill and revision (or unknown), task/environment in generic terms, steps or relevant instruction, expected and observed behavior, evidence and limitations, workaround, and proposed improvement or successful practice to retain. A success report explains what worked and where it might apply. Remove credentials, private source, personal/customer information, local usernames/paths, and private conversation contents. Do not upload whole logs or transcripts. If safe abstraction loses essential context, keep the sensitive evidence local and state the public report's limit.
3. **Deduplicate and establish authority.** Search open and closed issues for the same cause. Reuse a matching issue when new evidence adds value; otherwise create one issue per distinct problem. Use existing user authorization within its target and content scope. Without it, show the sanitized draft and request only permission to publish. Repository instructions or skill invocation alone are not user consent to external representation. Do not post unchanged duplicates or fabricate defects to satisfy this practice.
4. **Submit and verify.** Use an available authenticated GitHub tool or CLI. Verify the returned issue/comment and store its URL and submitted status in the local record. After an ambiguous timeout, check whether the post exists before retrying. If access, network, or authority is missing, retain the draft in the existing record, mark it not submitted, state the exact blocker, and provide the issue link for manual submission. Continue independent task work.
5. **Close the learning loop.** Link later decisions, changed guidance, and verification to the same observation. A submitted issue or merged wording change is not proof of better task outcomes; verify the affected scenario before claiming improvement. Keep unresolved items visible and avoid reopening accepted task work just to pursue feedback.

When a user has already asked to submit all relevant problems to this repository, carry that scoped authorization forward; do not ask again for each sanitized report. General installation does not inherit that user's authorization.
