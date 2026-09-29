# QA suite implementation report

Date: 2026-09-29. Goal: [QA suite](../../goal/qa-suite/GOAL.md). Author: editing agent, also supervisor/orchestrator. Status: completed; acceptance in the goal.

Added the single-file [Northstar QA skill](../../../skills/codex-qa/SKILL.md) and integrated it with Northstar, the goal template, repository navigation, English installation guidance, and Chinese skill listing. The initializer ran in ignored scratch; only Markdown enters the skill collection. No runtime framework or generated reporting machinery was added.

The skill requires a brief quality plan, relevant functional/visual/adversarial/structural checks, concrete evidence, and material-defect repair/recheck. It separates review-only from implementation work, defects from preferences, and missing evidence from a pass. Review is bounded; existing Northstar checkpoints remain authoritative for stalls.

Metadata validation passed for the new skill and Northstar. The independent browser review found the seeded false-save and narrow-layout defects, accepted the working case within scope, and preserved both sources. The parent viewed screenshots and reproduced the functional findings; [evaluation](../../evals/qa-suite.md) preserves four screenshots, observations, and limitations. Added a targeted instruction against redundant captures after observing excess screenshots. These are synthetic cases, not proof of broad delivery quality or human visual approval.

Installed Northstar QA alongside the existing local Northstar copy, preserving a backup before refreshing Northstar. Final source/install hash equality and repository checks are recorded in the evaluation. No commit or push is included in this follow-up.

Owner refinement: tightened screenshot handoff and evidence requirements, explicitly rejected bare LGTM, and added a five-minute initial inspection default with representative coverage. Refreshed the installed QA copy after preserving its matching prior version. Checked instructions and metadata; reused the earlier browser evidence rather than rerunning unchanged fixtures. No claim that the new timing target was behaviorally measured.
