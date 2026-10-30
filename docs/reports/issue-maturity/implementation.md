# Open-issue implementation handoff

Date: 2026-10-21. Author: primary implementation/integration agent. Status: implemented and independently reviewed for publication. [Goal](../../goal/issue-maturity/GOAL.md). Base: `293f230` with prior local changes preserved.

## Changes

- Issue #3: retained the existing [learning/feedback workflow](../../../skills/northstar/references/skill-feedback.md) and added [behavioral receipt guidance](../../../skills/independent-qa/references/skill-effectiveness.md). Exercise actual lesson reuse and fixture feedback transitions instead of claiming that existing prose proves effectiveness.
- Issue #4: a bounded worker made project-root defaults, installation-tree exclusion and write-denial/migration recovery explicit. See its [scoped handoff](goal-storage.md).
- Issue #5: added the [Spec Kit bridge](../../../skills/northstar/references/spec-kit.md), [three-pass checklist](../../../skills/independent-qa/references/spec-review.md), and [optional eight-section profile](../../../skills/independent-qa/templates/spec-profile.md). Existing schemas and constitutions win; spec readiness is distinct from executed implementation acceptance. Entrypoints and English/Chinese guides route to the new practices.
- Council-directed maturity increment: compact, reusable cold-trial receipts in existing records. No new installable runtime machinery. Gemini and Sol advice remain separately attributable in the [evaluation](../../evals/issue-maturity.md).

## Verification and limits

Six case expectations and a five-skill source snapshot were frozen before cold worker dispatch. First three probes use actual local files/code; denial evidence is synthetic. Feedback probes use a local service simulator, not GitHub. The nonauthor release reviewer inspected actual artifacts and the exact staged source, reran the 38 Python/two Node suites, verified full/detached link closure and reported scoped READY. Detailed outcomes and limitations belong in the evaluation and [review report](review.md).

Cold probes 1–6 met their scoped criteria; probe 7 exposed ambiguous cross-artifact/readiness gating. Primary clarified the checklist and the same independent reviewer verified separate spec and implementation verdicts. After repair of deliberately broken fixtures, separate-process persistence and blank-input preservation passed. Preserve the initial partial failure and scoped fixture side effect in the evaluation; this is no comparative-effectiveness claim.

The release deliberately adopts the five pre-existing Gemini 4 advisor route/docs/test edits after council identified published-source drift from the installed/live route. Thirty-eight Python and two Node offline regressions pass. Working source/installed caller SHA-256 bytes match; the staged caller differs only by LF normalization. The manifest distinguishes trial and exact staged bytes, including the trial entrypoint's excluded optional Windows routing. Other pre-existing changes remain excluded.

Initial council auth failure was retained, then corrected with the matching existing service credential through process environment only. No service/configuration/global-install change. Publication will isolate these changes from the saved dirty baseline and use PR/merge with post-merge issue verification.

## Checkpoint learning

The existing #3 implementation and reported #4 legacy path require inspecting current source before editing: a historical bug report is not proof the same text remains. Keep additions targeted. Council changed the evaluation from a proposed executable harness to a Markdown receipt practice (`decision_changed: true`); actual case artifacts, attempts and missing cost evidence will judge its usefulness. Do not claim six probes establish comparative improvement.
