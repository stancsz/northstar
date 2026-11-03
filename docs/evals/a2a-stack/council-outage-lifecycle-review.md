# Read-only lifecycle review: active Goal during host + MCP outage

## Scope and result

Reviewed the current local lifecycle in `a2a-stack/autonomy/manager.py`, `autonomy/runner.py`, `agent/task_store.py`, `agent/service.py`, `mcp/gateway.py`, `compose.yaml`, and `agent/install-host-task.ps1`. No source, process, container, Goal, or scheduled task was changed. The live interruption Goal is owned by the parent and was not touched.

**No concrete data-loss or Goal-loss defect was established from source inspection.** The recovery chain is coherent for process-death failures: the host task starts the A2A service; service lifespan starts each nonterminal Goal; `GoalManager` owns the controller process tree; SQLite persists per-agent A2A task records; task-store startup checks native process identity and fails interrupted work with a receipt; the controller resumes the persisted native session and reconciles its assignments before continuing. The current integration exercise is the right way to prove the whole chain.

## Concrete low-interference gap

`GoalManager.startup()` immediately launches every nonterminal controller (`autonomy/manager.py:220-226`) without checking that the MCP gateway is reachable. The native owner is configured for `http://127.0.0.1:18892/mcp` (`autonomy/manager.py:119-122`, `mcp/client-config.json`); the owner invokes Claude immediately (`autonomy/runner.py:317-320`). If the host service restarts before the gateway is available, tool failures go through the supervisor and the unbounded recovery loop; the only local pacing after an error is `pause(.2)` (`autonomy/runner.py:522-588`). This should preserve the Goal and avoid `NEEDS_USER` for ordinary transport failures, but it can create repeated model calls while the required MCP path is down. This is a confirmed code path and a resource/interference risk, not evidence that a Goal is lost.

The gateway is configured with `restart: unless-stopped` and a TCP-only healthcheck (`compose.yaml:16-23`). That covers container process exit when Docker is running and the container was not deliberately stopped. It does not establish a responsive MCP endpoint, and Compose restart policy does not restart a process solely because its health status is unhealthy. The Windows task likewise has logon and one-minute starts with `IgnoreNew`; it supervises the host process rather than probing A2A/MCP readiness (`install-host-task.ps1:32-42`). If the Docker daemon is unavailable, the gateway has no running local agent that can restore it. These are deployment boundaries; behavior for an actual daemon stop or a live-but-unresponsive gateway was not tested here.

## Recovery mechanisms verified by inspection

- The controller and native Claude/check children are placed in Windows Job Objects before they run (`runtime/runner.py:116-130`, `autonomy/manager.py:181-198`, `autonomy/runner.py:201-218`, `agent/service.py:388-408`). Closing the owning job object kills its child tree.
- The Goal journal persists immutable spec identity and native session state; controller startup resumes the same session (`autonomy/runner.py:157-180`, `317-320`). `GoalManager.startup()` starts nonterminal goals after host restart.
- Each root/role SDK handler uses its own SQLite `RecoveringDatabaseTaskStore` (`agent/service.py:601-650`). On first access it marks orphaned active tasks FAILED with durable receipts, preserves completed artifacts, and monitors any identity-matched survivor (`agent/task_store.py:106-167`).
- The owner prompt requires it to reconcile task IDs before a continuation; the candidate guard rejects active/unknown coder tasks and requires completed goal-bound producer provenance (`autonomy/runner.py:352-375`, `418-491`).
- A tool outage is not an eligible user blocker by text alone; external escalation requires verified native auth metadata or an exact missing registered input/user gate (`autonomy/runner.py:500-518`, `575-588`).

## Decisive experiment invariants

The parent’s active `g-24f186b05bc14f76bcc743622a04c796` exercise has a sound, scoped immutable check (`tmp/a2a-stack/qa/council-review/check_ledger.py`) and a suitable write scope of `tmp/council-delivery/ledger.py`. For a clean acceptance record:

1. Snapshot the immutable spec digest, Goal ID, owner session ID, selected stack/role assignment IDs, original A2A task IDs, and process identity tokens before fault injection.
2. Wait until an actual coder assignment is bound and its native process identity is recorded. Kill only the exact host service process after recording its identity. Make the gateway unavailable at the same time; do not issue `set_goal`, `resume_goal`, replacement `submit_job`, or task cancellation.
3. Prefer holding the gateway down until the new host process and same Goal controller are observed. Confirm the controller remains active/recovering under the same Goal ID/spec/session and does not convert transport errors to `NEEDS_USER`. Record whether MCP calls repeat during this interval; repeated attempts are a low-interference result even if the eventual Goal succeeds.
4. Restore MCP without changing the Goal. Require the same Goal to resume from the original assignment/task history; if the original coder child died, its original task should become terminal FAILED with receipt before a continuation is submitted. No overlapping writer task may remain active.
5. Accept only after `COMPLETE` is bound to a fresh exact candidate, all four immutable host tests pass, independent reviewer returns READY, only `ledger.py` is changed, and no provider/manual correction was sent. Preserve old-task terminal evidence and the final assignment/producer/review bindings.

The current plan (observer kills the host and restarts the gateway while the scheduled health trigger restarts host) can prove recovery. If gateway restart occurs immediately, it will not characterize behavior while the restarted host is waiting on an unavailable MCP endpoint; that observation is the one useful extension.

## Revision binding

- `autonomy/manager.py`: `CFCF8BA9DF215324E0FFA6532D635564FB227B862235F760DE93CB4829CC82F3`
- `autonomy/runner.py`: `88BD7D40C1557CE2CC87F57AB0F47C38BD0C3B6E454193777CD33D31FD541922`
- `agent/task_store.py`: `FD86222E696B59AA79B8A25E342D160C0F49C6A409E149C615B440C7ED8B0C0F`
- `agent/service.py`: `54F38EB0C7A21ACC575EAB8139E92534123F982152A231D365BEE934FAB5CA60`
- `mcp/gateway.py`: `BC12C57C5F740EDA113B36629EE42A0E682BBABE655329B85276170D0383D334`
- `compose.yaml`: `C2E0A2D6BD2A8F800F351D4691CD85A77C0D42B7F0D853B9091282E29FE9A830`
- `agent/install-host-task.ps1`: `883108FD5E6F614B556F6643F6311E108D41C7F07ACFB4B4A9FBEB7CE8C35923`

**Verdict:** source path is plausible for crash recovery, but full host+MCP outage recovery and low-interference behavior remain unverified until the live Goal completes with the invariants above. This review does not re-certify the full stack or substitute for the unavailable advisor-council response.
