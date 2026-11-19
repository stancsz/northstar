# `spot-advisor` Pre-Registered Research Protocol (`cs.SE` / `cs.AI`)

This document pre-registers the hypotheses, experimental arms, benchmarks, ablations, and statistical tests for evaluating `spot-advisor` prior to running Phase 2 experiments.

---

## 1. Working Thesis

**Decoupling cheap local or small-model execution from sparse, compressed, 1-turn frontier judgment shifts the cost–accuracy Pareto frontier for small/low-parameter coding agents beyond both continuous frontier loops and full-transcript advisor tools.**

Specifically:
1. Keeping raw file exploration, edits, and test execution on the small/fast executor eliminates ~90% of routine frontier token churn and prevents **context rot** inside the advisor call.
2. Combining deterministic ground-truth evidence extraction (`--snippet`, `--diff`, `--error-tail`), deterministic escalation triggers, and effort-calibrated atomic verdicts (`Verdict / Do / Verify / Risk`) overcomes the two core failure modes of small executors: **overconfidence** (failing to escalate) and **lossy prose summarization**.

---

## 2. Research Questions

- **RQ1 (Capability Lift):** How much does pairing small/fast executors (both local `7B–27B` open-weight SLMs and fast cloud models) with compressed 1-turn frontier advice improve `pass@1` resolution rate over solo execution and over compute-matched Best-of-N retries?
- **RQ2 (Cost–Accuracy Pareto Efficiency):** Compared against continuous frontier loops (`A3`) and full-transcript 1-turn advisor calls (`A4`), what reductions in expected cost per solved task ($\mathbb{E}[\text{cost}] = C_{\text{attempt}} / p_{\text{success}}$), frontier input tokens, frontier output/reasoning tokens, and wall-clock latency does `spot-advisor` (`T1`) achieve?
- **RQ3 (Component Ablations & Effort × I/O Budget Pareto Sweep):**
  1. **Input Compression & Linter Ablation:** Structured preflight-linted packet (`<= 4,000` chars R1 / `<= 1,000` chars R2+) vs. uncompressed/raw packet.
  2. **Deterministic Evidence Ablation:** Script-extracted `--snippet` / `--diff` / `--error-tail` vs. SLM prose summary only.
  3. **Escalation Policy Ablation:** Deterministic host triggers (2 consecutive test failures / edit-churn loop + optional pre-flight spot plan) vs. pure self-triggered escalation.
  4. **Output Schema Ablation:** Atomic `Verdict / Do / Verify / Risk` vs. unstructured prose guidance.
  5. **Calibrated Effort × Budget Pareto Sweep:** Factorial sweep over `reasoning_effort ∈ {low, medium, high}` × `visible_output_target ∈ {120w, 300w, uncapped}` × `input_mode ∈ {compressed_evidence, prose_only, full_transcript}`, measuring visible output tokens, hidden reasoning tokens, truncation rate (`finish_reason == "length"`), `pass@1`, and expected cost per solved task.
- **RQ4 (Failure Taxonomy):** Across all unresolved tasks in `T1`, what share of failures fall into:
  - `E1`: **Missed Escalation** (executor looped without triggering advisor)
  - `E2`: **Lossy / Missing Evidence** (critical file/line/error omitted from packet)
  - `E3`: **Wrong Advisor Verdict** (advisor misdiagnosed given adequate evidence)
  - `E4`: **Executor Patch Failure** (correct advisor verdict, small executor failed to apply/verify it)
  - `E5`: **Budget / Truncation Exhaustion** (round limit reached or thinking-budget truncation)

---

## 3. Benchmarks

1. **Primary Public Benchmark:** Stratified deterministic subset of **SWE-bench Verified** ($N \ge 50$ instances, stratified across repository and difficulty buckets) and/or **Terminal-Bench**. The exact frozen task ID list and sampling seed MUST be committed in `eval/tasks/` before any Phase 2 run begins.
2. **Diagnostic Hard-Fork Suite:** `15–25` self-contained multi-file repositories with deterministic `pytest` / `vitest` verifiers targeting known small-model bottlenecks: concurrency/race conditions, cache/state invalidation bugs, schema/migration traps, and cross-module root-cause debugging.

---

## 4. Experimental Arms (5 Conditions)

All arms use identical tool sandboxes, wall-clock timeouts, and executor turn budgets per task, with pinned model identifiers and seeds:

| Arm | Executor | Advisor / Control Mechanism | Purpose |
| :--- | :--- | :--- | :--- |
| **`A1` Small Solo** | Fast / small executor (`7B–27B` local SLM or fast cloud) | None | Baseline solo capability & loop failure rate |
| **`A2` Compute-Matched Small Best-of-N** | Same fast / small executor | Best-of-N / extra retries matched to `T1` dollar spend | Separates frontier judgment value from sheer extra compute |
| **`A3` Frontier Solo** | Frontier model (`gpt-6.2-astra` / Opus-tier) | Runs full tool loop end-to-end | Quality ceiling & baseline frontier token burn |
| **`A4` Full-Transcript 1-Turn Advisor** | Same small executor | Same frontier advisor, same trigger rules, receives **full raw conversation transcript** | Isolates value of input compression & context-rot elimination vs. Anthropic-style full-transcript advice |
| **`T1` `spot-advisor`** | Same small executor | Same frontier advisor, compressed packet + deterministic `--snippet`/`--diff`/`--error-tail` + rolling ledger + atomic `Verdict/Do/Verify/Risk` | Proposed protocol |

At least **two** distinct fast executors will be evaluated (one local/open-weight SLM in the `7B–27B` range and one fast cloud executor) paired with frontier advisors across `>= 2` model families where available.

---

## 5. Metrics & Statistical Analysis

- **Primary Effectiveness Metric:** Binary `pass@1` resolution verified exclusively by held-out test harnesses after container exit.
- **Primary Efficiency Metrics:**
  - Expected cost per solved task: $\mathbb{E}[\text{cost}] = \text{mean cost per attempt} / \text{pass@1}$.
  - Token breakdown (`p50`, `p95`, mean) separated into executor input/output/cached tokens and advisor input, visible output, hidden reasoning, and total output tokens.
  - Pinned pricing manifest (`eval/pricing.json`) committed alongside results so API cost comparisons remain fully auditable.
- **Statistical Tests:**
  - Pairwise pass-rate comparisons between `T1` and `A1`/`A2`/`A3`/`A4` using **exact two-sided McNemar's test** ($\alpha = 0.05$) on matched task instances.
  - Non-parametric **bootstrap 95% confidence intervals** ($B = 10,000$ resamples) for resolution rate, token deltas, and cost ratios.

---

## 6. Threats to Validity (Pre-Registered Controls)

- **Benchmark Contamination:** Verify performance deltas across both public SWE-bench instances and novel Phase 2 diagnostic tasks.
- **Model Version & API Drift:** Log exact provider-returned model IDs, timestamps, request IDs, and git commit SHAs in every JSONL telemetry record.
- **Pricing Asymmetry (API vs. Subscription vs. Local Hardware):** Report **raw token counts** (`input`, `visible_output`, `reasoning`, `executor`) first, and treat USD translations as secondary projections parameterized by an explicit, versioned `eval/pricing.json`.
- **Prompt & Trigger Sensitivity:** Freeze all prompts, linter thresholds, and escalation rules prior to running confirmatory Phase 2 benchmarks; treat any post-hoc adjustment as exploratory unless re-run end-to-end.
