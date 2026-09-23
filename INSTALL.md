# Install

This repository provides the Q4 collaboration skill and a companion Codex subagents skill.

## Install the Q4 collaboration skill

Copy this repository directory into your local skills directory with the folder name `q4-collaboration-protocol`.

PowerShell:

```powershell
Copy-Item -Recurse -Force . "$env:USERPROFILE\.agents\skills\q4-collaboration-protocol"
```

Invoke it as `$q4-collaboration-protocol`, then give it a goal, project, or task to classify.

## Install Codex Subagents

When this repository is open in Codex, `.agents/skills/codex-subagents/` is discovered as a repository-local skill. To make it available across projects, copy that folder to your personal skills directory:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\codex-subagents" | Out-Null
Copy-Item -Recurse -Force ".\.agents\skills\codex-subagents\*" "$env:USERPROFILE\.agents\skills\codex-subagents"
```

Invoke it explicitly with `$codex-subagents`. It defaults to one agent and delegates only when parallel work is likely to justify the coordination cost.
