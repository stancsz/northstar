# Goal: Clear, economical subagent dispatch context

Status: wording change accepted with limited replicated Claude CLI evidence; broad effectiveness remains unproven

## Outcome and acceptance

Improve Northstar's existing Codex subagent assignment guidance so delegates receive the context needed to act without inheriting unrelated history or guessing at the task.

- Keep the existing five brief elements and role/accountability rules.
- State the assigned result, immediate next action, essential facts, acceptance criteria and scope/authority limits explicitly in the prompt; link only supporting background.
- Name consequential unknowns and use a brief understanding check only for substantial or ambiguous assignments.
- Do not add an arbitrary prompt length limit or routine extra approval turn.
- Independently review realistic dispatch scenarios and compare bounded native and CLI trials using matched inputs and unchanged acceptance.
- Record observed outcomes, actual usage where available, route/model, failures and remaining uncertainty.
- Inspect changed instructions, local Markdown links and installation paths, and `git diff --check`.

The root cause remains only partly established. Claude CLI matched trials show treatment completing a small inventory task where control did not; native outcomes show no regressions and one retrieval/handoff proxy improvement. Codex CLI failed in both conditions before producing task results. This is not proof of general drift prevention or total token savings.

## Ownership and tasks

The primary agent owns the skill edits, bounded trials, goal/index/evaluation records, integration and final acceptance. The independent reviewer owns the scenario and trial review. Preserve unrelated staged and unstaged work. Commit and push only the scoped guidance and evidence files after the repeat Claude treatment advantage; do not include other worktree changes.

1. Primary: update the existing Codex Subagents task brief and manager templates. See [implementation report](../../reports/dispatch-context/implementation.md).
2. Primary: run matched native and CLI trials on identical inputs; record the CLI results in the [trial report](../../reports/dispatch-context/cli-trials.md).
3. Independent reviewer: inspect the instructions, scenarios and trial evidence; write only [review report](../../reports/dispatch-context/review.md).

## Acceptance record

The primary accepts the documentation change after inspecting the source, the independent review and the [evaluation](../../evals/dispatch-context.md). The new brief wording retains the five assignment elements, keeps acceptance and authority constraints explicit, and applies the understanding check conditionally. The Claude CLI replication showed a bounded completion advantage for treatment with identical fixture hashes; no observed treatment acceptance regression occurred. The three native pairs were correct in both conditions. Codex CLI did not yield a comparable result.

All six bundled skill entrypoint paths, the installation guide reference, scoped local Markdown links and `git diff --check` must pass before handoff. This accepts a narrow prompt-guidance change, not a claim of broad effectiveness. Codex CLI and total token/time savings remain unresolved.
