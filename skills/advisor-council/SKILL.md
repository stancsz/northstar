---
name: advisor-council
description: Consult an independent advisor or complexity-based council for capability risks, hard blockers, unresolved visual/design forks, and scoped source reading.
---

# Advisor Council

Follow Northstar's [delivery contract](../northstar/SKILL.md#delivery-contract). Load this companion only when material uncertainty, a documented capability risk, or an unresolved visual/design decision could change delivery. For routine functional or visual acceptance testing, use [Independent QA](../independent-qa/SKILL.md).

- **Complexity-based three-model council:** All calls request low reasoning effort. Exact defaults are `gpt-6.1-terra` (simple/primary; `NORTHSTAR_ADVISOR_MODEL`), `gemini-3.8-flash-low` (complex reviewer; `NORTHSTAR_COUNCIL_MODEL`), and `Claude Sonnet 5.5 Medium` (additional very-complex reviewer; `NORTHSTAR_SONNET_MODEL`). Use `--complexity simple` for Terra, `--complexity complex` for Gemini then Terra, and `--complexity very-complex` for Gemini, Sonnet, then Terra. Explicit model flags and environment variables override defaults; selected names pass unchanged to token counting and inference.
- **Bounded input:** Gateway requests use the configured service's Responses input-token counting endpoint for the exact selected model and complete text/image input, and submit only counts up to 32,000. The direct Codex route has no compatible count endpoint, so it caps the complete UTF-8 request body at 24,000 bytes and reports provider usage after completion. The packet and each council review retain their existing character caps. See [OpenAI's input token counting guide](https://developers.openai.com/api/docs/guides/token-counting).
- **Gateway and direct Codex transports:** `--transport auto` (default) uses the configured Advisor service. It falls back to the local Codex sign-in only when the gateway URL is unset or its input-token request cannot connect or times out before inference. Set `--transport gateway` to require the service, or `--transport codex` to explicitly use Codex. Direct Codex supports one simple text consultation with `gpt-6.1-terra` or `gpt-6.1-sol`. Images, multi-model council tiers, and reader mode require the configured service. The result records its transport and any fallback reason. HTTP errors, invalid token counts, authentication failures, and errors after inference begins remain visible; the caller never changes the selected model.
- **No retry or authority expansion:** A failed request is reported as unavailable. Keep implementation and independent acceptance with their owners; advice is a hypothesis, not a vote or approval.

Contents: [Capability risks](#consult-early-and-frequently-on-capability-risks) · [Mandatory visual guidance](#mandatory-visual-and-aesthetic-guidance) · [Choose whether to consult](#choose-whether-to-consult) · [Recovery limits](#keep-consultation-within-the-existing-recovery-boundary) · [Compact request](#make-a-compact-advice-request) · [Reader mode](#let-the-expert-independently-read-more) · [Resume ownership](#resume-worker-ownership)

## Consult early and frequently on capability risks

Check the [risk register](references/capability-triggers.md) for task conditions where external judgment or evidence can change the next action:
- **Consult before committing** when trial-and-error is costly or a capability gap makes local checks insufficient. Group overlapping risks into one compact packet.
- **Reconsult only on changed evidence** or a distinct material decision. Retain prior advice and failed receipts; a new risk tag never resets the 2-strike recovery count. Stop once the decision is supported—no reassurance calls.

## Mandatory visual and aesthetic guidance

- **Attach real images (`--image`):** Whenever consulting on an unresolved visual, layout, or aesthetic decision, attach actual screenshots or crops (`--image`), naming the artifact, viewport/state, and criteria. A file path, OCR dump, DOM/CSS snippet, or prose description never establishes visual appearance.
- **Repair and recheck:** Request concrete observations and prioritized fixes; supply requested crops or repaired views when the failed criterion needs expert recheck. Stop optional polish at diminishing returns. Missing required image evidence stays **unverified**.
- **Role separation:** An advisor that directed the visual design cannot act as its independent acceptance reviewer ([Independent QA](../independent-qa/SKILL.md)). One uninvolved reviewer may cover functional and visual acceptance together; human aesthetic approval is required only when explicitly retained by the user.

## Choose whether to consult

When no capability-risk or visual trigger applies, **do not consult** for routine implementation, untested hypotheses, questions answerable from local code/docs, missing credentials/permissions, or user-retained choices. First run the smallest local check.

For ordinary consultation outside capability/visual triggers, **all four conditions must hold**:
1. The worker has a specific objective and a concrete blocker or design fork.
2. Focused source/doc inspection plus a targeted test produced ambiguity, competing paths, or a repeatable failure.
3. No cheaper local observation would resolve the question.
4. One precise question (plus at most one dependent follow-up question) could change the next experiment or plan.

## Keep consultation within the existing recovery boundary

- **Ordinary decision ceiling:** Default to **1 bounded consultation** per decision (allow **1 distinct follow-up** only when new evidence warrants it).
- **Council & Reader ceilings:** `--complexity simple` uses 1 call; `complex` uses 1 reviewer + 1 primary call; `very-complex` uses 2 reviewers + 1 primary call. Ordinary reader mode allows at most **3 expert calls** and **3 Pi tasks**; multi-model tiers and reader mode cannot be combined.
- **No retry inflation:** Consultation ceilings are hard caps, not targets, and never reopen exhausted investigation or add implementation retries.

## Make a compact advice request

Configure `EXPERTS_BASE_URL` (or `--base-url`) and `EXPERTS_API_KEY` in the caller environment, and select models via `NORTHSTAR_ADVISOR_MODEL`, `NORTHSTAR_COUNCIL_MODEL`, and `NORTHSTAR_SONNET_MODEL` (or `--model`, `--council-model`, and `--sonnet-model`). On Windows, the caller can read a saved user `EXPERTS_API_KEY` for a local loopback service only when the process environment variable is absent. Never place credentials in a packet or file; on HTTP 401, fix the environment key rather than retrying.

`ask_expert.py` sends a direct OpenAI-compatible Chat Completions request to `{base_url}/chat/completions`. Set the base URL to the service's API prefix, usually including `/v1` (for example, `http://127.0.0.1:PORT/v1`), and make sure that URL is reachable from the process running the script. A Docker service name works only from a container on the matching network; a host process needs a published host port. The caller does not invoke a gateway's model-selected Advisor tool or inherit its saved model selection. Choose a model identifier or alias exposed by the selected Chat Completions service. The default model name is `default`, which works only if that service defines it. A service that exposes Advisor solely as a native tool inside another protocol is not compatible with this direct caller.

Keep the packet under **4,000 characters** (hard limit **6,000**), stripping chronology, raw logs, full files, speculation, and secrets:
1. **Decision or blocker** in one sentence.
2. **3–6 observed facts** as single bullets (at most one exact error/code excerpt ≤ 400 characters).
3. **Constraints and ruled-out paths** in one bullet.
4. **1 decision question** (add a 2nd only if directly dependent) asking for a `Verdict`, smallest `Next` experiment, and `Risk`/stop condition.

Resolve the installed `advisor-council` directory and run `scripts/ask_expert.py`:

```powershell
$skillDirectories = @()
if ($env:CODEX_HOME) { $skillDirectories += Join-Path (Join-Path $env:CODEX_HOME 'skills') 'advisor-council' }
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.agents\skills') 'advisor-council'
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.codex\skills') 'advisor-council'
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.claude\skills') 'advisor-council'
$advisorCouncil = $skillDirectories | Where-Object { Test-Path (Join-Path $_ 'SKILL.md') } | Select-Object -First 1
if (-not $advisorCouncil) { throw 'Set $advisorCouncil to this installation''s advisor-council directory.' }
$advisorCouncil = (Resolve-Path $advisorCouncil).Path
python (Join-Path $advisorCouncil 'scripts\ask_expert.py') --input-file .\advisor-packet.txt
```

Or in POSIX / Git Bash:

```bash
ADVISOR_DIR=$(for d in "${CODEX_HOME:+$CODEX_HOME/skills}" "$HOME/.agents/skills" "$HOME/.codex/skills" "$HOME/.claude/skills"; do [ -f "$d/advisor-council/SKILL.md" ] && echo "$d/advisor-council" && break; done)
python3 "$ADVISOR_DIR/scripts/ask_expert.py" --input-file ./advisor-packet.txt
```

The default `--transport auto` prefers the configured Advisor gateway and uses direct Codex for a simple text consultation if the gateway URL is unset or the input-token request cannot connect or times out. Use `--transport gateway` to require the configured service, or `--transport codex` to select direct Codex explicitly. Direct Codex reads the existing Codex sign-in from `CODEX_AUTH_FILE` or `$CODEX_HOME/auth.json` (`~/.codex/auth.json` by default); it does not use `EXPERTS_API_KEY`. Only `gpt-6.1-terra` and `gpt-6.1-sol` are supported directly. Complex tiers, images, and reader mode require the configured gateway.

- **Council mode (complex text decisions):** Select `--complexity complex` and the exact `--council-model <model-name>`. The council model reviews the packet independently; the primary model evaluates both the packet and council review. Council stops immediately if the council call fails and cannot be combined with `--image` or reader mode.
- **Visual mode (`--image`):** Attach up to 8 PNG/JPEG/WebP/GIF files (≤ 10 MB each, ≤ 20 MB total; `--image-detail high` by default):

```powershell
python (Join-Path $advisorCouncil 'scripts\ask_expert.py') --input-file .\advisor-packet.txt --image .\current.png --image .\detail.png
```

## Let the expert independently read more

Enable reader mode (`--reader-root` and explicit `--reader-scope`) at the start of a consultation when the advisor may need to inspect source files beyond the packet; see [Advisor Reader](references/reader.md).
- The advisor decides whether to dispatch an isolated, read-only Pi worker over the approved Git-tracked UTF-8 snapshot (no worker conversation, shell, writes, or recursive delegation).
- Combine `--image` with `--reader-root` / `--reader-scope` when visual inspection may also need source verification (Pi remains text-only; the advisor sees the images). Stop early once evidence supports the decision.

## Resume worker ownership

1. **State baseline before calling:** Record your intended next action in one sentence before invoking the advisor.
2. **Test the smallest experiment:** Treat advice as a hypothesis, implement the change yourself, and verify within the existing recovery allowance.
3. **Record value receipt:** Log `decision_changed: true` only if the advice changed your implementation or verification action (otherwise `false`), paired with reported provider usage.
4. **Preserve independent QA:** An unavailable or malformed advisor response is a visible failure, and advisor output never replaces development checks or nonauthor [Independent QA](../independent-qa/SKILL.md).
