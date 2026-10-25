# Acceptance-threshold source review

Date: 2026-10-24. Scope: risk-proportional review policy in the current Northstar source increment. This is source review, not a runtime or product-effect evaluation.

## Verdict

**PASS after repair.** A nonauthor Codex CLI reviewer inspected the working-tree source through the configured local LiteLLM route. The first pass found two genuine policy contradictions; the author fixed both, then a read-only recheck passed. The primary remains the single approval owner; QA remains evidence rather than a second approval queue.

## Findings and repairs

- `README.md` treated delegated work itself as a reason for nonauthor review. It now uses the shared contract's threshold: one nonauthor check when required, with commander acceptance for small, reversible work.
- `skills/northstar/references/goal-driven-engineering.md` required an unconditional nonauthor verdict in one lifecycle step while a later paragraph was conditional. The lifecycle now follows the shared threshold and allows commander acceptance from relevant evidence otherwise.

The final review found the six entrypoints aligned. It confirmed attributable scope and relevant evidence for direct acceptance, unverified status when required review is unavailable, author/reviewer separation, integrated-environment checks when warranted, inherited authority, bounded recovery, and native CLI limits. Delegation alone and unrelated dirty files are not review triggers.

## Cost and limits

The first pass used 264,833 input tokens (117,248 cached) and 6,412 output tokens across 16 command events; it reported the two findings and had one failed command. That command attempted a local memory search but failed on a PowerShell regular-expression error before reading content. The Codex process also logged an unsuccessful local BrowserOS MCP initialization. Neither supplied review evidence.

The recheck used 413,072 input tokens (153,088 cached) and 5,110 output tokens across nine command events, with no command failures. The BrowserOS MCP endpoint was disabled for this pass. Combined CLI-reported usage was 677,905 input tokens (270,336 cached) and 11,522 output tokens. These are reported run metrics, not a complete monetary bill. The cost reinforces the rule that routine low-risk sequential work should not automatically receive an additional reviewer.

The reviewer did not run tests or exercise Northstar in an application. The source walkthrough and Markdown checks establish neither runtime behavior nor general delivery effectiveness. Existing real-task trials remain bounded evidence only.
