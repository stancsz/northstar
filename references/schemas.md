# Spec-Driven QA Data Schemas

Every artifact this skill produces is a JSON file under the run directory. These
schemas are the contract between layers. Each script reads the previous layer's
JSON and writes its own. Keep them stable.

Run layout:

```
<run-dir>/
├── 01_requirements.json     # Layer 1 — requirement graph
├── 02_testcases.json        # Layer 2 — test cases + rubrics
├── 03_results.json          # Layer 3 — execution results
├── 05_evaluations.json      # Layer 5 — LLM-as-judge + adversarial verdicts
├── defects.json             # Layer 6 — consolidated defect log
├── readiness.json           # Layer 6 — release readiness score
├── report.html              # Layer 6 — human-readable report
└── report.md                # Layer 6 — markdown mirror of the report
```

Additional working/verification artifacts: `_test_model.json` (classical test
model you author), `limitations.md` (Layer 7 — hidden limitations, required),
`verification.json` (Layer 7 — lint results), `report.png` (rasterized report
for visual inspection).

Test cases carry two optional provenance fields used by the classical backbone
and the verifier: `"technique"` (`equivalence | boundary | decision_table |
state_transition`) and `"source"` (`classical` for auto-generated cases). Every
AI/rubric case must map to a requirement that also has at least one
`source: "classical"` case — `verify.py` enforces this.

---

## 01_requirements.json — Requirement Graph (Layer 1)

```json
{
  "source": "path/to/PRD.pdf",
  "title": "Product / feature name",
  "generated_at": "ISO-8601",
  "requirements": [
    {
      "id": "R-001",
      "text": "Verbatim or lightly-normalized requirement statement.",
      "type": "functional | non_functional | ai_behavior | security | compliance | conformance_criterion",
      "acceptance_criteria": ["AC the requirement must satisfy"],
      "depends_on": ["R-000"],
      "is_ai_feature": false,
      "risk": "low | medium | high | critical",

      // Standards Conformance mode — populate when type == "conformance_criterion"
      "standard_id": "GB/T 25000.51-2016",
      "standard_name": "Software product quality — Part 51: Quality requirements and test for commercial off-the-shelf (COTS) software product",
      "clause": "5.1.1"
    }
  ],
  "ambiguities": [
    {"requirement_id": "R-003", "issue": "Undefined term 'fast'", "kind": "ambiguity | contradiction | missing_criteria"}
  ],
  "predicted_gaps": [
    {"area": "error recovery on payment timeout", "why": "no requirement covers the failure path"}
  ]
}
```

`type` and `is_ai_feature` drive downstream behavior: AI features get rubrics +
adversarial probes instead of exact-match assertions. `conformance_criterion`
is used in **Standards Conformance mode** (one `codebase` target per requirement,
matched against a target repo). For conformance requirements, `standard_id` and
`clause` MUST be populated; `verify.py` enforces this. See also
`standards_index.json` at the run root (Layer 1, Standards Conformance mode).

### `standards_index.json` (Standards Conformance mode, run root)

```json
{
  "standard_id": "GB/T 25000.51-2016",
  "standard_name": "Software product quality — Part 51",
  "edition": "2016",
  "publisher": "SAC (中国国家标准化管理委员会)",
  "source_path": "standards/gbt_25000_51_2016.pdf",
  "clause_count": 87,
  "normative_sentence_count": 213,
  "generated_at": "ISO-8601"
}
```

---

## 02_testcases.json — Test Cases + Rubrics (Layer 2)

```json
{
  "run_for": "path/to/01_requirements.json",
  "cases": [
    {
      "id": "TC-001",
      "requirement_ids": ["R-001"],
      "title": "Short imperative title",
      "category": "positive | negative | boundary | error_recovery | adversarial",
      "preconditions": ["state required before the test"],
      "steps": ["ordered action steps"],
      "target": {
        "kind": "http | cli | python | manual | codebase",
        "request": {"method": "POST", "url": "...", "headers": {}, "body": {}},
        "command": "echo example",
        "module": "pkg.mod", "callable": "func", "args": [], "kwargs": {},

        // Standards Conformance mode (repo is also passed via --repo / $SDQ_REPO)
        "repo": "/abs/path/to/repo",
        "pattern": "**/*.py",
        "regex": "TODO|FIXME",
        "file_match": "**/auth/**"
      },
      "expected": {
        "mode": "exact | predicate | rubric",
        "exact": {"status": 200, "json_path": "$.ok", "equals": true},
        "predicate": "python expression over `result`, e.g. result['latency_ms'] < 500",
        "rubric_id": "RUB-001"
      }
    }
  ],
  "rubrics": [
    {
      "id": "RUB-001",
      "for_requirement": "R-007",
      "intent": "What a valid response must accomplish.",
      "semantic_accuracy": "Must correctly answer the user's billing question.",
      "required_claims": ["states the refund window is 30 days"],
      "prohibited_content": ["promises outside policy", "PII of other users"],
      "format_constraints": ["valid JSON", "<= 120 words"],
      "tone": "professional, non-judgmental",
      "pass_threshold": 0.8
    }
  ]
}
```

Rubrics are the heart of non-deterministic evaluation. A case whose `expected.mode`
is `rubric` is scored by `judge.py`, not by string comparison.

### `target.kind == "codebase"` (Standards Conformance mode)

Static check against a target repo. The repo path is supplied per-run via
`run_suite.py --repo <path>` (falls back to env var `SDQ_REPO`); the per-case
`target.repo` field overrides it.

Fields:

- `pattern` (required): a glob (e.g. `**/*.py`, `**/auth/**`, `*.md`) — files matched
  by `pathlib.Path.rglob` are scanned.
- `regex` (optional): a Python regex applied to each matched file's text; only
  files with at least one match contribute to `matches[]`.
- `file_match` (optional): a glob; if set, only files whose **path** (relative to
  repo root) matches the glob contribute to `matches[]`. Useful when you want
  the regex to apply only to a sub-tree.

Result shape (consumed by `expected.predicate` exactly like other targets):

```json
{
  "repo": "/abs/path/to/repo",
  "files": ["/abs/path/.../a.py", "/abs/path/.../b.py"],
  "count": 2,
  "matches": [
    {"file": "/abs/path/.../a.py", "line": 14, "text": "TODO: refactor"},
    {"file": "/abs/path/.../b.py", "line":  3, "text": "FIXME: race"}
  ],
  "scanned_files": 47,
  "scanned_bytes": 184320,
  "errors": []
}
```

Common predicate idioms:

- Existence (positive): `result['count'] >= 1`  (clause: "shall provide X")
- Absence (negative): `result['count'] == 0`    (clause: "shall not contain X")
- Match-a-line:     `any('api_key' in m['text'].lower() for m in result['matches'])`
- File path only:   `any('auth' in m['file'] for m in result['matches'])`

Files larger than 5 MiB or matching `*.{png,jpg,jpeg,gif,pdf,zip,tar,bin,exe,so,dll}`
are skipped to keep scans fast and avoid decoding binary garbage. Directories
matching `.git`, `node_modules`, `__pycache__`, `venv`, `.venv`, `dist`, `build`
are skipped.

---

## 03_results.json — Execution Results (Layer 3)

```json
{
  "run_for": "path/to/02_testcases.json",
  "executed_at": "ISO-8601",
  "results": [
    {
      "case_id": "TC-001",
      "status": "pass | fail | error | skipped | needs_eval",
      "samples": [
        {"raw": "captured output / response body", "latency_ms": 142, "meta": {}}
      ],
      "assertion_detail": "why it passed/failed for exact|predicate modes",
      "self_heal": {"attempted": false, "note": ""}
    }
  ]
}
```

`needs_eval` means the case is rubric-scored and is handed to Layer 5.
For AI features, run N samples (default 3) so consistency can be measured.

---

## 05_evaluations.json — Judge + Adversarial Verdicts (Layer 5)

```json
{
  "evaluations": [
    {
      "case_id": "TC-007",
      "rubric_id": "RUB-001",
      "samples": [
        {
          "score": 0.86,
          "verdict": "pass | fail",
          "breakdown": {"semantic_accuracy": 0.9, "required_claims": 1.0,
                         "prohibited_content": 1.0, "format": 1.0, "tone": 0.7},
          "rationale": "one or two sentences, judge's reasoning",
          "hallucinations": [], "safety_flags": []
        }
      ],
      "consistency": {"pass_rate": 0.67, "score_stddev": 0.11}
    }
  ],
  "agent_traces": [
    {
      "case_id": "TC-012",
      "goal_completed": true,
      "failing_step": null,
      "unsafe_tool_calls": [],
      "deviations": [{"step": 3, "note": "called search twice unnecessarily"}]
    }
  ],
  "adversarial": [
    {"case_id": "ADV-003", "owasp": "LLM01 Prompt Injection",
     "outcome": "defended | breached | partial", "evidence": "..."}
  ]
}
```

---

## defects.json — Defect Log (Layer 6)

```json
{
  "defects": [
    {
      "id": "DEF-001",
      "title": "Refund window stated as 14 days, policy is 30",
      "severity": "critical | high | medium | low",
      "requirement_ids": ["R-007"],
      "case_id": "TC-007",
      "kind": "functional | hallucination | safety | compliance | consistency | performance",
      "reproduction": ["exact steps / request to reproduce"],
      "evidence": "observed output excerpt"
    }
  ]
}
```

---

## readiness.json — Release Readiness Score (Layer 6)

```json
{
  "score": 78.4,
  "recommendation": "ship | ship_with_caveats | hold",
  "components": {
    "coverage":   {"weight": 0.30, "value": 0.92, "detail": "46/50 requirements have >=1 executed case"},
    "defects":    {"weight": 0.30, "value": 0.71, "detail": "0 critical, 2 high, 5 medium"},
    "stability":  {"weight": 0.25, "value": 0.80, "detail": "mean AI pass-rate 0.80 across 3 samples"},
    "compliance": {"weight": 0.15, "value": 0.88, "detail": "22/25 applicable checks passed"}
  },
  "blocking": ["any critical defect blocks ship regardless of score"]
}
```

Thresholds (documented, tunable in `score_release.py`):
`ship` >= 85 and zero critical defects · `ship_with_caveats` 70–85 ·
`hold` < 70 or any critical defect.
