# Targeted test-migration verification

## Verdict

**READY FOR SOURCE.** The remaining extraction-path gap from `core-focus-review.md` is closed: the captured pre-change excerpt and current test differ in the four described edits, including `SKILL` resolving to `skills/codex-subagents/references/cli-dispatch.md`; the extraction function reads that path; and the focused test suite passed.

## Evidence

- Independent excerpt comparison: module description, prose path, `SKILL` constant, and extraction-function docstring are the only changes in captured lines 1–140.
- `python -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py --basetemp=tmp/core-focus-20261024/test-review/pytest`: **26 passed in 22.10s**, exit code 0.
- SHA256 `tests/test_codex_subagents_helper.py`: `31313AF028D7DF3A7E2105E0F210315F1F70A23C77B03BB87DD5C584E27BD75`.
- SHA256 `skills/codex-subagents/references/cli-dispatch.md`: `0E72F2734C056240E49FBC93255FD9CE9C1A168117A66A2483243B711FDCF4D1`.

## Limits

The captured original test source ends at line 140, so this does not establish byte preservation of its uncaptured tail. The focused tests are offline evidence only; they do not verify provider use or live behavior.
