# Install

This repository provides the Northstar skill and a companion Codex subagents skill.

## Install the Northstar skill

Copy this repository directory into your local skills directory with the folder name `northstar`.

PowerShell:

```powershell
Copy-Item -Recurse -Force . "$env:USERPROFILE\.agents\skills\northstar"
```

Invoke it as `$northstar` when shaping a product direction or advancing a project. At project start, it challenges the customer/value/business thesis before implementation; once the direction is credible, it routes bounded execution and approval gates.

## Install Codex Subagents

When this repository is open in Codex, `.agents/skills/codex-subagents/` is discovered as a repository-local skill. To make it available across projects, copy that folder to your personal skills directory:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills\codex-subagents" | Out-Null
Copy-Item -Recurse -Force ".\.agents\skills\codex-subagents\*" "$env:USERPROFILE\.agents\skills\codex-subagents"
```

Invoke it explicitly with `$codex-subagents`. It defaults to one agent and delegates only when parallel work is likely to justify the coordination cost.
