# HOME as a regular file falls back to USERPROFILE

Goal: [dispatch-context](../../goal/dispatch-context/GOAL.md). Date: 2026-10-23.

## Outcome

One synthetic regression test now covers a caller `HOME` that points at an
existing regular file while `USERPROFILE` points at an existing directory. The
documented helper must fall back to `USERPROFILE`, dispatch the child exactly
once, restore the caller `HOME` exactly, and leave the file untouched.

Production code was not modified.

## Change

- `tests/test_codex_subagents_helper.py`: added
  `test_file_valued_home_falls_back_to_userprofile_and_leaves_the_file_untouched`
  directly after `test_invalid_home_falls_back_to_userprofile_and_restores_the_original_path`,
  inside the existing HOME-fallback group.

The test uses the existing `workspace` fixture and `run_helper` driver. It
writes `caller-home-is-a-file` with sentinel content in the disposable synthetic
root, sets `USERPROFILE` to the fixture's existing `user_profile` directory and
`HOME` to that file, then asserts:

- `payload["error"] is None` and `len(payload["invocations"]) == 1` (stub dispatched exactly once),
- child-visible `HOME` is present and resolves to the fixture `user_profile` directory,
- `before["HOME"]` and `after["HOME"]` are both `{"present": True, "value": str(home_file)}` and equal each other (caller `HOME` restored exactly),
- the path is still a regular file and its content still equals the sentinel.

No scratch files were created; the driver artifacts live in the fixture's
temporary root, which the fixture removes.

## Overlap check

The case was not already covered. Adjacent existing cases in the same file:

- `test_home_fallback_uses_existing_userprofile_and_restores_absent_home` — `HOME` unset.
- `test_home_fallback_restores_an_empty_caller_home` — `HOME` set to the empty string.
- `test_existing_home_is_passed_through_to_the_child_and_restored` — `HOME` is an existing directory.
- `test_invalid_home_falls_back_to_userprofile_and_restores_the_original_path` — `HOME` is a path that does not exist.
- `test_missing_home_and_userprofile_is_rejected_before_dispatch` — both unusable.
- `test_file_valued_userprofile_is_rejected_before_the_codex_stub_runs` — `USERPROFILE` is the regular file; it must reject before dispatch.

The distinguishing condition is a regular file as `HOME` with a valid
`USERPROFILE` directory. The documented helper gates the fallback on
`Test-Path -LiteralPath $priorHome -PathType Container`, so a file-valued
`HOME` is not a usable container and must fall back rather than reject. The
existing USERPROFILE-file test exercises the opposite guard and its
`invalid-path` parameter uses a missing path, not a file.

## Test result

Command run exactly as specified:

```
py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py
```

Result: `18 passed in 9.15s` (17 pre-existing plus the new test). The new test
was also confirmed to pass in isolation via `-k file_valued_home_falls_back`
(1 passed, 17 deselected).

## Limits and scope

- Offline regression only. The helper body is extracted from the PowerShell
  fence in `skills/codex-subagents/SKILL.md` and run under `pwsh` against a
  local `codex` function stub. No Codex CLI, Subroute gateway, or network
  service is contacted, and no real user profile is read or written.
- The assertions pin the observable contract (dispatch count, child `HOME`,
  caller `HOME` restoration, sentinel integrity) and not the helper's internal
  branch structure.
- The test file is currently untracked in this worktree and other unrelated
  modifications were already present; none were touched.
- Structured `file_change` events were confined to `tests/test_codex_subagents_helper.py` and this report. The worker nevertheless exceeded the stated read bounds: it ran an unscoped `git status --short`, searched the target file for test definitions, and read adjacent test ranges 387-420 and 456-500. These reads made no changes but are a dispatch-scope deviation.
- The corrected worker completed in about 179 seconds with 15 native command calls, four `file_change` lifecycle events, `turn.completed`, and exit 0. Usage: 380,106 input tokens (346,881 cached), 8,447 output and 4,472 reasoning; cost unknown. Receipt: `tmp/dispatch-context/home-file-fallback-corrected-worker-20261023/worker.jsonl`.
- No packaging, cleanup, commit, or push was performed.

## Unresolved

None for the assigned case. Parent owns `GOAL.md`, indexes, and acceptance.
