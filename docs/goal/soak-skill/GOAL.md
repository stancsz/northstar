# Goal: include the Soak testing skill in Northstar

Date: 2026-10-29. Status: complete.

## Outcome and acceptance

- Add Soak testing guidance as an installable, optional Northstar skill.
- Keep the repository skills-only; do not copy or package the independent Soak framework.
- Update package documentation and installation guidance, then verify links, metadata, whitespace, and the documented copy path where possible.

## Source and decision

The source is the public [`stancsz/soak` repository](https://github.com/stancsz/soak), inspected at the current `main` branch on 2026-10-29. Its README describes the framework as separate from the agent skill. The repository declares no license, so Northstar carries a concise independently authored adaptation of the five-step skill guidance rather than a wholesale copy. The skill links to the source repository and clearly distinguishes guidance from the framework.

## Acceptance record

- Added `skills/soak-testing/SKILL.md` as an optional standalone skill.
- Updated root guidance, the README skill table, and install guide with separate-skill installation instructions and the framework boundary.
- Scoped local Markdown links resolve and `git diff --check` passes. The copy command is documented; a temporary install simulation was blocked by execution policy, so copy behavior remains unverified. No framework runtime or model soak was run; package integration does not establish soak-test behavior.
