[CmdletBinding()]
param(
    # Registration is safe by default. Start only when the caller explicitly requests it.
    [switch]$Start
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$expectedArguments = '"{0}"' -f $servicePath

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
    $sameAction = $existing.Actions.Count -eq 1 -and
        [string]::Equals($existing.Actions[0].Execute, $pythonPath, [StringComparison]::OrdinalIgnoreCase) -and
        [string]::Equals($existing.Actions[0].Arguments, $expectedArguments, [StringComparison]::Ordinal) -and
        [string]::Equals($existing.Actions[0].WorkingDirectory, $repoRoot, [StringComparison]::OrdinalIgnoreCase)
    if (-not ($sameOwner -and $sameAction)) {
        throw "Refusing to replace task '$taskName': its owner or action differs from this installer. Inspect it manually."
    }
}

# The per-user interactive token preserves this account's existing Claude authentication.
# No credentials are read or copied. The task has no runtime deadline and ignores overlapping logon starts.
# It is hidden and runs pythonw.exe, so it does not open a console window. Windows keeps this task registration and its task identity across restart,
# but restart terminates the service process and in-memory workers. After login, reconcile task/broker state
# before retrying interrupted work so a recovered result is not dispatched twice.
# An exact owner/action match is safe to re-register: this updates only the intended trigger/settings.
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
