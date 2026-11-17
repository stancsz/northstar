# Install and Use Codex Advisor

**Codex Advisor** is a single, token-efficient skill ([`skills/advisor/SKILL.md`](../../skills/advisor/SKILL.md)) for **Codex CLI** and **Claude Code**.

---

## Install to Codex CLI

From the repository root in PowerShell:

```powershell
$dest = Join-Path $env:USERPROFILE '.codex\skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Or in Bash on macOS/Linux: `mkdir -p ~/.codex/skills/advisor && cp -R ./skills/advisor/* ~/.codex/skills/advisor/`.)*

If you also use `.agents/skills`, mirror the same directory there (`~/.agents/skills/advisor`).

## Install to Claude Code

From the repository root in PowerShell:

```powershell
$claudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$dest = Join-Path $claudeDir 'skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(Or in Bash on macOS/Linux: `mkdir -p "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor" && cp -R ./skills/advisor/* "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor/"`.)*

---

## Global Instructions (`AGENTS.md` / `CLAUDE.md`)

Add this short rule to `~/.codex/AGENTS.md` or `~/.claude/CLAUDE.md` so your coding agent knows when and how to ask the advisor without bloating packets:

```markdown
## Use $advisor for hard decisions (zero bloat)
- Do local file reading, edits, and test runs yourself.
- Consult `$advisor` only when blocked by a design fork, stubborn bug, or visual check (`--image`).
- Send a compact packet under 2,000 chars: 1-sentence decision, 3–5 verified facts (at most 1 snippet <= 400 chars), what was tried, and 1 sharp question.
- Execute the advisor's 4-line `Verdict / Next / Prompt / Risk` reply in your own turn; never let the advisor run multi-turn loops.
```

---

## Advisor Transport Setup

`skills/advisor/scripts/ask_expert.py` supports four `--transport` modes (`auto` by default):

1. **Gateway (`--transport gateway`):** Set `EXPERTS_BASE_URL` (e.g. `http://127.0.0.1:4040/v1`) and `EXPERTS_API_KEY` in your environment. Supports custom models (`--model` / `NORTHSTAR_ADVISOR_MODEL`) and `--image` attachments.
2. **Direct Codex (`--transport codex`):** Uses your existing `~/.codex/auth.json` (`codex login`) for simple text consultations with `gpt-6.2-astra`, `gpt-6.2-sol`, or `gpt-6-luna`.
3. **Direct Claude Code (`--transport claude`):** Invokes `claude -p --no-session-persistence --tools ""` for simple text consultations.
4. **Auto (`--transport auto`, default):** Uses `EXPERTS_BASE_URL` if configured and reachable, otherwise falls back to local Codex auth or `claude` CLI.

---

## Autonomous Highest-Privilege Codex Setup (`AGENTS.md` and `config.toml`)

When an owner explicitly authorizes unrestricted local execution and wants zero interactive permission prompts or sandbox stalls across Codex CLI and Codex Desktop:

### 1. Global `~/.codex/config.toml` (`$env:USERPROFILE\.codex\config.toml`)

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
approvals_reviewer = "user"
web_search = "live"

[windows]
sandbox = "elevated"

[sandbox_workspace_write]
network_access = true
exclude_tmpdir_env_var = false
exclude_slash_tmp = false

[shell_environment_policy]
inherit = "all"
ignore_default_excludes = true

[features]
memories = true
guardian_approval = false
exec_permission_approvals = false
request_permissions_tool = false
default_mode_request_user_input = false
write_stdin_approval = false

# Mark top-level workspace roots as trusted (include both drive-letter cases on Windows)
[projects.'C:\Users\<user>']
trust_level = "trusted"

[projects.'c:\users\<user>']
trust_level = "trusted"

[projects.'D:\github']
trust_level = "trusted"

[projects.'d:\github']
trust_level = "trusted"
```

### 2. Highest-Privilege Verification Checklist

- **Avoid `ReadOnly` (`read-only`) and `WorkspaceWrite` (`workspace-write`) sandboxes:** Both modes routinely stall on tool/package caches (`~/.cache`, npm/pip/uv/pytest caches), `.git` index/worktree locks, temporary directories, and non-interactive escalation rejections. Use `danger-full-access` (`--dangerously-bypass-approvals-and-sandbox`) and enforce read-only or write-scoped discipline through prompt instructions and `git status` / `git diff` checks.
- **No `sandbox_permissions` argument under `approval_policy = "never"`:** When `approval_policy` is `never`, Codex rejects any command that passes `sandbox_permissions` (such as `"require_escalated"`).
- **Desktop per-thread permission cache (`~/.codex/.codex-global-state.json`):** Ensure `agent-mode-by-host-id` is `"full-access"` and existing threads in `heartbeat-thread-permissions-by-id` use `approvalPolicy = "never"` and `sandboxPolicy.type = "dangerFullAccess"`.
- **Execpolicy rules (`~/.codex/rules/*.rules`):** Ensure no rule uses `decision="prompt"` or `decision="forbidden"`.

## Setup Tips & Gotchas

- **Never use Codex Desktop's native subagent (`spawn_agent`) as the advisor:** Native subagents start full agentic tool loops and burn tokens on unnecessary file reads and side exploration. Always call `ask_expert.py` for a **1-turn, tool-free** response while keeping all tools and heavy lifting on the caller CLI executor.
- **ChatGPT OAuth (`~/.codex/auth.json`) vs. `codex exec -m`:** `ask_expert.py --transport codex` calls `chatgpt.com/backend-api/codex/responses` directly with your `codex login` session (`gpt-6.2-astra`, `gpt-6.2-sol`, `gpt-6-luna`). If a local `codex` CLI build rejects a slug with `model_not_found` under ChatGPT auth, `ask_expert.py --transport codex` or a custom `EXPERTS_BASE_URL` gateway avoids that CLI restriction.
- **Clean stale models in `~/.codex/models_cache.json`:** Remove legacy `5.6` / `6.1` slugs if old models appear in pickers or stale profiles.
- **Use `--session-file` for multi-round delta context:** On Round 2+, `ask_expert.py` prepends only `Prior Verdict` (~200 chars) and tracks cumulative token usage instead of re-sending Round 1's full packet.
- **Avoid global Stop-hook loops (`~/.codex/hooks.json`):** Do not leave read-only Stop-hook reviewers (`guard_stop.py`) enabled globally; they reject out-of-repo config/attachment edits and burn extra frontier tokens on every turn.

---

[Back to Codex Advisor](../../README.md)
