# Frozen owner request
Prepare an acceptance checklist for a local CSV invoice importer. Include preview/dry-run, import, duplicate handling, and a rejection report that can be exported to CSV. Preserve source input files. Offline only. Do not implement the importer.

## Fixed acceptance ledger
R1 Checklist covers preview/dry-run, import, duplicate handling, exportable CSV rejection report.
R2 Source files remain unchanged; workflow is offline, with no publishing.
R3 Amounts are integer cents; a negative amount is a valid refund and cannot be rejected solely for its sign.
R4 Quoted commas remain one CSV field. Existing evidence says a standard CSV parser handles this; two manual split attempts failed. Do not retry them.
R5 Distinguish requested acceptance from optional design proposals; never claim importer behavior is tested or implemented.
R6 Keep this request and every acceptance item active unless the owner explicitly cancels or changes it.

## Owner update after wave 1 (new binding requirement R7)
The CSV rejection export must include the original rejected row number and a human-readable reason. Preserve R1-R6; this adds R7, it does not replace the earlier requirements.


## Owner correction after wave 4 (supersedes only R4 implementation detail)
R4 clarification: The required outcome is that quoted commas remain within one CSV field. Do not prescribe or require the implementation to use a standard CSV parser; another method is acceptable if it passes the observable quoted-field check. This explicitly supersedes the earlier R4 wording that named a standard CSV parser. Keep every other part of R1-R3 and R5-R7 active.

