# Independent review: Codex skill-discovery gate switch

Goal: [dispatch-context](../../goal/dispatch-context/GOAL.md). Reviewer: independent nonauthor (Codex CLI, read-only). Date: 2026-10-23. Reviewed artifact: [codex-skill-discovery-gate-20261023.md](codex-skill-discovery-gate-20261023.md).

## Verdict

**ACCEPT WITH LIMITS.** The increment is a correct, opt-in, process-only source/test change and the recorded claims are hedged in proportion to the evidence. It does not, and does not claim to, establish context reduction, reliability or economy from the experimental CLI feature. Two concrete corrections are required before this increment is treated as a finished source change, and the evidence limits below must travel with any later claim built on it.

## Scope actually inspected

- `AGENTS.md` lines 1-33 (Working on Northstar; Review and Git).
- `skills/codex-subagents/SKILL.md` lines 142-218.
- `tests/test_codex_subagents_helper.py` lines 25-46, 149-225, 383-480.
- `docs/reports/dispatch-context/codex-skill-discovery-gate-20261023.md` lines 1-45.
- `docs/reports/dispatch-context/cli-trials.md` lines 676-690.
- `docs/goal/dispatch-context/GOAL.md` lines 516-520.

No tests were run by this review; the parent reports `22 passed in 13.26 seconds, exit 0` for the focused suite. No repository search, no network, no credential access, and no implementation, test, goal, index or evaluation file was modified.

## 1. Opt-in gate and unchanged default vector

Supported by the source.

- `skills/codex-subagents/SKILL.md:149` declares `[switch] $SkipHostSkillDiscovery` as an optional parameter.
- `skills/codex-subagents/SKILL.md:191-193` appends `@('--enable', 'skip_host_skill_discovery')` only inside `if ($SkipHostSkillDiscovery)`. There is no other code path that contributes the feature or the `--enable` token, so the default path is structurally incapable of emitting them.
- `skills/codex-subagents/SKILL.md:174-178` holds the unchanged base vector; `:179-187` and `:188-190` are the two pre-existing independent opt-ins; `:194` runs `& codex @codexArguments '-'`, so the appended pair lands immediately before the stdin marker `-`, matching the documented order.
- `skills/codex-subagents/SKILL.md:216` states the switch is experimental, per-assignment, never default-on, process-only, independent of `-UseObservedSubrouteSettings` and `-DisablePlugins`, and that combining them keeps every contributed argument exactly once. The description matches the code read above.
- `tests/test_codex_subagents_helper.py:383-395` asserts the fully default invocation equals the fixture in `:159-178`, with `arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 0` and `arguments.count(SKILL_DISCOVERY_FEATURE) == 0`, and exactly one `-c`.

No gap found in this criterion.

## 2. Test coverage

Supported, with the coverage limits recorded below.

- Default preservation: `tests/test_codex_subagents_helper.py:383-395`, against the byte-for-byte fixture built at `:159-178`.
- Exact flag order once: `:398-415` — `--enable` count `== 1` (`:408`), `skip_host_skill_discovery` count `== 1` (`:409`), adjacency `arguments[index:index+2] == list(SKILL_DISCOVERY_ARGUMENTS)` (`:410-411`), stdin marker still final (`:412`), and whole-vector equality (`:413-415`). The driver passes `-SkipHostSkillDiscovery` through at `:210-211`.
- Independent combinations: `:418-480` — observed + feature (6 `-c`, `:429-438`), plugin + feature (2 `-c`, no observed override leakage, `:450-460`), and all three switches (7 `-c`, each override exactly once, `:473-480`). The `-c` arithmetic is consistent with `SKILL.md:177` (1 base) + `:181-185` (5 observed) + `:189` (1 plugin), and the feature pair is not a `-c`, so it cannot perturb those counts.

Recorded limits:

- **Environment-conditional coverage.** `tests/test_codex_subagents_helper.py:44-46` skips the whole module when `pwsh` is absent. On such a machine the three new tests skip silently instead of failing, so the coverage holds only where PowerShell 7 is present. The parent's `22 passed` run is therefore environment-dependent evidence.
- **Truncated visible assertion.** The assigned range ends at line 480, mid-call, in the all-three-switches case: the closing of `normalize(combined_arguments) == expected_arguments(...)` and any assertion after it lie outside the assigned range. The count and per-override assertions at `:473-477` are fully visible and pass on their own; the final equality for that case was not fully verified by this review.
- **No visible negative case for partial combinations.** Within the assigned ranges, absence of the feature is asserted only for the fully default invocation. No test asserts the absence of `--enable` / `skip_host_skill_discovery` when `-UseObservedSubrouteSettings` or `-DisablePlugins` is used alone. The independence requirement as written (combination behaviour) is met; this is a coverage nicety, not a stated requirement.
- **Unverifiable claim.** The gate report's statement at `docs/reports/dispatch-context/codex-skill-discovery-gate-20261023.md:21` that the helper-extraction guard now also requires `--enable` and `skip_host_skill_discovery` is outside the assigned ranges: `extract_helper_function` is only referenced at `tests/test_codex_subagents_helper.py:219`, and its body was not read. This review does not confirm or deny it.

## 3. Documentation: experimental warning and observed budget warning vs proven behaviour

The durable records separate the two correctly. The operator-facing skill file has one accuracy gap.

Correctly distinguished:

- `docs/reports/dispatch-context/codex-skill-discovery-gate-20261023.md:9` marks the switch experimental (under-development, per-assignment, may change or disappear, never written to global or user configuration, process-only).
- `:27` states the increment did not re-run the CLI, did not measure context savings, does not establish repeated reliability, and that the earlier probe's token difference was a single synthetic comparison on a different prompt and remains not a savings claim.
- `:31` records that the real write worker completed but startup still showed the under-development-feature warning and the skill-context budget warning, and that the single run does not isolate the feature's effect or prove context reduction.
- `:39` (parent acceptance) explicitly declines to claim context reduction or causal tool success and keeps adherence and economy open.
- `docs/reports/dispatch-context/cli-trials.md:682` records that the run does not demonstrate token savings or reliable scope adherence, does not show the flag caused the successful write, and that cost and backend model are not established by the receipt.
- `docs/goal/dispatch-context/GOAL.md:520` calls it one completed write handoff, not evidence of reliable context reduction or economical delegation, with the feature effect unproven.

Gap:

- `skills/codex-subagents/SKILL.md:216` states the removal effect as unconditional fact ("Enabling it removes the host-discovered skill descriptions and their context from the child") and does not mention that in the one recorded real run the skill-context budget warning still appeared (`codex-skill-discovery-gate-20261023.md:31`, `cli-trials.md:682`, `GOAL.md:520`). An operator reading only the skill file could infer that the switch clears skill-context pressure; the recorded evidence does not show that, and no cause for the persisting warning is identified. This is the required documentation correction below.
- `skills/codex-subagents/SKILL.md:216` also asserts that the Codex CLI lists `skip_host_skill_discovery` as under development. Within the assigned scope that is parent-attested (`codex-skill-discovery-gate-20261023.md:27`, `cli-trials.md:678`) and was not independently verified by this review.

## 4. What the real worker run does and does not support

- **Live success — supported only in the narrow sense of one completed handoff.** `cli-trials.md:680` records structured write events confined to the helper skill, its test file and the report; `GOAL.md:518` records exit 0 with a handoff; `codex-skill-discovery-gate-20261023.md:33` records that nothing else changed. What is **not** supported is that the feature caused that success — `cli-trials.md:682` and `:39` of the gate report say so explicitly, and this review concurs.
- **Context reduction — not supported.** The receipt shows 1,014,339 input tokens (964,608 cached), 16,173 output and 9,082 reasoning tokens (`cli-trials.md:682`, `GOAL.md:520`), the skill-context budget warning persisted (`codex-skill-discovery-gate-20261023.md:31`), there is no baseline comparison in scope, and the earlier probe delta is explicitly not a savings claim (`:27`). No token-saving or context-reduction statement is warranted from this evidence base.
- **Reliability — not supported.** One run only; `codex-skill-discovery-gate-20261023.md:27` states the increment does not establish repeated reliability, and `cli-trials.md:682` records a single comparison. The gate must remain per-assignment and opt-in; it must not be described as reliable or stable.
- **Economy — not supported, and the available signal is adverse.** The child first ran a broad `git status` and read substantially beyond the assigned ranges, including the full test file (`cli-trials.md:682`, `codex-skill-discovery-gate-20261023.md:31`, `GOAL.md:520`). Cost and backend model are not established by the receipt (`cli-trials.md:682`). A single high-input run with over-reading cannot support an economy claim for this dispatch pattern.
- **Attribution — unresolved, and the records disagree slightly.** `GOAL.md:518` attributes the process-only `--enable skip_host_skill_discovery` flag to that dispatch, while the dispatch enumeration at `cli-trials.md:678` lists the helper, the loopback `/v1` route, inherited `GATEWAY_MASTER_KEY`, `workspace-write`, the observed overrides and disabled plugins, but not the flag. Since the helper's own `-SkipHostSkillDiscovery` switch was added by this very increment (`SKILL.md:191-193`), the assigned ranges contain no description of how the flag reached that run's child. This is unverifiable here and should be stated explicitly rather than left to inference.

## Required corrections

1. `skills/codex-subagents/SKILL.md:216` — qualify the removal claim and record the observed warning. Add that in the one recorded real run the CLI still emitted the skill-context budget warning, that no cause for it was identified, and that the switch must therefore not be treated as a proven context-budget fix or as a token-saving measure. Keep the experimental, opt-in, never-default-on, process-only wording as is.
2. `docs/reports/dispatch-context/cli-trials.md:678` — align the dispatch enumeration with `docs/goal/dispatch-context/GOAL.md:518` by stating whether the evidence run's child received `--enable skip_host_skill_discovery` and by what mechanism, given that the helper switch postdates the launch. Do not add a savings, reliability or economy claim in doing so.

Both are documentation-accuracy fixes inside the increment's existing files. Neither expands scope.

## Recorded limitations of this review

- Read-only, within the assigned ranges; no tests re-run, no CLI or gateway contacted, no credential read or written.
- The three new tests are exercised only against the local PowerShell `codex` stub (`codex-skill-discovery-gate-20261023.md:15`); they prove the argument vector, not CLI acceptance of `--enable skip_host_skill_discovery` at runtime. Runtime acceptance rests on the parent's earlier native command-tool smoke (`codex-skill-discovery-gate-20261023.md:27`, `cli-trials.md:678`), which this review did not reproduce.
- The helper-extraction guard claim (gate report `:21`) and the all-three-switches final equality assertion were outside the assigned ranges and remain unverified here.
- `AGENTS.md:30` asks for `git diff --check` and local link checks on documentation changes. Link targets named by the gate report resolve (skills file, test file, goal file, trial file); the review path it anticipates at `codex-skill-discovery-gate-20261023.md:35` did not exist before this report was written and resolves now. `git diff --check` was run by the parent (`codex-skill-discovery-gate-20261023.md:23`, `:39`); this review did not re-run it and did not inspect a diff.

## Primary disposition

The two documentation corrections were implemented in the helper skill and trial log. The skill now describes the experimental flag as requesting host-skill removal and explicitly says the behavior, total-context reduction and token savings are unproven; it records that the skill-context warning persisted. The trial entry now names `-SkipHostSkillDiscovery` and the exact `--enable skip_host_skill_discovery` arguments. The parent reran the focused helper suite after the wording repair; results and remaining scope limits are in the current Goal checkpoint.

## Handoff

Accept the increment as a scoped, opt-in source/test change with the experimental boundary intact. Do not carry forward any claim of context reduction, reliability or economy from this evidence base, and do not default the switch on. This review covers the skill-discovery gate increment only; it makes no statement about the wider dispatch-context goal, which `cli-trials.md:682` records as still Active.
