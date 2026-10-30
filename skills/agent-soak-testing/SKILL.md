---
name: agent-soak-testing
description: Plan, run, and evaluate bounded repeated-use reliability and instruction-drift soak tests for agent harnesses and models.
---

# Agent Soak Testing

Use this skill when evaluating whether an AI agent harness, skill stack, or model stays reliable and resists instruction drift under repeated use over time. The [Soak framework](https://github.com/stancsz/soak) is a separate external runner; this skill provides evaluation guidance and does not install the runner or imply that a live target has been exercised.

1. **Define target and budget bounds first:** Name the exact agent harness, model, workload, environment, and pass/fail invariant. Lock authorized duration, request rate, concurrency, and spend ceiling before calling any paid or shared service. Never present synthetic or mock runs as real-system evidence.
2. **Design deterministic, sanitized cases:** Give each case a stable unique ID and explicit observable assertions (including tool use, state continuity, or multi-turn steering only when relevant). Strip secrets and sensitive data from all inputs and captured outputs.
3. **Verify adapter with a 1-run smoke:** Implement the runner's input/output adapter and pass one short smoke run against the actual target before starting repeated iterations. Separate `case_behavior`, `harness`, `adapter`, `route_or_auth`, and `timeout` failures in receipts.
4. **Enforce hard runtime and spend stops:** Run with explicit duration, per-call timeout, interval, and maximum iteration caps. Retain redacted configuration, target revisions, and environment metadata alongside JSONL event logs. Stop immediately on unexpected spend, retry storms, or loss of process control.
5. **Report time-series evidence honestly:** Inspect event streams for failure clusters, instruction drift, and latency changes over time. Report exact counts, elapsed time, versions, and gaps—never extrapolate a short smoke or small sample into a general reliability claim.
