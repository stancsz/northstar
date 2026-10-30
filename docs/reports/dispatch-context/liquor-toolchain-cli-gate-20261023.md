# Liquor POC: approved toolchain gate and CLI smoke

## Handoff

The parent revisited the parent-owned liquor-ordering Windows source task after a completion review requested a source-pinned approved compiler record and rejection fixtures. The POC already contains the complete Node/native schema contract, an identical source-pinned digest over an intentionally empty production allowlist, and synthetic missing, altered, mismatched, and unapproved compiler identity cases. No compiler record can be approved without authenticated release signature, signer, archive, and extracted compiler evidence.

## Route and CLI evidence

The parent sent a unique marker request through Subroute `http://127.0.0.1:4000/v1/responses`, alias `default`, then forced a function call, replayed the call/result transcript, and received the marker. Both direct route checks passed. A subsequent read-only Codex CLI smoke did not complete its native-tool gate. The child attempted a shell command against `/mnt/c/Users/stanc/.codex/memories/MEMORY.md`, which is unavailable in this Windows executor and returned exit 1. A following native executor launch emitted `CreateProcessWithLogonW failed: 267`; no completed native command or handoff was accepted. One parent PowerShell harness attempt also failed before child start because `$HOME` is a read-only automatic variable; the corrected launch started the CLI, so the harness error is separate from the CLI failure.

The parent withheld the write-enabled worker because the required read-only native smoke had not passed. This is evidence that route/API success does not establish that the Codex CLI can execute tools. No gateway key was printed or persisted; no provider, endpoint, model alias, global setting, or credential source changed. Exact failure output and route marker are in the parent task stream; no request body or secret was saved.

## Source and acceptance status

On the POC, `node --test tests/distribution-manifest.test.mjs tests/desktop-package-handoff.test.mjs` passed 26/26. These tests include the empty production allowlist and synthetic policy-injection cases; they do not execute the Rust fixtures. Fresh POC preflight counted 10,029,742,198 bytes against the 10,000,000,000-byte ceiling and rejected the fixed 7 GB package reserve. No compiler, app build, package, install, cleanup, download, or provider/runtime trial ran. Production compiler and launcher callbacks remain fail-closed, and Windows delivery remains **NOT READY**.

## Next action

The corrected native `Get-Location` smoke and one bounded CLI documentation implementation have now passed parent acceptance. Use the documented `Invoke-CodexChild` helper for the next substantive implementation, with a narrow file allowlist and the same `default`/Responses route checks. Do not spend another turn repeating cwd diagnostics. Keep the production toolchain list empty until the complete Rust release signature and compiler-byte provenance is verified, and do not compile or package while the measured cap fails.

## Advisor follow-up and corrected smoke findings

Advisor Council (Gemini 4 Argon and GPT-6.1 Sol; 4,453 reported tokens total) recommended one changed read-only cwd smoke, explicitly skipping memory reads and requiring the exact expected cwd in native command output. The first parent prompt accidentally requested `cmd.exe /d /c cd .`; the native command exited 0 but returned no output, so it failed acceptance. The corrected request was normalized in the native event as `"C:\WINDOWS\system32\cmd.exe" /c '/d /c cd'` and returned `'/d' is not recognized`, exit 1. This reveals that the nested-shell spelling is incompatible with the executor's command wrapper; it does not reproduce or explain error 267. No further dispatch diagnosis should repeat that command. The Codex Subagents skill now directs future cwd smokes to use the native shell builtin and require exact path output.

Claude Code was not invoked: neither `ANTHROPIC_API_KEY` nor `ANTHROPIC_AUTH_TOKEN` is available in the process or Windows user environment. Safe local status shows the current Claude profile uses first-party `apiKeyHelper` auth, base URL `http://127.0.0.1:3456`, and model `provider-1/default`; this is not the requested Subroute route and was not changed. A Subroute Claude worker requires an already-authorized LiteLLM inference virtual key, passed process-only as `ANTHROPIC_API_KEY`, with an isolated config set to `http://127.0.0.1:4000` and model alias `default`. The gateway master key and Advisor key are not substitutes. No credential was created and no dotenv or token file was read.

## PowerShell native cwd smoke follow-up

The parent verified a CLI-native read-only PowerShell `Get-Location` smoke through the configured `default`/Responses route. Its structured native `command_execution` exited 0, the turn completed with a concise handoff, and stdout used PowerShell's formatted `Path` table, with `D:\github\northstar` on its own line. Therefore the cwd gate parses stdout lines and requires one trimmed line to equal the expected absolute path; the whole stdout string need not equal the path. The structured event and completion/handoff remain required, and empty or malformed output still fails. The earlier nested `cmd.exe` probes remain failed evidence and are not repeated. This bounded correction updates the [Codex Subagents cwd-smoke acceptance](../../../skills/subagent-orchestration/SKILL.md); Claude auth and POC package gates are unchanged.

## Parent acceptance: bounded Codex CLI documentation implementation

After the native smoke passed, the parent dispatched one workspace-write Codex CLI worker through the documented helper, the already-verified Subroute `default`/Responses profile, and the exact two-path allowlist: this skill file and this report. The worker updated cwd-smoke wording to accept the expected absolute path as a trimmed standalone stdout line, accounting for PowerShell's `Path` table formatting. Structured events show eight completed command executions (three nonzero exploratory/check commands), a completed turn, and file-change events resolving to only those two authorized paths. The CLI process exited 0 with a handoff. The parent verified the exact changed-path set, the skill text, link target, trailing whitespace and scoped `git diff --check`; all parent checks passed. The read-only smoke itself had one completed native command with exit 0, exact cwd line, completed turn and handoff.

The worker used 377,577 input tokens (192,640 cached), 4,320 output and 882 reasoning; effective backend and cost are unknown. This accepts one small documentation implementation handoff and repairs the smoke criterion. It does not establish economical delegation, repeat reliability, broad read-scope adherence or product-source progress. The POC remains fail-closed and over its 10 GB cap; no compilation, packaging, cleanup, commit or push occurred. Claude remains untested because the authorized Subroute inference virtual key is absent; the existing first-party Claude profile was not changed. Receipts: `tmp/dispatch-context/native-powershell-cwd-53f48096955141ad8e031a5959bef14d/worker.jsonl` and `tmp/dispatch-context/powershell-cwd-format-acceptance-a0d180bfb1134f41be87ab5e3f33a921/worker.jsonl`.

## Subroute tool-preflight failure after the accepted native CLI smoke

A later POC-directed preflight used the same `default`/Responses alias. Its unique response succeeded after correcting the PowerShell parser to inspect `output[].content[].text`; the forced function-call request then returned HTTP 502 `supplemental_advisor_failed` and the gateway said the base request was not sent. No CLI worker ran. This is an observed supplemental-advisor dependency failure, not evidence that the base Codex provider or credential failed. No route/model/provider/key/config switch or identical retry was made.

The repository-authorized direct source fallback added a fail-closed launcher receipt adapter in the POC, with independently supplied compiler/input identities, fresh output capture, exact native receipt comparison and fixed `Cellar.exe` output validation. The production compiler remains disabled pending a real retained-handle identity provider. Focused Node suites passed 37/37. POC preflight still exceeds the 10 GB cap after its fixed reserve, so there was no compile, package, cleanup, install or provider trial. No code or documentation was committed or pushed.

### POC full-suite verification follow-up — 2026-10-23

After the receipt-adapter source increment, the POC passed `npm run typecheck`, `npm run lint`, `npm test` (304 Vitest plus 11 desktop-artifact tests), and `npm run test:e2e` (34/34). `npm test`'s `pretest` regenerated the existing 16.26 KB `build/mcp.js`; no Rust/Cargo or desktop application build ran. Post-test package preflight remained at 10,029,742,198 counted bytes with no inventory errors; the 7 GB reserve still exceeds the cap projection. There was no package, cleanup, install, download, provider trial, commit or push.

Northstar's current route failure and CLI pre-dispatch guard are recorded in the [Subroute tool preflight report](subroute-tool-preflight-guard-20261023.md).
