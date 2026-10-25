# Core CLI context relocation

## Result

Moved the Windows/local Codex CLI profile setup, invocation and capture guidance, observed-dispatch notes, `Invoke-CodexChild` helper, and host-discovery notes out of the startup section into [`cli-dispatch.md`](../../../skills/codex-subagents/references/cli-dispatch.md). The main skill retains generic capability/routing policy and links the reference for CLI dispatch. It also links the Northstar [delivery contract](../../../skills/northstar/SKILL.md#delivery-contract), assigns approval ownership to one commander, and permits worker-local decisions within the authorized brief without another approval round trip. Removed the roughly-20-agents scale suggestion.

## Verification

- Baseline: `python -B -m pytest -q -p no:cacheprovider tests/test_codex_subagents_helper.py --basetemp=tmp/core-focus-20261024/worker/pytest` — 26 passed.
- After relocation: same command — 26 passed.
- Extracted helper equality: baseline and reference SHA-256 both `D2ECB7167720D39394BE0D72D75B42C34EEAE3CBB98F3BB99B2817BC95D55C35`.
- `git diff --check` on the assigned paths — passed.
- Existing section anchors remain in `SKILL.md`; CLI reference links to `../SKILL.md` from its new location.

## Limits and remaining review

No live provider/CLI smoke was repeated; the commander supplied existing route evidence, and this change does not alter dispatch behavior. Independent acceptance remains with the parent. The delivery-contract target is parent-owned and was not independently verified as present during this task. No other known implementation issue remains.

## Changed paths

- `skills/codex-subagents/SKILL.md`
- `skills/codex-subagents/references/cli-dispatch.md`
- `tests/test_codex_subagents_helper.py`
- `docs/reports/delivery-focus/core-cli-relocation.md`

Parent integration note: corrected the report link, moved comparison/capacity details to the same reference, and aligned remaining ceremony wording with the shared contract after the worker exited. The helper body is unchanged; combined source acceptance is assigned to a separate reviewer.
