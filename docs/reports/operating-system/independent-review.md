# Independent documentation review: operating system

**Reviewer role/model:** independent documentation-only reviewer; `gpt-6-luna`, high reasoning effort.
**Scope:** Read `AGENTS.md`, `docs/northstar/README.md`, `docs/goal/operating-system/GOAL.md`, `skills/northstar/SKILL.md`, `skills/northstar/references/operating-system.md`, `skills/northstar/references/skill-feedback.md`, `skills/codex-subagents/SKILL.md` and its orchestrator/supervisor briefs, and `skills/northstar-qa/SKILL.md`. No source files or trial evidence were changed or evaluated.

## Finding

**Must fix — clarify that mandatory learning reviews cannot be skipped by adapting their timing.** In `skills/northstar/SKILL.md:44`, “review timing” is grouped with templates and default investigation windows as guidance that can be adapted. The new rule at `skills/northstar/SKILL.md:133` requires a review at every meaningful checkpoint, and `skills/northstar/references/skill-feedback.md:17-20` says to review at checkpoint triggers and calls the team review required. The strict rule makes intent recoverable, but “adapt review timing” can be read as permission to defer or omit a checkpoint review. That risks dropping the explicitly accepted mandatory solo/team learning behavior. Clarify that length and ceremony may scale or coalesce, while each meaningful checkpoint still requires the review before dependent work continues.

## Scenario review

| Scenario | Assessment and evidence |
|---|---|
| Solo mandatory checkpoint | Covered: `skills/northstar/SKILL.md:133-143` makes the loop core and mandatory at meaningful checkpoints; `skills/northstar/references/skill-feedback.md:17-20` gives a solo owner an explicit self-review and rejects invented independent reviewers. Subject to the wording finding above. |
| Team disagreement | Covered: `skills/northstar/references/operating-system.md:32-38` requires reasons, counterarguments and what could change a view; one direct exchange precedes a short superior-chaired meeting when material disagreement persists. `skills/codex-subagents/SKILL.md:70` and the role briefs repeat the rule. |
| Fact vs preference/tradeoff vs authority | Mostly covered: `operating-system.md:34-37` assigns factual claims a distinguishing check, tradeoffs to the decision owner, and authorization conflicts to the authority holder. Preferences with no failed criterion or material impact are suggestions under `skills/northstar-qa/SKILL.md:38,43`; preference-driven refactoring is deferred at `skills/northstar/SKILL.md:72`. The relationship is supported across the docs, though no single instruction explicitly says to classify “preference” as a suggestion/tradeoff before escalation. |
| Essential participant absent | Covered: `operating-system.md:36` requires noting the missing view and bounding the wait; no assent is invented. Work proceeds only within current evidence and authority, otherwise the dependent part is parked while independent work continues. |
| Expert unavailable | Covered: `operating-system.md:48` preserves uncertainty, stops the unsupported route, names the unblock condition, and advances independent work. |
| Expert after recovery is exhausted | Covered: `operating-system.md:42,48` keeps consultation advisory to disposition and bars an extra implementation trial beyond the existing alternative allowance. It disallows cycling experts for fresh retries. |
| Ongoing business promises vs proxy metrics | Covered: `operating-system.md:7-13` requires real operating signals, including promised delivery, quality, capacity, and realized revenue/cost, with source, period and unknowns. It says a proxy cannot replace intended value and project completion does not establish operational health. |
| Cheap worker failure vs commander takeover | Covered: `skills/codex-subagents/SKILL.md:23,91,105` requires inspecting inherited recovery, correcting the brief/boundary before blaming the model, and choosing an authorized remedy without giving a new worker fresh retries. Cost guidance explicitly counts manager takeover as rescue, not worker success, and accounts for intervention/rework (`:25`). |
| Full cost accounting | Covered: `skills/codex-subagents/SKILL.md:25` includes commander, workers, consultation, review and rework in total token/cost comparisons; unavailable usage/rates remain unknown. `operating-system.md:52-54` also says to include elapsed time, coordination and rework. |
| No fake consciousness or consensus | Covered: `operating-system.md:7,22-23,37` describes autonomy as bounded judgment without consciousness claims, rejects manufactured opposition, and rejects forced unanimity. `docs/goal/operating-system/GOAL.md:9` explicitly excludes fabricated consciousness/consensus. |
| No unconditional meetings or extra bureaucracy | Covered: `operating-system.md:3,20-23,35-38` limits meetings to unresolved material disagreement or urgent authority/acceptance threats, permits actual async participation, coalesces records, and removes spectators/duplicate approval. The core says ceremonies occur only at their triggers (`skills/northstar/SKILL.md:18`). |
| Old/new wording conflicts | One ambiguity recorded above. Other inspected transitions are coherent: the new “decide and act” recovery text preserves the inherited single alternative allowance; it does not make reassignment or expert consultation a retry reset (`skills/northstar/SKILL.md:64-83`, `operating-system.md:37-48`, `skills/codex-subagents/SKILL.md:91,103`). |

## Review decision and limits

**NOT READY pending the wording clarification above.** The substantive requested scenarios are otherwise represented with useful triggers, owners and outcomes. This is a documentation-only review of the named sources and role briefs; it does not establish that agents follow the guidance, validate a lower-tier execution trial, verify link resolution, or make a behavioral/effectiveness claim. No trial artifacts were inspected, as assigned.

## Recheck disposition (2026-09-29)

Rechecked only the affected wording and goal-template additions after the repair; the original finding and review record above are retained as history.

- **Resolved:** `skills/northstar/SKILL.md:44` now says to scale review length and attendance and coalesce overlapping events, while still completing the required review at each meaningful checkpoint before dependent work continues. The prior ambiguity is closed; it no longer reads as permission to skip a checkpoint review.
- **Resolved:** `skills/northstar/references/operating-system.md:35` explicitly classifies a preference without a failed criterion or material consequence as a suggestion, not grounds to block acceptance or convene escalation.
- **Template support confirmed:** `skills/northstar/templates/GOAL.md:14,25,35,37` adds an optional operating commitment, capability/model and observed usage fields with unknowns preserved, a triggered decision-meeting record, and checkpoint learning details. These fields make the relevant expectations easier to carry into execution without making every field mandatory.

**Recheck decision: READY for the previously recorded documentation finding and these affected changes.** This recheck does not change the original scope limits: no trials were inspected and no behavioral or effectiveness claim is made. Unaffected scenarios were not re-reviewed.
