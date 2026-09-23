# Northstar

**Production-first AI engineering.** Turn an ambiguous idea into a viable product direction, then keep each unit of research and implementation pointed at real user and business value.

Northstar makes the AI challenge the product thesis before coding: who needs this, what painful problem it solves, why they would choose or pay for it, and whether the economics and delivery path can hold up. If those answers are weak, the next step is focused validation—not a throwaway research prototype.

Once the direction is credible, the AI investigates implementation uncertainty and advances the product autonomously inside agreed bounds. It stops before the point of no return: production releases, destructive changes, spending, permission changes, and other external commitments require the contract's explicit approval.

The skill combines goal-driven engineering (`GOAL.md` as the durable, verifiable unit of work) with consequence-aware authority routing (`AUTO`, `GUARD`, `COCREATE`, `CHALLENGE`, `HUMAN_ONLY`). See [SKILL.md](SKILL.md) and [references/goal-driven-engineering.md](references/goal-driven-engineering.md).

## Quick start

```powershell
py -3 scripts/northstar_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
py -3 scripts/package_skill.py --output northstar.zip
```

`northstar_route.py` turns task intake into a JSON collaboration contract. `validate_contract.py` checks approval gates, acceptance evidence, rollback information, silence handling, and bounded scope.

This is a decision and execution aid, not a substitute for customer evidence, professional judgment, or organizational controls.

## Companion skill: Codex Subagents

This repository also includes a standalone Codex subagent workflow at [`.agents/skills/codex-subagents/SKILL.md`](.agents/skills/codex-subagents/SKILL.md). Use `$codex-subagents` when parallel work has a concrete benefit; it defaults to one agent.
