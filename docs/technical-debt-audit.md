# Spot Advisor foundation audit

This review covers the skill entry point, its transport and session code, and the evaluation paths that will support 2.1.

| Priority | Finding | Decision |
| --- | --- | --- |
| High | Live completion and crash recovery each implemented the same token accounting and pending-round update in `ask_expert.py`. A change to one path could leave the other with different totals. | Use one round-settlement function for both. Keep the existing receipt and CLI formats. |
| High | The session file and JSONL journal are separate durable writes. A crash after the pending state is saved and before the dispatch entry is written leaves an ambiguous record. An incomplete final journal line can also affect later appends. | Keep ambiguous requests from resending. Before broadening recovery, test each write boundary and define which file determines whether a round may continue. |
| High | Evaluation imports the skill CLI directly for the direct subscription transport. The evaluator also owns a separate request loop and receipt journal. A transport change can affect both the product and reproducibility of future runs. | Keep the public single-file skill entry point. Give any additional protocol parsing or transport changes one shared implementation where behavior matches, and test the skill and harness together. |
| Medium | `ask_expert.py` combines packet creation, routing, transport parsing and session persistence. Its three routes and two reply protocols have different callers and recovery behavior. | Keep the current entry point and compatibility. Isolate behavior as it changes, starting with session accounting. A broad module split has a packaging cost and should follow a concrete maintenance need. |
| Medium | The harness has multiple replay paths. Paper case regrading verifies a saved patch, while the proposed 2.1 experiment needs model context and the workspace before advice. | Reuse the existing workspace isolation and grader. Add checkpoint capture at the tool-response boundary and keep it distinct from final-patch regrading. |

The next foundation check is a local crash-boundary test paired with the 2.1 checkpoint preflight. The [execution plan](spot-advisor-2.1-execution-plan.md) describes the state needed for a fair continuation experiment.
