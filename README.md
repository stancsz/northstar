# Q4 Collaboration Protocol

An installable, standard-library Python skill for routing human-AI work by risk and uncertainty. It operationalizes five distinct authorities: intent, initiative, execution, acceptance, and commit.

The modes are `AUTO`, `GUARD`, `COCREATE`, `CHALLENGE`, and the `HUMAN_ONLY` veto. High-consequence tasks never receive an automatic commit; unknown classification evidence is conservative.

## Quick start

```powershell
py -3 scripts/q4_route.py --input assets/task-intake.json --output contract.json
py -3 scripts/validate_contract.py --input contract.json
py -3 -m unittest discover -s tests -v
py -3 scripts/package_skill.py --output q4-collaboration-protocol.zip
```

`q4_route.py` turns task intake into a JSON contract. `validate_contract.py` checks critical safety invariants, such as explicit approvals for GUARD and CHALLENGE, independent acceptance in AUTO, rollback information, no approval by silence, and child-boundary non-expansion.

See [SKILL.md](SKILL.md) for the operating workflow and [references/protocol.md](references/protocol.md) for the complete policy. This is a governance aid, not a replacement for organizational controls, expert judgment, or legal obligations.
