# Evaluate skill behavior with compact receipts

Use when the owner requests skill-effectiveness evaluation or a changed instruction needs behavioral evidence. This is a Markdown practice in the existing project review record, not a runtime harness or a new required record for every delivery. Preserve [checkpoint lessons](../../northstar/references/skill-feedback.md) and [capability accounting](../../subagent-orchestration/SKILL.md#allocate-capability-and-cost).

Before execution, freeze the case, source revision or file hashes, task inputs, allowed actions and expected observable outcome. Use a fresh context that has not seen the solution; distinguish synthetic fixtures, recorded tool outcomes and live integrations. Do not hide the relevant instruction from the worker. The nonauthor evaluator inspects actual artifacts and forbidden side effects, not just the worker's summary. Keep expectations unchanged after observing the result; record repairs and rechecks separately.

One row per case is usually enough:

| Case and frozen criterion | Skill snapshot / environment / actual model | Observed artifact and evidence | Outcome, intervention and next action |
| --- | --- | --- | --- |
| <case; expected output and forbidden effects> | <revision/hash; fresh or shared context; model/effort if exposed, otherwise unknown> | <commands/actual output or transcript; hashes and safe evidence link> | <pass/fail/unverified; attempts, rescue/repair, lesson, owner/check> |

For a useful evaluation, include an ordinary path and a relevant failure or authority boundary. Preserve failures in the case set, distinguish a second attempt from first-pass success, and recheck repaired scope. Link the reviewed artifact revision so later edits do not inherit an obsolete pass. A concise sanitized durable receipt should retain enough input, action and output to inspect the conclusion even after disposable scratch disappears; never rely only on a temporary filename.

Record actual available wall time, model/provider usage and interventions, including primary setup, advice, review and rework. Unknown effort or cost stays unknown; provider tokens alone are not total project cost. For Advisor calls preserve each model's opinion, usage, failure and `decision_changed` with the concrete action it affected. Advice remains separate from independent acceptance.

Use claims that fit the method: a document walkthrough establishes instruction coverage; a cold probe establishes that observed behavior in that case; one real submission establishes that submission path; offline tests establish their tested contracts. A simulation is not a provider or sandbox test. To claim improvement or savings, run matched cases from comparable starts with unchanged criteria, an uncontaminated control, appropriate repeated observations and full accounting. Otherwise report bounded feasibility and what remains unverified. Do not turn a few probe passes into a success-rate, host-compatibility or long-session reliability claim.
