# Goal: Coordinated delivery without avoidable approval loops

Status: done

## Outcome and acceptance

Give managing agents concise role briefs and an actionable coordination loop. Reuse Northstar recovery and QA instead of adding a second process. Preserve prior QA work in the checkout.

- Carry existing authorization across delegation/context changes; distinguish missing decisions from platform restrictions.
- Managers resolve local decisions, dependencies, overlap, stalled work, and false completion; verify the integrated result.
- Provide discoverable orchestrator and supervisor templates with explicit integration and handoff ownership.
- Exercise the guidance in bounded execution trials; inspect the artifacts independently and state evidence limits.
- Validate Markdown links, installation paths, and diffs; refresh the existing local installed copies.

## Ownership and tasks

The primary agent owns direction, shared indexes, implementation, trial setup, and final acceptance. Trial agents may edit only assigned scratch fixtures and their report paths. No commit, push, deployment, or external action is part of this increment.

1. Primary: skills/templates and documentation. [Implementation report](../../reports/coordinated-delivery/implementation.md).
2. Trial orchestrator: local receipt integration with overlapping inherited assignments; up to two leaf workers. [Trial report](../../reports/coordinated-delivery/orchestrator-trial.md).
3. Trial supervisor: inspect an inherited completion claim and finish a local repair with prior authorization. [Trial report](../../reports/coordinated-delivery/supervisor-trial.md).
4. Independent reviewer: inspect role/authorization/coordination instructions; write only the [review report](../../reports/coordinated-delivery/independent-review.md).

Critical dependency: stable role instructions before trials. Integration owner: primary agent. Trial outcomes cannot alone establish long-session reliability or enforced behavior.

## Execution and acceptance

Supervisor decision (primary agent): accepted implementation, both bounded execution trials, and independent review after reading reports and actual artifacts. Parent reran four receipt and three invoice acceptance cases successfully; protected-file hashes matched. No material repair remains.

Orchestrator decision (same primary agent): accepted this increment. The role briefs, shared coordination loop, authorization continuity, and local installed copies are complete. The trial orchestrator used one real worker with disjoint writes and an agreed interface, then integrated its result. The supervisor detected false completion and repaired it without repeated approval. Evidence supports these cases only; it does not guarantee future behavior. See [evaluation](../../evals/coordinated-delivery.md).

Documentation verification: both changed skill metadata checks passed; 37 Markdown files, 172 local links, and 27 heading targets resolved after all reports were available. `git diff --check` passed; `docs/` has no loose files. Evaluated instruction hashes remain unchanged; installed files including templates match source. Final checkout usage including ignored scratch/backups was 1,347,102 bytes. Existing QA edits are preserved. No commit/push is included in this increment.
