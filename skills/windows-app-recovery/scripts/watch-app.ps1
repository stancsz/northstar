param(
    [Parameter(Mandatory = $true)]
    [string] $AppId,

    [Parameter(Mandatory = $true)]
    [string] $ProcessName,

    [switch] $MinimizeAfterLaunch
)

$ErrorActionPreference = 'Stop'

function Get-AppWindow {
    Get-Process -Name $ProcessName -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
        Select-Object -First 1
}

if (Get-AppWindow) { exit 0 }

Start-Process -FilePath (Join-Path $env:WINDIR 'explorer.exe') `
    -ArgumentList "shell:AppsFolder\$AppId" -WindowStyle Hidden

if ($MinimizeAfterLaunch) {
    $source = 'using System; using System.Runtime.InteropServices; public static class AppRecoveryWindow { [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow); }'
    Add-Type -TypeDefinition $source

    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 500
        $window = Get-AppWindow
        if ($window) {
            [void][AppRecoveryWindow]::ShowWindowAsync($window.MainWindowHandle, 6)
            exit 0
        }
    } while ((Get-Date) -lt $deadline)
}

exit 0
