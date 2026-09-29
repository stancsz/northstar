# Publication snapshot review

Goal: [central package publication](../../goal/central-package/GOAL.md#publication-handoff).

Date: 2026-09-29. Scope: staged Northstar and Subroute snapshots for the central package publication. Both checked-out `HEAD` commits match fetched `origin/main` (`265c9db305d4f42f1e6d964f4a2e76a2aa80df97` and `c7080695ffc0e0605a114899df42a166cdaf1309`, respectively).

**Decision: READY for the reviewed publication scope.** Northstar’s staged snapshot has the four current skill entrypoints (`northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`), matching metadata, the QA rename, the Advisor migration and tests, and the scoped operating guidance and historical evaluation updates. The three migrated Advisor scripts have staged Git blob IDs identical to their Subroute `HEAD` versions. Northstar `git diff --cached --check` passes.

Subroute’s staged snapshot is exactly nine paths: README migration notice, old Advisor skill notice/history, five migrated payload removals, and two migrated test removals. The notice links to the matching Northstar Advisor, four-skill install guide and reader reference. No runtime, service, authentication, configuration, unrelated test, secret, cache or scratch path is staged. Subroute `git diff --cached --check` passes. Prior package evaluation records the detached four-skill copy/link-closure checks and 24 Python plus 2 Node offline regressions; this review did not rerun them because Advisor runtime and test logic are unchanged. Its metadata, limits, migration dependencies and documented prior independent review are consistent with the staged package.

This is repository snapshot verification only. It does not prove live provider/service behavior, deployment, hosted availability or production outcomes. Publish Northstar first, then Subroute, and verify both remote commit IDs as planned.
