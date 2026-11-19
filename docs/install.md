# Install and Use Spot Advisor

**Spot Advisor** (`spot-advisor`) is a host-agnostic, token-efficient skill ([`skills/advisor/SKILL.md`](../skills/advisor/SKILL.md)) that lets a fast, low-cost coding agent consult a frontier advisor in 1 tool-free turn.

---

## 1. Install the Skill

### Generic `.agents/skills` (Cross-Agent)

From the repository root in PowerShell:

```powershell
$dest = Join-Path $env:USERPROFILE '.agents\skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Bash on macOS/Linux: `mkdir -p ~/.agents/skills/advisor && cp -R ./skills/advisor/* ~/.agents/skills/advisor/`.)*

### Claude Code

From the repository root in PowerShell:

```powershell
$claudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$dest = Join-Path $claudeDir 'skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Bash on macOS/Linux: `mkdir -p "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor" && cp -R ./skills/advisor/* "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor/"`.)*

### Codex CLI

From the repository root in PowerShell:

```powershell
$dest = Join-Path $env:USERPROFILE '.codex\skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Bash on macOS/Linux: `mkdir -p ~/.codex/skills/advisor && cp -R ./skills/advisor/* ~/.codex/skills/advisor/`.)*

---

## 2. Global Agent Instructions (`AGENTS.md` / `CLAUDE.md`)

Add this rule to your global agent instructions (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, or equivalent) so your fast executor knows when to escalate and keeps packets small:

```markdown
## Use Spot Advisor for hard decisions (zero bloat)
- Do all local file reading, edits, builds, and test runs yourself.
- Never spawn a heavy subagent as the advisor; call `ask_expert.py` for a 1-turn, tool-free response.
- Escalate when blocked by a design fork, 2 consecutive failed fix attempts, or a visual check (`--image`).
- Send a compact packet (target <= 2,000 chars, hard cap 4,000): 1-sentence blocker, 3–5 verified facts (at most 1 short snippet <= 400 chars), what was tried, and 1 sharp question.
- For multi-round debugging, pass `--session-file` and send only a short delta packet on Round 2+.
- Execute the advisor's reply directly in your own next turn.
```

---

## 3. Transport Setup (`--transport`)

[`skills/advisor/scripts/ask_expert.py`](../skills/advisor/scripts/ask_expert.py) defaults to `--transport auto`, routing as follows:

1. **Direct Codex (`--transport auto` #1 default / `--transport codex`):** Uses `~/.codex/auth.json` (`codex login`) directly against ChatGPT OAuth for `gpt-6.2-astra` (default), `gpt-6.2-sol`, or `gpt-6-luna`. No gateway or separate API key required.
2. **OpenAI-Compatible Gateway (`--transport gateway`):** Set `EXPERTS_BASE_URL` (e.g., OpenRouter, LiteLLM, Subroute, `http://127.0.0.1:4040/v1`) and `EXPERTS_API_KEY`. Used automatically by `auto` when `--image` screenshots are attached or when requesting non-Codex models via `--model` / `CODEX_ADVISOR_MODEL`.
3. **Claude Code CLI (`--transport claude`):** Invokes `claude -p --no-session-persistence --tools ""` for text consultations when Codex auth and gateway are unavailable.

---

## 4. Optional Codex CLI / Desktop Appendix

If you run Codex CLI or Codex Desktop with local unrestricted execution, see the optional [Codex Setup Appendix](codex-setup.md) for `config.toml`, OAuth vs. `codex exec` behavior, and Stop-hook gotchas.

[Back to Spot Advisor](../README.md)
