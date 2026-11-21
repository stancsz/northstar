# Spot Advisor 2.1 pilot

Spot Advisor lets a coding agent ask for one focused second opinion while
keeping repository access, edits, and verification with the executor. A
structured consultation returns a verdict, an action, a check, and a risk.
You can preview the advice packet and inspect a session after interruption.

[Install for Codex or Claude Code](docs/install.md) · [Advisor skill](skills/advisor/SKILL.md) · [2.1 roadmap](docs/spot-advisor-2.1-roadmap.md) · [Evaluation](eval/README.md)

The 2.1 pilot gives attempts within a single consultation a shared ID. The
checkpoint harness compares Luna continuing alone, Luna with one Astra
reply, and Astra taking over. Local and public-repository qualifications
have exercised these three branches. Native Claude Advisor needs an
Anthropic API credential for the live benchmark. Developer trials and the
larger comparison remain part of the [execution plan](docs/spot-advisor-2.1-execution-plan.md).
