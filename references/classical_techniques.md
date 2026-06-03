# Classical Test Design — the backbone every AI test sits on

AI/rubric tests are worthless if they float free of established test design. An
LLM asked to "write tests" will produce plausible-looking cases that miss the
boundaries and condition combinations that actually break software. So this
skill generates a **classical backbone first**, mechanically, and only then
layers AI rubric and adversarial tests on top. Every AI test must trace back to
a requirement that already has classical coverage.

`classical_tests.py` does the mechanical expansion. Your job is to author a small
**test model** per requirement; the script turns it into concrete cases using the
four canonical techniques. Expansion is where coverage actually grows: one
hand-written case becomes five boundary cases and a full decision table.

## The four techniques the expander implements

### 1. Equivalence Partitioning (EP)
Divide each input into classes where the system should behave identically, then
test one representative per class — valid and invalid. Testing every value is
wasteful; testing one per class is sufficient and meaningful.

### 2. Boundary Value Analysis (BVA)
Bugs cluster at edges. For every boundary `b` the expander emits `b-1, b, b+1`,
plus the range `min`, `max`, and just-outside `min-1`, `max+1`. A "30-day window"
requirement becomes cases at 29, 30, 31, 0, 365, -1, 366 — not a single "20 days".

### 3. Decision Tables (DT)
For requirements with combined conditions, enumerate condition combinations and
their expected outcomes. Catches the "what if A and not B" cases prose hides.

### 4. State Transition (ST)
For stateful features/agents, test each valid transition and a sample of invalid
events from each state. Catches illegal-transition bugs (e.g. refund after refund).

### 5. Combinatorial / Pairwise (for multi-variable requirements)
When a requirement has two or more input variables, defects often hide in the
*interaction* between them, not in any single value. Testing the full cartesian
product explodes (3 vars × 4 levels = 64 cases); **pairwise (all-pairs)** covers
every pair of values across every pair of variables in a fraction of the cases
(usually ~10–16 for that example) while still catching the vast majority of
interaction bugs. The expander runs pairwise automatically whenever a model has
≥2 variables. Override per model:

```json
"combinatorial": "pairwise"   // default for >=2 vars; or "all" (cartesian) or "none"
```

Each variable's "levels" are one representative per equivalence partition, so
combinatorial coverage stays grounded in the partitions you already defined.

## The test model you author — `_test_model.json`

```json
{
  "models": [
    {
      "requirement_id": "R-003",
      "title": "refund eligibility by order age",
      "variables": [
        {"name": "days_ago", "type": "int", "min": 0, "max": 365,
         "partitions": [
           {"label": "within_window",   "valid": true,  "range": [0, 30]},
           {"label": "outside_window",  "valid": true,  "range": [31, 365]},
           {"label": "negative_invalid","valid": false, "range": [-3650, -1]}
         ],
         "boundaries": [30]}
      ],
      "decision_table": {
        "conditions": ["within_window"],
        "rules": [
          {"when": {"within_window": true},  "expect": "eligible"},
          {"when": {"within_window": false}, "expect": "not eligible"}
        ]
      },
      "target_template": {"kind": "python", "module": "sut",
                          "callable": "refund_answer", "arg_from": "days_ago"},
      "states": null
    }
  ]
}
```

- `arg_from` tells the expander to inject the variable's value as the first
  positional arg (python/cli) or as the body for http. For http, set
  `"body_path": "messages.0.content"` instead.
- **Multi-variable targets** (needed for combinatorial): instead of `arg_from`, use
  `"args_from": ["v1","v2"]` (positional order), `"kwargs_from": {"v1":"param_a"}`
  (var → keyword-arg name), or for http `"body_paths": {"v1":"body.a","v2":"body.b"}`.
- `expect` is a token the generated predicate looks for in the output, e.g.
  `'eligible' in str(result).lower()`. Refine the predicate after expansion if the
  SUT phrases things differently.
- `states` (optional) is a list like
  `[{"from":"open","event":"refund","to":"refunded"}, ...]` for ST expansion.

## State-transition model shape

```json
"states": {
  "transitions": [
    {"from": "open", "event": "refund", "to": "refunded"},
    {"from": "refunded", "event": "refund", "to": "INVALID"}
  ]
}
```
`INVALID` targets become negative cases (the event must be rejected from that state).

## How the layers stack

1. `classical_tests.py expand` writes EP + BVA + DT + ST cases tagged with
   `technique` and `source: "classical"`.
2. You add AI rubric cases for `is_ai_feature` requirements — but only for
   requirements that already have a classical backbone. The rubric case reuses the
   same input partitions/boundaries so the AI is judged on the same meaningful
   inputs, not arbitrary ones.
3. Adversarial cases layer on top for user-facing LLM surfaces.

`verify.py` fails the run if an AI feature has rubric cases but no classical
coverage of its requirement — that's the rule that keeps AI tests honest.
