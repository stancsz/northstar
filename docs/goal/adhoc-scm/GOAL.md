# Goal: design a Northstar-aligned task SCM workflow

Date: 2026-10-22. Status: **workflow design READY after independent three-pass review; real-task pilot deferred.** The owner clarified that the goal is to study SCM patterns and design a source-control workflow that stays synchronized with Northstar's project loop. They selected a workflow-level design in this skills-only repository.

## Outcome and acceptance

- **Owner outcome:** a practical, lightweight SCM method that connects Northstar project goals, delegated tasks, Git changes, handoffs, nonauthor review, and final integration without drifting out of sync.
- **Current increment:** source-backed workflow design using a Spec Kit profile. No app or runtime implementation is authorized in this repo.
- **Must pass:** map project state and revision state; define a recoverable task lifecycle; bind independent review to the exact candidate and invalidate stale approval; preserve existing records/Git as sources of truth; challenge the design through three ordered nonauthor passes; state a concrete pilot that could falsify the design.
- **Constraints:** this repo is skills-only; preserve all existing user changes, project-specific records, authorization, independent acceptance, and one-writer scopes. Do not create a duplicate task ledger, custom VCS, global lock, app/runtime, or claim unmeasured benefits.
- **Direction:** [Northstar direction](../../northstar/README.md), [current next proof](../../northstar/next-proof.md), [Spec Kit bridge](../../../skills/northstar/references/spec-kit.md), [design draft](../../northstar/adhoc-scm.md).

## Ownership and tasks

- **Orchestrator / supervisor:** primary agent; owns the design, goal, index edits, synthesis, and final disposition.
- **Research worker:** `/root/scm_reference_research`; completed read-only research in [reference report](../../reports/adhoc-scm/reference-research.md). No shared indexes or source files were edited by worker.
- **Spec author:** primary agent; authored [workflow design](../../northstar/adhoc-scm.md).
- **Independent reviewer:** nonauthor GPT-6 Luna subagent; completed the ordered structural, evidence/privacy, and adversarial passes plus a final exact-revision check in [spec-review.md](../../reports/adhoc-scm/spec-review.md); current verdict READY for workflow design only.

## Evidence and decision

The research report inspected the Anthropic Scion article, Sapling docs and repository, the supplied Piper summary plus Google's official 2016 monorepo paper, and the supplied X post (403; contents unverified). A mistaken Google PDF citation to an unrelated ML review paper was caught and corrected; the unsupported approval-flow claim was removed and the error retained in the report's correction note. Northstar's repo has no local Spec Kit CLI/feature layout or constitution; per the bridge, this design uses the optional eight-section profile. This is a workflow specification only, not proof of implementation or use.

The [Advisor council receipt](../../evals/adhoc-scm/advisor-council.json) recommends task changesets in existing project records over a new ledger. Its essential links are task/owner/scope, base/head, handoff/recovery, exact independent review, integration provenance, and integrated-result inspection. Temporary worktree paths are not durable identity; any changed base/diff makes prior review stale. Gemini and Sol independently identified the post-review rebase as the strongest falsification case. Usage: Gemini 3,267 tokens; GPT-6.1 Sol 912; advice changed the design from a generic Git convention to an explicit exact-candidate changeset and stale-review invariant. These are provider-reported call totals, not full task cost.

### Ordered execution plan

1. **Finish the spec review.** First three-pass review returned NOT READY. The author repaired the reported issues; the same nonauthor reviewer rechecked changed portions of structure, evidence/privacy, and adversarial scrutiny while preserving original criteria and the first report. Verdict: READY for workflow design only.
2. **Decide design readiness.** Orchestrator checked the independent report and integrated doc. Deliver the workflow-level protocol as a design hypothesis; implementation and effectiveness remain unverified.
3. **Run a real-task falsification pilot later.** Use two related tasks that share an interface; bind each to a base and writer scope; complete one review; move the base through the second task/rebase; confirm stale approval blocks integration and a nonauthor rechecks the exact current candidate. Inspect recovery and integrated behavior. If existing Git and task records cannot do this without duplicate state, reject or narrow the design. No eligible project/task pair has been selected yet, so the pilot is not part of this delivery.

## Review and acceptance

- **First independent result:** NOT READY against design revision SHA-256 `88B6AE92E8FF3CC0B563C46B96A30C759D489DA47BEEF99B24303AD70185E1ED`. It found a wrong goal anchor, a malformed report-index target (fixed before re-review), an unmeasured claimed benefit, missing durable checkpoint behavior, undefined dirty/untracked start handling, missing overlap checks and transitions, and ambiguous exact review/integration identity. The detailed report preserves the original findings.
- **Final independent result:** READY for current design revision SHA-256 `3A62A9AD0F32C68FDDAB423D04CF23F13323FA93EE62656B4AFC2ADA802FB862`; structure, evidence/privacy, and adversarial passes pass. Reviewer suggested a future explicit legal-transition edge table but judged the current ordered states, owners, and guards sufficient for design readiness. See [review](../../reports/adhoc-scm/spec-review.md).
- **Primary known uncertainty:** design's sufficiency and usability are untested on a real Northstar-assisted task. A passing spec review establishes only specification readiness, not workflow effectiveness or product need.
- **Learning:** copying Scion's service architecture would solve an unobserved scaling problem. Preserve task edits as a durable task-owned revision at handoff; report text alone cannot recover an uncommitted diff. Bind review to both base and content tree, inspect dirty state and actual changed paths, and record transitions in existing project records. Sapling's focused graph/recovery ideas remain optional UI inspiration. The X post remained inaccessible. Reopen if primary evidence arrives or a real task demonstrates a failure the protocol does not address.
- **Claude Code adapter:** inspected its applicable skill and local CLI; effective base URL is a custom endpoint while credential source/intent was not established by `claude auth status`. Per the adapter's routing boundary, no request was sent. The Codex Luna research/review delegation is used instead.

## Acceptance record

- Research handoff inspected: report contains direct reference citations, Northstar-specific design inference, limits, and pilot proposal.
- Advisor: council completed; recommendation incorporated; receipt records 3,267 Gemini and 912 Sol tokens.
- Spec review: initial NOT READY findings, repaired-revision verdict, and exact current-revision READY check are preserved in [spec-review.md](../../reports/adhoc-scm/spec-review.md).
- Workflow pilot: deferred pending real eligible tasks; no claims of synchrony, prevention, speedup, or effectiveness are made.
