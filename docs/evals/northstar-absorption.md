# What Northstar should absorb next

Date: 2026-10-22. [Goal](../goal/northstar-absorption/GOAL.md). Scope: a direction decision, not an effectiveness evaluation or implementation.

## Decision

**Absorb no new framework or SCM mechanism yet.** Execute the existing [matched real-task proof](../northstar/next-proof.md) first: keep acceptance and authority fixed, compare against the direct-agent baseline, and account for accepted outcomes, total effort, and owner rescue. The three-task cohort is diagnostic rather than statistically representative; it may miss concurrency-specific friction.

Keep Northstar's existing practices in force: intent-to-acceptance alignment, bounded delegated scope and authority, one writer per scope, independent QA, durable recovery/handoffs, checkpoint learning, and proportionate coordination. Do not add overlapping principles just because another organization uses them.

Keep the task-changeset protocol [as a design hypothesis](../northstar/adhoc-scm.md). Pilot it when real work supplies a relevant case—such as interruption after edits, overlapping tasks, dirty user files, or a base move after review. Consider a derived Smartlog-style view only if people or agents actually miss dependency, revision, recovery, or stale-review state. Defer a mandatory monorepo, Scion-scale online storage/service, duplicate task graph or ledger, global lock, and additional approval layers absent a demonstrated need.

## Evidence and reasoning

Northstar's [current direction](../northstar/README.md) sets the outcome as accepted useful work at owner standards with lower total effort and less rescue; it says the practical value and comparative superiority have not been established. The [dogfood review](dogfood-review.md) concludes that document reviews and synthetic drills do not answer the central usefulness/economics question. The [operating-system evaluation](operating-system.md) records local fixture and synthetic planning evidence, not real business outcomes or savings. The [product-delivery goal](../goal/product-delivery/GOAL.md) still leaves real intended-environment delivery unverified.

The worker inventory finds that Northstar has already absorbed many relevant methods. It identifies evidence from real accepted work as the current gap, not a missing management framework. See [inventory](../reports/northstar-absorption/inventory.md).

The Advisor council independently recommends completing the frozen three-task cohort before considering new mechanisms. Gemini flags that a small cohort may miss concurrent-work friction; Sol agrees on sequencing and says observed overlap/interruption failures could justify testing the existing SCM safeguards. The advice changed the planned next action. The [council receipt](northstar-absorption-council.json) records both opinions and provider-reported token usage; financial cost was unavailable.

The SCM research itself distinguishes transferable workflow ideas from architecture: Anthropic's [Scion article](https://www.anthropic.com/research/redesigning-source-control) presents a solution to its unusual scale and says Git remains appropriate for most repositories; Google's [monorepo paper](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/) supports the broad shared-source-of-truth context, not every Piper workflow detail; [Sapling's Smartlog and stack docs](https://sapling-scm.com/docs/overview/stacks/) provide a focused graph/recovery interaction to test only if it addresses observed friction. The detailed Piper mechanics in current research rely partly on a secondary source.

## Limits and reopening conditions

No real-task cohort or SCM pilot was run here. No new mechanism is rejected as universally ineffective; it is deferred because its local need and net value are unproven. Reopen an import when a specific real task demonstrates an unmet capability, then test the smallest mechanism against the unchanged owner standards and full effort accounting. An absent incident in three cases does not prove that concurrency safeguards are unnecessary.
