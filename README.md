# Northstar

Production-first AI engineering practices, delivered as Markdown skills.

Northstar helps agents clarify a worthwhile product direction, learn from strong comparable products, do the implementation research, and carry useful work through critique, repair, and verification. It keeps the owner's quality standards and approval boundaries visible throughout.

## Skills

- [Northstar](skills/northstar/SKILL.md): product direction, competitive comparisons, autonomous execution, critics, verification, and repository practices.
- [Codex Subagents](skills/codex-subagents/SKILL.md): focused delegation, shared documentation, and clean handoffs.

[Install and use](docs/misc/install.md) · [中文说明](docs/misc/README.zh-CN.md)

## Project memory

- [North Star](docs/northstar/README.md): orchestrator-owned direction, owner standards, decisions, and open assumptions.
- [Goals](docs/goal/README.md): supervisor-owned outcomes, task coordination, acceptance, and remaining work.
- [Worker reports](docs/reports/README.md): worker-owned handoffs with deliverables, checks, gaps, and next actions.
- [Evaluations](docs/evals/README.md): observed results, criticism, fixes, and limitations.
- [Agent instructions](AGENTS.md): reading order and contribution practices.

Keep disposable artifacts in ignored `tmp/`. All agents share a 100 GB project artifact limit. Keep the root small and `docs/` limited to subdirectories; supporting docs go in `docs/misc/`. Keep documentation current and commits meaningful.
