# Install and use the Northstar package

The coordinated package has six distinct skills: [Northstar](../../skills/northstar/SKILL.md), [Codex QA](../../skills/codex-qa/SKILL.md), [Codex Subagents](../../skills/codex-subagents/SKILL.md), [Codex Advisor](../../skills/codex-advisor/SKILL.md), [Claude Code Subagents](../../skills/claude-code-subagents/SKILL.md) and [Task Completion Review](../../skills/task-completion-review/SKILL.md). Install them together as sibling directories so their relative links work. Northstar is the central coordinator; all six keep their own `SKILL.md` and can be invoked directly. Claude Code Subagents is a Codex-to-Claude CLI adapter; it does not install or configure Claude Code or its provider.

Claude Code Subagents invokes the available Claude Code CLI; it does not install or configure Claude Code itself. Follow **Install all six** below for the package copy flow.

## Installing from another agent

**Installer instruction:** this package is native to Codex, but its Markdown practices are also intended for Claude Code, OpenCode and other agents. Do not reject or skip a skill because its name contains `Codex` or you are a different agent. Select skills by the work they support. Preserve the six skill names and sibling directories when installing. `claude-code-subagents` is specifically for Codex delegating through the Claude Code CLI; use its instructions only when that host context is available.

Use the receiving host's actual configured skill location and loading/invocation mechanism; the PowerShell paths and `$skill-name` examples below are Codex-oriented examples, not requirements for every host. If there is no native skill loader, read `northstar/SKILL.md` directly and load linked companions as needed. Tell the receiving agent that the six skills are available and point it to the bundled [host adaptation guidance](../../skills/northstar/SKILL.md#use-with-other-agents).

Adapt host-specific tools to available equivalents. Advisor service/model routes and optional reader prerequisites still apply; a different executor does not supply those dependencies or change the configured backend. This is portable operating guidance, not a claim that every integration has been tested on every host.

## Install all six

From this repository root in PowerShell:

```powershell
$northstarSkills = @('northstar', 'codex-qa', 'codex-subagents', 'codex-advisor', 'claude-code-subagents', 'task-completion-review')
$skillsDestination = Join-Path $env:USERPROFILE '.codex\skills'
foreach ($skillName in $northstarSkills) {
    $skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
    $skillDestination = Join-Path $skillsDestination $skillName
    New-Item -ItemType Directory -Force $skillDestination | Out-Null
    Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
}
```

Use your host's configured skills directory if different, such as `.agents/skills`. Preserve any local customization before replacing existing installations. Copy each whole directory, including its references, templates, scripts and metadata; copying only `SKILL.md` is incomplete. The six directories collectively are the coordinated package, not six separate setup exercises.

## Add global Codex instructions

Installing skills makes their workflows available; it does not change Codex's hidden system prompt or make every workflow run automatically. To have Codex consider the Advisor and delegates across projects, add a personal global `AGENTS.md`: `~/.codex/AGENTS.md` on macOS/Linux or `$env:USERPROFILE\.codex\AGENTS.md` on Windows. Create the `.codex` directory if needed, then append the guidance below to that file without replacing your existing instructions. Codex reads this as persistent user-level guidance; repository `AGENTS.md` files can add project-specific rules.

```markdown
## Proactively use Codex Advisor and delegates

At the start of every nontrivial task, check whether Codex Advisor, Codex subagents, or Claude Code Subagents could materially improve the decision, speed, or quality. Read and follow the applicable installed skill before use. Keep the primary agent accountable for the outcome and verify delegated work.

- For substantive decisions, consult the Advisor when a documented capability-risk trigger applies or its answer could change the next action. Prefer council when an independent Gemini view could materially improve that decision. Keep each conclusion attributable; council advice is not a vote or independent acceptance. Use the bundled caller and configured routes. Do not spend calls on routine implementation, trivial questions, or generic reassurance.
- Council mode cannot include image attachments or Pi reader mode in the same invocation. For visual work, follow the skill's image-backed Sol review and do not imply Gemini inspected pixels. If council is unavailable or incompatible with a required path, state why and continue with the supported route.
- Before substantial work, assess whether a bounded Codex subagent or Claude Code assignment would add useful independent review or parallel progress. Delegate when likely benefit justifies coordination and cost; use distinct write scopes and preserve independent acceptance. Check availability and follow the corresponding skill. If unavailable or not useful, proceed directly and state a material limitation when relevant.
```

The bundled `codex-advisor` skill explains the Gemini-then-Sol council route and its limits. The `codex-subagents` and `claude-code-subagents` skills describe when and how to delegate. This global instruction guides Codex; it does not install services or configure external applications.

## Invoke the central coordinator or a companion

- `$northstar`: give the desired outcome. It applies execution/recovery/learning and loads companions when their triggers apply.
- `$codex-qa`: inspect an artifact and its actual workflow, classify findings and verify repairs.
- `$codex-subagents`: coordinate worthwhile independent workstreams with explicit scope, authority and handoffs.
- `$codex-advisor`: consult early and frequently when [capability-risk tags](../../skills/codex-advisor/references/capability-triggers.md) apply; attach real images for visual direction. For ordinary work without a tag, consult on a concrete unresolved decision after local evidence. The current executor retains implementation and verification ownership.
- `$task-completion-review`: review a proposed stop against the actual outcome and inherited authority. For the opt-in hook, follow its [Stop-hook setup](../../skills/task-completion-review/references/stop-hook.md); copying the skill does not enable it.
- `$claude-code-subagents`: delegate one bounded task from Codex through the Claude Code CLI when the user asks for it or it adds useful independent capacity. Check CLI access and model availability first; preserve the configured provider/auth path and stop when an evidence-based smoke test fails.

Existing task and repository requirements remain binding. Reuse the target project's records and authorization; these skills do not require Northstar's repository layout. Direct invocation of a companion does not grant additional authority or reset recovery history.

## Upgrade renamed skills

`northstar-qa` is now **codex-qa**. `luna-advisor-escalation` from [Subroute](https://github.com/stancsz/subroute) is now **codex-advisor**. After copying and checking the six skills, archive or disable those two old-name installations in your host to avoid conflicting stale entries; preserve their customizations first. Existing skill names remain stable. This repository change does not itself alter installed copies.

Reload updated skills or start a new chat because active chats may retain earlier instructions. Historical repository evaluations describe their original layouts; follow current installation guidance for new work.

`completion-guardian` and `dont-stop-early` are now **Task Completion Review** (`task-completion-review`). Preserve local customizations, update hook commands to the new directory and retain the existing state directory so review budgets/history survive. Review and trust the changed commands through the normal host flow, then retire the old installation to avoid duplicate checks.

For optional use across projects, its [event mode](../../skills/task-completion-review/references/stop-hook.md#across-projects-event-mode) pairs `UserPromptSubmit` and `Stop` through the same helper; it does not require a fixed project brief. Review and trust the exact commands through the host's normal flow, reload the host and capture a new request. Read the [tested installation and remaining limits](../evals/completion-guardian/installation.md); copying files or trusting a declaration alone is not evidence of actual continuation.

## Advisor prerequisites

Ordinary compact consultation requires Python 3.10+ and the already-configured Subroute `experts` service at `http://127.0.0.1:4040/v1`, with Codex service authentication managed there. [Subroute setup](https://github.com/stancsz/subroute) remains the service's source of truth. Copying the skills does not deploy the service, supply credentials or grant spending/data-transmission authority.

Advisor is fixed to **GPT-6.1 Sol only**. Caller `--model sol` sends the versioned alias `codex-gpt-6.1-sol-advisor`; the dedicated service must expose that alias mapped to `codex-advisor/gpt-6.1-sol`. Astra and older Sol aliases are removed from this dedicated endpoint. An older service fails visibly; do not substitute another model or the worker gateway.

Optional [expert-directed reading](../../skills/codex-advisor/references/reader.md) additionally requires its documented Node/Pi/Git/ripgrep setup and the separate worker gateway at `http://localhost:4000/v1`. Do not silently use that worker route as the expert route. Nonvisual execution, QA and coordination do not require these services.

[Mandatory visual consultation](../../skills/codex-advisor/SKILL.md#mandatory-visual-and-aesthetic-guidance) uses repeatable `--image` arguments to send actual image bytes to the dedicated Advisor endpoint. The Subroute backend must include image-input support; an older text-only backend rejects these requests visibly. Optional Pi reading stays text-only: the Advisor sees attached screenshots and can dispatch Pi for source evidence. Missing image access leaves required visual consultation unverified.

Resolve `scripts/ask_expert.py` under the installed Codex Advisor directory shown by your skill loader. For the installation above:

```powershell
$advisorHome = Join-Path $env:USERPROFILE '.codex\skills\codex-advisor'
python (Join-Path $advisorHome 'scripts\ask_expert.py') --help
```

`--help` is local and makes no provider call. Read the [advisor skill](../../skills/codex-advisor/SKILL.md) before sending a packet.

## Continue existing work

For a long session: “Use Northstar. Read the active goal, applicable lessons and recovery checkpoint, verify current files, and continue the next unmet criterion. Preserve rejected approaches and remaining investigation limits.” See [recovery](../../skills/northstar/SKILL.md#recover-from-a-stall). Guidance is not an enforced runtime watchdog.

[Back to Northstar](../../README.md)
