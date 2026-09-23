# Goal: Q4 collaboration protocol skill

Status: done

## Steward-owned contract

### Outcome

Refactor this repository from the spec-driven QA skill into an installable, runnable `q4-collaboration-protocol` skill. It must route work by consequence risk and complexity or uncertainty, assign bounded human and AI authority, and reject unsafe or incomplete contracts.

### Source of truth

The user-provided conversation "研究四象限协作协议". Its required model is AUTO, GUARD, COCREATE, CHALLENGE, plus a HUMAN_ONLY veto; authority is split into intent, initiative, execution, acceptance, and commit.

### Acceptance criteria

- `SKILL.md` describes the protocol and a usable workflow, with progressive references.
- `scripts/q4_route.py` deterministically classifies valid task-intake JSON, defaults missing classification evidence conservatively upward, and emits a contract.
- `scripts/validate_contract.py` rejects authority, classification-to-mode, commit, escalation, rollback, and parent-boundary violations, including approval by silence.
- The repository includes the documented contract schema, GDE integration, examples, input/template assets, a reproducible portable ZIP builder, and automated tests for each mode plus unsafe negative cases.
- `py -3 -m unittest discover -s tests -v` passes, CLI smoke checks demonstrate both routing and validation, and the manifest builds an inspectable portable ZIP.

### Constraints / invariants

- An executor cannot accept or commit its own consequential work.
- The agent may escalate supervision but cannot autonomously lower it.
- A child contract cannot widen parent scope, permissions, budgets, or risk tolerance.
- GUARD and CHALLENGE require explicit human commit. Approval by silence is invalid.
- No deployment, publication, credential use, or external action is authorized by this goal.

### Non-goals

- A hosted control plane, identity system, or automatic human-approval UI.
- Claiming that a JSON policy alone provides organizational or legal governance.

## Builder-owned execution record

### Current approach

Replace the old QA-specific surface with a compact Python standard-library skill: route JSON intake, validate a JSON contract, and document the human handoff and GDE mapping.

### Progress

- [x] Extracted protocol requirements from the supplied conversation.
- [x] Implemented skill assets, routing, validation, and tests.
- [x] Verified CLI behavior and full test suite.

### Discoveries

- The checked-out repository is the prior `spec-driven-qa` skill and contains no runtime package or existing tests.

### Validation

- `py -3 -m unittest discover -s tests -v`: 12 passed. Covers all five modes, conservative missing-evidence routing, approval-by-silence rejection, mode/classification mismatch, high-risk automatic commit rejection, parent-boundary non-expansion, JSON schema parsing, and ZIP construction.
- `py -3 scripts/q4_route.py --input assets/task-intake.json --output .q4-smoke-contract.json` followed by `py -3 scripts/validate_contract.py --input .q4-smoke-contract.json`: generated a GUARD contract and returned `VALID`.
- `py -3 scripts/package_skill.py --output .q4-package-smoke.zip` built a ZIP containing 18 manifest files, including the skill entrypoint and validator.
- `py -3 -m py_compile scripts/q4_route.py scripts/validate_contract.py scripts/package_skill.py` and `git diff --check`: passed.

### Remaining gap

None within this repository-local skill scope. Installation and any real organizational approval workflow remain intentionally out of scope.
