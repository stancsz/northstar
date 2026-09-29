# Task report: Bound delivery and reuse completed work

Goal: [Usable MVP delivery](../../goal/incremental-delivery/GOAL.md). Date: 2026-09-28.

Worker: editing agent, also acting as supervisor, orchestrator, and reviewer. No delegated or independent review. Status: completed; acceptance recorded in the goal.

Based on `8b8e5bbd1c981e299e60977076ea76ee3f11740d`, updated the [core skill](../../../skills/northstar/SKILL.md), its [lifecycle](../../../skills/northstar/references/goal-driven-engineering.md), [template](../../../skills/northstar/templates/GOAL.md), [examples](../../../skills/northstar/references/examples.md), and [delegation guidance](../../../skills/codex-subagents/SKILL.md). Updated project direction and English/Chinese entrypoints; the [Chinese guide](../../misc/README.zh-CN.md#避免重复绕圈) includes a reusable prompt.

The changes distinguish current delivery from the long-term destination, require reasons for repeated work, change uninformative retry approaches, and make delivery criteria the stopping point. The existing report and ownership practices remain intact; one agent can inspect once for multiple responsibilities.

Incorporated the owner's clarification: maximize useful outcomes per time and total tokens; lean and functioning first with excellent architecture. Added minimal necessary boundaries, deliberate hard-to-reverse decisions, and inspection of credible extensions without speculative frameworks or claims of tested extensibility.

Follow-up: tightened the same design section and Chinese prompt around lean, clean code, shared rules, explicit data flow, removal of unnecessary machinery, and concise expression. Preserved readability and avoided prescribing generic abstractions solely for reuse. Updated the existing records rather than creating another reporting cycle.

Clarity refinement: rewrote the entrypoint from 3,846 to 1,182 whitespace-delimited words, removed the undefined numeric parity example, and condensed the lifecycle and goal template instead of moving repeated prose elsewhere. The entrypoint now gives a five-step execution sequence, repeat/ask/finish conditions, and concrete code-quality checks. Word reduction is a document measurement, not evidence of runtime token savings.

Checks passed and limitations recorded: see the [evaluation](../../evals/incremental-delivery.md). No agent execution trial, measured speedup, installed-copy update, commit, or push. No in-scope work remains; use the revised skill in a subsequent real task to evaluate behavioral improvement.

## Recovery follow-up — 2026-09-29

Implemented a measurable progress definition, criterion-based attempts, bounded investigation/recovery, protected baselines, and a continuation checkpoint in the existing template. Aligned companion delegation and installation guidance. Two fresh workers ran isolated forward trials; the parent inspected reports/artifacts and independently checked outcomes. See [trial evidence and limitations](../../evals/stall-recovery-trials.md). Both dispositions met acceptance; there is no long-session or measured efficiency claim.

Refreshed the existing `C:\Users\stanc\.codex\skills\northstar` and `codex-subagents` copies after comparing all installed files to repository HEAD and finding no local changes. Preserved originals under `tmp/stall-recovery/installed-backup/`, copied repository skill files, and verified byte hashes. No commit, push, network call, or live deployment. Older statements above describe prior stages, before this follow-up.
