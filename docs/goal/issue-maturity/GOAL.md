# Goal: Resolve open issues and verify useful skill behavior

Date: 2026-10-21. Status: implementation independently accepted; publication recorded in [PR #6](https://github.com/stancsz/northstar/pull/6). Base: `293f230dfcf1f5db360ce17901e4a594fc66e451` plus preserved pre-existing edits.

## Outcome and acceptance

The owner requests all open GitHub issues implemented carefully, effectiveness evaluated, Advisor council guidance on maturity executed, then shipped through prepared and merged PRs with issues closed after merge. Snapshot: [#3](https://github.com/stancsz/northstar/issues/3), [#4](https://github.com/stancsz/northstar/issues/4), [#5](https://github.com/stancsz/northstar/issues/5); all comment lists empty at intake.

- #3: preserve useful existing learning/feedback implementation; exercise lesson reuse, failures, privacy, deduplication and truthful submission status without unsolicited external posting.
- #4: canonical goals remain project-owned, existing conventions win, installation directories are excluded, and write-denial recovery preserves ownership and evidence.
- #5: optional spec-kit integration supports three ordered nonauthor passes (structure, evidence/privacy, adversarial); map requirements to actual checks and distinguish custom profiles from upstream defaults. Spec approval never proves implementation acceptance.
- Evaluate bounded cold agent behavior and independent review, not just document coverage. Report missing live/longitudinal/cost evidence honestly; fix material findings before publication.
- Use the installed caller and exact council routes. Preserve distinct Gemini and Sol opinions, failures, usage and whether advice changes an action. Implement a bounded council-recommended maturity improvement within the above mandate.

## Ownership and tasks

Primary owns integration, Northstar routing, QA/spec integration, shared indexes, this goal and GitHub publication. A bounded worker owns goal-storage wording and its report. Separate cold workers execute probes in `tmp/issues-20261021/`; a nonauthor reviewer owns the acceptance report only. No service, global installation or unrelated pre-existing changes are in the release.

Scratch: `tmp/issues-20261021/`; initial status, full baseline patch and tracked hashes are saved there. Checkout size measured 19,164,530 bytes before small fixtures, well below the shared 100 GB ceiling. No additional checkout yet.

## Execution and continuation

- Intended next action before consultation: repair goal ownership, integrate spec review, run cold probes, independently review, publish focused changes. Latest owner update requires PR/merge rather than direct-main publication.
- Initial council call failed with HTTP 401 (missing caller API key); receipt retained. The existing experts service `.env` supplied its own matching key in process environment only; the corrected invocation succeeded, without route/model fallback or secret disclosure.
- Upstream spec-kit README and spec template inspected on 2026-10-21. Issue #5's eight sections/KE/A/Q/Articles IV and IX describe a custom profile, not universal upstream rules.
- Initial checkpoint required council evidence, issue implementation and behavioral checks; the following results supersede that pending state.

- Both council invocations completed after the one corrected auth setup. [Evaluation](../../evals/issue-maturity.md) preserves model-specific views and 9,292 reported successful provider tokens; full cost remains unknown. Council selected compact receipt guidance and later the narrow existing Gemini 4 compatibility update as a release dependency. No service/global changes.
- All issue guidance is implemented. Six frozen cold cases met bounded criteria; a seventh discovered artifact/readiness ambiguity, which primary repaired and a nonauthor rechecked. Seeded fixture defects were repaired separately and independently verified. Offline caller/reader checks passed (38 Python, two Node). At PR preparation, the remaining publication checks were merge and verified issue closure; the linked PR and issue events record their actual state.

## Acceptance and publication

The independent [release review](../../reports/issue-maturity/review.md) inspected the 29-path staged payload, actual probe artifacts, full/detached link closure and exact source fingerprints, then reran 38 Python and two Node tests against staged source. No material blockers remained; scoped READY. Primary inspected its evidence and accepts the implementation without claiming comparative effectiveness. This applies the artifact-scoped judging lesson from probe 7.

User authorization covers creating and merging the PR and closing #3–#5 only after merge. GitHub's associated PR merge event and issue closing references record the actual publication transition; local READY alone is not shipment. Unrelated baseline work stays unstaged and unchanged.

Publication record: [PR #6](https://github.com/stancsz/northstar/pull/6), prepared from accepted implementation commit `538e80cc4bf38eeb4962f56eb81e3bcb2280b49a`, with closing references to all three issues. This record-only follow-up adds traceability without changing reviewed source or repeating its tests. The PR's merged commit and linked issue state, verified by the publishing agent, are authoritative for shipment.

## Learning checkpoint

Retrieve existing [learning evaluation](../../evals/skill-feedback.md): walkthroughs differ from executed probes, and one cold trial establishes narrow feasibility only. Apply that distinction to this release. Preserve the auth failure; retry only after correcting its demonstrated cause. Publication must isolate current changes from the dirty baseline.
