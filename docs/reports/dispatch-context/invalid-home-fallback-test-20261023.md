# Invalid caller HOME falls back to USERPROFILE and is restored

Goal: dispatch-context / invalid-home-fallback-test
Date: 2026-10-23
Status: complete, one focused regression added, no production source changed

## Outcome

One pytest case now covers the previously uncovered Windows dispatch-helper branch where
the caller's `HOME` is present but points to a directory that does not exist. The case proves
that `Invoke-CodexChild` hands the child an existing `USERPROFILE` as `HOME` and restores the
caller's exact original invalid `HOME` value after the call returns. The helper behaved as
documented on this host; no production-source edit was needed or made.

## Files changed

- `tests/test_codex_subagents_helper.py` (pre-existing untracked work; one case appended, all
  other content preserved)
- `docs/reports/dispatch-context/invalid-home-fallback-test-20261023.md` (this report, new)

## What was inspected

- `AGENTS.md`
- `tests/test_codex_subagents_helper.py`
- The `Invoke-CodexChild` function in `skills/codex-subagents/SKILL.md` (lines 142-198)

Relevant helper behaviour, quoted from `skills/codex-subagents/SKILL.md`:

- Lines 157-166: the helper captures `$hadHome` / `$priorHome`, then enters the fallback when
  `HOME` is absent, empty, **or not an existing container** (line 160), and only accepts a
  `USERPROFILE` that exists as a container.
- Line 172: `if ($homeFallback) { $env:HOME = $homeFallback }` sets the child `HOME`.
- Line 193: `if ($hadHome) { $env:HOME = $priorHome }` in the `finally` block restores the exact
  prior value; the `else` branch removes `HOME` only when the caller had none.

## Existing coverage already in the test file

- `HOME` absent -> fallback to `USERPROFILE`, `HOME` removed again after return.
- `HOME` present but empty -> fallback to `USERPROFILE`, empty `HOME` restored.
- `HOME` present and existing -> passed through to the child unchanged.
- `HOME` absent and `USERPROFILE` missing -> rejected before dispatch, stub never runs.

The gap was the fourth state: `HOME` present, non-empty, and pointing at a path that does not
exist. Nothing else in the file exercised that combination.

## Test added

`test_invalid_home_falls_back_to_userprofile_and_restores_the_original_path`

Design, reusing the file's existing `run_helper` / `workspace` harness:

- The caller `HOME` is set to `<workspace root>/absent-home`, a path that is never created; the
  test asserts after the run that the directory still does not exist, so the helper cannot be
  passing because it created the missing directory.
- `USERPROFILE` is set to the existing synthetic `workspace["user_profile"]` directory, and
  `HOME` is set to the invalid path, so the invalid `HOME` branch and the fallback branch are
  both reached.
- Assertions: the driver receipt reports no error; the codex stub dispatched exactly once; the
  child-visible `HOME` is present and equals the synthetic `USERPROFILE` (compared through
  `os.path.normcase`/`os.path.normpath`, matching the file's existing convention); and the
  caller's `HOME` is byte-identical before and after the call, i.e. exactly the invalid path
  string, not the fallback value.
- The child-visible `HOME` assertion also excludes the invalid path implicitly: a pass-through
  implementation would fail it.

## Test result

Command run from `D:\github\northstar`:

```
py -3 -m pytest -q tests/test_codex_subagents_helper.py
```

Output:

```
...............                                                          [100%]
15 passed, 1 warning in 7.68s
```

Exit code 0. The 15 cases are the 14 pre-existing cases plus the one added here; every prior
case still passes, so the addition did not change existing behaviour.

The single warning is a `PytestCacheWarning` from the pytest cache provider, which could not
create `D:\github\northstar\.pytest_cache\v\cache` (`WinError 183`, a file already exists at
that path). It is a pre-existing repository condition, not caused by this change, and it does
not affect the test outcome. No cleanup was performed.

## Event-boundary observations

- The two file edits were applied with the native file-edit tool, one patch per named path:
  `tests/test_codex_subagents_helper.py` and this report. The test-file change was read back
  from disk after patching and confirmed present at the intended location, immediately after
  `test_existing_home_is_passed_through_to_the_child_and_restored`.
- No scratch directory was created. The only temporary artifacts are the disposable
  `tempfile.mkdtemp` directories that the pre-existing `synthetic_root` fixture already creates
  and removes around each `run_helper` call; the missing `HOME` path is never created.
- Within the driver, the stub recorded exactly one invocation for the new case, and the child's
  captured environment is the evidence for the fallback and restore behaviour.
- The native `file_change` event stream belongs to the parent CLI session; it is observed there,
  not from inside this worker.

## Limitations

- The regression is offline and synthetic. It drives the documented helper body in `pwsh`
  against a local `codex` function stub; the Codex CLI, the Subroute gateway at
  `127.0.0.1:4000`, and the network were not contacted, so this proves the helper's environment
  handling, not live CLI behaviour.
- The `HOME` environment variable is a Unix convention that Windows does not define natively;
  this case covers the helper's handling of a caller-set `HOME`, which is exactly the dispatch
  path this helper implements, but it does not exercise the real Windows sandbox's own
  home-directory enforcement.
- The child-visible `HOME` comparison normalizes case and path separators. The caller's
  restored `HOME` is asserted as the exact original string, with no normalization.
- `tests/test_codex_subagents_helper.py` is untracked pre-existing work. `git diff --check` does
  not cover untracked files, so no whitespace check is claimed for the added case or for this
  report.
- No other test, build, package, cleanup, or network operation was run, and nothing was
  committed or published.

## Handoff

Parent owns independent acceptance. The added case is
`test_invalid_home_falls_back_to_userprofile_and_restores_the_original_path` in
`tests/test_codex_subagents_helper.py`. The helper needed no change: the branch was real, it was
simply uncovered, and the new test pins the documented behaviour. No follow-up work is pending
on this test task; the broader dispatch-context goal remains active.
