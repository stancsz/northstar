# A2A evaluation summary

Northstar keeps reusable implementation, tests, usage guidance and concise capability conclusions in Git. Generated receipts, source manifests, observations, detailed reviews and project-specific execution records are stored outside this repository.

## Evidence location

Local archive: `D:/northstar-artifacts/a2a-stack/`.

- [Archive manifest](D:/northstar-artifacts/a2a-stack/northstar-migration-manifest-2026-11-03.json): original names, byte sizes and SHA-256 values for the 78 files migrated on 2026-11-03.
- [Local framework recovery review](D:/northstar-artifacts/a2a-stack/council-long-running-review.md).
- [Current workload checkpoint](D:/northstar-artifacts/a2a-stack/instacart-soak.md).
- [Supervisor checkpoint](D:/northstar-artifacts/a2a-stack/supervision-checkpoint.md).

These local links are machine-specific and are not distributed by cloning Northstar. Archive data needs its own backup if retention is required. Missing local evidence must be reported as unavailable, not inferred from this summary. Existing Git history still contains previously committed files; this migration does not rewrite history.

## Retained capability conclusions

The recorded local Windows/Claude Code/A2A/MCP trial completed a two-hour workload with independent review and same-Goal recovery after planned host/tool outages, without corrective operator dispatch or source edits during the acceptance run. This is scoped evidence, not arbitrary-project, whole-OS-reboot or perpetual reliability proof.

Later application-maintenance trials have separate evidence in the local archive. Assisted and unassisted results must remain distinct. Their success does not establish completion of the application.

## Storage rules

Write new run receipts, logs, screenshots, snapshots, private review details, candidate manifests and application execution journals to the external archive or the application's own designated untracked evidence storage. Do not promote them into Northstar Git. Keep application source and maintained regression tests in their owning repository.

Existing live runtime state under `tmp/a2a-stack/` is ignored and was not moved: relocating active databases, process receipts, immutable fixtures or worker paths requires a separate quiescent migration. This exception is not permission to commit those files.
