---
name: northstar
description: Central workflow for project and business delivery. Use for coordination, delegation, advice, QA, recovery, and completion decisions.
---

# Northstar

Deliver verified outcomes with low effort and zero silent drift. Follow the [delivery contract](#delivery-contract).

**Rule 0 — Act on the next unmet criterion.** Read the request and current state, pick the next unmet requirement, and make the smallest code change or distinguishing check that advances it. Do not build process files, expand plans, or read every linked reference before producing a real artifact or test result.

## Preserve task continuity and accumulate evidence

Fast, long-running agents lose focus when tool outputs push the original request out of view or when context compacts. Prevent drift with one explicit state anchor and hard execution brakes:

### 1. Maintain one compact state anchor
For multi-step or resumed work, keep one live block in the project's existing task/goal record (or in your working notes for a one-turn task):

```markdown
- Ask (Locked): [User's exact outcome & must-haves; never silently weaken]
- Done (Verified): [Criteria passed with command/artifact evidence]
- Remaining: [All unfinished required criteria]
- Facts vs. Unknowns: [Observed facts with source | Open unknowns/assumptions]
- Failed / Ruled Out: [Approaches tried + recovery count (0/2)]
- Next Action: [Single concrete step tied to one Remaining item]
```

- **Lock the baseline at entry.** Extract user-stated outcomes, constraints, and exclusions before dependent edits. Label agent ideas as *proposals*, never mandatory requirements. Only explicit user steering can drop or replace a requirement; if an item is blocked, keep it open in `Remaining` and report the blocker.
- **Save and read back at boundaries.** Update the anchor after a user correction, verified increment, failed attempt, or before handoff/compaction. Read back the saved file before claiming persistence.
- **Rehydrate on resume.** After compaction or session resume, read the anchor and inspect `git status` / `git diff` before making edits. Reconcile stale notes against actual files.

### 2. Hard anti-drift rules
- **Brake on tool-output hijacking.** Unrelated warnings, lint noise, or side discoveries in tool output must **never** redirect the current step. Log out-of-scope issues to `TECH_DEBT.md` (or `Remaining`) and stay on `Next Action`.
- **Protect tests and assertions.** When a check fails, fix the implementation. **Never** delete a failing test, weaken an assertion, mock out required integration, or relabel a required item as optional just to get a green run.
- **Answer side questions without losing the thread.** If the user asks a status or side question, answer it directly and immediately resume `Next Action`. If the user corrects a requirement, update `Ask`, mark superseded assumptions, and keep all unaffected requirements intact.

## Delivery contract

Shared rules across all six Northstar skills (`northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`, `claude-code-subagents`, `task-completion-review`):

- **Focus one core commitment.** Finish and verify the highest-value existing workflow before expanding. Park optional ideas.
- **Finish before expanding.** Build the smallest complete result and run real checks. The commander accepts small, reversible, attributable work directly from test/diff evidence. Use one independent nonauthor review ([Codex QA](../codex-qa/SKILL.md)) only when required or when material user/data/security/visual risk applies.
- **Stop optional work at diminishing returns.** Continue while steps satisfy required criteria or remove material risk. Stop optional polish, research, or consultation when cost exceeds value. Never use diminishing returns to waive an unmet required criterion.
- **One approval owner.** One commander agent owns covered approvals and decisions under the user's standing grant. Workers execute in scope without asking the user or opening a second approval queue. Ask the user only for decisions explicitly reserved to them or outside the grant.
- **Subtract process.** Default to one agent. Add subagents, reviewers, or council calls only when their value clearly exceeds coordination cost.

## Deliver a usable MVP, then improve in increments

1. **Resume the actual request.** Read existing records and diffs; do not restart accepted work or create empty Northstar directories. (Use [business planning](references/business-planning.md) only when asked for market/financial/GTM strategy.)
2. **Define the finish.** State the target workflow, environment, and observable acceptance check.
3. **Build the next complete step.** Reuse existing code and tools. Cap read-only exploration at **5 tool calls** before making a concrete edit or running a distinguishing check. When delegating to a CLI worker, assign one target artifact, exact writable paths, one verification check, and a firm deadline (5-minute artifact checkpoint, 10-minute handoff).
4. **Verify and repair.** Run the actual check and inspect affected workflows. Repair failures in scope. A passing build, HTTP 200, mock, or worker summary alone is not verification.
5. **Deliver the requested endpoint.** Reconcile every item in `Ask` against real evidence (`passed`, `unmet`, or `unverified`). Report material limits and stop—do not invent a new phase after completion.

## Recover from a stall

Do not loop on the same error or run unbounded diagnostics:

1. **Cap investigation at 5 calls or 10 minutes.** Name the unmet criterion and run one distinguishing check.
2. **2-strike rule on failures.** Test one causal change at a time while preserving working diffs. After **2 consecutive attempts** with the same failure or no progress, stop patching and enter **one recovery window** (counts carry across agents and context resets).
3. **Isolate or simplify.** Reproduce the minimal failure, test one simpler implementation, or consult [Codex Advisor](../codex-advisor/SKILL.md) for a concrete capability gap. Never retry an unchanged command or rejected approach.

### Decide after exhausted recovery
When the recovery window is spent, take the first credible action in the same turn:
- Switch to **one bounded alternative implementation** that preserves the required outcome;
- Resolve the blocking coordination/dependency; or
- Stop that route, preserve clean partial work with its exact unblock condition in the checkpoint, and advance independent authorized work. Never lower acceptance silently or end with bare options.

## Six skills, one coordinated package

Load a companion skill **only** when its trigger applies:

| Trigger | Companion to load |
| --- | --- |
| Independent nonauthor QA or visual inspection is required | [Codex QA](../codex-qa/SKILL.md) |
| Parallel workstream or CLI worker dispatch helps | [Codex Subagents](../codex-subagents/SKILL.md) |
| Concrete blocker, capability risk, or visual/aesthetic check | [Codex Advisor](../codex-advisor/SKILL.md) |
| Delegating bounded CLI work to Claude Code | [Claude Code Subagents](../claude-code-subagents/SKILL.md) |
| Auditing whether substantive work may stop, wait, or continue | [Task Completion Review](../task-completion-review/SKILL.md) |

## Use with other agents

These practices work across Codex, Claude Code, Gemini, MiniMax, Luna, and OpenCode. Adapt tool calls to the host while keeping intent locking, single-commander authority, 2-strike recovery, and evidence verification intact. (For bilingual buyer-facing slide decks, use `bilingual-product-demo-deck` when installed and ensure slides stand alone visually.)

## Prefer local LiteLLM inference for agent work

Default Codex and Claude CLI workers to `http://127.0.0.1:4000/v1` using Subroute's dynamic `default` alias unless the task selects another supported model ID/alias; never pin a vendor model in shared docs. The parent verifies the route and tool path once with a bounded smoke before dispatch, keeps keys process-scoped, and never silently switches providers on failure. See [CLI setup](../codex-subagents/SKILL.md#allocate-capability-and-cost).

## Coordinate proportionately

Coordinate shared interfaces with affected owners, then let the accountable owner decide within the mandate. Reuse existing handoffs; add meetings or reports only when they change the next action.

## Run the work as an operating system

For sustained multi-team operations, ownership transfer, or unresolved disputes, load [operating practice](references/operating-system.md). For projects explicitly using GitHub Spec Kit, load the [Spec Kit bridge](references/spec-kit.md). Ignore both for ordinary tasks.

## Excellent design with minimal machinery

Build simple, modular code with minimal moving parts. Separate pure logic from I/O adapters. Reuse existing modules, delete dead code in touched scope, and separate structural refactoring from behavior changes. Log out-of-scope cleanup in `TECH_DEBT.md` rather than expanding the current task.

## Ownership: North Star → goals → tasks

Keep goal and task state in the project repository, never inside `~/.codex/skills` or `~/.claude/skills`; see [goal storage](references/goal-driven-engineering.md#define-the-goal). Orchestrators own the integrated outcome, supervisors coordinate multi-task goals, and workers own one scoped task. Combine roles when working solo, but an author cannot certify their own work as independent QA.

## Worker reports and handoffs

Return one concise handoff:
- **Artifact & paths changed** (with revision/base)
- **Checks run & actual results** (link evidence instead of pasting long logs)
- **Remaining gaps / unknowns** (`passed`, `unmet`, `unverified`)
- **Next action**

## Learn from every use

At meaningful checkpoints, compare expected vs. observed results. Record only lessons that change future action in the existing task record ([learning practice](references/skill-feedback.md)).

## Recommend feedback and report skill issues

At handoff, note any reusable skill lesson and optionally suggest reporting sanitized issues to [Northstar Issues](https://github.com/stancsz/northstar/issues) once; never post publicly without explicit user authority.

## Keep records and the repository small

Update records only at material decisions and handoffs, with one editor per shared file. Use `tmp/<task>/` for disposable scratch, stage only intentional files, and follow [goal lifecycle](references/goal-driven-engineering.md), [goal template](templates/GOAL.md), or [examples](references/examples.md) only when needed.
