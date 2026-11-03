# Targeted MCP recovery / endurance-check review

## Scope and results

Reviewed current `a2a-stack/autonomy/runner.py`, `autonomy/test_runner.py`, and `tmp/a2a-stack/qa/council-review/check_endurance.py` (plus the immutable `check_ledger.py`). No product edits or live task/service/container mutations.

- Affected offline controller tests: **23/23 passed** with `python -B a2a-stack/autonomy/test_runner.py`; all fixture scratch is under `tmp/a2a-stack/qa/council-review/runner-fix`.
- The new owner path is ordered correctly: SDK `list_tools()` preflight happens before native Claude launch; unavailable/missing tools retry without starting the owner or calling the model supervisor. On a native `init` missing a required tool or reporting the gateway disconnected, the process is terminated through the `finally` Job cleanup, the same journal session is retained, and the controller re-enters preflight/resumes rather than treating an intermediate API retry as terminal.
- The cancellation path checks the cancel marker while waiting, cancels/joins the pending SDK probe, and raises `Canceled`. The init capability check requires the full 11 owner MCP tool names and, when `mcp_servers` metadata is present, requires the named server to be connected. The SDK probe strips the configured server prefix by using raw tool names from `list_tools()`.

## Must fix before trusting endurance completion receipts

`check_endurance.py:38-48` binds `progress.json` to `source_sha256` but always reuses the single `STATE/ledger.sqlite` path (`:45`). If the source hash changes, progress counters reset while the old database is retained; the script then requeues `soak-0..5` rows from that previous run and consumes them alongside the new candidate's work. This mixes candidate versions and can inflate `completed_tasks` or make schema/queue state from an earlier revision affect the new two-hour result. The same cache check does not bind the endurance checker or immutable `check_ledger.py` hash, so edits to those tests can reuse a prior completion record for the same product source.

**Required correction:** key both database and progress/receipt by a manifest containing the target source SHA plus `check_endurance.py` and `check_ledger.py` SHA-256 values (or refuse reuse when any differs). Start a fresh isolated DB for each exact manifest; only resume a prior DB whose entire manifest matches. Record the manifest in the final completion receipt and verify it on the cached-complete path.

This is a defect in the test artifact’s evidence binding, not in the MCP preflight code. Do not accept a reported two-hour endurance pass until the checker is corrected or the evidence is independently rerun against an exact manifest.

## Revision binding

- `a2a-stack/autonomy/runner.py`: `369F8D3E2765E01088BDD85BD2147F87C82131F65C178F0EDF67AB1D03152DA3`
- `a2a-stack/autonomy/test_runner.py`: `019FF9E7DC6AC2F691AF5ED1FE450A09C0E1236E0C6E3CC05FB30682C2B38081`
- `tmp/a2a-stack/qa/council-review/check_endurance.py`: `871C6486E2CBFA3CC020734FED55A0D484B2A8B6BEA04D8693282B469B0D1ABA`
- `tmp/a2a-stack/qa/council-review/check_ledger.py`: `594CB42A3F51E354AC68ABDB4CB7FC4E998217C00E0A58ACB73080FF476CF480`
