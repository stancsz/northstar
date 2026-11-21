---
name: advisor
description: Ask a frontier advisor for a checkable next action at a design fork, a repeated failed check, or a conflict in observed evidence.
---

# Advisor

You own the files, tools, edits, and validation. Use `scripts/ask_expert.py` for a standalone advisory turn.

1. Ask when local checks leave two materially different next actions, or the same targeted check fails twice. If the failure names an unavailable local dependency, probe it first. Rerun the check on the same patch and confirm the intended assertion executed. Bring a remaining failure or decision to the advisor.
2. Keep a local task state with `task_id`, `revision`, `goal`, `phase`, arrays for `constraints`, `acceptance` and `evidence`, and optional `last_advice_outcome`. Preserve constraints and use current evidence. Set a new revision after a material workspace or task-state change.
3. Ask one question and give the advisor a reason to reject your preferred action. Target 2,000 characters on round one (limit 4,000). A follow-up has 1,000 characters. Give it the latest check, its outcome and the decision that changed.
4. Read `Verdict / Do / Verify / Risk`. Confirm that the revision and evidence still apply. Execute and verify the action locally, then record the outcome in the next state. A stale, unusable, or rate-limited reply ends that consultation.

```powershell
python <advisor-skill>/scripts/ask_expert.py --state-file tmp/advisor-state.json --session-file tmp/advisor-session.json --trigger two_failed_checks --question "Which observed failure should I address first?"
```

Use the same session file for a task (default three rounds). For a code excerpt or log, use `--snippet PATH:FIRST-LAST`, `--diff`, or `--error-tail PATH`. Add `--preview` to inspect the exact packet and size locally before sending it. If a follow-up returns `packet_too_large`, put a short, faithful restatement of the goal in the state's optional `decision_focus`. Preserve the constraints, acceptance checks and full goal in the state. A local rejection spends zero rounds.

`--transport auto` prefers configured Codex text, then the gateway, then Claude Code. It can switch routes when the prior route was unavailable before generation. A completed response with missing usage remains usable. Claude consultations run outside the project directory.

After an interruption, inspect the local session with `--status --session-file PATH`. It shows the consultation ID when available, remaining rounds, possible dispatch, receipt availability, and unknown usage. On `dispatch_unresolved`, continue the local investigation and leave the interrupted call alone. On `recovered_receipt`, the prior round has been reconciled. Start another round only if the current evidence still leaves a decision that needs advice.

A state file selects v2 automatically. Plain questions and gateway images default to the original `Verdict / Next / Prompt / Risk` format.
