# Matched Codex CLI pair: canonical comma grouping

## Result

The baseline and plugin-disabled treatment both passed the five assigned tests and 23 parent acceptance probes. A separate read-only Codex CLI reviewer reran the tests and probes and returned PASS for the written contract. The task explicitly required comma-grouped strings to start with a 1–9 digit followed by exact groups of three; `0,000`, `000,000`, and `001,000` were rejected in both. Numeric exponent requirements (`1e21`, `1e3`, `1.23e2` accepted; `1e-7` rejected) also passed.

A separate extra probe found an ungraded signed-zero difference: baseline accepts numeric `-0` and returns a negative-zero value; treatment returns `null`. Both reject string `"-0"`. The assignment did not specify IEEE signed zero. Advisor Council recommended no retroactive penalty and future wording: accept numeric `-0` as `+0`, reject string `"-0"`, with `Object.is` used to verify normalization. Thus the pair passes the written assignment but is not behaviorally identical for all values.

## Matched setup and worker evidence

The isolated fixtures are under `tmp/dispatch-context/plugin-pair-canonical-grouping-3c008a88f3ae41b6bf4fb85d8786f189/`. The shared assignment SHA-256 is `63E6AE70FF240B96436AED94D8B44F0A7B53BA89ED308C9CD6305E493FAEF2F5`. Both arms started with identical hashes: package `6D7F1FE7A82FB0AF981D3C68B7DF1BEC57BF60BF4F2971A38BB86EA9AD7F89AB`, tests `0BD831323B3D9895DE5CCC8423B2492E34D65E321F83BE79C019B471AFD5FBB9`, source stub `44D9D51951C83ED45692937BA7F14451507E5CB9396EE72689402D1DB75F3C2D`. Both initial runs failed four of five tests.

Both tasks used the same Subroute `default`/Responses profile, route, workspace-write sandbox, brief, fixtures and helper settings. Treatment alone added `features.plugins=false`. Each worker exited 0, completed its turn, emitted three native command events and changed only its assigned `src/quantity.js` and `handoff.md`. Each worker and the parent independently ran `node --test test/quantity.test.js`; all runs passed 5/5. Parent acceptance and the reviewer each passed all 23 specified probes per arm.

Baseline usage was 126,979 input (30,848 cached), 2,380 output and 756 reasoning tokens. Treatment usage was 118,991 input (37,120 cached), 2,023 output and 508 reasoning tokens. Treatment used 6.29% fewer total input tokens and 15.0% fewer output tokens in this pair; cost is unknown. This does not establish a general saving.

## Route, Advisor and review evidence

The current direct `default`/Responses unique-response and function-result receipt was reused. A fresh helper-mediated read-only smoke returned marker `NORTHSTAR-CLI-SMOKE-3c008a88f3ae41b6bf4fb85d8786f189` in one native command, with exit 0, no file changes, and usage 55,283 input (22,656 cached), 372 output and 52 reasoning tokens.

Advisor Council recommended recording numeric `-0` as ungraded and specifying future normalization to `+0`; its reported usage was Gemini 1,423 plus Sol 671, or 2,094 tokens. The separate read-only Codex CLI reviewer returned PASS, reran tests and probes, confirmed the token arithmetic and unknown cost, and made no file changes. It completed 12 native command events with three corrected command failures (one Windows path, one `node -e` quoting error in each arm), exit 0, usage 310,156 input (135,424 cached), 4,077 output and 974 reasoning tokens. The review report preserves those command errors and corrections.

Across the four Codex CLI turns in this continuation (smoke, two workers, reviewer), known usage totaled 611,409 input (226,048 cached), 8,852 output and 2,290 reasoning tokens. Advisor usage is separate. Parent orchestration usage was unavailable, and cost is unknown. This high total leaves economical dispatch unresolved.

No Northstar production source, provider target, global CLI setting, credential, package, cleanup, commit or push changed. Full JSONL, stderr, tests, assignments, parent receipts and handoffs remain in the fixture directory.
