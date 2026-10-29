---
name: claude-code-subagents
description: Delegate bounded work from Codex to Claude Code CLI. Use when requested or when independent capacity helps; inspect and integrate the result.
---

# Claude Code Subagents

Follow the shared [Northstar delivery contract](../northstar/SKILL.md#delivery-contract). Codex is the commander and accepting owner; Claude Code is a bounded CLI worker. Load this skill only when Claude Code is requested or adds clear independent value.

## Decide and assign

Group related criteria into one coherent, bounded assignment with disjoint writable files (never let Codex and Claude edit the same file concurrently). Pass inherited authority, exact write scope, baseline context, verification command, and wall-clock deadline in a self-contained brief. Stop optional delegation once required acceptance passes.

## Verify CLI readiness before use

1. **Check CLI availability and settings:** Verify `claude` is installed and use the host's configured authentication and model settings (or pass an explicit `--model <id>` when requested). Never read, print, or log credentials or tokens, and never mutate global user settings.
2. **Isolate child configuration when needed:** When running in an isolated profile (`CLAUDE_CONFIG_DIR`, `--bare`, or `--setting-sources ""`), pass any required model selection explicitly so unrelated user-profile defaults do not leak into the child invocation.
3. **Bounded CLI smoke:** When the CLI setup is new or reconfigured, run one bounded read-only smoke (`claude -p --permission-mode plan ...`) and confirm it exits `0` with the expected marker before launching the worker.

## Run bounded work

- **Never use `--dangerously-skip-permissions`.** Use read-only/plan mode for audits, or explicitly enable only the native tools needed (`Read`, `Edit`, `Write`, `Bash`) for scoped implementation.
- **Bound wall-clock time and stop on retry storms:** Enforce a parent wall-clock timeout alongside `--max-turns` and `--max-budget-usd`. Stream output with `--output-format stream-json` (or `json`) keeping stdout and stderr in separate task-scratch files. **Terminate the child immediately on the first native `api_retry` (HTTP 429) or `unrecognized_model` event** rather than burning budget in retry loops.
- **Inspect only after process exit:** Wait for the child process to exit before reading the captured JSONL stream and checking diffs. Require native tool events (`Read`/`Write`/`Edit`/`Bash`), a final handoff, and exit code `0`.

## Accept and integrate

1. Inspect `git status` and diffs before and after dispatch; reject any out-of-scope file edits.
2. Independently run the verification check and inspect the actual artifact. Claude cannot certify its own authored work as independent QA.
3. Record the artifact, check results, usage/cost metrics actually returned, remaining gaps, and next action in the project's existing record.

See local `claude --help`, the official [CLI reference](https://code.claude.com/docs/en/cli-reference), and [environment variables](https://code.claude.com/docs/en/env-vars).
