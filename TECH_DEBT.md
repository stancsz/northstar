# Technical debt

## A2A root scopes containing live operational state

Status: open; priority: P2. Observed during the 2026-11-03 Instacart readiness work.

The default Northstar workspace contains its own `tmp/a2a-stack` state tree. A whole-workspace `.` scope therefore includes changing journals and live lock files; snapshotting can fail with `PermissionError`, and operational changes invalidate candidates. The corrected root matcher deliberately includes all authorized files and fails closed. It does not silently omit state or `.git`.

The current eight-file framework Goal and prepared nine-file Instacart Goal use explicit paths and avoid this overlap. Their acceptance does not establish stable self-hosted whole-root execution.

Follow-up: provide a clear admission diagnostic for an operational-state overlap, or an explicitly configured external state location with a reviewed migration that preserves existing default-workspace data. Preserve completeness: do not quietly skip unreadable or changing scoped files. Verify with isolated lock/state fixtures before broadening the supported configuration.
