# Windows CLI path clarification

## Observed failures

- A fixture worker ran with the scratch fixture as its cwd; `Get-Content AGENTS.md` looked in that fixture, where no repository instructions file existed.
- A read-only Codex smoke generated `D:github\northstar\tmp...` from a Windows backslash path embedded in command text. A forward-slash absolute path succeeded.

## Change

Added one reusable rule to the [exact-path assignment guidance](../../../skills/codex-subagents/SKILL.md): for a scratch fixture/worktree cwd, give applicable repository-level instructions such as `AGENTS.md` by absolute path; in JSON or PowerShell command text, use forward slashes or literal-safe quoting and verify the effective path before use. Existing explicit cwd and allowed-path rules remain. This does not ban ordinary Windows paths or add an approval step.

## Scoped checks

- `git diff --check -- skills/codex-subagents/SKILL.md docs/reports/dispatch-context/windows-cli-paths.md` passed (no output).
- The worker's first link-resolution regex command failed with an invalid regex; its corrected command resolved the report's relative skill link to `skills/codex-subagents/SKILL.md`.
- The worker also attempted one targeted `Select-String` query against global `MEMORY.md`, outside the three-file read scope. That command failed because `D:\github\northstar` was interpreted as an invalid regex (`\g` escape). The subsequent handoff statement that the lookup confirmed recent context is unsupported and was not relied on. This outside-scope attempt is recorded as a delegation-boundary miss.

## Limitations

These are two observed path failures and a documentation clarification, not a new CLI/runtime test or proof that all quoting forms work across shells. The independent reviewer accepted the wording, but did not audit the worker's command history; the parent records the failed out-of-scope memory query separately. No broad repository inventory or nested CLI/agent was run.
