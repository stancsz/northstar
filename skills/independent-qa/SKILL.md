---
name: independent-qa
description: Nonauthor functional, visual, runtime, adversarial, and spec acceptance review; verify material repairs against exact criteria and tree revisions.
---

# Independent QA

Follow Northstar's [delivery contract](../northstar/SKILL.md#delivery-contract). Load this companion whenever nonauthor acceptance testing, live runtime/browser verification, spec review, or visual inspection is required.

- **Strict author separation:** Never act as builder and QA/taste judge of the same deliverable. Builder development checks are inputs, not independent acceptance.
- **Inspect the actual artifact and bind to exact tree SHA:** Never approve from a builder's summary, passing build, screenshot filename alone, or filled checklist. Record the reviewed base commit and candidate tree SHA (`git rev-parse HEAD^{tree}`) so post-review edits or rebases visibly invalidate stale approvals; see [worktree & changeset binding](../subagent-orchestration/references/worktree-isolation.md#3-bind-independent-qa-to-exact-tree-identity).
- **Classical-first, then visual/AI judgment:** Check deterministic equivalence partitions, boundary values, and state transitions first before applying visual or rubric judgment; see [live runtime and browser verification](references/runtime-verification.md). Consult [Advisor Council](../advisor-council/SKILL.md#mandatory-visual-and-aesthetic-guidance) only when a material visual/design fork remains unresolved.

## Set the quality bar before building

- **Clarify criteria up front:** Record the main journey, target environment, critical boundary/failure cases, and required evidence in the existing task record (or handoff for a one-turn change). For visible work, note hierarchy, layout, typography/spacing/color, responsive viewports, and required states using the product's existing design system.
- **Reconcile the integrated outcome:** Before final delivery, verify that accumulated passes cover the full requested user workflow and release obligations. Keep missing evidence **unverified**; for explicitly local-only work, judge that local endpoint without inventing a release gate.
- **Separate defects from preferences:** When reviewing completed work without a prior plan, derive criteria from the request and established product. Label extra preferences as *suggestions*—never invent requirements to fail working code.

## Inspect relevant surfaces

- **Spec-driven reviews:** Run the [three-pass review](references/spec-review.md) (structure, evidence/privacy, adversarial FR/SC scrutiny) using the project's schema or the [optional eight-section profile](templates/spec-profile.md).
- **Live runtime & browser verification:** Follow [runtime verification](references/runtime-verification.md) to launch ephemeral local servers on free ports, isolate test data, capture console/network errors, inspect narrow/wide viewports, and guarantee process teardown.
- **Skill-effectiveness evaluation:** Record [compact behavioral receipts](references/skill-effectiveness.md).

Start routine reviews with **one critical journey**, **its primary boundary/failure cases**, and **1–3 screenshots** covering the changed surface and required viewports/states (aim for a 5-minute initial pass). Reuse valid evidence from the same tree SHA; expand only for a failed criterion, relevant change, or coverage gap. Unavailable evidence is **unverified**, not a pass.

| Lane | Required behavior |
| --- | --- |
| **Functional & boundary** | Execute the primary journey through its real entry point across valid/invalid equivalence partitions and exact boundary values (`0`, `1`, `max`, empty, malformed). Verify resulting data, persistence across reload, and error/empty/loading/recovery states. Distinguish fixture/stub results from live integration evidence. |
| **Visual and interaction** | Open the rendered UI or exported artifact at intended narrow and wide viewports ([runtime verification](references/runtime-verification.md#3-live-browser-viewport-and-telemetry-inspection)). Check hierarchy, alignment, spacing, typography, contrast, wrapping, asset quality, keyboard/focus states, and zero uncaught console/network errors. DOM/CSS inspection alone never establishes visual quality. |
| **Adversarial** | Before reading the builder's explanation, test high-value ways to disprove readiness: invalid/long/empty input, repeated submit/double-click, interruption, reload, dependency failure, stale state, or unauthorized access. State the invariant and inspect the actual effect in an isolated/authorized environment. |
| **Structure and content** | Check changed code for duplicated rules, swallowed errors, fake success, brittle hardcoding, and weakened/skipped tests. Check user-facing copy and controls for placeholders, dead controls, or contradictions. |

For nonvisual work, omit visual inspection with a brief reason. For visible work, open and inspect each screenshot, record route/state/dimensions/revision, and attach representative final screenshots in the handoff.

## Challenge the result, then repair

Assign an uninvolved reviewer who did not author the reviewed scope or own the audited operational decisions (a fresh context or new label does not remove author conflict; see [functional separation rules](../subagent-orchestration/references/role-profiles.md)). Give the reviewer original intent, criteria, and artifacts before the builder's conclusions. If no independent reviewer is available, mark acceptance **UNVERIFIED**.

Every finding requires **location/state, expected vs. observed result, user impact, and reproduction/evidence**:

- **Must fix (blocks acceptance):** Failed required criterion or material user risk (broken core flow, lost data, misleading success, console/network errors on core flow, unusable layout, missing required states, or visibly unfinished UI).
- **Suggestion (non-blocking):** Optional enhancement or preference with no failed criterion. Record for later; never hold delivery hostage.
- **Unverified:** A relevant check could not be run. Name the missing evidence and its readiness impact; never downgrade it to a suggestion.

The builder repairs must-fix defects; the independent reviewer rechecks the reproduction and captures fresh visual evidence for visible fixes. A reviewer who edits product files becomes a builder for that scope and cannot certify it. Contain material defects at their source while allowing unrelated safe work to continue.

## Finish without a review loop

Run one scoped inspection, then targeted repair/rechecks. Stop optional critique at diminishing returns; carry finding and failed-attempt counts across reviewers. After **2 unproductive repair attempts**, isolate the failing case within one recovery window; if still unresolved, the implementing owner must [decide and act](../northstar/SKILL.md#decide-after-exhausted-recovery).

Record the review in the existing task record or handoff (`docs/evals/` is optional):
- **Scope:** Artifact, base commit + candidate tree SHA, environment/port, journeys/viewports, and inspected lanes.
- **Findings:** Must-fix, suggestions, and unverified checks with evidence and disposition.
- **Verification:** Screenshot links/observations, functional/boundary and adversarial results, rechecked repairs, explicit limitations, and reviewer independence (never a bare "LGTM" or "tests pass").
- **Decision:** Name the reviewed scope (increment vs. full outcome) and verdict:
  - `READY` — independent evidence covers the scope and material repairs for the exact candidate tree SHA.
  - `NOT READY` — observed blockers remain (retain any unverified list alongside it).
  - `UNVERIFIED` — required evidence is missing.

Feed material findings and contradicted assumptions into [checkpoint learning](../northstar/SKILL.md#learn-from-every-use).
