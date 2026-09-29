# Goal: Learn from skill use and contribute feedback

Status: done. Date: 2026-09-29. Base: `1bb158a3d36205c50bb40ceba854bb59fc176474` plus existing uncommitted coordinated-delivery changes.

## Outcome and acceptance

The owner requests two mechanisms: record successful and unsuccessful uses and improvement opportunities during work and at handoff; separately recommend how those records can improve the skill and submit skill problems to `stancsz/northstar` Issues.

- Record material observations during work and every final/partial/blocked outcome in existing project records, with evidence and limits.
- Provide a separate user-facing feedback recommendation and a concrete issue workflow covering authorization, privacy, duplicates, and failed submissions.
- Keep installed guidance self-contained within the skill directory; expose the practice through the goal template and English/Chinese guides.
- Review realistic scenarios, local Markdown links, installation paths and whitespace; distinguish document review from behavioral testing.
- Record and submit the observed missing-feedback workflow using the owner's explicit authorization. Verify its issue URL.

## Ownership and execution

Primary agent owns direction, indexes, skill implementation, report, review and acceptance; no delegation. Write scope: Northstar entrypoint/reference/template, English/Chinese guides, direction and category indexes, and this goal's report/evaluation. Preserve all pre-existing edits. No commit or push requested.

Task: implement and review the two mechanisms. [Worker report](../../reports/skill-feedback/implementation.md). [Evaluation and skill learning](../../evals/skill-feedback.md).

## Acceptance

Primary agent, filling all roles, accepts the scoped documentation change after inspecting the report, actual additions and nine scenario walkthroughs. Local links/anchors and whitespace checks passed. Refreshed the three affected files in the existing local Northstar installation after confirming the old entrypoint/template matched the starting source, backing them up, and verifying new SHA256 equality. Existing changes are preserved; no commit or push performed.

The observed feedback-workflow gap was submitted and read back as [Issue #3](https://github.com/stancsz/northstar/issues/3) under the owner's explicit authorization. It remains open for upstream delivery and real-use follow-up. See the evaluation for the single skill-learning record, verification details and limits; document acceptance does not establish future agent compliance.

## Follow-up: checkpoint self-learning and drift control (2026-09-29)

Status: done for this scoped follow-up. Base `265c9db305d4f42f1e6d964f4a2e76a2aa80df97` plus earlier uncommitted feedback, autonomy and cross-domain changes, all preserved. The owner requires accumulated what-works/what-does-not-work experience and a short retrospective at checkpoints for both solo agents and teams, so continuation uses evidence instead of drifting.

Primary owns implementation, shared docs/indexes and acceptance. Scope: core loop and entry/resume guidance, existing feedback reference, delegation/QA connections, templates, English/Chinese guides, direction and this goal's existing report/evaluation. Independent reviewer owns `tmp/checkpoint-learning/review.md`. A fresh trial worker owns only `tmp/checkpoint-learning/trial/summarize.py` and its `REPORT.md`; primary owns fixture inputs/checks. Reviewer and worker may not delegate. Use existing records, not new reporting machinery.

Acceptance: retrieve scoped lessons before action; review each meaningful checkpoint without per-call meetings; preserve both successful methods and rejected paths with evidence/applicability/reopening conditions; check intent/acceptance/authority drift; decide the next action and actually feed lessons into it; supersede contradicted advice without erasing history. Solo review is explicit, team review uses affected owners and one accepting decision, and missing evidence cannot become a pass. No retry reset, global-memory/installed-skill mutation, public posting, commit or push.

Validation: independent scenario review and one isolated fresh-agent continuation trial. Seed historical lesson records, including a valid parsing method, a rejected shortcut and overly broad encoding advice; introduce a new fixture that contradicts the encoding advice. Worker must inspect/repair the real local behavior, preserve input/check/note hashes and intent, retain/narrow/supersede lessons as evidence warrants, and record a checkpoint decision. This short synthetic trial does not establish long-session drift prevention or team-wide behavioral reliability.

Acceptance: primary inspected the independent 12-scenario review, actual one-line encoding repair and checkpoint report, then independently reran both unchanged acceptance cases and verified all seven protected-file hashes. Documentation checks passed. Accepted as a scoped learning-loop implementation; stronger-model execution is not proof of economical delegation. The subsequent operating-system work adds mixed-capability validation. See the evaluation for evidence and limits.
