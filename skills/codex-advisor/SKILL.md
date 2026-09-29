---
name: codex-advisor
description: Use compact Sol or Astra advice to unblock an agent task while keeping execution and verification with the current worker. Codex-native and usable by other agents with the configured advisor service.
---

# Codex Advisor

Use this skill in other agents too; the Codex name is not a usage restriction. Follow the bundled [host adaptation guidance](../northstar/SKILL.md#use-with-other-agents); the advisor service and reader prerequisites still apply.

Use this skill when the current worker has a concrete decision blocker that focused local investigation has not resolved. The advisor is a short-lived reviewer; the current worker retains task ownership, implementation and development checks; independent QA owns acceptance verification. Advice does not replace that verdict. Follow [Northstar's expert consultation practice](../northstar/references/operating-system.md#bring-in-expertise), including its recovery and alternative-trial limits.

Contents: [Choose whether to consult](#choose-whether-to-consult) · [Recovery limits](#keep-consultation-within-the-existing-recovery-boundary) · [Compact request](#make-a-compact-advice-request) · [Reader mode](#let-the-expert-independently-read-more) · [Resume ownership](#resume-worker-ownership)

## Choose whether to consult

Do not consult for routine implementation, an untested hypothesis, a question answerable from local code or documentation, or to have an expert perform the work. First make the smallest useful local check and compact the result.

Consult only when all four conditions hold:

1. The current worker has a specific objective and a concrete blocker or decision.
2. Focused source or documentation inspection plus a targeted test or bounded attempt produced ambiguity, competing paths, or a repeatable failure.
3. No cheaper local observation would resolve the question.
4. One precise question could change the worker's next experiment or plan. Use a second question only when it is needed to interpret the first.

Do not consult for missing credentials or permissions, an unresolved user choice, work that only needs implementation time, or generic reassurance.

Use Sol first for diagnosis, a design fork, a failed test path, or a bounded challenge to an implementation plan. An advisor that coauthors the plan is not its independent acceptance reviewer; expertise does not bypass role separation. Use Astra only when the unresolved question has high leverage or spans multiple subsystems, security or data-loss risk, or when direct evidence and a Sol answer leave a specific decision unresolved. Escalate from Sol to Astra only when Sol identifies a system-level tradeoff, its suggested experiment fails, or two evidence-backed paths have materially different consequences. Do not ask both models the same question just to vote.

## Keep consultation within the existing recovery boundary

One consultation is the default. In ordinary mode, the maximum is two expert calls total for the task: Sol first, then only one distinct follow-up after the suggested check or an evidence-backed Astra escalation. State the reason for that second call. Reader mode replaces the ordinary allowance and has ceilings of three expert calls and three Pi tasks total for the task, not per invocation. Start reader mode before any consultations; do not switch into it after ordinary calls. These are ceilings, not fresh retry windows or targets. A call limit never resets failed-attempt counts, reopens exhausted investigation, grants another implementation trial, or expands the single alternative allowance. Apply the stricter remaining task and Northstar recovery limits. Stop as soon as evidence supports a decision. Do not automatically retry a failed consultation with another model or make a third ordinary-mode call without the user's direction.

## Make a compact advice request

The dedicated expert API is `http://127.0.0.1:4040/v1`, not the worker gateway on port 4000. It exposes only `codex-sol-advisor` and `codex-astra-advisor`; do not substitute an executor alias or silently fall back to port 4000.

Write a high-density packet, normally under 4,000 characters and never over 6,000. Keep only information that could change the recommendation:

1. The decision or blocker in one sentence.
2. Three to six observed facts, each as one bullet. Include at most one exact error or code excerpt, no longer than 400 characters.
3. Constraints and already-rejected paths in one short bullet.
4. One decision question. Add a second only when it directly depends on the first.

Remove chronology, raw logs, full source files, duplicated conclusions, speculation, and any fact that cannot change the decision. Strip secrets. Ask for a verdict, the smallest next experiment, and a material stop condition. The advisor must not write code, use tools, issue commands with side effects, or complete the task.

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

Use `--model astra` only under the criteria above. The experts service must already be running in the Subroute gateway checkout. Its current [Compose configuration](https://github.com/stancsz/subroute/blob/main/docker-compose.yml) defines `docker compose up -d experts`; the expert listener is loopback-only on port 4040. Set `EXPERTS_API_KEY` in the caller environment only if that optional service key is configured. Never put a credential in a packet or write it to a file. Installing this skill does not install, start or authenticate the external gateway service.

## Let the expert independently read more

Use reader mode only when a legitimate consultation needs source evidence beyond the compact packet. Read [Advisor Reader](references/reader.md) before using it for setup and limits.

Pi is a separate, ephemeral harness using `http://localhost:4000/v1`, never direct OpenAI credentials. It receives only the expert's evidence question and an approved source snapshot, not the worker's conversation or conclusions. It can read and search, but cannot implement, run shell commands, or delegate again. This reduces shared-context bias; it does not guarantee unbiased findings.

Reader mode uses the shared task-wide ceilings described above. Each Pi task can use multiple bounded model/tool calls and returns a compact evidence brief. Independent Pi tasks may run in parallel; dependent questions wait for findings. Stop early once evidence supports a decision. Default to the ordinary one-call path when the packet already suffices.

## Resume worker ownership

Treat advice as a hypothesis. Choose the smallest safe experiment that can confirm or reject it, implement the resulting change yourself, and run relevant verification within the original recovery allowance. Record actual reported usage when it affects a cost or quota decision. An unavailable, malformed, or incomplete advisor answer is visible failure, not permission to proceed as if advice was received.

Before consulting, state the worker's intended next action in one sentence. After verification, record `decision_changed: true` only if the advice changed the implementation or verification action; otherwise record `false`. Pair that boolean with provider usage. This is the minimum receipt for deciding whether advisor tokens created practical value rather than merely restating a plan.

An advisor response is not proof that the implementation works. The current worker remains responsible for changes, development checks, authorized external actions, recovery accounting and its handoff evidence. A separate nonauthor reviewer owns acceptance testing and QA; advice cannot waive that separation.
