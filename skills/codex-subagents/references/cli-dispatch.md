# Local Codex CLI dispatch

> On-demand host-specific setup for the [Codex Subagents skill](../SKILL.md). Use this reference when dispatching a local Codex CLI worker.

Route each Codex subagent's primary model inference through the local LiteLLM API at `http://127.0.0.1:4000/v1` by default; this applies to the worker itself, not just its supporting tools. Address the gateway by its explicit loopback IP rather than the `localhost` name: on this Windows host Subroute binds `127.0.0.1:4000`, and `localhost` CLI requests failed to connect. Use model ID `default` as a gateway alias for the currently saved routing-desk target regardless of alias/force/off mode. This does not pin the worker to Luna or another fixed model; LiteLLM chooses the configured target. If no target is saved, the gateway applies its own configured initial-target fallback. The orchestrator owns route and client setup: when the route or client is new or reconfigured, it runs one bounded read-only smoke request and confirms the unique response before dispatch, because a catalog listing or open port is insufficient. Pass the smoke evidence — endpoint, model alias, the exact confirmed command and its unique response — to the worker in its brief; the worker does not repeat the smoke or troubleshoot the route. Preserve explicit per-task model/provider constraints, credential boundaries and client protocol requirements. Do not change saved global settings or send credentials to a different host. If the Codex runtime cannot use the local route, or it is unavailable, state the concrete limitation and surface any authorized fallback; do not silently change providers. This does not change the Advisor's own route or allow an advisor to perform implementation or acceptance.

For work that needs CLI tools, also complete a harmless tool round trip before dispatch when the project requires one: force a named function call with a unique marker, then send the returned call and a matching function result in a stateless continuation and verify the marker in the final response. Parse text from the actual Responses `output` message `content` blocks; do not assume a client convenience field such as `output_text` is populated. If a request returns an error such as `supplemental_advisor_failed` stating that the base request was not sent, classify it as a gateway pre-inference failure, stop before launching the worker, preserve the exact status/error, and do not retry unchanged or blame the CLI child. Continue only through an already-authorized direct fallback or independent work.

For local Codex CLI workers, use a dedicated profile so the child process has an explicit gateway endpoint and never inherits or changes the primary Codex provider. Create `%USERPROFILE%\.codex\subroute-subagents.config.toml` with this profile, and provide `GATEWAY_MASTER_KEY` through the process environment:

```toml
model = "default"
model_provider = "subroute"
model_catalog_json = 'C:\Users\<user>\.codex\subroute-subagents-models.json'

[model_providers.subroute]
name = "Subroute local LiteLLM"
base_url = "http://127.0.0.1:4000/v1"
env_key = "GATEWAY_MASTER_KEY"
wire_api = "responses"
requires_openai_auth = false
```

The current Codex CLI expects its own `{"models":[...]}` catalog schema, while LiteLLM returns OpenAI's `{"data":[...]}` schema. Generate a profile-local compatible catalog from the installed CLI's bundled catalog, append a copy of a compatible bundled model entry with `slug` and `display_name` changed to `default`; this catalog entry is local CLI metadata only, while LiteLLM resolves the request to the active target, and point `model_catalog_json` to that file. Regenerate it after CLI upgrades. Do not copy a model catalog or prompt metadata from another Codex version.

```powershell
$catalogPath = Join-Path $env:USERPROFILE '.codex\subroute-subagents-models.json'
$bundled = codex debug models --bundled | ConvertFrom-Json
$template = $bundled.models | Select-Object -First 1
$default = $template | ConvertTo-Json -Depth 30 | ConvertFrom-Json
$default.slug = 'default'
$default.display_name = 'default'
[ordered]@{ models = @($bundled.models) + @($default) } |
    ConvertTo-Json -Depth 30 |
    Set-Content -LiteralPath $catalogPath -Encoding utf8
```

Never combine `--ignore-user-config` with the `subroute-subagents` profile: it bypassed the profile and selected `gpt-6-astra` from provider `openai`. Optional process-only `CODEX_HOME` isolation works only if that home contains the dedicated profile and a compatible catalog. Keep `GATEWAY_MASTER_KEY` inherited through the process environment only; do not put it in the profile or catalog. Before sending any task data, confirm the startup banner shows the authorized effective sandbox as well as provider `subroute` and model `default`; if an authorized write task starts read-only, stop and correct the invocation instead of blaming the worker. An isolated home does not inherit user setup automatically: deliberately copy any required skills, tools, or hooks into it.

Run a bounded child assignment with an explicit target working directory. The parent must set the worker's directory explicitly: launching from another directory can mis-scope relative task paths. Resolve and validate that the directory exists before launch, then pass it with `--cd` (or `-C`). Keep the brief focused on necessary context, exact paths, and acceptance; keep the worker's file scope narrow. Choose the mode from the task's authorization, and capture the child's output as a handoff. Add the process-only base URL override so a profile still saved with `localhost` reaches the observed loopback route without changing the saved profile or any user config.

**Dispatch on this Windows host.** The route was actually proven through `Invoke-CodexChild` (helper defined below), so normal tool-using or write dispatch must invoke that helper with `-UseObservedSubrouteSettings`, adding `-DisablePlugins` when the task needs no plugin integrations. The standalone `codex exec` blocks below document the underlying flags; they are not the accepted operational recipe for this host unless separately smoke-verified.

**Write-enabled implementation** — when the assigned task authorizes edits within a bounded write scope:

```powershell
$workingDirectory = (Resolve-Path -LiteralPath '<target-working-directory>' -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) { throw "Not a directory: $workingDirectory" }
$assignment = '<complete assignment text>'
$assignment | codex exec --json --cd $workingDirectory --profile subroute-subagents --ephemeral --skip-git-repo-check --sandbox workspace-write -c 'model_providers.subroute.base_url="http://127.0.0.1:4000/v1"' -
```

**Read-only review or investigation** — when the worker must not write:

```powershell
$workingDirectory = (Resolve-Path -LiteralPath '<target-working-directory>' -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) { throw "Not a directory: $workingDirectory" }
$assignment = '<complete assignment text>'
$assignment | codex exec --json --cd $workingDirectory --profile subroute-subagents --ephemeral --skip-git-repo-check --sandbox read-only -c 'model_providers.subroute.base_url="http://127.0.0.1:4000/v1"' -
```

**Prompt transport.** Submit the complete assignment on stdin with the supported `codex exec ... -` form instead of a positional prompt. In non-TTY PowerShell a prompt argument and piped stdin are both read — the piped text is appended as a `<stdin>` block — so use `-` with a closed prompt pipe: pass no positional prompt and let the assignment arrive only through stdin.

On this Windows host, use forward slashes or literal-safe quoting for paths embedded in JSON or PowerShell command text, and verify the resolved path before acting on it. The CLI sandbox modes and assignment wording do not provide a per-path read allowlist; do not claim task-brief read isolation. The parent audits worker output and treats it as untrusted input when reads may extend beyond the intended context.

The `-c` override sets only the base URL for that invocation. The model alias `default`, provider `subroute`, the `GATEWAY_MASTER_KEY` auth variable, the sandbox mode and the Responses wire API stay as configured.

Neither mode expands the assigned write scope: the sandbox and permissions express the scope the orchestrator already granted, and the worker stays inside the paths named in its brief. A read-only worker cannot implement, and a write-enabled worker does not gain writes beyond its brief. The parent keeps independent acceptance: a worker's own claim that its changes are correct is not acceptance, and the accepting role still inspects the result against the criteria.

Brief the operation and exact scope instead of asking the worker to echo startup facts or predict native tool names; route, model and sandbox verification belong to the orchestrator.

Classify tool provenance from the CLI's structured events — for example `command_execution` and `file_change` entries — not from the model's prose. Reasoning that mentions a tool is not an invocation. Stop a worker on an actual unauthorized wrapper call in the structured events, not on speculative text that merely names one.

A Codex CLI child must use its own structured native `command_execution` for bounded shell work. A shell command that launches `codex exec` or another CLI is a nested agent, not evidence of this child's native tool path; allow that subdelegation only when the brief explicitly assigns it. If the native tool route is unavailable, or a nested CLI fails at startup, stop and report the exact event and error without retrying unchanged.

The noninteractive invocations in this section use `--json`: retain and parse stdout as JSONL to capture actual `command_execution` and `file_change` events, the final handoff, and `turn.completed` usage fields. Capture stderr separately; it is diagnostic output, not the structured event stream.

**Observed Codex CLI path on this Windows host** — one observed configuration produced native CLI events on Codex CLI 0.154.0 with profile `subroute-subagents`, model alias `default`, provider `subroute`, the Responses protocol and these process-only overrides: `features.shell_tool=true`, `features.apps=false`, `features.remote_plugin=false`, `features.multi_agent=false`, `mcp_servers.browseros-neo.enabled=false` (the MCP server configured on this host), plus the explicit loopback base URL `http://127.0.0.1:4000/v1`. This is the flag-level view of the same settings the helper applies; dispatch real delegated work through the helper.

```powershell
$assignment | codex exec --json --cd $workingDirectory --profile subroute-subagents --ephemeral --skip-git-repo-check --sandbox read-only -c 'model_providers.subroute.base_url="http://127.0.0.1:4000/v1"' -c 'features.shell_tool=true' -c 'features.apps=false' -c 'features.remote_plugin=false' -c 'features.multi_agent=false' -c 'mcp_servers.browseros-neo.enabled=false' -
```

For the write run, change only `--sandbox` to `workspace-write`. These overrides exist for that child process alone: never edit global or user Codex settings to reproduce them, keep `GATEWAY_MASTER_KEY` inherited through the child environment only, and leave the model alias `default`, the Responses protocol and credential handling as configured.

Run this path in order:

1. **Route preflight.** Send one direct request to `http://127.0.0.1:4000/v1` with model alias `default` and confirm the unique marker, then force a function call, return its tool result, and confirm the same marker comes back. An open port, a catalog listing, or a text-only reply is not this evidence.

   **Observed follow-up shape on this route.** In the observed Subroute Responses preflight, sending only `previous_response_id` with the tool result failed; the successful stateless follow-up replayed the complete emitted `function_call` item, its matching `function_call_output` with the same `call_id`, and the user echo. Treat this as an observed detail of this route, not a general API guarantee; confirming the same unique marker stays the acceptance check for whichever follow-up shape works.
2. **Bounded read-only smoke.** Run one CLI-native read-only assignment through `Invoke-CodexChild -UseObservedSubrouteSettings`, and accept it only when the JSONL carries a structured `command_execution` event and a concise handoff.
3. **Write work.** Only then issue one exact-path `workspace-write` assignment through the same helper, and accept it only when the JSONL carries structured native events (`command_execution`, plus `file_change` for the named file), the change is confined to the named path, and the worker returns a concise handoff.

Make the smoke command native to the shell exposed by `command_execution`; do not launch a nested shell executable unless the task specifically tests process launch. The executor wraps command text in its configured Windows shell. In one current trial, asking the worker to run `cmd.exe /d /c cd` was normalized to `cmd.exe /c '/d /c cd'` and failed with `'/d' is not recognized`; adding `.` to `cd` returned exit 0 but no output. Neither proves the expected cwd. For a cwd smoke, name the verified absolute path in the assignment and ask for the shell-native cwd builtin (`cd` under cmd, `Get-Location` under PowerShell). Accept only when the structured native `command_execution` event exits 0, the turn reaches `turn.completed`, the worker returns a concise handoff, and parsing stdout by lines finds at least one trimmed line equal to the expected absolute path. Do not require the entire stdout string to equal that path: PowerShell may format `Get-Location` as a `Path` table. Empty or malformed output fails the gate even when the CLI process itself exits 0. Do not repeat a nested-shell command unchanged.

**Capture every dispatch.** Dispatch through the helper and retain the structured stream while it runs: `Tee-Object` writes each JSONL line to a task-scoped file as the event arrives, and stderr goes to a separate task-scoped file because it is diagnostic output, not part of the event stream.

```powershell
$taskId = 'issue-42-doc-write'
$jsonlPath = Join-Path $env:TEMP "$taskId.jsonl"
$stderrPath = Join-Path $env:TEMP "$taskId.stderr.log"
$assignment = 'Update the scoped documentation and return a concise handoff.'
$workingDirectory = 'D:\work\my-project'

Invoke-CodexChild -Assignment $assignment -WorkingDirectory $workingDirectory `
    -Sandbox workspace-write -UseObservedSubrouteSettings -DisablePlugins `
    2> $stderrPath | Tee-Object -FilePath $jsonlPath | Out-Null
$childExitStatus = $LASTEXITCODE
```

Use a fresh path pair per run: `Tee-Object` overwrites its target, so reusing a path overwrites and destroys the earlier run's receipt. Add `-DisablePlugins` only when the task needs no plugin integration, and leave it off otherwise. Capturing changes nothing about the child's route, model, provider or credentials — the helper still runs profile `subroute-subagents`, model alias `default`, provider `subroute` at the loopback base URL, with `GATEWAY_MASTER_KEY` inherited through the child environment only. `Tee-Object` also passes the lines on to the parent; `| Out-Null` only keeps the parent console readable.

**Interruption.** If the run is cancelled, the child dies, or the session is cut, whatever arrived is already on disk, but that receipt is incomplete: the stream stopped early, so an absent later event proves nothing — the event may never have been emitted. Read the partial file for what it does contain, then re-dispatch or diagnose. Never accept a truncated file as the run's evidence.

**Acceptance.** Accept the run only when all four hold: a completed turn (`turn.completed`), the worker's final handoff, the child's exit status recorded and equal to 0 (`$LASTEXITCODE` after the call, because the helper's last native command is `codex`), and the native events the step above requires (`command_execution`, plus `file_change` on the named path for write work). If any one is missing, the run is not accepted — report the exact gap and apply the inherited recovery limit; do not automatically re-dispatch or infer a missing event from an absent line.

Stop the run when the native events are missing, when a change lands outside the named path, or when the worker reaches for the parent's `functions.exec` wrapper. That wrapper is never the worker shell: using it bypasses the CLI sandbox boundary.

**Evidence limit** — this is a single observed combined configuration, not a proven causal fix. The read-only smoke produced native `command_execution` and a handoff, a prior `workspace-write` task with the same overrides produced native `command_execution`, `file_change` and a handoff, and a comparable run without these overrides produced no native `command_execution` or `file_change`. The overrides changed together, so no single cause is identified and general reliability is unproven. Treat them as a working starting configuration to re-verify, not as a fix. The Windows sandbox home requirement noted below is a separate, identified cause of a `no home dir` failure and does not turn this override bundle into a proven single-cause fix.

When this exact Task Completion Review Stop adapter is installed in the effective Codex home — `$env:CODEX_HOME` when set, otherwise `Join-Path $env:USERPROFILE '.codex'` — at `skills\task-completion-review\scripts\guard_stop.py`, the orchestrator sets `DONT_STOP_EARLY_REVIEW_CHILD=1` in the environment of the delegated Codex worker process only. That adapter's source checks `DONT_STOP_EARLY_REVIEW_CHILD == "1"` and skips its own Stop review, so the child cannot re-review the worker it just launched. The path is host-conditional and need not be installed in this repository. Set the marker only when that exact adapter file exists, only for the child CLI invocation; when the adapter is absent, clear the marker for the child even if the caller already had a value, and always restore the caller's exact prior state afterwards; never set it on the parent session or on unrelated hooks — the parent's own Stop review and every other hook keep running unchanged.

```powershell
function Invoke-CodexChild {
    param(
        [Parameter(Mandatory)] [AllowEmptyString()] [string] $Assignment,
        [Parameter(Mandatory)] [string] $WorkingDirectory,
        [ValidateSet('read-only', 'workspace-write')] [string] $Sandbox = 'read-only',
        [switch] $UseObservedSubrouteSettings,
        [switch] $DisablePlugins,
        [switch] $SkipHostSkillDiscovery
    )
    if ([string]::IsNullOrWhiteSpace($Assignment)) {
        throw 'Assignment must not be empty or whitespace-only: provide the work item for the delegated Codex worker.'
    }
    $resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory -PathType Container)) {
        throw "WorkingDirectory is not an existing directory: $WorkingDirectory"
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
            'exec', '--json', '--cd', $resolvedWorkingDirectory, '--profile', 'subroute-subagents',
            '--ephemeral', '--skip-git-repo-check', '--sandbox', $Sandbox,
            '-c', 'model_providers.subroute.base_url="http://127.0.0.1:4000/v1"'
        )
        if ($UseObservedSubrouteSettings) {
            $codexArguments += @(
                '-c', 'features.shell_tool=true',
                '-c', 'features.apps=false',
                '-c', 'features.remote_plugin=false',
                '-c', 'features.multi_agent=false',
                '-c', 'mcp_servers.browseros-neo.enabled=false'
            )
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

Example call with an explicit assignment and working directory:

```powershell
$assignment = 'Update the scoped documentation and return a concise handoff.'
$workingDirectory = 'D:\work\my-project'
Invoke-CodexChild -Assignment $assignment -WorkingDirectory $workingDirectory -Sandbox workspace-write -UseObservedSubrouteSettings -DisablePlugins
```

Omitting `-UseObservedSubrouteSettings` preserves the helper's default child arguments.
`-DisablePlugins` is a separate opt-in that appends exactly one `-c features.plugins=false`; it is independent of `-UseObservedSubrouteSettings` and is intended only for tasks that do not rely on plugin-provided integrations. Omitting it preserves the existing arguments exactly.

`-SkipHostSkillDiscovery` is a third, separate opt-in. When present it appends exactly `--enable skip_host_skill_discovery` to that one child invocation and nothing else; when absent, the default invocation arguments are unchanged. The Codex CLI lists `skip_host_skill_discovery` as an under-development feature, so this switch is experimental: enable it per assignment when the task needs it, expect it to change or disappear in a later CLI release, and never make it default-on. It is process-only and never edits global or user Codex configuration. Enabling it requests that the host-discovered skill descriptions and their context are removed from the child, but the feature is under development and that behavior is not guaranteed. No total-context or token reduction is proven: the recorded write worker still emitted the skill-context-budget warning. Inline the skill instructions the worker needs in the assignment, do not dispatch work that depends on host skill discovery, and do not rely on this flag as a context-budget or token-saving fix. The switch is independent of `-UseObservedSubrouteSettings` and `-DisablePlugins`, and combining them keeps every contributed argument exactly once.

The wrapper sets only the child marker and, when the host requires it, a process-only child `HOME`. The model alias `default`, provider `subroute`, the `GATEWAY_MASTER_KEY` auth variable, the base-URL override, the sandbox mode and the Responses wire API stay as configured; when the adapter is absent, the child simply runs without the marker.

**Windows sandbox home prerequisite.** The Codex CLI sandbox on Windows needs a resolvable home directory. Without one the CLI can still register the native command tool and then fail to start the sandbox with `windows sandbox failed: no home dir`, which produces no native `command_execution` event. The helper keeps a valid existing `HOME`; when `HOME` is missing or does not resolve to an existing directory it uses an existing `USERPROFILE` for that child invocation only, and it restores the caller's exact prior `HOME` state afterwards, including an absent or empty `HOME`. When neither `HOME` nor `USERPROFILE` resolves to an existing directory the helper fails before dispatch. This fallback is process-only: never set a user-level or machine-level `HOME` to work around it, and keep every other route, credential and sandbox boundary unchanged.

The installed Codex CLI's native `spawn_agent` path may reject the custom `default` model before dispatch; a successful parent request does not prove that native child path works. If that occurs, use the explicit profile-backed CLI worker only when it satisfies the task's acceptance criteria, and report that the native spawn path remains unavailable. Never substitute a platform-hosted model or claim it used port 4000.


## Configuration comparisons

For a CLI configuration comparison, make two isolated copies from the same fixture and record hashes before dispatch. Run the same failing baseline checks first; keep the assignment, route/profile, sandbox, working directory shape, tool availability, deadlines and handoff criteria identical, changing one declared setting only. Retain JSONL and stderr separately, then verify native command events, allowed file-change paths, final handoff, completed turn, exit status and reported usage for each arm. The parent reruns tests against each final artifact and adds acceptance probes for relevant runtime types, boundaries and malformed inputs; worker-reported tests alone do not establish equivalent quality. If either arm misses a criterion, report the pair as non-equivalent and do not call lower token usage a saving. Count cached and uncached usage distinctly, include the preflight, smoke, review and repair work in total effort, and leave cost unknown without measured pricing. One pair is provisional evidence only. For example, a parser test suite may pass while a finite exponent-form number such as `1e21` still distinguishes implementations; acceptance should explicitly cover numeric magnitudes beyond ordinary decimal notation when the contract permits them.

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
