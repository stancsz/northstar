# Northstar QA evaluation

Date: 2026-09-29. Goal: [QA suite](../goal/qa-suite/GOAL.md). Report: [implementation](../reports/qa-suite/implementation.md). Working-tree base: `5f0f860ec40541e3f6c5b5c1e95484719ed89b07`.

## Documentation inspection

The editing agent inspected rules for visible versus nonvisual work, missing browser access, stale evidence, subjective redesign requests, review-only authority, and meaningful readiness. Required missing evidence remains UNVERIFIED; observed defects are NOT READY. Optional preferences cannot reopen accepted work. Actual rendered inspection is required for visual claims; human acceptance is not inferred from an AI verdict. Security and accessibility checks are scoped, not claims of formal conformance.

Skill metadata validation passed. The independent review-only worker preserved both source hashes; the parent verified this before acceptance. Local-link, whitespace, and installation checks are recorded below.

## Forward trial

One fresh reviewer received only the new skill, two local profile-settings pages, their shared criteria, and safe browser tooling. It was instructed to inspect each through an isolated browser, actually view screenshots, and produce a report without editing HTML. The parent designed the synthetic fixtures and acceptance trap; the reviewer was not given the intended defects or builder conclusions. No production systems or network access are involved.

Criteria: labelled form, clear save action, nonempty display name persists after reload, empty name yields an understandable error without success, and readable/usable controls at 1280x800 and 390x844. The fixtures share a quiet single-form design brief; no server or formal accessibility claim is made.

Predeclared case A defects: success feedback without persistence and a fixed-width layout clipping the narrow screen. Case B implements the bounded workflow. Review must produce evidence-backed findings, preserve source, and avoid inventing a defect merely to appear adversarial.

## Observations and evidence

The fresh worker returned **A: NOT READY; B: READY for the supplied fixture scope**. It executed save/reload, empty and whitespace input, repeat actions, long Unicode input, keyboard submission/focus, and state recovery at both viewports. It viewed nine actual screenshots with image tools and inspected source after selecting adversarial cases. The parent read the report, opened both narrow screenshots, reproduced save/reload and initial button bounds using a separate browser run, and checked source hashes. All launched browsers were closed.

| Observation | Parent verification | Durable evidence |
| --- | --- | --- |
| A reports success without persistence | Success text: `Changes saved.`; after reload the input was empty. | [Claimed save, 1280x800](assets/qa-suite/A-desktop-saved.png), [after reload, 1280x800](assets/qa-suite/A-desktop-reload.png) |
| A clips the primary action at 390px | Initial button x=601.48, width=133.52; outside the 390px viewport. Parent visually inspected the clipped input and absent button. | [A initial narrow viewport, 390x844](assets/qa-suite/A-narrow-viewport.png) |
| B supports the bounded workflow | `Parent verification` survived reload; button x=41, width=133.52 fits the narrow viewport. Parent inspected the coherent narrow saved state. | [B narrow saved state, 390x844](assets/qa-suite/B-narrow-saved.png) |

Reproduce the functional observations by entering a nonempty name, saving, then reloading each local page. Inspect the narrow screen before interacting: automation may scroll toward an offscreen button and conceal its initial placement. The reviewer distinguished a full-page overflow capture from the actual viewport. The fixes were not applied because the trial was review-only.

Environment: installed headless Google Chrome 154.0.8037.58, Playwright from the bundled runtime, isolated contexts, local file URLs. No actual server or paid service. A source SHA-256 remained `5ca30d4999467dcbaf629df511a495b4ecf446328ee337f53c730a720d4ec79d`; B remained `eca889d72ee993f78d1d41456f64de49c797ca965d6b118ef0334f08ef25ec60`. Trial skill SHA-256: `2cf5f6845525c413d70bcc9ba4278a12899f3279b897e9fd0ffc8c47a3a14491`.

The trial generated more captures than it inspected. Added one narrow efficiency correction afterward: capture representative states and failures/fixes, not every interaction or unchanged screen. This wording correction was reviewed but was not subjected to another forward trial. Only four necessary screenshots were promoted; raw scripts, observations, and worker report remain disposable scratch.

## Conclusion and limitations

The trial met predeclared criteria: found both material defects with evidence, preserved review-only scope, and did not manufacture a blocker for the functioning case. This is limited behavioral evidence for this simple fixture, not measured general anti-slop effectiveness, long-session reliability, actual mobile-device testing, accessibility conformance, or human aesthetic acceptance. Repair/recheck behavior and missing-tool disposition were inspected as instructions, not exercised in this trial. The author designed the fixtures and integrated the independent worker's report; the study as a whole is not independently designed.

Final repository checks: 29 Markdown files, 126 local links including 22 heading links resolved; whitespace and skill metadata validation passed. Skill source remains Markdown only. Northstar and Northstar QA installed files match repository source byte-for-byte; the previous Northstar installation was backed up. Checkout usage including ignored fixtures, captures, and backups was approximately 1.17 MB, well below the shared ceiling. These checks establish packaging and navigation, not additional behavioral coverage.

Follow-up instruction review: visible handoff now requires opened screenshots and specific visual observations alongside actions/results; bare LGTM is explicitly insufficient. A routine initial inspection targets five minutes and representative coverage, without waiving required checks. Reviewed the small-change, required-multiple-viewports, unavailable-browser, and repaired-state cases: coverage gaps remain unverified and relevant requirements can extend the initial pass. Metadata, whitespace, and source/install equality checks passed. Earlier browser evidence was reused; no new runtime timing or compliance claim is made.
