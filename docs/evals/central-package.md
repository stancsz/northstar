# Four-skill package and advisor migration evaluation

Date: 2026-09-29. [Goal](../goal/central-package/GOAL.md). [Implementation](../reports/central-package/implementation.md). Northstar base `265c9db` plus prior working edits; Subroute source `c7080695ffc0e0605a114899df42a166cdaf1309`, initially clean.

## Acceptance and method

The final owner requirement is four separately named skills together in one package, with Northstar as the coordinator: `northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`. Check entrypoint names, metadata/default prompts, trigger routing, full-bundle relative link closure and portable installation. Rename QA, move the advisor assets and skill-only tests, and leave Subroute discovery URLs without changing gateway runtime. Preserve earlier learning, autonomy and authority rules.

Primary owns layout/docs/integration; selected `gpt-6-luna` medium inventories and migrates the advisor; a separate selected `gpt-6-luna` high reviews the package. This task uses local regressions and documentation checks, not paid provider calls. Test/cost/quality claims stay scoped to actual observations.

## Evidence

- Ran the documented four-directory PowerShell copy flow into a fresh `tmp/central-package/install-probe/skills/` destination. Exactly four entrypoints and their names were verified. Every copied file was byte-identical to source; all 94 local links and 61 heading links resolved inside the detached bundle, with no repository fallback.
- Invoked the detached `codex-advisor/scripts/ask_expert.py --help` successfully without a provider request. Copied the migrated tests beside that bundle, so their path resolution loaded the installed helpers rather than source. Python: **24 passed in 4.58s**. Node: **2 passed, 0 skipped**, about 1.79s, including native Pi line-number behavior against the existing local package. This follows the worker's original-path runs of 24 and 2 passing checks. No dependencies were installed.
- All four skill frontmatter validations passed; each UI default prompt invokes its own name and descriptions meet the UI length limit. Current skill content has no retired QA/advisor name or developer-specific user path. QA and coordination requirements remain; the independent reviewer caught and rechecked one stale QA name in the reusable goal template.
- Primary independently compared all three scripts against Subroute and saved original file hashes in scoped scratch. All scripts are byte-identical. The migrated test differences are only asset paths and the Python loader module name. Original hashes are recorded in the [migration report](../reports/central-package/advisor-migration.md).
- Subroute's changed-path list is exactly README, the old advisor entrypoint and its five migrated payload removals, plus two skill-specific test removals. Runtime handlers, configs, Compose, normal gateway tests and auth were untouched. README and old entrypoint link to `stancsz/northstar/skills/codex-advisor` and the package installation guide. The old file starts with a migration notice, has no discoverable YAML frontmatter and retains original instructions explicitly as archived history.
- [Independent package review](../reports/central-package/package-review.md) is READY after the goal-template rename repair. The reviewer independently inspected structure, limits, paths and Subroute scope without repeating provider or behavioral claims. Both repository `git diff --check` checks passed; final whole-repository local-link check recorded below.

Automatic approval review rejected removing an empty legacy QA directory and replacing the old advisor file wholesale, with only a generic policy reason. No empty-folder cleanup was forced. The safer advisor update preserved its old text as archived history beneath a clear migration banner; the four installable entrypoints and bundle flow are unaffected.

## Boundaries

The dedicated Subroute `experts` Compose service and configuration remain in Subroute, along with provider auth and gateway runtime tests. The current source still exposes Sol/Astra on the dedicated loopback expert service. Installation does not start it, authenticate it or authorize source transmission or spending. Ordinary calls and optional Pi reading have distinct prerequisites. No hosted publication, installed-copy refresh, service deployment or live advisor compatibility is claimed by a successful local package check.

## Learning

The user's clarification fixes the package boundary: central coordination and one install flow must preserve four discoverable skills. Do not equate bundling with flattening away their identities. Keep source-specific caller tests with the migrated code, distinguish the client skill from the gateway runtime, and validate the complete installed bundle rather than isolated source-file presence.

Acceptance: primary accepts the four-skill source package and scoped Subroute migration after reviewing the actual detached installation, test outputs, byte comparisons and independent findings. No commit, push, installed-copy refresh or service deployment is included. Hosted new paths will reflect the migration only after publication.

Final documentation check: 56 Markdown files, 321 local links and 85 heading links all resolved. Docs layout and exact nine-path Subroute scope passed; both diff whitespace checks passed.
