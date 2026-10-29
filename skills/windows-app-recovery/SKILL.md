---
name: windows-app-recovery
description: Keep a selected Windows desktop app available by checking for its window in the background and relaunching it when it exits. Use when the user asks to recover a Windows app after a crash or keep it running across sign-in sessions.
metadata:
  short-description: Recover Windows desktop apps
---

# Windows app recovery

Configure a per-user Scheduled Task to check a GUI app silently after sign-in and at a modest interval. Prefer checking for a top-level app window rather than any process, since Chromium/Electron apps can leave helper processes running after the window closes.

- Resolve the app's Start menu AppID with `Get-StartApps`; do not guess Store app package IDs.
- Use the reusable `scripts/watch-app.ps1` helper and pass the AppID and process name explicitly.
- Run the task as the signed-in user with an interactive token and least privilege. Hide the PowerShell host; do not run as SYSTEM or request elevation for a per-user desktop app.
- Start on user logon and repeat at a modest interval. Avoid overlapping instances.
- If the app was relaunched, minimize its window when requested. Windows Store GUI apps generally cannot be relaunched as truly headless services; be clear that the monitor is silent but the app itself may briefly appear or need a visible window to be usable.
- Verify the task registration, its action/trigger, and a safe run while the app is already open. Do not close the user's app just to test recovery unless they explicitly ask.
- Keep the monitor limited to the selected app. Remove or update only the task and helper created for this setup when requested.
