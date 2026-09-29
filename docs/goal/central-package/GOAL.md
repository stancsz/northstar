# Goal: One Northstar package including Codex Advisor

Status: done. Date: 2026-09-29. Base: `265c9db` plus preserved prior working edits.

## Outcome and acceptance

The user requests one central package containing four distinct skills: Northstar, Codex QA (renamed from Northstar QA), Codex Subagents and Codex Advisor (migrated/renamed from Luna Advisor in Subroute). Subroute must direct users to the new location.

Acceptance: exactly four `skills/<name>/SKILL.md` entrypoints named `northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`; one install flow copies the four complete sibling directories. Northstar routes to companions, which remain directly invocable. All dependencies must resolve inside this four-skill bundle without user-specific paths. Preserve current guidance and existing advisor behavior/limits. Migrate advisor-only tests with portable source paths, retain a redirect at the old Subroute location, and preserve gateway runtime and unrelated dirty work. Historical records remain historical; links follow moved artifacts.

The explicitly requested advisor migration includes its existing caller scripts and regression tests as a narrow exception to the earlier Markdown-only convention. It does not authorize new enforcement/reporting machinery, deployment, package installation, paid provider calls, commit or push.

## Ownership and tasks

Primary owns package layout, existing-module relocation, shared indexes/direction, Subroute migration notice/source removal, integration and acceptance. Lower-tier inventory/migration worker owns only assigned new advisor references/scripts/tests plus its report; no gateway or installed-skill writes. Independent lower-tier review follows integration. Scratch is `tmp/central-package/`. [Reports](../../reports/central-package/implementation.md), [evaluation](../../evals/central-package.md).

## Validation

Inspect preserved content and full relative link closure after a detached copy of the complete four-skill bundle. Validate all four skill metadata/UI entries; run the migrated local caller/reader regression tests without paid calls. Check CLI help from the detached package, obsolete current paths, installation instructions, both repo diffs and protected Subroute runtime state. Document external advisor service/Pi prerequisites honestly. No live provider, runtime deployment, cost-saving or long-session efficacy claim.

Acceptance: primary accepts the four-skill bundle, renamed QA, migrated advisor and Subroute redirect. Detached installation/CLI checks, 24 Python and 2 Node regressions, all four metadata validations, source hash/scope checks and independent READY review passed. See the evaluation for exact checks and remaining publication/runtime limits. Prior dirty work remains intact.

## Publication handoff

2026-09-29: the owner explicitly requested commit and push after accepting the package and subsequent operating-practice updates. This supersedes the earlier task-local no-commit/no-push boundary for these changes. Both repositories are on `main` and matched their fetched `origin/main` before committing. Publish Northstar first, then Subroute's nine-path migration/redirect so the destination exists. Gateway runtime, live services and installed skill copies remain outside this publication. Inspect the staged snapshots and verify both remote commit IDs after push; Git history and the final handoff record the actual publication results.

A separate Luna medium reviewer owns `docs/reports/central-package/release-review.md`, scratch `tmp/release/reviewer/`; inspect staged scope, four-skill packaging and migration dependencies without redoing completed behavioral reviews. Primary owns staging and Git operations. Staged whitespace inspection found five pre-existing trailing blank lines in newly added docs/tests; removed only those blank lines. Advisor runtime and test logic are unchanged from the passing offline regressions.

Primary inspected and accepted the independent [publication review](../../reports/central-package/release-review.md): READY, with no blocking findings in either staged snapshot. Remote publication verification follows the push.

## Cross-agent installation note

2026-09-29 follow-up, base `bd41b18`: the owner requests an explicit installer-facing note that Codex-native skills also apply to Claude Code, OpenCode and other agents. Keep four names and sibling paths; make the note visible in installation guidance and discovery metadata as well as loaded instructions. Adapt host tools without claiming untested integration support or changing Advisor dependencies. Primary owns these edits, shared records and publication using the existing direct-to-main workflow. A separate Luna medium reviewer owns only `docs/reports/central-package/portability-review.md`, with scratch under `tmp/portability/reviewer/`. Acceptance requires a scoped independent documentation review, local link checks and valid four-skill metadata; live cross-host execution is outside this note's claim.

Accepted: primary inspected the changed documents and independent [READY review](../../reports/central-package/portability-review.md). Four skill validations, local links and whitespace checks pass. The [implementation handoff](../../reports/central-package/implementation.md#cross-agent-note-follow-up) records the reusable lesson: make compatibility visible during discovery and preserve it after installation. No runtime or installed-copy change is included.
