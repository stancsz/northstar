# Skill learning and feedback evaluation

Date: 2026-09-29. Goal: [Skill learning and feedback](../goal/skill-feedback/GOAL.md). Evaluated base: `1bb158a3d36205c50bb40ceba854bb59fc176474` plus pre-existing changes and this task's uncommitted diff. Reviewer: implementation agent; not independent.

## Scenario review

Manual inspection of the entrypoint, reference, goal template and user guides against these cases; these are document walkthroughs, not agent execution trials:

| Scenario | Guidance inspected and conclusion |
| --- | --- |
| Successful completion | Delivery requires an outcome entry; helpful practices retain evidence without invented timing/token savings. |
| Failure, recovery, partial or blocked work | Material observations are captured during work and handoff; recovery retains failed history and missing evidence stays explicit. |
| Routine use with no insight | Brief outcome required; no fabricated lesson or repetitive feedback prompt. |
| Valuable new lesson | Separate recommendation names the local record and how the lesson could improve Northstar. |
| Existing authority versus ordinary installation | Explicit issue authorization is reused; installing the skill does not authorize public posting. |
| Duplicate or ambiguous submission | Search open/closed issues and check for a successful post before retrying; unchanged duplicates are skipped. |
| Sensitive evidence or missing tools | Sanitized minimal report; retain local draft and state not submitted when blocked. |
| Application bug unrelated to the skill | Keep the defect in the application tracker; only relevant skill lessons go upstream. |
| Standalone skill installation | Detailed practice is in the copied `northstar/references/` directory and links back to its entrypoint. |

## Skill learning from this task

Expected: Northstar should learn from both good and bad outcomes and direct actionable feedback to its issue tracker. Observed gap: before this change, the entrypoint required delivery/review records but had no explicit every-use skill lesson or upstream feedback workflow. Evidence: entrypoint at the evaluated base and the scoped additions in this working tree. This is a documentation gap, not evidence that prior agents always failed to learn.

What helped: existing goal/report/evaluation ownership provides a place for the record, so no separate diary or runtime collector is needed. Repair: explicit learning and feedback sections, with detail packaged in the skill reference. Follow-up: review the affected scenarios in real future tasks before claiming improved behavior, lower cost or higher success rates. Submitted [Issue #3](https://github.com/stancsz/northstar/issues/3) after an open/closed issue listing returned no matches; read back its title, body, URL and open state with GitHub CLI. The user's current request authorized this sanitized submission. Upstream commit/push and real-use evaluation remain future work.

## Checks and limitations

Checked 43 Markdown files, 207 local links and 36 heading targets: all resolved. Inspected installation paths and confirmed the new reference travels inside the copied skill directory. Refreshed `SKILL.md`, `templates/GOAL.md` and `references/skill-feedback.md` in the existing local Codex Northstar installation with backups; all three match source SHA256. `docs/` has no loose files. The scoped before/after diff preserves pre-existing content except the intentional delivery-step extension. `git diff --check` passed under the repository's normal line-ending configuration.

Inspection setbacks: an unnecessary `core.autocrlf=false` override falsely flagged existing CRLF endings; rerunning with the normal configuration passed without changing those files. The first Python diff display stopped on Windows console encoding after link checks passed; rerunning with `-X utf8` completed the diff inspection. These were inspection-tool issues, not skill defects, and did not justify additional upstream issues.

No build or executable suite exists for this Markdown collection. The nine walkthroughs establish instruction coverage only; they do not prove future compliance, automatic collection or improvement in task outcomes. The real issue submission verifies one authorized reporting path only. Existing unrelated work remains outside this review.

## Follow-up: checkpoint learning and drift control, 2026-09-29

Base `265c9db` plus pre-existing working changes. Primary edits the instructions and owns acceptance. Independent `decision_review` inspects boundary scenarios; fresh `learning_trial` receives no parent conversation and executes one scoped continuation task. Scratch: `tmp/checkpoint-learning/`. No runtime code enters the installable skill collection. Checkout usage before the small fixture was 2,099,579 bytes, including ignored files.

Predeclared behavioral case: old CSV totals passed; a newly supplied UTF-8 BOM input fails. Seeded prior lessons contain a supported standard CSV parser, a rejected comma-splitting shortcut, and an overbroad statement that ordinary UTF-8 works for every export. Worker must repair the real function without changing acceptance/data/history, check old and new inputs, and record what to reuse, avoid or revise with scope/evidence, drift review and next disposition. Primary observed `KeyError: 'sku'` on the new input before delegation and saved seven input/check/history/note hashes. The seeded earlier history is synthetic, not evidence of earlier real runs.

Expected loop improvement: applicable experience should influence the action, contradicted advice should be narrowed/superseded, and the report should preserve a usable next checkpoint. A successful repair alone does not establish these behaviors; primary will inspect both the work and the report. Solo execution is tested; team review remains scenario inspection. There is no control arm, long-session/context-compaction run, automatic memory service or measured cost saving.

Observed: the cold worker retained `csv.DictReader`, avoided the previously rejected comma split, and changed only `utf-8` to `utf-8-sig` in the summarizer. Its report retained L1/L2 and explicitly superseded the overbroad L3 encoding advice, with expected/observed evidence, scope, drift check and next acceptance owner. Primary reran the unchanged check: `2 unchanged acceptance cases passed`; all seven protected-file hashes matched. Independent review covered 12 instruction scenarios and found no material defect. Core skill SHA256 at trial: `3C1A1A439B4F2988474F9947445EBD7B4C4B2EBC69D85F2D6CEE4EC80F1D1270`.

Checked 44 Markdown files, 234 local links and 52 heading links, three skill metadata validations, installation source paths and `git diff --check`: passed. This records the pre-operating-system revision, not subsequent edits.

Learning: the scoped loop was followed in this one cold continuation. Preserve the distinction between supported parser choice and input-encoding scope. Mandatory reviews must retain decision value, not be dismissed as ceremony. The owner subsequently rejected all-strong-model testing as evidence of efficiency; this trial is a functional observation only, and provides no cheaper-worker or cost comparison. Subsequent validation is recorded under the operating-system goal.
