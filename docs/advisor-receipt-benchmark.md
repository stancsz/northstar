# What Spot Advisor can learn about receipts

This comparison uses public documentation. It covers the record of a consultation attempt, including its outcome, timing and usage.

| Reference | What it does | What Spot Advisor can borrow |
| --- | --- | --- |
| [Anthropic Advisor tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) | Represents an advisor invocation and its result as separate events. Reports executor and advisor usage separately in `usage.iterations`, with model-specific pricing and cache counts. | Keep executor and advisor costs attributable at the attempt level. Store estimates separately from observed usage. |
| [OpenAI Agents tracing](https://developers.openai.com/api/docs/guides/agents-api/tracing) | Organizes traces by session, turn, and step. Records outcome and duration. Usage can arrive later, and a blank count means unknown. | Give one consultation a stable ID across routing attempts. Allow an existing attempt to gain usage data later through reconciliation. |
| [OpenTelemetry GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) | Specifies common names for the provider, requested and returned models, response ID, errors, and usage on model operations. The conventions are marked Development. | Align field meanings where they match. Keep the local format independent of changes to the telemetry convention. |
| [Temporal activity guidance](https://docs.temporal.io/activity-definition) | Uses a stable activity identity across retries and relies on the external system to honor an idempotency key for side effects. | Distinguish the intended consultation, each attempt, and any provider response ID. When dispatch is uncertain, only retry if the route can establish that another paid generation will be avoided. |

## How the current receipt compares

The [skill journal](../skills/advisor/scripts/ask_expert.py) already records a local attempt ID, task and revision, round, transport, requested model, returned model and provider identifier when available. It records start, possible dispatch and finish, as well as elapsed time and normalized usage. The [evaluation schema](../eval/telemetry_schema.json) preserves attempt-level data. Those are useful foundations for troubleshooting and cost analysis.

The biggest gaps are linking retries explicitly to the same intended consultation and giving usage observations enough provenance to reconcile a late receipt. Provider identifiers also need clear semantics. A response ID and an HTTP request ID are different identifiers when a provider exposes both. A completed response, a valid answer and complete usage are distinct facts.

## A small 2.1 design to test

- Keep the existing attempt ID and add one stable consultation ID across attempts. Keep the task ID and revision so the executor can check that the result still applies.
- Record the requested and returned model, transport, dispatch state, and final outcome. Retain provider identifiers when supplied and document their meaning per route.
- Preserve nullable input and output counts. Separate observed usage from estimates and allow partial or late observations. Keep cache and reasoning breakdowns only when provided and document how they relate to the totals.
- Use one versioned attempt-event contract. Derive the concise CLI summary and research export from it. Keep raw prompt, reply and tool logs out of the receipt by default.

Validate the design with a pre-dispatch fallback, a disconnect after possible dispatch, and a late usage receipt. Verify that each case can be explained from its records, that unknown usage does not become zero, and that reconciling the same receipt twice leaves the totals unchanged. This is a proposed design based on public references. It has yet to be implemented or tested.
