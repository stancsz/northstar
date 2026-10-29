# Windows app recovery skill package review

Goal: [Windows app recovery skill](../goal/windows-app-recovery/GOAL.md)

Date: 2026-10-19. Scope: the added standalone skill, its helper, and package/install documentation. Review question: can an agent discover and install the utility without confusing it with the five coordinated workflow skills?

## Observations

- The repository contains `skills/windows-app-recovery/SKILL.md` and `scripts/watch-app.ps1`, copied from the personal skill that was used to configure the current Windows ChatGPT app.
- The skill instructs use of a per-user hidden Scheduled Task and checks for a top-level app window. It notes the interactive-session and possible relaunch-window limits.
- The central Northstar skill routes Windows app recovery to the standalone utility. The English and Chinese READMEs, contributor instructions, direction, and install guide describe it as optional and separate. The install guide copies the entire skill directory and says installation alone does not create a scheduled task.
- The installed helper ran while the ChatGPT window was already open and exited successfully without starting another window. The registered task is hidden, uses the current user's logon trigger, repeats every minute, and its safe run returned result `0`.
- The repository copy is validated with the skill validator; detailed link and whitespace checks are recorded with the delivery.

## Limits

No app crash or forced close was induced, so automatic recovery after an actual stop was not exercised. Relaunching a GUI app may briefly show its window before the helper minimizes it. Windows sleep, shutdown, sign-out, task policy, and network loss remain outside this monitor. This is a scoped packaging and current-machine configuration review, not a broad Windows compatibility test.
