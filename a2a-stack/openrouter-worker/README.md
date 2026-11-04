# Isolated Codex CLI worker (draft)

**Not the current default:** The owner switched Codex workers back to the local
LiteLLM profile at `http://127.0.0.1:4000/v1`. This OpenRouter experiment is retained as
a draft; do not use it for default dispatch.

The supervisor keeps its existing Codex session. This launcher starts a separate
Codex CLI process using a temporary Codex home and an explicitly selected
OpenRouter Responses provider. It requires `OPENROUTER_API_KEY` to already exist in
the launcher's environment; it does not read credential files or print the key.
Never replace a failed CLI dispatch with a subscription-backed native subagent.
Specify the intended native CLI executable explicitly; on Windows this must be
an `.exe`, not a shell wrapper. The installed `codex` wrapper and PATH
`codex.exe` were observed to report different versions, so do not infer that
they are interchangeable. Check the selected executable's version first.
Provider settings are also passed as CLI overrides to take precedence over
workspace configuration. The worker defaults to `minimax/minimax-m3.1-flash`;
`--model` overrides it explicitly. The supervisor keeps its own model selection.
Request and stream retries use the documented Codex defaults explicitly, so a
project configuration cannot silently disable them. These per-request limits do
not implement goal-level recovery; resuming after a terminal CLI failure remains
unimplemented and must not blindly repeat an uncertain write. This draft uses
`--ephemeral` and deletes its temporary Codex home, so it does not retain a CLI
session for resumption. Its JSONL receipt alone cannot recover that session.
The CLI is instructed to exclude the key from model-launched shell commands.
This setting is unverified against a live CLI worker, and it is not a complete
security boundary: other process inspection, inherited integrations, prompt
content, and receipt files require their own controls.
On Windows the isolated home selects the `elevated` Windows sandbox
implementation, matching the existing host configuration. This is a sandbox
implementation, not a request to run the worker unsandboxed. Sandbox setup and
the actual effective permissions still depend on the host's policy.

This adapter is not installed into Codex Desktop. Verify the real API route,
sandbox, and billing before relying on it for work. The earlier rejected
credential-reading command targeted Badlands, not this OpenRouter route.

From a separate PowerShell process with an authorized credential already injected:

```powershell
python a2a-stack/openrouter-worker/launch.py --workdir D:/github/northstar `
  --assignment D:/path/to/assignment.txt --receipts D:/northstar-artifacts/a2a-stack/worker-receipts `
  --codex-executable D:/path/to/codex.exe --sandbox read-only --disable-plugins
```

Supply a model actually available to the account. For an authorized edit use
`--sandbox workspace-write`, name exact allowed paths in the assignment, and
independently inspect changes; the sandbox is not a per-path allowlist. The
`--disable-plugins` option is only for tasks that need no plugin integration.
launcher writes JSONL and stderr receipts, which can contain task data; protect
and retain them accordingly. It does not impose a fixed worker deadline. It rejects nonzero exit, a timeout, invalid events,
a missing `turn.completed` or final message, and failed file changes. A successful
receipt does not prove correct work or billing. On timeout the launcher requests
termination of the process tree and reports unverified cleanup if that request
fails. A local synthetic parent/child test passed in one run, but a subsequent
independent run under a restricted Windows sandbox failed to confirm tree
termination and encountered a locked test log. Cleanup of actual sandbox
descendants remains unverified. Do not use this draft for unattended write work
until that real path is verified. Inspect the final
handoff and actual tool events, confirm the exact changed paths, and match the run
to an OpenRouter request/usage record. Verify that the supervisor's session and
model remain unchanged. Do not claim successful routing without that evidence.
