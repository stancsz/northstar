# Codex Advisor

**Pair a fast, low-cost executor (Luna Max in Codex CLI, or Qwen 3.8 27B in Claude Code) with a smart frontier advisor (Astra / Sol)—cutting task cost by up to 99% without losing frontier judgment.**

Running a frontier model for every file read, edit, and test loop burns tokens fast. **Codex Advisor** flips the pattern: your fast executor does all the local legwork, prepares a compact summary packet (under 2,000 characters), asks **one sharp question**, and gets back a 4-line reply (`Verdict`, `Next`, `Prompt`, `Risk`) to execute in its next turn. The advisor can use **your Codex subscription directly** or **any custom API/gateway URL** (`EXPERTS_BASE_URL`).

> **Not for Codex Desktop's built-in session takeover:** Do **not** use this skill with Codex Desktop's native connection where Codex takes over the session—once Codex Desktop takes over, the advisor/host loop tends to burn tokens on unnecessary tool calls and side exploration. Keep a cheap **CLI** executor (**Codex CLI** or **Claude Code**) in the driver's seat and call [`ask_expert.py`](skills/advisor/scripts/ask_expert.py) only for 1-turn advice.

[Install & Setup](docs/misc/install.md) · [Advisor Skill](skills/advisor/SKILL.md) · [License](LICENSE)

---

## The Pattern: Cheap Executor + Smart Advisor

| Setup | Executor (Does the Work) | Advisor (1-Turn Guidance) | Result |
| :--- | :--- | :--- | :--- |
| **Codex CLI** | **Luna Max** (reads files, edits, runs tests) | **Astra / Sol** (via Codex subscription or custom URL) | Up to **99% cost reduction** on multi-step coding tasks while keeping frontier architecture & debugging quality. |
| **Claude Code** | **Qwen 3.8 27B** / fast local or open-weights model | **Astra / Sol** (via custom URL or Codex subscription) | Same low-cost execution loop in Claude Code with frontier unblocking on hard decisions. |

### Why It Saves Tokens

| Problem | How Codex Advisor Solves It |
| :--- | :--- |
| **Frontier models burn tokens reading files and logs** | The executor reads files and runs tests locally, sending only 3–5 verified facts + 1 error snippet (≤ 400 chars). |
| **Vague prompts produce bloated, unfocused advice** | [`SKILL.md`](skills/advisor/SKILL.md) enforces a strict 4-part packet (`Decision`, `Verified Facts`, `Tried & Constraints`, `1 Sharp Question`) with Good vs. Bad examples. |
| **Multi-turn subagent loops stall on permissions & cache misses** | Every consultation is a **1-turn, tool-free call** returning `Verdict`, `Next`, `Prompt`, and `Risk` (≤ 150 words). The executor runs the turn itself. |
| **Different tooling for Codex CLI vs. Claude Code** | One skill ([`skills/advisor/`](skills/advisor/SKILL.md)) and one Python caller ([`ask_expert.py`](skills/advisor/scripts/ask_expert.py)) work identically in both. |

---

## How It Works

1. **Executor prepares a minimal packet** (`≤ 2,000` chars target, `4,000` hard cap):
   - **Decision / Blocker:** 1 sentence.
   - **Verified Facts:** 3–5 bullets from actual files/tests (no raw log dumps).
   - **Tried & Constraints:** 1 bullet.
   - **1 Sharp Question:** Specific enough to change the next turn.
2. **Advisor responds in 1 turn** (`≤ 150` words):
   - `Verdict:` One decisive sentence.
   - `Next:` Up to 3 short, testable actions.
   - `Prompt:` One ready-to-execute instruction for the executor's next turn.
   - `Risk:` One material risk or stop condition (`none` if clear).
3. **Executor runs the turn** and only re-consults if new evidence creates a new decision fork.

---

## Advisor Backends (Custom URL or Codex Subscription)

[`ask_expert.py`](skills/advisor/scripts/ask_expert.py) supports `--transport auto|gateway|codex|claude`:

- **`codex` (Codex Subscription Directly):** Uses your existing Codex CLI sign-in (`~/.codex/auth.json` via `codex login`) directly—no separate gateway or API key needed.
- **`gateway` (Custom URL):** Point `EXPERTS_BASE_URL` (and `EXPERTS_API_KEY`) to any OpenAI-compatible `/v1` endpoint (LiteLLM, Subroute, OpenRouter, etc.), with optional `--image` screenshot attachments.
- **`claude`:** Invokes `claude -p --no-session-persistence --tools ""` for simple text consultations.
- **`auto`** *(default)*: Uses `EXPERTS_BASE_URL` if configured and reachable; otherwise falls back to your Codex subscription or local `claude` CLI.

---

## Install & Test

See [the installation guide](docs/misc/install.md) for Codex CLI and Claude Code installation steps, global `AGENTS.md` / `CLAUDE.md` snippets, and highest-privilege Codex configuration.

Run the offline regression suite:

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
```
