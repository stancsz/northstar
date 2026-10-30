# Codex skill-discovery gate switch

Goal: [dispatch-context](../../goal/dispatch-context/GOAL.md). Author: bounded Codex CLI-delegation increment, 2026-10-23. Status: source change implemented and verified with offline tests; the tests used a local stub only. The parent separately used Subroute to dispatch the worker.

## Behavior

[`Invoke-CodexChild`](../../../skills/subagent-orchestration/SKILL.md) now accepts an optional `[switch] $SkipHostSkillDiscovery`. When present, the helper appends exactly `--enable skip_host_skill_discovery` to that one child invocation, immediately before the stdin marker `-`. When absent, the default child arguments are unchanged and the flag is never default-on.

The switch is documented as experimental: the Codex CLI lists `skip_host_skill_discovery` under development, so it is enabled per assignment, may change or disappear in a later CLI release, and is never written into global or user Codex configuration. It is process-only. Enabling it removes the host-discovered skill descriptions and their context from the child, so the caller must carry the necessary skill instructions in the assignment instead of relying on host skill discovery.

The switch is independent of `-UseObservedSubrouteSettings` and `-DisablePlugins`: with any combination, every contributed argument still appears exactly once, and the observed settings and the plugin override keep their previous counts.

## Test coverage

Extended [`tests/test_codex_subagents_helper.py`](../../../tests/test_codex_subagents_helper.py) against its local PowerShell `codex` stub only. No Codex CLI, Subroute gateway, network service or credential was contacted.

- `test_default_invocation_keeps_the_documented_arguments_unchanged` — the default invocation still equals the byte-for-byte argument fixture, with no `--enable` and no `skip_host_skill_discovery` present.
- `test_skip_host_skill_discovery_adds_the_enable_flag_exactly_once` — the pair `--enable`, `skip_host_skill_discovery` appears exactly once, adjacent, and before the final `-`.
- `test_skip_host_skill_discovery_stays_independent_of_observed_and_plugin_switches` — combined with the observed settings (6 `-c` arguments), with `-DisablePlugins` (2 `-c`), and with all three switches (7 `-c`), each contributed argument appears exactly once.

The helper-extraction guard in `extract_helper_function` now also requires `--enable` and `skip_host_skill_discovery` to be present in the extracted function body, so the documented helper and its fence stay in sync.

Checks run: `py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py` — 22 passed (19 baseline + 3 new) in 12.25 s, exit 0. `git diff --check` on `skills/codex-subagents/SKILL.md` reported no whitespace errors.

## Feature maturity caveat

`skip_host_skill_discovery` is an under-development Codex CLI feature, and the parent had already verified the CLI feature listing plus a native command-tool smoke on the authorized Subroute route with this process-only flag before this increment. This increment adds only the documented opt-in switch and its offline argument coverage: it did not re-run the CLI, did not measure context savings, and does not establish repeated reliability. The earlier probe's token differences were a single synthetic comparison on a different prompt and remain not a savings claim.

## Gaps and handoff

- The parent subsequently dispatched the real write worker through this switch; it completed, but startup still showed the under-development-feature warning and skill-context-budget warning. This single run does not isolate the feature's effect or prove context reduction.
- Because the flag removes host-discovered skill context, an assignment that uses it must inline the skill instructions the worker needs; a parent that sends a skill-dependent brief without that content will get a less capable child.
- Nothing outside the two source files and this report was changed: no `GOAL.md`, index, evaluation, global or user Codex setting, gateway target or credential file was touched. The pre-existing unrelated modifications and untracked files in the worktree were preserved.

Next action (parent): obtain the independent nonauthor review in `docs/reports/dispatch-context/codex-skill-discovery-review-20261023.md`; retain the experimental, opt-in boundary unless stronger current CLI evidence justifies a correction.

## Parent acceptance

Accepted as a scoped source/test increment after independent review. The documented default argument vector is unchanged; the opt-in contributes exactly the adjacent `--enable`, `skip_host_skill_discovery` pair before the final stdin marker, including when combined with the observed Subroute and plugin switches. The parent reran `py -3 -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py` and confirmed 22 passed in 13.26 seconds, exit 0. All three report links resolve; `git diff --check` on the skill file reports no whitespace errors. The write worker's real run did include the opt-in flag and completed, but emitted both the under-development-feature warning and the skill-context budget warning, so no claim is made that the feature reduced context or caused tool success. Worker usage was 1,014,339 input (964,608 cached), 16,173 output and 9,082 reasoning tokens; its broad reads and high input keep adherence and economy open.

## Repair note: qualified skill-discovery caveat

The independent nonauthor review (`codex-skill-discovery-review-20261023.md`) required the `-SkipHostSkillDiscovery` paragraph in [`skills/codex-subagents/SKILL.md`](../../../skills/subagent-orchestration/SKILL.md) to stop asserting the flag as a guarantee. That sentence now states that enabling the flag requests that the host-discovered skill descriptions and their context are removed from the child, notes that the feature is under development and that this behavior is not guaranteed, records that no total-context or token reduction is proven and that the recorded write worker still emitted the skill-context-budget warning, and tells callers to inline the skill instructions the worker needs and not to rely on the flag as a context-budget or token-saving fix.

The experimental boundary is unchanged: default-off, process-only, enabled per assignment, never written to global or user Codex configuration, and still independent of `-UseObservedSubrouteSettings` and `-DisablePlugins`.

Verification was documentation-only: the scoped diff was inspected and `git diff --check` reported no whitespace errors. No test, helper, goal, index, evaluation or review file was changed; no Codex CLI or gateway run was repeated; no credential was read; and the earlier single synthetic token comparison remains not a savings claim. Runtime behavior of `skip_host_skill_discovery` is still unverified beyond the recorded run.
