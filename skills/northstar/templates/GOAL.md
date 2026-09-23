# Goal: <production-value outcome>

Location: docs/goal/<goal>/GOAL.md

Status: active

## Ownership and tasks

- Orchestrator: <owns alignment with the North Star and final goal acceptance>
- Supervisor: <owns this goal and its index entry, task acceptance, integration, and evaluation coverage; may be the same agent>
- Tasks: <bounded outcome, worker, write scope, acceptance, dependencies, status, and link to docs/reports/<goal>/<task>.md for each task>
- Review: <who critiques quality and verifies behavior; disclose when the implementer also reviews>

## North Star

- Direction and owner standards: <relative link to docs/northstar/>
- Contribution to that direction: <the customer/business value this goal advances>
- Relevant assumptions and unknowns: <link durable research; record goal-specific details here>

## Outcome

<A production-capable user or business outcome, not just an implementation activity.>

## Why this matters now

<User value, business value, or validated risk this goal addresses.>

## Source of truth

<Links to product specs, customer evidence, architecture decisions, and relevant AGENTS.md instructions.>

## Acceptance criteria

- [ ] <Observable behavior or business/product signal>
- [ ] <Verification evidence for the production path>

## Constraints and invariants

- <Product, security, reliability, cost, or compatibility constraints>
- Total project artifacts stay below 100 GB across all agents; account for ignored files, scratch work, caches, and peak growth before large operations.

## Reference product and quality expectations

- <Link to the reference product research and owner standards in docs/northstar/>
- <Concrete competitive gaps in the real workflow, UX, effectiveness, and maintainability>

## Non-goals

- <Explicitly excluded scope; label any prototype as a bounded experiment>

## Point of no return and escalation

- Stop for explicit approval before: <release, destructive change, spending, permissions, external commitment>
- Escalate to the orchestrator if: <goal scope, acceptance, or a cross-goal dependency must change>; the orchestrator takes decisions beyond the user's mandate to the human.

## Goal execution record

### Current approach

<Highest-value next step and why it advances the outcome.>

### Progress and decisions

- <Record material discoveries and decisions, not every action.>

### Worker handoffs

- <Task report link, supervisor's acceptance or repair decision, and remaining integration work; keep detailed worker findings in the report>

### Validation and evidence

- <Link to docs/evals/ results: evaluated revision/environment, checks actually run, observations, limitations, and durable evidence>

### Remaining gap

- <Unmet acceptance criterion, production blocker, and next action; or none>

### Critique and fixes

- <Brief material findings and fixes, with links to their evaluation details>

### Acceptance

- Supervisor recommendation: <ready or remaining work, with integrated evidence>
- Orchestrator decision, recorded by the supervisor: <accepted or returned for repair, with reasons; include human acceptance when required and update the goal index>
