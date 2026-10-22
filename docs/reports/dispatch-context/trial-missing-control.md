# Dispatch context trial — missing input (control)

## Files inspected
- `tmp/dispatch-context-trials-2026-10-22/pair-missing-input/control/README.md`
- `tmp/dispatch-context-trials-2026-10-22/pair-missing-input/control/june-shipments.csv`
- Directory listing of the assigned control folder (confirmed no July CSV was present).

## Assumptions and clarifications
The fixture README states that `july-shipments.csv` is absent and says not to estimate or reuse June totals as July values. Followed that instruction; no July figures are inferred.

## Produced
Created `tmp/dispatch-context-trials-2026-10-22/pair-missing-input/control/july-summary.md` with a blocker, June context labeled as June, and a request for the missing source.

## Exact values or blocker
July shipment count and total units: unavailable because the July source file is absent. June example: 2 shipments, 12 units (not a July estimate).

## Checks performed
Inspected the assigned directory and read both supplied files. Confirmed the output file was written and measured its character length. Source files were not edited. No other checks performed.

## Output length
`july-summary.md`: 425 characters.