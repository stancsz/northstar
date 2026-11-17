# Codex Advisor

**Pair a fast, low-cost executor (`gpt-6-luna` Max in Codex CLI, or `Qwen 3.8 27B` in Claude Code) with a smart frontier advisor (`gpt-6.2-astra` / `gpt-6.2-sol`)—cutting task cost by up to 99% without losing frontier judgment.**

Running a frontier model for every file read, edit, and test loop burns tokens fast. **Codex Advisor** flips the pattern: your fast CLI executor does all the heavy lifting locally, prepares a compact summary packet (under 2,000 characters), asks **one sharp question**, and gets back a 4-line reply (`Verdict`, `Next`, `Prompt`, `Risk`) to execute in its next turn.

> **Standalone 1-call advisor (never a native subagent):** Never spawn a Codex Desktop / native subagent (`spawn_agent`) as the advisor. [`ask_expert.py`](skills/advisor/scripts/ask_expert.py) makes **one standalone, tool-free call** using your **Codex subscription directly** (default #1 route) or a custom URL. All tools, file reads, code edits, and tests stay on the **caller agent**.

[Install & Setup](docs/install.md) · [Advisor Skill](skills/advisor/SKILL.md) · [License](LICENSE)

---

## The Pattern: Cheap Executor + Smart Advisor

| Host | Executor (Owns Tools & Heavy Lifting) | Advisor (1-Turn Guidance) | Result |
| :--- | :--- | :--- | :--- |
| **Codex CLI** | **`gpt-6-luna` Max** (reads files, edits, runs tests) | **`gpt-6.2-astra` / `gpt-6.2-sol`** (via Codex subscription #1 or custom URL) | Up to **99% cost reduction** on multi-step coding tasks while keeping frontier architecture & debugging quality. |
| **Claude Code** | **`Qwen 3.8 27B`** / fast local or open-weights model | **`gpt-6.2-astra` / `gpt-6.2-sol`** (via Codex subscription #1 or custom URL) | Same low-cost execution loop in Claude Code with frontier unblocking on hard decisions. |

### Why It Saves Tokens

| Problem | How Codex Advisor Solves It |
| :--- | :--- |
| **Frontier models burn tokens reading files and logs** | The executor reads files and runs tests locally, sending only 3–5 verified facts + 1 error snippet (<= 400 chars). |
| **Vague prompts produce bloated, unfocused advice** | [`SKILL.md`](skills/advisor/SKILL.md) enforces a strict 4-part packet (`Decision`, `Verified Facts`, `Tried & Constraints`, `1 Sharp Question`) with Good vs. Bad examples. |
| **Multi-round history re-sends bloat every turn** | `--session-file` tracks your round budget (`--max-rounds`, default `3`) and automatically prepends only `Prior Verdict` (~200 chars) on Round 2+, so follow-up rounds use even fewer input tokens than Round 1. |
| **Native subagents spin up expensive tool loops** | Every consultation is a **1-turn, tool-free call** returning `Verdict`, `Next`, `Prompt`, and `Risk` (<= 120 words). |

---

## How It Works

1. **Executor prepares a minimal packet** (`<= 2,000` chars target, `4,000` hard cap):
   - **Decision / Blocker:** 1 sentence.
   - **Verified Facts:** 3–5 bullets from actual files/tests (no raw log dumps).
   - **Tried & Constraints:** 1 bullet.
   - **1 Sharp Question:** Specific enough to change the next turn.
2. **Advisor responds in 1 turn** (`<= 120` words):
   - `Verdict:` One decisive sentence.
   - `Next:` Up to 3 short, testable actions.
   - `Prompt:` One short next-turn instruction for the executor.
   - `Risk:` One material risk or stop condition (`none` if clear).
3. **Executor runs the turn — and sends only a tiny delta if Round 2 is needed:** Passing `--session-file <path> --max-rounds 3` tracks your round budget and prepends only `Prior Verdict` (~200 chars) on Round 2+, keeping follow-up input tokens minimal.

---

## Advisor Transports (`--transport`)

[`ask_expert.py`](skills/advisor/scripts/ask_expert.py) supports `--transport auto|codex|gateway|claude`:

1. **`auto` *(default)*:** Prefers **Direct Codex subscription (`~/.codex/auth.json`) #1** for text consultations (`gpt-6.2-astra`, `gpt-6.2-sol`, `gpt-6-luna`); routes `--image` attachments or custom models to `gateway` (`EXPERTS_BASE_URL`), and falls back to local `claude` CLI if needed.
2. **`codex`:** Direct Codex subscription (`~/.codex/auth.json` via `codex login`)—no separate gateway or API key needed.
3. **`gateway`:** OpenAI-compatible `/v1` endpoint (`EXPERTS_BASE_URL` + `EXPERTS_API_KEY`, e.g., LiteLLM, Subroute, OpenRouter), with optional `--image` screenshot attachments.
4. **`claude`:** Local Claude Code CLI (`claude -p --no-session-persistence --tools ""`) for text consultations.

---

## Install & Test

See [the installation guide](docs/install.md) for Codex CLI and Claude Code installation steps, global `AGENTS.md` / `CLAUDE.md` snippets, highest-privilege Codex configuration, and setup gotchas.

Run the offline regression suite:

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
```
