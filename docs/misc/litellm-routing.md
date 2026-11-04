# Local LiteLLM routing

See the [dependency inventory](litellm-dependency-inventory.md) for the
configurable clients, exact identifiers and historical references.

For Northstar Codex CLI workers, the owner-selected route is the local LiteLLM
endpoint `http://127.0.0.1:4000/v1`, with model alias `default` and the
`GATEWAY_MASTER_KEY` supplied in the worker process environment. Use the
existing `subroute-subagents` Codex profile and explicitly override its base URL
to the endpoint above. The profile name is an existing configuration identifier;
it is not a second endpoint. The supervisor retains its own subscription and
model. Verify the effective route, sandbox and native tool execution before
relying on a worker; do not silently switch providers or use native
subscription-backed subagents as a fallback.

Advisor Council and its optional reader have separately configured endpoints and
credentials. To use the local LiteLLM route for an authorized Advisor call,
set `EXPERTS_BASE_URL` to `http://127.0.0.1:4000/v1` and provide the matching
`EXPERTS_API_KEY` in that process. If using the reader, set `READER_BASE_URL`
and `READER_API_KEY` as appropriate, or let it inherit `EXPERTS_BASE_URL`.
Select models supported by that endpoint. Endpoint compatibility, model
availability, authentication and actual execution must be verified separately;
this document does not change the user's global environment or establish live
Advisor functionality.
