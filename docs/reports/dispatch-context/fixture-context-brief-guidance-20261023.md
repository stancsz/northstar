# Fixture context brief guidance

## Result

Northstar's Codex delegation templates now require a test brief to name the exact fixture/setup/helper ranges and the latest passing baseline, so a parent does not send a worker to rediscover harness context.

## Files changed

- `skills/codex-subagents/templates/orchestrator.md` — Guidance bullet, line 8: added the fixture/baseline sentence once; every other sentence, including route, scope and validation guidance, is unchanged.
- `skills/codex-subagents/templates/supervisor.md` — Guidance bullet, line 8: added the same sentence once; every other sentence, including route, scope and validation guidance, is unchanged.

No other path was edited.

## Sentence added

> For test assignments, include the exact fixture/setup/helper ranges and latest passing baseline in the brief; keep missing-context discovery parent-owned. Do not ask the worker to rediscover the harness or rerun an unchanged baseline, but still run required post-change validation.

## Scope and validation notes

- Change is documentation-only inside the two assigned templates; no skill behavior, provider, model alias, endpoint or credential was touched.
- This repository has no build. Parent validation is pending: the parent owns the diff inspection, local Markdown link and installation-path check, and `git diff --check`, per `AGENTS.md`.
- The unchanged inference route (local LiteLLM at http://127.0.0.1:4000, model alias `default`, process-only Bearer in `ANTHROPIC_AUTH_TOKEN`) returned the expected marker with exit 0 in 3.1 seconds; the `unrecognized_model` stderr diagnostic is unclassified and is not attributed to auth. The direct Subroute Responses preflight passed a unique response and a stateless function-result tool roundtrip, all HTTP 200.

## Parent acceptance

Accepted after parent review. The Claude stream has one completed result, `is_error=false`, exit 0, and a final handoff. It records native Read/Edit calls only on the three assigned paths: the two manager templates and this report. The final Reads re-opened both templates and the report. The initial Read calls omitted line offsets for the two short template files, so the worker read each whole target file rather than only line 8; it did not read any other repository path or perform a broad search. Treat this as a small prompt-range deviation, not proof that line ranges are enforced by Claude's host tools.

The parent compared each final line against the pre-dispatch line plus the exact requested sentence. Both matched byte-for-byte; the sentence appears once in each file, and every other sentence is unchanged. All nine existing local links in each template resolve. `git diff --check` passed for both templates, and the untracked report has no trailing whitespace. This was documentation-only, so no build or test was required. The report's parent-validation-pending note is superseded by this acceptance section.

CLI-reported usage: 10,387 input tokens, 44,489 cache-read input tokens, 2,773 output tokens, 1,328 thinking tokens, 11 turns, and $0.1435045. Stderr contained an `unrecognized_model` diagnostic; the unique-response smoke exited 0, and the diagnostic remains unclassified. No key value was written to child command arguments or receipts; the existing owner-authorized Bearer was injected only as child `ANTHROPIC_AUTH_TOKEN`, while `GATEWAY_MASTER_KEY`, `EXPERTS_API_KEY`, and `ANTHROPIC_API_KEY` were absent in that child.
