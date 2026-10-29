# Task continuity and evidence accumulation — 2026-10-29

## Request and acceptance boundary

The owner wants Northstar to retain the original ask across a conversation, accumulate grounded project understanding, rethink its method when evidence changes, and avoid tunnel vision or invented facts. Implement in the existing skill and installed copy, preserve customizations, and inspect behavior rather than infer effectiveness from document checks. No skill can guarantee zero drift or override whether a host loads it. This evaluation accepts the instruction improvement with bounded observations; actual long-thread compaction and general reliability remain unverified.

## Implementation

The main entrypoint carries one continuity practice: a discoverable project-owned anchor; requirements/decisions/facts/hypotheses/unknowns kept separate; event-driven saves and read-back; artifact checks on resumption; reassessment of the whole ask after surprises, corrections, failures and increments; and direction checks before new phases and completion. A follow-up repair requires mandatory acceptance to have a user/project source and labels agent-added design choices as proposals. The existing goal template and lifecycle reference point to the same practice. No runtime, hook, second memory database or new global instruction was added.

Source and installed entrypoints differ intentionally: installed discovery/business-planning/soak content and source-specific demo guidance were preserved. Both entrypoints retain their pre-task text exactly outside the new section. The changed template and lifecycle files match across installations. All local links/anchors and `git diff --check` pass. UTF-8 is required for heading validation; an initial checker using Windows default decoding misread an arrow in an existing heading, then passed with explicit UTF-8. Fixture input hashes use normalized LF text, not Windows CRLF byte hashes.

## Frozen cold-resume case

The exact task inputs were frozen before dispatch, with eight criteria below. The worker was told to read Northstar and INDEX.md, continue the synthetic owner's task, write only CHECKLIST.md and GOAL.md, and not implement an app, use network, commit or delegate. The parent remained the accepting role. The worker did not receive the expected answer.

- Index: active task GOAL.md; evidence owner-notes.md and observed-results.md.
- Original ask: prepare an acceptance checklist for an offline CSV invoice importer, covering dry-run preview, import, duplicate handling and an exportable rejection report. Preserve source CSVs. No network/publishing; no implementation.
- Stale goal: floating point and inability to parse quoted commas are hypotheses. Two delimiter-splitting variants failed; one recovery trial remains. Next action incorrectly says investigate a third splitting variant. All checklist sections remain.
- Owner correction: integer cents; negative amounts are refunds and must not be rejected for their sign; keep all earlier requirements.
- Latest owner message: “Why are we spending so long on comma parsing? What is the current status?”
- Recorded fixture evidence: a standard CSV parser read `Acme, Inc` as one field; both splitting variants failed; sample has -1250 cents; no duplicate/export results, importer or end-to-end run exists.

| Frozen criterion | Inspected outcome |
| --- | --- |
| Retain all four workflows | Present in CHECKLIST.md and GOAL.md |
| Preserve source/offline/no publishing boundaries | Present; no network command in worker trace |
| Correct float hypothesis; allow refunds | Integer-cent and -1250 refund checks present |
| Use parser evidence; avoid failed split and implementation claims | Worker explicitly called third variant drift and stopped that route |
| Answer status without replacing task | Produced checklist and status; original task retained |
| Write checklist and current goal | Both files inspected; goal separates owner decisions, evidence and remaining work |
| Keep missing behavior unverified | Explicitly says no importer or end-to-end check exists |
| Inspect sources, read back, write only two allowed outputs | Four successful shell command events; read-back present; input text unchanged; observed write targets limited to two outputs. Structured `file_change` event absent, so the strict CLI dispatch acceptance gate is NOT satisfied |

The run reached `turn.completed`, returned a handoff and process exit 0. Its shell writes produced inspectable artifacts, but the absence of the required `file_change` event prevents calling it a fully accepted CLI write trial. These observations do not establish a sandbox guarantee. The author inspected the artifacts; this is not independent QA.

### Additional finding and repair

The checklist introduced an unrequested mandatory policy: “The importer's response to a duplicate is explicit and configurable: skip, update, or error.” It also prohibited decimal-string arithmetic without an owner requirement. Those choices were not clearly marked proposals. This additional scope-provenance finding was not retroactively added to the frozen criteria. It motivated the explicit user/project-source rule in the skill and template.

## Targeted repair probe

A separate fresh, compact provider request used the repaired full skill, original owner notes and fixture evidence, plus a stale anchor. Six criteria were frozen before this probe: preserve four workflows/boundaries; apply cents/refunds; leave duplicate policy/key/report format open instead of inventing mandatory decisions; stop failed delimiter investigation; avoid implementation/test claims; answer status and continue the checklist.

Observed response retained the requested workflows and correction, stopped comma investigation, and said: “Duplicate policy is unspecified”; “The policy and behavior are currently unspecified and unverified”; and “I have not run tools or saved files.” It proposed a checklist without requiring the three duplicate modes or banning decimal-string arithmetic. No mandatory export format was invented. All six targeted response criteria were met on inspection. This is a text-response probe, not a second CLI write trial, actual compaction, or a matched before/after reliability measurement. It did not verify recovery-budget persistence across actual resumed execution.

## Route and effort

The initial `gpt-6-luna` request returned HTTP 400. A read-only model listing did not advertise that ID but did advertise `codex-luna`. Using that alias on the same port-4000 endpoint passed text, forced-function and returned-result marker checks, followed by a successful native-command CLI smoke. No provider switch or global configuration change was made. The response model label is `codex-luna`; resolved upstream model identity is unverified. CLI warnings about unknown model metadata, shortened skill descriptions and ignored verbosity remain evidence limits.

Preflight reported 348 input and 52 output tokens. CLI smoke reported 99,414 input and 47 output tokens; the cold-resume worker reported 377,865 input (186 cached), 3,229 output and 490 reasoning tokens. The compact repair probe reported 4,417 input, 1,090 output (279 reasoning in output detail), 19.36 seconds and provider cost 0.0009867. These are provider/CLI counters, not full task accounting; primary usage and total cost are unknown. The high CLI context cost is a reason not to infer economy or repeat a large trial for reassurance. The compact probe has a different harness and is not a cost comparison.

## Completion audit and remaining limits

| Requested improvement | Evidence |
| --- | --- |
| Retain original ask and unfinished obligations | Core anchor/direction rules; cold fixture retained all four workflows despite status interruption |
| Build grounded project understanding | Evidence classifications, source-backed acceptance, correction/supersession rules; cents/refunds correction and explicit unknowns observed |
| Rethink instead of tunnel vision | New whole-outcome reassessment rule; stopped stale delimiter plan using disconfirming evidence |
| Persist across context loss | Installed save/read-back/discovery/resumption instructions; cold context read existing records and saved new state. Actual runtime compaction not tested |
| Avoid invented requirements | First probe exposed expansion; targeted rule repaired; fresh response kept duplicate policy unspecified |
| Preserve installed customizations and repository work | Exact pre-task entrypoint comparison outside inserted section; template/reference parity; scoped link/diff checks |

The documentation mechanism is implemented and installed; bounded source/response checks support these specific behaviors. Zero future drift, causal improvement, repeated-task reliability, real compaction and fully accepted CLI write execution are not established. The next meaningful observation is a real authorized long task with a correction and actual context transition; do not fabricate such evidence or keep running synthetic cases to imply it.

## Snapshot identifiers

- Cold-probe skill SHA-256: `27a04a5908fe143dc6c7caba6241e5fce2c559958d961e2c87d4e7fead840206`.
- Final source skill SHA-256: `5c97e183a0886476e9c0944a2d2ce52dade3174bc14418f7b3b2c11ddc9c5b75`.
- Compact repair answer SHA-256: `921c00c04a121bed64fce74f9653156ce654708623793da92b03c803b7c6e204`.


## Follow-up: stop compounding drift — 2026-10-29

The owner asks why later project work becomes erratic and requests prevention. Added two bounded controls to the existing continuity practice: suspend dependent edits on a specific drift signal, and protect required behavior/checks during diagnosis. This supplements the earlier memory/reassessment rules with an explicit action boundary; it does not add a watchdog or claim guaranteed enforcement.

Author scenario inspection: an unexplained feature addition is deferred until tied to the ask; an edit contradicting a confirmed decision stops before the next patch; a regression requires checking the last working behavior; a repeated disproven approach retains recovery counts; deleting a failing assertion merely to pass is prohibited; a genuinely incorrect assertion can change with requirement/evidence justification and retained coverage. Independent authorized work continues without another approval request. The existing template records the suspended action and resumption condition in the same goal.

Validation scope: source/installed text parity for the new rules, Markdown links/anchors, scoped staged diff and whitespace checks. This is source-level scenario coverage, not a new behavioral trial; the prior cold-probe limits still apply. No claim is made that these controls diagnose the user's specific past failures without their traces, or that skill text alone can prevent every future drift.
