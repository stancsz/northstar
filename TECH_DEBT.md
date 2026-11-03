# Technical debt

## A2A root scopes containing live operational state

Status: open; priority: P2. Observed during the 2026-11-03 Instacart readiness work.

The default Northstar workspace contains its own `tmp/a2a-stack` state tree. A whole-workspace `.` scope therefore includes changing journals and live lock files; snapshotting can fail with `PermissionError`, and operational changes invalidate candidates. The corrected root matcher deliberately includes all authorized files and fails closed. It does not silently omit state or `.git`.

The current eight-file framework Goal and prepared nine-file Instacart Goal use explicit paths and avoid this overlap. Their acceptance does not establish stable self-hosted whole-root execution.

Follow-up: provide a clear admission diagnostic for an operational-state overlap, or an explicitly configured external state location with a reviewed migration that preserves existing default-workspace data. Preserve completeness: do not quietly skip unreadable or changing scoped files. Verify with isolated lock/state fixtures before broadening the supported configuration.

## Windows checkpoint replacement contention

Status: open efficiency follow-up; priority: P2 while automatic recovery converges. On 2026-11-03 the actual Instacart Goal `g-2ab099f9f9424d93917be136905cf3da` recorded one `WinError 5` replacing `state.json`. The existing harness resumed the same session without interrupting its separate coding worker. The actual holder and cause remain unknown; this is not evidence of an external blocker.

Owned Windows 10.0.26200 / NTFS fixtures reproduced the error with a held ordinary reader. A reader allowing read/write/delete sharing still blocked `os.replace` of its open target, although renaming that open source to a new name succeeded. The proposed reader-only repair failed its effectiveness test and was reverted in the private copies; production was unchanged.

`ReplaceFileW` passed a limited open-target fixture with share-delete readers, but Microsoft documents partial-failure states (1176/1177) that can move or remove the destination. It was not adopted as an atomic writer. See [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew) and [ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew). The controlled fixtures establish a platform vulnerability, not attribution of the actual incident or crash/power-loss durability.

Reopen if contention repeatedly prevents progress or measured owner restarts warrant a dedicated fix. Preserve same-Goal recovery and atomic snapshots; do not silently weaken durability, overwrite in place, change file permissions, kill readers, or block the host event loop with an unbounded synchronous retry. A replacement must pass failure-state and concurrent-snapshot checks before deployment. Diagnostic evidence is retained privately under `tmp/a2a-stack/instacart-soak/state-reader-repair/`.

The later reviewed snapshot-recovery increment keeps the existing writer unchanged and avoids model diagnosis for recognized owned-state write errors only after recovery persistence succeeds. It also closes the post-spawn cleanup gap. These are separate from the unresolved Windows replacement API/holder investigation; neither establishes a new writer or attributes the original lock.
