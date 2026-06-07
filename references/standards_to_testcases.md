# From Standards Clauses to Codebase Test Cases

A clause in a standards document is a normative statement ("shall …", "应 …", "不得 …").
In Standards Conformance mode the skill translates each clause into a test case whose
`target.kind` is `codebase` and whose `expected.predicate` runs over a static scan of
the target repo. This guide is the translation table.

The full schema for a `codebase` target and its result shape is in
[`schemas.md`](schemas.md). Read that first; the examples below assume it.

## The five clause shapes you'll see, and what they map to

### 1. "shall provide / shall implement / shall contain" — positive existence

**Clause shape.** "The product shall provide user authentication."
**Test intent.** Something in the repo exists that implements the capability.

```json
{
  "category": "positive",
  "target": {"kind": "codebase", "pattern": "**/*.py",
             "regex": "(?i)(auth(enticate|entication)?|login|session)"},
  "expected": {"mode": "predicate", "predicate": "result['count'] >= 1"}
}
```

- `pattern` narrows the scan (e.g. `**/*.py` for code, `**/*.md` for docs).
- `regex` is a *seed* — one or two keywords that, if present, strongly suggest the
  capability is implemented. Be liberal: a single match is enough for "shall provide".
- `predicate` is `count >= 1`. Absence is the failure mode.

### 2. "shall not contain / 不得" — negative absence

**Clause shape.** "The product shall not log user passwords in plaintext."
**Test intent.** The repo does not contain the prohibited pattern in production code.

```json
{
  "category": "negative",
  "target": {"kind": "codebase",
             "pattern": ["**/*.py", "**/*.js", "**/*.ts"],
             "regex": "(?i)console\\.log\\s*\\(\\s*.*password|print\\s*\\(\\s*.*password"},
  "expected": {"mode": "predicate", "predicate": "result['count'] == 0"}
}
```

- `pattern` may be a list — the runner globs each entry and unions the file set.
- `regex` should be tight enough to avoid false positives; if it's noisy, narrow with
  `file_match` (e.g. `file_match: "**/auth/**"`).
- `predicate` is `count == 0`. Any match is a defect.

### 3. "shall document / shall specify" — documentation existence

**Clause shape.** "The product shall include a privacy notice."
**Test intent.** A doc file contains the required topic.

```json
{
  "category": "positive",
  "target": {"kind": "codebase", "pattern": ["**/README*", "**/PRIVACY*", "**/*.md"],
             "regex": "(?i)privacy"},
  "expected": {"mode": "predicate",
               "predicate": "any('PRIVACY' in m['file'].upper() or 'README' in m['file'].upper() for m in result['matches'])"}
}
```

- Prefer matching by **file path** for documentation: README/PRIVACY/CHANGELOG files
  matter more than any one mention. The `file_match` field handles that.
- For "shall include a section", the regex can be the section header; predicate checks
  the file's text contains it.

### 4. "shall respond within / shall handle N concurrent" — runtime, NOT static

**Clause shape.** "The product shall respond within 500 ms at p95."
**Test intent.** Cannot be satisfied by grep. Mark as `skipped`, not pass.

```json
{
  "category": "error_recovery",
  "target": {"kind": "manual"},
  "expected": {"mode": "exact", "exact": {"note": "runtime conformance — requires load harness"}}
}
```

- These are NOT `codebase` targets. They are `manual` and are reported honestly as
  untested in the Conformance Matrix.
- The agent should call this out in `limitations.md` so a stakeholder knows
  the green checkmark is for the static portion only.
- If the user has a load harness (k6, locust, JMeter), wire it as a `cli` target
  pointing at the harness binary, with the perf threshold in `expected.predicate`.

### 5. Multi-file / cross-cutting — config + code + tests

**Clause shape.** "The product shall enforce access control on all API endpoints."
**Test intent.** Several files together imply the control. Use **multiple cases**
that *each* pass — a single grep is too brittle.

```json
[
  {"id": "TC-101", "category": "positive",
   "target": {"kind": "codebase", "pattern": "**/middleware/**",
              "regex": "(?i)(auth(entication)?|jwt|oauth)"},
   "expected": {"mode": "predicate", "predicate": "result['count'] >= 1"}},

  {"id": "TC-102", "category": "positive",
   "target": {"kind": "codebase", "pattern": "**/routes/**",
              "regex": "@.*require_auth|@authenticated|require\\s*\\(\\s*['\"]auth"},
   "expected": {"mode": "predicate", "predicate": "result['count'] >= 1"}},

  {"id": "TC-103", "category": "positive",
   "target": {"kind": "codebase", "pattern": "**/tests/**",
              "regex": "(?i)test.*(auth|permission|forbidden)"},
   "expected": {"mode": "predicate", "predicate": "result['count'] >= 1"}}
]
```

- One clause → many cases. The classical expander does this automatically when the
  test model has multiple variables; for static checks you author the cases directly.
- Aggregate in the report: the clause is "pass" only if **all** its cases pass.

## Predicate cookbook for the five shapes

| Clause shape | Predicate | Notes |
|---|---|---|
| positive existence | `result['count'] >= 1` | the most common; default |
| negative absence | `result['count'] == 0` | any match = fail |
| file-path match | `any('X' in m['file'] for m in result['matches'])` | use with `file_match` |
| regex-in-text | `any(re.search(PAT, m['text']) for m in result['matches'])` | re is in safe builtins |
| coverage % | `result['count'] / max(result['scanned_files'], 1) >= 0.5` | e.g. ≥50% of files |
| all-of-multi-case | report aggregates the per-case status; no predicate needed | the framework handles this |
| runtime (out of scope) | mark as `manual` and skip | be honest |

The `safe` builtin set available in `expected.predicate` is:
`str, len, int, float, abs, min, max, any, all, bool, sorted, round, re`.
Use `re.search` / `re.match` when the regex is too rich for the target's `regex`
field alone (e.g. when you want to assert *shape*, not just presence).

## Authoring a test model for a standards clause

If you want the classical expander to derive the cases, fill in
`_test_model.json` like this (one model per requirement):

```json
{
  "models": [
    {
      "requirement_id": "R-007",
      "title": "access control on API endpoints",
      "variables": [
        {"name": "area", "type": "enum",
         "partitions": [
           {"label": "middleware",  "valid": true,  "values": ["**/middleware/**"]},
           {"label": "routes",      "valid": true,  "values": ["**/routes/**"]},
           {"label": "tests",       "valid": true,  "values": ["**/tests/**"]}
         ],
         "boundaries": []}
      ],
      "decision_table": null,
      "target_template": {"kind": "codebase", "pattern": "**/*",
                          "regex": "(?i)(auth|require_auth|jwt)"},
      "states": null
    }
  ]
}
```

The expander generates one case per partition with `pattern` set to the partition's
value (the variable's first partition value, when the template has no explicit
`pattern` field). `expected.predicate` becomes `result['count'] >= 1` (positive
existence) by default — fine for most "shall" clauses. For "shall not" clauses,
author the cases directly in `02_testcases.json` with
`expected.predicate = "result['count'] == 0"`; the expander's positive-existence
default is not appropriate for prohibitions.

## What you should NOT reduce to a static check

These clause shapes cannot be grep-validated and must be reported as
**runtime / not-exercised**:

- Latency, throughput, capacity, scalability (need a load harness).
- Correctness of encryption, hashing, randomness (need a test that exercises the function).
- Concurrency safety, race conditions, deadlock-freedom (need a stress test).
- Interoperability with another system (need an integration test).

Mark them as `target.kind == "manual"` in the test suite. The Conformance Matrix will
show the clause as `skipped` and `limitations.md` will enumerate why. This is the
correct, honest outcome — green-by-omission is the failure mode the skill is designed
to prevent.
