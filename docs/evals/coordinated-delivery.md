# Coordinated delivery evaluation

Date: 2026-09-29. Goal: [Coordinated delivery](../goal/coordinated-delivery/GOAL.md). Base: `5f0f860ec40541e3f6c5b5c1e95484719ed89b07` plus prior QA working-tree changes.

## Method

Two bounded execution trials use separate ignored fixtures. The orchestrator receives overlapping inherited assignments and must deliver a receipt workflow. The supervisor receives an incorrect completed-worker claim, existing local authorization, and optional unauthorized upload outside the delivery. One independent reviewer inspects the changed instructions. Parent owns fixtures and final acceptance; trial agents receive current skill paths and concrete work, not evaluator answers.

No production system, user data, paid API, or external side effect is involved. Python code lives only in ignored scratch; this remains a Markdown skill collection. The checkout including ignored artifacts was 1,277,888 bytes before trials, well below the shared 100 GB ceiling.

## Evidence

| Case | Observed execution and parent verification |
| --- | --- |
| Overlapping assignments and missing integration owner | [Orchestrator trial](../reports/coordinated-delivery/orchestrator-trial.md): retired the two planning-only duplicate assignments, spawned one actual leaf worker for `amounts.total_cents`, and owned presentation/integration itself. Agreed on integer cents before concurrent implementation; inspected the worker's source/report and ran the combined workflow. Parent read both modules and reran the unchanged check: **4 acceptance cases passed**. |
| False completion and needless approval | [Supervisor trial](../reports/coordinated-delivery/supervisor-trial.md): ran the existing check under inherited local authorization, observed its failure despite the prior completion claim, and repaired premature per-price rounding after confirming the old writer was stopped. Parent inspected the single causal source change and reran the unchanged check: **3 acceptance cases passed**. No further approval was requested; optional unauthorized upload remained outside the local delivery. |
| Preserve user work and the test oracle | Parent checked both fixtures' acceptance files and user-note hashes against the trial agents' pre-edit receipts; all matched. The false worker report was preserved. No acceptance checks were weakened and no external action was taken. |
| Instruction consistency | [Independent review](../reports/coordinated-delivery/independent-review.md) considered inherited authorization, platform rejection, duplicate writers, false completion, and resumed recovery. No material actionable findings. Reviewer did not implement the instructions or run the trials. |

Trial agents also reported four targeted boundary cases each; parent reran the seven original acceptance cases, not those extra checks. The orchestrator used one leaf rather than filling all available slots. This demonstrates a bounded dependency handoff and concurrent disjoint writes, not a multi-supervisor stress test or takeover from a still-running writer.

Operational corrections: one parent read used repository-relative paths from a fixture directory; it failed and was corrected with absolute paths. The skill metadata validator initially encountered Windows cp1252 decoding on Codex Subagents; rerunning with `python -X utf8` passed without changing content. An early link scan ran before the orchestrator report existed; final validation waits for all reports. These are verification-tool issues, not product acceptance failures.

Both updated skills were copied to the existing `C:/Users/stanc/.codex/skills/` installation after backup under ignored scratch. Every source file, including both role templates, matched its installed copy by SHA256. Already-running sessions must reload the changed instructions to use them.

Evaluated instruction SHA256 values (unchanged during the trials):

- Northstar: `1D241736CB346B5FCDFEC5BDE6E15FD9724D434288207AB80A055518C44B26B8`
- Codex Subagents: `DBF5A2046AF8FAF2D2CA022B5B3F70E017868C71CA96550E203CCC340CE78333`
- Orchestrator template: `9BBD9FA7ADF151605F286A1D2D72C3A1B7C412471D80A82DD3BB473BF03536F1`
- Supervisor template: `4475BDFC37EADE1B74865F60CCAD7F8ED4A39B121DF4A8842E4B6EC57C1886E5`

Final documentation checks are recorded in the linked goal after all reports are present.

## Limitations

Small synthetic cases, no old-skill control, no context-compaction or long-duration soak, no measured total-token savings. These trials can demonstrate specific behavior on the supplied cases; they cannot guarantee future compliance, platform approval behavior, runtime timeouts, or large-team coordination. Required visual inspection is not applicable to Markdown role instructions and numeric fixtures; the preceding [QA suite evaluation](qa-suite.md) covers its own rendered-fixture evidence.

## Follow-up: proportionate autonomy, 2026-09-29

Evaluated working-tree changes from `1bb158a`; previous hashes/results above describe the original increment, not this follow-up. Primary edited skills; separate agents executed the [local trial](../reports/coordinated-delivery/autonomy-trial.md) and [scenario review](../reports/coordinated-delivery/autonomy-review.md).

- **Written overhead:** the two skill entrypoints plus two role briefs decreased from 4,193 to 3,891 whitespace-delimited words. This measures text size, not tokens consumed or task latency. The core grows to explain decision boundaries; the companion and briefs remove duplication. Small tasks reuse current records, with explicit repository reporting exceptions.
- **Actual local behavior:** the trial agent chose a direct integer implementation, fixed the precision failure, retained the shared integer API despite an optional dictionary-return suggestion, and recorded one readiness decision. It asked no approval question and did not block on an unavailable consumer owner or optional publishing. Parent independently observed the original precision failure, inspected the repaired code/caller and goal, and reran the unchanged five-case acceptance check successfully.
- **Preservation:** parent captured hashes before delegation and compared them after execution for `check.py`, `caller.py`, `user-note.md`, and `prior-suggestion.md`; all four matched. The worker reported eight additional assertions; parent did not rerun these or count them as independently verified checks.
- **Adversarial instruction review:** covered local refactoring, shared interfaces, peer authority, small-task records, default versus explicit limits, resumed recovery, existing GUARD authority, and partial blockers. Found a stale deployment example that still demanded approval unconditionally. Primary corrected it; reviewer verified the correction. No material finding remains open.
- **Operational correction:** the parent's first baseline invocation used the wrong working directory and could not locate the check. Corrected once to the fixture directory; the resulting assertion failure is the actual before-repair evidence.

This tests one short authorized local repair and reviews the remaining cases as written scenarios. It does not exercise live peer negotiation, owner disagreement, long-session compaction, or a runtime permission gate. There is no matched old/new execution comparison, so reduced interruptions or total cost in general remain unproven. No screenshot is relevant to these nonvisual instructions and numeric fixtures. Final documentation and installed-copy checks are recorded in the goal.

## Preflight: entry guidance and existing project records

2026-09-29, based on `1bb158a` plus this goal's autonomy changes. Aligned core entry, role mapping, QA, lifecycle/protocol, optional goal template and guides: direct implementation/verification by default; continuation, delegation and QA only as relevant; native project records before optional Northstar paths. Repository requirements and external-write authorization remain explicit.

The independent reviewer checked a tiny task without docs folders, an existing issue/plan, this repository's mandatory records, an external tracker and a visual change. No material issue remained; see the appended [review](../reports/coordinated-delivery/autonomy-review.md). This is scenario inspection, not additional execution evidence. Earlier numeric trials were not rerun for these documentation-only changes. The separate skill-feedback work was excluded from the commit; staged-snapshot link, metadata and whitespace checks determine delivery readiness. Freeze this delivered baseline for real-use evaluation rather than claiming measured production gains.

## Follow-up: mandatory decisions after exhausted recovery, 2026-09-29

Base `265c9db305d4f42f1e6d964f4a2e76a2aa80df97` plus pre-existing feedback edits. Primary implements the new decision mechanism; independent `decision_review` agent inspects written scenarios, with disposable report `tmp/autonomy-decision/review.md`. This section preserves the useful evidence. No new execution trial or military-doctrine comparison was performed. Visual inspection is inapplicable to these nonvisual process instructions.

The mechanism preserves the two-no-progress-attempt trigger and one recovery window, then requires a chosen action and first executable step. A justified alternative gets one bounded trial, including dependency substitutes; history follows the criterion across methods and agents. Intent, authority and decision ownership accompany delegation. Managers resolve the issue or identify the exact decision owned elsewhere. Missing prerequisites permit early disposition without artificial retries.

Independent review found **P2: the recovery trigger still allowed another diagnostic check justified by old evidence after two no-progress attempts**, which could bypass the mandatory decision. Primary repaired the trigger: two consecutive unproductive attempts enter recovery; another ordinary window requires actual progress under the existing definition. Primary also explicitly charged dependency substitutes to the same single alternative-trial allowance. The reviewer independently reread these repairs and the missing-prerequisite exit; no material finding remains. Primary inspected that report and the final wording before accepting the documentation change.

Scenario coverage: exhausted recovery, failed alternative/reassignment, worker-local methods, shared APIs and active writers, unavailable owners, tighter explicit caps, missing customer data, unmet acceptance, manager status relay and review-only QA. The reviewer found no other material inconsistency in the initial pass. These are readings of instructions, not observed future compliance.

Primary checks: inspected the changed source diff and installation guide; all three installable skill source paths exist and all three metadata validations passed. Before this evaluation addition, 43 Markdown files contained 217 resolving local links, including 42 heading targets; no loose files appeared in `docs/`. Whitespace checks passed. Existing unrelated feedback work remains intact; no installation, commit or push occurred.

**Skill learning:** expected a decisive exit from repeated unproductive recovery; review observed that permissive trigger wording could prevent reaching it. Lesson: specify both entry and exit conditions and share one allowance across alternate-route labels. The wording repair addresses that ambiguity; real long-session behavior, comparative cost, reduced supervision and enforcement remain unverified. Prior trial results above apply to their earlier revisions, not this new mechanism.

## Follow-up: cross-domain focus and decisions, 2026-09-29

Base `265c9db` plus the prior decision-rule and feedback working changes. Primary researched sources and edited the core, delegation, QA, goal template, direction and one optional reference. A separate reviewer inspects documentation scenarios only, with scratch report `tmp/historical-principles/review.md`; useful conclusions are preserved here. No new execution trial or visual artifact is involved.

Research: inspected Sunzi's digitized original text and relevant indexed official passages from MCDP 1 (printed pages 57 and 91), MCDP 1-3 (printed page 106), the May–June 2019 Army University Press mission-command article and PLA Daily's frontline-autonomous-coordination discussion. Military direct fetches returned errors; no complete-PDF reading is claimed. Opened primary Amazon/Toyota/YC/Sequoia pages and inspected relevant decision, production-quality, MVP-feedback and customer/problem passages. Precise links and source/application distinctions live in the [reference](../../skills/northstar/references/operating-principles.md). This supports attribution, not proof of uniform organizational practice, comparative organizational effectiveness or improved AI performance.

Selected additions: prioritize the delivery constraint; cheaply test the assumption that changes the next commitment; use authorized fallback triggers; leave capacity for finishing; learn from honest failures; decide reversible matters without unanimity; and contain defects before downstream acceptance. Direct escalation bypasses unnecessary relays, not permissions. Reused intent/authority, recovery and learning instead of parallel command, OODA or review structures. Rejected copied confidence percentages, fixed team/reserve quotas and VC-style permission to lose user data or spend without authority.

Initial independent review found no material issue in seven scenarios: bottleneck versus easy tasks, writer ownership, cheap checks versus research bureaucracy, fallback authority and recovery history, finishing capacity versus arbitrary quotas, honest failure versus acceptance, and historical analogy versus efficacy claims. A targeted seven-case second pass for the user's broadened scope checked dissent/commitment, reversible-choice authority, artifact containment, reviewer boundaries, costs/spending, staged commitment/required scope and cross-domain attribution. No material contradiction remained. The reviewer did not refetch original publications or perform execution trials; primary inspected the report and final source before accepting the documentation.

Final primary checks: 44 Markdown files, 225 resolving local links including 44 heading targets; all three skill metadata validators pass; source installation entrypoints and `docs/` layout are valid; diff/whitespace checks pass. Initial sources and added reference were inspected, and pre-existing feedback/recovery changes were preserved. No installed-copy refresh, commit or push occurred.

**Skill learning:** the requested analogy is useful only when it changes a concrete decision. Most intent/delegation/learning ideas were already present; reference them rather than duplicating them. New rules target missing resource prioritization and decision-trigger behavior. Their real-task effect and overhead remain unmeasured; this increment accepts inspectable instructions, not a proven historical recipe for agent performance.
