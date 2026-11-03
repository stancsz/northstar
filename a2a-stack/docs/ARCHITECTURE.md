# Why A2A + MCP + Compose

## Decision under test

Keep Claude Code as the coding harness. Use the official A2A SDK for agent discovery, task lifecycle and artifacts; expose a small MCP facade for coding assistants. Compose manages the facade's process/network/health lifecycle. These are complementary boundaries, not three competing agent frameworks.

The first operational topology is hybrid: MCP gateway in Docker, A2A/Claude on the Windows host. This preserves the installed Claude configuration without copying authentication into a container. An actual Docker probe reached a host loopback health endpoint through `host.docker.internal`. Client-side advertised A2A URLs must be remapped explicitly to this configured upstream; `127.0.0.1` inside a container names that container.

This does not make all components containerized or the workflow durable across every failure. The current SDK TaskStore is in memory; server restart loses task history. Do not re-run write tasks blindly after a timeout/restart. Always reconcile the task ID, candidate files and execution receipt first.

## Reused components and limits

| Component | Role | Limit |
| --- | --- | --- |
| Claude Code CLI | File/tools/model loop using the existing configured route | Code-completion success is not independent QA; tool allowlists are not a path sandbox |
| a2a-sdk 1.3.0 | Formal A2A JSON-RPC 1.0 server/client, task model, routes | Business authorization, write scope and acceptance remain ours |
| Official a2a-cli 0.3.1 | Independent discovery/send/get/cancel interoperability client | Its exec demo mode is not our long-running production server |
| Official MCP Python SDK 2.3.0 | Tool discovery/calls over Streamable HTTP | MCP alone does not define project goals or guarantee agent-task completion |
| Docker Compose | Isolated facade startup/network/health/restart | A healthy container is not protocol or code acceptance |

ADK/LangGraph remain options if actual orchestration/persistence needs justify them. Community bridges inspected were either tied to a pre-1.0 A2A SDK or a small first release with conformance/auth caveats. Current choice is a thin adapter on official SDKs, not an assertion that an entire new platform is needed.

## Acceptance boundary

Native `system/api_retry` is an intermediate recovery event. The adapter logs it and lets Claude's own retry policy continue; final error results and failed processes remain failures. Both success and abnormal termination must leave terminal receipts. See [official headless retry semantics](https://code.claude.com/docs/en/headless#handle-api-retries).

Actual tests must cover discovery → send → task query → artifact, malformed/unknown inputs, failed job, timeout, active and queued cancellation without killing another task, real Claude work, independent QA/candidate binding, and MCP calls through the running container. Echo, static schemas, unit fixtures, HTTP 200 or a worker's prose are insufficient alone.

## Primary references

- [A2A official project](https://github.com/a2aproject), [protocol](https://a2a-protocol.org/latest/), [Python SDK](https://github.com/a2aproject/a2a-python).
- [A2A CLI](https://github.com/a2aproject/a2a-cli), [exec-mode limitations](https://github.com/a2aproject/a2a-cli/tree/main/examples/01-exec-demo).
- [Claude Agent SDK / Claude Code distinction](https://code.claude.com/docs/en/agent-sdk/overview).
- [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture), [official Python SDK](https://github.com/modelcontextprotocol/python-sdk).
- [Docker Compose uses](https://docs.docker.com/compose/intro/features-uses/).

Research checked 2026-11-02; framework recommendations are project judgments. Live acceptance status is maintained in the goal, not inferred from these links.
