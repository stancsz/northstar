# Install and use the Northstar package

The coordinated package has five core skills: [Northstar](../../skills/northstar/SKILL.md), [Subagent Orchestration](../../skills/subagent-orchestration/SKILL.md), [Independent QA](../../skills/independent-qa/SKILL.md), [Advisor Council](../../skills/advisor-council/SKILL.md), and [Task Completion Review](../../skills/task-completion-review/SKILL.md). Install them together as sibling directories so their relative links work. Northstar is the central coordinator; all five keep their own `SKILL.md` and can be invoked directly. Subagent Orchestration unifies multi-agent delegation across native subagents, Codex CLI workers ([`references/cli-dispatch.md`](../../skills/subagent-orchestration/references/cli-dispatch.md)), Claude Code CLI workers ([`references/claude-cli-dispatch.md`](../../skills/subagent-orchestration/references/claude-cli-dispatch.md)), and Git worktree isolation ([`references/worktree-isolation.md`](../../skills/subagent-orchestration/references/worktree-isolation.md)).

The repository also includes the standalone [Agent Soak Testing skill](../../skills/agent-soak-testing/SKILL.md) and [Windows App Watchdog skill](../../skills/windows-app-watchdog/SKILL.md), installed separately. Agent Soak Testing is guidance; the [Soak framework](https://github.com/stancsz/soak) is a separate project and is not bundled or installed here.

The Windows App Watchdog skill is a separate utility. Its scheduled-task setup is not performed by copying the skill; read and follow its instructions only when you want to configure window monitoring for a specific Windows app.

## Installing from another agent

**Installer instruction:** these Markdown skills are host-agnostic and designed for Codex, Claude Code, OpenCode and other coding agents. Select skills by the work they support. Preserve the five core skill names and sibling directories when installing.

Use the receiving host's actual configured skill location and loading/invocation mechanism; the PowerShell paths and `$skill-name` examples below are Codex-oriented examples, not requirements for every host. If there is no native skill loader, read `northstar/SKILL.md` directly and load linked companions as needed. Tell the receiving agent that the five core skills are available and point it to the bundled [host adaptation guidance](../../skills/northstar/SKILL.md#use-with-other-agents).

Adapt host-specific tools to available equivalents. Advisor service/model routes and optional reader prerequisites still apply; a different executor does not supply those dependencies or change the configured backend. This is portable operating guidance, not a claim that every integration has been tested on every host.

## Install all five core skills

From this repository root in PowerShell:

```powershell
$northstarSkills = @('northstar', 'subagent-orchestration', 'independent-qa', 'advisor-council', 'task-completion-review')
$skillsDestination = Join-Path $env:USERPROFILE '.codex\skills'
foreach ($skillName in $northstarSkills) {
    $skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
    $skillDestination = Join-Path $skillsDestination $skillName
    New-Item -ItemType Directory -Force $skillDestination | Out-Null
    Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
}
```

Use your host's configured skills directory if different, such as `.agents/skills` or `.claude/skills`. Preserve any local customization before replacing existing installations. Copy each whole directory, including its references, templates, scripts and metadata; copying only `SKILL.md` is incomplete. The five directories collectively are the coordinated package, not five separate setup exercises.

To add Agent Soak Testing guidance, copy `skills/agent-soak-testing` to the same skills directory as a sibling. This does not install the separate Soak framework.

## Install the optional Agent Soak Testing skill

This section gives both client paths. Codex discovers personal skills under `.codex\skills`; Claude Code discovers personal skills under `.claude\skills` (or under `$env:CLAUDE_CONFIG_DIR\skills` when using an isolated profile). These are copies of the same source skill, installed as siblings to the five core skills.

Install to Codex from this repository root in PowerShell:

```powershell
$skillsDestination = Join-Path $env:USERPROFILE '.codex\skills'
$skillName = 'agent-soak-testing'
$skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
$skillDestination = Join-Path $skillsDestination $skillName
New-Item -ItemType Directory -Force $skillDestination | Out-Null
Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
```

Install to Claude Code's default personal skill directory:

```powershell
$skillsDestination = Join-Path $env:USERPROFILE '.claude\skills'
$skillName = 'agent-soak-testing'
$skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
$skillDestination = Join-Path $skillsDestination $skillName
New-Item -ItemType Directory -Force $skillDestination | Out-Null
Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
```

For an isolated Claude profile, set `$env:CLAUDE_CONFIG_DIR` to that profile root before computing `$skillsDestination`, and keep the same value when launching Claude Code. Verify the installed `SKILL.md` against the repository copy and restart the corresponding agent session when needed for discovery. Installing the skill does not install or run the separate Soak framework.

## Add global Codex instructions

Installing skills makes their workflows available; it does not change Codex's hidden system prompt or make every workflow run automatically. To have Codex consider the Advisor Council and delegates across projects, add a personal global `AGENTS.md`: `~/.codex/AGENTS.md` on macOS/Linux or `$env:USERPROFILE\.codex\AGENTS.md` on Windows. Create the `.codex` directory if needed, then append the guidance below to that file without replacing your existing instructions. Codex reads this as persistent user-level guidance; repository `AGENTS.md` files can add project-specific rules.

```markdown
## Proactively use Advisor Council and Subagent Orchestration

At the start of every nontrivial task, check whether Advisor Council or Subagent Orchestration (native subagents, Codex CLI workers, or Claude Code CLI workers) could materially improve the decision, speed, or quality. Read and follow the applicable installed skill before use. Keep the primary agent accountable for the outcome and verify delegated work.

- For substantive decisions, consult the Advisor when a documented capability-risk trigger applies or its answer could change the next action. Prefer council when a distinct configured model ID or alias could materially improve that decision. Keep each conclusion attributable; council advice is not a vote or independent acceptance. Use the bundled caller and configured routes. Do not spend calls on routine implementation, trivial questions, or generic reassurance.
- Council mode cannot include image attachments or Pi reader mode in the same invocation. For visual work, use the configured primary route's image-backed path; do not imply the council route inspected pixels unless it received them. If a selected route is unavailable or incompatible with a required path, report that route's limitation; make any route change explicitly within the task's authority.
- Before substantial work, assess whether a bounded subagent, Codex CLI worker, or Claude Code CLI worker assignment would add useful independent review or parallel progress. Delegate when likely benefit justifies coordination and cost; use distinct write scopes (or Git worktrees) and preserve independent acceptance. Check availability and follow `subagent-orchestration`. If unavailable or not useful, proceed directly and state a material limitation when relevant.
```

The bundled `advisor-council` skill explains how to configure primary and distinct council model identifiers and their limits without prescribing a vendor or backend model. The `subagent-orchestration` skill describes when and how to delegate across native subagents, Codex CLI, and Claude Code CLI. This global instruction guides Codex; it does not install services or configure external applications.

## Invoke the central coordinator or a companion

- `$northstar`: give the desired outcome. It applies execution/recovery/learning and loads companions when their triggers apply.
- `$subagent-orchestration`: coordinate worthwhile independent workstreams with explicit scope, Git worktree isolation, route preflight, and Codex CLI (`references/cli-dispatch.md`) or Claude Code CLI (`references/claude-cli-dispatch.md`) worker dispatch.
- `$independent-qa`: inspect an artifact and its actual runtime/browser workflow across boundary values and viewports, bind the verdict to the exact candidate tree SHA, and verify repairs.
- `$advisor-council`: consult early and frequently when [capability-risk tags](../../skills/advisor-council/references/capability-triggers.md) apply; attach real images for unresolved visual/design forks. For ordinary work without a tag, consult on a concrete unresolved decision after local evidence. The current executor retains implementation and verification ownership.
- `$task-completion-review`: review a proposed stop against the actual outcome and inherited authority. For the opt-in hook, follow its [Stop-hook setup](../../skills/task-completion-review/references/stop-hook.md); copying the skill does not enable it.

Existing task and repository requirements remain binding. Reuse the target project's records and authorization; these skills do not require Northstar's repository layout. Direct invocation of a companion does not grant additional authority or reset recovery history.

## Upgrade renamed and merged skills

The skills now use unified, self-explanatory, host-agnostic names:
- `codex-qa` (and earlier `northstar-qa`) is now **Independent QA** (`independent-qa`), including live runtime/browser verification and classical boundary-value test design.
- `codex-subagents` and `claude-code-subagents` (`claude-cli-worker`) are unified into **Subagent Orchestration** (`subagent-orchestration`), with dedicated references for Codex CLI dispatch (`references/cli-dispatch.md`), Claude Code CLI dispatch (`references/claude-cli-dispatch.md`), and Git worktree isolation (`references/worktree-isolation.md`).
- `codex-advisor` (and earlier `luna-advisor-escalation`) is now **Advisor Council** (`advisor-council`).
- `soak-testing` is now **Agent Soak Testing** (`agent-soak-testing`).
- `windows-app-recovery` is now **Windows App Watchdog** (`windows-app-watchdog`).
- `completion-guardian` and `dont-stop-early` are **Task Completion Review** (`task-completion-review`).

After copying and checking the updated skills, archive or remove old-name installations (`codex-qa`, `northstar-qa`, `codex-subagents`, `claude-code-subagents`, `claude-cli-worker`, `codex-advisor`, `soak-testing`, `windows-app-recovery`) in your host (`~/.codex/skills`, `~/.claude/skills`, or `.agents/skills`) to avoid conflicting duplicate entries; preserve any local customizations first. This repository change does not itself alter installed copies.

Reload updated skills or start a new chat because active chats may retain earlier instructions. Historical repository evaluations describe their original layouts; follow current installation guidance for new work.

For `task-completion-review` optional use across projects, its [event mode](../../skills/task-completion-review/references/stop-hook.md#across-projects-event-mode) pairs `UserPromptSubmit` and `Stop` through the same helper; it does not require a fixed project brief. Review and trust the exact commands through the host's normal flow, reload the host and capture a new request. Read the [tested installation and remaining limits](../evals/completion-guardian/installation.md); copying files or trusting a declaration alone is not evidence of actual continuation.

## Install the optional Windows App Watchdog skill

From this repository root in PowerShell:

```powershell
$skillsDestination = Join-Path $env:USERPROFILE '.codex\skills'
$skillName = 'windows-app-watchdog'
$skillSource = (Resolve-Path (Join-Path '.\skills' $skillName)).Path
$skillDestination = Join-Path $skillsDestination $skillName
New-Item -ItemType Directory -Force $skillDestination | Out-Null
Copy-Item -Path (Join-Path $skillSource '*') -Destination $skillDestination -Recurse -Force
```

Use your host's configured skills directory if it differs. The skill includes a PowerShell helper for its scheduled check. Installing it does not register a task or start monitoring; task configuration is a separate, app-specific action.

## Advisor prerequisites

Ordinary compact consultation requires Python 3.10+ and an already-configured Chat Completions service (`EXPERTS_BASE_URL` and `EXPERTS_API_KEY`). Copying the skills does not deploy a service, supply credentials or grant spending/data-transmission authority.

On Windows, the caller can read a saved user `EXPERTS_API_KEY` for a local loopback service when the process environment variable is absent. See the [authentication behavior](../../skills/advisor-council/SKILL.md#make-a-compact-advice-request). HTTP 401 requires correcting the key in the environment, not disabling authentication.

Advisor model selection is model-agnostic: pass any supported model identifier or alias with `--model` or `NORTHSTAR_ADVISOR_MODEL`. Set a separate `--council-model` or `NORTHSTAR_COUNCIL_MODEL` for Council; the two selections must be distinct. Failed selections remain visible; the caller does not substitute another model.

Optional [expert-directed reading](../../skills/advisor-council/references/reader.md) additionally requires its documented Node/Pi/Git/ripgrep setup and `READER_BASE_URL` (or `EXPERTS_BASE_URL`). Nonvisual execution, QA and coordination do not require these services.

[Mandatory visual consultation](../../skills/advisor-council/SKILL.md#mandatory-visual-and-aesthetic-guidance) uses repeatable `--image` arguments to send actual image bytes to the configured Advisor service. A text-only backend rejects these requests visibly. Optional Pi reading stays text-only: the Advisor sees attached screenshots and can dispatch Pi for source evidence. Missing image access leaves required visual consultation unverified.

Resolve `scripts/ask_expert.py` under the installed Advisor Council directory shown by your skill loader. For the installation above:

```powershell
$advisorHome = Join-Path $env:USERPROFILE '.codex\skills\advisor-council'
python (Join-Path $advisorHome 'scripts\ask_expert.py') --help
```

`--help` is local and makes no provider call. Read the [advisor skill](../../skills/advisor-council/SKILL.md) before sending a packet.

## Continue existing work

For a long session: “Use Northstar. Read the active goal, applicable lessons and recovery checkpoint, verify current files, and continue the next unmet criterion. Preserve rejected approaches and remaining investigation limits.” See [recovery](../../skills/northstar/SKILL.md#recover-from-a-stall). Guidance is not an enforced runtime watchdog.

[Back to Northstar](../../README.md)
