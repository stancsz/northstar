---
name: advisor
description: Consult a frontier advisor model in 1 fast turn with a minimal, non-bloated summary packet to get Verdict/Next/Prompt/Risk guidance for Codex CLI and Claude Code.
---

# Advisor

Get decisive judgment from a frontier advisor model **without wasting advisor tokens**. You (the caller CLI agent in Codex CLI or Claude Code) own all file reading, editing, builds, and tests. The advisor never runs multi-turn tool loops—you send a distilled summary, get a short `Verdict / Next / Prompt / Risk` reply, and execute the next turn yourself.

> **Standalone 1-call advisor (never a native subagent):** Do **not** use Codex Desktop's native subagent (`spawn_agent`) as the advisor. `scripts/ask_expert.py` makes **one standalone, tool-free call** using your **Codex subscription directly** (or a custom URL). All tools, file reads, edits, and tests stay on **you (the caller agent)**—you do all the heavy lifting.

## When to consult (and when NOT to)

**Consult when:**
- You hit a genuine design fork, architecture tradeoff, or stubborn bug after running at least one local check.
- An unresolved UI/layout decision needs a visual check (`--image`).
- Trial-and-error in code would cost more time/tokens than one sharp question.

**Do NOT consult when:**
- You have not read the relevant file or run the failing command yet.
- The answer is obvious from local code, docs, or a single test run.
- You just want reassurance on routine implementation.

## How to ask a good question (just enough info, zero bloat)

Target **under 2,000 characters** (hard cap **4,000**). Every wasted line in your packet burns frontier tokens and dilutes the answer.

Include **only**:
1. **Decision / Blocker (1 sentence):** What choice or failure is blocking your next turn.
2. **Verified Facts (3–5 short bullets):** Concrete file paths, observed behavior, and at most **one** exact error or code snippet (≤ 400 chars).
3. **Tried & Constraints (1 bullet):** What you already ruled out and any hard constraint.
4. **1 Sharp Question:** A specific question whose answer changes your next action.

**Strip completely:** raw stack traces, full files, chat history, speculative theories, and unrelated side issues.

### Good vs. Bloated Packet

**Bad (bloated, vague):**
> We are building auth in our app and tests are failing. Here is the 200-line `auth.py` and the full pytest log: `[...]`. What should we do? Can you also check if our folder structure is good?

**Good (sharp, minimal):**
> **Decision:** Token refresh races when two concurrent 401 responses trigger `refreshSession()` in `src/auth/client.ts`.
> **Facts:**
> - `client.ts:42` calls `POST /auth/refresh` without an in-flight lock; second call sends the rotated-out token and gets `401 invalid_grant`.
> - Existing `tests/auth.test.ts` passes sequentially but fails under `Promise.all([fetchA(), fetchB()])`.
> - Constraint: No external state store; must stay browser-side in `client.ts`.
> **Tried:** Added retry-once on 401, which still double-refreshes under concurrency.
> **Question:** Should `refreshSession()` deduplicate via a module-level in-flight `Promise` singleton cleared in `finally`, or is a BroadcastChannel lock needed across tabs?

## Work in turns (with delta rounds & budget)

1. **Send Round 1** via `scripts/ask_expert.py --session-file ./tmp/advisor-session.json --max-rounds 3`.
2. **Read the 4-line reply** (≤ 150 words):
   - `Verdict:` One decisive sentence.
   - `Next:` Up to 3 short, testable steps.
   - `Prompt:` A ready-to-execute instruction for your next turn.
   - `Risk:` One material risk or stop condition (`none` if clear).
3. **Execute the turn yourself** (edit, run tests, verify).
4. **If another round is needed, send a tiny delta packet** (target <= 600 chars: only what you ran, what changed, and your new question). `--session-file` automatically prepends `Prior Verdict` (~200 chars) and enforces `--max-rounds` so Round 2+ uses **even fewer input tokens** than Round 1. Never re-send Round 1's background.

## Invoke from Codex CLI or Claude Code

Resolve the installed `advisor` skill directory (`~/.codex/skills/advisor`, `~/.agents/skills/advisor`, or `~/.claude/skills/advisor`) and run `scripts/ask_expert.py`.

**PowerShell (Windows):**
```powershell
$advisorDir = @(
    $(if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills\advisor' }),
    (Join-Path $env:USERPROFILE '.codex\skills\advisor'),
    (Join-Path $env:USERPROFILE '.agents\skills\advisor'),
    $(if ($env:CLAUDE_CONFIG_DIR) { Join-Path $env:CLAUDE_CONFIG_DIR 'skills\advisor' }),
    (Join-Path $env:USERPROFILE '.claude\skills\advisor')
) | Where-Object { $_ -and (Test-Path (Join-Path $_ 'SKILL.md')) } | Select-Object -First 1
if (-not $advisorDir) { throw 'advisor skill directory not found.' }
python (Join-Path $advisorDir 'scripts\ask_expert.py') --input-file .\advisor-packet.txt
```

**Bash (macOS / Linux / Git Bash):**
```bash
ADVISOR_DIR=$(for d in "${CODEX_HOME:+$CODEX_HOME/skills}" "$HOME/.codex/skills" "$HOME/.agents/skills" "${CLAUDE_CONFIG_DIR:+$CLAUDE_CONFIG_DIR/skills}" "$HOME/.claude/skills"; do [ -f "$d/advisor/SKILL.md" ] && echo "$d/advisor" && break; done)
python3 "$ADVISOR_DIR/scripts/ask_expert.py" --input-file ./advisor-packet.txt
```

### Transport & options
- `--transport auto` *(default)*: Uses `EXPERTS_BASE_URL` (`/chat/completions` + `/responses/input_tokens`) if configured and reachable; otherwise falls back to local Codex auth (`~/.codex/auth.json`) or local `claude` CLI (`claude -p --no-session-persistence --tools ""`).
- `--transport gateway`: Require the configured OpenAI-compatible gateway (`EXPERTS_BASE_URL` and `EXPERTS_API_KEY`).
- `--transport codex`: Direct Codex text consultation (`gpt-6.1-terra` or `gpt-6.1-sol`).
- `--transport claude`: Direct Claude Code CLI text consultation (`claude -p`).
- `--model <name>`: Exact advisor model identifier (or set `NORTHSTAR_ADVISOR_MODEL`).
- `--session-file <path>` & `--max-rounds <n>`: Optional round-budget tracker (default `3` rounds). Automatically prepends `Prior Verdict` on Round 2+ so you only send a short delta packet.
- `--image <path>`: Attach up to 8 local PNG/JPEG/WebP/GIF screenshots for visual/UI advice (requires `--transport gateway` / `auto` with gateway).
