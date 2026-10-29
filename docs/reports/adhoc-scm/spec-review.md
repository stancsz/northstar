# Independent Spec Kit review: Northstar-aligned task SCM

Date: 2026-10-22. Reviewer: GPT-6 Luna subagent, nonauthor. Spec author: primary agent. Scope: workflow design only; no implementation or real-project pilot was reviewed.

## Review target and method

- Spec: [`docs/northstar/adhoc-scm.md`](../../northstar/adhoc-scm.md), SHA-256 `3F3517D8F0F53090C89F663FAEEC39E64031EDC5F0286428264F86A49F534F3E` at final inspection.
- Context: owner clarified “synchronous” means a source-control workflow in step with project goals/tasks/review/integration and selected a workflow-level Northstar design. The repo is skills-only.
- Schema: confirmed no `.specify/` directory or local constitution in this checkout. Reviewed against Northstar's optional eight-section profile and the required [Spec Kit bridge](../../../skills/northstar/references/spec-kit.md), not a claim of running Spec Kit CLI.
- Evidence inspected: current Northstar coordination/QA instructions; [Anthropic Scion post](https://www.anthropic.com/research/redesigning-source-control); [official Google Research record for the 2016 monorepo paper](https://research.google.com/pubs/pub45424.html); supplied [Piper Wikipedia page](https://en.wikipedia.org/wiki/Piper_(source_control_system)); [Sapling Smartlog](https://sapling-scm.com/docs/overview/smartlog/) and [stack guide](https://sapling-scm.com/docs/overview/stacks/); the supplied [Anthropic X post](https://x.com/AnthropicAI/status/2110047081414987957) returned HTTP 403.
- I read the spec and goal/research handoff before reaching findings. I did not edit either.

## Pass 1 — Structural

**Result: NOT PASS — repair two broken links.**

- **Must fix — wrong goal anchor.** In §7, the Advisor receipt link targets `../goal/adhoc-scm/GOAL.md#advice-and-decision`, but the goal's heading is “Evidence and decision,” so the generated anchor is `#evidence-and-decision`. A click from the spec does not land on the cited evidence.
- **Must fix — malformed reports-index target.** `docs/reports/README.md` contains `[independent Spec Kit review](adhoc-scm/spec-review.md, pending)`. The comma and “pending” are inside the target, so it resolves to a nonexistent path even after this report exists. Keep the destination as `adhoc-scm/spec-review.md` and put “pending” outside the link or update its status.
- **Pass — profile structure.** Sections 1–8 are present. All seven FRs map to at least one SC; all five SCs map back to FRs. Q-001–Q-004 identify owners/statuses. The profile is correctly distinguished from universal Spec Kit requirements.
- **Unverified/expected pending target.** The spec's link to this review report resolved only once this assigned report was written; no defect remains for that target itself.

## Pass 2 — Evidence and privacy

**Result: NOT PASS — one unsupported benefit statement.**

- **Must fix — claim is stated as an observed result.** The INT-001 rationale says “This reduces scope collisions, stale approvals, lost recovery context, and handoffs that cannot be resumed.” Northstar has no measured SCM failure rate, and the spec later says no workflow pilot has run. Recast this as an intended risk reduction or hypothesis. Do not present it as an observed effect.
- **Pass — source fit after the author corrected the Google citation.** The earlier Google Cloud PDF was about ML-generated code-review suggestions, not Piper; that was an actual citation error. The current spec instead links Google's official publication record for Potvin and Levenberg's 2016 monorepo article. Its abstract supports broad claims about the monorepo, custom repository and trade-offs. It does not support a detailed approval/ownership claim; the current spec no longer makes one. Keep Piper details attributed to the supplied secondary page as the spec does.
- **Pass — Scion scope.** The official article explicitly describes its unusual scale/workload and says Git remains suitable for the vast majority of repositories; the spec appropriately rejects transferring its server/storage design to Northstar.
- **Pass — Sapling scope.** The current official docs support the focused graph and stacked-edit/recovery examples. The spec treats them as inspiration and does not claim Northstar needs Sapling or its unsupported server/filesystem.
- **Unverified — X post.** The reader returned 403; the spec accurately records that no recommendation relies on the unseen post.
- **Pass — proposed criteria are inspectable.** SC-001–SC-005 name observable cases and a verifier, with implementation outcomes explicitly marked untested. They are workflow hypotheses, not measured results.
- **Pass — privacy scan.** The workflow spec contains public links, generic role names, and no credential, customer data, or private identity. No privacy blocker found.

## Pass 3 — Adversarial

**Result: NOT PASS — the resumable and synchronized contract can be falsely satisfied.**

### Must fix

- **FR-003 / SC-001 — uncommitted work can disappear.** A worker can edit files, report a “pending diff,” and then lose access to a temporary worktree. Git does not preserve an uncommitted diff merely because the report mentions it. That implementation would satisfy the assignment to record diff/status but fail the promised successor-resume behavior. Specify that handoff content is persisted in a task-owned Git revision or another durable, recoverable artifact with an identity; never use a temporary worktree path as the recovery mechanism.
- **FR-001 / FR-007 / SC-002 — dirty starting state is undefined.** A base commit does not identify pre-existing tracked edits or untracked user files. Creating a worktree from that base omits those edits; an overbroad clean/stash/delete can destroy them. Define the safe start rule: inspect and record dirty/untracked state, preserve it, and either isolate only committed content or stop/reconcile assignment before touching those files. Exercise that boundary in the pilot.
- **FR-002 / SC-002 — overlap detection has no decision point.** The design says shared paths have one active writer and asks that overlap be detected, but it does not specify who checks assigned scopes and actual changed paths, or what happens when a worker edits outside scope. Add the minimal rule: compare scopes before parallel assignment and compare the candidate's changed paths before review/integration; suspend/sequence/re-scope any overlap or out-of-scope change without discarding either worktree.
- **Journey/FR-005 — lifecycle is implicit.** An implementation can update the goal when convenient while Git advances independently because no ordered state transitions or transition owner are defined. State the minimum transitions and the record/Git update required at each: assigned(base/scope) → working/checkpointed → handed-off/reviewing → accepted(candidate identity) or returned → integrated(integrated identity), with stale review and recovery/abandon handling. This is the core “in sync with the project” contract.
- **FR-004–006 / SC-003 — exact reviewed content at integration is not concretely identified.** “Candidate head (or an equivalent exact diff identity)” leaves the identity implementation-defined; “compare ... integrated revision” does not say what proves equivalence after squash/rebase. Define the invariant: bind approval to exact base and candidate content identity (for example, base plus tree/diff identity); integrate that exact reviewed candidate, or make any changed base/content stale and obtain a nonauthor recheck. A new integrated SHA alone is insufficient, as the spec already recognizes.

### Suggestions

- Keep the pilot's two tasks genuinely independent until one task's review is complete, then move the base through the second task and require stale status. If the integration changes content, the reviewer must see the resulting candidate before acceptance. This will isolate stale-approval behavior from ordinary merge-conflict repair.
- Since no CLI or product is in scope, express lifecycle transitions as a concise table/state rule in the design; do not add a database schema or runtime state machine.

## Verdict

**Spec readiness: NOT READY.** The draft has a promising lean direction—Git remains canonical, task/review records stay project-owned, and approvals bind to revisions—but the broken references, unsupported benefit claim, and gaps around durable checkpoints, dirty workspaces, scope overlap, state transitions, and exact integration identity leave material requirements open. No implementation readiness verdict applies; no implementation was reviewed.

**Next action for the spec author:** repair these findings in `adhoc-scm.md`, fix the report index/anchor, then have a nonauthor recheck the changed portions of passes 1–3. Preserve this report as evidence of the original review. After spec readiness, pilot the post-review base movement and interruption cases on a real eligible project before adding any automation/tooling.

# Re-review — 2026-10-22

**Relationship to first review:** targeted independent re-review by the same nonauthor reviewer. The original NOT READY findings above remain intact as history; this section records the repaired revision and supersedes that verdict for the current spec text. I did not edit the spec or other product documents.

**Artifact:** `docs/northstar/adhoc-scm.md` — SHA-256 `03F4856E8D212A79E58536C2E534C78BB1C93ABCBE6F2CA8D6F58B0F23E50B61`.

## Pass 1 — Structural

**Result: PASS.** The draft has all eight sections in Northstar's optional profile, and correctly says this repository has no installed Spec Kit feature layout or local constitution. Checks confirmed `.specify/` and `specs/` are absent; no Spec Kit CLI run or universal eight-section requirement is claimed. All seven FRs link to one or more SCs, and all five SCs link back to FRs. KE/A/Q sections and stable IDs are present. The former `#evidence-and-decision` reference is no longer used; current local links and anchors in the spec, goal, and reports index resolve. `docs/reports/README.md` now links to `adhoc-scm/spec-review.md` as a valid target.

## Pass 2 — Evidence and privacy

**Result: PASS, with X content unverified.**

- The intended benefit is now explicitly described as intended and unmeasured; the spec does not present reduced collisions, stale approvals, lost context, or failed handoffs as observed outcomes.
- The official [Anthropic engineering article](https://www.anthropic.com/research/redesigning-source-control) supports the stated Scion workload and its caveat that Git remains appropriate for most repositories. The spec does not transfer Scion's unusual scale architecture to Northstar.
- Google's [official research publication record](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/) identifies the 2016 monorepo paper and describes its scope as repository scale, systems/workflows, reasons, and trade-offs. The design uses it only for that broader context. It no longer claims the source proves a directory-owner/technical-review distinction. The correction note in the research report accurately records the unrelated prior citation and removed claim.
- The supplied Piper account remains labeled as secondary Wikipedia material; Sapling's [Smartlog](https://sapling-scm.com/docs/overview/smartlog/) and [commit stack](https://sapling-scm.com/docs/overview/stacks/) docs were directly inspected and support the limited interaction/recoverability inspirations claimed.
- The supplied [Anthropic X post](https://x.com/AnthropicAI/status/2110047081414987957) still returns HTTP 403. Its contents remain unverified and are not used as evidence for a requirement.
- Requirements cite Northstar owner/project rules or clearly label the advisor input/design inference. SCs name observable cases and a verifier while labeling all pilot outcomes unobserved. The spec and this report contain no credentials, customer data, or private identity; no privacy blocker found.

## Pass 3 — Adversarial

**Result: PASS for spec wording and proposed discriminators.** No remaining must-fix finding. The pilot remains future evidence, not a completed workflow check.

- **FR-001 / SC-001, SC-002, SC-004 — assignment and dirty state:** the assignment names owner, declared scope, dependencies, and base; checks status and relevant untracked files before workspace creation; and stops for owner reconciliation when dirty content overlaps the scope or is required input. An implementation that silently drops that input or edits it would fail the stated checks.
- **FR-002 / SC-002, SC-004 — overlapping and out-of-scope writes:** the supervisor compares declared scopes before parallel assignment and actual changed paths against scope and concurrent tasks before review/integration. The supervisor contains and sequences/re-scopes conflicts while preserving both candidates. The spec names who decides and when; a path-overlap flag without a resolution would not meet it.
- **FR-003 / SC-001, SC-005 — checkpoint persistence:** interruption, reassignment, review, and abandonment require a task-owned draft commit or other durable versioned artifact with stable identity. A report or temporary worktree path alone explicitly fails. The successor-resume check distinguishes a surviving candidate from a status-only handoff.
- **FR-004 / SC-003, SC-004 — independent review identity:** verdicts include the exact base commit and candidate tree object ID, plus commit and changed paths for navigation; worker self-acceptance is prohibited. A reviewer cannot pass by naming only a branch or mutable worktree.
- **FR-005 / SC-003, SC-004 — stale approvals and rewritten commits:** either base or tree change invalidates the verdict; recheck is by a nonauthor against current base and original acceptance. A rewritten commit SHA alone is insufficient. The same tree under another commit SHA is accepted only with unchanged reviewed base. These provide implementable comparison values and explicit stale behavior.
- **FR-006 / SC-003, SC-005 — integration:** supervisor records integrated commit/tree and checks the integrated tree against the accepted tree. A mismatch or changed base returns for nonauthor review, so a squash/rebase cannot pass merely because a new commit exists. Integrated behavior still needs the proposed pilot check.
- **FR-007 / SC-001, SC-002, SC-005 — preservation and cleanup:** unrelated/relevant dirty and untracked content and useful checkpoints must survive start, handoff, rebase, and abandonment; cleanup is limited to owned disposable work after durable evidence is retained. SC-001 and SC-002 inspect persisted recovery and byte-for-byte input preservation.
- **SC-001–SC-005 — criterion attacks:** status-only or vanished-worktree handoffs fail SC-001; broad cleanup or unisolated overlapping paths fail SC-002; same-SHA/different-tree or moved-base approvals fail SC-003; self-acceptance/stale acceptance fail SC-004; a new parallel ledger/service fails SC-005. Each criterion includes an observable case and verifier, and the outcome remains explicitly proposed rather than reported as measured.

**Suggestion, not a blocker — transition edges:** the lifecycle table gives ordered states, per-state evidence, and transition owners, while SC-004 requires testing unauthorized/out-of-order transitions. A later protocol revision could make legal edges and the `Returned`-to-`Working` repair loop explicit in a small from/to table, especially if multiple projects interpret the row order differently. The current ordered lifecycle, owners, accepted/returned outcomes, and integration/staleness guards are sufficient for this design-spec pass; no runtime enforcement is claimed.

## Verdict and next action

**Spec readiness: READY, for the inspected workflow design only.** The earlier structural, evidence, and functional blockers are repaired in the pinned revision. This does not establish workflow or implementation readiness: SC-001–SC-005 remain proposed pilot criteria, and Q-004's concurrent-task/base-movement/interruption pilot has not run. The project owner should update the goal/spec review status and select an eligible isolated task pair before claiming the protocol works in practice.

# Post-review status/link revision check — 2026-10-22

**Artifact checked:** `docs/northstar/adhoc-scm.md` — SHA-256 `3A62A9AD0F32C68FDDAB423D04CF23F13323FA93EE62656B4AFC2ADA802FB862`.

The post-review edits only update the status and delivery/review references. The status accurately distinguishes **workflow design READY** from the **real-task pilot pending**; the table links the existing independent review and labels it READY for design only. All local links in the spec, goal, and reports index resolve. No new structural, evidence/privacy, or adversarial blocker is introduced. The unmeasured-benefit statement, source attribution, exact base/tree/staleness rules, lifecycle and preservation requirements remain as reviewed.

**Current revision verdict: READY for the workflow design only.** This check does not change the earlier verdict or claim pilot/implementation evidence.
