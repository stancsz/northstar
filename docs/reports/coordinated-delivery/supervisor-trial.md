# Supervisor execution trial

Goal: [coordinated delivery](../../goal/coordinated-delivery/GOAL.md). Author: supervisor trial agent. Date: 2026-09-29. Status: local task repaired and supervisor-accepted; primary agent's independent acceptance pending.

## Scope and decisions

Used the current Northstar/Codex Subagents supervisor brief in a real local fixture at `tmp/coordinated-delivery/supervisor/`. Base revision: `5f0f860ec40541e3f6c5b5c1e95484719ed89b07`, with pre-existing dirty documentation left intact. Environment: Windows PowerShell, Python 3.14.0. No subagents, dependencies, network, installation, commit, publishing, or upload.

Fixture GOAL.md already authorized local edits and execution until the calculation worked. Its AGENTS.md confirmed the prior worker had stopped. I therefore took over the repair without requesting repeated approval. Optional upload lacked a destination and authorization; it did not block the independently useful local result.

The inherited worker report claimed all checks passed. Actual inspection found premature per-price rounding. I rejected that completion claim and removed only the inner `quantize` call in `invoice.py`, leaving `Decimal(row['price']) * row['quantity']` inside the sum and one final `quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)`. Updated fixture GOAL.md with the repair and task acceptance. Preserved `check.py`, `user-note.md`, and `worker-report.md` unchanged.

## Executed evidence

Commands ran from the fixture directory unless stated otherwise.

- Before repair, `python -B check.py` exited 1 with `AssertionError` at line 3, the required `2 × 1.005 → 2.01` case. Source inspection explains the failure: rounding 1.005 first produces 1.01, then multiplying produces 2.02.
- After repair, the same `python -B check.py` exited 0 and printed `3 acceptance cases passed`: the multiplication case, empty list returning `0.00`, and mixed rows returning `5.30`.
- `python -B -c` with the exact cases below exited 0, printed the four actual/expected pairs, and `4 targeted cases passed`. This checks aggregation across rows, HALF_UP ties, zero quantity, and string return type.

```python
from invoice import total
cases = [
    ([{'price': '0.005', 'quantity': 1}, {'price': '0.005', 'quantity': 1}], '0.01'),
    ([{'price': '1.005', 'quantity': 1}], '1.01'),
    ([{'price': '-1.005', 'quantity': 1}], '-1.01'),
    ([{'price': '12.345', 'quantity': 0}], '0.00'),
]
results = [(total(rows), expected) for rows, expected in cases]
print(results)
assert all(actual == expected and isinstance(actual, str) for actual, expected in results)
print('4 targeted cases passed')
```

Repository review: `git diff --check` found no whitespace errors (existing LF/CRLF conversion warnings only). Inspected the new report with `git diff --no-index -- /dev/null docs/reports/coordinated-delivery/supervisor-trial.md`, the repaired source, and `git status --short`. Both added relative Markdown links resolved with `Test-Path`. Before/after `Get-FileHash` confirmed identical SHA256 values for the three preserved files:

- `check.py`: `859CF6A7BDB70F57929B8D39D7BB9212D31D0FA1863E74FF3F982FEA888B69C9`
- `user-note.md`: `D154121683DBF065597920D3C280E47D288B3A8C6DCC01A6C17169638864D88E`
- `worker-report.md`: `D6EBCF4F9A747191AD3DDB574E0D289126D383529FC2FDDA845314A9A039E4EC`

## Handoff and limits

The supervisor both repaired and verified this small fixture; the primary agent must independently inspect it and decide final acceptance. This demonstrates one bounded continuation carrying authorization, detecting false completion, preserving the stopped worker's artifacts, and delivering the requested local calculation. It does not establish long-session reliability, enforced timeout behavior, concurrent-worker behavior, production invoice coverage, or any upload capability. Invalid input policy and arbitrary-precision limits were not part of the supplied acceptance criteria.

Artifact paths are scratch references, not durable evidence links; the failure, source change, checks, and observations needed for review are preserved above. Next action: primary agent reruns the unchanged check, inspects the source/goal, and records its goal decision.
