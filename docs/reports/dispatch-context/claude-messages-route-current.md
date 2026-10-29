# Claude Messages route evidence

The parent sent one synthetic HTTP request to `POST http://127.0.0.1:4000/v1/messages?beta=true` with model alias `default`, authenticated to the gateway using the parent-only `GATEWAY_MASTER_KEY` as `x-api-key`. It returned HTTP 200 and the exact requested unique response. The secret, marker, response body, and authorization header are not recorded.

This establishes only that the current endpoint/path and `default` alias worked for that parent-authenticated request. It does not establish that a task-scoped virtual key works, that Claude Code works, or that Claude's native Read/tool-result roundtrip passes. Do not map the master key into Claude or treat direct HTTP success as a Claude CLI pass.

An earlier task-keyed Claude CLI request to the same Messages path returned 404. This remains a separate historical CLI observation; it is not superseded as a CLI result by the parent's HTTP 200. The CLI virtual-key gate and native tool-result gate remain open. If another CLI 404 occurs, record the redacted URL, status/body, and key metadata, then stop without changing model, provider, or endpoint.
