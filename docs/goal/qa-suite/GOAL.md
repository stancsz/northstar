# Goal: Concise QA that prevents sloppy delivery

Status: done. Base: `5f0f860ec40541e3f6c5b5c1e95484719ed89b07`.

## Outcome and acceptance

Add an installable Markdown-only `northstar-qa` skill: a brief quality plan, relevant functional/rendered-visual/adversarial/structural inspection, actionable findings, repair/recheck, and a bounded readiness decision. Integrate it with Northstar and installation guidance. Preserve lean delivery, ownership, user authority, and existing stall recovery.

Must pass: visual claims require actual visual inspection; meaningful functional claims require observed effects; review cannot be reduced to the builder's summary. Distinguish defects, optional preferences, missing evidence, and human acceptance. Review-only mode must not edit the product; blockers and unverified required checks cannot pass. Use no generic quality percentage or endless review cycle.

## Ownership and tasks

The editing agent owns direction, integration, and shared indexes, writes the [implementation report](../../reports/qa-suite/implementation.md), and performs final acceptance. One independent worker will use the new skill on isolated browser fixtures, with write scope/scratch/report under `tmp/qa-suite/trial/`. Only needed trial evidence is promoted to [evaluation](../../evals/qa-suite.md). No runtime tools or generated machinery enter the installable suite.

## Verification plan

Check Markdown links, installation paths, skill metadata, and whitespace. Review the rules against nonvisual work, missing browser access, stale screenshots, subjective redesign requests, and safety/authority boundaries.

For the forward trial, provide two small local settings pages with the same criteria and no builder assessment. Predeclared traps: one page falsely reports saving and clips required controls on a narrow screen; the other implements the bounded workflow. The reviewer must inspect actual renderings and interactions, preserve source in review-only mode, report supported findings, and avoid inventing blockers on the working case. Parent inspects artifacts and reproduces relevant observations. These synthetic cases cannot establish general anti-slop effectiveness, accessibility conformance, or human aesthetic acceptance.

## Acceptance record

Supervisor accepted the implementation and independent fixture review after inspecting the report, screenshot evidence, unchanged source hashes, and parent reproduction. The reviewer found both seeded material defects and accepted the functioning case within scope. One post-trial wording refinement limits redundant capture; its effect has not been measured.

Orchestrator accepted the bounded suite against the owner's request: concise quality planning, relevant inspections, adversarial challenge, evidence-backed decisions, and repair without an endless review loop. No requested implementation remains open. Broader reliability, actual product aesthetic acceptance, and repair-mode execution remain outside this evaluation's claims. Installation is local; commit/push is not part of this follow-up.

Owner refinement: require screenshots actually viewed plus concrete visual and functional observations, never a bare LGTM. Routine initial inspection targets five minutes, one critical journey and relevant failure, usually 1–3 representative screenshots; requirements and observed gaps determine any expansion. Accepted after instruction/metadata/whitespace checks and installed-copy verification. The time target is guidance, not a measured guarantee or permission to skip checks.
