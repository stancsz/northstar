# Codex Badlands subagent experiment (historical)

This note records a local routing experiment, not an operating guide. Its
provider, profile, and command details are historical and must not be used as
current routing instructions. Follow [AGENTS.md](../../AGENTS.md) and the
[current LiteLLM routing note](litellm-routing.md) for Northstar workers.

## What the experiment observed

A local loopback simulation used separate mock `/subscription/v1/responses`
and `/badlands/v1/responses` endpoints. In that simulated run, the parent
requests and dispatcher turn reached the subscription mock, while an isolated
CLI child reached the Badlands mock and returned a successful workspace-write
result. This supports only the bounded observation that the tested process
chain routed those requests to those local mock endpoints.

It did not contact or validate the real Badlands provider, establish real
credentials, model availability, billing or subscription consumption, or prove
Codex Desktop UI behavior. The mock response trace is not independent provider,
billing, or Desktop evidence. Historical setup and workaround details are
intentionally omitted.

The experiment raised a useful architectural question—whether a worker can use
a distinct route while the supervisor retains its own route—but its specific
configuration and conclusions are superseded. Do not infer current Northstar
worker behavior from this record.
