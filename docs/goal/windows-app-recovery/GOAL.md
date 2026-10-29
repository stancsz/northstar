# Goal: Windows app recovery skill

Status: done

## Outcome

Package the existing Windows app recovery skill in Northstar as an optional standalone utility, without changing the five-skill coordinated workflow bundle.

## Acceptance

- Copy the skill entrypoint and its narrowly scoped PowerShell helper into `skills/windows-app-recovery/`.
- Route relevant requests from the central skill; document separate installation and clearly state that copying the skill does not register a scheduled task.
- Keep English and Chinese package descriptions accurate about the five coordinated skills and the optional utility.
- Inspect package links, skill validation, whitespace, and the available runtime evidence; record limits without claiming an induced crash recovery.

## Result

The optional skill and helper are in the repository. The central skill, English and Chinese READMEs, direction, contributor instructions, and install guidance distinguish it from the five coordinated skills. The detailed review and runtime limits are in the [evaluation](../../evals/windows-app-recovery.md).
