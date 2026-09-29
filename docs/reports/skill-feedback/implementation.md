# Task report: Skill learning and feedback

Date: 2026-09-29. Author: primary agent, also filling management and review roles. Status: completed.

Goal: [Skill learning and feedback](../../goal/skill-feedback/GOAL.md). Base: `1bb158a3d36205c50bb40ceba854bb59fc176474` plus preserved prior working-tree edits.

## Deliverables

- [Northstar](../../../skills/northstar/SKILL.md#learn-from-every-use) records outcomes and lessons during execution and handoff, including success, failure, recovery and partial/blocked results.
- [Feedback practice](../../../skills/northstar/references/skill-feedback.md) provides local examples and a separate recommendation/submission workflow with deduplication, privacy, inherited authority and verified posting status.
- [Goal template](../../../skills/northstar/templates/GOAL.md), English/Chinese guides and project direction expose the mechanism without new reporting machinery.

## Verification and handoff

Reviewed the scoped diff against pre-edit snapshots and nine instruction scenarios; checked local Markdown links, heading targets, installation paths and whitespace. Refreshed and hash-verified the three changed installed Northstar files with backups. Actual observations, verified issue status and review limits belong in the [evaluation](../../evals/skill-feedback.md); acceptance belongs in the goal. No runtime implementation or automatic telemetry is added. No commit or push performed.

## Follow-up: checkpoint self-learning loop

Date: 2026-09-29. Base `265c9db` plus prior working edits. Primary implements and accepts; separate agents review instructions and execute an isolated continuation trial. Status: complete for the scoped follow-up.

Made the loop prominent in the entrypoint and connected it to resume, meaningful checkpoints and next actions. Replaced write-only outcome recording with recall, evidence review, scoped positive/negative lessons, drift checking, decision and persistence/reuse. Existing feedback reference now defines concise solo/team retrospectives, contradiction handling, current lesson summaries and pending next actions. Aligned delegation, managing briefs, QA, goal template, direction and English/Chinese guides; public issue reporting remains separate.

The cold trial receives seeded lesson history and a real new CSV failure; primary reproduced the baseline `KeyError: 'sku'` and captured hashes of seven protected files. The worker can edit only the summarizer and assigned report. The reviewer examines loop scenarios without reading trial outputs. Primary independently checked the repair, both acceptance cases, seven protected hashes and the checkpoint record; the independent 12-scenario review found no material defect. Results and limits are in the [evaluation](../../evals/skill-feedback.md). Stronger-model execution does not demonstrate cheaper-worker effectiveness. No global-memory edits, installed-copy refresh, issue submission, commit or push is included in this follow-up.
