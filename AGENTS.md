# Spot Advisor Repository Instructions

Keep this repository focused on a single, lean, token-efficient **Spot Advisor** protocol and skill for decoupling cheap local execution from compressed, 1-turn frontier judgment across any coding agent.

## Repository Pillars & Scope

- **`skills/`** — Lean, host-agnostic, 1-turn tool-free advisor skill (`skills/advisor/` in v0, transitioning to `skills/spot-advisor/` in Phase 1). **Advisor-only:** do not reintroduce multi-agent delegation frameworks, council chains, workspace-reading subagents, Stop-hook blockers, or `a2a-stack` runtimes.
- **`eval/`** — Reproducible benchmark harness, task manifests, and immutable JSONL telemetry matching [`eval/telemetry_schema.json`](eval/telemetry_schema.json).
- **`paper/`** — Self-contained arXiv LaTeX manuscript (`cs.SE` / `cs.AI`) generated strictly from logged `eval/` artifacts.
- **`docs/` & `ROADMAP.md`** — Generic installation guides, pre-registered empirical protocol (`docs/research-protocol.md`), and phased project milestones.

## Core Engineering & Scientific Rules

- **Token & reasoning budget safety:** Keep input packets compact and structured (`<= 4,000` chars target in Round 1; compact deltas via `--session-file`). Never cap `max_output_tokens` below thinking headroom on reasoning models (reasoning tokens bill against `max_output_tokens`); bound *visible* length via structured schema and parser checks.
- **Host-agnostic:** Keep the skill working cleanly for Codex CLI (`~/.codex/skills/`), Claude Code (`~/.claude/skills/`), and generic `.agents/skills/` hosts without hardcoding vendor-specific paths in primary docs.
- **Scientific Integrity (Zero Fabrication):** Never fabricate, extrapolate, or hand-edit benchmark metrics in `README.md`, `ROADMAP.md`, or `paper/main.tex`. Every reported number must trace directly to a committed, reproducible `eval/results/` artifact and run manifest.

## Verification

- For documentation changes, check that all relative Markdown links resolve and run `git diff --check`.
- For Python / advisor changes, run:
  ```powershell
  python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
  ```
- Stage intentional files only; keep `tmp/`, `eval/runs/`, and LaTeX build outputs out of Git.
