# Examples

- **New product idea with unclear customer and revenue model:** Ask focused North Star questions, research market/customer evidence, and challenge assumptions before coding. If the thesis remains uncertain, set a bounded validation goal with a decision threshold and a route to a production product.
- **Known goal, unfamiliar SDK:** `AUTO` for bounded reversible investigation and implementation. The AI reads authoritative docs, builds the smallest integrated slice, and verifies it; it does not ask the user to choose an SDK without first comparing options.
- **Complex local refactor with tests:** `AUTO` when bounded and reversible, even if implementation complexity is high. The AI researches dependencies and verifies behavior.
- **Production deployment with a known rollback:** `GUARD`. Prepare and verify the release, then stop for explicit approval before deploy.
- **Privacy-impacting architecture with unresolved product tradeoffs:** `CHALLENGE`. Present evidence, viable alternatives, consequences, and a recommendation for human decision.
- **Brand or positioning choice:** `COCREATE` when the product owner owns the taste or positioning call; bring evidence and options rather than asking an open-ended question.
- **Writing a personal apology where authenticity is the point:** `HUMAN_ONLY`.
