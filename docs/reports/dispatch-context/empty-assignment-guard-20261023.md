# Empty-assignment guard for `Invoke-CodexChild`

**Goal** — `dispatch-context`, task `empty-assignment-guard`
**Date** — 2026-10-23
**Scope** — `skills/codex-subagents/SKILL.md`, `tests/test_codex_subagents_helper.py`

## Outcome

`Invoke-CodexChild` now rejects an empty or whitespace-only assignment with one stable
message before it resolves the working directory, inspects Codex-home/adapter state,
mutates the environment, or invokes the Codex CLI.

## Changed behavior

- The `$Assignment` parameter gained `[AllowEmptyString()]`. Without it, PowerShell's
  mandatory-parameter binder rejects `''` on its own with
  `Cannot bind argument to parameter 'Assignment' because it is an empty string.`, while
  a whitespace-only assignment passes binding and reaches the helper body. The two cases
  therefore failed differently. `AllowEmptyString` lets both reach the helper's own
  check, so both fail with the same message. It does not change the parameter's
  required-ness, any default, or the behavior for nonblank assignments.
- The first statement in the function body is now:

  ```powershell
  if ([string]::IsNullOrWhiteSpace($Assignment)) {
      throw 'Assignment must not be empty or whitespace-only: provide the work item for the delegated Codex worker.'
  }
  ```

  `[string]::IsNullOrWhiteSpace` covers empty, spaces, tabs, and newline-only values.
- A short prose note after the helper fence documents the guard, its ordering, and the
  stable message.

## Tests

`tests/test_codex_subagents_helper.py` gains one parametrized test with two cases
(`empty`, `whitespace-newline`). For each case it runs the extracted helper against the
local `codex` stub and asserts:

- the dispatch fails and the message contains `must not be empty or whitespace-only`;
- the stub was never called (`payload["invocations"] == []`);
- exact caller-environment equality across the rejected call (`payload["before"] ==`
  `payload["after"]`);
- the same guard message is reported when the working directory does not exist, which
  shows the guard runs before path resolution rather than after it.

The working directory used in the primary assertion is a valid synthetic project, and
`USERPROFILE`/`HOME` are set the same way the existing invalid-directory test sets them,
so the call would otherwise have reached the stub. The rejection is caused by the guard,
not by an unrelated precondition.

## Verification

```
py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py
24 passed in 19.20s
```

24 = the 22-test baseline plus the two new parameter cases; no existing test changed
behavior. `git diff --check` on the two changed tracked source files exits 0 (the
LF/CRLF warning for `skills/codex-subagents/SKILL.md` is a pre-existing line-ending
notice for that file, not a whitespace error).

## Limits

- The suite is an offline regression against a local PowerShell `codex` stub. It does not
  exercise a live Codex CLI dispatch, a real Codex home, or the real Task Completion
  Review adapter.
- The guard is verified only through the two documented blank shapes (empty string and
  whitespace/tab/newline). Other whitespace-only encodings are covered by
  `[string]::IsNullOrWhiteSpace` but were not separately exercised.
- `docs/reports/README.md` was not updated; that index is outside this task's write
  scope, so the parent owns it.

## Files changed

- `skills/codex-subagents/SKILL.md` — parameter attribute, guard, prose note.
- `tests/test_codex_subagents_helper.py` — new parametrized test.
- `docs/reports/dispatch-context/empty-assignment-guard-20261023.md` — this report.
- Scratch only: `tmp/dispatch-context/implementation-empty-assignment-20261023/`.

## Parent acceptance and independent-review attempt

The primary inspected the helper's `[AllowEmptyString()]` binding attribute and first-statement guard, verified they precede working-directory resolution and all environment/CLI work, inspected the two parametrized synthetic cases including their invalid-directory ordering assertions, and independently reran the full focused suite: 24 passed in 15.35 seconds. Scoped diff and whitespace checks passed. Accept this narrow source increment; the offline local-stub tests do not prove live CLI behavior, and no unchanged argument path or route configuration was modified by the guard.

A separate read-only Codex CLI reviewer was dispatched through the same freshly verified Subroute `default`/Responses helper. It completed five native read-only commands, read only assigned source/test/report ranges, and made no writes, but produced no verdict, final handoff, or report by the 90-second checkpoint. The parent stopped it as incomplete; receipt `tmp/dispatch-context/implementation-empty-assignment-20261023/reviewer.jsonl`, stderr and exit status are retained. Do not count this attempt as an independent reviewer verdict. Parent acceptance is based on direct inspection and the independent test rerun above.
