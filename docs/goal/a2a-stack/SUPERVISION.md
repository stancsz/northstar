# Supervisor direction

The user authorized the main chat to check three Workers every 15 minutes, review actual results, correct drift and assign distinct useful `/goal` increments toward [NORTHSTAR.md](../../../NORTHSTAR.md). Each Worker should hold one actual active host goal while its assigned work remains unfinished.

- Main chat: `01a1a2d2-5a91-7381-9559-6a808135b144`.
- Worker: `01a19d53-7d62-7c92-abc7-ff1533947e0b`, local host.
- Worker 2: `01a1a300-69fb-7c90-a886-3eddc08cecd0`, local host; private scope-admission candidate under `D:/northstar-artifacts/a2a-stack/worker-2/`.
- Worker 3: `01a1a300-9454-77d0-8770-994c8462a9ba`, local host; private checkpoint-contention candidate under `D:/northstar-artifacts/a2a-stack/worker-3/`.
- Reuse automation `instacart-2` to wake the main chat. Worker executes; it does not create a competing supervisor schedule.
- The main chat alone maintains the [external supervisor checkpoint](D:/northstar-artifacts/a2a-stack/supervision-checkpoint.md), including cursors, dispatch/acceptance decisions, receipts and timed-wakeup evidence.
- Worker maintains its [external framework checkpoint](D:/northstar-artifacts/a2a-stack/northstar-a2a-progress.md). The application-load journal remains external evidence only. Both roles preserve existing authority and application restrictions.
- Every 15-minute review advances Northstar A2A capabilities, not Instacart product development. Each new goal must name a demonstrated framework gap and its distinguishing acceptance. Safely close active application-load tasks; do not keep finding application defects as the next-goal strategy.
- Prefer sending a concrete goal instruction that requires the Worker to call its own `create_goal` and verify with `get_goal`. Plain `/goal` text or an active chat is not sufficient proof; Computer Use is not the default.
- Prevent overlapping writes across source files, scratch, test state, process-local TEMP/TMP, ports and host operations. Worker 2/3 keep production source and live queues read-only. Accept exact candidates through nonauthor QA, then integrate serially against the latest baseline. If overlap appears, hold the conflicting write step, preserve both artifacts, assign one writer and reverify; never reset, clean or overwrite another worker to resolve it.
- Read current runtime and evidence before acting; do not equate a saved schedule or live process with successful autonomous delivery.

Storage policy and historical evidence are described in the [evaluation index](../../evals/a2a-stack/README.md). Do not append per-run observations or application artifacts to this repository file.
