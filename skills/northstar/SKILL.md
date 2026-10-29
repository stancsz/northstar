---
name: northstar
description: Central workflow for project and business delivery. Use for coordination, delegation, advice, QA, recovery, and completion decisions.
---

# Northstar

Deliver useful, verified work with low total effort and rework. Preserve authority, dirty work and the full requested outcome; follow the [delivery contract](#delivery-contract).

**Start with the next useful action.** Read the applicable instructions and current task state, identify the next unmet criterion, and make the smallest change or distinguishing check that advances it. Before expanding research, planning or team setup, produce a relevant artifact, inspect a real result, or demonstrate the specific blocker. More process records are not delivery. Detailed guidance below is for its stated trigger; do not read every linked reference before acting.

## Preserve task continuity and accumulate evidence

More context should refine project understanding without replacing the requested outcome. Apply this check at task entry, after context compaction/resumption, and before changing direction or claiming completion.

- **Keep one durable anchor.** For sustained work, maintain a compact current-state block in the existing project task/goal record: full Ask, acceptance and remaining obligations; user decisions/constraints with their source; verified artifacts/checks; unresolved assumptions; failed attempts/recovery allowance; and one next action tied to an unmet criterion. Keep its path in the handoff or existing project index so a new context can find it. Small one-turn work needs only its request and handoff; promote it to the existing durable record if it grows across turns or needs recovery.
- **Learn from evidence.** Distinguish user requirements/decisions, observed facts (source plus revision/environment where relevant), hypotheses, and unknowns. Integrate new evidence into the current understanding; mark contradicted conclusions superseded with the reason instead of leaving conflicting facts active. Preserve material decisions, rejected approaches and unresolved requirements when shortening history. Trace mandatory acceptance to the user request or applicable project rules. Label agent-added design choices as proposals or working assumptions; do not promote them into user requirements or retained user decisions. Summaries and worker claims are pointers, not verification; do not fill missing details with plausible inventions or treat repeated claims as new evidence.
- **Save at meaningful boundaries.** Update the same anchor after a user correction, material finding, accepted step, failed approach, direction change, and before a handoff or anticipated compaction. Read back saved changes before claiming persistence. Do not depend on a compaction warning arriving; maintain state during work. Keep detailed logs elsewhere and link them only when needed; do not grow an append-only transcript or update a record on every tool call.
- **Rehydrate before acting.** After resumption, read the anchor and relevant user steering, then inspect the actual artifact/diff and any evidence whose freshness affects the next action. Reconcile mismatches before dependent edits. If the record is missing or stale, reconstruct from accessible user instructions and artifacts, label gaps unknown, and ask only when missing information changes scope, authority or correctness. Never silently choose among multiple plausible active tasks.
- **Rethink the method, preserve the outcome.** After surprising evidence, a user correction, repeated failure, or a completed increment, compare the original ask with the whole current result, not just the subtask in view. State what changed in project understanding and whether the current method still serves the outcome; test a disconfirming fact or simpler alternative when it could change the decision. Revise a disproven plan within existing authority without silently narrowing acceptance. If nothing material changed, continue without ceremonial replanning.
- **Check direction.** Before a new work phase, delegation, broad investigation or final answer, identify which remaining criterion the action advances and which evidence supports it. An unrelated action is deferred; repeated investigation uses the existing recovery allowance. A status question or side question does not replace the task: answer it and resume. Apply explicit user changes or cancellations, preserve unaffected obligations, and record what was superseded. Do not let the latest tool output redefine the goal.

This is a persistent working practice, not an enforced runtime guard or a guarantee against hallucination. It works only when the host loads these instructions and the agent reads/writes the record. If storage is unavailable, follow the existing [storage boundary](references/goal-driven-engineering.md#keep-goal-state-project-owned), disclose unsaved state, and carry a concise handoff; never claim durable learning from chat alone.

## Delivery contract

This is the shared default for all six skills, their references and templates. Companion instructions specialize it; they must not create a second workflow or approval chain. Explicit task requirements and platform boundaries still govern.

- **Focus the existing core.** Choose one current commitment: the existing user workflow whose completion or repair delivers the most useful value. Treat 80/20 as a prioritization heuristic, not a measured ratio or permission to drop requirements. Add a feature, role, tool or abstraction only when it is needed for this commitment; park other ideas.
- **Finish before expanding.** Keep Ask / Acceptance / Remaining in the existing task record. Build the smallest complete result and run relevant checks. Use one nonauthor review when required or when it can change acceptance: material user/data/security risk, cross-component integration, unresolved uncertainty or visual judgment. Otherwise the commander accepts small, reversible work when its scope is attributable and relevant checks pass. If scope or evidence cannot be established, keep acceptance unverified or obtain the required review. This is accountable acceptance, not an independent verdict. Repair failed criteria; keep accepted scope closed unless new evidence warrants reopening it. Reuse evidence only while its artifact, environment and claim remain applicable.
- **Continue while the next step earns its cost.** Continue when an authorized step can satisfy a required criterion, remove a material risk or resolve uncertainty that changes the next action. Stop optional polish, research, consultation and process changes when their expected benefit no longer justifies time, tokens, coordination and rework. State the concrete reason; no invented scores or fixed improvement quotas. Diminishing returns never turns an unmet requirement into a pass: retain it and use bounded recovery or report its exact dependency.
- **One approval owner.** Name one commander agent as the sole approval/decision owner. Covered actions are already authorized by the user's standing grant; the commander directs them without fresh approval, and workers execute within scope without asking the user or opening another approval queue. The commander resolves exceptions within its delegated authority. QA supplies an independent verdict, not another permission gate. Ask the user only for a decision explicitly reserved to them or authority the grant does not cover. An agent cannot approve beyond the user's grant or override a platform denial; report the exact boundary and continue independent authorized work.
- **Subtract process.** Default to one owner. Add workers or reviewers only when required or when their value exceeds coordination and integration cost. Load a companion only for the current need. Reuse one result, decision and evidence record. Consult council for a material unresolved decision, not reassurance. Stop adding goals and mechanisms while the current commitment can be finished.

## Deliver a usable MVP, then improve in increments

When the customer, problem, value or product direction is uncertain, choose an informative test before committing to a build. For a consequential business plan, market/research decision, go-to-market or pricing choice, operating model, or scenario analysis needing adversarial examination and economics, use [business planning and adversarial research](references/business-planning.md). A focused product test addresses a specific assumption; business planning integrates buyers, evidence, alternatives, operations and financial scenarios. Neither is a stage gate for a clearly specified delivery. Apply the steps below to the chosen outcome, including research when that is the task.

1. **Resume the actual request.** Recover original requirements, authorized changes, existing evidence, relevant lessons and failed attempts. Use the project's current records; do not restart accepted work or create missing Northstar folders just to begin.
2. **Define the finish.** Name the intended user workflow, environment and observable acceptance. Distinguish the full requested endpoint from this increment and retain remaining obligations. A request and short handoff suffice for small work. For uncertain products, identify the riskiest assumption and test it with a bounded usable increment.
3. **Build the next complete step.** Reuse existing tools and supported capabilities. Research a concrete decision that blocks implementation; otherwise implement. Choose reversible details within the mandate. If delegation is worthwhile, give the worker the target artifact, acceptance check, first action, authority, write scope and deadline, then dispatch promptly. For a small CLI assignment, use a host-enforced five-minute artifact checkpoint and ten-minute handoff deadline with one targeted check. Longer work names intermediate artifacts and a real deadline. Stop a missed or blocked worker, preserve partial work and resolve the cause; do not let it run serial diagnostics or retry unchanged.
4. **Verify and repair.** Check changed behavior and plausible failures. Load [Codex QA](../codex-qa/SKILL.md) when the review threshold applies, including visual inspection when relevant. Otherwise the commander accepts attributable, small and reversible work from relevant checks and the scoped diff. Repair failed criteria and recheck affected scope when required; reuse evidence. A build, HTTP 200, mock or worker claim alone is insufficient.
5. **Deliver the requested endpoint.** Reconcile every original requirement against evidence and the reviewer verdict when required, otherwise the commander's acceptance. Mark each passed, unmet or unverified. Keep required work open; a narrower review cannot discharge it. Deliver with checks and material limits, and do not invent another increment after completion.

Use [Task Completion Review](../task-completion-review/SKILL.md) only when a substantive finish, wait or escalation decision remains uncertain after applying this contract; otherwise decide directly and reuse current evidence. Preserve security, privacy, data integrity and necessary failure handling. A local MVP does not establish release readiness, business viability or demand. For explicitly local work, do not invent deployment obligations.

## Six skills, one coordinated package

Install sibling directories `northstar`, `codex-qa`, `codex-subagents`, `codex-advisor`, `claude-code-subagents` and `task-completion-review` together. Load only the companion needed for the next decision:

| Trigger | Load |
| --- | --- |
| Independent acceptance is required or materially useful | [Codex QA](../codex-qa/SKILL.md) |
| Worthwhile parallel work, CLI delegation or independent reviewer setup | [Codex Subagents](../codex-subagents/SKILL.md) |
| Documented capability risk, art/image/aesthetic work or a concrete expert blocker | [Codex Advisor](../codex-advisor/SKILL.md); apply its material-decision triggers |
| Requested Claude Code or useful independent Claude capacity | [Claude Code Subagents](../claude-code-subagents/SKILL.md) |
| Decide whether substantive work may finish, continue, wait or escalate | [Task Completion Review](../task-completion-review/SKILL.md) |

Bundling does not require every lane or parallel implementation. When independent acceptance applies, keep it separate from authorship. The optional [Windows app recovery](../windows-app-recovery/SKILL.md) utility installs separately. Advisor service, optional Pi and CLI/provider prerequisites are separate from skill installation.

## Use with other agents

Use these practices in Codex, Claude Code, OpenCode or another agent. `Codex` names identify origin, not a restriction. Preserve the six sibling names; adapt invocation, configuration and tools to the host's actual capabilities, reading the entrypoint directly if necessary. Preserve intent, authority, recovery history and independent acceptance where required. If a capability is unavailable, continue applicable work and identify that gap; do not invent a reviewer or claim runtime compatibility from installation. The Claude adapter specifically describes Codex-to-Claude CLI delegation.

## Prefer local LiteLLM inference for agent work

Route Codex and Claude CLI workers' primary inference through `http://127.0.0.1:4000/v1` by default. Use the gateway's dynamic `default` alias unless the task selects any other model ID or alias supported by that Subroute endpoint; never pin a backend model in shared guidance. The parent verifies a new/reconfigured client and required tool path with bounded smoke evidence before dispatch, keeps credentials private, and passes the proven endpoint and model selection to the worker. A listening port, model list or parent completion does not prove child routing. Follow the [CLI setup and capture instructions](../codex-subagents/SKILL.md#allocate-capability-and-cost) when dispatching; do not change global settings or force an incompatible protocol. Surface an unavailable route and any authorized fallback; never silently switch providers. Advisor uses its separately configured route.

## Coordinate proportionately

Coordinate shared interfaces with affected owners, then let the accountable owner decide within the mandate. Use existing handoffs; add meetings or reports only when they can change acceptance or the next action. Treat templates as prompts, not forms.

## Run the work as an operating system

For sustained business operations, responsibility transfer or a material unresolved disagreement, load the relevant part of the [operating practice](references/operating-system.md). Use an existing brief, handoff or decision record; convene people/agents only when an exchange will resolve a specific issue. A finished project does not prove a healthy business or supply a scheduler.

For explicitly requested spec-driven work or a project using GitHub Spec Kit, follow the [Spec Kit bridge](references/spec-kit.md) and its required reviews. Do not add that workflow to ordinary tasks.

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

Reuse before adding. Remove dead code and duplication in touched scope, flatten abstractions, and leave unrelated work intact. For tangled internals, introduce a narrow boundary and replace incrementally rather than rewriting. Separate structural refactoring from behavior changes; verify the relevant baseline before and after, and revert only your failed refactor. Log out-of-scope debt in the project's existing `TECH_DEBT.md` or designated debt record without turning it into current scope. Judge quality through working behavior and understandable structure, not speculative extensibility.

## Ownership: North Star → goals → tasks

Use project-owned records and existing conventions, never a skill installation tree. Goals, reports and evaluations name information and ownership, not mandatory folders. The optional `docs/northstar/`, `docs/goal/`, `docs/reports/`, `docs/evals/` layout applies only when needed or explicitly required by the repository. For stale pointers or denied writes, use [goal storage guidance](references/goal-driven-engineering.md#define-the-goal); do not invent competing canonical state.

Orchestrators own integrated outcomes; supervisors coordinate goals; workers own scoped artifacts. Combine roles where compatible. A creator cannot independently certify their work. If required review is unavailable, report it unverified; otherwise the commander accepts from evidence. Human acceptance applies only to retained decisions. See [role profiles](../codex-subagents/references/role-profiles.md) when assigning a team.

## Worker reports and handoffs

Use one concise handoff in the task response or existing record: artifact/revision, actual checks/results, material failures, remaining gaps and next action. Link evidence instead of copying it; preserve report paths only when the repository or task requires a durable handoff. Failed experiments do not create another approval stage.

## Learn from every use

At meaningful checkpoints, compare intended and observed results, carry failed attempts forward, and choose the next action.

Persist only evidence or a lesson that changes future action in one existing record, with its limits and reopening condition; apply it rather than recording it alone. Routine success needs no extra report. Learning is not independent QA. See the [learning practice](references/skill-feedback.md) for detailed team guidance. Keep secrets out and do not silently edit installed skills or global memory.

## Recommend feedback and report skill issues

At a natural handoff, briefly identify a new actionable lesson and its record; recommend useful sanitized contributions to [Northstar Issues](https://github.com/stancsz/northstar/issues) once, without delaying delivery. Follow [feedback practice](references/skill-feedback.md#contribute-to-northstar-issues): deduplicate, use explicit publishing authority, verify submission and retain its URL. Invocation alone does not authorize public posting. Without authority/access, retain a minimal draft and state it was not submitted; local learning continues independently.

## Keep records and the repository small

Maintain existing records at material decisions and handoff, one editor per shared file. Keep `AGENTS.md` concise and follow the project's layout. Use scoped `tmp/` scratch, preserve necessary evidence, and ignore actual caches/secrets rather than blanket file extensions. Inspect status/diffs, stage only intentional files and follow the user's Git workflow.

Use the [goal lifecycle](references/goal-driven-engineering.md), [goal template](templates/GOAL.md) or [examples](references/examples.md) only when they help the current work.
