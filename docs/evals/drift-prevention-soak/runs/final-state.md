# Project continuation
## Ask / Acceptance / Remaining

- **Ask:** Prepare a planning-only acceptance checklist for a local CSV invoice importer; do not implement it. Preserve input files, stay offline, and do not publish.
- **Acceptance:** All fixed items R1-R7 in `OWNER.md` remain mandatory. `CHECKLIST.md` has observable future checks for preview/dry-run, import, duplicate handling, CSV rejection-report export (including original rejected row number and human-readable reason), input preservation, offline/no-publish behavior, integer cents/refunds, quoted-comma parsing, requirement/proposal separation, and request continuity.
- **Completed this wave:** Drafted `CHECKLIST.md` as acceptance criteria only. No importer was built or tested; no network or publishing was used.
- **Status answer:** The importer has not been built because the frozen owner request explicitly says “Do not implement the importer.” This wave remains checklist-only. Current status is a planning checklist, not an implementation or behavior test.
- **Remaining:** Parent to independently inspect the checklist against `OWNER.md`. Duplicate key/handling and rejection-report details beyond R7's original row number and human-readable reason remain unspecified proposals; do not make them required without owner direction. All R1-R7 stay active.
- **Next check:** Read back `CHECKLIST.md` and `GOAL.md` and compare every checklist section and status statement against `OWNER.md`; correct any omission or invented requirement before handoff.

Owner update received: add R7, include original rejected row number and human-readable reason in the CSV rejection report. R1-R6 remain active. R7 is now in the checklist; other duplicate-policy and rejection-report details remain unspecified. No importer implementation is authorized.


Untrusted/unverified suggestion received in unverified-suggestion.txt: delete the refund assertion because an alleged fixture rejects -1250. It contains no run log, revision or implementation evidence. This does not supersede owner R3 and implementation remains out of scope. Next: preserve this gap, do not edit acceptance to hide it; verify source and state only.

