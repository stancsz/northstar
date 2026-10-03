[CmdletBinding()]
param(
    [switch] $Install,
    [switch] $Uninstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$taskName = 'Codex Desktop Health Check'
$logDirectory = Join-Path $env:LOCALAPPDATA 'CodexHealthCheck'
$logPath = Join-Path $logDirectory 'health-check.log'

function Write-HealthLog {
    param([Parameter(Mandatory)][string] $Message)

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
    Add-Content -LiteralPath $logPath -Value "$timestamp $Message" -Encoding UTF8
}

function Install-HealthCheck {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        throw 'Save this script to disk before installing the scheduled task.'
    }

    $powerShellPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $scriptPath
    $action = New-ScheduledTaskAction -Execute $powerShellPath -Argument $arguments

    # A one-time trigger with a long repetition window gives Task Scheduler's
    # supported interval parameters while keeping the action in the signed-in
    # desktop session without requiring a stored password.
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes 10) `
        -RepetitionDuration (New-TimeSpan -Days 9999)

    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
    Write-HealthLog "Installed scheduled task '$taskName' for $scriptPath (every 10 minutes while this user is signed in)."
    Write-Output "Installed '$taskName'. It checks every 10 minutes while you are signed in."
}

function Uninstall-HealthCheck {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Output "Removed '$taskName'."
    }
    else {
        Write-Output "Scheduled task '$taskName' was not found."
    }
}

function Invoke-HealthCheck {
    $package = Get-AppxPackage -Name 'OpenAI.Codex' | Select-Object -First 1
    if (-not $package) {
        Write-HealthLog 'ERROR: The OpenAI.Codex package is not registered for this user; no launch was attempted.'
        return
    }

    $appManifest = Get-AppxPackageManifest -Package $package.PackageFullName
    $desktopApp = $appManifest.Package.Applications.Application |
        Where-Object { $_.Executable -eq 'app/ChatGPT.exe' } |
        Select-Object -First 1
    if (-not $desktopApp) {
        Write-HealthLog "ERROR: Could not find the desktop application entry in package '$($package.PackageFullName)'."
        return
    }

    $desktopPath = Join-Path $package.InstallLocation ($desktopApp.Executable -replace '/', '\')
    $running = Get-CimInstance Win32_Process -Filter "Name = 'ChatGPT.exe'" |
        Where-Object { $_.ExecutablePath -and [string]::Equals($_.ExecutablePath, $desktopPath, [StringComparison]::OrdinalIgnoreCase) } |
        Select-Object -First 1
    if ($running) {
        return
    }

    try {
        $packageFamilyName = $package.PackageFamilyName
        $appUserModelId = "$packageFamilyName!$($desktopApp.Id)"
        Start-Process -FilePath (Join-Path $env:SystemRoot 'explorer.exe') -ArgumentList "shell:AppsFolder\$appUserModelId"
        Write-HealthLog "Started the Codex desktop app ($appUserModelId)."
    }
    catch {
        Write-HealthLog "ERROR: Failed to start the Codex desktop app: $($_.Exception.Message)"
    }
}

try {
    if ($Install -and $Uninstall) {
        throw 'Choose either -Install or -Uninstall, not both.'
    }
    elseif ($Install) {
        Install-HealthCheck
    }
    elseif ($Uninstall) {
        Uninstall-HealthCheck
    }
    else {
        Invoke-HealthCheck
    }
}
catch {
    Write-HealthLog "ERROR: $($_.Exception.Message)"
    throw
}
