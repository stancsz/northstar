# Fresh CLI trial: parent acceptance

2026-10-29. Verdict: **FAIL overall; narrative requirement passes, bilingual identity requirement fails.** First drafts remain untouched.

## Execution and version

Exactly one write-enabled Codex CLI worker ran via the installed Invoke-CodexChild helper with provider subroute, explicit loopback endpoint http://127.0.0.1:4000/v1, model codex-luna, workspace-write and plugins disabled. Parent text and function-call/result preflights both returned NORTHSTAR_SOAK_29. The worker's first native shell command successfully read the skill and returned D:\github\northstar as cwd. CLI exit was 0 and the structured stream ended with turn.completed. Task logs remain in tmp/demo-soak/fresh-cli.jsonl, .stderr and .exit (disposable diagnostics, not durable links).

Parent verified the current skill SHA256 matches the worker receipt: AC958D2DD09F61469F007006FD08B178B4B36435CDA36557FC661198B472C52E. The actual successful skill-read output includes the added clause below; this was a test of the revised skill, not the prior version.

> Before rendering, compare both language drafts against the shared scenario: retain exact screenshot brand, person, shop and product names (optional translated glosses may follow), name every monetary currency, and distinguish each payer's purchased service when institutions and end users both pay.

> A reader viewing the exported slides without a presenter must understand the proposal.

## Independent inspection of untouched sources

Parent read [English](first-en.md), [Chinese](first-zh.md) and [worker receipt](receipt.md) in full.

| Criterion | Result and evidence |
| --- | --- |
| Visible standalone narrative | PASS: six slides explain handoff pain, shared checklist, optional staffed delivery, buyer questions and a one-event workflow test. No essential content is hidden in notes. |
| Cross-language identity | FAIL: Pinecone Event Rentals becomes 松针活动租赁; Riverside Market becomes 河岸市集; Riverside Park becomes 河岸公园, without retaining the exact names used by the English scenario/shared screens. StageKit alone is preserved. |
| Numeric consistency | PASS for the sample: both versions have 12 tables, 48 chairs, 2 tents, June 20 2026 and 08:00. No actual monetary amount is asserted. |
| Unsupported capability promises | PASS: explicitly fictional concept; workflow described as proposed; no fabricated savings, integrations or proven delivery outcomes. |
| Payers and next step | PASS: rental company buys workspace, organizer separately buys optional staffed delivery; one-event comparison is the next step. Only workspace willingness-to-pay is elicited, so delivery pricing remains untested. |
| Shared assets | PASS at reference level only: six identical missing-image filenames in both sources. No real image identity was tested. |
| Worker self-check reliability | FAIL: receipt claims the same company/organizer identity in both languages despite name changes. Its final excerpt also paraphrases the skill while labeled exact. Parent verdict supersedes those claims. |

The narrative is understandable but repeats caveats enough to weaken the sales tone; this is a quality concern, not evidence of rendered layout failure.

## Conclusion and limits

The new sample confirms that instructions to put the story on slides can produce the intended structure. It does **not** establish reliable first-pass adherence: explicit identity instructions were still missed and the worker's own check did not catch this. Keep independent bilingual review as an acceptance step; do not label the skill issue-free or repeatably validated. This bounded test is complete with a recorded failure, not a successful soak certification. No images, PDF render, fonts, clipping, long-duration reliability or customer validation were tested. No further worker was dispatched and no first draft was patched to conceal the failure.
