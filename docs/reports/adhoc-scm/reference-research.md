# Reference research: an ad hoc SCM for Northstar work

Date: 2026-10-22. Status: research handoff; independently researched, not an accepted design.

## Question

Which ideas from Anthropic Scion, Google Piper and Meta Sapling help design a small source-control/coordination layer for Northstar's agent workflows, and which are unjustified for this repository?

## Verified source observations

### Anthropic Scion

Anthropic's post says Scion was built for a highly unusual workload: an online agent/job-heavy monorepo whose daily merge rate rose from about 2,500 to over 30,000 changes. Its history is nearly 100 GB and a compressed checkout over 25 GB. Anthropic explicitly says Git's decentralized/offline model remains appropriate for the vast majority of repos; Scion was motivated by their atypical scale. ([Anthropic engineering post](https://www.anthropic.com/research/redesigning-source-control))

The design principles described are: online clients; server/client asymmetry; APIs for source-control queries; horizontally scalable content-addressed data; cheap incremental server-side changesets; sparse/virtualized working copies; and discouraging global refs except main/release refs. A changeset stores files changed relative to its first parent plus content-addressed blob pointers; derived indices (e.g. blame/path history) can be computed eagerly or lazily. The post reports these choices reduced checkout/maintenance costs at Anthropic's scale. These are observations about their service, not validated requirements for Northstar.

The workflow lessons are more transferable than the storage architecture: operators set high-level invariants and reject agent implementations that violate them; reviewers inspect intent, rather than blindly reading every line; adversarial review can catch issues but can also prompt overengineering; explicit hermetic simulations and fuzzing were used for infrastructure interactions; semantic approval requirements focus human review on consequential changes. ([Anthropic engineering post](https://www.anthropic.com/research/redesigning-source-control))

The official X URL was opened but returned HTTP 403 via the research tool, so I could not verify its text or media independently. The article itself is the source used above. ([Anthropic X post](https://x.com/AnthropicAI/status/2110047081414987957))

### Google Piper

The linked Piper description is Wikipedia, not an official Google Piper product page. It describes Piper as centralized version control, with developers changing local working copies and submitting changes for review through Critique before commit. CitC presents a cloud-backed, FUSE-based view over the repository with small local working copies and snapshots; it supports easy machine switching and shared work. The page's concrete scale figures are historical (2016) and should not be used as current measurements. ([Piper overview](https://en.wikipedia.org/wiki/Piper_(source_control_system)))

Google Research's record for Potvin and Levenberg's 2016 Communications of the ACM article identifies it as an overview of Google's monolithic repository, its scale, custom-built repository, supporting systems/workflows, and trade-offs. This supports using Piper as an example of a repository model shaped around large-scale collaboration; it does not by itself support a detailed approval-flow claim. ([Google Research publication record](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/), [DOI](https://doi.org/10.1145/2854146))

**Correction note:** The earlier handoff linked an unrelated Google Cloud Storage paper about resolving code-review comments with machine learning and attributed a directory-owner/technical-review distinction to it. That citation and claim were incorrect and have been removed; the original failed citation is retained here for audit: [unrelated paper](https://storage.googleapis.com/gweb-research2023-media/pubtools/pdf/0449374e831a796a5e88f92380c64e7e090c6dfa.pdf).

### Meta Sapling

Sapling's official site emphasizes accessible source-control workflows, Git interoperability, and stacking work for iterative review. Smartlog is a compact graph view of the current user's relevant commits, showing the base, work location, parent/child relations and landed/rewritten state; it intentionally hides irrelevant history to reduce mental overhead. Sapling's stack documentation describes amend, restack, fold/split and undo to iterate without losing recovery context. ([Sapling home](https://sapling-scm.com/), [Smartlog](https://sapling-scm.com/docs/overview/smartlog/), [commit stacks](https://sapling-scm.com/docs/overview/stacks/), [safe hide/unhide](https://sapling-scm.com/docs/overview/hide-unhide/))

Sapling is not itself evidence that Northstar should replace Git. The official project describes its scalability goals as per-user working-set scaling; the project README also says Meta's internal deployment is not yet supported for external use. ([Sapling GitHub](https://github.com/facebook/sapling))

## Northstar-specific design inferences

Northstar's actual unit of coordination is a goal/task with an owner, bounded artifact scope, base state, handoff, independent reviewer, acceptance evidence and learning checkpoint. Its repo instructions already preserve Git as the repository history, use one writer per scope, and require inspecting diffs/status and staging intentional files only. ([Northstar direction](../../northstar/README.md), [subagent coordination](../../../skills/codex-subagents/SKILL.md), [repository instructions](../../../AGENTS.md))

The useful adaptation is therefore a **thin, task-centric SCM overlay on ordinary Git/worktrees**, not a new VCS or online source-control service:

1. **Task changeset:** identify the task/goal, owner, base commit or worktree identity, owned paths, dependencies, and changed-file/diff summary. This makes provenance and overlap inspectable.
2. **Small task graph:** show each active task's base, parent/dependency, status (working, handed off, under independent review, accepted, returned, integrated), changed paths and acceptance link. Borrow Sapling Smartlog's “only the relevant neighborhood” presentation; do not expose a repo-wide graph by default.
3. **Stack related increments:** when task B depends on task A, record that edge and the exact base/revision. Permit an amended/returned task to get a new revision while retaining the prior diff and reviewer result. Preserve recoverability instead of overwriting or hiding prior evidence.
4. **Separate review from integration:** a nonauthor reviewer checks the proposed changeset against original intent and acceptance; integration then confirms the reviewed revision is the one merged. A changed diff invalidates only the affected review evidence. This requirement comes from Northstar's existing author/reviewer separation; Piper-specific approval mechanics remain attributed only to the supplied secondary overview.
5. **Conflict visibility:** compare task path scopes early, flag overlapping writes and stale bases, and make the supervisor choose task order or rebase/repair. Do not solve concurrency with a global lock or permit multiple agents to edit the same scope.
6. **Use Git mechanisms already available:** commits/branches, managed worktrees, diff/status, and PRs remain durable storage and authority. Use structured Markdown goal/report records or existing tracker fields as the task metadata until real workflow evidence demonstrates that metadata duplication or Git ergonomics is the bottleneck.

This model targets the observed Northstar problem space: traceable handoffs, clean scope isolation, review/acceptance against the right revision, and retained learning. It does not assert that Northstar currently has a measured SCM bottleneck. The repository's current direction says evidence of practical usefulness is the constraint, so a paper design should be followed by a small real-task dogfood probe before building tooling.

## Do not copy without evidence

- Do not build Scion's always-online server, blob store, API, caches, virtual checkout, or custom changeset format: Anthropic's cited reasons are petabyte-scale fetch and checkout pressure that Northstar has not demonstrated.
- Do not force all work through a centralized mutable workspace or use a single shared tree for parallel agents; current Northstar guidance values isolation and explicit write boundaries.
- Do not replace Git, adopt Sapling, or create a parallel source-of-truth ledger just to have a graph UI. Sapling can inspire the view/undo affordance while Git remains canonical.
- Do not copy Piper's broad monorepo access, directory-level permissions, or mandatory centralized review system unless Northstar actually faces shared sensitive paths, multi-user access, or policy enforcement needs.
- Do not treat “agent always online” as a default. Northstar can run across hosts and local worktrees; offline/reconnect behavior and host-specific capabilities remain relevant.
- Do not turn review into line-by-line ceremony or let adversarial review justify speculative architecture. Review the intent and highest-risk evidence, retain the real acceptance bar, and capture overengineering as a review cost.

## Uncertainty and next discriminating check

- X post contents/media were not accessible (403); no conclusion depends on it.
- Piper mechanics described here rely on the supplied Wikipedia page; Google's official 2016 publication record supports only the broader monorepo context and trade-offs, not detailed Piper approval mechanics.
- The article's scale/performance results are vendor-reported and tailored to Anthropic's environment; independent measurements were not reviewed.
- It is not yet clear whether the user means an agent task/change provenance overlay, a custom Git-like VCS, or both. This first design assumes a lightweight coordination/provenance layer because it fits Northstar's current skills-only remit and existing Git practices.
- Next useful check: inspect one representative recent Northstar task's worktree/task handoffs and determine whether a compact changeset/task-graph record would have prevented a concrete scope, stale-base, or review-revision failure. If no such failure occurred, keep the design as guidance and do not build tooling.

## Handoff

Artifact: `docs/reports/adhoc-scm/reference-research.md`.

Sources checked: Anthropic engineering article; user-provided X post URL; official Sapling site/docs and GitHub repository; supplied Piper Wikipedia page; official Google Research publication record for Potvin and Levenberg (2016) and its DOI. No code or shared indexes changed. Acceptance and design selection remain with the orchestrator; the primary should reconcile this report with Advisor council advice and Northstar's current direction before updating the goal.

## Orchestrator scope update — 2026-10-22

The owner clarified that this work is a **workflow-level SCM design kept in sync with Northstar's project loop**, not an undecided Git replacement versus app-overlay comparison. That resolves the scope question above in favor of a task changeset protocol over the project's existing VCS and authoritative goal/task/report records. The design is in [`docs/northstar/adhoc-scm.md`](../../northstar/adhoc-scm.md). Independent Spec Kit review remains pending.


