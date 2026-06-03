---
name: spec-driven-qa
description: >
  Use this skill to run an end-to-end spec-driven QA pipeline: turn a PRD into a
  full test suite (classical backbone + AI rubric + adversarial layers on top),
  execute it against a system under test, evaluate non-deterministic LLM/agent
  outputs, run OWASP LLM Top 10 probes and compliance checks, and produce a
  coverage map, defect log, and release-readiness decision. Trigger whenever the
  user mentions: generating test cases from a PRD or spec, "test my agent /
  chatbot / API", QA for an AI or non-deterministic feature, red-teaming an LLM,
  building a release-readiness or coverage report, or any variation of "run full
  testing on this" / "is this ready to ship". Also trigger on a bare
  `/spec-driven-qa`.
trigger_phrases:
  - /spec-driven-qa
  - run spec-driven qa
  - generate test cases from this PRD
  - test my AI product
  - is this ready to ship
  - red team my LLM
  - QA my agent
  - release readiness report
  - build a test suite from this spec
compatibility: Python >= 3.10. Optional extras (auto-installable): pypdf / python-docx for PRD ingestion; playwright + chromium for the visual report render; a judge API key (ANTHROPIC_API_KEY / MINIMAX_API_KEY / OPENAI_API_KEY) for headless evaluation. Without an API key Claude scores inline for free.
---

# Spec-Driven QA — End-to-End Quality Pipeline

A spec-driven QA pipeline that runs the full quality lifecycle:
**requirement → test → execute → integrate → evaluate → report → verify**.

The bulk of the pipeline is *classical software QA* — requirement graphs,
equivalence partitioning, boundary value analysis, decision tables, state
transition, pairwise — driven mechanically from a PRD. AI-specific layers
(rubric scoring, OWASP LLM Top 10 probes, consistency, agent-trace evaluation)
sit *on top* of the classical backbone, so they only apply where they're
appropriate and never float free.

The work splits two ways, and getting this split right is the whole game:

- **Claude (you) does the judgment.** Reading the PRD, authoring the requirement
  graph, writing test cases and rubrics, scoring outputs as the LLM-as-judge,
  triaging defects. This is irreducibly semantic work.
- **Scripts do the deterministic work.** Parsing files, validating structure,
  executing the suite, computing consistency/coverage/scores, rendering reports.
  Never re-implement these by hand; they exist so results are repeatable.

All scripts live in `scripts/`, take a **run directory** as their workspace, and
read/write JSON whose schemas are in `references/schemas.md`. Read that file
before authoring any artifact.

## Non-negotiable principles

These three rules are not optional. Breaking any one of them produces a report
that looks finished but isn't — which is worse than no report.

1. **Classical first; AI tests must rest on classical tests.** Never invent test
   cases free-form. Generate a classical backbone automatically — equivalence
   partitioning, boundary value analysis, decision tables, state transition (see
   Layer 2A) — for *every* requirement, including AI ones. Only then layer AI
   rubric and adversarial tests on top, and only for requirements that already
   have classical coverage. An LLM left to "write tests" will produce
   plausible-looking cases that miss the boundaries and condition combinations
   that actually break things. The classical backbone is what makes coverage
   *meaningful* rather than decorative, and it grows coverage automatically (one
   requirement becomes a dozen boundary and decision-table cases).

2. **Verify before you finish — with your own eyes.** A script exiting 0 is not
   success. Before presenting anything to the user you MUST run Layer 7, then
   open the rendered report and visually inspect its formatting: tables aligned,
   badges visible, no leaked HTML/markdown artifacts, every section populated, the
   readiness call consistent with the data. If you skipped the visual check, you
   are not done.

3. **Surface hidden limitations.** A green report hides what wasn't tested. You
   MUST author `limitations.md` every run: what was out of scope, what assumptions
   you made, what the classical/AI/adversarial layers could NOT exercise, and what
   could still fail in production despite a passing score. Honesty about the gaps
   is the deliverable — coverage theater is the failure mode to avoid.

---

## Setup

```bash
cd <skill-dir>           # the directory containing this SKILL.md
RUN=runs/$(date +%Y%m%d-%H%M%S)   # one run dir per engagement
mkdir -p "$RUN"
pip install pypdf python-docx --break-system-packages 2>/dev/null || true
```

Two ways in:
- **Spec mode** (self-serve, default): generate + execute + report, Claude scores
  inline.
- **Run mode** (expert review): same pipeline, but you pause after each layer,
  surface findings to the user, and apply human sign-off before the report.
  Use this when the user says stakes are high (fintech, healthcare, regulated).

---

## Layer 1 — UNDERSTAND (Requirements → Testable Structure)

Goal: a validated requirement graph with ambiguities and predicted gaps flagged
*before* any test is generated.

1. Ingest the PRD (DOCX/PDF/MD/HTML/Confluence/Notion export):
   ```bash
   python scripts/ingest_prd.py <prd-path> --out "$RUN"
   ```
   This writes `_prd_text.txt` (full text) and `_prd_candidates.json` (heuristic
   requirement sentences). If a PRD is a scanned image, OCR it first (pdf skill).

2. **Read `_prd_text.txt` yourself** and author `$RUN/01_requirements.json`
   following the schema. For each requirement set `type`, `acceptance_criteria`,
   `depends_on`, `is_ai_feature`, and `risk`. Capture flowcharts/state-machines/UI
   described in the PRD as requirements too (multimodal understanding). List every
   ambiguity, contradiction, and missing acceptance criterion in `ambiguities`,
   and predict coverage gaps against common failure patterns in `predicted_gaps`.

3. Validate and enrich:
   ```bash
   python scripts/graph_tools.py "$RUN/01_requirements.json"
   ```
   This checks IDs/dependencies/cycles and adds heuristic ambiguity flags. Fix any
   structural error it reports before moving on. Surface the ambiguities to the
   user — a contradiction caught here is worth a hundred tests downstream.

---

## Layer 2 — GENERATE (Requirements → Test Cases)

Goal: a classical backbone covering positive/negative/boundary/error-recovery
paths, with AI rubric tests layered on top. **Do these in order — 2A before 2B.**

### Layer 2A — Classical backbone (automatic, mandatory)

This is generated mechanically so coverage is meaningful, not invented. Read
`references/classical_techniques.md` first.

1. Get a starting scaffold so the suite file exists:
   ```bash
   python scripts/generate_test_cases.py scaffold "$RUN/01_requirements.json" --out "$RUN/02_testcases.json"
   ```
2. Author a **test model** — emit a skeleton, then fill in the input variables,
   their equivalence partitions, boundaries, and decision rules for each
   requirement (this is the judgment step; the partitions/boundaries come from the
   acceptance criteria):
   ```bash
   python scripts/classical_tests.py model "$RUN/01_requirements.json" --out "$RUN/_test_model.json"
   # ... fill in every TODO in _test_model.json ...
   ```
3. Expand the model into concrete classical cases and merge them into the suite:
   ```bash
   python scripts/classical_tests.py expand "$RUN/_test_model.json" --into "$RUN/02_testcases.json"
   ```
   This auto-generates equivalence (one rep per class), boundary (b-1/b/b+1 +
   min/max + just-outside), decision-table (one per rule), state-transition, and —
   for any requirement with ≥2 input variables — **pairwise/combinatorial** cases
   that exercise variable interactions. Every requirement now has a real,
   technique-grounded backbone. This is where coverage grows: do not hand-write
   what the expander generates.

### Layer 2B — AI rubric + error-recovery on top

4. Now fill in the remaining scaffolded cases and add what classical expansion
   can't: rubric cases for AI features and explicit error-recovery paths.
   - For deterministic gaps: `expected.mode = exact` or `predicate`.
   - For AI features: `expected.mode = rubric`, and **reuse the same input
     partitions/boundaries from the test model** so the AI is judged on meaningful
     inputs, not arbitrary ones. Write the rubric properly — read
     `references/rubric_guide.md`. Only add a rubric case for a requirement that
     already has classical (2A) coverage.
   - Add error-recovery cases for every failure path the PRD implies.

5. Validate and read the coverage line:
   ```bash
   python scripts/generate_test_cases.py validate "$RUN/02_testcases.json" --graph "$RUN/01_requirements.json"
   ```
   If any requirement is uncovered, add cases until coverage is intentional —
   coverage is measured against the requirement graph, not test count.

   `02_testcases.json` is the deliverable test suite. Convert to
   Markdown/Excel/TestRail/Jira from this file if the user wants those formats.

---

## Layer 3 — EXECUTE (Cases → Results)

Goal: run the suite natively, no export/import loop.

```bash
python scripts/run_suite.py "$RUN/02_testcases.json" --out "$RUN/03_results.json" --samples 3
```

- Deterministic cases get a pass/fail/error via exact or predicate checks.
- AI/rubric cases run **N samples** (default 3) and are marked `needs_eval` for
  Layer 5 — that's how consistency gets measured.
- `manual` targets are marked `skipped` with a note (report them honestly as
  untested rather than faking a result).
- Transient failures trigger one retry; self-heal notes are logged, never silent.
  True self-healing = re-deriving intent when a UI/selector changed, not patching
  selectors. When that's needed, re-derive the step from the requirement and note it.

For **agent** products, capture the full decision trace (each tool call, reasoning
step, state transition) and write `agent_traces` entries in `05_evaluations.json`
per `references/rubric_guide.md`. The trace is the test, not just the final answer.

---

## Layer 4 — INTEGRATE (Platform → Workflow)

Wire the run into the user's workflow when they want it:

- **CI/CD gate:** copy `assets/ci/github-actions.yml` into their repo. It runs the
  suite on every PR and blocks merge below a readiness threshold. Adapt for GitLab
  CI / Jenkins / CircleCI by porting the same five script calls.
- **Test management sync:** map `02_testcases.json` cases to Jira/Linear/TestRail
  issues; map `defects.json` to tickets with the reproduction path attached.
- **Delivery:** post the readiness line + report link to Slack/Lark/DingTalk.
- **API/webhook:** every artifact is JSON, so any external system can consume it.

If a connector (Jira, Slack, etc.) would help and isn't loaded, search for it
rather than asking the user to copy-paste.

---

## Layer 5 — EVALUATE (AI Outputs → Quality Signal)

Goal: turn AI outputs into a quality signal — the part conventional tools can't do.

**Non-deterministic evaluation (LLM-as-judge).** Two ways:

- *Inline (default, free, calibrated):* you are the judge.
  ```bash
  python scripts/judge.py emit "$RUN"        # writes _judge_tasks.json
  ```
  Read each task, score the output against its rubric on the five dimensions
  (`references/rubric_guide.md`), and write `$RUN/_judge_scores.json`. Then:
  ```bash
  python scripts/judge.py ingest "$RUN"      # -> 05_evaluations.json + consistency
  ```
- *Headless (CI / large batches):*
  ```bash
  python scripts/judge.py run "$RUN" --provider anthropic   # or minimax / openai
  ```

Either way you get `pass_rate` and `score_stddev` per AI case. A feature that
passes 2 of 3 runs is not shippable even with a good average — say so.

**Adversarial / red-team (OWASP LLM Top 10):**
```bash
python scripts/adversarial.py "$RUN" --target target.json --inject-into body.input
```
`target.json` is a single test-case `target` object pointing at the live LLM.
Extend the probe pack per product using `references/owasp_llm_top10.md`.
Adversarial coverage is not optional for any user-facing LLM.

**Bias & consistency:** generate rubric cases that hold the request constant while
varying input profiles (names, locales, genders); a quality system scores them
equivalently. Divergence is a consistency defect.

---

## Layer 6 — REPORT & COMPLY (Evidence → Decisions)

Goal: a decision, not a pile of logs.

1. *(Optional)* Author `$RUN/compliance.json` from `references/compliance.md`
   (GDPR / PIPL / SOC 2 / ISO 25010 checks, PII-leak and access-control results).

2. Consolidate defects and compute readiness:
   ```bash
   python scripts/score_release.py "$RUN"     # -> defects.json + readiness.json
   ```
   Readiness = 0.30·coverage + 0.30·defect-health + 0.25·AI-stability +
   0.15·compliance, scaled to 100. **Any critical defect forces a `hold`.**

3. Render the report:
   ```bash
   python scripts/make_report.py "$RUN"       # -> report.html + report.md
   ```
   Coverage is requirement-mapped, every defect carries a reproduction path, and
   the readiness scorecard shows the ship / ship-with-caveats / hold call.

---

## Layer 7 — VERIFY (mandatory — never skip, never present without it)

A script exiting 0 is not done. Before you show the user anything, verify both
the substance and the formatting.

1. Author `$RUN/limitations.md` — the hidden-limitations artifact (principle 3).
   Enumerate honestly: what was out of scope, assumptions made, what each layer
   could NOT exercise (e.g. manual targets never executed, adversarial pack is a
   7-probe screen not a full pentest, judge calibrated against human samples or
   not at all), and what could still fail in production despite the score.

2. Run the verifier:
   ```bash
   python scripts/verify.py "$RUN"
   ```
   It lints for failures that pass silently — leaked HTML entities in the report,
   unfilled TODOs, uncovered requirements, AI cases with no classical backbone,
   missing limitations, readiness/data mismatch — and tries to rasterize
   `report.html` to `report.png`. Fix every FAIL and re-run until clean. Add
   `--strict` to make a failed render itself a blocking FAIL — use it in CI or
   any pipeline where a report must not be emitted without a successful visual
   render.

3. **Do the visual check with your own eyes.** Open `report.png` (or
   `report.html` if no renderer was available) using `view`, and confirm: tables
   aligned and non-empty, severity badges render, no raw `&quot;` / `<td></td>` /
   stray `{ }` artifacts, every section populated, and the readiness call matches
   the numbers. If anything looks off, fix the data or `make_report.py`,
   regenerate, and look again. Do not present a report you have not looked at.

4. Only now present `report.html` to the user (use `present_files` if available),
   and state the key hidden limitations alongside the readiness call.

---

## What this skill does NOT promise

Say this plainly in every engagement: this skill does **not** promise zero
post-launch defects — no system can. It promises complete coverage of the
**agreed scope**, honest reporting when something is untestable within that scope,
and findings specific enough to act on. If a layer can't be run (e.g. no live
system for Layer 3, no API key and you can't judge inline), report it as untested
rather than papering over it. That honesty is the product.

---

## One-shot run (Spec mode, quick reference)

```bash
RUN=runs/$(date +%Y%m%d-%H%M%S); mkdir -p "$RUN"
python scripts/ingest_prd.py PRD.pdf --out "$RUN"
# author 01_requirements.json ...
python scripts/graph_tools.py "$RUN/01_requirements.json"
python scripts/generate_test_cases.py scaffold "$RUN/01_requirements.json" --out "$RUN/02_testcases.json"
# --- 2A classical backbone (automatic) ---
python scripts/classical_tests.py model "$RUN/01_requirements.json" --out "$RUN/_test_model.json"
# fill in _test_model.json (variables/partitions/boundaries/rules) ...
python scripts/classical_tests.py expand "$RUN/_test_model.json" --into "$RUN/02_testcases.json"
# --- 2B layer AI rubric + error-recovery cases on top ---
python scripts/generate_test_cases.py validate "$RUN/02_testcases.json" --graph "$RUN/01_requirements.json"
python scripts/run_suite.py "$RUN/02_testcases.json" --out "$RUN/03_results.json" --samples 3
python scripts/judge.py emit "$RUN"        # score -> _judge_scores.json
python scripts/judge.py ingest "$RUN"
python scripts/adversarial.py "$RUN" --target "$RUN/target.json" --inject-into body.input
python scripts/score_release.py "$RUN"
python scripts/make_report.py "$RUN"
# author limitations.md, then VERIFY before presenting:
python scripts/verify.py "$RUN"            # then `view "$RUN/report.png"` and eyeball it
```

## File map

```
spec-driven-qa/
├── SKILL.md                 this file — the workflow spine
├── scripts/
│   ├── _common.py           shared IO / severity weights
│   ├── ingest_prd.py        L1: PRD -> text + candidate requirements
│   ├── graph_tools.py       L1: validate + enrich requirement graph
│   ├── generate_test_cases.py L2: scaffold + validate suite
│   ├── classical_tests.py    L2A: auto EP/BVA/decision-table/state-transition backbone
│   ├── run_suite.py         L3: execute http/cli/python/manual targets
│   ├── judge.py             L5: LLM-as-judge (inline or API) + consistency
│   ├── adversarial.py       L5: OWASP LLM Top 10 probe runner
│   ├── score_release.py     L6: defect consolidation + readiness score
│   ├── make_report.py       L6: report.html + report.md (+ hidden limitations)
│   └── verify.py            L7: quality/format lint + report rasterization (--strict gate)
├── references/
│   ├── schemas.md           every JSON artifact's shape — read first
│   ├── classical_techniques.md  the test model + EP/BVA/DT/ST expansion
│   ├── rubric_guide.md      writing non-deterministic rubrics + agent traces
│   ├── owasp_llm_top10.md   adversarial probe reference
│   └── compliance.md        GDPR/PIPL/SOC2/ISO25010 + PII detectors
└── assets/ci/github-actions.yml  L4: CI/CD quality gate
```
