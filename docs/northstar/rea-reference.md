# REA as a reference for Northstar's skill stack

Inspected 2026-10-29 at upstream `morluto/rea` HEAD `1da304b28213ca7a50f6787eae716abe73c4e628`. This is a focused reverse-engineering note for workflow and packaging decisions, not a complete security, code, or product audit. See the [REA repository](https://github.com/morluto/rea), its [installation and setup guide](https://github.com/morluto/rea/blob/main/docs/installation.md), [guided MCP workflow contract](https://github.com/morluto/rea/blob/main/docs/mcp-prompts.md), and [MCP result contract](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md).

## What REA is

REA is a local analysis toolkit exposed through an MCP server and CLI. Its tools inspect varied artifacts and application behavior; its packaged agent guidance helps select and sequence those tools. It supports multiple agent clients, installs the bundled workflow into client-specific skill locations, and separates tool registration from workflow installation. It is a reference for this goal, not a Northstar dependency.

The important workflow seam is explicit: discover tool/workflow capability, use guided instructions as optional starting points, inspect evidence in tool results, then explain or implement from those facts. A prompt does not itself call tools, alter state or grant authorization. REA contracts distinguish normalized result from raw provider data, identify retained evidence, and preserve coverage and limitations rather than treating missing data as absence.

## Patterns that transfer

- **Instructions travel with the capability.** Install workflow guidance for each selected agent, and name the actual destination and activation/restart state.
- **Probe the scope that matters.** REA's readiness examples select one client, skill or provider; an audit-wide health result is not required to establish a narrower capability.
- **Keep discovery, guidance and execution distinct.** A listed/rendered workflow is guidance, not execution. Capability inventory is not proof that a selected operation succeeds.
- **Make handoffs evidence carrying.** Preserve source identity, result, unknowns, and limitations. Do not make downstream acceptance rely on worker claims alone.
- **Keep permissions and state-changing execution explicit.** Setup previews selected changes; tools and prompts cannot broaden target scope or authorization.
- **Use stable interfaces across clients.** The CLI and MCP paths share workflow contracts, while client-specific installation remains explicit.

## Northstar fit and boundary

Northstar already has most analogous concepts: a central coordinator and conditional companion skills; scoped worker briefs and handoffs; evidence-based QA; checkpoint learning; bounded Soak guidance; and explicit install instructions. The initial package review found no concrete Claude Code destination for the optional Soak skill. That gap is now addressed in the [install guide](../misc/install.md#install-the-optional-soak-testing-skill), which gives Codex and Claude personal skill paths and covers isolated Claude profiles. The copy/hash evidence is recorded in the [active goal](../goal/rea-skill-stack/GOAL.md); agent runtime discovery remains unverified.

Absorb only these workflow and packaging patterns in original wording. Do not vendor REA source, its MCP server, prompts, generated catalog, or installation machinery. Northstar remains a Markdown-first skills package. REA is MIT-licensed according to its repository metadata, but that does not create a need to copy code or text. Since there is no dependency, no third-party runtime/license bundle is needed.

## Limits

This review used public README and selected setup, prompt and result-contract documentation at the revision above. It did not install or execute REA, inspect every provider/tool implementation, test its setup transaction, or compare its runtime behavior. The patterns above are observations and fit judgments, not proof that they improve Northstar outcomes. Northstar skill-stack soak evidence is tracked separately in [the active goal](../goal/rea-skill-stack/GOAL.md).
