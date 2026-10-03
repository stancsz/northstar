# Windows Codex Desktop health check

[`scripts/windows/codex-health-check.ps1`](../../scripts/windows/codex-health-check.ps1) checks whether the signed-in user's Codex desktop app is running. If it is closed, the script launches the registered `OpenAI.Codex` app. It identifies the desktop app process from its Windows package path, so Codex background services do not count as the desktop app.

## Install

From the repository root in PowerShell, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\codex-health-check.ps1" -Install
```

The script registers **Codex Desktop Health Check** in Task Scheduler as one hidden, long-running PowerShell process. It starts when the current user signs in and checks every 1 minute in that user's interactive session. It does not require a stored password or administrator privileges. If the repository moves, run the install command again from its new path; this updates and restarts the task.

To check once without installing the task, omit `-Install`. To remove the task, run the same command with `-Uninstall`.

Only recovery attempts and errors are logged to `%LOCALAPPDATA%\CodexHealthCheck\health-check.log`; healthy checks do not write log entries.
