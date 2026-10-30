---
name: subagent-orchestration
description: Orchestrate bounded multi-agent work across native subagents, Codex CLI, and Claude Code CLI; manage role hierarchy, worktree isolation, route preflight, and integration.
---

# Subagent Orchestration

Use this skill across any agent host; follow [host adaptation](../northstar/SKILL.md#use-with-other-agents).

Contents: [team](#plan-the-team), [capability/cost](#allocate-capability-and-cost), [capacity](#configure-codex-thread-capacity-and-delegation-depth), [authority](#roles-and-authority), [briefs](#task-brief-and-handoff), [coordination](#coordinate-to-a-working-result), [records](#documentation-and-repository-hygiene), [recovery](#failure-retries-and-final-integration).

Default to one owner. Delegate builders or reviewers only when required or when parallel/isolated execution clearly beats coordination and token cost. When delegating, use at most three levels: **Orchestrator** → **Supervisors** (0 or more) → **Workers**.

## Plan the team

1. Lock the requested outcome, constraints, and verification commands before dispatching.
2. Split only disjoint, bounded deliverables. Assign **one task and one exact write scope** per worker, with its own verification check.
3. For parallel write workers or shared build/test outputs, isolate each worker using [Git worktree and changeset isolation](references/worktree-isolation.md) so concurrent edits never collide and reviews bind to exact tree SHAs (`git rev-parse HEAD^{tree}`).
4. Add a supervisor only when a multi-task workstream needs dedicated coordination; otherwise the orchestrator manages workers directly.
5. Apply Northstar's review threshold: the commander accepts small, reversible, attributable work directly from test/diff evidence; use one independent nonauthor reviewer ([Independent QA](../independent-qa/SKILL.md)) only when required. See [role profiles](references/role-profiles.md) and [agent handoffs](references/agent-handoffs.md).

## Allocate capability and cost

Follow the [Northstar delivery contract](../northstar/SKILL.md#delivery-contract).

- **Model selection:** Match capability to task difficulty. Default bounded worker execution to a fast, capable model (`--model` / `-Model` when overriding the host default), and reserve heavier reasoning or [Advisor Council](../advisor-council/SKILL.md) for architecture forks, hard blockers, or visual judgment. Never silently switch models on failure.
- **Unified route & environment preflight:**
  1. **Parent owns CLI verification:** Verify any new or reconfigured CLI setup once in the parent (1-turn read-only smoke) before dispatching write work, and pass the baseline context in the worker brief so workers never repeat setup checks.
  2. **Prevent profile model leakage:** When isolating child configuration (`CLAUDE_CONFIG_DIR`, `--bare`, `--setting-sources ""`, or custom `CODEX_HOME`), pass the intended model explicitly so user-profile defaults do not leak into or drop from the child run.
  3. **Stop immediately on retry storms or bad routes:** Terminate a CLI worker immediately on the first native `api_retry` (HTTP 429) or `unrecognized_model` event rather than burning budget in backoff loops.
- **CLI dispatch adapters:**
  - **Codex CLI workers:** Follow [local Codex CLI dispatch](references/cli-dispatch.md) (`Invoke-CodexChild`).
  - **Claude Code CLI workers:** Follow [local Claude Code CLI dispatch](references/claude-cli-dispatch.md) (`claude -p` with explicit `--allowedTools`, `--max-turns`, and `--max-budget-usd`).
  - **Effectiveness comparisons:** Use [skill-effectiveness receipts](../independent-qa/references/skill-effectiveness.md) and [configuration comparisons](references/cli-dispatch.md#configuration-comparisons).

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
- Context & Baseline: [Relevant facts, base commit SHA, baseline test/error, and verified CLI setup]
- Verification: [Exact command that must pass before handoff]
- Bounds: [5-min artifact checkpoint, 10-min handoff deadline, max 5 read-only calls before first edit/check, no nested CLI]
```

- **Search & output discipline:** Exclude generated/log/cache directories from searches, cap command output, and read focused line ranges.
- **Native tools only:** CLI workers must use their native tools (`command_execution`/`file_change` in Codex; `Read`/`Edit`/`Write`/`Bash` in Claude Code), never nested CLI invocations or parent wrappers.
- **Required handoff:** Return `Artifact/paths changed` (with base and candidate commit/tree SHA when using worktrees), `Checks run & results`, `Unmet/unknown items`, and `Next action` (plus failure/recovery count if any).

## Coordinate to a working result

1. **Split only disjoint work:** One writer per file scope, using [worktree isolation](references/worktree-isolation.md) when running parallel tasks.
2. **Verify after process exit:** Wait for process completion (`turn.completed` and exit code `0`) before inspecting captured JSONL streams, diffs, and test outputs. Never judge a stream while it is still being written.
3. **Carry recovery counts:** Workers own local fixes (up to 2 attempts); supervisors/orchestrator resolve cross-scope blockers and verify the old writer stopped before reassigning scope.
4. **Integrate against full acceptance:** Check the combined result against the full `Ask` and verify that any nonauthor QA approval matches the integrated tree SHA.

## Documentation and repository hygiene

Follow Northstar's [repository rules](../northstar/SKILL.md#keep-records-and-the-repository-small): update existing records only at material decisions and handoffs, keep one editor per shared file, and use `tmp/<task>/` for disposable outputs.

## Failure, retries, and final integration

Delegation never weakens acceptance or resets the 2-strike recovery count. If CLI dispatch fails, continue directly in the parent within authority or report the exact blocker using Northstar's [delivery loop](../northstar/SKILL.md#deliver-a-usable-mvp-then-improve-in-increments) and [stall recovery](../northstar/SKILL.md#recover-from-a-stall).
