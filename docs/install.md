# Install and Use Spot Advisor

**Spot Advisor** (`spot-advisor`) is a host-agnostic, token-efficient skill ([`skills/advisor/SKILL.md`](../skills/advisor/SKILL.md)) that lets a fast, low-cost coding agent consult a frontier advisor in 1 tool-free turn.

---

## 1. Install the Skill

### Codex and other hosts that discover `.agents/skills`

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

### Hosts configured to read `.codex/skills`

From the repository root in PowerShell:

```powershell
$codexDir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$dest = Join-Path $codexDir 'skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Bash on macOS/Linux: `mkdir -p ~/.codex/skills/advisor && cp -R ./skills/advisor/* ~/.codex/skills/advisor/`.)*

Choose one discoverable Codex copy. An existing `SKILL.md.disabled` marks an inactive copy. Claude Code has its own skill directory.

---

## 2. Use the 2.0 text protocol

Save a task state JSON file. Update its revision when the workspace, evidence, or decision changes.

```json
{
  "task_id": "cache-expiry-fix",
  "revision": "1",
  "goal": "Fix cache expiry at the deadline.",
  "phase": "Reproduced the failure",
  "constraints": ["Preserve the public cache interface."],
  "acceptance": ["The focused expiry test and existing suite pass."],
  "evidence": ["Two runs still returned the cached value at time == expiry."],
  "last_advice_outcome": ""
}
```

From the task workspace, use the script from the installed skill. For example:

```powershell
$advisorScript = Join-Path $env:USERPROFILE '.agents\skills\advisor\scripts\ask_expert.py'
python $advisorScript --state-file tmp/advisor-state.json --session-file tmp/advisor-session.json --trigger two_failed_checks --question "Which boundary condition should change?"
```

A state file selects v2 automatically. Check whether the intended test ran and whether its dependencies were available. A successful command with zero tests provides no evidence about the patch.

After an interruption, `python $advisorScript --status --session-file tmp/advisor-session.json` reads the local round budget and receipt, including unknown usage. An unresolved dispatch blocks a duplicate. A completed journal entry can recover a round after a crash.

Reuse the session file for the task. Its first invocation sets the persistent round limit. Advice that passes validation is available in `advice_fields`; use `status` to distinguish valid, stale, and unusable replies. The adjacent `.attempts.jsonl` records possible dispatches and provider token receipts. An explicit `--receipt-file` can choose a different journal.

Append `--preview` to inspect the task packet before sending it. The Claude Code route adds a short reply-format reminder. The preview reads the current round and leaves the session and journal untouched. On a tight follow-up, the packer keeps the question, constraints and acceptance checks, and excerpts the head and tail of long evidence. Supply a short `decision_focus` in the task state if the full goal leaves insufficient space. A `packet_too_large` result identifies an input to shorten and has an empty attempts list.

For exact local evidence, select `--snippet PATH:FIRST-LAST`, `--diff`, or `--error-tail PATH` from the repository root. Read the included evidence before sending it. Use `--protocol v1` for the original four-line format and image attachments.

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
