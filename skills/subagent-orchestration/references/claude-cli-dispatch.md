# Local Claude Code CLI dispatch

> On-demand host-specific setup for the [Subagent Orchestration skill](../SKILL.md). Use this reference when dispatching a bounded task to the Claude Code CLI (`claude -p`).

Follow the shared [Northstar delivery contract](../../northstar/SKILL.md#delivery-contract) and the [Subagent Orchestration role hierarchy](../SKILL.md#roles-and-authority). The orchestrating commander remains the sole accepting owner; Claude Code runs as a bounded, single-assignment CLI worker.

## 1. Decide and scope the assignment

Group related acceptance criteria into one coherent, bounded assignment with an exclusive write scope:
- **Never allow concurrent writes** to the same file between the parent session and the Claude worker (or across parallel workers). Use [worktree isolation](worktree-isolation.md) when parallel tasks touch adjacent files or shared build outputs.
- **Self-contained brief:** Include the inherited authority grant, exact writable file paths, forbidden paths, baseline context, exact verification command, and wall-clock deadline (`5-minute` artifact checkpoint, `10-minute` handoff deadline).
- **Stop at acceptance:** Stop optional delegation as soon as required acceptance passes.

## 2. Verify CLI readiness and isolate environment

Run preflight once in the parent before dispatching:

1. **Check availability and auth safely:** Verify `claude --version` succeeds and rely on the host's configured authentication and model routing (or pass an explicit `--model <id>` when requested). **Never** read, print, or log credential files or API tokens, and **never** mutate global user settings (`~/.claude/settings.json`).
2. **Prevent profile model leakage:** When launching in an isolated configuration (`CLAUDE_CONFIG_DIR`, `--bare`, or `--setting-sources ""`), user-profile defaults are bypassed. Always pass the intended `--model <id>` explicitly when isolating settings so the child does not fall back to an unintended default route.
3. **One-turn read-only smoke:** When the CLI route or environment is new or reconfigured, run a single 1-turn read-only check before launching a write worker:
   ```powershell
   'Reply with READY only.' | claude -p --permission-mode plan --max-turns 1 --output-format json
   ```
   Confirm exit code `0` and the expected output before dispatching implementation work.

## 3. Run bounded work safely

- **Never use `--dangerously-skip-permissions`.**
  - For **read-only audits or reviews**, use `--permission-mode plan` (or `--allowedTools Read,Grep,Glob`).
  - For **scoped implementation**, explicitly enable only the required native tools: `--allowedTools "Read,Edit,Write,Bash"`.
- **Enforce hard execution bounds:** Always pass `--max-turns` and `--max-budget-usd` alongside a parent wall-clock timeout.
- **Capture structured streams separately:** Run with `--output-format stream-json --verbose` (or `--output-format json`), redirecting stdout to a task-scoped `.jsonl` file and stderr to a separate `.stderr.log` file under `tmp/<task-id>/`.
- **Terminate immediately on retry storms or bad routes:** Monitor or inspect the JSONL stream for native error events. **Kill the child process immediately on the first `api_retry` (HTTP 429) or `unrecognized_model` event**—never let a worker burn budget or wall-clock time in exponential backoff loops.
- **Wait for process exit before judging:** Do not grade partial artifacts while the child process is still running. Wait for exit code `0` and stream completion before inspecting diffs and test outputs.

```powershell
$taskId = 'issue-42-claude-worker'
$scratchDir = Join-Path (Resolve-Path '.').Path "tmp\$taskId"
New-Item -ItemType Directory -Force -Path $scratchDir | Out-Null
$jsonlPath = Join-Path $scratchDir 'events.jsonl'
$stderrPath = Join-Path $scratchDir 'stderr.log'
$workingDirectory = (Resolve-Path -LiteralPath '<target-working-directory>' -ErrorAction Stop).Path

Push-Location $workingDirectory
try {
    $assignment | claude -p `
        --allowedTools 'Read,Edit,Write,Bash' `
        --max-turns 15 `
        --max-budget-usd 2.00 `
        --output-format stream-json `
        --verbose `
        2> $stderrPath | Tee-Object -FilePath $jsonlPath | Out-Null
    $childExitStatus = $LASTEXITCODE
}
finally {
    Pop-Location
}
```

## 4. Accept and integrate

1. **Audit scope and native provenance:** Inspect `git status --short` and `git diff` after the process exits. Verify from the captured JSONL stream that the child used its native tools (`Read`, `Edit`, `Write`, `Bash`) rather than fabricating tool output in prose, and reject any out-of-scope file modifications.
2. **Independent verification:** Run the required verification command yourself in the parent (or route to a nonauthor [Independent QA](../../independent-qa/SKILL.md) reviewer when required). A Claude CLI worker cannot certify its own authored work.
3. **Record the receipt:** Log the changed paths, verification output, reported token/cost usage from the JSONL result event, remaining gaps, and next action in the project's existing record.

See local `claude --help`, the official [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference), and [environment variables](https://code.claude.com/docs/en/env-vars).
