[CmdletBinding()]
param(
    # Registration is safe by default. Start only when the caller explicitly requests it.
    [switch]$Start,
    # Optional authorized workspace the host service may work in. When omitted the
    # service keeps its default (the repository root), exactly as before.
    [string]$Workspace = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-HostTaskArguments {
    # Pure helper: builds the Scheduled Task action argument string.
    # The service path is quoted the same way it always was, and an optional
    # workspace is passed as ONE additional argument so paths with spaces survive.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServicePath,
        [string]$Workspace = ''
    )
    $base = '"{0}"' -f $ServicePath
    if ([string]::IsNullOrWhiteSpace($Workspace)) {
        return $base
    }
    return ('{0} {1}' -f $base, (Get-HostTaskWorkspaceArgument -Workspace $Workspace))
}

function Get-HostTaskWorkspaceArgument {
    # Pure helper: renders the --workspace argument for one workspace path.
    # A double quote cannot be quoted safely inside a Windows command line, so
    # such a path is rejected instead of being silently mangled.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Workspace
    )
    if ($Workspace.Contains('"')) {
        throw "Workspace path must not contain a double-quote character: $Workspace"
    }
    # Backslashes immediately before a closing quote must be doubled for Windows argv.
    $quotedWorkspace = [regex]::Replace($Workspace, '(\\+)$', '$1$1')
    return ('--workspace "{0}"' -f $quotedWorkspace)
}

function Split-HostTaskArguments {
    # Pure helper: splits an action argument string into its base service
    # argument and its optional workspace argument. Returns $null when the
    # string is not a recognizable base-service-argument form.
    [CmdletBinding()]
    param(
        [string]$Arguments = ''
    )
    if ($null -eq $Arguments) {
        return $null
    }
    $pattern = '^(?<base>"[^"]*")(?:\s+--workspace\s+(?:"(?<quoted>[^"]*)"|(?<plain>\S+)))?\s*$'
    $match = [regex]::Match($Arguments, $pattern)
    if (-not $match.Success) {
        return $null
    }
    $workspace = ''
    if ($match.Groups['quoted'].Success) {
        $workspace = $match.Groups['quoted'].Value
    }
    elseif ($match.Groups['plain'].Success) {
        $workspace = $match.Groups['plain'].Value
    }
    return [pscustomobject]@{
        BaseArguments = $match.Groups['base'].Value
        Workspace     = $workspace
    }
}

function Compare-HostTaskAction {
    # Pure helper: decides whether an existing task action may be replaced by
    # this installer. Returns 'match' (identical), 'workspace-update' (only the
    # workspace argument differs) or 'refuse'.
    [CmdletBinding()]
    param(
        [string]$ExpectedArguments = '',
        [string]$ExistingArguments = '',
        [string]$ExpectedExecute = '',
        [string]$ExistingExecute = '',
        [string]$ExpectedWorkingDirectory = '',
        [string]$ExistingWorkingDirectory = '',
        [bool]$SameOwner = $false
    )
    if (-not $SameOwner) {
        return 'refuse'
    }
    if (-not [string]::Equals($ExistingExecute, $ExpectedExecute, [StringComparison]::OrdinalIgnoreCase)) {
        return 'refuse'
    }
    if (-not [string]::Equals($ExistingWorkingDirectory, $ExpectedWorkingDirectory, [StringComparison]::OrdinalIgnoreCase)) {
        return 'refuse'
    }
    $expected = Split-HostTaskArguments -Arguments $ExpectedArguments
    $existing = Split-HostTaskArguments -Arguments $ExistingArguments
    if ($null -eq $expected -or $null -eq $existing) {
        return 'refuse'
    }
    if (-not [string]::Equals($existing.BaseArguments, $expected.BaseArguments, [StringComparison]::Ordinal)) {
        return 'refuse'
    }
    if ([string]::Equals($existing.Workspace, $expected.Workspace, [StringComparison]::OrdinalIgnoreCase)) {
        return 'match'
    }
    # Same trusted owner, same executable, same working directory and same base
    # service argument: only the authorized workspace differs, which is an
    # intentional workspace-only update.
    return 'workspace-update'
}

$taskName = 'Northstar-A2A-Host'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$pythonPath = Join-Path $repoRoot 'tmp\a2a-stack\venv\Scripts\pythonw.exe'
$servicePath = Join-Path $repoRoot 'a2a-stack\agent\service.py'

foreach ($requiredPath in @($pythonPath, $servicePath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required host service path does not exist: $requiredPath"
    }
}

$pythonPath = (Resolve-Path -LiteralPath $pythonPath).Path
$servicePath = (Resolve-Path -LiteralPath $servicePath).Path

$workspacePath = ''
if (-not [string]::IsNullOrWhiteSpace($Workspace)) {
    if ($Workspace.Contains('"')) {
        throw "Workspace path must not contain a double-quote character: $Workspace"
    }
    if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) {
        throw "Workspace directory does not exist: $Workspace"
    }
    $workspacePath = (Resolve-Path -LiteralPath $Workspace).Path
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$expectedArguments = Get-HostTaskArguments -ServicePath $servicePath -Workspace $workspacePath

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $expectedArguments `
    -WorkingDirectory $repoRoot
$trigger = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $identity),
    (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval ([TimeSpan]::FromMinutes(1)))
)
$principal = New-ScheduledTaskPrincipal `
    -UserId $identity `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -Hidden `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $existing) {
    $existingSid = $null
    try {
        $existingUser = [string]$existing.Principal.UserId
        if ($existingUser -match '^S-\d-') {
            $existingSid = [System.Security.Principal.SecurityIdentifier]::new($existingUser).Value
        }
        else {
            $existingSid = ([System.Security.Principal.NTAccount]::new($existingUser)).Translate(
                [System.Security.Principal.SecurityIdentifier]
            ).Value
        }
    }
    catch {
        throw "Refusing to replace task '$taskName': its owner cannot be resolved to a SID. Inspect it manually."
    }
    $sameOwner = [string]::Equals($existingSid, $currentSid, [StringComparison]::OrdinalIgnoreCase)
    if ($existing.Actions.Count -ne 1) {
        throw "Refusing to replace task '$taskName': its owner or action differs from this installer. Inspect it manually."
    }
    $decision = Compare-HostTaskAction `
        -ExpectedArguments $expectedArguments `
        -ExistingArguments ([string]$existing.Actions[0].Arguments) `
        -ExpectedExecute $pythonPath `
        -ExistingExecute ([string]$existing.Actions[0].Execute) `
        -ExpectedWorkingDirectory $repoRoot `
        -ExistingWorkingDirectory ([string]$existing.Actions[0].WorkingDirectory) `
        -SameOwner $sameOwner
    if ($decision -eq 'refuse') {
        throw "Refusing to replace task '$taskName': its owner or action differs from this installer. Inspect it manually."
    }
}

# The per-user interactive token preserves this account's existing Claude authentication.
# No credentials are read or copied. The task has no runtime deadline and ignores overlapping logon starts.
# It is hidden and runs pythonw.exe, so it does not open a console window. Windows keeps this task registration and its task identity across restart,
# but restart terminates the service process and in-memory workers. After login, reconcile task/broker state
# before retrying interrupted work so a recovered result is not dispatched twice.
# An exact owner/action match is safe to re-register: this updates only the intended trigger/settings.
# A workspace-only difference for the same owner, executable, service path and working directory is an
# intentional authorized-workspace update, so the persisted workspace survives restarts and can be changed here.
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Per-user Northstar A2A host service. Reconcile worker state after restart before retrying.' `
    -Force | Out-Null

if ($Start) {
    Start-ScheduledTask -TaskName $taskName
}

Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, @{Name='UserId'; Expression={$_.Principal.UserId}}, Actions
