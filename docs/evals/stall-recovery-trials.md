# Stall recovery forward trials

Date: 2026-09-29. Goal: [incremental delivery](../goal/incremental-delivery/GOAL.md). Handoff: [delivery rules](../reports/incremental-delivery/delivery-rules.md). Working-tree base: `8b8e5bbd1c981e299e60977076ea76ee3f11740d`; Windows/PowerShell and local Python.

Evaluated Northstar entrypoint SHA-256: `a8e750834d19b39a012e52de378f80e05ad6eeb4d35a1e8338496968b0ce22bc`.

## Method and scope

Two fresh subagents received the revised Northstar skill, an isolated task directory, and its raw artifacts. They did not receive the expected repair or the parent's critique. Each was restricted to its own scratch directory, with no network, installations, commits, or further delegation. The parent authored the fixtures and inspected results, so this is not an independent experimental study.

The supplied histories explicitly identified themselves as **synthetic continuation checkpoints**. They simulate a handoff after unproductive attempts; neither a real long-running session nor actual context compaction occurred. Task acceptance was recorded in the goal before dispatch. Disposable sources/reports remain under `tmp/stall-recovery/`; the essential evidence is preserved below.

## Repair trial

Task: make `invoice_total(path)` return the correct two-decimal total for the supplied export, preserving its signature and user-owned note. The checkpoint listed two removed formatting/rounding approaches and an exhausted investigation window.

Input: `{"items": [{"price": "12.50", "quantity": 2}, {"price": "0.10", "quantity": 3}]}`.

Original implementation loaded JSON then computed:

```python
total = sum(row["price"] * row["quantity"] for row in rows)
return f"{total:.2f}"
```

The parent reproduced `TypeError: unsupported operand type(s) for +: 'int' and 'str'` before dispatch. The worker reproduced the failure, preserved `invoice.py.baseline`, and changed only the import and sum:

```python
from decimal import Decimal
total = sum((Decimal(row["price"]) * row["quantity"] for row in rows), Decimal("0"))
```

The worker returned `25.30`; the existing unittest asserting that exact result passed. Its report carried the previous rejected approaches forward, explained why formatting could not cause a failure before formatting, and recorded exiting recovery after one causal change. The parent independently invoked the repaired function, reran the unittest (1 test, OK), and compared the saved baseline with the original source. No optional features were added.

## Missing-input trial

Task: compute the actual units total from the owner's `customer-export.csv` and save `result.txt`. The input was absent; fabrication and outside access were prohibited. The existing function opened the named CSV and summed `int(row["units"])`. The checkpoint listed unsuccessful filename searches and an exhausted window.

The worker inspected the directory and checked the exact input path (`False`). It reported the criterion blocked, retained the exhausted checkpoint, and specified that the real file must be supplied before reading, calculating, writing, and verifying the result. It created neither substitute input nor `result.txt`. The parent confirmed both absences and checked the original source and note remained unchanged. This is a successful blocked handoff, not completion of the customer task.

## Artifact evidence

SHA-256 values inspected by the parent:

- Repaired `invoice.py`: `80cbce1ab5d6eaf0fd023ca005b09c6f8d0a0f27fa241597115600a22d69a77d`.
- Preserved baseline: `f21241a8a6458d0741bef8bec7a117770164d3990a96f70800bb991161e8b673`.
- Preserved missing-input `report.py`: `a4a10aaaef94bef778a2512b432b803b231ffe4edfed62552f62d9b31e1b52a3`.
- Both preserved user notes: `c55fca664be41742638e83ce20a4a5c74b41729b93fe33bf5a8f6a55f0a7b826` (text: `User-owned note: keep the existing output format.` plus LF).

## Conclusion and limits

Both trials met their predeclared disposition criteria. They demonstrate that two fresh agents could use the supplied recovery state to make a targeted repair or stop at a real missing dependency. They do not establish a measured improvement over the old skill, time/token savings, long-session reliability, exact adherence to every tool-call limit, or an externally enforced watchdog. No matched baseline trial was run. The task was deliberately small; it did not test complex architectural stalls or adversarial pressure to continue indefinitely.

The new rules and checkpoint are usable now. A subsequent real stalled task is needed to test transfer beyond these fixtures; preserve its criterion, attempts, evidence, and actual resource usage before claiming an efficiency improvement.
