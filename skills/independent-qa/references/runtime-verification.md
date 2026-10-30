# Live runtime and browser verification

> On-demand reference for [Independent QA](../SKILL.md). Use this playbook to combine classical boundary-value test design with live runtime, server, and browser verification without leaving orphan processes.

## 1. Classical-first test backbone before visual or AI judgment

Before running subjective visual rubric checks or exploratory clicking, design a compact, deterministic test matrix from the specification:

- **Equivalence partitioning:** Group inputs into valid classes (typical user input, alternate supported formats) and invalid classes (malformed, unauthorized, wrong type) and test one representative case per partition.
- **Boundary value analysis (BVA):** Test exact boundaries (`0`, `1`, `max`, `max + 1`, empty string `""`, whitespace-only, `null`/missing, negative `-0` or extreme magnitudes like `1e21` where numeric contracts apply).
- **State transitions:** Verify state persistence across page reload, back/forward navigation, repeated submit/double-click, and error-to-recovery transitions.

Never substitute an LLM "looks good" opinion for a deterministic assertion when an exact status code, DOM state, or boundary output can be checked directly.

## 2. Ephemeral local server lifecycle and port isolation

When verifying a web UI, API, or desktop/CLI server locally:

1. **Pick a free ephemeral port:** Never hardcode default ports (`3000`, `8000`, `8080`) that may collide with the user's running services or return false-positive responses from a stale server. Bind to an unused local port (`127.0.0.1:<port>`) and verify nothing was listening on that port before launch.
2. **Isolate test state:** Point the server at a task-scoped SQLite file, temporary data directory (`tmp/<task-id>/data`), or seeded test fixture so QA actions never pollute user data.
3. **Wait for readiness probe:** Poll the health/root endpoint with a bounded retry loop (e.g., up to 15 seconds) and verify the response comes from the newly spawned PID before running browser checks.
4. **Guaranteed teardown (`try / finally`):** Always record the spawned process ID and kill the process tree in a `finally` block so no background server survives the turn:
   ```powershell
   $serverProc = Start-Process -FilePath 'node' -ArgumentList 'server.js', '--port', $port `
       -WorkingDirectory $appDir -PassThru -NoNewWindow
   try {
       # Run readiness check, functional/browser checks, and screenshot capture here
   }
   finally {
       if ($serverProc -and -not $serverProc.HasExited) {
           Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue
       }
   }
   ```

## 3. Live browser, viewport, and telemetry inspection

When changes affect rendered UI, layout, or client behavior:

1. **Exercise the real entry point:** Navigate through the actual user controls rather than calling internal functions from the console.
2. **Capture console and network errors:** Record any uncaught page exceptions (`pageerror`), `console.error` messages, and failed network requests (`HTTP >= 400` or CORS/asset load failures). A visually rendered page with broken console/network requests is **not** a clean pass.
3. **Inspect narrow and wide viewports:** Capture and visually inspect screenshots at both desktop (e.g., `1280×800`) and mobile/narrow (e.g., `390×844`) viewports when responsive layout matters, plus key interactive states (empty, loading, populated, error).
4. **Verify persistence:** After creating or mutating state in the UI, perform a full page reload and confirm the rendered state persists accurately.

## 4. Explicit limitations disclosure

Every runtime QA report must distinguish what was actually executed live from what remained mocked or unverified:
- Name the exact command, URL/port, viewport dimensions, and git tree/commit SHA inspected.
- If a live browser, external service, or device environment was unavailable, mark that lane **`UNVERIFIED`** with the exact blocker—never imply live runtime verification from static code reading or unit mocks.
