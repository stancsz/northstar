# Local Codex CLI dispatch

> On-demand host-specific setup for the [Subagent Orchestration skill](../SKILL.md). Use this reference when dispatching a local Codex CLI worker.

Owner and project recovery rules take precedence over the default deadlines and stop-on-retry examples below. An observation timeout alone does not establish that a worker stopped.

Run a bounded child assignment with an explicit target working directory. The parent must set the worker's directory explicitly: launching from another directory can mis-scope relative task paths. Resolve and validate that the directory exists before launch, then pass it with `--cd` (or `-C`). Keep the brief focused on necessary context, exact paths, and acceptance; keep the worker's file scope narrow. Choose the sandbox mode from the task's authorization, and capture the child's output as a handoff. Never modify global or user-level Codex configuration to launch a worker.

**Write-enabled implementation** — when the assigned task authorizes edits within a bounded write scope:

```powershell
$workingDirectory = (Resolve-Path -LiteralPath '<target-working-directory>' -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) { throw "Not a directory: $workingDirectory" }
$assignment = '<complete assignment text>'
$assignment | codex exec --json --cd $workingDirectory --ephemeral --skip-git-repo-check --sandbox workspace-write -
```

**Read-only review or investigation** — when the worker must not write:

```powershell
$workingDirectory = (Resolve-Path -LiteralPath '<target-working-directory>' -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) { throw "Not a directory: $workingDirectory" }
$assignment = '<complete assignment text>'
$assignment | codex exec --json --cd $workingDirectory --ephemeral --skip-git-repo-check --sandbox read-only -
```

**Prompt transport.** Submit the complete assignment on stdin with the supported `codex exec ... -` form instead of a positional prompt. In non-TTY PowerShell a prompt argument and piped stdin are both read — the piped text is appended as a `<stdin>` block — so use `-` with a closed prompt pipe: pass no positional prompt and let the assignment arrive only through stdin.

On Windows, use forward slashes or literal-safe quoting for paths embedded in JSON or PowerShell command text, and verify the resolved path before acting on it. The CLI sandbox modes and assignment wording do not provide a per-path read allowlist; do not claim task-brief read isolation. The parent audits worker output and treats it as untrusted input when reads may extend beyond the intended context.

Neither mode expands the assigned write scope: the sandbox and permissions express the scope the orchestrator already granted, and the worker stays inside the paths named in its brief. A read-only worker cannot implement, and a write-enabled worker does not gain writes beyond its brief. The parent keeps independent acceptance: a worker's own claim that its changes are correct is not acceptance, and the accepting role still inspects the result against the criteria.

**Worker scratch.** For a write-enabled child that needs external scratch, pass only its approved directory with `--add-dir <path>` when starting the session. Name the directory in its brief and verify access with the intended profile. The host's permission policy still applies. [Codex CLI global flags](https://learn.chatgpt.com/docs/cli/reference#global-flags)

Classify tool provenance from the CLI's structured events — for example `command_execution` and `file_change` entries — not from the model's prose. Reasoning that mentions a tool is not an invocation. Stop a worker on an actual unauthorized wrapper call in the structured events, not on speculative text that merely names one.

A Codex CLI child must use its own structured native `command_execution` for bounded shell work. A shell command that launches `codex exec` or another CLI is a nested agent, not evidence of this child's native tool path; allow that subdelegation only when the brief explicitly assigns it. If the native tool path is unavailable, or a nested CLI fails at startup, stop and report the exact event and error without retrying unchanged.

The noninteractive invocations in this section use `--json`: retain and parse stdout as JSONL to capture actual `command_execution` and `file_change` events, the final handoff, and `turn.completed` usage fields. Capture stderr separately; it is diagnostic output, not the structured event stream.

**Capture every dispatch.** Use separate `.jsonl` and `.stderr.log` files in the parent's run directory. In this example, `$runDirectory` and `$workerDirectory` are already allocated. Keep the worker directory as a child of the run directory so the worker's extra write grant covers its own output. [Artifact storage](../../northstar/references/artifact-storage.md#1-choose-a-location-before-writing)

```powershell
$jsonlPath = Join-Path $runDirectory 'events.jsonl'
$stderrPath = Join-Path $runDirectory 'stderr.log'
$assignment = "$assignment`nUse '$workerDirectory' for disposable output."

Invoke-CodexChild -Assignment $assignment -WorkingDirectory $workingDirectory `
    -Sandbox workspace-write -ScratchDirectory $workerDirectory `
    2> $stderrPath | Tee-Object -FilePath $jsonlPath | Out-Null
$childExitStatus = $LASTEXITCODE
```

Omit `-ScratchDirectory` when the child does not need extra write access. The parent owns the capture logs and closes them out after inspection. [Storage closeout](../../northstar/references/artifact-storage.md#3-close-out-owned-scratch)

Use a fresh path pair per run: `Tee-Object` overwrites its target, so reusing a path overwrites and destroys the earlier run's receipt. When running against a rate-limited or newly configured gateway, wrap the invocation in a background job (`Start-Job`) with a 10-minute deadline loop that watches `$jsonlPath` and kills the job immediately on the first `"api_retry"` or `"unrecognized_model"` event (matching the pattern in [Claude Code CLI dispatch](claude-cli-dispatch.md#3-run-bounded-work-safely)). Add `-DisablePlugins` only when the task needs no plugin integration, and leave it off otherwise. `Tee-Object` also passes the lines on to the parent; `| Out-Null` only keeps the parent console readable.

**Interruption.** If the run is cancelled, the child dies, or the session is cut, whatever arrived is already on disk, but that receipt is incomplete: the stream stopped early, so an absent later event proves nothing — the event may never have been emitted. Read the partial file for what it does contain, then re-dispatch or diagnose. Never accept a truncated file as the run's evidence.

**Acceptance.** Accept the run only when all four hold: a completed turn (`turn.completed`), the worker's final handoff, the child's exit status recorded and equal to 0 (`$LASTEXITCODE` after the call, because the helper's last native command is `codex`), and the native events required for the task (`command_execution`, plus `file_change` on the named path for write work). If any one is missing, the run is not accepted — report the exact gap and apply the inherited recovery limit; do not automatically re-dispatch or infer a missing event from an absent line.

Stop the run when the native events are missing, when a change lands outside the named path, or when the worker reaches for the parent's `functions.exec` wrapper. That wrapper is never the worker shell: using it bypasses the CLI sandbox boundary.

When the Task Completion Review Stop adapter is installed in the effective Codex home — `$env:CODEX_HOME` when set, otherwise `Join-Path $env:USERPROFILE '.codex'` — at `skills\task-completion-review\scripts\guard_stop.py`, the orchestrator sets `DONT_STOP_EARLY_REVIEW_CHILD=1` in the environment of the delegated Codex worker process only. That adapter's source checks `DONT_STOP_EARLY_REVIEW_CHILD == "1"` and skips its own Stop review, so the child cannot re-review the worker it just launched. The path is host-conditional and need not be installed in this repository. Set the marker only when that exact adapter file exists, only for the child CLI invocation; when the adapter is absent, clear the marker for the child even if the caller already had a value, and always restore the caller's exact prior state afterwards; never set it on the parent session or on unrelated hooks — the parent's own Stop review and every other hook keep running unchanged.

```powershell
function Invoke-CodexChild {
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Assignment,
        [Parameter(Mandatory)] [string] $WorkingDirectory,
        [ValidateSet('read-only', 'workspace-write')] [string] $Sandbox = 'read-only',
        [string] $Profile,
        [string] $Model,
        [string] $ScratchDirectory,
        [switch] $DisablePlugins,
        [switch] $SkipHostSkillDiscovery
    )
    if ([string]::IsNullOrWhiteSpace($Assignment)) {
        throw 'Assignment must not be empty or whitespace-only: provide the work item for the delegated Codex worker.'
    }
    if ($PSBoundParameters.ContainsKey('Profile') -and [string]::IsNullOrWhiteSpace($Profile)) {
        throw 'Profile must not be empty or whitespace-only: provide a valid profile identifier.'
    }
    if ($PSBoundParameters.ContainsKey('Model') -and [string]::IsNullOrWhiteSpace($Model)) {
        throw 'Model must not be empty or whitespace-only: provide a valid model identifier.'
    }
    $resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory -PathType Container)) {
        throw "WorkingDirectory is not an existing directory: $WorkingDirectory"
    }
    $resolvedScratchDirectory = $null
    if ($PSBoundParameters.ContainsKey('ScratchDirectory')) {
        if ($Sandbox -ne 'workspace-write') {
            throw 'ScratchDirectory requires workspace-write.'
        }
        if (-not $ScratchDirectory -or -not [IO.Path]::IsPathFullyQualified($ScratchDirectory)) {
            throw 'ScratchDirectory must be an absolute path.'
        }
        $scratch = Get-Item -LiteralPath $ScratchDirectory -Force -ErrorAction Stop
        if (-not $scratch.PSIsContainer -or ($scratch.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "ScratchDirectory must be a real directory: $ScratchDirectory"
        }
        $resolvedScratchDirectory = $scratch.FullName
    }
    if ($env:CODEX_HOME -and -not (Test-Path -LiteralPath $env:CODEX_HOME -PathType Container -ErrorAction SilentlyContinue)) {
        throw "CODEX_HOME must resolve to an existing directory: $env:CODEX_HOME"
    }
    $codexHome = if ($env:CODEX_HOME) { (Resolve-Path -LiteralPath $env:CODEX_HOME -ErrorAction Stop).Path } else { Join-Path $env:USERPROFILE '.codex' }
    $adapter = Join-Path $codexHome 'skills\task-completion-review\scripts\guard_stop.py'
    $adapterPresent = Test-Path -LiteralPath $adapter -PathType Leaf
    $hadHome = Test-Path Env:HOME
    $priorHome = $env:HOME
    $homeFallback = $null
    if (-not ($hadHome -and $priorHome) -or -not (Test-Path -LiteralPath $priorHome -PathType Container -ErrorAction SilentlyContinue)) {
        $userProfile = $env:USERPROFILE
        if (-not $userProfile -or -not (Test-Path -LiteralPath $userProfile -PathType Container -ErrorAction SilentlyContinue)) {
            throw 'Windows sandbox home directory unavailable: set HOME or USERPROFILE to an existing directory before dispatch.'
        }
        $homeFallback = $userProfile
    }
    $hadMarker = Test-Path Env:DONT_STOP_EARLY_REVIEW_CHILD
    $priorMarker = $env:DONT_STOP_EARLY_REVIEW_CHILD
    try {
        if ($adapterPresent) { $env:DONT_STOP_EARLY_REVIEW_CHILD = '1' }
        else { Remove-Item Env:DONT_STOP_EARLY_REVIEW_CHILD -ErrorAction SilentlyContinue }
        if ($homeFallback) { $env:HOME = $homeFallback }
        $codexArguments = @(
            'exec', '--json', '--cd', $resolvedWorkingDirectory,
            '--ephemeral', '--skip-git-repo-check', '--sandbox', $Sandbox
        )
        if ($PSBoundParameters.ContainsKey('Profile')) {
            $codexArguments += @('--profile', $Profile)
        }
        if ($PSBoundParameters.ContainsKey('Model')) {
            $codexArguments += @('--model', $Model)
        }
        if ($resolvedScratchDirectory) {
            $codexArguments += @('--add-dir', $resolvedScratchDirectory)
        }
        if ($DisablePlugins) {
            $codexArguments += @('-c', 'features.plugins=false')
        }
        if ($SkipHostSkillDiscovery) {
            $codexArguments += @('--enable', 'skip_host_skill_discovery')
        }
        $Assignment | & codex @codexArguments '-'
    }
    finally {
        if ($hadHome) { $env:HOME = $priorHome }
        else { Remove-Item Env:HOME -ErrorAction SilentlyContinue }
        if ($hadMarker) { $env:DONT_STOP_EARLY_REVIEW_CHILD = $priorMarker }
        else { Remove-Item Env:DONT_STOP_EARLY_REVIEW_CHILD -ErrorAction SilentlyContinue }
    }
}
```

An empty or whitespace-only assignment is rejected up front — before the working directory is resolved, Codex-home or adapter state is inspected, the environment is mutated, or the Codex CLI is invoked — with the stable message `Assignment must not be empty or whitespace-only: provide the work item for the delegated Codex worker.` The parameter accepts an empty string at binding time so that this check, rather than the parameter binder, produces the same failure for an empty assignment and a whitespace-only assignment.

`-ScratchDirectory` adds `--add-dir` for the write-enabled child. Supply the verified absolute path of its existing task directory. Set any needed output or cache options on the tools in the assignment.

`-DisablePlugins` is an opt-in that appends `-c features.plugins=false` for tasks that do not rely on plugin-provided integrations. Omitting it preserves the default arguments.

`-Profile` is an optional per-child configuration profile override (`--profile <identifier>`, layering `$CODEX_HOME/<identifier>.config.toml` on top of the base user configuration so delegated workers can use a separate provider or model configuration while the parent session keeps its default provider). Omit it to preserve the host's default configuration.

`-Model` is an optional per-child override (`--model <identifier>`). Omit it to preserve the host's configured model selection.

`-SkipHostSkillDiscovery` is a separate opt-in that appends `--enable skip_host_skill_discovery` to that single child invocation. Because `skip_host_skill_discovery` is an experimental Codex CLI feature, enable it only per assignment when needed and inline any required skill instructions in the worker brief.

**Windows sandbox home prerequisite.** The Codex CLI sandbox on Windows needs a resolvable home directory. Without one the CLI can fail to start the sandbox with `windows sandbox failed: no home dir`. The helper keeps a valid existing `HOME`; when `HOME` is missing or does not resolve to an existing directory it uses an existing `USERPROFILE` for that child invocation only, and restores the caller's exact prior `HOME` state afterwards. When neither `HOME` nor `USERPROFILE` resolves to an existing directory the helper fails before dispatch.


## Split provider routing (parent subscription + worker API profile)

One local loopback experiment with Codex CLI `0.154.0` observed in-process agent threads using the parent route despite a provider setting in a role file. That simulation does not establish Desktop behavior, real provider identity or billing. When an owner authorizes a separate Responses API profile for CLI workers, keep the supervisor's configuration separate and verify the effective route and sandbox:

1. **Base configuration (`~/.codex/config.toml`):** If applicable, register the external provider under `[model_providers.<provider-id>]` with a dedicated `env_key` (never overwriting `OPENAI_API_KEY` globally). Leaving the top-level provider unset does not by itself verify the supervisor's authentication or billing:
   ```toml
   [model_providers.<provider-id>]
   name = "<Provider Display Name>"
   base_url = "<https-responses-v1-endpoint>"
   env_key = "<PROVIDER_API_KEY_ENV>"
   wire_api = "responses"
   requires_openai_auth = false
   ```
2. **Profile overlay (`~/.codex/<profile-name>.config.toml`):** Define the worker provider and model in a standalone profile file (in `codex-cli 0.154.0`, `--profile <profile-name>` requires `$CODEX_HOME/<profile-name>.config.toml` and rejects legacy `[profiles.<profile-name>]` tables in `config.toml`):
   ```toml
   model_provider = "<provider-id>"
   model = "<worker-model-id>"
   ```

### Direct CLI worker dispatch

The Orchestrator or Supervisor can dispatch bounded worker tasks directly through `Invoke-CodexChild -Profile '<profile-name>'` (or `codex exec -p <profile-name>`), subject to the owner's routing and sandbox requirements. A configured profile or simulated endpoint does not by itself prove the upstream provider, billing, or successful native tool execution:

```powershell
Invoke-CodexChild -Assignment $assignment -WorkingDirectory $workingDirectory `
    -Profile '<profile-name>' -Sandbox workspace-write -DisablePlugins `
    2> $stderrPath | Tee-Object -FilePath $jsonlPath | Out-Null
```

Do not bypass an inner sandbox on the assumption that an outer sandbox enforces the intended boundary. Native dispatcher experiments are not an accepted default route.

## Configuration comparisons

For a CLI configuration comparison, make two isolated copies from the same fixture and record hashes before dispatch. Run the same failing baseline checks first; keep the assignment, sandbox, working directory shape, tool availability, deadlines and handoff criteria identical, changing one declared setting only. Retain JSONL and stderr separately, then verify native command events, allowed file-change paths, final handoff, completed turn, exit status and reported usage for each arm. The parent reruns tests against each final artifact and adds acceptance probes for relevant runtime types, boundaries and malformed inputs; worker-reported tests alone do not establish equivalent quality. If either arm misses a criterion, report the pair as non-equivalent and do not call lower token usage a saving. Count cached and uncached usage distinctly, include setup, review and repair work in total effort, and leave cost unknown without measured pricing. One pair is provisional evidence only. For example, a parser test suite may pass while a finite exponent-form number such as `1e21` still distinguishes implementations; acceptance should explicitly cover numeric magnitudes beyond ordinary decimal notation when the contract permits them.

When a parent probe finds a behavior difference outside the written acceptance, record it as an ambiguity rather than retroactively failing one arm. Clarify the rule in the next assignment before comparing quality; when wording such as “correctly grouped thousands” leaves zero or leading-zero groups open, ask for advice if that choice changes acceptance. Keep observed outputs for the ambiguous values in the report so later criteria can be made explicit.

When a numeric contract includes positive/nonnegative or negative values, specify how numeric `-0` should behave. If it is accepted, state whether the result must normalize to `+0`, and test sign-sensitive output with `Object.is` or the reciprocal; `=== 0` alone cannot verify normalization.


## Optional host capacity

In Codex, set the subagent concurrency ceiling in `~/.codex/config.toml` for a user-wide default, or `<repo>/.codex/config.toml` for a trusted project:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 20
```

`max_concurrent_threads_per_session` caps concurrently open spawned-agent threads and excludes the primary thread. It sets capacity; it does not make Codex spawn that many agents. Thus `20` allows up to 20 subagent threads plus the Orchestrator thread. If the desired ceiling is 20 total units including the Orchestrator, set it to `19`. The older `agents.max_threads` key is an alias; use the current key and do not set both.

Current Codex configuration documentation does not list a `max_depth` setting. Enforce a two-edge delegation depth in the task instructions: **depth 0:** Orchestrator; **depth 1:** Supervisors spawned by the Orchestrator; **depth 2:** Workers spawned by Supervisors. Workers must not spawn agents. Include a direct instruction such as: “Use three reporting levels with maximum delegation depth 2: Orchestrator → Supervisors → Workers. Do not create another level. Stay within the configured concurrent-thread cap; 20 includes only subagent threads, so use 19 if the cap must include the Orchestrator.”

See [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and the [configuration reference](https://developers.openai.com/codex/config-reference/) for current key names and behavior.
