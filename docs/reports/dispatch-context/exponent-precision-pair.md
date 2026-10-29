# Matched plugin-disabled repeat with scientific-notation acceptance

## Result

Parent acceptance passed the declared implementation contract in both arms. Each worker and the parent passed the same five-test suite; each final source also passed 18 additional parent probes. The plugin-disabled worker reported 141,368 input tokens versus 167,926 for baseline (15.8% fewer) and 2,089 output versus 2,433 (14.1% fewer). Cost is unknown. This is one synthetic pair and does not prove a general saving or reliability rate.

There is a behavior difference outside the prompt's explicit acceptance: baseline parses `0,000`, `000,000`, and `001,000`, while treatment returns `null` for all three. The phrase “correctly grouped thousands” did not specify leading-zero behavior. Advisor Council judged the pair against its written acceptance and said not to retroactively fail either arm; the implementations are not behaviorally identical on these unspecified inputs. Future assignments must state the rule explicitly. This report retains the observed outputs instead of hiding the difference.

## Route and setup

Reused the current `default`/Responses direct-route receipt at `tmp/dispatch-context/current-route-preflight/receipt.json` (unique response plus complete function-call/result roundtrip, timestamp 2026-10-23T03:16:01Z). The helper-mediated native read-only smoke returned exact marker `NORTHSTAR-SUBROUTE-READONLY-fb5edcc0653d45189e11d5df6e9e7697`, exited 0, and made no file changes. Its first command used an incorrectly escaped Windows path and failed; the second command used the exact forward-slash path and succeeded. This path error is retained in the JSONL.

The two isolated fixture workspaces are under `tmp/dispatch-context/plugin-pair-exponent-fb5edcc0653d45189e11d5df6e9e7697/`. The assignment SHA-256 was `B130DDCB81BFD644E0BFAA59406D3425FF5B1A2DD827F9BF58FE3F76FB71C537`. Before dispatch, both arms had identical hashes: `package.json` `6D7F1FE7A82FB0AF981D3C68B7DF1BEC57BF60BF4F2971A38BB86EA9AD7F89AB`, tests `AB6FD014F79B356E3006477FB50424B13FAC5521D96CA9CFB6714D3EE600E73E`, and failing source stub `44D9D51951C83ED45692937BA7F14451507E5CB9396EE72689402D1DB75F3C2D`. Both initial runs failed four of five tests. Prompts, model alias, endpoint, profile, sandbox, helper process settings, fixture and deadlines matched; treatment alone added `features.plugins=false`.

## Worker and parent verification

Both worker JSONL streams contain three native `command_execution` events, each with exit 0; `turn.completed`; and file changes only to their assigned `src/quantity.js` and `handoff.md`. Baseline emitted three file-change events because its handoff was updated once; its unique changed-path set still contains exactly those two files. Both workers returned a complete handoff and reported their exact `node --test test/quantity.test.js` output with 5/5 passing. Parent reran the same command in both fixture roots and got 5/5 passing.

The 18 parent probes in each arm covered integer and 3-place values, over-precision, scientific integer/decimal forms (`1e21`, `1e3`, `1.23e2`, `1e-3`, `1e-7`), `Number.MAX_VALUE`, grouped/whitespace values, malformed grouping, string exponent syntax, negative/non-finite values, negative zero, and wrong types. All 18 passed in each arm. A first probe run incorrectly used `Object.is(-0, 0)` and produced a false failure; the corrected numeric equality check passed. The three leading-zero grouped cases above were then inspected separately and retained as an unspecified behavior difference.

Worker usage: baseline 167,926 input (33,280 cached), 2,433 output and 762 reasoning; treatment 141,368 input (26,624 cached), 2,089 output and 585 reasoning. Advisor Council usage was 2,403 combined tokens (Gemini 1,528; Sol 875). The initial Advisor script launch via `py` failed before any model request because the Windows Python app alias was inaccessible. One Council call then succeeded using Codex's bundled Python executable and the same Northstar Advisor caller, key and endpoint; no provider or model fallback occurred. Cost is unknown. Parent orchestration token use is not available.

Across this continuation's five Codex CLI turns (read smoke, two implementation workers, the unsuccessful reviewer brief, and the corrected independent review), reported usage totals 557,605 input (129,280 cached), 7,972 output, and 2,481 reasoning tokens. The Advisor Council separately reported 2,403 total provider tokens. These are measured CLI and Advisor categories only; parent orchestration usage is unavailable, and no cost was returned.

Advisor decision: retain the present pair as passing its written acceptance, but report the grouped-leading-zero behavior difference as unresolved specification ambiguity. The next comparable assignment should choose and state whether grouped strings permit leading zeros, then include `0,000`, `000,000`, and `001,000` in both fixtures before dispatch.

No production source, credentials, provider settings or global CLI settings changed. No package, cleanup, commit or push occurred. Raw command streams, stderr, before hashes, assignments and handoffs remain in the fixture directory.
