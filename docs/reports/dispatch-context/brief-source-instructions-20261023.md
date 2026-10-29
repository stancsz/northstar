# Brief source and instruction guidance

Goal: [dispatch context](../../goal/dispatch-context/GOAL.md). Scope: the Guidance placeholder in the two Codex Subagents brief templates.

## Outcome

Both brief templates now require the assigning parent to hand a worker the applicable repository instructions and the essential source/test facts, to reserve links for supporting background, and never to instruct a worker to skip required instructions. No other brief element changed.

## Changed paths

- `skills/codex-subagents/templates/orchestrator.md` - Guidance placeholder only.
- `skills/codex-subagents/templates/supervisor.md` - Guidance placeholder only.
- `docs/reports/dispatch-context/brief-source-instructions-20261023.md` - this handoff.

The Guidance text is identical in both templates, so an orchestrator brief and a supervisor brief now carry the same dispatch guidance.

## Guidance text added

`- Guidance: <intended value; must-know facts needed now; next action; fallback or escalation trigger. Put applicable repository instructions (for example `AGENTS.md`) and the essential source/test facts in the prompt, or name their exact path. Link supporting background only; do not paste unrelated history or rely on a link for essential instructions. Never tell a worker to skip required instructions.>`

## Rationale

The recorded helper-contract-test dispatch asked for one test file only, yet the worker's structured events also showed transient writes to `tmp/probe/env-probe.ps1` and `tmp/probe/mutation_check.py`. The parent later verified both paths are absent, but that absence does not make the run scope-compliant: the out-of-scope events are the delegation-quality finding on record ([trial log](cli-trials.md#2026-10-23-helper-contract-test-passes-worker-scope-deviation-recorded)).

An earlier brief in the same goal forbade rereading `AGENTS.md` and omitted the source-direction excerpts. The log records that as a possible source of instruction friction and explicitly not a proven cause. A brief that withholds required instructions, or asks a worker to skip them, removes the constraints that keep the worker inside its scope, and the parent cannot recover them from the artifact afterwards.

The new wording therefore does three things in the existing placeholder: put applicable repository instructions and essential source/test facts in the prompt or name their exact path, limit links to supporting background, and forbid telling a worker to skip required instructions.

## Scope kept

The five brief elements, the route field, the acceptance and accountability rules, and the Dispatch timing field are unchanged. No new field, no prompt-length rule and no extra approval step were added. The parent keeps its existing authority to trim or omit fields; the change only names what must survive that trimming.

## Checks

- `git diff --check -- skills/codex-subagents/templates/orchestrator.md skills/codex-subagents/templates/supervisor.md` - clean, apart from the repository's existing LF/CRLF working-copy warnings.
- Local Markdown links in both templates: 9 unique links per template, 18 instances, all resolve; every fragment matches a heading in its target file.
- No test, build, package, network call, cleanup, commit or push was run, and no path outside the three listed above was written.

## Route and usage

Dispatched through the documented Codex helper against the local route at `http://127.0.0.1:4000/v1`, model alias `default`, Responses protocol. The orchestrator-supplied read smoke returned its exact marker with one successful `command_execution`, `turn.completed`, exit 0 and no file changes; no credential or key value is recorded here. Usage for this worker's own calls was not reported to this worker, so cost is unknown.

## Limits

This is a prose change to two templates. It was reviewed against the recorded failure and the templates were diffed and link-checked, but it was not behaviorally tested by dispatching a worker under the new guidance, so it is not evidence of improved scope compliance. The cause of the recorded out-of-scope events remains unestablished. The orchestrator owns acceptance.
