# Representation-aware validation handoff

## Observed failure

A synthetic parser worker rejected string '1.2345' but accepted numeric literal 1.2345. A later handoff claimed the repair although direct inspection found the source unchanged. Targeted re-dispatch fixed it; the worker's Git scope check also ran from the enclosing repository root rather than the assigned fixture.

## Instruction change

Added to the handoff guidance in [Codex subagents](../../../skills/subagent-orchestration/SKILL.md#task-brief-and-handoff): when acceptance depends on value type or representation, test actual values of each relevant runtime type rather than textual equivalents alone; rerun targeted acceptance against the final edited artifact before reporting; provide concrete commands/results or explicitly mark uncovered criteria unverified. The existing five brief elements, authority rules, and independent parent acceptance remain unchanged.

## Checks and limits

Read AGENTS.md, the assigned handoff sections in skills/codex-subagents/SKILL.md, and docs/reports/dispatch-context/plugin-disabled-helper-option.md. Inspected the scoped diff and ran git diff --check on the two assigned files; it passed. This is an instruction change, not parser implementation or a runtime behavioral test. No broader link audit or repository checks were run.
