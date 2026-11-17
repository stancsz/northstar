# Install and Use Codex Advisor

**Codex Advisor** is a single, token-efficient skill ([`skills/advisor/SKILL.md`](../skills/advisor/SKILL.md)) for **Codex CLI** and **Claude Code**.

---

## 1. Install the Skill

### Codex CLI

From the repository root in PowerShell:

```powershell
$dest = Join-Path $env:USERPROFILE '.codex\skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(In Bash on macOS/Linux: `mkdir -p ~/.codex/skills/advisor && cp -R ./skills/advisor/* ~/.codex/skills/advisor/`.)*

If you also use `.agents/skills`, mirror the same directory there (`~/.agents/skills/advisor`).

### Claude Code

From the repository root in PowerShell:

```powershell
$claudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$dest = Join-Path $claudeDir 'skills\advisor'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Path '.\skills\advisor\*' -Destination $dest -Recurse -Force
```

*(In Bash on macOS/Linux: `mkdir -p "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor" && cp -R ./skills/advisor/* "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/advisor/"`.)*

---

## 2. Global Agent Instructions (`AGENTS.md` / `CLAUDE.md`)

Add this rule to `~/.codex/AGENTS.md` or `~/.claude/CLAUDE.md` so your coding agent knows when and how to call `advisor` without bloating packets:

```markdown
## Use $advisor for hard decisions (zero bloat)
- Do all local file reading, edits, and test runs yourself.
- Never spawn a Codex Desktop native subagent (`spawn_agent`) as the advisor; call `ask_expert.py` directly for a 1-turn, tool-free response.
- Consult `$advisor` only when blocked by a design fork, stubborn bug, or visual check (`--image`).
- Send a compact packet under 2,000 chars: 1-sentence decision, 3–5 verified facts (at most 1 snippet <= 400 chars), what was tried, and 1 sharp question.
- For multi-round debugging, pass `--session-file` and send only a tiny delta packet on Round 2+.
- Execute the advisor's 4-line `Verdict / Next / Prompt / Risk` reply in your own turn.
```

---

## 3. Transport Setup (`--transport`)

[`skills/advisor/scripts/ask_expert.py`](../skills/advisor/scripts/ask_expert.py) defaults to `--transport auto`, which routes as follows:

1. **Direct Codex (`--transport auto` #1 default / `--transport codex`):** Uses your existing `~/.codex/auth.json` (`codex login`) directly against ChatGPT OAuth for `gpt-6.2-astra` (default), `gpt-6.2-sol`, or `gpt-6-luna`. No gateway or extra API key is required.
2. **Custom Gateway (`--transport gateway`):** Set `EXPERTS_BASE_URL` (e.g., `http://127.0.0.1:4040/v1`) and `EXPERTS_API_KEY`. Used automatically by `auto` when `--image` screenshots are attached or when using custom/non-Codex models.
3. **Claude Code CLI (`--transport claude`):** Invokes `claude -p --no-session-persistence --tools ""` for text consultations when Codex auth and gateway are unavailable.

---

## 4. Autonomous Highest-Privilege Codex Setup (`config.toml`)

When an owner explicitly authorizes unrestricted local execution and wants zero interactive permission prompts or sandbox stalls across Codex CLI and Codex Desktop:

```toml
# ~/.codex/config.toml
model = "gpt-6-luna"
model_reasoning_effort = "max"
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

### Highest-Privilege Verification Checklist

- **Avoid `ReadOnly` (`read-only`) and `WorkspaceWrite` (`workspace-write`) sandboxes:** Both modes routinely stall on tool/package caches (`~/.cache`, npm/pip/uv/pytest caches), `.git` index/worktree locks, temporary directories, and non-interactive escalation rejections. Use `danger-full-access` (`--dangerously-bypass-approvals-and-sandbox`) and enforce scope through prompt instructions and `git status` / `git diff` checks.
- **No `sandbox_permissions` argument under `approval_policy = "never"`:** When `approval_policy` is `never`, Codex rejects any command that passes `sandbox_permissions` (such as `"require_escalated"`).
- **Desktop per-thread permission cache (`~/.codex/.codex-global-state.json`):** Ensure `agent-mode-by-host-id` is `"full-access"` and existing threads in `heartbeat-thread-permissions-by-id` use `approvalPolicy = "never"` and `sandboxPolicy.type = "dangerFullAccess"`.
- **Execpolicy rules (`~/.codex/rules/*.rules`):** Ensure no rule uses `decision="prompt"` or `decision="forbidden"`.

---

## 5. Setup Tips & Gotchas

- **Never use Codex Desktop's native subagent (`spawn_agent`) as the advisor:** Native subagents start full agentic tool loops and burn tokens on unnecessary file reads and side exploration. Always call `ask_expert.py` for a **1-turn, tool-free** response while keeping all tools and heavy lifting on the caller CLI executor.
- **ChatGPT OAuth (`~/.codex/auth.json`) vs. `codex exec -m`:** `ask_expert.py --transport codex` calls `chatgpt.com/backend-api/codex/responses` directly with your `codex login` session (`gpt-6.2-astra`, `gpt-6.2-sol`, `gpt-6-luna`). If a local `codex` CLI build rejects a slug with `model_not_found` under ChatGPT auth, `ask_expert.py --transport codex` or a custom `EXPERTS_BASE_URL` gateway avoids that CLI restriction.
- **Clean stale models in `~/.codex/models_cache.json`:** Remove legacy `5.6` / `6.1` slugs if old models appear in pickers or stale profiles.
- **Use `--session-file` for multi-round delta context:** On Round 2+, `ask_expert.py` prepends only `Prior Verdict` (~200 chars) and tracks cumulative token usage instead of re-sending Round 1's full packet.
- **Avoid global Stop-hook loops (`~/.codex/hooks.json`):** Do not leave read-only Stop-hook reviewers (`guard_stop.py`) enabled globally; they reject out-of-repo config/attachment edits and burn extra frontier tokens on every turn.

[Back to Codex Advisor](../README.md)
