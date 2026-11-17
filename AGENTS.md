# Codex Advisor Repository Instructions

Keep this repository focused on a single, lean, token-efficient **Codex Advisor** skill (`skills/advisor/`) for **Codex CLI** and **Claude Code**.

## Scope & Principles

- **Advisor-only:** Do not reintroduce subagent delegation skills, multi-model council chains, Pi workspace readers, Stop-hook blockers, or application runtimes (`a2a-stack`).
- **Token efficiency first:** Every change to `skills/advisor/SKILL.md` or `skills/advisor/scripts/ask_expert.py` should keep packets minimal, responses short (`Verdict / Next / Prompt / Risk`), and consultations 1-turn.
- **Host-agnostic:** Keep `skills/advisor/` working cleanly for both Codex CLI (`~/.codex/skills/advisor`, `~/.agents/skills/advisor`) and Claude Code (`~/.claude/skills/advisor`).

## Verification

- For documentation changes, check local Markdown links and run `git diff --check`.
- For `ask_expert.py` changes, run:
  ```powershell
  python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
  ```
- Stage intentional files only; keep `tmp/` and scratch output out of Git.
