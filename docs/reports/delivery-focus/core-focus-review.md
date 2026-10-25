# Independent source review: core-focus consolidation

## Verdict

**UNVERIFIED.** The Markdown source reviewed is coherent on the requested delivery, approval, consultation, visual-review, and platform-boundary cases; I found no defect in those inspected instructions. I could not independently verify the separate `tests/test_codex_subagents_helper.py` extraction-path change against its source diff: the supplied `incremental.diff` is the Markdown comparison and does not include that test diff. The worker report's before/after test receipts are useful evidence, but do not substitute for this requested source inspection. Do not treat this verdict as package-effectiveness or agent-behavior evidence.

## Ask / Acceptance / Remaining

- **Ask:** independently review the completed skills/documentation consolidation against the preserved dirty baseline, especially cross-entrypoint consistency and the stated boundary scenarios; do not implement.
- **Acceptance evidence:** checked the supplied Markdown incremental diff and current source, reviewed the six core entrypoints and scoped references/templates, checked supplied link-scan results, compared the relocated helper body, and considered all eight source scenarios below.
- **Remaining:** inspect the separate test diff and confirm its import/extraction points at `skills/codex-subagents/references/cli-dispatch.md`. No further Markdown review is indicated by the evidence gathered.

## Source findings

1. The canonical contract in `skills/northstar/SKILL.md` (delivery contract, lines 10–20; authorization, lines 99–108) is the controlling policy. All six coordinated entrypoints link it. The scoped templates and protocol repeat its conclusions without creating a second approval queue: `skills/northstar/references/protocol.md:5-21`, `skills/northstar/templates/GOAL.md:30-31`, and the Codex orchestrator/supervisor templates' ownership, authority and handoff fields.
2. Consultation is now conditional on a material uncertainty or decision. `skills/codex-advisor/SKILL.md:15-46` says topic tags alone do not trigger calls, permits routine local resolution, and makes follow-up evidence/decision-dependent. The heading “Mandatory visual and aesthetic guidance” at line 25 describes evidence requirements *when consulting*; lines 29-31 expressly say accepted design reuse does not automatically require consultation, retain rendered verification, and separate the design author's advice from nonauthor acceptance. This is not a contradictory always-consult rule.
3. The focused helper comparison succeeded: the `Invoke-CodexChild` PowerShell block extracted from the baseline entrypoint and the current `cli-dispatch.md` is byte-for-byte equal after trimming trailing whitespace (3,547 characters). Its digest matches the worker report's `D2ECB7167720D39394BE0D72D75B42C34EEAE3CBB98F3BB99B2817BC95D55C35`. No runtime implementation was in the reviewed scope. The test extraction/import source remains the explicit verification gap above.
4. The supplied `checks.json` reports 408 local Markdown links checked, with no new or pre-existing errors. This review did not rerun its script. Its checked entrypoint word counts are 17,915 before and 13,964 after. I treated these as recorded check results, not independent proof of the script's implementation.
5. I used `tmp/core-focus-20261024/baseline/` as the comparison base, not Git HEAD. The checkout has substantial unrelated dirty content; no unrelated changes were attributed to this consolidation or modified.

## Scenario decisions (instruction walkthrough only)

| Case | Source disposition | Evidence |
|---|---|---|
| Existing workflow fails while a feature idea appears | Finish/repair the current commitment; defer unrelated expansion. | `skills/northstar/SKILL.md:16-18, 27-28, 68-72` |
| Required criteria pass and reviewer suggests optional polish | Stop optional work at diminishing returns; deliver. | `skills/northstar/SKILL.md:17-18, 28`; `skills/codex-qa/SKILL.md:49, 58` |
| Required criterion remains unmet | Keep it unmet; use bounded recovery or name the real dependency; do not mark Complete. | `skills/northstar/SKILL.md:18, 28, 75-87`; `skills/task-completion-review/SKILL.md:11` |
| Consequential action is covered by standing authority | Existing commander decides/executes within the grant; no additional human approval round trip. | `skills/northstar/SKILL.md:19, 99-103`; `skills/northstar/references/protocol.md:5-11` |
| Actual platform/tool denial occurs | Diagnose and preserve the boundary; no agent or blanket grant bypass. | `skills/northstar/SKILL.md:19, 102`; `skills/northstar/references/protocol.md:17, 21` |
| Approval owner authored the design | Owner may manage the disposition, but cannot provide independent acceptance of own work; a nonauthor verdict remains needed. | `skills/codex-advisor/SKILL.md:31, 46`; `skills/codex-qa/SKILL.md:44` |
| Ordinary accepted visual design is reused | No automatic Advisor call; retain appropriate rendered QA. | `skills/codex-advisor/SKILL.md:29-35`; `skills/codex-qa/SKILL.md:11, 36-40` |
| Real unresolved visual risk remains | Image-backed consultation and rendered inspection are required; do not assert unsupported taste/visual quality. | `skills/codex-advisor/SKILL.md:27-31`; `skills/codex-qa/SKILL.md:36-40` |

These are judgments about what the instructions say, not demonstrations that agents follow them or that the package improves real delivery.

## Checked source hashes

SHA-256 of current reviewed sources:

| Path | SHA-256 |
|---|---|
| `skills/northstar/SKILL.md` | `84F88ECE56C2A8AC97B21E41474D1701643878408C3507388AABF217EC7B22F9` |
| `skills/codex-qa/SKILL.md` | `98915ACAF5804DC51370CFF5A480915C7297D30AE7956548F67304DCB0186DB3` |
| `skills/codex-subagents/SKILL.md` | `22940665778954831E5CE48A43A591521DAA7159FDE95EA82209F93FF6CE45FA` |
| `skills/codex-advisor/SKILL.md` | `AFCDB198507D1E98617734BFDF371EF201D52DF33014BD88C26948B1200F71FF` |
| `skills/claude-code-subagents/SKILL.md` | `59873723E2353425CDC44E30C9BE24B26361A395FCD45B3C4FF0D9A2C451C3A2` |
| `skills/task-completion-review/SKILL.md` | `C93031F4EFFAEA502B68127BFAAAEAB613B8E4896370C3019E027F7175D0CA93` |
| `skills/northstar/references/protocol.md` | `F49AA74F5B404F84402C890FAAE180F687D84B2128ECFF710CA47A44447B153A` |
| `skills/northstar/templates/GOAL.md` | `E2A2E4A81AAB31186E858D196AB3B91B9F21E9CB0B4CAAF72E406FE1C271ECCF` |
| `skills/codex-subagents/references/cli-dispatch.md` | `0E72F2734C056240E49FBC93255FD9CE9C1A168117A66A2483243B711FDCF4D1` |
| `skills/codex-subagents/templates/orchestrator.md` | `CBD299F557BA947BBFEC3A2368443CFDEAED35F18ADFB9036BC5B161B8FED2F5` |
| `skills/codex-subagents/templates/supervisor.md` | `3F9C08D9C29A57CFF430A1554D9E24389BBDB4C5BDBE5268ECD85254476ACCD7` |

Scope limits: this was static source/link/hash inspection plus source-level scenario walkthroughs. I did not rerun the helper tests, dispatch a provider, install skills, inspect rendered UI, verify runtime enforcement, or claim behavioral effectiveness. The supplied worker report records 26 helper tests passing before and after; that remains worker-reported evidence here.
