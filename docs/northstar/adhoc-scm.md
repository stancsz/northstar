# Northstar-aligned task changesets

Status: **workflow design READY after independent three-pass review; real-task pilot pending.** This is a workflow specification for synchronizing Northstar project work with its source history. It is not an application spec, runtime, or a claim that a new SCM has been implemented.

This draft uses Northstar's optional [eight-section Spec Kit profile](../../skills/independent-qa/templates/spec-profile.md) because this repository has no installed Spec Kit feature structure or local constitution. The [Spec Kit bridge](../../skills/northstar/references/spec-kit.md) is Markdown integration; the three ordered nonauthor passes still apply.

## 1. Intent and evidence

### INT-001 — Keep project state and source changes in sync

When Northstar delegates work in a project, every accepted change should be traceable from that project's existing goal and task assignment, through the exact source revision and handoff, to independent review and integration. The intended benefit is to reduce scope collisions, stale approvals, lost recovery context, and unusable handoffs; Northstar has not measured this effect.

The Northstar owner explicitly requests a workflow-level SCM design that operates in sync with the project's Northstar loop. The Northstar direction requires project-owned records, one writer per scope, durable reports, independent acceptance, and integrated-result review. ([Owner request](../goal/adhoc-scm/GOAL.md), [Northstar direction](README.md), [subagent coordination](../../skills/subagent-orchestration/SKILL.md))

### Evidence and references

- Anthropic's [Scion engineering post](https://www.anthropic.com/research/redesigning-source-control) describes an online, server-centered SCM for Anthropic's unusually large agent-heavy monorepo. It explicitly says Git remains appropriate for most repositories and Scion is not a general replacement. Its transferable lesson here is to design around observed workflow constraints and expose reviewable change intent; its storage and scale architecture is unsupported for Northstar's needs.
- The supplied [Google Piper overview](https://en.wikipedia.org/wiki/Piper_(source_control_system)) is a secondary page, not an official product manual. Google's [official 2016 monorepo paper](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/) describes the rationale, systems, trade-offs, and workflow behind its unusually large shared repository. Its scale does not establish that Piper's centralized infrastructure is a requirement for Northstar.
- Meta's [Sapling site](https://sapling-scm.com/), [Smartlog guide](https://sapling-scm.com/docs/overview/smartlog/), and [stack guide](https://sapling-scm.com/docs/overview/stacks/) demonstrate Git interoperability, a focused view of related work, and recoverable stacked edits. These are interaction ideas; adopting Sapling itself is not required.
- The supplied [Anthropic X post](https://x.com/AnthropicAI/status/2110047081414987957) returned HTTP 403 through the available reader. Its contents are unverified and no requirement depends on them.

No measured Northstar SCM failure rate or performance bottleneck is established. A product/tool is not justified until a real workflow shows that the protocol is insufficient.

## 2. Scope and user journeys

### Journey A — Assign and isolate work

**Given** an existing project goal and an authorized task, **when** a supervisor assigns it, **then** the assignment identifies the task/goal, one writer, owned paths or artifacts, dependencies, and the starting Git commit. Before creating or reusing a workspace, the supervisor inspects `git status --short`. A new isolated worktree starts from committed content and does not silently inherit dirty or untracked files from another tree. The worktree path is only a temporary locator.

### Journey B — Checkpoint and hand off

**Given** work in progress or an interruption, **when** the worker checkpoints or hands off, **then** the work is first persisted as a task-owned draft Git commit (or another durable, versioned artifact with a stable identity) and the existing goal/task/report records that identity, changed paths, checks/observations, recovery history, and next action. A report that merely describes an uncommitted diff does not make the diff recoverable. No separate ledger is introduced.

### Journey C — Review and integrate

**Given** a proposed task changeset, **when** an independent reviewer accepts it, **then** its verdict names the exact base commit and candidate tree identity. The supervisor integrates that reviewed tree and records the integrated commit/tree in the existing goal/task record. A changed base or tree invalidates the prior review until a nonauthor rechecks the current candidate.

### Journey D — Resolve overlap

**Given** two tasks with overlapping paths or a moving shared base, **when** conflict is detected, **then** the supervisor chooses order, dependencies, or a rebase/repair and preserves each task's prior checkpoint and review history. The system does not solve this with a global write lock.

### Minimum task lifecycle

Record each transition in the existing project task/goal record or its worker report; do not create a parallel status store. The supervisor owns assignment, review routing, stale-state resolution, and integration. The worker owns task checkpoints and handoff. The nonauthor reviewer owns the verdict for the named candidate.

| State | Required synchronized evidence | Transition owner |
| --- | --- | --- |
| **Assigned** | Goal/task ID, one writer, declared paths, dependencies, and base commit; inspect and record relevant dirty/untracked state before workspace creation. | Supervisor |
| **Working / checkpointed** | Current task-owned draft commit or durable versioned artifact plus changed paths and last verified check; checkpoint again before interruption or transfer. | Worker |
| **Handed off / reviewing** | Worker has stopped writing; handoff links the persisted candidate, base, actual paths, checks, recovery checkpoint, and unmet criterion. | Worker, then supervisor |
| **Returned** | Reviewer findings identify the reviewed candidate and failed criteria; old candidate remains recoverable. | Reviewer, then supervisor |
| **Accepted** | Nonauthor verdict names the exact base commit and candidate tree identity and covers the original acceptance criteria. | Nonauthor reviewer |
| **Integrated** | Project record names the integrated commit and tree. The integrated tree must match the accepted tree; if base or tree differs, mark the approval stale and return the candidate for nonauthor review. | Supervisor |
| **Abandoned** | Reason, last durable candidate, and remaining/unmet criteria are recorded before any owned disposable workspace is cleaned up. | Supervisor |

Scope is protocol and lightweight Git usage within an existing project. It does not create a graphical interface, daemon, remote service, database, custom VCS, or new mandatory project folder layout.

## 3. Functional requirements

- **FR-001 — Bind assignment to project state.** Before a delegated task edits files, its existing task/goal record identifies task, accountable owner, exclusive declared write scope, dependencies, and base commit. The assigning supervisor checks current status and relevant untracked files before workspace creation. If dirty state touches the task scope or is required input, stop and reconcile/transfer it with its owner; never discard or silently omit it. Source: Northstar owner and subagent coordination rules. Linked checks: SC-001, SC-002, SC-004.
- **FR-002 — Detect write overlap.** Before parallel assignment, the supervisor compares declared path scopes. Before review and integration, the supervisor compares actual changed paths against each task's declared scope and concurrent tasks' paths. An overlap or out-of-scope edit is contained and sequenced/re-scoped while both task candidates remain recoverable. Source: [Northstar one-writer and worktree rules](../../skills/subagent-orchestration/SKILL.md#documentation-and-repository-hygiene). Linked checks: SC-002, SC-004.
- **FR-003 — Persist checkpoint and handoff.** Before interruption, reassignment, review, or abandonment, task changes are saved in a task-owned draft commit or another durable, versioned project artifact with stable identity. Existing task/report records link the base, persisted candidate, actual changed paths, checks and observations, unmet criterion, recovery history, and next action. A report or temporary worktree path alone does not persist file content. Source: [Northstar handoff and recovery rules](../../skills/northstar/SKILL.md#worker-reports-and-handoffs). Linked checks: SC-001, SC-005.
- **FR-004 — Bind independent review to exact content.** Review evidence names the base commit and candidate tree object ID (the exact content snapshot), plus the candidate commit and changed paths for navigation, and covers original acceptance criteria. A worker cannot accept its own change. Source: [Northstar role separation](../../skills/subagent-orchestration/references/role-profiles.md). Linked checks: SC-003, SC-004.
- **FR-005 — Invalidate stale approval.** If the candidate's base commit or tree identity changes before integration, the approval is stale. The current candidate must receive a nonauthor recheck against the current base and acceptance before integration. A commit SHA recorded after squash/rebase is insufficient unless its tree matches the reviewed tree and its reviewed base remains unchanged. Source: [Independent QA recheck rule](../../skills/independent-qa/SKILL.md#challenge-the-result-then-repair), Advisor council on this design. Linked checks: SC-003, SC-004.
- **FR-006 — Integrate and close the loop.** The supervisor records the integrated commit/tree in the existing task/goal and verifies integrated behavior against the required workflow. Integration is complete only when the integrated tree matches the accepted tree; otherwise return the new candidate to nonauthor review. A task is not complete merely because its worker committed or isolated branch passed. Source: [Northstar integration and acceptance rules](../../skills/subagent-orchestration/SKILL.md#coordinate-to-a-working-result). Linked checks: SC-003, SC-005.
- **FR-007 — Preserve user and worker data.** Starting, handing off, rebasing, or abandoning work must preserve unrelated and relevant dirty/untracked user content and each worker's useful checkpoints. Cleanup may remove only owned, disposable work after its durable content/evidence is retained. Source: [AGENTS.md](../../AGENTS.md). Linked checks: SC-001, SC-002, SC-005.

## 4. Key entities

- **KE-001 — Project goal:** the project's existing authoritative intended outcome, acceptance, decisions, and owner. It is not copied into an SCM database.
- **KE-002 — Task assignment:** a bounded unit from the project's current tracker/goal, with owner, write scope, dependencies, and base revision.
- **KE-003 — Worktree:** a disposable isolated filesystem view used for local work. Its path is not durable task identity.
- **KE-004 — Changeset:** the Git revision and diff produced by one task, tied to its base and assignment.
- **KE-005 — Handoff/review evidence:** existing task report or review record, tied to the exact changeset and current criterion; it states observations, findings, and next action.
- **KE-006 — Integration revision:** the resulting project revision after supervisor integration and integrated-result check.

The protocol reuses project records and Git; it does not create a second task graph or source-of-truth database.

## 5. Success criteria

- **SC-001 — Resumable handoff:** Given interruption after edits, an uninvolved successor can recover the exact persisted candidate by its stable revision/artifact identity and find the goal/task, base, owned paths, unmet criterion, last verified check, recovery history, and next action in the existing project record. A report that references only a vanished worktree or an uncommitted diff fails. Verifier: nonauthor reviewer interrupts and resumes a prepared task. Links: FR-001, FR-003, FR-007.
- **SC-002 — Dirty-state safety and writer isolation:** In a two-task case with pre-existing tracked and untracked files, each task candidate is recoverable separately; declared/actual path overlap and out-of-scope edits are caught before review/integration; pre-existing files remain byte-for-byte present. Verifier: inspect status, paths, candidate trees, and preserved inputs. Links: FR-001, FR-002, FR-007.
- **SC-003 — Exact-review integration:** Review records base commit and tree ID. Integrating the same accepted tree succeeds; changing the base or tree makes the old verdict visibly stale and prevents integration acceptance until a nonauthor reviews the current candidate. A different commit SHA with the same tree is allowed only when the reviewed base is unchanged. Verifier: compare base/tree identities across review and integration. Links: FR-004–006.
- **SC-004 — Correct lifecycle and no self-acceptance:** Each state transition is recorded by its named owner, and a worker's own verdict or a stale approval cannot mark the task accepted/integrated. Verifier: adversarial reviewer attempts unauthorized and out-of-order transitions. Links: FR-001, FR-002, FR-004–006.
- **SC-005 — No duplicate ledger:** Goal, task, report/review, and Git each retain their existing distinct purpose. The protocol adds only revision, scope and transition links in those records; it does not require a new service, database, or copied task-state store. Verifier: structural review of the design and pilot records. Links: FR-003, FR-006, FR-007.

These criteria are proposed for a later dogfood pilot; none has been observed as passed by this document.

## 6. Assumptions and constraints

- **A-001:** “Synchronous with the project” means task and source state stay in lockstep at assignment, handoff, review, and integration checkpoints; it does not mean real-time co-editing or a central server. Confirmed by the owner's clarification.
- **A-002:** Participating projects use Git or provide an equivalent stable revision identity. If no VCS exists, the task record must name the actual artifact/version mechanism rather than fabricate a commit.
- **A-003:** Git worktrees/branches and project records are sufficient for the first version. This is a low-cost design hypothesis, not a measured result.
- **A-004:** No candidate SCM problem warrants a custom server/VCS today. Revisit only after real tasks show repeated stale approvals, lost handoffs, unsafe overlap, or costly manual reconciliation despite the protocol.
- **A-005:** The design must preserve project-specific records, authority, independent review, existing recovery history, and the current skills-only boundary of this repository.

## 7. Delivery and verification links

| Item | Owner | Evidence/status |
| --- | --- | --- |
| Research Scion, Piper and Sapling mechanisms | Research worker | [Reference report](../reports/adhoc-scm/reference-research.md); inspected by orchestrator |
| Select the lean Northstar pattern | Orchestrator | [Advisor council receipt](../evals/adhoc-scm/advisor-council.json); accepted as a design recommendation, not runtime proof |
| Specify task changeset lifecycle | Orchestrator | This document; READY for workflow design |
| Three ordered Spec Kit passes | Nonauthor reviewer | [Independent review](../reports/adhoc-scm/spec-review.md); READY for design only |
| Dogfood with concurrent related tasks and post-review base movement | Future project owner | Not run; requires an actual eligible project/task pair and safe isolated workspace |

The available Northstar repo contains no installed Spec Kit feature layout or constitution, so this document uses Northstar's optional eight-section profile. No Spec Kit CLI run or implementation verification is claimed.

## 8. Open questions and decisions

- **Q-001 — Terminology:** “Synchronous” is interpreted as checkpoint synchronization between the project loop and Git, not synchronous multi-agent co-editing. Status: resolved by owner clarification.
- **Q-002 — Commit identity when integration rewrites history:** Use the exact base + diff identity and require re-review when the base changes; never infer equivalence from the resulting commit SHA alone. Status: resolved in this design; confirm implementation behavior in pilot.
- **Q-003 — Need for a tool:** Is a command/UI/API needed beyond Git and the existing goal/task/report? Status: intentionally deferred until the pilot demonstrates friction that existing records cannot cover.
- **Q-004 — Falsification pilot:** Can two related tasks sharing an interface expose stale review after a post-review base movement, while preserving dirty/untracked user files and resuming an interrupted candidate from its persisted checkpoint? Status: next check; no qualifying task selected.

## Decision

Adopt a **task changeset protocol over Git**, with project records remaining authoritative and review bound to the exact candidate. Borrow Sapling's focused work graph and recoverable editing concepts; do not adopt Sapling as a replacement. Do not copy Scion's online server/sparse storage or Piper's centralized monorepo controls. Treat the protocol as a hypothesis until the specified falsification pilot passes. If it cannot work without duplicating project state, stop the design rather than add a ledger.
