---
name: q4-collaboration-protocol
description: Use when a user asks to delegate work between people and AI agents, classify autonomy or approval levels, create a human-in-the-loop contract, design agent escalation or handoff rules, or apply the Q4 AUTO, GUARD, COCREATE, CHALLENGE protocol. It routes each meaningful task by consequence risk and complexity or uncertainty, separates intent, initiative, execution, acceptance, and commit authority, and requires evidence before consequential action.
---

# Q4 Human-AI Collaboration Protocol

Use this skill to make collaboration authority explicit and executable. It is a task-level protocol, not a claim that an agent is trustworthy by default.

## Workflow

1. Decompose the request. Do not assign a whole project one permanent mode.
2. Check `HUMAN_ONLY` first. Use it for consent, dignity, personal expression, learning, policy, or any work where reliable verification is unavailable.
3. Classify consequence risk. Any production, money, permissions, privacy, security, compliance, external representation, non-sandbox, irreversible, or non-simulable impact is high risk.
4. Classify complexity or uncertainty. Two or more of ambiguous goal or acceptance, novelty, interacting dependencies, implicit value judgments, difficult verification, or reasonable expert disagreement is high complexity. Missing classification evidence defaults upward.
5. Route: low/low `AUTO`; high-risk/low-complexity `GUARD`; low-risk/high-complexity `COCREATE`; high/high `CHALLENGE`.
6. Produce a contract using `assets/collaboration-contract.yaml` and validate it. Read `references/contract-schema.md` before authoring nontrivial contracts.
7. Execute only inside the contract. Escalate on verifier failure, novelty, scope or permission expansion, budget overrun, unresolved disagreement, irreversible side effect, or security or privacy concern. Never lower supervision autonomously.
8. At a human handoff, use only the typed calls in `references/protocol.md`, including recommendation, alternative, evidence, impact, rollback, and deadline.

## Mode summary

| Mode | Use | Commit |
| --- | --- | --- |
| `AUTO` | Low risk, low complexity, objectively verified and reversible | Automatic only within reversible bounds |
| `GUARD` | High risk, mechanically understood | Explicit `human.approve_commit` |
| `COCREATE` | Low risk, open or subjective work | Human |
| `CHALLENGE` | High risk and high uncertainty | Human, with AI as structured dissent |
| `HUMAN_ONLY` | Human sovereignty or no safe verification | Human |

## Commands

```powershell
py -3 scripts/q4_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
```

Read `references/gde-integration.md` when using `GOAL.md`; read `references/routing-rubric.md` for classification nuance; read `references/examples.md` for worked cases.
