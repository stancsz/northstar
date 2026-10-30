# Northstar

### Give your AI team a mission. Let it own the decisions. Inspect the result.

**Five coordinated skills for delegated AI work.** Northstar connects your intent to accountable execution: clear authority, local initiative, proportionate acceptance, and learning that carries into the next assignment.

Start with [one delivery contract](skills/northstar/SKILL.md#delivery-contract): improve the highest-value existing workflow, finish and verify it before expanding, let one commander handle covered approvals, and stop optional work at diminishing returns. The five skills support that loop; they are not five stages to run.

This repository stays focused on simple, reusable skills and their necessary supporting tools. Applications and their implementation plans belong in separate repositories.

[中文](docs/misc/README.zh-CN.md) · [Install](docs/misc/install.md) · [How it works](#the-management-ideas-made-executable) · [Evidence](#what-has-actually-been-checked)

![Format: Markdown skills](https://img.shields.io/badge/format-Markdown_skills-2563eb)
![Five coordinated skills](https://img.shields.io/badge/package-5_coordinated_skills-0f766e)
[![License: MIT](https://img.shields.io/badge/license-MIT-475569)](LICENSE)

Built for founders, developers, and operators who want to delegate a meaningful outcome—and stop being the routing layer for every decision.

## You set the direction. The team owns the work.

An agent writes the code. Another declares it done. You discover the integration is missing, answer the same approval question again, and explain the goal for the third time.

Northstar addresses that management gap. It gives agents a way to carry intent, make decisions within a mandate, resolve dependencies, and deliver work someone else has actually inspected.

> **Delegate the outcome, the authority to act, and the responsibility to prove it.**

| Where AI work gets stuck | What Northstar requires |
| --- | --- |
| Every meaningful choice comes back to you. | A commander uses standing authority, makes covered tradeoffs, and escalates only decisions outside its mandate or indispensable human-held dependencies. |
| More agents produce more disconnected pieces. | One owner integrates the workflow. Managers resolve dependencies and conflicting interfaces using isolated worktrees and tree-SHA review binding when running in parallel. |
| “Done” means the author thinks it works. | Use one nonauthor check when the shared contract requires it; the commander verifies small, reversible work. Builders repair defects; reviewers recheck when independent review applies. |
| A stalled agent repeats the same experiment. | Bounded recovery carries failed attempts across handoffs; the owner chooses an alternative, resolves a dependency, or stops the failed route. |
| Every new chat forgets what was learned. | Checkpoints preserve verified state, lessons, rejected paths, and the next decision in your project's existing records. |
| A simple task grows a management bureaucracy. | Add functions and coordination only when needed. Reuse evidence, combine compatible roles, and remove redundant approvals. |

These are inspectable working rules. Their effectiveness depends on the executing agents and tools; see the [evaluation boundary](#what-has-actually-been-checked).

## Try it on one real outcome

Install the five coordinated sibling skills from this repository using the [installation guide](docs/misc/install.md). The optional [Agent Soak Testing skill](skills/agent-soak-testing/SKILL.md) and [Windows App Watchdog skill](skills/windows-app-watchdog/SKILL.md) are installed separately. Soak guidance does not include the separate [Soak framework](https://github.com/stancsz/soak). Then give the agent a bounded outcome, for example:

```text
Use $northstar to deliver a working CSV import flow in this project.

Done means: a user can upload a CSV, see validation errors, fix them,
and import valid rows without duplicate writes. Exercise that workflow.

You own implementation and reversible design decisions in this repository.
Reuse the existing stack and records. Delegate useful work and arrange
independent review. Resolve covered blockers yourself. Keep deployment
and new paid services outside this assignment.

Return the working result, verification evidence, and remaining limits.
```

The intended workflow: inspect the project → choose the smallest complete delivery → implement → verify (independently when warranted) → repair → hand off evidence and lessons. This is a usage example, not a reported benchmark.

**Host-agnostic across coding agents.** Codex, Claude Code, OpenCode, and other agents can use these skills directly. Preserve the five core skill names and sibling directories when installing; adapt invocation and native tools to the host. `subagent-orchestration` includes dedicated dispatch playbooks for both Codex CLI (`references/cli-dispatch.md`) and Claude Code CLI (`references/claude-cli-dispatch.md`), plus Git worktree isolation (`references/worktree-isolation.md`). [Host adaptation and prerequisites →](docs/misc/install.md#installing-from-another-agent)

## The management ideas, made executable

### 1. Shared intent. Distributed decisions.

The owner defines the desired value, standards, resources, and limits. The commander turns that mandate into actionable guidance. Workers choose methods close to the work. Authority travels with the assignment, so a handoff or a new context does not trigger another round of permission requests.

When a hard choice belongs to the commander, it must decide: weigh expected value, total cost, time, downside, and reversibility, then act. Difficulty alone does not send the decision back to the human. [Standing authority →](skills/northstar/SKILL.md#delivery-contract)

### 2. Managers own resolution.

A supervisor is accountable for a usable result. It supplies context, resolves dependencies, reconciles interfaces, and inspects integration. A status relay is insufficient.

Disagreement gets an evidence exchange. If it persists, the responsible superior hears the actual positions, decides within its authority, and assigns the next action. Material dissent stays visible; unanimous agreement is unnecessary. [Operating practice →](skills/northstar/references/operating-system.md)

### 3. Freedom to build. Proportionate acceptance.

Builders run relevant checks and learn from their work. Use one independent QA/taste review when required or when it can change acceptance: material user/data/security risk, cross-component integration, unresolved uncertainty or visual judgment. The commander directly verifies small, reversible changes with clear evidence. A reviewer must not certify work they created or repaired.

A manager who edits the work inherits the same conflict. A green build, a worker's report, or a confident “LGTM” cannot replace inspection. [Independent QA →](skills/independent-qa/SKILL.md)

### 4. Intelligence goes where it changes the outcome.

Use capable lower-cost execution for bounded work; apply stronger reasoning to direction, integration, consequential tradeoffs, and difficult diagnosis when warranted. Bring in a specialist for a concrete knowledge gap.

Judge efficiency by **accepted outcomes and total effort**, including coordination, review, expert calls, and rework. A cheaper model or a larger team does not establish savings. [Capability and cost →](skills/subagent-orchestration/SKILL.md#allocate-capability-and-cost)

### 5. Experience changes the next move.

At meaningful checkpoints, compare intent with evidence. Keep successful methods with their conditions, preserve failed approaches and reopening criteria, and use that record before acting again. Recovery ends in a decision and action; switching agents cannot reset the attempt history.

This is a project learning loop stored in ordinary records. It does not retrain model weights. [Learning →](skills/northstar/SKILL.md#learn-from-every-use) · [Recovery →](skills/northstar/SKILL.md#recover-from-a-stall)

The design adapts ideas from mission command, reversible decision-making, lean delivery, quality at the source, and strategy-to-execution management. Read the [source mapping](skills/northstar/references/operating-principles.md) and [operating-system rationale](skills/northstar/references/operating-system.md#sources-and-what-was-distilled) for what was retained and where the analogy ends. These are design influences, not institutional endorsements or proof of agent performance.

## Five core skills. One coherent way of working.

| Skill | Responsibility | Use directly when… |
| --- | --- | --- |
| [**Northstar**](skills/northstar/SKILL.md) | Direction, authority, quantitative goal framing, delivery, recovery, and learning. | You want an outcome carried through to inspected delivery. |
| [**Subagent Orchestration**](skills/subagent-orchestration/SKILL.md) | Scope, roles, worktree isolation, route preflight, and Codex / Claude Code CLI worker dispatch. | Work needs delegation, parallel execution, integration, or review separation. |
| [**Independent QA**](skills/independent-qa/SKILL.md) | Nonauthor functional/boundary, live runtime/browser, visual, adversarial, and spec review bound to tree SHAs. | You need to know whether the actual result meets the bar. |
| [**Advisor Council**](skills/advisor-council/SKILL.md) | Configurable advisor model or two-model council for capability-risk, design forks, image inspection, and Pi reading. | A documented capability risk, an unresolved visual/design fork, or a concrete knowledge gap. |
| [**Task Completion Review**](skills/task-completion-review/SKILL.md) | Audit a proposed stop, wait, or escalation against original requirements and authority; optional Stop-hook adapter. | An agent claims completion or wants to stop while requirements may remain. |
| [**Agent Soak Testing**](skills/agent-soak-testing/SKILL.md) *(standalone)* | Plan, run, and evaluate bounded soak tests for agent harnesses and models. | You need evidence about repeated-use reliability and anti-drift performance over time. |
| [**Windows App Watchdog**](skills/windows-app-watchdog/SKILL.md) *(standalone)* | Configure a per-user Windows scheduled task to monitor and relaunch a desktop app if its window closes. | You want automatic user-session recovery for a desktop app. |

Agent Soak Testing and Windows App Watchdog are standalone additions to the five-skill coordination workflow. Agent Soak Testing does not include the [Soak framework](https://github.com/stancsz/soak).

Use `$northstar` as the central entry point; each companion is also directly invocable. Install all five core skills, load what the task needs. One owner handles small, reversible changes; use one independent reviewer when the shared contract requires it. Add supervisors only when coordination warrants them.

```mermaid
flowchart TD
    O[Owner: outcome, standards, authority] --> N[Northstar: direction and accountable decisions]
    N --> B[Subagent Orchestration & Execution: scoped owners, worktrees, CLI workers]
    B --> Q[Independent QA: runtime, boundary, visual & adversarial review]
    Q -->|Repair needed| B
    Q -->|Tree-bound evidence| N
    N --> D[Accepted delivery and next commitment]
    N -. Capability risks, images or design forks .-> A[Advisor Council]
    A -. Advice .-> N
    D --> L[Checkpoint learning]
    L --> N
```

Core practices are Markdown. Task Completion Review adds an opt-in Stop-hook adapter; installing the skill does not activate a hook or elevate host permissions. The bundle also includes the Advisor caller and optional reader; [Advisor service setup](docs/misc/install.md#advisor-prerequisites) is separate. Installing the package does not start services or make provider calls. Nonvisual execution, coordination, and QA can be used without that service. Unresolved visual or aesthetic forks use [Advisor Council's image attachment loop](skills/advisor-council/SKILL.md#mandatory-visual-and-aesthetic-guidance) (`--image`), while routine functional and visual verification uses [Independent QA](skills/independent-qa/SKILL.md).

## Built for delivery—and the work after delivery

- **Build a product:** challenge the problem and risky assumptions, ship a complete usable slice, then improve accepted work in bounded increments.
- **Recover a stalled project:** resume the next unmet criterion, use existing evidence, and take a concrete action on the bottleneck.
- **Coordinate a team:** assign explicit write scopes, isolated Git worktrees, and integration ownership; preserve authority, artifact tree identity, and recovery state through handoffs.
- **Run an operation:** define a responsible operator and review period, inspect real signals, and decide whether to continue, repair, reallocate, expand, or stop.

Reuse your repository's issues, plans, and records. Northstar's own documentation layout is an example, not an installation requirement. Ongoing operation still requires the host's tools and scheduling; a Markdown skill alone cannot run unattended.

For [GitHub Spec Kit or spec-driven work](skills/northstar/references/spec-kit.md), keep the project's artifacts and review the spec in three independent passes: structure, evidence/privacy, then adversarial FR/SC scrutiny. Verify the implementation separately. Existing schemas remain authoritative; the optional eight-section profile is a Northstar customization.

## What has actually been checked

The repository contains inspectable practices and scoped evaluations:

| Evidence | What it supports |
| --- | --- |
| [Stall-recovery trials](docs/evals/stall-recovery-trials.md) | Limited execution evidence for specific recovery cases. |
| [Issue revisions and skill-behavior probes](docs/evals/issue-maturity.md) | Project-owned goals, spec-driven QA, and bounded fresh-context probes with explicit simulation and effectiveness limits. |
| [Roles and authority review](docs/evals/healthy-roles.md) | Role-conflict scenarios, independent acceptance rules, and scoped inspection of commander authority. |
| [Northstar reviewing Northstar](docs/evals/dogfood-review.md) | An actual multi-agent review and decision workflow, with disagreements and limits recorded. |
| [Central package migration evaluation](docs/evals/central-package.md) | Historical four-skill packaging, installation-path inspection, and offline Advisor regressions. |
| [Claude Code Subagents evaluation](docs/evals/claude-code-subagents.md) | Personal skill use limits and CLI worker integration (now unified under `subagent-orchestration`). |
| [Task Completion Review evaluation](docs/evals/completion-guardian/README.md) | Manual and direct CLI stopping cases, 58 runner checks and a new-native block/continuation/allow test; installation evidence and limits are recorded separately. |

**Still to prove:** comparative real-task gains, less owner intervention, total cost savings, sustained business results, and broad host integration. The [matched-task pilot](docs/northstar/next-proof.md) is proposed, not completed. This package guides behavior; it is not a runtime enforcement engine or a guarantee of autonomy.

## Explore, use, improve

[Install the package](docs/misc/install.md) · [Read the central skill](skills/northstar/SKILL.md) · [Report a skill issue](https://github.com/stancsz/northstar/issues)

Bring a concrete case: the intended outcome, what happened, the evidence, and the change that would help. Sanitize private data. Reproducible failures and useful field experience help improve the practices.

For contributors: [direction](docs/northstar/README.md), [goals](docs/goal/README.md), [handoffs](docs/reports/README.md), [evaluations](docs/evals/README.md), and [repository instructions](AGENTS.md). Northstar is [MIT licensed](LICENSE).
