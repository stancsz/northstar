---
name: windows-app-watchdog
description: Monitor a selected Windows desktop GUI app via a per-user Scheduled Task and relaunch it when its top-level window closes.
metadata:
  short-description: Relaunch closed Windows desktop apps
---

# Windows App Watchdog

Configure a silent per-user Windows Scheduled Task that checks whether a desktop GUI app's top-level window is open and relaunches it when closed. Check for a top-level window (`MainWindowHandle`) rather than any background process, because Chromium/Electron apps often leave helper processes running after the main window exits.

- **Resolve the exact AppID:** Look up the app's Start menu `AppID` with `Get-StartApps`; never guess Windows Store package IDs.
- **Use the bundled PowerShell helper:** Invoke `scripts/watch-app.ps1` with explicit `-AppId` and `-ProcessName` arguments (plus optional `-MinimizeAfterLaunch`).
- **Least-privilege user session:** Register the Scheduled Task to run as the signed-in user with an interactive token (`LogonType Interactive`) and hidden PowerShell host (`-WindowStyle Hidden`). Never run as `SYSTEM` or request administrator elevation for a per-user desktop app.
- **Cadence and single-instance safety:** Trigger at user sign-in and repeat at a modest interval while avoiding overlapping task instances.
- **State UI behavior clearly:** If `-MinimizeAfterLaunch` is set, the helper minimizes the window once it appears. Be explicit that Windows Store/GUI apps cannot run as headless services—the watchdog check is silent, but relaunching the app briefly creates a visible window.
- **Safe verification:** Verify task registration, triggers/actions, and a no-op check while the app is already open. Never close the user's running app just to test relaunch unless explicitly asked.
- **Scoped cleanup:** Modify or remove only the task and helper created for the selected app.
