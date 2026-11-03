# MCP gateway (HYBRID topology)

This directory holds an **MCP facade** in front of the official-SDK A2A host
worker that runs on the Windows host (`a2a-stack/agent/service.py`). The
gateway exposes legacy task operations and dynamic stack control over streamable HTTP.

## Hybrid, not fully containerized

This is a **hybrid** deployment and is deliberately **not** a fully
containerized stack:

- The **MCP gateway runs in a container** (`mcp-gateway` service, built from
  `docker/Dockerfile.gateway`, published on `127.0.0.1:18892`).
- The **A2A agent and Claude Code run on the host**, because the host keeps
  the current authentication and credential environment (Claude Code CLI
  login, `~/.claude` state, MCP client configuration). Nothing in this change
  alters that auth path.

The container talks to the host over `host.docker.internal:18890`. Only the
gateway container is created; the host worker is started and supervised
separately.

## Tools

| Tool | Purpose |
| --- | --- |
| `discover_agent` | Fetch the upstream A2A agent card, retargeted at the configured upstream. |
| `submit_job(job_name)` | Submit a **registered** local job by name; returns the A2A task id. |
| `get_task(task_id)` | Poll one A2A task. Long-running jobs are polled with this tool. |
| `cancel_task(task_id)` | Cancel one A2A task. |
| `list_tasks` | List upstream tasks with artifacts. |
| `list_templates` | Discover available team recipes and profiles. |
| `create_stack` | Let the main agent select a template/custom roster for this run. |
| `list_stacks` / `get_stack` | Inspect chosen role endpoints and assignment/task bindings. |
| `create_assignment` | Create one scoped task instance under a chosen stack role. |

The five task operations accept optional `stack_id` and `role_id` together.
These select that role's actual Agent Card and SDK endpoint. Omit both for
the original diagnostic agent. See [dynamic workflow](../docs/DYNAMIC-WORKFLOW.md).

### Trust boundary

The upstream URL comes only from `A2A_URL`. Dynamic calls accept goal/task
text and a validated workspace/scope; trusted host profiles choose tools and
the Claude harness. Callers cannot supply executables, model overrides,
arbitrary agent URLs or CLI flags. `submit_job` names an assignment created
for that role. The original job registry remains for diagnostics.

Upstream URLs advertised in the agent card are rewritten to the configured
upstream scheme/netloc while preserving the exact path, because the host card
advertises `127.0.0.1`. Cards that are not A2A JSONRPC protocol version `1.0`
are rejected. Errors propagate as tool errors; the gateway never fabricates a
successful result.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `A2A_URL` | `http://127.0.0.1:18890` | Upstream A2A agent. Compose sets `http://host.docker.internal:18890`. |

## Running

```bash
docker compose -f a2a-stack/compose.yaml up --build -d
```

The host A2A worker must already be running on port `18890`; the gateway will
fail its tool calls if the upstream is unreachable.

## Healthcheck caveat

The Compose healthcheck is a **TCP connect to port 18892 only**. It proves the
process is listening — it is **not** protocol evidence. It does not verify that
the MCP session initializes, that the tools list, or that the upstream A2A
agent is reachable. Use an MCP client handshake and a real `discover_agent`
call for that.

## Transport security

The MCP transport is bound with `TransportSecuritySettings` allowing only
`127.0.0.1:*`, `localhost:*` and `mcp-gateway:*` hosts, and
`http://127.0.0.1:*` / `http://localhost:*` origins. The container port is
published on loopback only.

## Requirements

`mcp/requirements.txt` pins the same SDK versions the host uses:
`mcp==2.3.0`, `a2a-sdk[http-server]==1.3.0`.
