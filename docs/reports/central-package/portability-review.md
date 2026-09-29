# Cross-agent portability review

- Goal: [central package](../../goal/central-package/GOAL.md), cross-agent installation note.
- Review base: `bd41b18`; review date: 2026-09-29; reviewer configured as `gpt-6-luna`, medium reasoning.
- Verdict: **READY**.

The installer guidance explicitly says the package is Codex-native and usable by Claude Code, OpenCode and other agents, and tells installers not to skip skills based on `Codex` names. The same intent appears in the root discovery text, Chinese installation index, Northstar direction, and all four skill descriptions/loaded entrypoints. Four skill names and sibling-directory instructions remain intact.

Host adaptation is framed as guidance: use the receiving host's loader, tools and invocation conventions, or read the entrypoint directly. It does not claim tested runtime integration. Northstar and Advisor retain the configured service, authentication and optional reader prerequisites. The Advisor UI metadata now describes an agent task/current worker while preserving its skill identifier and behavior.

Checks: inspected the diff from `bd41b18`, touched installer/discovery/skill metadata, relevant Northstar and Advisor instructions, goal follow-up, and existing four-skill references. Confirmed the added relative links point into the bundled installation/skill paths. Primary reports all four metadata validators passed, 74 Markdown files / 439 local links / 112 heading targets passed, and `git diff --check` passed; these repository-wide checks were not rerun by this reviewer.

Limitations: documentation and metadata review only. No Claude Code, OpenCode, other-host or live Advisor execution was performed or claimed.
