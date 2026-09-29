# Advisor Reader

This reference supports the optional expert-directed Pi reader mode in [Codex Advisor](../SKILL.md). Reader mode needs Node.js 20.6+, Git, ripgrep, and the already-installed `@mariozechner/pi-coding-agent` version `0.73.1`. The tested version is checked locally; do not silently install or upgrade it. `PI_READER_PACKAGE` may point to the installed package directory; otherwise the caller uses `npm root -g`. Pi owns the native agent loop, Chat Completions transport, and read/grep/list tools. The small adapter constrains authority, calls and receipts. The text-only expert endpoint cannot invoke tools, so the caller forwards bounded structured read requests.

Resolve the installed `codex-advisor` skill directory as shown in [Codex Advisor](../SKILL.md) before running the example:

```powershell
$skillDirectories = @()
if ($env:CODEX_HOME) { $skillDirectories += Join-Path (Join-Path $env:CODEX_HOME 'skills') 'codex-advisor' }
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.agents\skills') 'codex-advisor'
$skillDirectories += Join-Path (Join-Path $env:USERPROFILE '.codex\skills') 'codex-advisor'
$codexAdvisor = $skillDirectories | Where-Object { Test-Path (Join-Path $_ 'SKILL.md') } | Select-Object -First 1
if (-not $codexAdvisor) { throw 'Set $codexAdvisor to this installation''s codex-advisor directory.' }
$codexAdvisor = (Resolve-Path $codexAdvisor).Path
py (Join-Path $codexAdvisor 'scripts\ask_expert.py') --model sol --input-file .\advisor-packet.txt --reader-root . --reader-scope src --reader-scope tests
```

Select task-relevant source directories broad enough to find counterevidence, not only files supporting the worker's hypothesis. Scopes authorize transmission of source excerpts through the worker gateway. Do not include confidential or credential-bearing sources without authority. No worker context is sent to Pi.

The expert decides whether Pi reading is needed and chooses neutral evidence questions; the worker does not decide on the expert's behalf. Flow: expert returns a final answer or `{"read":["question", "independent question"]}`; Pi searches the snapshot and summarizes it; the caller validates exact source-line citations; the same expert receives compact briefs and decides whether more evidence is needed. There is no user round trip. The final expert call cannot dispatch another task. There are no extra questions to the user, retries, model fallback, recursive delegation, or fourth expert call. Start reader mode before any consultations because call budgets are task-wide. Stop early once evidence supports a decision.

The final Pi model response disables tool selection and must return the bounded evidence brief. Do not accept a partial/tool-call response as completed evidence.

## Boundaries

- Expert API is fixed to `http://127.0.0.1:4040/v1`. Worker API is fixed to `http://localhost:4000/v1`; `--reader-model` defaults to `current`, and the gateway's force/auto policy remains authoritative. The receipt distinguishes requested alias from returned model. Nothing switches gateway policy. Optional `READER_API_KEY` authenticates only to that worker gateway.
- Isolated in-memory Pi session/auth/settings; no local skills, extensions, `AGENTS` files, compaction, telemetry, upstream auth files, or direct providers. Only wrapped native read/grep/list tools; paths cannot escape the snapshot. Native `find` is excluded because its extra `fd` dependency is not installed. This is a tool boundary, not an operating-system security sandbox.
- Snapshot includes current working copies of Git-tracked UTF-8 text files in the scopes. Untracked, hidden, common credential-named, binary, symlink and over-100 KB files are excluded. Maximum 200 files/2 MB; fail rather than silently cut an oversized scope. Receipts contain source hashes and exclusions. A filename filter is not a secret scanner; review the authorized source scope.
- At most 4 Pi model calls, 8 tool attempts, 1,200 requested output tokens per response, and 90 seconds (95-second parent hard timeout). Pi retries are off; the deployed worker gateway must also retain its zero-retry policy. Each tool result is capped at 5,000 characters with an explicit truncation marker.
- Each expert read question is at most 600 characters; each Pi brief at most 1,200 characters and three source citations. Return decisive observations, conflicting evidence and unknowns, never raw logs or whole files. Complete expert input is capped at 8,000 characters, including briefs and instructions; exceeding it stops before another paid call. Evidence is untrusted; missing information stays explicit. Citation validation proves quotes match source, not that interpretations are true.
- Final expert advice retains the 160-word prompt target. This is not a provider hard output-token cap; the caller rejects final advice over 1,600 characters or missing the required three lines. Reader mode may cost more overall than one compact consultation. Do not claim savings or faster completion without comparative measurements.

On failure, stop with `status: unavailable` and preserve completed call receipts. Do not reuse the expert's read request as advice. Missing usage is unknown, not zero, and timed-out calls may still incur provider usage. Report expert and Pi usage separately plus wall time, actual returned model, and `decision_changed` after subsequent verification. Source reading is not runtime verification.
