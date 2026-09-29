# Independent package review: integrated four-skill bundle

**Reviewer role/model:** independent documentation and packaging reviewer; `gpt-6-luna`, high reasoning effort.
**Date:** 2026-09-29. **Status:** READY for the reviewed documentation/package surface.
**Scope:** `AGENTS.md`, root README, project direction, central-package goal, English install guide, Chinese guide, Northstar core and metadata, Codex QA, Codex Subagents and templates, Codex Advisor skill/reference/metadata/scripts, four-skill entrypoint count, and Subroute migration notice/removal diff. No provider calls, service startup, installation, or behavioral tests were performed by this reviewer.

## Final review

The package has exactly four current entrypoints: `skills/northstar/SKILL.md`, `skills/codex-qa/SKILL.md`, `skills/codex-subagents/SKILL.md`, and `skills/codex-advisor/SKILL.md`. The four metadata files use the matching names and UI prompts. Northstar identifies itself as the central coordinator and routes to companions using relative sibling links; direct invocation remains documented. The PowerShell install flow copies all four complete skill directories in one operation, and both language guides explain that they must remain siblings.

Northstar still owns execution and checkpoint learning. Codex QA retains workflow-based functional and rendered-visual inspection, adversarial checks, readiness evidence, repair/recheck, and its link to mandatory checkpoint learning. Codex Subagents retains bounded delegation, cost/capability, recovery, ownership, and handoff guidance. The Advisor skill preserves the advice-only role, current-worker ownership, ordinary and reader-mode call ceilings, separate expert and Pi endpoints, prerequisites, evidence boundaries, and local receipt expectations. Its examples resolve the installed directory rather than a user-specific path. The copied caller/reader scripts are reported byte-identical to Subroute source in the assigned migration handoff.

A local relative-link scan found no missing Markdown targets in any of the four skill trees. The three root-owned skill trees and the Advisor tree contain no user-specific filesystem paths. Installation and advisor-prerequisite guidance distinguish local CLI help and offline regressions from live service/provider proof.

The Subroute scope contains only the intended README migration notice, old-skill notice/history conversion, and removal of migrated assets/tests. Its README links to the Northstar package, installer and Codex Advisor entrypoint. The old `skills/luna-advisor-escalation/SKILL.md` begins with the new location and names the retired body as archived history; it has no discovery frontmatter. The changed-path list contains no gateway runtime, provider configuration or service implementation files. Existing gateway tests still mention Luna as a service model name, which is unrelated to the migrated skill and correctly remains in Subroute.

The earlier must-fix finding was resolved: `skills/northstar/templates/GOAL.md:17` now says “use Codex QA.” The remaining old skill names in current install/Chinese docs appear only as upgrade instructions, and in prior goals/reports/evaluations or the explicitly archived Subroute skill text; none is presented as a current entrypoint or path. `git diff --check` passed in the Northstar checkout. The Subroute checkout reports only its intended files changed; Git emitted a line-ending conversion warning for the archived skill notice, not a whitespace failure.

## Review decision and limits

**READY** for the reviewed package and migration documentation. The migration handoff reports 24 Python and 2 Node offline regressions passing; this reviewer did not rerun them, and those results do not establish live provider behavior. The primary owner is conducting the detached installation checks, CLI help check and integrated acceptance. This review does not claim successful skill-loader behavior on every host, live expert/Pi availability, provider quality, savings, human acceptance, or deployment.

## First-pass finding and recheck history

The first pass found that the reusable goal template still said “Northstar QA.” The primary owner changed the wording to “Codex QA”; final inspection confirmed the correction. No other must-fix package issue was found in the final scoped review.
