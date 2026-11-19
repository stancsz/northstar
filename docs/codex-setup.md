# Optional Codex CLI & Desktop Setup Appendix

This optional appendix covers host-specific Codex CLI / Codex Desktop configuration tips kept separate from the main [Install & Setup Guide](install.md).

---

## 1. Autonomous Highest-Privilege Codex Setup (`config.toml`)

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

[projects.'<workspace-root>']
trust_level = "trusted"
```

### Highest-Privilege Verification Checklist

- **Avoid `ReadOnly` (`read-only`) and `WorkspaceWrite` (`workspace-write`) sandboxes:** Both modes routinely stall on tool/package caches (`~/.cache`, npm/pip/uv/pytest caches), `.git` index/worktree locks, temporary directories, and non-interactive escalation rejections. Use `danger-full-access` (`--dangerously-bypass-approvals-and-sandbox`) and enforce scope through prompt instructions and `git status` / `git diff` checks.
- **No `sandbox_permissions` argument under `approval_policy = "never"`:** When `approval_policy` is `never`, Codex rejects any command that passes `sandbox_permissions` (such as `"require_escalated"`).
- **Desktop per-thread permission cache (`~/.codex/.codex-global-state.json`):** Ensure `agent-mode-by-host-id` is `"full-access"` and existing threads in `heartbeat-thread-permissions-by-id` use `approvalPolicy = "never"` and `sandboxPolicy.type = "dangerFullAccess"`.
- **Execpolicy rules (`~/.codex/rules/*.rules`):** Ensure no rule uses `decision="prompt"` or `decision="forbidden"`.

---

## 2. Codex-Specific Tips & Gotchas

- **Never use Codex Desktop's native subagent (`spawn_agent`) as the advisor:** Native subagents start full agentic tool loops and burn tokens on unnecessary file reads and side exploration. Always call `ask_expert.py` for a **1-turn, tool-free** response while keeping all tools and heavy lifting on the caller CLI executor.
- **ChatGPT OAuth (`~/.codex/auth.json`) vs. `codex exec -m`:** `ask_expert.py --transport codex` calls `chatgpt.com/backend-api/codex/responses` directly with your `codex login` session (`gpt-6.2-astra`, `gpt-6.2-sol`, `gpt-6-luna`). If a local `codex` CLI build rejects a slug with `model_not_found` under ChatGPT auth, `ask_expert.py --transport codex` or a custom `EXPERTS_BASE_URL` gateway avoids that CLI restriction.
- **Clean stale models in `~/.codex/models_cache.json`:** Remove legacy `5.6` / `6.1` slugs if old models appear in pickers or stale profiles.
- **Use `--session-file` for multi-round delta context:** On Round 2+, `ask_expert.py` prepends only `Prior Verdict` (~200 chars) and tracks cumulative token usage instead of re-sending Round 1's full packet.
- **Avoid global Stop-hook loops (`~/.codex/hooks.json`):** Do not leave read-only Stop-hook reviewers (`guard_stop.py`) enabled globally; they reject out-of-repo config/attachment edits and burn extra frontier tokens on every turn.

[Back to Install & Setup](install.md) · [Back to Spot Advisor](../README.md)
