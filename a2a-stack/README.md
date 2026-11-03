# Northstar A2A stack

Reusable local stack under `D:\github\northstar\a2a-stack`. Coding uses the installed **Claude Code** harness; formal agent transport uses the **official A2A Python SDK 1.3.0**. MCP is a tool-facing facade over A2A, not a replacement for it.

**Current direction: [main-agent selected dynamic A2A teams](docs/DYNAMIC-WORKFLOW.md).** The main agent chooses a template or custom roster and creates per-run role agents/assignments. The original single registered-job endpoint is a compatibility and diagnostic route. Fixed delivery/supervisor timers are optional entry points, not the team architecture.

**[中文启动与 MCP 操作指南](docs/SETUP.md)** · **[自主完成契约](AUTONOMY.md)**

Human interaction is goal-bounded: `set_goal` starts a persistent main agent; `get_goal_report` presents the verified result; the human chooses the next goal. Within the goal, the harness handles native retry, context/process recovery and independent acceptance. Two real local goals completed, including one transient verifier failure and one controller-crash recovery without corrective intervention. Evidence is stored outside Git; see the [evaluation storage index](../docs/evals/a2a-stack/README.md) for scope and local archive location.

```text
Codex / Claude Code (MCP client)
          ↓ MCP Streamable HTTP
Docker Compose MCP gateway
          ↓ A2A JSON-RPC 1.0
Host A2A service → registered Claude Code / check job
          ↓ task status + artifact
Independent QA → exact candidate acceptance
```

## Current topology

Hybrid by design: the MCP gateway is containerized; A2A/Claude Code stays on the Windows host to preserve its existing configured model/authentication without copying credentials into an image or container. Docker-to-host loopback reachability has been tested here. This is not a claim that all components or credentials are containerized.

Local-only, single project owner. No authentication has been added to the loopback service; do not expose it on a public interface. HTTP may name only a locally registered job; it cannot supply an arbitrary executable, command or prompt. Trusted owner-created job files still carry code-execution authority.

## Host setup

Run from the Northstar root:

```powershell
Set-Location D:\github\northstar
uv venv tmp\a2a-stack\venv
uv pip install --python tmp\a2a-stack\venv\Scripts\python.exe -r a2a-stack\requirements.txt
tmp\a2a-stack\venv\Scripts\python.exe a2a-stack\agent\service.py
```

Keep the server command alive in a terminal or a Codex exec session. In Codex, retain its returned session ID; starting a detached child and letting its owning tool job exit is not reliable in this host. The service holds `tmp/a2a-stack/control/owner.lock` for its lifetime. Stop it with Ctrl+C in that terminal/session after confirming active work can end.

For a persistent per-user Windows entry point, install the logon task after setting up the venv:

```powershell
& .\a2a-stack\agent\install-host-task.ps1
# Only after the old foreground service has stopped and all active work is reconciled:
Start-ScheduledTask -TaskName Northstar-A2A-Host
```

The installer registers without starting by default. It uses this user's interactive login and `pythonw.exe`, no runtime deadline, continues on battery and ignores overlapping starts. Run the same installer again to restore its intended settings; it refuses to replace a different owner/action. Background startup messages go to `tmp/a2a-stack/control/host-service.log`; task evidence stays in `tmp/a2a-stack/tasks/`. Logon startup requires this user to log in. Per-role SQLite stores preserve A2A task history; startup recovery reconciles interrupted tasks with process identity and receipts before continuation. To stop deliberately, reconcile active work and disable the health trigger before stopping the scheduled task, as described below.

`A2A_WORKSPACE` can explicitly select the repository a job may access; default is the Northstar root. State remains under Northstar's `tmp/a2a-stack/`, separate from the target repository. Only one service/broker may hold this stack's execution lock. The installed host task also has an indefinite one-minute health trigger: IgnoreNew preserves a running service, and a dead service is started again. For maintenance, disable the host Scheduled Task before stopping it; re-enable it afterwards.

## Registered jobs

Owner creates `tmp/a2a-stack/jobs/<name>.json`. The A2A message is text containing `{"job":"<name>"}`. Example check job:

```json
{"mode":"check","command":["python","-c","print('local check')"]}
```

Claude job:

```json
{"mode":"claude","prompt_file":"tmp/a2a-stack/assignments/task.txt","tools":["Read","Edit","Write","Bash"],"permission_mode":"acceptEdits"}
```

Prompt paths/cwd must stay under the configured workspace. Fill exact write scope, baseline and acceptance in each prompt; tool allowlists are not path sandboxes. A2A does not grant access beyond the assigned job. Preserve the target project's rules and evidence boundaries.

**Latest owner instruction:** do not impose money, turn-count or elapsed-work ceilings. Default jobs have no execution deadline and pass no `--max-turns` or `--max-budget-usd`. Explicit operational timeouts remain available for deliberate test fixtures. Cancellation, process cleanup and truthful error reporting remain. A network observation timeout does not mean that the job stopped; query its original task ID.

## Protocol check

An independently downloaded/checksum-verified official CLI is currently at `tmp/a2a-stack/tools/a2a.exe` (v0.3.1). It is a local tool artifact, not vendored into Git.

```powershell
tmp\a2a-stack\tools\a2a.exe card get http://127.0.0.1:18890 -o json
tmp\a2a-stack\tools\a2a.exe send -a http://127.0.0.1:18890 --async '{"job":"your-job"}' -o json
tmp\a2a-stack\tools\a2a.exe task get -a http://127.0.0.1:18890 TASK_ID -o json
tmp\a2a-stack\tools\a2a.exe task cancel -a http://127.0.0.1:18890 TASK_ID -o json
```

Never resend a write job just because polling timed out: query the original task ID first. The official SDK DatabaseTaskStore now persists each agent's protocol history/artifacts in SQLite. Startup detects interrupted native workers; a live survivor is monitored until it finishes, and interrupted work is exposed to the autonomous controller for safe continuation. The goal/session journal also persists. Completion of an A2A task means the configured job completed, not independent QA or the project's goal passed.

## Compose / MCP

The running Docker gateway has passed actual five-tool tests through the real host A2A service. Claude Code has also called its MCP discovery tool successfully. Start the gateway:

```powershell
docker compose -p northstar-a2a -f a2a-stack/compose.yaml up -d --build
```

Connect Claude Code without changing global settings:

```powershell
claude --mcp-config a2a-stack/mcp/client-config.json --strict-mcp-config
```

MCP endpoint: `http://127.0.0.1:18892/mcp`. A container healthcheck does not establish project acceptance. The hybrid topology and in-memory task-store limitations above still apply.

## Acceptance and current goal

Role prompts are in [prompts/](prompts/): delivery owner, Claude worker, independent QA and read-only supervisor. The owner runs **outside** the A2A worker queue (for example in this Codex chat). It selects an unmet goal criterion, registers a scoped Claude job, submits it through MCP, inspects its real changes, and sends the exact candidate to an uninvolved reviewer. Repairs repeat that same loop until acceptance.

Do not register `delivery-owner.md` as a Claude worker that submits and waits for another job on this same service: the single execution slot would wait on itself. A schedule submits a prepared worker job; it does not by itself supply goal decomposition or independent QA. Keep the owner and reviewer responsibilities explicit. Application acceptance boundaries still apply even with unlimited execution budget.

The optional Compose timer and its setup are documented in [scheduler/README.md](scheduler/README.md). Native Codex automations are paused backup entry points; their actual timed wakeup was not verified here. Do not run both clocks for the same role/job.

[Active work and evidence](../docs/goal/a2a-stack/GOAL.md). Original Instacart app fixes and app-specific evidence remain in that repository. Earlier CLI-only probes did not implement A2A and are not used as protocol conformance proof.

Runtime helper regressions:

```powershell
python -m unittest discover -s a2a-stack/runtime -p "test_*.py" -v
```

These use isolated fixture processes/control directories and do not prove real protocol behavior. Formal protocol, Claude, QA, MCP and scheduled-entry evidence must be inspected separately before claiming the workflow is complete.
