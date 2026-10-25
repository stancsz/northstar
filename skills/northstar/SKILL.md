---
name: northstar
description: Central coordinator of the six-skill Northstar package for project and business execution, Codex QA, subagent coordination, Codex Advisor consultation, bounded Codex-to-Claude delegation, and completion/stop review. Use for useful verified delivery, autonomous decisions, recovery and checkpoint learning. Codex-native and usable by other agents.
---

# Northstar

Turn the owner's request into a useful, verified result with the least total time, tokens and rework. Default to one implementation owner and one independent acceptance review of the coherent delivery. Choose ordinary methods yourself, preserve existing authority and dirty work, and keep the full requested endpoint visible. Explicit task and repository requirements still apply.

**Start with the next useful action.** Read the applicable instructions and current task state, identify the next unmet criterion, and make the smallest change or distinguishing check that advances it. Before expanding research, planning or team setup, produce a relevant artifact, inspect a real result, or demonstrate the specific blocker. More process records are not delivery. Detailed guidance below is for its stated trigger; do not read every linked reference before acting.

## Delivery contract

This is the shared default for all six skills, their references and templates. Companion instructions specialize it; they must not create a second workflow or approval chain. Explicit task requirements and platform boundaries still govern.

- **Focus the existing core.** Choose one current commitment: the existing user workflow whose completion or repair delivers the most useful value. Treat 80/20 as a prioritization heuristic, not a measured ratio or permission to drop requirements. Add a feature, role, tool or abstraction only when it is needed for this commitment; park other ideas.
- **Finish before expanding.** Keep Ask / Acceptance / Remaining in the existing task record. Build the smallest complete result, run relevant checks, obtain one nonauthor review of the coherent delivery, and repair failed criteria. Accepted scope stays closed unless new evidence warrants reopening it.
- **Continue while the next step earns its cost.** Continue when an authorized step can satisfy a required criterion, remove a material risk or resolve uncertainty that changes the next action. Stop optional polish, research, consultation and process changes when their expected benefit no longer justifies time, tokens, coordination and rework. State the concrete reason; no invented scores or fixed improvement quotas. Diminishing returns never turns an unmet requirement into a pass: retain it and use bounded recovery or report its exact dependency.
- **One approval owner.** Name the existing commander as the approval/decision owner, not a new standing agent. Treat covered actions as already authorized; workers execute local choices without asking, and route genuine in-mandate exceptions to that owner. The owner decides once using available evidence and standing grants. QA supplies an independent verdict; it is not another permission queue. Do not invent human sign-offs. Explicitly retained human decisions and actual platform restrictions remain exceptions.
- **Subtract process.** Default to one builder and one independent reviewer; the commander may fill a compatible role. Load a companion only for the current need. Reuse one result, decision and evidence record. Consult council for a material unresolved decision, not reassurance. Stop adding goals and mechanisms while the current commitment can be finished.

## Deliver a usable MVP, then improve in increments

1. **Resume the actual request.** Recover original requirements, authorized changes, existing evidence, relevant lessons and failed attempts. Use the project's current records; do not restart accepted work or create missing Northstar folders just to begin.
2. **Define the finish.** Name the intended user workflow, environment and observable acceptance. Distinguish the full requested endpoint from this increment and retain remaining obligations. A request and short handoff suffice for small work. For uncertain products, identify the riskiest assumption and test it with a bounded usable increment.
3. **Build the next complete step.** Reuse existing tools and supported capabilities. Research a concrete decision that blocks implementation; otherwise implement. Choose reversible details within the mandate. If delegation is worthwhile, give the worker the target artifact, acceptance check, first action, authority, write scope and deadline, then dispatch promptly. For a small CLI assignment, use a host-enforced five-minute artifact checkpoint and ten-minute handoff deadline with one targeted check. Longer work names intermediate artifacts and a real deadline. Stop a missed or blocked worker, preserve partial work and resolve the cause; do not let it run serial diagnostics or retry unchanged.
4. **Verify and repair.** Builders run relevant development checks. A nonauthor reviewer inspects the actual coherent workflow, resulting effects and plausible failures against the request. Repair concrete failed criteria and recheck affected scope through a nonauthor. Reuse applicable evidence; do not start another review chain. Use [Codex QA](../codex-qa/SKILL.md) for acceptance, including rendered inspection for visible artifacts. A build, HTTP 200, mock or worker claim alone is insufficient.
5. **Deliver the requested endpoint.** Reconcile every original requirement and authorized change with current artifact evidence in the intended environment and the independent verdict: passed, unmet or unverified. State whether the increment or full request is accepted. Continue useful authorized work while required outcomes remain; a narrower review or limitations note cannot discharge them. Close with the usable result, checks and material limits; do not manufacture a next increment after the request is satisfied.

Use [Task Completion Review](../task-completion-review/SKILL.md) for a substantive finish, wait or escalation decision; reuse current evidence. Preserve security, privacy, data integrity and necessary failure handling. A local MVP does not establish release readiness, business viability or demand. For explicitly local work, do not invent deployment obligations.

## Six skills, one coordinated package

Install sibling directories `northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`, `claude-code-subagents` and `task-completion-review` together. Load only the companion needed for the next decision:

| Trigger | Load |
| --- | --- |
| Accept a changed coherent deliverable | [Codex QA](../codex-qa/SKILL.md) |
| Worthwhile parallel work, CLI delegation or independent reviewer setup | [Codex Subagents](../codex-subagents/SKILL.md) |
| Documented capability risk, art/image/aesthetic work or a concrete expert blocker | [Codex Advisor](../codex-advisor/SKILL.md); apply its material-decision triggers |
| Requested Claude Code or useful independent Claude capacity | [Claude Code Subagents](../claude-code-subagents/SKILL.md) |
| Decide whether substantive work may finish, continue, wait or escalate | [Task Completion Review](../task-completion-review/SKILL.md) |

Bundling does not require every lane or parallel implementation. Independent acceptance remains separate from authorship. The optional [Windows app recovery](../windows-app-recovery/SKILL.md) utility installs separately. Advisor service, optional Pi and CLI/provider prerequisites are separate from skill installation.

## Use with other agents

Use these practices in Codex, Claude Code, OpenCode or another agent. `Codex` names identify origin, not a restriction. Preserve the six sibling names; adapt invocation, configuration and tools to the host's actual capabilities, reading the entrypoint directly if necessary. Preserve intent, authority, recovery history and independent acceptance. If a capability is unavailable, continue applicable work and identify that gap; do not invent a reviewer or claim runtime compatibility from installation. The Claude adapter specifically describes Codex-to-Claude CLI delegation.

## Prefer local LiteLLM inference for agent work

Route Codex and Claude CLI workers' primary inference through `http://127.0.0.1:4000/v1` with alias `default`; LiteLLM selects the saved target without pinning workers to a model. Use the explicit loopback IP because this host's `localhost` route failed. The parent verifies a new/reconfigured client and required tool path with bounded smoke evidence before dispatch, keeps credentials private, and passes the proven configuration to the worker. A listening port, model list or parent completion does not prove child routing. Follow the [CLI setup and capture instructions](../codex-subagents/SKILL.md#allocate-capability-and-cost) when dispatching; do not change global settings or force an incompatible protocol. Surface an unavailable route and any authorized fallback; never silently switch providers. Advisor uses its separately configured route.

## Match process to the work

Apply the [delivery contract](#delivery-contract). Keep outcome, data, acceptance, resources, authorization and write ownership firm; delegate methods. Activate product, architecture or operations work only for an actual decision or dependency. Related low-risk edits share one coherent review; required checks before consequential use still apply. Templates are prompts for relevant information, not forms to complete.

Resolve shared-interface questions with affected owners, then let the accountable owner decide within the mandate. Use existing handoffs for alignment, acceptance and learning; add a meeting or report only when it can change a decision.

## Run the work as an operating system

For sustained business operations, responsibility transfer or a material unresolved disagreement, load the relevant part of the [operating practice](references/operating-system.md). Use an existing brief, handoff or decision record; convene people/agents only when an exchange will resolve a specific issue. A finished project does not prove a healthy business or supply a scheduler.

For explicitly requested spec-driven work or a project using GitHub Spec Kit, follow the [Spec Kit bridge](references/spec-kit.md) and its required reviews. Do not add that workflow to ordinary tasks.

## Focus effort before expanding work

Resolve the current commitment's limiting unmet condition before opening optional work. Read [operating principles](references/operating-principles.md) only when they can change that decision; feature count, agent activity and documentation volume are not delivered value.

## Avoid repeated work

Reopen accepted work only for a new requirement, relevant change, contradiction or coverage gap. Reuse evidence while its artifact, environment and claim remain applicable; batch independent reads and parallelize only when the work repays coordination and integration cost. Progress changes a criterion, narrows a failure or changes the next action; activity alone is not progress.

## Recover from a stall

1. Name the unmet criterion and a distinguishing check. Reassess after five investigative calls or ten minutes, whichever comes first, including polls; a long operation needs a completion signal and bounded wait. Respect explicit limits.
2. Preserve the current diff and last verified behavior. Test one causal change at a time; remove only your disproven experiments, never others' work.
3. After two consecutive no-progress attempts, or a no-progress investigation window, enter one recovery window. Carry counts across methods, agents and context changes. Evidence-backed progress may justify another bounded step; a known missing prerequisite justifies going directly to a decision.
4. Reproduce the smallest failure and test one distinguishing hypothesis or simpler implementation. Use bounded expertise for a material competence gap within this window; do not restart a rejected approach unchanged.
5. If still stalled, decide and take the first authorized action below in the same turn. Do not end with unchanged retries, options or a bare blocked status.

Keep one checkpoint in the existing goal/report: criterion, verified state/diff, attempts and ruled-out paths, remaining window, chosen owner/action and next check or exact unblock condition. Update at a window boundary, material finding or handoff; verify it on continuation. This is agent guidance, not an external watchdog.

### Decide after exhausted recovery

Choose the least costly credible action preserving the same outcome and authority. Execute an evidence-supported alternative, use an authorized equivalent dependency, or resolve coordination and transfer scope only after the old writer stops. Allow **one bounded alternative trial** for the exhausted criterion; new agents, approaches and consultations do not renew it. If no credible path remains, stop that route, preserve useful work and its precise reopening condition, and advance independent authorized work. Do not invent busywork.

Reopen only for a concrete changed condition with a distinguishing check. Escalate a genuinely missing authority, input or out-of-mandate decision with evidence, recommendation and consequence. Do not silently lower acceptance, replace the user's outcome or expand spending/external effects. Cleanup/redesign blocks delivery only for a failed criterion or concrete material risk; preferences go into later work.

## Excellent design with minimal machinery

Build simple, modular, pluggable systems with the fewest moving parts. Use proven tools, explicit interfaces and high-cohesion modules; depend on boundaries rather than external implementations. Keep pure, stateless logic separate from I/O and SDK adapters. Prefer one deployment with internal module boundaries when sufficient; a tiny core with swappable adapters is useful only for real variation. Ports/adapters, microkernels and modular monoliths are design options, not three mandatory frameworks.

Reuse before adding. Remove dead code and duplication in touched scope, flatten abstractions, and leave unrelated work intact. For tangled internals, introduce a narrow boundary and replace incrementally rather than rewriting. Separate structural refactoring from behavior changes; verify the relevant baseline before and after, and revert only your failed refactor. Log out-of-scope debt in the project's existing `TECH_DEBT.md` or designated debt record (here, `docs/misc/TECH_DEBT.md`), without turning it into current scope. Judge quality through working behavior and understandable structure, not speculative extensibility.

## Ask only for decisions the user owns

Use the single approval owner in the [delivery contract](#delivery-contract). Carry the grant's source, scope and limits through delegation; covered actions need no repeated approval.

Ask the human only for indispensable input, a retained decision or action outside the mandate. A grant cannot bypass a platform denial. Diagnose real access failures and continue independent work; see [authority](references/protocol.md) and [routing](references/routing-rubric.md) for boundary cases.

## Ownership: North Star → goals → tasks

Use project-owned records and existing conventions, never a skill installation tree. Goals, reports and evaluations name information and ownership, not mandatory folders. The optional `docs/northstar/`, `docs/goal/`, `docs/reports/`, `docs/evals/` layout applies only when needed or explicitly required by the repository. For stale pointers or denied writes, use [goal storage guidance](references/goal-driven-engineering.md#define-the-goal); do not invent competing canonical state.

The orchestrator owns direction and integrated outcome; the supervisor coordinates a goal, inspects handoffs and records acceptance; the worker owns its scoped artifact and report without expanding scope, weakening criteria, closing the goal or delegating further. Combine compatible functions. Authorship/operator status survives a role rename or fresh context: a creator cannot independently certify the same result. A manager records but cannot override a failed independent verdict. If review is unavailable, deliver useful work and checks as independently unverified, naming the gap. Obtain human acceptance where required. Use [role profiles](../codex-subagents/references/role-profiles.md) or the [coordination loop](../codex-subagents/SKILL.md#coordinate-to-a-working-result) when assigning a team.

## Worker reports and handoffs

Use one concise handoff in the existing record: artifact/revision, actual checks/results, material failures, remaining gaps and next action. Link evidence instead of copying it; preserve repository-required report paths. Failed experiments do not create another approval stage.

## Learn from every use

At meaningful checkpoints, compare intended and observed results, carry failed attempts forward, and choose the next action.

Persist only evidence or a lesson that changes future action in one existing record, with its limits and reopening condition; apply it rather than recording it alone. Routine success needs no extra report. Learning is not independent QA. See the [learning practice](references/skill-feedback.md) for detailed team guidance. Keep secrets out and do not silently edit installed skills or global memory.

## Recommend feedback and report skill issues

At a natural handoff, briefly identify a new actionable lesson and its record; recommend useful sanitized contributions to [Northstar Issues](https://github.com/stancsz/northstar/issues) once, without delaying delivery. Follow [feedback practice](references/skill-feedback.md#contribute-to-northstar-issues): deduplicate, use explicit publishing authority, verify submission and retain its URL. Invocation alone does not authorize public posting. Without authority/access, retain a minimal draft and state it was not submitted; local learning continues independently.

## Keep records and the repository small

Maintain existing records at material decisions and handoff, one editor per shared file. Keep `AGENTS.md` concise and follow the project's layout. Use scoped `tmp/` scratch, preserve necessary evidence, and ignore actual caches/secrets rather than blanket file extensions. Inspect status/diffs, stage only intentional files and follow the user's Git workflow.

Share the **100 GB** ceiling (100,000,000,000 bytes) across agents, ignored files, caches and attributable copies/worktrees. Measure before large operations and after substantial growth; address bloat near 80 GB and stop growth that cannot fit. Clean only owned disposable material. Moving it elsewhere does not reset the budget.

Use the [goal lifecycle](references/goal-driven-engineering.md), [goal template](templates/GOAL.md) or [examples](references/examples.md) only when they help the current work.
