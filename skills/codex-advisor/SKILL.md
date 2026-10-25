---
name: codex-advisor
description: Consult GPT-6.1 Sol for material uncertainty, relevant capability risks or visual decisions; use council when a second perspective can change the action. Send compact evidence and actual image attachments; retain worker ownership. Codex-native and usable by other agents.
---

# Codex Advisor

Follow Northstar's [delivery contract](../northstar/SKILL.md#delivery-contract). Load this companion only for its advisory function.


Use this skill in other agents too; the Codex name is not a usage restriction. Follow the bundled [host adaptation guidance](../northstar/SKILL.md#use-with-other-agents); the advisor service and reader prerequisites still apply.

**Default Advisor is GPT-6.1 Sol.** The caller's `--model sol` choice targets the versioned `codex-gpt-6.1-sol-advisor` route. For a complex text decision where a second perspective could change the next action, `--council` makes one independent Gemini 4 Argon call first, then one GPT-6.1 Sol call with both the original packet and Gemini's review. Sol must give its own verdict and explain agreement or disagreement. This is not a model vote or independent acceptance. No Astra, older Sol, worker-model substitution or model fallback. If a selected call fails, report it as unavailable; do not silently replace it. Pi remains a separately scoped source reader.

Use this skill when a material uncertainty, relevant capability limitation or unresolved visual decision could change delivery. Consult early when the consequence makes trial and error inappropriate; a topic label alone is not a trigger. Use council for a material unresolved text decision when an independent second view can change the choice. Keep implementation and independent acceptance with their owners; advice grants no additional authority.

Contents: [Capability risks](#consult-early-and-frequently-on-capability-risks) · [Mandatory visual guidance](#mandatory-visual-and-aesthetic-guidance) · [Choose whether to consult](#choose-whether-to-consult) · [Recovery limits](#keep-consultation-within-the-existing-recovery-boundary) · [Compact request](#make-a-compact-advice-request) · [Reader mode](#let-the-expert-independently-read-more) · [Resume ownership](#resume-worker-ownership)

## Consult early and frequently on capability risks

Use the [risk register](references/capability-triggers.md) as evidence of possible limitations, not a mandatory consultation list. Identify the concrete decision, consequence and missing evidence. Resolve a routine factual question locally; consult before committing when a relevant capability gap makes that insufficient. Group overlapping risks into one packet.

Reconsult only for a distinct material decision, changed evidence or a failed recommendation whose repair needs expert judgment. Retain prior advice and failed receipts. A new risk tag does not reset recovery. Stop when the decision is supported; no reassurance calls or hidden model fallback.

## Mandatory visual and aesthetic guidance

When consulting about a visual decision, actual image evidence is mandatory: attach current screenshots or images with `--image`, identifying the artifact, state and criteria. A path, OCR, source code or prose description cannot establish appearance. Request concrete observations and the smallest repair; provide requested crops or alternate states only when needed to judge the current criterion.

Consult before an unresolved visual direction or material aesthetic risk, and return repaired views when the failed criterion needs expert recheck. Reusing an accepted design or making an ordinary change with adequate rendered verification does not automatically require another consultation. Stop at agreed acceptance; optional taste changes follow the shared diminishing-returns rule. Missing required image evidence stays unverified.

An advisor who directed the design is not its independent acceptance reviewer. One uninvolved qualified reviewer may cover functional and visual acceptance together. Human aesthetic approval applies only if the user explicitly retained it.

## Choose whether to consult

When no material capability or visual uncertainty applies, do not consult for routine implementation, an untested hypothesis, a question answerable from local code or documentation, or to have an expert perform the work. First make the smallest useful local check and compact the result. [Capability-risk consultation](#consult-early-and-frequently-on-capability-risks) and [mandatory visual guidance](#mandatory-visual-and-aesthetic-guidance) take precedence when their triggers apply.

For ordinary consultation outside those triggers, all four conditions must hold:

1. The current worker has a specific objective and a concrete blocker or decision.
2. Focused source or documentation inspection plus a targeted test or bounded attempt produced ambiguity, competing paths, or a repeatable failure.
3. No cheaper local observation would resolve the question.
4. One precise question could change the worker's next experiment or plan. Use a second question only when it is needed to interpret the first.

Do not consult for missing credentials or permissions, an unresolved user choice, work that only needs implementation time, or generic reassurance.

Use GPT-6.1 Sol for diagnosis, a design fork, a failed test path or a bounded challenge to an implementation plan. An advisor that coauthors the plan is not its independent acceptance reviewer; expertise does not bypass role separation. Unresolved decisions require changed evidence or a scoped follow-up to the same Advisor, never Astra escalation or a model vote.

## Keep consultation within the existing recovery boundary

Default to one bounded consultation for the current decision; allow one distinct follow-up when new evidence makes it useful. A council invocation uses one Sol call plus one Gemini call. Ordinary reader mode allows at most three expert calls and three Pi tasks; council and reader cannot be combined. These are ceilings, not targets or retry windows.

A required unresolved criterion may justify further image-backed or capability-risk guidance only when the next call can change a concrete action and stays within existing resources and recovery. Optional refinement stops at diminishing returns. Never reopen exhausted investigation or add implementation trials by consulting again.

## Make a compact advice request

The dedicated expert API is `http://127.0.0.1:4040/v1`, separate from the worker gateway on port 4000. The skill uses `codex-gpt-6.1-sol-advisor` for Sol and, only in council mode, `gemini-4-argon-advisor` for Gemini Subscription at low reasoning effort. The versioned Sol alias intentionally fails on an older service rather than silently using older Sol. Do not substitute an executor alias or silently fall back to port 4000.

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
python (Join-Path $codexAdvisor 'scripts\ask_expert.py') --model sol --input-file .\advisor-packet.txt
```

For a complex text decision with a concrete reason for an independent second view, add `--council` to the command above. Gemini receives the packet without Sol's opinion. Sol receives the same packet plus Gemini's bounded review, gives its own verdict, and then assesses the review. A successful receipt includes both answers, model IDs and provider usage. The caller makes at most one call to each model, with no retry or fallback; Gemini failure stops before Sol. Council mode cannot be combined with image attachments or Pi reader mode; use Sol's image-backed path for visual decisions.

For visual advice, attach the overall view and useful details proactively. The text packet supplies criteria, revision/state, reference roles and the next decision; image bytes are separate from its character budget:

```powershell
python (Join-Path $codexAdvisor 'scripts\ask_expert.py') --model sol --input-file .\advisor-packet.txt --image .\current.png --image .\detail.png
```

Supported files are PNG, JPEG, WebP and GIF, with at most eight images, 10 MB per file and 20 MB total per call; split further requested views into calls. Bytes are preserved without resizing, with `--image-detail high` by default (`auto`/`low` also available). High detail requests provider inspection quality; it does not guarantee every fine feature is readable. The receipt records attachment paths, types, byte counts and hashes without echoing pixels. Visual advice asks for concrete observations, fixes and requested views under 4,000 characters, rather than the ordinary 160-word target. An attachment receipt proves what was sent; only image-backed feedback establishes what was inspected.

The experts service must already be running with the Sol and Gemini Advisor routes in the Subroute gateway checkout. Its current [Compose configuration](https://github.com/stancsz/subroute/blob/main/docker-compose.yml) defines `docker compose up -d experts`; port 4040 is LAN-published and requires bearer authentication. The Gemini route uses the existing Antigravity subscription bridge. Set `EXPERTS_API_KEY` in the caller environment to match the service key. Never put a credential in a packet or write it to a file. Installing this skill does not install, start or authenticate the external gateway service.

On Windows, the caller also reads `EXPERTS_API_KEY` from the Windows user environment for the default local service (`http://127.0.0.1:4040`, `localhost` or `::1`). This lets an already-open desktop app use a newly configured key without restarting. An explicit process variable takes precedence, including an empty value; other hosts, schemes and ports require the process variable. The caller never follows redirects or retries a failed request. HTTP 401 means the service key is missing or rejected: correct that configuration before trying again; do not disable service authentication or change gateways.

## Let the expert independently read more

Use reader mode when the Advisor may need to independently dispatch a source reader beyond the compact packet. Enable it at the start when source uncertainty is plausible; the Advisor decides whether to read and what to ask, and can finish without dispatching a reader. Combine `--image` with `--reader-root` and explicit `--reader-scope` values for image-backed consultation with optional source investigation. Read [Advisor Reader](references/reader.md) before using it for setup and limits.

Pi is a separate, ephemeral harness using `http://localhost:4000/v1`, never direct OpenAI credentials. It receives only the expert's evidence question and an approved source snapshot, not the worker's conversation or conclusions. It can read and search, but cannot implement, run shell commands, or delegate again. This reduces shared-context bias; it does not guarantee unbiased findings.

Ordinary reader mode uses the task-wide ceilings above; required risk/visual consultation uses its stated allowance while each reader invocation remains bounded. Each Pi task returns a compact evidence brief. Independent Pi tasks may run in parallel; dependent questions wait for findings. Stop early once evidence supports the current decision. Use the direct one-call path when no independent source reading is needed.

## Resume worker ownership

Treat advice as a hypothesis. Choose the smallest safe experiment that can confirm or reject it, implement the resulting change yourself, and run relevant verification within the original recovery allowance. Record actual reported usage when it affects a cost or quota decision. An unavailable, malformed, or incomplete advisor answer is visible failure, not permission to proceed as if advice was received.

Before consulting, state the worker's intended next action in one sentence. After verification, record `decision_changed: true` only if the advice changed the implementation or verification action; otherwise record `false`. Pair that boolean with provider usage. This is the minimum receipt for deciding whether advisor tokens created practical value rather than merely restating a plan.

An advisor response is not proof that the implementation works. The current worker remains responsible for changes, development checks, authorized external actions, recovery accounting and its handoff evidence. A separate nonauthor reviewer owns acceptance testing and QA; advice cannot waive that separation.
