# File-valued USERPROFILE helper regression

Goal: [dispatch context](../../goal/dispatch-context/GOAL.md). This task tests the documented Windows Codex helper with a synthetic local stub; it does not use the gateway or credentials.

## Outcome

Added two parametrized cases proving that a regular-file `USERPROFILE` is rejected before Codex dispatch when `HOME` is absent or points to a missing directory. The tests confirm zero stub invocations, unchanged sentinel-file content, and exact restoration of both caller environment values. No production/helper code changed.

## Changed paths

- `tests/test_codex_subagents_helper.py` - two cases in `test_file_valued_userprofile_is_rejected_before_the_codex_stub_runs`.
- `docs/reports/dispatch-context/userprofile-file-home-guard-20261023.md` - this handoff.

The test file was already untracked before this task and remains untracked. Structured worker events changed only these two assigned paths.

## Verification

- Baseline before dispatch: `py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py` — 15 passed.
- Worker: same command — 17 passed; both new cases also passed in isolation.
- Parent independently reran the focused suite — 17 passed in 9.02s.
- Parent checked the added test and this report for trailing whitespace; none found. No build, package, cleanup, commit or push.

## Dispatch evidence and limits

The parent rendered the updated orchestrator brief and dispatched through the documented helper on Subroute `default`/Responses. The worker exited 0 with `turn.completed`, 13 native command calls, and four `file_change` lifecycle events confined to the test and report. Elapsed time was 203.8s. Usage was 618,703 input (578,733 cached), 10,954 output and 4,959 reasoning tokens; cost unknown. Receipt: `tmp/dispatch-context/userprofile-file-home-guard-20261023/worker.jsonl`.

The brief named the relevant helper and rejection-test line ranges, but omitted the shared harness range and did not explicitly forbid an unscoped `rg -l` search or reading the whole target test file. The worker read the test file in broad chunks and searched the repository for helper references. It made no out-of-scope writes; this is a prompt-specificity and context-efficiency gap, not evidence of a write-scope violation. For the next dispatch, include the precise harness range and explicitly exclude repository-wide text searches when unnecessary.

This is one successful synthetic test handoff, not proof of live CLI reliability or economical delegation. The dispatch-context goal remains Active.
