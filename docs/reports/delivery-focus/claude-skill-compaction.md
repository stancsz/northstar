# Claude Code Subagents skill compaction

Date: 2026-10-25. Goal: [delivery focus](../../goal/delivery-focus/GOAL.md). Worker: local Codex CLI through the configured LiteLLM `default` route. Parent owns integration and acceptance.

## Ask and result

Shorten the installable Claude Code companion, remove references that fail outside the repository, preserve its route, authority, credential, tool-evidence and handoff boundaries, and avoid one worker per criterion. The worker changed only [`SKILL.md`](../../../skills/claude-code-subagents/SKILL.md), from 3,216 to 1,091 whitespace-delimited words. It removed timestamped trial narrative and all links to repository-only reports; a new reference file was unnecessary.

## Evidence

- A preceding read-only CLI smoke returned its unique marker in a successful native `command_execution` event and final handoff; exit 0.
- The write worker exited 0 and emitted a `file_change` event for the assigned skill only. Its scoped `git diff --check` and local link/anchor check passed. Parent review confirmed the change stayed within the assignment and retained the required operating boundaries.
- Before syncing, all six installed core `SKILL.md` files differed from the repository sources; installed Northstar was 5,392 words versus 2,566 in source. The six directories were backed up under `tmp/installed-skills-before-sync-20261025/`, then synchronized. The Claude skill was separately backed up before its follow-up update. Source files now hash-match; three installed-only files were preserved. All 26 installed Markdown files pass local link/anchor checks.
- CLI-reported usage for the write task: 461,635 input tokens (93,952 cached) and 6,536 output tokens. It emitted the skill-description-budget warning and spent tool calls on a broad memory search plus full install/history reads. This one task is not an efficiency comparison; it is evidence that this CLI path can be costly for a bounded edit. Do not claim savings or general reliability from word-count reduction or this successful handoff.

## Remaining

No Claude CLI inference or tool behavior was exercised by the edit worker; it was a Codex CLI worker operating on Claude instructions. Future sessions may need to reload installed skills. General Northstar effectiveness and real-product delivery remain unverified.
