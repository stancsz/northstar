# Contract schema

Every contract contains `mode`, classification reasons, authority, bounds, required evidence, escalation, rollback, and audit artifacts. Use [the machine schema](../assets/collaboration-contract.schema.json) for structural validation and `scripts/validate_contract.py` for policy validation.

Bounds define scope, permissions, prohibited actions, data access, token and monetary budgets, and retry limits. A nested task may only narrow those fields. Parent-bound checking is enabled by adding `parent_bounds` beside `bounds`.
