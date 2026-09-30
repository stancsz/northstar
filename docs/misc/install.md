# Install and use the Northstar package

The package has four distinct skills: [Northstar](../../skills/northstar/SKILL.md), [Codex QA](../../skills/codex-qa/SKILL.md), [Codex Subagents](../../skills/codex-subagents/SKILL.md) and [Codex Advisor](../../skills/codex-advisor/SKILL.md). Install them together as sibling directories so their relative links work. Northstar is the central coordinator; all four keep their own `SKILL.md` and can be invoked directly.

## Installing from another agent

**Installer instruction:** this package is native to Codex, but its Markdown practices are also intended for Claude Code, OpenCode and other agents. Do not reject or skip a skill because its name contains `Codex` or you are a different agent. Select skills by the work they support. Preserve the four skill names and sibling directories when installing.

Use the receiving host's actual configured skill location and loading/invocation mechanism; the PowerShell paths and `$skill-name` examples below are Codex-oriented examples, not requirements for every host. If there is no native skill loader, read `northstar/SKILL.md` directly and load linked companions as needed. Tell the receiving agent that all four skills apply to it and point it to the bundled [host adaptation guidance](../../skills/northstar/SKILL.md#use-with-other-agents).

Adapt host-specific tools to available equivalents. Advisor service/model routes and optional reader prerequisites still apply; a different executor does not supply those dependencies or change the configured backend. This is portable operating guidance, not a claim that every integration has been tested on every host.

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
- `$codex-advisor`: consult early and frequently when [capability-risk tags](../../skills/codex-advisor/references/capability-triggers.md) apply; attach real images for visual direction. For ordinary work without a tag, consult on a concrete unresolved decision after local evidence. The current executor retains implementation and verification ownership.

Existing task and repository requirements remain binding. Reuse the target project's records and authorization; these skills do not require Northstar's repository layout. Direct invocation of a companion does not grant additional authority or reset recovery history.

## Upgrade renamed skills

`northstar-qa` is now **codex-qa**. `luna-advisor-escalation` from [Subroute](https://github.com/stancsz/subroute) is now **codex-advisor**. After copying and checking the four skills, archive or disable those two old-name installations in your host to avoid conflicting stale entries; preserve their customizations first. `northstar` and `codex-subagents` retain their names and receive normal updates. This repository change does not itself alter installed copies.

Reload updated skills or start a new chat because active chats may retain earlier instructions. Historical repository evaluations describe their original layouts; follow current installation guidance for new work.

## Advisor prerequisites

Ordinary compact consultation requires Python 3.10+ and the already-configured Subroute `experts` service at `http://127.0.0.1:4040/v1`, with Codex service authentication managed there. [Subroute setup](https://github.com/stancsz/subroute) remains the service's source of truth. Copying the skills does not deploy the service, supply credentials or grant spending/data-transmission authority.

Advisor is fixed to **GPT-6.1 Sol only**. Caller `--model sol` sends the versioned alias `codex-gpt-6.1-sol-advisor`; the dedicated service must expose that alias mapped to `codex-advisor/gpt-6.1-sol`. Astra and older Sol aliases are removed from this dedicated endpoint. An older service fails visibly; do not substitute another model or the worker gateway.

Optional [expert-directed reading](../../skills/codex-advisor/references/reader.md) additionally requires its documented Node/Pi/Git/ripgrep setup and the separate worker gateway at `http://localhost:4000/v1`. Do not silently use that worker route as the expert route. Nonvisual execution, QA and coordination do not require these services.

[Mandatory visual consultation](../../skills/codex-advisor/SKILL.md#mandatory-visual-and-aesthetic-guidance) uses repeatable `--image` arguments to send actual image bytes to the dedicated Advisor endpoint. The Subroute backend must include image-input support; an older text-only backend rejects these requests visibly. Optional Pi reading stays text-only: the Advisor sees attached screenshots and can dispatch Pi for source evidence. Missing image access leaves required visual consultation unverified.

Resolve `scripts/ask_expert.py` under the installed Codex Advisor directory shown by your skill loader. For the installation above:

```powershell
$advisorHome = Join-Path $env:USERPROFILE '.agents\skills\codex-advisor'
py (Join-Path $advisorHome 'scripts\ask_expert.py') --help
```

`--help` is local and makes no provider call. Read the [advisor skill](../../skills/codex-advisor/SKILL.md) before sending a packet.

## Continue existing work

For a long session: “Use Northstar. Read the active goal, applicable lessons and recovery checkpoint, verify current files, and continue the next unmet criterion. Preserve rejected approaches and remaining investigation limits.” See [recovery](../../skills/northstar/SKILL.md#recover-from-a-stall). Guidance is not an enforced runtime watchdog.

[Back to Northstar](../../README.md)
