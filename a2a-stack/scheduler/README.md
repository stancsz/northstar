# Compose interval scheduling

The topology is Docker APScheduler → MCP gateway → Windows host A2A service → Claude Code worker. Claude Code remains the registered delivery job's coding engine. Start the host service as described in the stack README before starting the gateway and timer.

Configure `DELIVERY_JOB` and/or `SUPERVISOR_JOB` with trusted gateway job names. Empty values disable those roles. The defaults are 3600 and 1800 seconds; these values select trigger frequency and do not limit a task's runtime, turns, or cost. The first dispatch happens only when the first interval trigger fires, never at container startup.

A reusable read-only supervisor job can be registered from the repository root:

```powershell
New-Item -ItemType Directory -Force tmp/a2a-stack/jobs | Out-Null
@'
{"mode":"claude","prompt_file":"a2a-stack/prompts/supervisor.md","mcp_config":"a2a-stack/mcp/client-config.json","tools":["Read"],"allowed_tools":["Read","mcp__northstar_a2a__discover_agent","mcp__northstar_a2a__list_tasks","mcp__northstar_a2a__get_task"],"permission_mode":"default"}
'@ | Set-Content tmp/a2a-stack/jobs/northstar-supervisor.json -Encoding utf8
$env:SUPERVISOR_JOB = 'northstar-supervisor'
$env:DELIVERY_JOB = ''
```

This checks goal/evidence/task state and returns an artifact; it does not send external notifications or dispatch another builder. For delivery, the owner first prepares a concrete scoped task prompt and registers its name, then sets `DELIVERY_JOB`. One registered delivery-job name means one explicitly assigned increment. After any terminal result, that name is consumed and will not be submitted again, including after `FAILED`, `CANCELED`, or `REJECTED`. To dispatch a new increment or retry, the owner must prepare and register it under a new job name/revision. Leave it empty when no authorized executable increment remains.

For the included 30-minute supervisor configuration, after registering that job:

```powershell
docker compose -p northstar-a2a --env-file a2a-stack/scheduler/example.env -f a2a-stack/compose.yaml --profile scheduled up -d --build scheduler
```

The stack's Compose file already includes this optional service:

```yaml
services:
  scheduler:
    build:
      context: ./scheduler
    profiles: [scheduled]
    environment:
      MCP_URL: ${MCP_URL:-http://mcp-gateway:18892/mcp}
      DELIVERY_JOB: ${DELIVERY_JOB:-}
      SUPERVISOR_JOB: ${SUPERVISOR_JOB:-}
      DELIVERY_INTERVAL_SECONDS: ${DELIVERY_INTERVAL_SECONDS:-3600}
      SUPERVISOR_INTERVAL_SECONDS: ${SUPERVISOR_INTERVAL_SECONDS:-1800}
    volumes:
      - scheduler-state:/state
    depends_on:
      mcp-gateway:
        condition: service_healthy
    restart: unless-stopped

volumes:
  scheduler-state:
```

Register trusted local jobs as described in the stack README, then select their names and start normal scheduling from `D:\github\northstar`:

```powershell
$env:DELIVERY_JOB = 'your-prepared-worker'
$env:SUPERVISOR_JOB = 'your-read-only-audit'
docker compose -p northstar-a2a -f a2a-stack/compose.yaml --profile scheduled up -d --build scheduler
```

For an operator-selected short interval while observing the timer:

```powershell
$env:DELIVERY_INTERVAL_SECONDS = '30'
$env:SUPERVISOR_INTERVAL_SECONDS = '30'
docker compose -p northstar-a2a -f a2a-stack/compose.yaml --profile scheduled up -d scheduler
```

The named `scheduler-state` volume stores atomic per-role JSON state and `events.jsonl`. Each interval first queries the persisted task ID. An active task is rejoined. Delivery terminal results are recorded with artifact evidence and the configured job name is consumed; a different delivery name is accepted only after the old task is reconciled terminal. Supervisor audits remain recurring: a terminal audit permits a later scheduled audit. Ambiguous submission or an unknown task after A2A server restart fails closed as `NEEDS_RECONCILIATION`; the scheduler does not blindly duplicate it. Events contain timestamps, role, configured job name, task ID, phase, and task status, not prompts or tool bodies.

The scheduler does not guarantee that the A2A host's task store survives a host restart. A running scheduler container and an `events.jsonl` trigger record alone do not prove that a task completed or produced an artifact; inspect the task ID and returned A2A artifacts as separate evidence.

Schedule **leaf jobs** only. The delivery owner and independent reviewer run outside this single worker queue; do not schedule an owner that submits another worker and waits for it from inside the same queue. A timer triggers prepared jobs; it does not itself select goal criteria or certify QA.

Inspect state and pause the timer without canceling the host's running task:

```powershell
docker exec northstar-a2a-scheduler cat /state/events.jsonl
docker exec northstar-a2a-scheduler cat /state/delivery.json
docker exec northstar-a2a-scheduler cat /state/supervisor.json
docker stop northstar-a2a-scheduler
```

After a short-interval test, restore 3600/1800 seconds or remove the interval environment overrides before recreating the service. Do not leave test jobs repeating. Preserve the volume; do not use `down -v` as recovery. For `NEEDS_RECONCILIATION`, first inspect original IDs, host receipts and changed files. Resume only after the owner has established whether the prior work ran; never erase ambiguous state to force a new submission.
