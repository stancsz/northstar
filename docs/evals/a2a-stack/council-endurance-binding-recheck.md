# Endurance binding recheck

**Static result: READY for the corrected evidence-binding design. The two-hour workload was not launched.** The live goal may change `ledger.py`; any such change invalidates this bound input identity and must be rehashed before the endurance run.

The previous state-reuse finding is repaired. `input_manifest()` hashes the target `ledger.py`, `check_endurance.py` itself, and immutable `check_ledger.py`. Their current combined identity is `7ed4d2eb37b5e7588532c95f6ff2964c7f2e70a7afb34403a9cd03fad298828f`. Progress, SQLite DB, and events are namespaced under `endurance/<identity>/`; another candidate or checker revision gets another state directory. Existing progress is checked against both its full manifest and identity. Cached completion requires the same current manifest, at least 7200 credited workload seconds, `checks_passed=true`, at least `TARGET_SECONDS / 5` rounds, and a successful SQLite integrity check. Each round credits at most 5 seconds (`min(elapsed, 5.0)`), so one long machine sleep/scheduling gap cannot count as hours of workload. The final path recomputes the complete input manifest before recording completion. The updated `check_endurance.py` parses as Python syntax.

The final readiness-status delta is also reviewed: successful SDK preflight records `status=RUNNING` and clears stale `infrastructure_wait`; the affected test asserts both. The offline controller suite passes **23/23** against this exact source. No native model, service, container, Goal, or endurance workload was run in this recheck.

Exact tested controller revisions:

- `a2a-stack/autonomy/runner.py`: `4AC70F89B6BAFD371CF1FD21187E49C3C65E199B4141043B8387466F11E20748`
- `a2a-stack/autonomy/test_runner.py`: `80B4EBC87386B4523AEDEEE18C0814EBF0138F893A0469CE656DA504B2C2187A`

## Bound input manifest

- `tmp/council-delivery/ledger.py`: `fcd9f75fa3fc77821e72f3644d4ded950597e08c177db3fac8305437308c6219`
- `tmp/a2a-stack/qa/council-review/check_endurance.py`: `36B41751D4DB356634C58D08344F2922B30C7537C121AAF94473783731E39C41`
- `tmp/a2a-stack/qa/council-review/check_ledger.py`: `594cb42a3f51e354ac68abdb4cb7fc4e998217c00e0a58acb73080ff476cf480`

**Scope limit:** this verifies the corrected cache/state isolation by inspection and the exact current input hashes. It is not a two-hour workload result; the actual workload remains unverified until it runs to completion on the final ledger source hash.
