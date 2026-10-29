# Native versus nested CLI dispatch evidence

The baseline read-only Codex invocation, using the documented Subroute settings, emitted a structured native `command_execution` that read the assigned synthetic JSON file, returned its exact marker (`NS_RAW_ffc7e595a00f4d1cb19722380bdc4714`) and a handoff, then completed with `usage.input_tokens=37955`.

The plugins-disabled variant still emitted the warning that skill descriptions were shortened. Its only `command_execution` launched a nested `codex exec`; that child failed before reading the target with `Could not find home directory` / `Error finding codex home`, and the outer worker stopped without source edits.

Disabling plugins did not demonstrate context savings. The prompts were not identical, so the usage values are not a valid matched token-reduction comparison. This is a narrow guidance repair for the observed nested-CLI failure, not general reliability proof.
