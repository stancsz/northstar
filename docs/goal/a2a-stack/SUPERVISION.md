# Supervisor direction

The user authorized the main chat to check Worker every 30 minutes, review actual results, correct drift and assign the next useful `/goal` toward [NORTHSTAR.md](../../../NORTHSTAR.md).

- Main chat: `01a1a2d2-5a91-7381-9559-6a808135b144`.
- Worker: `01a19d53-7d62-7c92-abc7-ff1533947e0b`, local host.
- Reuse automation `instacart-2` to wake the main chat. Worker executes; it does not create a competing supervisor schedule.
- The main chat alone maintains the [external supervisor checkpoint](D:/northstar-artifacts/a2a-stack/supervision-checkpoint.md), including cursors, dispatch/acceptance decisions, receipts and timed-wakeup evidence.
- Worker maintains its [external framework checkpoint](D:/northstar-artifacts/a2a-stack/northstar-a2a-progress.md). The application-load journal remains external evidence only. Both roles preserve existing authority and application restrictions.
- Every 30-minute review advances Northstar A2A capabilities, not Instacart product development. Each new goal must name a demonstrated framework gap and its distinguishing acceptance. Safely close active application-load tasks; do not keep finding application defects as the next-goal strategy.
- Read current runtime and evidence before acting; do not equate a saved schedule or live process with successful autonomous delivery.

Storage policy and historical evidence are described in the [evaluation index](../../evals/a2a-stack/README.md). Do not append per-run observations or application artifacts to this repository file.
