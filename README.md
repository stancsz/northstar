# Codex Advisor

**A single, token-efficient advisor skill for Codex CLI and Claude Code.**

Instead of letting an expensive frontier model run long, multi-turn tool loops or read raw logs, **Codex Advisor** teaches your coding agent to do the local legwork first, prepare a compact summary packet (under 2,000 characters), ask **one sharp question**, and receive a 4-line reply (`Verdict`, `Next`, `Prompt`, `Risk`) to execute in its next turn.

[Install & Setup](docs/misc/install.md) · [Advisor Skill](skills/advisor/SKILL.md) · [License](LICENSE)

---

## Why Advisor?

| Problem | How Advisor Solves It |
| :--- | :--- |
| **Frontier models burn tokens reading files and logs** | The caller agent reads files and runs tests locally, sending only 3–5 verified facts + 1 error snippet (≤ 400 chars). |
| **Vague prompts produce bloated, unfocused advice** | [`SKILL.md`](skills/advisor/SKILL.md) enforces a strict 4-part packet (`Decision`, `Verified Facts`, `Tried & Constraints`, `1 Sharp Question`) with Good vs. Bad examples. |
| **Multi-turn subagent loops stall on permissions & cache misses** | Every consultation is a **1-turn, tool-free call** returning `Verdict`, `Next`, `Prompt`, and `Risk` (≤ 150 words). The caller executes the turn. |
| **Different tooling for Codex CLI vs. Claude Code** | One skill ([`skills/advisor/`](skills/advisor/SKILL.md)) and one Python caller ([`ask_expert.py`](skills/advisor/scripts/ask_expert.py)) work across both Codex CLI and Claude Code. |

## How It Works

1. **Caller prepares a minimal packet** (`≤ 2,000` chars target, `4,000` hard cap):
   - **Decision / Blocker:** 1 sentence.
   - **Verified Facts:** 3–5 bullets from actual files/tests (no raw log dumps).
   - **Tried & Constraints:** 1 bullet.
   - **1 Sharp Question:** Specific enough to change the next turn.
2. **Advisor responds in 1 turn** (`≤ 150` words):
   - `Verdict:` One decisive sentence.
   - `Next:` Up to 3 short, testable actions.
   - `Prompt:` One ready-to-execute instruction for the caller's next turn.
   - `Risk:` One material risk or stop condition (`none` if clear).
3. **Caller executes the turn** and only re-consults if new evidence creates a new decision fork.

## Transports

[`ask_expert.py`](skills/advisor/scripts/ask_expert.py) supports `--transport auto|gateway|codex|claude`:
- **`gateway`**: OpenAI-compatible `/chat/completions` + `/responses/input_tokens` (`EXPERTS_BASE_URL`, `EXPERTS_API_KEY`), with optional `--image` attachments.
- **`codex`**: Direct Codex CLI auth (`~/.codex/auth.json`) for text consultations (`gpt-6.1-terra` or `gpt-6.1-sol`).
- **`claude`**: Direct Claude Code CLI (`claude -p --no-session-persistence --tools ""`) for text consultations.
- **`auto`** *(default)*: Uses `EXPERTS_BASE_URL` when configured and reachable, otherwise falls back to local Codex auth or `claude` CLI.

## Install & Test

See [the installation guide](docs/misc/install.md) for Codex CLI and Claude Code installation steps, global `AGENTS.md` / `CLAUDE.md` snippets, and highest-privilege Codex configuration.

Run the offline regression suite:

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
```
