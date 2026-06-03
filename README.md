# Spec-Driven QA — End-to-End Quality Pipeline (Claude Code Skill)

A spec-driven QA pipeline as a Claude Code skill. It turns a product spec (PRD)
into a full, executed test suite and a release-readiness decision.

The pipeline is mostly *classical software QA* — requirement graphs, equivalence
partitioning, boundary value analysis, decision tables, state transition,
pairwise — driven mechanically from the spec. AI-specific layers (rubric
scoring, OWASP LLM Top 10 probes, consistency, agent-trace evaluation) layer on
top so they only apply where they're appropriate and never float free. Built so
that AI features (where the same input yields varied valid outputs) get
evaluated honestly rather than with brittle exact-match assertions.

This is a **Claude Code skill**: a workflow (`SKILL.md`) plus runnable Python
scripts. Claude does the judgment (reading the PRD, writing the requirement
graph, authoring rubrics, scoring AI outputs); the scripts do the deterministic,
repeatable work (parsing, generating the classical test backbone, executing,
scoring, reporting, verifying).

---

## Install

Drop the skill folder into your Claude Code skills directory so it lives at
`~/.claude/skills/spec-driven-qa/` (or your project's `.claude/skills/`). It's
plain Markdown + Python — no build step.

```bash
git clone https://github.com/stancsz/spec-driven-qa-skill.git
mkdir -p ~/.claude/skills
cp -r spec-driven-qa-skill ~/.claude/skills/spec-driven-qa
```

Then just talk to Claude Code:

```
/spec-driven-qa
test my refund chatbot against this PRD
is this feature ready to ship?
```

Claude reads `SKILL.md` and drives the pipeline. You don't run the scripts by
hand unless you want to — but you can; everything below is exactly what Claude
runs.

**Requirements:** Python ≥ 3.10. Optional extras Claude installs as needed:
`pypdf`/`python-docx` (PRD ingestion), a headless renderer for the visual check
(`pip install playwright --break-system-packages && playwright install chromium`),
and a judge API key only if you want headless evaluation (otherwise Claude scores
inline for free).

---

## Quickstart (the full run)

Everything happens inside one **run directory**. Each step reads the previous
step's JSON and writes its own (schemas in `references/schemas.md`).

```bash
cd ~/.claude/skills/spec-driven-qa
RUN=runs/$(date +%Y%m%d-%H%M%S); mkdir -p "$RUN"

# 1. UNDERSTAND — ingest the PRD, then Claude authors the requirement graph
python scripts/ingest_prd.py PRD.pdf --out "$RUN"
#    -> Claude writes $RUN/01_requirements.json
python scripts/graph_tools.py "$RUN/01_requirements.json"      # validate + flag ambiguities

# 2A. GENERATE (classical backbone, automatic)
python scripts/generate_test_cases.py scaffold "$RUN/01_requirements.json" --out "$RUN/02_testcases.json"
python scripts/classical_tests.py model "$RUN/01_requirements.json" --out "$RUN/_test_model.json"
#    -> Claude fills in variables / partitions / boundaries / rules
python scripts/classical_tests.py expand "$RUN/_test_model.json" --into "$RUN/02_testcases.json"

# 2B. GENERATE (AI rubric + error-recovery cases on top)
#    -> Claude adds rubric cases for AI features, then:
python scripts/generate_test_cases.py validate "$RUN/02_testcases.json" --graph "$RUN/01_requirements.json"

# 3. EXECUTE
python scripts/run_suite.py "$RUN/02_testcases.json" --out "$RUN/03_results.json" --samples 3

# 5. EVALUATE (AI outputs)
python scripts/judge.py emit "$RUN"        # Claude scores -> $RUN/_judge_scores.json
python scripts/judge.py ingest "$RUN"
python scripts/adversarial.py "$RUN" --target "$RUN/target.json" --inject-into body.input

# 6. REPORT & COMPLY
python scripts/score_release.py "$RUN"     # defects.json + readiness.json
python scripts/make_report.py "$RUN"       # report.html + report.md

# 7. VERIFY (mandatory)
#    -> Claude authors $RUN/limitations.md first, then:
python scripts/verify.py "$RUN" --strict   # lints + renders report.png; --strict requires a render
#    -> Claude opens report.png and visually confirms formatting before showing you
```

(Layer 4, INTEGRATE, is optional: see `assets/ci/github-actions.yml` for a CI gate.)

---

## What you get

| Artifact | What it is |
|---|---|
| `01_requirements.json` | Requirement graph with dependencies, AI flags, ambiguities, predicted gaps |
| `02_testcases.json` | The test suite — classical backbone + AI rubrics + adversarial |
| `03_results.json` | Execution results (pass/fail/error/needs_eval/skipped) |
| `05_evaluations.json` | AI judge verdicts + consistency, adversarial outcomes, agent traces |
| `defects.json` | Defect log, each with severity and a reproduction path |
| `readiness.json` | Release-readiness score + ship / ship-with-caveats / hold call |
| `report.html` / `report.md` | The human-readable report (coverage map, defects, limitations) |
| `report.png` | Rasterized report for the mandatory visual check |
| `limitations.md` | Hidden limitations — what was NOT tested and what could still fail |

---

## The ideas that make it work

**Classical tests first; AI tests sit on top.** An LLM asked to "write tests"
produces plausible cases that miss the edges that actually break software. So
this skill generates a classical backbone automatically — equivalence
partitioning, boundary value analysis, decision tables, state transition, and
pairwise for multi-variable requirements — then layers AI rubric and
adversarial tests on top. You author a small **test model** (the input
variables and their partitions); the expander turns it into many concrete
cases. `verify.py` refuses to pass if an AI feature has rubric tests but no
classical coverage.

**Non-deterministic evaluation.** AI features are scored against **rubrics**
(required claims, prohibited content, format, tone) by an LLM judge, across N
samples, so you get a pass-rate and a consistency number — not a brittle string
match. See `references/rubric_guide.md`.

**Verify before finishing — visually.** A script exiting 0 isn't success. Layer 7
lints the artifacts and renders the report to an image so formatting is checked by
eye, not assumed. Add `--strict` to make a failed render a hard stop.

**Honest limitations.** Every run produces `limitations.md` and the report ends
with a Hidden Limitations section. The promise is complete coverage of the agreed
scope — never "zero defects."

---

## Useful options

- **Combinatorial coverage:** for a requirement with ≥2 input variables, the
  expander runs pairwise (all-pairs) automatically. Override per model with
  `"combinatorial": "pairwise" | "all" | "none"`. See `references/classical_techniques.md`.
- **Strict visual gate:** `python scripts/verify.py "$RUN" --strict` fails the run
  unless the report rasterizes — use it in CI.
- **Judge backends:** inline (Claude, default, free) via `judge.py emit`/`ingest`,
  or headless via `judge.py run "$RUN" --provider anthropic|minimax|openai` (reads
  the matching `*_API_KEY` from the environment).
- **Targets:** test cases run against `http`, `cli`, `python`, or `manual` targets.
  `manual` cases are reported as untested, never faked.

---

## Troubleshooting

- *"No text extracted" on ingest* — the PDF is scanned; OCR it first.
- *Verify FAILs "AI tests grounded in classical tests"* — add the AI feature's
  requirement to your `_test_model.json` and re-expand; the rubric must sit on a
  classical backbone.
- *Verify WARNs "report rasterized" (or FAILs under `--strict`)* — install a
  headless renderer (Playwright + Chromium), or inspect `report.html` directly.
- *Predicate cases all "error"* — your predicate references something unavailable;
  predicates run with a small safe builtin set (`str`, `len`, `int`, `any`, …).

---

## Layout

```
spec-driven-qa/
├── SKILL.md                       the workflow Claude follows
├── README.md                      this file
├── scripts/                       the pipeline (run by Claude or by hand)
├── references/                    schemas, classical techniques, rubrics, OWASP, compliance
└── assets/ci/github-actions.yml   optional CI quality gate
```

Full per-script and per-layer detail lives in `SKILL.md`.

## License

MIT.
