# Goal storage revision

Date: 2026-10-21. Author: `goal_storage` implementation worker. Status: implemented; independent acceptance pending. Goal: [issue maturity](../../goal/issue-maturity/GOAL.md). Base: `293f230dfcf1f5db360ce17901e4a594fc66e451` with pre-existing working edits preserved.

## Artifact and checks

Updated only the [goal reference](../../../skills/northstar/references/goal-driven-engineering.md#keep-goal-state-project-owned) and [fallback template](../../../skills/northstar/templates/GOAL.md). Existing project conventions remain first; the fresh-project fallback is explicitly rooted in the project. Canonical state is excluded from installation trees on every host. Legacy migration preserves the source, verifies the project copy before changing a project pointer, and retains inaccessible/conflicting-source gaps. Denial recovery distinguishes a new record from a denied established canonical record, preventing silent duplication. Explicitly personal work may use a named user-owned location subject to actual host rules.

Inspected the scoped diff and ran scoped `git diff --check`: passed. Checked both changed documents' six local links and five heading anchors: passed. Walked five instruction cases: existing project convention, fresh project, stale installation-root pointer, established project-path denial, and explicitly personal work. Each has a specified route without installation writes, access bypass or duplicate canonical goals. These were document walkthroughs; no sandbox denial, migration or agent execution was performed by this worker. Entrypoint routing and integrated behavioral probes belong to primary.

## Learning and handoff

The reported historical wrong path is absent from current source; the actual remaining gap was an explicit installation-tree boundary and recovery behavior. Preserve that distinction instead of claiming to remove a still-current path. The next check is a cold agent probe of a stale pointer and denied canonical project path, followed by nonauthor review. Primary owns acceptance/publication. No installed-copy changes, external actions, commits or pushes were made.
