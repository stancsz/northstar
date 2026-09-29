# Four-skill package implementation

Date: 2026-09-29. Author: primary. Status: complete for the requested source migration. [Goal](../../goal/central-package/GOAL.md).

The final package contains four independently invocable skills: `northstar` as the central coordinator, `codex-qa` renamed from `northstar-qa`, `codex-subagents`, and `codex-advisor` migrated from Subroute. One installation flow copies the four complete directories as siblings. The central routing table names when to load each companion; it does not require all agents or advisor calls on every task.

Updated package metadata, relative links, English/Chinese guides, role briefs, direction and contribution guidance. Preserved previous uncommitted operating-system/learning work. Historical links follow current locations while historical evaluation claims and hashes retain their original meaning. Existing advisor helpers/tests are the user-requested narrow exception to the earlier Markdown-only collection rule.

Advisor migration inventory and implementation are by `advisor_inventory` using selected `gpt-6-luna` medium; [worker report](advisor-migration.md). Independent [package review](package-review.md) by `package_review` using selected `gpt-6-luna` high is READY after repairing the stale QA name in the goal template. Primary owns integration, source-removal/redirect in Subroute and acceptance. Verification and limitations are in the [evaluation](../../evals/central-package.md).

No installed copies, running services, gateway routes, authentication, Git commits or remote branches are changed by this task. New hosted advisor URLs become available only when the source changes are published.

Validation: a detached copy of all four skills retained byte-identical files, 94 package-local links and 61 heading links; all four metadata/UI prompts passed. The copied advisor CLI help and its copied regression suites passed: 24 Python tests and 2 Node tests, zero skipped. Primary independently checked source script hashes and Subroute's exact changed-path list. Source migration retains only a clear moved notice with archived text at the old advisor entrypoint. No gateway changes or live provider requests occurred.

## Cross-agent note follow-up

2026-09-29, base `bd41b18`, primary: added the owner's portability note to English/Chinese discovery and installation guidance, all four skill descriptions and entrypoints. Shared host adaptation guidance stays inside the installed bundle. Advisor UI copy now refers to the current worker without a Codex-only executor implication; actual service prerequisites remain. Four metadata validations and local links pass, with Python UTF-8 mode needed for the validator on Windows. No runtime edits or live cross-host tests. Learning: make eligibility clear before skill selection, then carry the same note into the installed instructions; a body-only note can be missed by an installer filtering names.
