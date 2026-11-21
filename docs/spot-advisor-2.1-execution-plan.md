# Spot Advisor 2.1 execution plan

This plan turns the [roadmap](spot-advisor-2.1-roadmap.md) and [critical review](spot-advisor-2.1-critical-review.md) into two work packages. The next round tests a recurring blockage before widening the skill's default behavior.

## Research work package

1. **Freeze the comparison.** Start from the ordered [follow-up manifest](../eval/checkpoint_tasks.json). Record the eligibility rule, case order, analysis thresholds, and request budget in a new run manifest before seeing outcomes. Keep the existing two-arm study and paper snapshot intact. Use the current screening cap of 120 and target up to 40 eligible checkpoints for the new comparison, subject to the run budget.
2. **Build and qualify checkpoint replay.** Inspect the existing `eval/run.py` checkpoint hook and verify which state it can restore. Capture the workspace, conversation or supported resume state, failing check, acceptance tests, and remaining tool allowance. Give each arm a clean copy. If the same Luna state cannot be restored, qualify a shared transcript restart as a separate design and label that limitation. Exercise three harmless local cases before the formal run to verify isolation, grading and receipt collection.
3. **Run three continuations.** Compare Luna continuing on its own, Luna receiving one Astra reply, and Astra taking over the same blockage. Give each arm the same frozen task evidence and verification access. Match the remaining executor allowance and count any advisor cost separately within the advice arm. Counterbalance execution order, grade without arm labels where feasible, and keep failures and missing receipts in the record.
4. **Report results.** Use `eval/report.py` and the telemetry schema where they fit. Report paired verified completion, harmful advice cases, input and output tokens and total model cost per verified task, plus usage coverage. Include the common prefix in whole-task costs once per arm. Report human takeovers from observed developer sessions and label automated escalation events separately. Publish a decision for the tested class and retain the case-level evidence behind it.

## Product work package

1. **Prepare the daily-use pilot alongside research.** Freeze the skill revision used in the experiment. Capture a baseline using the Codex and Claude Code install paths and the existing advisor tests. Define a short developer trial on real tasks that covers first use, one representative interruption, and voluntary reuse. Record points that require a person to reconstruct state, retry a request, or intervene.
2. **Build the smallest change supported by evidence.** If results show a recurring failure from a wrong diagnosis, let the advisor request one discriminating local check and have the executor record the result. If interruptions block normal work, prioritize the specific resume, deduplication, or stale-reply defect. Keep the one-turn advisory flow and use the existing session file and receipts where possible.
3. **Verify the candidate.** Run the existing advisor tests, replay the triggering cases against 2.0 and the candidate, and smoke-test the installed skill in both hosts. Verify that the candidate still lets the executor continue locally after a failed consultation. Record installation friction, manual intervention and voluntary repeat use.

## Handoff and decision

The research package hands off a reproducible case set, receipts, comparative outcomes, and any cases that advice made worse. The product package hands back real install and recovery observations. Both packages can prepare their infrastructure in parallel. Changes to the experimental skill revision wait until the comparison is frozen.

Expand the default trigger only when advice has a repeatable advantage over both alternatives on the tested class, with acceptable tradeoffs in verified completion, total model cost and human intervention. If the result is inconclusive, keep the scope narrow and record the evidence needed for another round. If another workflow wins for that class, document when to use it. Publish a savings claim only when the usage coverage and pricing assumptions support it.

## Product acceptance thresholds

For the selected class of recurring blockage, compare 2.1 directly with the installed 2.0 baseline using matched cases and the same verifier. Use a gain of 10 percentage points in verified completion or 20 fewer human takeovers per 100 started tasks as a practical target for the pilot. Require the other outcome to hold up, and check model cost per verified completion against 2.0. Count human takeovers in developer sessions and report automated escalations separately.

Treat a ten-case pilot as a reason to continue testing. Report paired wins and losses, the uncertainty around the effect, and whether missing usage could change the cost conclusion. Confirm the gain on fresh cases before widening the default trigger. Assess the Luna continuation and Astra takeover alternatives under the separate research comparison above. Describe the difference from 1.0 qualitatively until a matched 1.0 baseline is available.

## Head-to-head benchmark against Claude Advisor

The primary peer is [Anthropic's native Claude Advisor](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool). Keep the same-checkpoint study for measuring the effect of one consultation. For the product benchmark, run both advisors from the same starting task with their normal consultation behavior.

- **Match conditions.** Use the same routine coding tasks, repository revisions, available tools, and independent acceptance checks. Match executor and advisor model versions, effort settings, and starting context wherever both products support them. Record any differences and distinguish a matched-model comparison from an end-to-end product comparison.
- **Count the whole job.** Collect input and output tokens for executor and advisor separately, including failed runs, retries, and repeated context. Report both total and frontier tokens per verified task, plus cost under documented rates and cache treatment. Retain unknown usage and check whether it could reverse the result.
- **Measure usability on both products.** Give developers equivalent install instructions and comparable real tasks. Record setup steps, manual takeovers, interruption recovery and voluntary reuse. Counterbalance order and report where each product creates friction.
- **Define the win before running it.** Set the completion-quality margin and minimum meaningful savings in advance. Claim a combined win only if fresh matched cases support at least comparable verified completion and lower total tokens per verified task, and developer trials show fewer interventions or a clear usability improvement. Claim stronger task performance only where the verified completion data supports it. Report narrower wins and losses by task class when the combined goal is unmet.

## Local preflight

The three-case diagnostic cohort completed all nine continuations. Regrading each saved workspace in a fresh container reproduced all nine passes. Per verified task, Luna alone used 9,278 tokens at $0.00138 API equivalent, Luna with advice used 6,994 tokens at $0.01042, and Astra takeover used 3,360 tokens at $0.03631. These selected diagnostics establish that the harness can execute and regrade the three branches. They provide no observed completion gain from advice. Keep the default trigger unchanged while checking more representative blockages. The native Claude Advisor comparison still requires an Anthropic API account with access to the advisor tool.

The budget qualification on the nested configuration copy case used 39 remaining tool calls and 120 seconds per continuation. All three branches passed. The separate product pilot solved the same case from a fresh workspace using the normal Spot Advisor trigger. It finished without an advisor call at 13,053 tokens and $0.00253 API equivalent. This establishes one runnable product arm. Developer intervention and voluntary repeat use still need participant observations.

Use `eval/claude_native_pilot.py` for the two product arms and `eval/product_pilot_report.py` for their usage and cost summaries. Compare task input and grader digests before interpreting the results. The first Spot Advisor smoke run predates automatic manifest recording. Future paired runs should use one output directory and the current manifest-producing entry point for both arms.

### Public repository qualification

The Open Library ISBNdb task passed upstream grading on all three arms in a controlled first-failure fork. Independent regrading reproduced every pass. Including the common prefix, Luna alone consumed 58,225 tokens ($0.00650 API equivalent), Luna with one Astra reply consumed 122,188 ($0.02172), and Astra takeover consumed 13,236 ($0.12404). The consultation used 520 Astra tokens within its overall total. This run qualifies repository snapshot, continuation, receipt collection, and upstream grading.

Separately, Luna passed five local diagnostic tasks and the corrected Open Library check in natural-trigger screening, with zero consultations across those six completed tasks. The qutebrowser relocation attempts ended before a usable checkpoint. The qutebrowser process-cleanup case is a regression replay selected from historical consultations. Report it separately from the new-case sample. These results support retaining the current default trigger. The rate of recovery on genuinely blocked tasks remains open.

- The advisor and evaluation suites passed 35 tests at baseline commit `8ea6c5b`.
- Two local diagnostic fixtures, `pilot-zero-capacity` and `pilot-numeric-sort`, produced the same baseline failure in three independent workspace copies. Editing one copy left the other copies unchanged.
- The existing checkpoint records a revision, exit status, trigger, and output digest. The direct executor keeps its conversation items in memory and sends stateless requests. The existing checkpoint therefore cannot restore a continuation by itself.
- The first harness implementation needs to capture the ordered conversation and tool outputs at the completed tool-response boundary before advice, then restore the matching workspace and remaining tool allowance into each arm. Verify that isolated copies receive equivalent inputs before launching any formal comparison. The local fixture check covers workspace isolation only.
