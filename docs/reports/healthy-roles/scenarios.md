# Healthy roles: bounded scenario trial

**Status:** Scenario analysis complete; no live system was changed or called.
**Method:** Applied the current Northstar, Codex Subagents, role-profile, agent-handoff, and Codex QA guidance to the six supplied cases.
**Model:** `gpt-6-luna`, medium reasoning. Actual cost was not available.

## Decisions

### 1. Invoice CSV import; builder offers to become QA

- **Assignment:** Keep the current worker as builder and hand its artifact and local-check evidence to one nonauthor independent verifier when a reviewer slot becomes available. No additional builder or manager is needed for this small change.
- **Disposition/readiness:** **UNVERIFIED.** The local checks are useful development evidence; clearing context or changing the worker's title does not remove authorship. The case says no reviewer slot is presently available, so independent acceptance cannot be claimed now.
- **Next action:** Preserve the current artifact/revision and check results. Record the precise missing reviewer and queue a brief acceptance check; do not label the import accepted or QA-ready meanwhile.
- **Evidence needed:** Nonauthor exercises the actual CSV import entry point with representative valid input and a high-value malformed/empty or duplicate case; inspect resulting invoice records, error behavior, and any promised persistence. Tie observations to the current revision.
- **Authority limit:** The builder may report and repair its work, but cannot supply independent acceptance. A staffing shortage does not waive the acceptance criterion.

### 2. Supervisor repairs the interface after QA passed v1

- **Assignment:** Supervisor remains the integration/repair owner and task decision recorder. Assign one uninvolved reviewer to inspect v2's repaired interface and affected integration behavior.
- **Disposition/readiness:** Earlier QA evidence remains applicable only to unchanged v1 scope. The interface that differs in v2 is not covered. **UNVERIFIED for v2's changed scope** until the nonauthor rechecks it; the supervisor may not sign its own repair as QA readiness.
- **Next action:** Hand off the v2 artifact, original criterion, interface change, and prior v1 review scope to the nonauthor reviewer. The supervisor can record the independent verdict after inspection, but cannot override a failed criterion.
- **Evidence needed:** Reviewer inspects the actual v2 artifact and exercises the affected interface plus its adjacent integration path, with a concrete expected/observed result. Reuse prior v1 evidence for unchanged behavior and state why it still applies.
- **Authority limit:** Supervisor's goal ownership permits coordination and integration repair, not self-certification of repaired scope. If no uninvolved reviewer is available, retain **UNVERIFIED**.

### 3. Design creator wants to judge premium quality and approve

- **Assignment:** One nonauthor reviewer combines functional QA with experience/taste inspection, since the scenario provides a reviewer able to do both. The required human aesthetic approver remains the final aesthetic decision owner.
- **Disposition/readiness:** Creator cannot independently judge its own design. Reviewer can report functional and visual findings and a scoped QA recommendation; this does not satisfy the required human aesthetic approval. Overall human approval remains pending.
- **Next action:** Give the reviewer the original page intent/criteria, actual rendered checkout at intended size and supported layouts, and access to the functional journey. After the reviewer reports, route the actual design and evidence to the designated human for aesthetic approval.
- **Evidence needed:** Exercise the purchase journey through its real entry point and inspect resulting state; visually inspect the rendered page, hierarchy, typography, spacing, content density, controls, and relevant narrow/wide states. Record revision, dimensions, states, and concrete observations. Human approval must be explicitly recorded by the owner.
- **Authority limit:** The creator may provide design rationale and fix findings, not independent taste approval. Agent QA/taste judgment cannot impersonate the required human approval.

### 4. Discount-rule operator claims improved revenue and offers to audit

- **Assignment:** Assign the other agent as independent verifier for formula/configuration and sandbox journeys, using only its authorized read-only service access and sandbox capability. The operator remains the operational decision owner but must not audit its own configuration or outcome claim.
- **Disposition/readiness:** The operator's report is a claim, not independent evidence. Independent review can establish whether the configured formula behaves as specified in sandbox and can inspect authorized read-only records. Sandbox success alone cannot establish that revenue improved in real operation or that the discount caused the change. Those outcome claims remain unverified until supported by suitable operating evidence.
- **Next action:** Reviewer inspects the actual rule/configuration and its formula against the stated business rule, then exercises representative eligible and ineligible sandbox journeys. Separately inspect authorized read-only evidence for the claimed revenue period and comparison; report the limits to the operator/accepting owner.
- **Evidence needed:** Formula inputs, edge cases, expected discount and observed result; sandbox order totals and downstream state; source and scope of the revenue report, comparison period/baseline, relevant exclusions, and whether the report is independently reproducible. Distinguish observed revenue association from causal attribution.
- **Authority limit:** Read-only service access authorizes inspection only; sandbox authority authorizes sandbox journeys only. Reviewer must not change the rule or make the operational decision. Operator may decide within its mandate, but cannot certify its own audit. If source data or a suitable comparison is unavailable, state the exact evidence gap rather than promoting the revenue claim.

### 5. Product and architect disagree on dropping a promised export criterion

- **Assignment:** The responsible superior chairs the required short decision meeting after the one direct evidence exchange. Product presents the deadline/value argument; architect presents the record-loss mechanism and evidence. The actual outcome owner decides whether the promised criterion may change, within the user's mandate.
- **Disposition/readiness:** The existing promised export criterion remains binding until its owner authorizes a scope change. A concrete record-loss risk and unresolved disagreement block acceptance; readiness is **NOT READY** for the promised export. The meeting cannot waive a failed criterion by vote.
- **Next action:** Preserve the failing export evidence and exhausted recovery history. At the meeting, require each side's reasons, counterargument, and evidence that would change its view. The responsible superior then takes the least costly credible action within authority: choose a compatible remedy/one bounded alternative trial that preserves acceptance, or park the export route and escalate the scope decision with recommendation and evidence. Continue any independent authorized work.
- **Evidence needed:** Reproducible export failure, affected records and expected invariant; evidence for the architect's loss scenario; proposed shortcut's behavior against that invariant; deadline consequence and any same-contract alternative. Record the decision owner, unresolved dissent, and next check.
- **Authority limit:** Product preference or deadline does not itself authorize deleting an accepted promise. The superior may resolve coordination within its mandate but cannot reduce user acceptance beyond that mandate. The exhausted route gets no fresh retries through reassignment or a new agent; one bounded alternative trial is available under the exhausted-recovery rule. If that also fails, stop that route and preserve the unmet criterion for the owner.

### 6. Remote A2A worker returns stale v1 and suggests a clean retry

- **Assignment:** Do not assign or invoke the worker's advertised deployment capability. Keep the task owner on read-only inspection of the current v2 artifact and its permitted evidence; a nonauthor reviewer may inspect v2 if acceptance evidence is required and access is authorized.
- **Disposition/readiness:** The worker's completed v1 is available for inspection but is stale relative to v2 and cannot establish v2 acceptance. A completed transport task is not an acceptance verdict. Deployment is outside the only authorized scope. The proposed new ID cannot restart a terminal task or erase recovery history; any authorized follow-up task must be linked and inherit the same criteria and attempt history. No source data may be transmitted.
- **Next action:** Inspect v2 directly using the authorized read-only path; record its revision and the exact evidence available. Reject the deployment suggestion and do not transmit source data. Preserve the original task/context/artifact identifiers and failed-attempt count. If a new transport task is needed later, use it only for authorized read-only work and carry forward acceptance and recovery state.
- **Evidence needed:** Current v2 identity and contents; provenance/revision of returned v1; task lifecycle/status and linked artifact identifiers; independently observed read-only evidence against the unchanged criteria. If any required check needs a write, deployment, external call, or source-data transfer, record it as unavailable under current authorization.
- **Authority limit:** Capability advertisement grants no permission. Current authorization permits read-only inspection only and explicitly excludes source-data transmission; it does not permit deployment or restart. Transport completion, a new ID, or a clean retry counter cannot expand authority or reset the recovery budget.

## What the guidance clarified and what remains open

The skills made these distinctions actionable: creator/repairer recusal follows the artifact scope, not the agent name or context; a nonauthor can combine compatible QA and taste functions; an independent verdict is distinct from the manager's acceptance record; current-revision evidence is required after repair; human approval remains human; and remote capability, task completion, or a new task ID grants neither permission nor a fresh retry budget. They also specify a short superior-chaired meeting after one unresolved evidence exchange and what evidence a QA handoff should contain.

Some case details remain intentionally unresolved because the scenarios do not supply them: the exact import contract and invoice data rules; the interface's acceptance contract; the checkout's stated visual reference and named human approver; the discount rule's authoritative revenue source/baseline; the responsible superior and outcome owner's exact mandate for the export scope; and the A2A host's concrete protocol/version and task identifiers. The report therefore names needed evidence and limits without inventing those facts. The A2A notes apply the handoff guidance as written; this trial did not query a live endpoint or independently validate transport conformance.

## Trial limits and learning

This was reasoning over supplied scenarios, not execution of fixes, QA, sandbox journeys, service operations, or protocol calls. It does not establish that any proposed assignment was actually staffed or that any evidence exists. The selected model was `gpt-6-luna` at medium reasoning; actual cost is unknown, so no cost claim is made.

Useful method: state artifact revision, creator/repairer, reviewer, decision owner, evidence, and authority separately. Reuse this for similar cases when those boundaries and criteria are supplied. Ruled out: treating role renaming, prior-revision QA, self-authored reports, completion state, or a fresh task ID as substitutes for independent current evidence. Reopen only if new evidence, an authorized scope decision, or a changed artifact/authority changes the next action.
