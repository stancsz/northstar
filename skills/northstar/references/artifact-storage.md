# Artifact storage and cleanup

Use this procedure when a task needs temporary files, generated output, or large downloads. Skip scratch setup when the task can work without it.

## 1. Choose a location before writing

Put disposable output in a fresh, real directory named `<root>/<project>/<unique-task-or-run-id>/`. Assign one cleanup owner. Give concurrent writers separate subdirectories and keep parent receipts outside the worker's write scope.

1. Use an approved absolute scratch root when the project or user has set one, for example `AGENT_SCRATCH_ROOT=D:/scratch` on a Windows host with a separate drive. Otherwise use `scratch/` under the host's permitted temp directory. The resulting path is typically `%TEMP%\scratch\<project>\<run-id>\` on Windows and `/tmp/scratch/<project>/<run-id>/` on POSIX. Resolve the temp directory with `[IO.Path]::GetTempPath()` or `${TMPDIR:-/tmp}` respectively. Use `tmp/<task>/` in the checkout only if it passes the same checks.
2. Check the actual volume and its available space before a large operation. Estimate peak use including temporary copies and apply any project artifact budget across all locations. The project's artifact total and the volume's free space answer different questions. If the work cannot fit, redirect future output to a permitted volume, reuse a suitable cache, or reduce the output before proceeding.
3. Before placing sizable output in a location, verify it in the actual host and permission profile. Check the absolute root and its parents, then create and measure a tiny new file in a fresh task directory. Remove that exact file with the intended permitted cleanup operation and verify it is absent. Check the empty directory can also be retired if the workflow depends on it. Recheck when the location, host, or cleanup route changes. A single file probe does not establish that a recursive removal or a different target will be allowed.

For example, after confirming the root is permitted, create the parent capture directory and the worker's child directory. Reuse these names in the Codex and Claude dispatch examples. Give every run a new ID.

```powershell
$scratchBase = if ($env:AGENT_SCRATCH_ROOT) { $env:AGENT_SCRATCH_ROOT } else { Join-Path ([IO.Path]::GetTempPath()) 'scratch' }
$projectRoot = Join-Path $scratchBase 'northstar'
New-Item -ItemType Directory -Path $projectRoot -Force -ErrorAction Stop | Out-Null
$taskId = 'issue-42-doc-write'
$runId = "$taskId-$([guid]::NewGuid().ToString('N'))"
$runDirectory = (New-Item -ItemType Directory -Path (Join-Path $projectRoot $runId) -ErrorAction Stop).FullName
$workerDirectory = (New-Item -ItemType Directory -Path (Join-Path $runDirectory 'worker') -ErrorAction Stop).FullName
```

Point tools at the absolute task directory with their output options. Use process scoped temp or cache overrides for tools that need them. Set up access before dispatch. For a CLI worker that needs to write outside its checkout, use the host's scoped directory option and name the exact path in the brief. See [Codex CLI](../../subagent-orchestration/references/cli-dispatch.md) or [Claude Code CLI](../../subagent-orchestration/references/claude-cli-dispatch.md).

A symlink or junction is useful only if a tool requires a fixed path. Record the link and its independently permitted target. Measure and clean the real path. The host evaluates access to that target.

### Give Codex a persistent scratch root

When Codex's built-in `:workspace` permission profile is active, it allows writes to the operating system temp directory. On Windows, `%TEMP%\scratch` then needs no symlink or extra Codex root grant. Permission profiles are beta; a managed setup may need its administrator to enable the profile. For a separate drive such as `D:\scratch`, add that path as a workspace root in a named permission profile that extends `:workspace`:

```toml
default_permissions = "scratch"

[permissions.scratch]
extends = ":workspace"

[permissions.scratch.workspace_roots]
"D:\\scratch" = true

[permissions.scratch.filesystem.":workspace_roots"]
"." = "write"
```

For Codex CLI, put this in `$CODEX_HOME/scratch.config.toml` and start that session with `codex --profile scratch`; `--profile` loads a config layer. Setting `default_permissions` selects the profile for that layer. Existing `sandbox_mode` settings or an explicit CLI `--sandbox` select the legacy sandbox instead. For one CLI child, grant its exact task directory with `--add-dir <task-directory>`. Each task still gets its own subdirectory. The host's approval and filesystem policy still applies. See [Codex permission profiles](https://learn.chatgpt.com/docs/permissions#extend-a-profile) and the [CLI global flags](https://learn.chatgpt.com/docs/cli/reference#global-flags).

## 2. Record ownership as artifacts are created

Record the task ID, cleanup owner, absolute path, purpose, and retention condition in the existing task record before writing sizable output. Add measured bytes or meaningful size changes as the work progresses. For routine scratch, one entry per owned directory covers its contents. Record significant output outside the assigned root separately. Keep the mapping available if a run stops before closeout.

| What it is | Where it goes and when it can be removed |
| --- | --- |
| Disposable scratch | Task directory. Remove after the last writer and consumer has finished. |
| Deliverables and necessary evidence | Approved project or evidence storage. Promote and verify what the task needs for delivery or resumption before cleaning scratch. |
| Shared caches, models, and app or Git managed state | Use the owner's designated storage and supported lifecycle. A task's use of a shared asset does not grant cleanup authority. |

For example, a handoff can say `run-42, parent owns D:/scratch/project/run-42/ (412 MB, logs). Keep until review passes, then remove. D:/evidence/project/run-42/summary.md verified and retained.`

For existing ignored or unmapped output, start with a read-only inventory of known project and tool locations. In Git, `git status --short --ignored=matching -- <scoped-path>` can show paths a normal status misses. Measure candidates and corroborate their owner and purpose with task records, tool reports, or app state. Git ignore controls visibility to Git. Establish permission and disposability from the host and the task's authority. Record unknowns and preserve live work, shared assets, and sole copies. Clean verified legacy candidates when the task has authority over them.

## 3. Close out owned scratch

The cleanup owner acts under the existing grant. Finish or stop owned writers and consumers as appropriate, verify retained files at their destination, and reconcile expected output with the actual task directory and known external paths.

Before removal, resolve and verify the exact absolute target is within the assigned scope. Check path components for links, junctions, and other reparse points. For any recursive operation, confirm the full tree is owned and disposable, with no linked or unverified subtrees. Use the literal target in the host's permitted cleanup operation, without wildcards or broad `git clean`. On Windows, keep verification and removal in PowerShell. Once the owned run directory passes those checks and its writers have stopped, remove that exact directory with `Remove-Item -LiteralPath $runDirectory -Recurse` and verify it is absent. For registered worktrees or app storage, use the owning tool's supported lifecycle and verify that its registration or reference is also gone.

Verify the targets are absent and report any retained bytes. Report reclaimed volume space only when measured. Logical file size can differ from space actually reclaimed.

- **Ordinary failure.** Resolve a known cause within scope, such as waiting for or stopping the task's own process holding a file open. Recheck the target before retrying.
- **Permission request or denial.** Use the host's supported approval flow when it offers one. If a sandbox or automatic review denies the action, record the exact target, reported reason, retained size, cleanup owner, and what permission or owner decision would resolve it. Do not retry the same action through another tool, alias, link, move, or permission change. Select a permitted root for future output and continue independent work.

A required cleanup stays open until verified. For incidental leftovers, leave one actionable handoff entry, for example `run-42, parent, D:/scratch/project/run-42/logs/ (380 MB). Automatic approval review denied removal. Retained. Owner to resolve the host restriction before another attempt.`
