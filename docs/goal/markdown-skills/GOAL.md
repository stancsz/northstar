# Goal: Markdown skills and repository practices

Status: done

## Direction and source

[Northstar direction](../../northstar/README.md) and the owner's instructions: remove all runtime scripts and machine contracts; keep Markdown skills under `skills/`; use documentation heavily; require clean repositories, useful AGENTS.md guidance, meaningful commits, and a shared 100 GB artifact ceiling.

## Outcome

An agent can install and use Northstar as Markdown engineering guidance, with a clear reading path and durable documentation for direction, execution, and evaluation.

## Acceptance

- Northstar and its companion skill live under `skills/`, with Markdown entrypoints and supporting material.
- Runtime scripts, executable tests, machine contracts, schemas, YAML UI metadata, and the old packaging manifest are removed.
- Current navigation and install instructions point to the new layout.
- The repository root is minimal, `docs/` contains only subdirectories, and supporting docs live in `docs/misc/`.
- `AGENTS.md` and both skills explain documentation upkeep, scratch ownership, scoped ignore rules, meaningful commits, and the shared storage limit.
- Existing historical goal content is preserved under `docs/goal/`.
- Changes are reviewed for broken links, obsolete instructions, unintended files, and whitespace problems.

## Constraints

Keep this a collection of practices. Do not introduce replacement tooling. Preserve the owner's quality, comparison, critic, verifier, and point-of-no-return guidance. Commit directly to main as requested. Project artifacts stay below 100 GB, including ignored files and attributable copies.

## Result

Both skills now live under skills/ with Markdown support material. Runtime machinery is removed, the root has only essential files, and install/translation docs live under docs/misc/. The docs/ directory contains only subdirectories. The historical goal was moved without altering its contents.

Documentation maintenance, agent/subagent hygiene, meaningful commits, and the shared 100 GB artifact limit are recorded in the skill and repository instructions. Local links, ignore behavior, storage use, and historical preservation were inspected; see the evaluation for observations and limitations.

Remaining work within this goal: none. Behavioral evaluation of the skill on real product tasks remains a separate product question.

## Evaluation

[Restructure review](../../evals/markdown-skills.md)
