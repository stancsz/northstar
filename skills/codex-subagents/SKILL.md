---
name: codex-subagents
description: Coordinate bounded agent work when delegation helps; define ownership, authority, handoffs, and integration.
---

# Codex subagents

Use this skill in Codex or any other host; follow [host adaptation](../northstar/SKILL.md#use-with-other-agents).

Contents: [team](#plan-the-team), [capability/cost](#allocate-capability-and-cost), [capacity](#configure-codex-thread-capacity-and-delegation-depth), [authority](#roles-and-authority), [briefs](#task-brief-and-handoff), [coordination](#coordinate-to-a-working-result), [records](#documentation-and-repository-hygiene), [recovery](#failure-retries-and-final-integration).

Default to one owner. Delegate builders or reviewers only when required or when parallel/isolated execution clearly beats coordination and token cost. When delegating, use at most three levels: **Orchestrator** → **Supervisors** (0 or more) → **Workers**.

## Plan the team

1. Lock the requested outcome, constraints, and verification commands before dispatching.
2. Split only disjoint, bounded deliverables. Assign **one task and one exact write scope** per worker, with its own verification check.
3. Add a supervisor only when a multi-task workstream needs dedicated coordination; otherwise the orchestrator manages workers directly.
4. Apply Northstar's review threshold: the commander accepts small, reversible, attributable work directly from test/diff evidence; use one independent nonauthor reviewer ([Codex QA](../codex-qa/SKILL.md)) only when required. See [role profiles](references/role-profiles.md) and [agent handoffs](references/agent-handoffs.md).

## Allocate capability and cost

Follow the [Northstar delivery contract](../northstar/SKILL.md#delivery-contract).

- **Model routing:** Default bounded worker execution to a fast, capable model via local Subroute (`http://127.0.0.1:4000/v1`), using the dynamic `default` alias or an explicit endpoint-supported model ID/alias via `-Model` (e.g., MiniMax, Luna, or Gemini aliases configured on the gateway). Reserve heavy reasoning or [Codex Advisor](../codex-advisor/SKILL.md) for architecture forks, hard blockers, or visual judgment.
- **Parent owns route setup:** Verify any new/reconfigured route and tool roundtrip once before dispatch, keep credentials process-scoped, and pass the verified smoke evidence (`endpoint`, `model`, `marker`) in the worker brief so the worker never repeats route checks. Never silently switch providers on failure.
- **CLI dispatch:** Follow [local CLI dispatch](references/cli-dispatch.md) (`Invoke-CodexChild`). For effectiveness comparisons, use [skill-effectiveness receipts](../codex-qa/references/skill-effectiveness.md) and [configuration comparisons](references/cli-dispatch.md#configuration-comparisons).

## Configure Codex thread capacity and delegation depth

Use the host's existing capacity unless parallel work requires adjustment; see [optional host capacity](references/cli-dispatch.md#optional-host-capacity). Never modify global config just to start a routine task.

## Roles and authority

Under [Northstar ownership](../northstar/SKILL.md#ownership-north-star--goals--tasks), map **orchestrator → direction, supervisor → one goal, worker → one task** to existing project records. One commander owns covered approvals; subdelegated tasks carry that standing grant so workers never open a second approval queue. Independent review stays outside authorship.

### Orchestrator
- Owns user intent, cross-goal interfaces, team shape, and final integration.
- Sets each delegate's exact writable paths, forbidden paths, verification command, and deadline.
- Exercises the standing grant for covered actions and escalates only genuinely missing authority or user-retained decisions.

### Supervisors
- Own one workstream, keep worker write scopes disjoint, and inspect worker handoffs against acceptance criteria.
- Resolve internal workstream dependencies and escalate cross-goal tradeoffs to the orchestrator with a recommendation.

### Workers
- Complete **one assigned task** strictly inside the assigned write paths and authorized side effects.
- Do not spawn nested agents, edit outside scope, or broaden the task.
- If blocked, report the exact dependency and finish any independent in-scope work.

When peers disagree on an interface, route to the approval owner via a compact [decision exchange](../northstar/references/operating-system.md#resolve-disagreement) or consult [expertise](../northstar/references/operating-system.md#bring-in-expertise).

## Task brief and handoff

Every worker brief must be self-contained so a fast model can execute without rediscovery:

```markdown
- Outcome & Why: [Single deliverable and its purpose]
- First Action: [Exact file to read/edit or command to run first]
- Write Scope: [Exact allowed file paths + tmp/<task-id>/ scratch; all other paths read-only]
- Context & Baseline: [Relevant facts, verified route/model smoke, baseline test/error]
- Verification: [Exact command that must pass before handoff]
- Bounds: [5-min artifact checkpoint, 10-min handoff deadline, max 5 read-only calls before first edit/check, no nested CLI]
```

- **Search & output discipline:** Exclude generated/log/cache directories from searches, cap command output, and read focused line ranges.
- **Native tools only:** Codex CLI workers must use their native tools (`command_execution`, `file_change`), never nested `codex exec` or parent wrappers.
- **Required handoff:** Return `Artifact/paths changed`, `Checks run & results`, `Unmet/unknown items`, and `Next action` (plus failure/recovery count if any).

## Coordinate to a working result

1. **Split only disjoint work:** One writer per file scope.
2. **Verify after process exit:** Wait for process completion (`turn.completed` and exit code `0`) before inspecting captured JSONL streams, diffs, and test outputs. Never judge a stream while it is still being written.
3. **Carry recovery counts:** Workers own local fixes (up to 2 attempts); supervisors/orchestrator resolve cross-scope blockers and verify the old writer stopped before reassigning scope.
4. **Integrate against full acceptance:** Check the combined result against the full `Ask`.

## Documentation and repository hygiene

Follow Northstar's [repository rules](../northstar/SKILL.md#keep-records-and-the-repository-small): update existing records only at material decisions and handoffs, keep one editor per shared file, and use `tmp/<task>/` for disposable outputs.

## Failure, retries, and final integration

Delegation never weakens acceptance or resets the 2-strike recovery count. If CLI dispatch fails, continue directly in the parent within authority or report the exact route blocker using Northstar's [delivery loop](../northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments) and [stall recovery](../northstar/SKILL.md#recover-from-a-stall).
