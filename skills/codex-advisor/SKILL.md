---
name: codex-advisor
description: Consult GPT-6.1 Sol early and frequently on documented Luna/workhorse capability risks, images and aesthetics, or a concrete decision blocker. Send compact evidence and actual image attachments; retain worker ownership. Codex-native and usable by other agents.
---

# Codex Advisor

Use this skill in other agents too; the Codex name is not a usage restriction. Follow the bundled [host adaptation guidance](../northstar/SKILL.md#use-with-other-agents); the advisor service and reader prerequisites still apply.

**Advisor model is fixed to GPT-6.1 Sol.** The caller's sole `--model sol` choice targets the versioned `codex-gpt-6.1-sol-advisor` route; the dedicated service exposes only that route. No Astra, older Sol, worker-model substitution or model fallback. If 6.1 Sol is unavailable, report unavailable and retain the unmet decision. Pi is the separately scoped source reader, not another Advisor. Historical benchmark comparisons do not authorize selecting their other models.

Use this skill whenever the [capability-risk register](references/capability-triggers.md) applies, for any art, image inspection or aesthetic decision, and when focused local investigation leaves a concrete decision blocker. Consult early and frequently on relevant Luna/workhorse weaknesses; do not wait for repeated failure. Visual work requires active advisor direction. The current worker retains task ownership, implementation and development checks; independent QA owns acceptance verification. Advice does not replace that verdict. Follow [Northstar's expert consultation practice](../northstar/references/operating-system.md#bring-in-expertise), including its recovery and alternative-trial limits.

Contents: [Capability risks](#consult-early-and-frequently-on-capability-risks) · [Mandatory visual guidance](#mandatory-visual-and-aesthetic-guidance) · [Choose whether to consult](#choose-whether-to-consult) · [Recovery limits](#keep-consultation-within-the-existing-recovery-boundary) · [Compact request](#make-a-compact-advice-request) · [Reader mode](#let-the-expert-independently-read-more) · [Resume ownership](#resume-worker-ownership)

## Consult early and frequently on capability risks

Read the [risk tags, evidence and encounter triggers](references/capability-triggers.md) before assigning or executing relevant work. Tag the current decision in the existing task/handoff; use actual task characteristics and observed limits, rather than trusting the worker's confidence. Distinguish directly measured Luna gaps, general-model risk and the owner's aesthetic standard. Published challenge results are not everyday failure rates or proof that an advisor is infallible.

**When a tag applies, invoke a compact Advisor before the risky decision, even without a failed attempt.** Send the tag, intended action, acceptance, a few raw observations and one decision question. Attach images when the question depends on pixels. Group overlapping risks for the same decision into one packet. Consult again at a distinct risky decision or when changed evidence, an invalidated recommendation or a repaired artifact needs reassessment; retain the previous advice and what changed. Frequent means decision-relevant guidance throughout the work, not repeated reassurance on unchanged evidence.

The ordinary blocker prerequisites and task-wide two-/three-call consultation ceilings do not suppress these required consultations. Existing resource limits, source scope, call receipts and no-progress recovery still apply; the Pi reader's per-invocation ceilings remain unchanged. A new risk tag, reader invocation or model does not renew an exhausted recovery route. Preserve failed consultation receipts and correct the demonstrated cause before any justified new attempt; no automatic retry or hidden model fallback.

Use only GPT-6.1 Sol for every risk tag. Do not assume a stronger model is infallible; the reference records counterexamples across evaluated models. Advisor guidance can help identify an authorized route; it cannot overturn a review denial, warning, permission boundary or user restriction. Disclose broken tools and missing evidence immediately, before consulting; do not use consultation to postpone that disclosure. Implementation and independent acceptance remain with their existing owners.

## Mandatory visual and aesthetic guidance

**Any art, image interpretation, visual design or aesthetic judgment requires advisor consultation.** This includes UI appearance, typography, color, composition, illustrations, generated images, visual fidelity and judging screenshots. Consult before committing to a visual direction and throughout repair; do not wait for a failed local attempt or let the workhorse's own taste substitute for guidance. A routine-looking visual task is still covered. Nonvisual work follows capability-risk triggers or the ordinary path below.

Use GPT-6.1 Sol and verify actual image-viewing capability and suitable visual judgment. Give it further evidence and compact follow-up questions when aesthetic direction is unresolved; do not switch models. A model name does not prove image access or taste. The advisor must actually receive and inspect the images.

1. **Show the real artifact.** Supply current rendered screenshots or the actual image, the owner's criteria and any visual reference. Identify revision, viewport/state and image dimensions. A worker description, source code, file path, OCR or successful build cannot substitute for pixels delivered to the advisor. Ask it to identify visible problems and choose a concrete direction.
2. **Let the advisor control inspection depth.** Include an overall view. If details are illegible, send multiple labeled crops at original resolution with their positions in the full image; avoid shrinking the entire image to fit. Ask which areas it wants to inspect next. Fulfill every requested region, zoom, alternate state, reference or comparison within the authorized task, then return the evidence to the same advisor. Do not choose away inconvenient areas, invent unseen detail or treat an outstanding request as optional. If access or authority prevents a request, record the exact gap and keep that visual judgment unverified.
3. **Obtain step-by-step repair guidance.** Ask for observations tied to visible regions, prioritized defects, concrete changes and the next judging view. Resolve vague feedback with another image-backed question. The advisor directs the visual work; the worker makes the changes and runs development checks.
4. **Return the repaired screenshots.** Capture the changed state and show it to the advisor alongside the relevant earlier view/reference. Repeat requested close-ups, feedback and repair until the current visual criteria are met and its evidence requests are satisfied, or a real capability/resource/recovery limit stops progress. One initial opinion or a worker's claim that it followed the advice does not complete this loop. Stop at current acceptance rather than chasing unrelated preferences.

The ordinary blocker prerequisites, two-call ceiling and three-call reader ceiling do not cap this required visual feedback loop. Compact text around the images, but never omit necessary visual evidence or requested detail to meet a text/answer target. Track calls, actual usage and unresolved requests; retain existing resource, authority and no-progress recovery boundaries. More screenshots or opinions alone do not reset recovery or prove progress.

**Actively attach images to the consultation.** Use the bundled caller's repeatable `--image` option for actual screenshots, references and crops; it sends image bytes as structured `image_url` data URLs to the dedicated Advisor endpoint. Images stay attached on every expert follow-up when reader mode is enabled. The Advisor sees the pixels directly; its optional Pi agent reads approved source evidence, rather than being required to take the initial screenshot. A path, OCR or base64 pasted into the text packet is not an image attachment. If the backend rejects images or inspection is inconclusive, keep visual consultation unverified; do not silently switch gateways or treat the worker's own view as Advisor inspection.

Record images/crops viewed, requested detail, advisor feedback, repairs, recheck findings and remaining limits in the existing handoff. An advisor that directed or coauthored the design cannot independently accept that same design. Obtain a separate nonauthor acceptance review and any required human aesthetic approval.

## Choose whether to consult

For work with no capability-risk or visual trigger, do not consult for routine implementation, an untested hypothesis, a question answerable from local code or documentation, or to have an expert perform the work. First make the smallest useful local check and compact the result. [Capability-risk consultation](#consult-early-and-frequently-on-capability-risks) and [mandatory visual guidance](#mandatory-visual-and-aesthetic-guidance) take precedence when their triggers apply.

For ordinary consultation outside those triggers, all four conditions must hold:

1. The current worker has a specific objective and a concrete blocker or decision.
2. Focused source or documentation inspection plus a targeted test or bounded attempt produced ambiguity, competing paths, or a repeatable failure.
3. No cheaper local observation would resolve the question.
4. One precise question could change the worker's next experiment or plan. Use a second question only when it is needed to interpret the first.

Do not consult for missing credentials or permissions, an unresolved user choice, work that only needs implementation time, or generic reassurance.

Use GPT-6.1 Sol for diagnosis, a design fork, a failed test path or a bounded challenge to an implementation plan. An advisor that coauthors the plan is not its independent acceptance reviewer; expertise does not bypass role separation. Unresolved decisions require changed evidence or a scoped follow-up to the same Advisor, never Astra escalation or a model vote.

## Keep consultation within the existing recovery boundary

Outside capability-risk and visual triggers, one consultation is the default. Ordinary mode permits at most two GPT-6.1 Sol calls total for the task: the initial consultation, then one distinct follow-up after its suggested check. State why. Ordinary reader mode replaces that allowance with at most three expert calls and three Pi tasks total for the task; enable it before consulting that question. These are ceilings, not targets or retry windows. Required [capability-risk consultation](#consult-early-and-frequently-on-capability-risks) and the [visual loop](#mandatory-visual-and-aesthetic-guidance) may need more calls, but do not enlarge ordinary unrelated call budgets, Pi runtime limits, existing resources or recovery. Stop when the current decision is supported; do not automatically retry failed consultations, reopen exhausted investigation or add implementation trials by consulting again.

## Make a compact advice request

The dedicated expert API is `http://127.0.0.1:4040/v1`, not the worker gateway on port 4000. It exposes only `codex-gpt-6.1-sol-advisor`, mapped to GPT-6.1 Sol. The versioned alias intentionally fails on an older service rather than silently using older Sol. Do not substitute an executor alias or silently fall back to port 4000.

Write a high-density packet, normally under 4,000 characters and never over 6,000. Keep only information that could change the recommendation:

1. The decision or blocker in one sentence.
2. Three to six observed facts, each as one bullet. Include at most one exact error or code excerpt, no longer than 400 characters.
3. Constraints and already-rejected paths in one short bullet.
4. One decision question. Add a second only when it directly depends on the first.

Remove chronology, raw logs, full source files, duplicated conclusions, speculation, and any fact that cannot change the decision. Strip secrets. Ask for a verdict, the smallest next experiment, and a material stop condition. The advisor must not write code, issue commands with side effects, or complete the task. Ordinary text advice uses no tools; visual advice may use available read-only image inspection to examine the supplied evidence and request more views.

Run the bundled caller. It rejects packets above 6,000 characters, requests a compact answer, emits UTF-8 JSON on Windows, and returns the answer, selected model, packet/output size, and reported provider usage. Resolve the installed `codex-advisor` directory rather than relying on the current working directory:

```powershell
$skillDirectories = @()
if ($env:CODEX_HOME) { $skillDirectories += Join-Path (Join-Path $env:CODEX_HOME 'skills') 'codex-advisor' }
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.agents\skills') 'codex-advisor'
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.codex\skills') 'codex-advisor'
$codexAdvisor = $skillDirectories | Where-Object { Test-Path (Join-Path $_ 'SKILL.md') } | Select-Object -First 1
if (-not $codexAdvisor) { throw 'Set $codexAdvisor to this installation''s codex-advisor directory.' }
$codexAdvisor = (Resolve-Path $codexAdvisor).Path
py (Join-Path $codexAdvisor 'scripts\ask_expert.py') --model sol --input-file .\advisor-packet.txt
```

For visual advice, attach the overall view and useful details proactively. The text packet supplies criteria, revision/state, reference roles and the next decision; image bytes are separate from its character budget:

```powershell
py (Join-Path $codexAdvisor 'scripts\ask_expert.py') --model sol --input-file .\advisor-packet.txt --image .\current.png --image .\detail.png
```

Supported files are PNG, JPEG, WebP and GIF, with at most eight images, 10 MB per file and 20 MB total per call; split further requested views into calls. Bytes are preserved without resizing, with `--image-detail high` by default (`auto`/`low` also available). High detail requests provider inspection quality; it does not guarantee every fine feature is readable. The receipt records attachment paths, types, byte counts and hashes without echoing pixels. Visual advice asks for concrete observations, fixes and requested views under 4,000 characters, rather than the ordinary 160-word target. An attachment receipt proves what was sent; only image-backed feedback establishes what was inspected.

The experts service must already be running with the GPT-6.1 Sol-only configuration in the Subroute gateway checkout. Its current [Compose configuration](https://github.com/stancsz/subroute/blob/main/docker-compose.yml) defines `docker compose up -d experts`; the expert listener is loopback-only on port 4040. Set `EXPERTS_API_KEY` in the caller environment only if that optional service key is configured. Never put a credential in a packet or write it to a file. Installing this skill does not install, start or authenticate the external gateway service.

## Let the expert independently read more

Use reader mode when the Advisor may need to independently dispatch a source reader beyond the compact packet. Enable it at the start when source uncertainty is plausible; the Advisor decides whether to read and what to ask, and can finish without dispatching a reader. Combine `--image` with `--reader-root` and explicit `--reader-scope` values for image-backed consultation with optional source investigation. Read [Advisor Reader](references/reader.md) before using it for setup and limits.

Pi is a separate, ephemeral harness using `http://localhost:4000/v1`, never direct OpenAI credentials. It receives only the expert's evidence question and an approved source snapshot, not the worker's conversation or conclusions. It can read and search, but cannot implement, run shell commands, or delegate again. This reduces shared-context bias; it does not guarantee unbiased findings.

Ordinary reader mode uses the task-wide ceilings above; required risk/visual consultation uses its stated allowance while each reader invocation remains bounded. Each Pi task returns a compact evidence brief. Independent Pi tasks may run in parallel; dependent questions wait for findings. Stop early once evidence supports the current decision. Use the direct one-call path when no independent source reading is needed.

## Resume worker ownership

Treat advice as a hypothesis. Choose the smallest safe experiment that can confirm or reject it, implement the resulting change yourself, and run relevant verification within the original recovery allowance. Record actual reported usage when it affects a cost or quota decision. An unavailable, malformed, or incomplete advisor answer is visible failure, not permission to proceed as if advice was received.

Before consulting, state the worker's intended next action in one sentence. After verification, record `decision_changed: true` only if the advice changed the implementation or verification action; otherwise record `false`. Pair that boolean with provider usage. This is the minimum receipt for deciding whether advisor tokens created practical value rather than merely restating a plan.

An advisor response is not proof that the implementation works. The current worker remains responsible for changes, development checks, authorized external actions, recovery accounting and its handoff evidence. A separate nonauthor reviewer owns acceptance testing and QA; advice cannot waive that separation.
