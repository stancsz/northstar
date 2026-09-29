# Install and use the Northstar package

The package has four distinct skills: [Northstar](../../skills/northstar/SKILL.md), [Codex QA](../../skills/codex-qa/SKILL.md), [Codex Subagents](../../skills/codex-subagents/SKILL.md) and [Codex Advisor](../../skills/codex-advisor/SKILL.md). Install them together as sibling directories so their relative links work. Northstar is the central coordinator; all four keep their own `SKILL.md` and can be invoked directly.

## Install all four

From this repository root in PowerShell:

```powershell
$northstarSkills = @('northstar', 'codex-qa', 'codex-subagents', 'codex-advisor')
$skillsDestination = Join-Path $env:USERPROFILE '.agents\skills'
foreach ($skillName in $northstarSkills) {
    $skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
    $skillDestination = Join-Path $skillsDestination $skillName
    New-Item -ItemType Directory -Force $skillDestination | Out-Null
    Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
}
```

Use your host's configured skills directory if different, such as `.codex/skills`. Preserve any local customization before replacing existing installations. Copy each whole directory, including its references, templates, scripts and metadata; copying only `SKILL.md` is incomplete. The four directories collectively are the package, not four separate setup exercises.

## Invoke the central coordinator or a companion

- `$northstar`: give the desired outcome. It applies execution/recovery/learning and loads companions when their triggers apply.
- `$codex-qa`: inspect an artifact and its actual workflow, classify findings and verify repairs.
- `$codex-subagents`: coordinate worthwhile independent workstreams with explicit scope, authority and handoffs.
- `$codex-advisor`: obtain compact advice for a concrete unresolved decision after bounded local evidence. The current executor retains implementation and verification ownership.

Existing task and repository requirements remain binding. Reuse the target project's records and authorization; these skills do not require Northstar's repository layout. Direct invocation of a companion does not grant additional authority or reset recovery history.

## Upgrade renamed skills

`northstar-qa` is now **codex-qa**. `luna-advisor-escalation` from [Subroute](https://github.com/stancsz/subroute) is now **codex-advisor**. After copying and checking the four skills, archive or disable those two old-name installations in your host to avoid conflicting stale entries; preserve their customizations first. `northstar` and `codex-subagents` retain their names and receive normal updates. This repository change does not itself alter installed copies.

Reload updated skills or start a new chat because active chats may retain earlier instructions. Historical repository evaluations describe their original layouts; follow current installation guidance for new work.

## Advisor prerequisites

Ordinary compact consultation requires Python 3.10+ and the already-configured Subroute `experts` service at `http://127.0.0.1:4040/v1`, with Codex service authentication managed there. [Subroute setup](https://github.com/stancsz/subroute) remains the service's source of truth. Copying the skills does not deploy the service, supply credentials or grant spending/data-transmission authority.

Optional [expert-directed reading](../../skills/codex-advisor/references/reader.md) additionally requires its documented Node/Pi/Git/ripgrep setup and the separate worker gateway at `http://localhost:4000/v1`. Do not silently use that worker route as the expert route. Core execution, QA and coordination do not require these services.

Resolve `scripts/ask_expert.py` under the installed Codex Advisor directory shown by your skill loader. For the installation above:

```powershell
$advisorHome = Join-Path $env:USERPROFILE '.agents\skills\codex-advisor'
py (Join-Path $advisorHome 'scripts\ask_expert.py') --help
```

`--help` is local and makes no provider call. Read the [advisor skill](../../skills/codex-advisor/SKILL.md) before sending a packet.

## Continue existing work

For a long session: “Use Northstar. Read the active goal, applicable lessons and recovery checkpoint, verify current files, and continue the next unmet criterion. Preserve rejected approaches and remaining investigation limits.” See [recovery](../../skills/northstar/SKILL.md#recover-from-a-stall). Guidance is not an enforced runtime watchdog.

[Back to Northstar](../../README.md)
