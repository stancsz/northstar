# Spot Advisor 2.1

## Why build 2.1?

Most day-to-day coding tasks should be affordable to run. When an executor gets stuck and repeats the same failed approach, it still spends tokens and may need a person to step in. Spot Advisor gives that executor access to a stronger model for a focused decision, then lets the executor carry the work through verification.

The commercial question is whether teams can finish their daily work at a lower model cost per completed task, with fewer manual takeovers. The research question is which types of blockage benefit from advice and how much that advice changes the outcome. The earlier study compared two complete workflows. A Luna-only arm and a comparison from the same blocked state will help measure the contribution of advice.

## Product philosophy

Our goal is to make Spot Advisor the best skill in its class for everyday coding work. Compare it with the strongest available alternatives on verified task completion, total model cost per verified task, input and output tokens, and how often developers have to step in. Include both low-cost execution and direct frontier takeover in the comparison. Use evidence from repeated daily use to establish where the skill leads.

- **Finish the work and check it.** A consultation is useful when it helps the executor reach the user's acceptance criteria. The executor remains responsible for editing, running the relevant checks, and continuing the investigation if a suggestion fails.
- **Use frontier judgment selectively.** Let the lower-cost executor handle routine work. Consult when a specific unresolved decision can change the next action. Send the goal, relevant evidence, failed attempts, and one focused question. Keep each consultation to one tool-free advisory turn.
- **Make daily use simple.** The normal flow is to start work and let the skill handle a consultation when warranted. After an interruption, the executor should be able to recover the task context and continue locally. Deadline-based consultation budgeting is outside the 2.1 core scope.
- **Account for the whole task.** Include executor and advisor input and output tokens, retries, and failed attempts. Keep missing usage visible. Report model cost per task that passes verification alongside the overall completion rate and manual takeovers.

## Roadmap

Anthropic's native Claude Advisor is the primary product benchmark. The 2.1 target is stronger verified outcomes, easier daily use, and fewer total tokens per verified task. Use matched conditions and independent grading, and report the evidence for each dimension. See the [head-to-head benchmark plan](spot-advisor-2.1-execution-plan.md#head-to-head-benchmark-against-claude-advisor).

**First decision.** Expand 2.1 only where one focused consultation provides a repeatable advantage over both letting Luna continue and switching to Astra at the same blockage, with verified completion, total model cost and human takeovers measured together.

| Step | Product work | Evidence to check |
| --- | --- | --- |
| 1. Test the three choices at the same blockage | Pick a recurring failure and freeze the workspace, task evidence and acceptance checks before advice. Compare Luna continuing, Luna receiving one Astra reply, and Astra taking over. Include failed attempts and report missing usage. | Identify where advice improves verified completion, cost per verified task, or human intervention without an unacceptable loss elsewhere. Narrow the default trigger if gains are confined to a specific class. |
| 2. Improve the call for help | Give the executor practical guidance on when to consult. Check a suspected missing local dependency first. When a real decision remains, send the failing check and the evidence that distinguishes the options. Have the executor try the proposed action, rerun the relevant check, and record what happened. | Try everyday setup failures, regressions, and ambiguous diagnoses. Check that routine failures can be resolved locally and that consultations lead to a concrete action the executor can verify. |
| 3. Verify daily use and recovery | Observe developers installing and using the skill on real tasks. Exercise routine interruptions on Codex and Claude Code. Prioritize recovery fixes that prevent duplicate requests, stale advice, or manual reconstruction in the observed workflow. | Check verified outcomes, human takeovers, and voluntary repeat use. Reproduce any recovery defects against 2.0 and confirm the fix in 2.1. |

The release decision rests on two checks. The day-to-day workflow must recover from common interruptions without duplicate calls or stale advice. The evaluation must show where teams get completed work at lower cost and how often they still need to intervene. Use that evidence to decide when consultation should be enabled by default, and publish savings with the task mix and pricing assumptions that produced them.

### Receipt acceptance

Preserve the consultation trigger and task revision so the executor can explain why it asked and check whether the advice still applies. Link routing attempts under one stable consultation ID. Distinguish a possible dispatch from a confirmed outcome, and unknown usage from observed zero usage. Reconcile late provider usage where the route supports it, counting each receipt once. Validate pre-dispatch fallback, disconnect after possible dispatch, and replay of the same late receipt. Use the [receipt benchmark](advisor-receipt-benchmark.md) to compare these behaviors with public peer implementations.

[Critical review](spot-advisor-2.1-critical-review.md) · [2.0 roadmap](../ROADMAP.md) · [Research protocol](research-protocol.md) · [Installation](install.md)
