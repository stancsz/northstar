# Operating system for projects and businesses

Use this on-demand reference for sustained multi-team operations, ownership transfer, or unresolved disputes. It connects [Northstar delivery](../SKILL.md) with [Subagent Orchestration](../../subagent-orchestration/SKILL.md) without adding mandatory bureaucracy.

## 1. Turn direction into today's work

Cover the needed [functional roles](../../subagent-orchestration/references/role-profiles.md) (product, architecture, implementation, independent QA, UX/taste, operations, domain expertise) across the existing hierarchy, using [agent handoffs](../../subagent-orchestration/references/agent-handoffs.md) when work moves between owners. Keep creation/operating authority separate from nonauthor [Independent QA](../../independent-qa/SKILL.md).

Maintain one visible value chain in existing records:
**Beneficiary & value → Current outcome → Limiting condition → Owned action → Acceptance evidence → Operational result → Learning**

- **Direction:** State the user/customer problem, intended value, protected standards, and authority. Label unvalidated demand or ROI as a hypothesis.
- **Commitment:** Pick one complete result, one accountable owner, resources, acceptance check, and stop condition. Cap WIP to what can be finished and verified.
- **Execution:** Let the closest competent owner choose the method and flag bad assumptions; managers remove blockers and decide cross-scope tradeoffs rather than rewriting worker output.
- **Operations:** For ongoing services, set a review trigger/cadence and operator. Track only decision-changing signals (demand/retention, delivery, failure rate, capacity, realized revenue/cost) with source and period.
- **Transfer:** Before marking a capability operated, record the service owner, failure signals, recovery/escalation path, and any required release/spend authority.

## 2. Decision ceremonies (run only on trigger)

Reuse existing briefs, test receipts, and handoffs. Convene an exchange **only** when a trigger below applies:

| Trigger | Participants | Required output in existing record |
| --- | --- | --- |
| New outcome, changed mandate, or consequential handoff | Owner + affected implementers | Aligned effect, acceptance, write scopes, authority, dependencies, and next checkpoint. |
| Meaningful checkpoint (failed check, partial handoff, or slice completion) | Solo owner or accepting owner + workers | [Learning review](../SKILL.md#learn-from-every-use): expected vs. observed, reuse/avoid, drift check, and next action (skip if routine pass with no new lesson). |
| Material disagreement persists after 1 direct evidence exchange | Responsible superior + disputing owners | [Decision exchange](#3-resolve-disagreement): positions, evidence, chosen action, rationale, owner, check, and reopening condition. |
| Material knowledge gap remains after bounded local checks | Owner + specialist / [Advisor Council](../../advisor-council/SKILL.md) | [Expert consultation](#4-bring-in-expertise): recommendation, uncertainty, smallest distinguishing check, and owner disposition. |
| Operating period ends or key business signal shifts | Accountable operator + affected owners | Outcome vs. commitment comparison, constraint resolution, and next bounded commitment. |
| Acceptance or ownership transfer | Delivering owner + accepting owner (+ nonauthor QA if required) | Verified integrated result, explicit unmet/unverified items, and acceptance or blocker decision. |

## 3. Resolve disagreement

1. **State concrete positions:** Each side states its recommendation, evidence, assumptions, upside/downside, strongest case for the alternative, and what check would change its view.
2. **Exchange once, then classify:**
   - *Factual dispute* → Run one distinguishing check.
   - *Design/scope tradeoff* → Accountable owner decides (supervisor within a goal; orchestrator across goals).
   - *Authorization boundary* → Route to the authority holder.
   - *Pure preference (no failed criterion)* → Log as a non-blocking suggestion and move on.
3. **Decide and execute:** The accountable owner selects and executes the best in-mandate option by value, cost, time, and reversibility—never forward bare options to the human unless the decision is explicitly user-retained.
4. **Close and reopen only on new evidence:** Execute the chosen check. Reopen only if acceptance fails or material new evidence appears; a debate never resets the 2-strike recovery count.

## 4. Bring in expertise

Use [Advisor Council](../../advisor-council/SKILL.md) or a domain specialist when trial-and-error is costly or bounded local recovery leaves a concrete capability gap:
- **Compact brief:** State the exact question, target criterion, current evidence, ruled-out attempts, and remaining recovery budget.
- **Keep ownership:** Treat expert output as a hypothesis to test with one discriminating check inside the existing recovery allowance. If inconclusive or unavailable, stop that route, record the unblock condition, and advance independent work.

## 5. Distilled sources

Checked 2026-09-29; see [cross-domain source map](operating-principles.md):

| Source | Mechanism retained | Detail excluded |
| --- | --- | --- |
| [PMI / Stanford Strategic Execution Framework](https://www.pmi.org/learning/library/framework-aligning-strategy-execution-9349) | Link strategy, selected projects, and operations. | Enterprise PMO ceremony and 6-domain overhead on small tasks. |
| [Stanford Engineering: Simple Rules](https://engineering.stanford.edu/news/conquering-complexity-simple-rules) | Define the outcome, find the bottleneck, apply a few clear decision/stopping rules. | Context-free checklists. |
| [Stanford GSB: Workplace Friction](https://www.gsb.stanford.edu/insights/workplace-friction-how-make-right-things-easier-wrong-things-harder) | Remove process friction while keeping high-consequence checks. | Eliminating necessary verification. |
| [Stanford GSB: Team Contrarians](https://www.gsb.stanford.edu/insights/do-you-have-contrarian-your-team) | Surface minority evidence early without power contests. | Manufactured debates or unanimity gates. |
| [Stanford IT: PM Scope](https://uit.stanford.edu/service/project-managers-for-it-projects/project-manager-scope) | Coordinate risks/decisions, verify support ownership, retain lessons. | Institutional committee reporting. |
