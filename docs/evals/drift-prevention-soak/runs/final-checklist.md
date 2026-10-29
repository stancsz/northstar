# Local CSV invoice importer acceptance checklist

Planning artifact only. These are proposed observable acceptance checks for a future importer; no importer exists and no importer behavior has been tested or implemented. Keep all checks local and offline. Never publish or transmit input or output.

## R1 — Requested workflow coverage

- [ ] Preview/dry-run: Given a selected input CSV, inspect the preview and confirm it shows the records and interpreted invoice values that a subsequent import would use, without committing/importing records. Confirm source-file bytes remain unchanged.
- [ ] Import: In a separate acceptance run using a test copy, perform the import and inspect the resulting records against the accepted preview. Confirm the selected source file remains byte-for-byte unchanged.
- [ ] Duplicate handling: Confirm the checklist/specification records an explicit duplicate key and handling rule before behavior is accepted; exercise duplicate and nonduplicate cases against that owner-approved rule and compare outcomes. **Unresolved proposal:** duplicate key and exact handling policy are unspecified; do not assume or require a particular one.
- [ ] Rejection report: Provide at least one rejected-row fixture and confirm the workflow produces a report identifying rejected input rows and can export that report as a readable CSV file. **Binding R7:** the exported CSV must include the original rejected row number and a human-readable reason. **Unresolved proposal:** all other report columns, error-detail format, and rejection-schema details are unspecified; agree them before treating those details as required.

## R2 — Preserve inputs; offline, no publishing

- [ ] Preserve each selected source input file unchanged through preview and import; the source file remains present and its contents are not modified. **Suggested verification method (optional, not an owner requirement):** compare a cryptographic hash recorded before and after the workflow.
- [ ] Run the complete workflow offline; preview, import, and rejection-report CSV export complete using only local resources, with no network-dependent service required.
- [ ] Inspect the workflow and its outputs for publishing/transmission actions; confirm none occur and no input or report is sent to an external destination.

## R3 — Integer-cent amounts and refunds

- [ ] Use fixtures whose expected amounts are specified in integer cents; inspect preview and imported values and confirm they are represented/compared as integer cents, without floating-point rounding changing the cents value.
- [ ] Include a negative integer-cent amount representing a refund. Confirm it is not rejected solely because it is negative and is previewed/imported according to the same applicable amount rules as other valid records.

## R4 — Quoted commas remain one field

- [ ] Include a valid CSV row with a quoted field containing a comma. Confirm preview and subsequent import each retain that comma within one field and preserve the expected field boundaries. This observable field-boundary outcome is binding; implementation method is not prescribed.
- **Superseded method prescription:** the earlier R4 wording named/recommended a standard CSV parser and said not to retry manual delimiter splitting. The owner correction explicitly removes that method requirement; any method is acceptable if it passes the quoted-field boundary check. The two failed manual attempts remain historical evidence, not an acceptance rule.

## R5 — Separate requirements from proposals; no implementation claims

- [ ] Review this checklist against `OWNER.md`: mark only its R1–R7 items as requested acceptance; label design choices not specified there as proposals/unresolved, not requirements.
- [ ] Before implementation exists, report only checklist/document review evidence. Do not claim importer behavior has been tested, accepted, or implemented; future behavior checks remain unchecked until run against an implementation.

## R6 — Preserve the full active request

- [ ] Before each checklist revision or handoff, compare against every fixed acceptance item in `OWNER.md` and confirm R1–R7 remain present and active here, with no silent deletion, weakening, or cancellation.
- [ ] Keep the original request and all R1–R7 active unless the owner explicitly cancels or changes them; record any such owner change before revising acceptance.

## R7 — Rejection export row number and reason

- [ ] Include a rejected-row fixture and verify the exportable CSV contains that row's original input row number and a human-readable rejection reason. These two fields are binding; other report details remain unspecified.
