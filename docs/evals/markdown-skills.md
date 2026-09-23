# Markdown skills restructure review

Goal: [Markdown skills and repository practices](../goal/markdown-skills/GOAL.md)

Scope: the working-tree restructure based on commit `ab4ee1f`, reviewed on 2026-09-23 using Windows PowerShell and Git. This record covers repository organization and documentation, not a behavioral evaluation of agents following the skill.

## Observations

- Root inspection found four files: README.md, AGENTS.md, LICENSE, and .gitignore. The only content directories are docs/ and skills/; .git/ is repository metadata.
- The docs/ directory contains only northstar/, goal/, evals/, and misc/ subdirectories. Installation and translation documents are under misc/.
- Both installable skill directories contain only Markdown. Runtime scripts, executable tests, schemas, machine-contract assets, YAML UI metadata, and the packaging manifest are removed.
- All 39 local Markdown links across 17 documents resolved during review. Install instructions point to the standalone skills/northstar/ and skills/codex-subagents/ directories.
- Searching current documentation for removed runtime paths found no obsolete instructions. The historical goal intentionally retains commands from its original version and is labeled historical in the goal index.
- The moved historical goal has the same Git blob hash as the original: 728704b96dc7bf00101b05a6ac1fdec821709712.
- Ignore checks confirmed tmp/ and private environment files are ignored. Environment examples and documentation PNG/PDF/DOCX assets remain trackable.
- Workspace storage measured 278,602 bytes at inspection, including both research checkouts, Git data, and ignored files. This is a point-in-time logical file-size measurement, well below the 100 GB ceiling; no external project cache was created.
- Working and staged whitespace checks passed. Local links and both directory-layout checks were rerun successfully after moving supporting docs into misc/.

## Practice review

The updated reading path leads from AGENTS.md to direction, goals, evaluations, and the relevant skill. Northstar asks agents to maintain those records as decisions change. Delegation guidance supplies documentation context, write ownership, a scoped tmp/ directory, and shared storage accounting.

The product-reference, critic, repair, and verifier practices remain in the skill. Large operations require a space estimate before execution, attention around 80 GB, and a stop on growth that cannot fit below 100 GB.

## Limits

This was a documentation and repository inspection by the editing agent. It did not install skills into the user's personal directories or run agents against product tasks. The 100 GB limit is an instruction for agents to follow; this Markdown collection does not provide a storage-monitoring service. Behavioral quality and competitive parity require separate evaluations on actual work.
