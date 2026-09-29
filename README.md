# Northstar

An operating practice for AI-assisted projects and businesses, delivered as Markdown skills: clear intent, autonomous execution, reasoned decisions, verified delivery and checkpoint learning.

Northstar connects intended value to owned work and inspected outcomes. Engineering work starts with a usable MVP and improves in verified increments. Continuing operations get bounded commitments and reviews of real results. The owner's standards and authority stay visible.

## Four skills, one Northstar package

Install all four skills together. Use `$northstar` as the central coordinator, or invoke a companion directly when you need its specific capability:

**Codex-native, usable by other agents.** Claude Code, OpenCode and other agents can use these Markdown practices. `Codex` in a skill name identifies its origin, not an eligibility restriction. Installing agents must not skip a skill because of that name; follow the [host adaptation guidance](docs/misc/install.md#installing-from-another-agent).

| Skill | Purpose |
| --- | --- |
| [northstar](skills/northstar/SKILL.md) | Direction, execution, recovery, ownership and checkpoint learning. |
| [codex-qa](skills/codex-qa/SKILL.md) | Quality planning, functional/visual/adversarial inspection and verified repairs. Formerly Northstar QA. |
| [codex-subagents](skills/codex-subagents/SKILL.md) | Coordination, model allocation and handoffs, with [orchestrator](skills/codex-subagents/templates/orchestrator.md) and [supervisor](skills/codex-subagents/templates/supervisor.md) briefs. |
| [codex-advisor](skills/codex-advisor/SKILL.md) | Compact advice-only consultation, its caller and optional independent source reader. Formerly Luna Advisor in Subroute. |

One [installation flow](docs/misc/install.md) installs the package. Northstar loads companions only when needed, so installing four skills does not mean using four agents or making an advisor call on every task. The advisor still needs its separately configured service; package installation does not provision it or authorize calls.

[Install and use](docs/misc/install.md) · [中文说明](docs/misc/README.zh-CN.md)

**Self-learning is part of delivery:** before acting, retrieve applicable experience; at each meaningful checkpoint, inspect what worked and failed, check for drift from the intended outcome, and record the next decision. Reuse supported methods, avoid unchanged failed approaches, and supersede stale advice in existing project records. Solo agents review their own learning, which cannot substitute for independent QA or acceptance; teams consolidate evidence through short reviews of existing handoffs. See the [learning loop](skills/northstar/SKILL.md#learn-from-every-use).

The [operating system](skills/northstar/references/operating-system.md) defines required alignment, reasoned debate, superior-chaired decision meetings, expert consultation and operating reviews. Keep ceremonies that produce decisions and learning; remove redundant status and approval work. [Allocate model capability](skills/codex-subagents/SKILL.md#allocate-capability-and-cost) to the task and count management, review and rework when evaluating efficiency.

[Functional profiles](skills/codex-subagents/references/role-profiles.md) cover product/outcomes, architecture, building/integration, independent QA, experience/taste, operations and expertise. Activate needed functions and combine compatible roles. A builder may run development checks but cannot independently test, QA or judge the taste of its own deliverable. Missing independent review leaves acceptance unverified. [Agent-to-agent handoffs](skills/codex-subagents/references/agent-handoffs.md) preserve artifact identity, authority, evidence and recovery across agents; this package does not implement the A2A wire protocol.

Useful skill feedback can separately go to [Northstar Issues](https://github.com/stancsz/northstar/issues), with sanitized reports and existing publishing authority. Local learning does not wait for a public issue. See [learning and feedback](skills/northstar/references/skill-feedback.md).

## Project memory

- [North Star](docs/northstar/README.md): orchestrator-owned direction, owner standards, decisions, and open assumptions.
- [Goals](docs/goal/README.md): supervisor-owned outcomes, task coordination, acceptance, and remaining work.
- [Worker reports](docs/reports/README.md): worker-owned handoffs with deliverables, checks, gaps, and next actions.
- [Evaluations](docs/evals/README.md): observed results, criticism, fixes, and limitations.
- [Agent instructions](AGENTS.md): reading order and contribution practices.

Keep disposable artifacts in ignored `tmp/`. All agents share a 100 GB project artifact limit. Keep the root small and `docs/` limited to subdirectories; supporting docs go in `docs/misc/`. Keep documentation current and commits meaningful.
