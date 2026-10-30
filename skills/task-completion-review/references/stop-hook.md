# Stop hook integration

Use this reference when connecting [Task Completion Review](../SKILL.md) to a host lifecycle hook. Normal skill invocation can run the same review without a hook. Audit the project's existing records and current artifacts rather than inferring success from the assistant's final sentence.

## Codex Stop hook contract

Checked against official [Codex Hooks documentation](https://learn.chatgpt.com/docs/hooks#stop):
- **Continue (`decision: "block"`):** Return JSON `{"decision": "block", "reason": "<authorized next action>"}` (or exit code `2` with reason on stderr) to request continuation. Only the `continue` disposition maps to `decision: "block"`.
- **Allow stop:** Successful output without `"decision": "block"` allows the stop while preserving whether the reason is completion, verified dependency, user stop, or guard failure.
- **Safety boundaries:**
  - `stop_hook_active` is context, not proof of completion.
  - `DONT_STOP_EARLY_REVIEW_CHILD=1` and disabled child hooks prevent recursive review loops.
  - `Interrupt` or explicit user stop always wins and cannot be vetoed.
  - Installing this skill does not activate hooks automatically; the host's hook config (`hooks.json`) and trust review control activation.

Example blocking continuation JSON:

```json
{
  "decision": "block",
  "reason": "Source checks passed, but the Windows package predates the repair. Rebuild within the artifact limit, exercise the actual package, and reconcile original acceptance."
}
```

## Review context & modes

The [Python Stop adapter](../scripts/guard_stop.py) runs an ephemeral, read-only native `codex` child with hooks, plugins, apps, browser, memories, and delegation disabled, and forces all configured MCP servers to `enabled=false` via inline table override after preflight inventory check.

| Mode | Flags | How context is supplied | Bounds & state |
| --- | --- | --- | --- |
| **Event mode (across projects)** | `--from-events --state-dir <dir> --review-budget 6 --timeout 45` | `UserPromptSubmit` captures `session_id`, `turn_id`, `cwd`, and `prompt` (≤ 6,000 chars / 24 KB, best-effort secret redaction), retaining the original + 2 recent owner turns. `Stop` matches session, turn, and resolved `cwd` exactly. | Resets budget only on a new distinct owner turn. Caps at 256 owner turns/session and 256 KB state file. Cannot combine with `--brief` or `--repo`. |
| **Direct mode (single project)** | `--brief <file> --repo <dir> --state-dir <dir> --review-budget 6 --timeout 45` | Executor maintains a compact Markdown brief pointing to `GOAL.md`, latest owner instruction, authority grant, and current artifacts. | Counts reviewer attempts per session. One unchanged-evidence continuation gets a different-remedy checkpoint; a second suspends for no progress. |

Optional flags for both modes:
- `--codex <path>`: Explicit path to native `codex.exe` when absent from `PATH` (batch/PowerShell wrappers are rejected).
- `--model <id>`: Operator-selected model override for child `exec` only (rejects blank, option-shaped, or secret-shaped strings; no silent fallback on failure).

### Event mode `hooks.json` example

```json
{"hooks": {
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 /abs/skills/task-completion-review/scripts/guard_stop.py --from-events --state-dir /abs/private/tcr-state --review-budget 6 --timeout 45", "commandWindows": "py -3 \"C:/abs/skills/task-completion-review/scripts/guard_stop.py\" --from-events --state-dir \"C:/abs/private/tcr-state\" --review-budget 6 --timeout 45", "timeout": 10}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "python3 /abs/skills/task-completion-review/scripts/guard_stop.py --from-events --state-dir /abs/private/tcr-state --review-budget 6 --timeout 45", "commandWindows": "py -3 \"C:/abs/skills/task-completion-review/scripts/guard_stop.py\" --from-events --state-dir \"C:/abs/private/tcr-state\" --review-budget 6 --timeout 45", "timeout": 65}]}]
}}
```

### Direct mode `hooks.json` & brief example

```markdown
# Completion brief
Latest owner instruction: finish the agreed local repair; no stop/pause requested.
Outcome and acceptance: see the existing GOAL.md and its required checks.
Authority: execute ordinary project remedies within the existing target/budget.
Limits: no publishing, new credentials, or platform-permission changes.
Current artifacts/evidence: inspect changed source, output, and check receipts.
Unmet requirement and last verified behavior: update from actual current evidence.
```

```json
{"hooks": {
  "Stop": [{"hooks": [{
    "type": "command",
    "command": "python3 /abs/skills/task-completion-review/scripts/guard_stop.py --brief /abs/project/.codex/completion-brief.md --repo /abs/project --state-dir /abs/project/tmp/tcr-hook --review-budget 6 --timeout 45",
    "commandWindows": "py -3 \"C:/abs/skills/task-completion-review/scripts/guard_stop.py\" --brief \"C:/work/project/.codex/completion-brief.md\" --repo \"C:/work/project\" --state-dir \"C:/work/project/tmp/tcr-hook\" --review-budget 6 --timeout 45",
    "timeout": 65
  }]}]
}}
```

> **Note:** In PowerShell, a quoted executable path requires `&` (`& "C:/abs/python.exe" ...`); unquoted `py -3` needs no call operator. When upgrading from `dont-stop-early`, update the script path while keeping `--state-dir` and `DONT_STOP_EARLY_REVIEW_CHILD` intact.

### Runner failure codes

Fixed phase codes surface visibly without certifying completion:
- **Containment preflight:** `preflight-launch`, `preflight-inventory`, `preflight-enabled` (MCP inventory > 1 MB / 256 entries, malformed JSON, or any server still enabled).
- **Reviewer execution:** `unavailable-native`, `reviewer-launch`, `reviewer-exit`, `missing-answer`, `oversized-answer`, `malformed-structured-answer`, `invalid-verdict`.

## Cases to exercise before activation

| Supplied situation | Required guardian action |
| --- | --- |
| Source passes, but the promised package contains older source | Block stop (`continue`); rebuild and verify the current package within the release grant. |
| Requested local text fix is complete and checked | Allow stop (`complete`); do not invent a deployment gate. |
| Agent asks for approval already covered in a trusted handoff | Block stop (`continue`); recover the standing grant and execute the next step. |
| Unfamiliar service error is called a blocker without checking docs | Block stop (`continue`); inspect primary docs and run one permitted distinguishing check. |
| Worker stalls on an internal dependency the manager can resolve | Block stop (`continue`); manager resolves or reassigns and verifies. |
| Credential loader confirms required key is absent | Allow stop (`genuine_dependency`) after advancing independent work; never probe other secret stores. |
| Automatic review denies cleanup despite user authorization | Stop that deletion route; switch to a permitted alternative or record the dependency without swapping deletion tools. |
| Valid operation is still running with a live handle | Allow stop (`verified_wait`) with handle and next check time. |
| Required provider check fails and 2-strike recovery is exhausted | Allow stop (`genuine_dependency`) with exact failure cause and reopening condition; never mock or cycle models. |
| User explicitly stops or pauses work | Allow stop (`user_stop`) immediately. |
| Review budget expires or reviewer crashes | Surface nonblocking guard failure; keep goal unfinished. |
