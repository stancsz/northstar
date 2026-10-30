# Skill learning and feedback

Follow the [Northstar learning loop](../SKILL.md#learn-from-every-use): act, compare expected vs. observed results at meaningful checkpoints, record lessons that change future action, and apply them on resume.

## 1. Keep one compact local lesson entry

Update the project's existing goal, task record, or handoff—never create a separate file per checkpoint. For routine passes with no new lesson, write one line (`No new lesson; checks linked above`).

When a checkpoint reveals a reusable method, failed path, or instruction drift, record one compact block:

```markdown
- **Checkpoint (task & rev):** [Expected vs. observed result + evidence link]
- **Reuse:** [Verified method & matching conditions | none]
- **Do not repeat:** [Failed approach, exact error, and reopening condition | none]
- **Drift / Decision:** [Intent/acceptance check → retain, adjust method, or escalate + next action]
```

- **Keep facts distinct:** Separate verified causes from unverified hypotheses. Never erase a failed attempt to make history look clean, and never claim time/token savings without measured comparison.
- **Carry across handoffs:** On resume or delegation, read prior `Reuse` and `Do not repeat` entries so a new agent or context reset never retries a ruled-out approach.
- **No silent authority expansion:** A local lesson refines *how* to execute within scope; it cannot weaken user requirements, grant permissions, or auto-edit global installed skills.

## 2. Contribute sanitized issues to Northstar (optional)

Use [stancsz/northstar Issues](https://github.com/stancsz/northstar/issues) when a task exposes a reusable bug, ambiguity, or improvement in the Northstar skills:

1. **Recommend once at handoff:** Briefly note the observed skill lesson and ask once if the user wants to file a sanitized issue (unless standing user authorization to submit issues is already active).
2. **Sanitize completely:** Strip all credentials, private code, customer data, local usernames/paths, and raw transcripts. Include: title, affected skill/revision, generic environment, expected vs. observed behavior, and proposed fix.
3. **Deduplicate and respect authority:** Search existing open/closed issues first. Never post publicly without explicit user permission; if network or permission is absent, leave the sanitized draft in the local task record with the repo link.
