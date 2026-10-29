# Codex HOME preflight guard — CLI implementation

Status: parent accepted as a bounded source/test increment.

Task: reject a nonempty `CODEX_HOME` unless it resolves to an existing directory, before stop-hook adapter probing, environment mutation, or Codex invocation. Add focused regressions for file-valued and missing-directory paths while preserving unset/empty fallback and valid-directory behavior.

Implementation: `skills/codex-subagents/SKILL.md` validates and resolves nonempty `CODEX_HOME`; `tests/test_codex_subagents_helper.py` adds synthetic file-valued and missing-directory cases. Both assert a clear rejection, zero Codex stub invocations, and unchanged caller environment.

Verification: `py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py` passed (26 tests, 16.51 seconds). Running the new parametrized test against the frozen pre-change helper failed in both cases as expected, demonstrating that the regression distinguishes the old behavior. The parent reviewed the exact diff against the frozen baseline and the existing valid/unset/empty cases. The Codex CLI handoff completed with `turn.completed`, exit 0, native command and file-change events confined to the three assigned write paths. Usage: 197,032 input (15,488 cached), 5,865 output, 852 reasoning tokens; cost and selected backend are unknown.

The earlier Claude CLI attempt for the same bounded task did not produce a stdout stream or source edits within the 15-minute cap. Its stderr retained an `unrecognized_model` diagnostic for alias `default`; the parent stopped that exact process without retrying or changing routes. No Claude implementation is claimed. Detailed receipts are under `tmp/dispatch-context/codexhome-failfast-20261023/`.
