# Incremental delivery documentation review

Date: 2026-09-28. Goal: [Usable MVP delivery](../goal/incremental-delivery/GOAL.md). Worker report: [delivery rules](../reports/incremental-delivery/delivery-rules.md).

Evaluated revision: working-tree edits based on `8b8e5bbd1c981e299e60977076ea76ee3f11740d`, Windows/PowerShell. The editing agent performs this review; no independent reviewer or agent execution trial.

## Scenario inspection

| Scenario | Instruction-level result |
| --- | --- |
| A new idea needs evidence before broad investment | Core and lifecycle allow a bounded validation MVP; assumptions remain unproven rather than blocking all implementation. |
| A CSV MVP grows into accounts, billing, and cloud sync | Current workflow/environment and later increments bound acceptance; relevant input failures still need checking. |
| An accepted workflow is resumed in a new chat | Resume rule preserves accepted work and requires a concrete reason to reopen it. |
| A dependency changes after a prior passing check | Evidence reuse is conditional on applicability; affected parsing and integration checks must be repeated. |
| Review suggests optional themes or discovers corrupt output | Optional themes become later work; corruption blocks acceptance and requires repair. |
| Two attempts repeat the same failure without information | Change approach, diagnose narrowly, or name an external blocker; unmet criteria remain unmet. |
| One agent fills three roles | One coordinated inspection can cover the responsibilities; reports and acceptance decisions remain distinct records. |
| User requested a larger outcome or continuous execution | Mark the increment delivered and continue authorized work; do not treat MVP as permission to abandon the larger request. |
| User explicitly required parity, security, or public release | MVP cannot silently reduce acceptance or inherit release authorization. |
| A quick implementation couples core logic to one provider | Design guidance calls for a minimal useful boundary and inspection of a credible provider change, not a speculative plugin framework. |
| Fewer tokens leave data migration or rework for the owner | Efficiency includes later rework; material migration costs must be explicit. No savings are claimed without measurements. |
| A working patch duplicates a rule or adds another special case | Design review requires checking the cause, reuse, and coupling; functional success alone is insufficient. |
| A one-liner hides control flow, or a generic helper couples unrelated rules | Clarity takes precedence over line count; reuse follows shared behavior rather than similar syntax. |
| Agent interprets an undefined parity percentage as the delivery target | Removed the numeric example from current instructions. Comparisons require named tasks and observable measurements; no default parity gate. |

These are manual readings against scenarios, not observed agent behaviors. The source of prior looping is not proven without run evidence. Timing, token savings, and future compliance have not been measured.

## Repository checks

Initial review: inspected the changed skill/lifecycle/template and user-facing diff, plus this goal and report. Across 24 Markdown files, all 94 local links resolved, including 18 heading links. Both documented installation source directories contain their `SKILL.md`; `docs/` contains only directories. `git diff --check` passed. No executable test suite is applicable to this Markdown-only change. The installed `C:\Users\stanc\.codex\skills\northstar\SKILL.md` still has the prior entrypoint description; this task changed repository sources, not installed copies.

Clarity revision: inspected the rewritten entrypoint, lifecycle, and shorter goal template against the scenarios above. Preserved role/report ownership, review independence disclosure, valid-evidence reuse, retry limits, meaningful acceptance, authority boundaries, storage limits, and scope-preserving continuation. The entrypoint decreased from 3,846 to 1,182 whitespace-delimited words. This is manual documentation review, not a behavioral trial.

After the rewrite, all 94 local links across 24 Markdown files resolved, including 17 heading links; installation source paths and directory layout remain valid. No numeric parity example remains in current skill instructions or project direction. Whitespace checks passed.

2026-09-29 follow-up: added bounded recovery and persistent checkpoints, then ran [two isolated forward trials](stall-recovery-trials.md). This later evaluation adds limited behavioral evidence; the earlier documentation-only findings remain historical. Both installed skill copies were backed up and refreshed after verifying they matched the original repository versions without local modifications.
