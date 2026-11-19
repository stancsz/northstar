# `spot-advisor` Roadmap

> **To get 100 tokens of frontier judgment at a hard coding fork today, you either pay for 100,000+ tokens of frontier context churn—or watch a fast, cheap model spin in circles.**
>
> **`spot-advisor` decouples execution from judgment: your fast agent absorbs 100% of the file reads, edits, and tool loops, and buys only a tiny packet in and a tiny verdict out when intelligence actually counts.**

---

## 1. The Core Problem (Bolded Top of `README.md`)

Coding agents couple expensive intelligence to cheap context churn:

- **Continuous frontier loops waste ~90% of tokens on grunt work.** Every turn re-sends growing chat history, file reads, and test output. A normal 20-turn fix easily burns 200k+ frontier input tokens—draining API budgets and subscription rate limits mostly on `grep`, edits, and retries.
- **Fast, cheap, or local executors stall on the hard ~10%.** Small/fast models fly through routine reads, diffs, and test runs, then get trapped in trial-and-error loops at the 1–3 real decision forks (subtle concurrency bugs, wrong root causes, architecture tradeoffs).
- **Native frontier subagents don't fix it.** Spawning a frontier subagent either dumps the bloated conversation history into it or starts a fresh multi-turn tool loop—still burning tens of thousands of frontier tokens just to settle one decision.

---

## 2. Research Positioning & Tiny-Agent Design Insights

Empirical findings from 2025–2026 confirm that **asymmetric fast execution + sparse frontier advice** is one of the highest-leverage approaches for making small models perform near-frontier software engineering without fine-tuning—while exposing specific pitfalls around **context rot**, **thinking-token truncation**, and **small-model self-escalation**:

| Reference | Key Finding | Design Implication for `spot-advisor` |
| :--- | :--- | :--- |
| **Anthropic Advisor Strategy (`advisor_20260301`, Apr 2026)** | Haiku + Opus Advisor **more than doubled** Haiku solo on BrowseComp (`19.7% → 41.2%`); Sonnet + Opus beat Sonnet solo (`+2.7pp`) on SWE-bench Multilingual while cutting cost `11.9%` vs. Opus solo. Typical advisor calls emit **`400–700` visible text tokens (`1,400–1,800` total with thinking)**. | **Validates the pattern—and reveals our wedge:** Native server-side advisors feed the **full raw transcript** to the frontier model (keeping input costs high) and are Claude-only. `spot-advisor` stays **cross-provider** and compresses input to `~400–1,500` tokens. |
| **Stanford Hazy Research `Minions` / `MinionS` ([arXiv:2502.15964](https://arxiv.org/abs/2502.15964))** | Keeping large context on a local SLM (`1B–32B`) and exchanging compact messages with a cloud frontier model cut cloud tokens `5.7×` at **`97.9%`** of frontier quality once instructions were structured and atomic (vs. `87%` with naive prose chat). | **Structure beats chat:** Tiny executors fail on vague prose hints, but reach near-frontier reliability when given concrete, atomic, verifiable actions. |
| **SLMs in Agentic AI ([arXiv:2506.02153](https://arxiv.org/abs/2506.02153)), RouteLLM ([arXiv:2406.18665](https://arxiv.org/abs/2406.18665)), FrugalGPT ([arXiv:2305.05176](https://arxiv.org/abs/2305.05176))** | Routing and cascading cut inference cost substantially when hard queries are separated from routine ones. | Standard coarse query-level routers decide *before* execution; `spot-advisor` escalates **mid-trajectory** only at verified bottlenecks. |
| **Context Rot & SLM Metacognition Studies** | Input quality degrades on bloated, noisy histories (**context rot**); tiny models also suffer from **(1) overconfidence** (failing to escalate when stuck) and **(2) lossy prose summarization** (dropping the exact code line or stack frame holding the root cause). | Keep packets small and surgical, never rely solely on SLM prose summaries, and trigger escalation deterministically from host rules. |
| **SWE-bench ([arXiv:2310.06770](https://arxiv.org/abs/2310.06770)) & SWE-agent ([arXiv:2405.15793](https://arxiv.org/abs/2405.15793))** | Agent-computer interfaces and deterministic test feedback strongly govern end-to-end resolution rates. | Anchor every advisor turn with exact ground truth and a falsifiable `Verify:` check. |

### The 3 Required Upgrades for Tiny (7B–27B / Haiku-Class) Executors
1. **Deterministic Evidence Extraction (fixes lossy summaries):** Let the CLI attach bounded, machine-extracted ground truth (`--snippet path:start-end`, `--diff`, `--error-tail`) instead of trusting a small executor's paraphrase alone.
2. **Deterministic Escalation Triggers + Optional Pre-Flight Spot Plan (fixes overconfidence):** Trigger `spot-advisor` via concrete host rules/hooks (e.g., after 2 consecutive test failures, repeated edits to the same file, or once upfront on multi-file tasks) rather than hoping a small model recognizes it is looping.
3. **Atomic `Verdict / Do / Verify / Risk` Output (fixes instruction drift):** Give the fast executor exact symbol/file changes plus an explicit command to prove or falsify the fix.

---

## 3. Calibrated Small I/O & Reasoning-Effort Protocol

Hard lessons from frontier reasoning models (e.g., `gpt-6.2-astra`, `claude-5-fable` / Opus-tier adaptive reasoners) shape our protocol design:

### Input Contract (Target: `400–1,500` tokens Round 1; `150–400` tokens Round 2+)
- **Structured 4-slot packet:** Accept CLI flags (`--blocker`, `--facts`, `--tried`, `--question`) or labeled sections in `--input-file`, plus bounded deterministic evidence flags (`--snippet`, `--diff`, `--error-tail`, reserving up to `~1,200` chars so frontier models see actual code/errors).
- **Zero-cost local preflight linter:** Before any network call, reject empty/vague packets, raw stack-trace dumps, or oversized blocks (Round 1 `<= 4,000` chars; Round 2+ delta `<= 1,000` chars), strip ANSI escapes, and return a 1-line compression hint.
- **Strict text token ceiling & universal counting:** Lower text `MAX_INPUT_TOKENS` from `32,000` to `2,500` (separate visual cap for `--image`). Use a fast local token gate by default instead of requiring `/responses/input_tokens` (which 404s on OpenRouter, LiteLLM, vLLM, and standard OpenAI-compatible gateways).
- **Rolling Session Ledger (`--session-file`):** Replace single-line `last_verdict` with a compact `<= 400`-char ledger (`R1: <verdict> -> <1-line outcome>`) so Round 2–3 inputs stay tiny without repeating failed ideas.

### Visible Output vs. Thinking Budget Contract
- **Zero-redundancy 4-line schema** (replacing overlapping `Next` + `Prompt`):
  - `Verdict:` 1 decisive sentence (the call + *why*)
  - `Do:` ≤ 3 concrete, ordered actions (files/symbols/changes)
  - `Verify:` 1 exact command or assertion proving the fix worked (or falsifying it)
  - `Risk:` 1 material stop condition / edge case (`none` if clear)
- **Target visible length (`150–400` words / `~200–550` visible tokens):** Concise enough to forbid code dumps, detailed enough that a tiny `7B–27B` executor receives unambiguous edits and test checks.
- **Default `--effort medium` (Pareto sweet spot, NOT `low`):** On the 1–2 hardest decision forks per task, `--effort medium` captures ~85–95% of peak frontier reasoning at modest thinking cost (typically `~1,400–1,800` total tokens), minimizing expected cost per solved task ($\mathbb{E}[\text{cost}] = C / p_{\text{success}}$). Expose `--effort low|medium|high` with auto-escalation or opt-in `high` on Round 2+ deadlocks.
- **Safe API `max_output_tokens` headroom:** Because APIs count **both** hidden reasoning tokens and visible tokens toward `max_output_tokens`, hard-capping at `250` causes reasoning models to fail mid-thought (`finish_reason: length`). Scale safe API ceilings by effort (`2,048` for `low`, `4,096` for `medium`, `8,192` for `high`) and enforce *visible* conciseness via prompt, parser validation, and telemetry (`schema_ok`, `visible_budget_ok`, `truncated`).

---

## 4. Pre-Registered Research Questions & Empirical Proof

All empirical evaluation follows our pre-registered [Research Protocol](docs/research-protocol.md) and immutable logging contract in [`eval/`](eval/README.md):

- **RQ1 (Capability Lift):** How much does sparse compressed frontier advice improve resolution rates (`pass@1`) of tiny local (`7B–27B`) and fast cloud executors vs. solo execution and compute-matched Best-of-N?
- **RQ2 (Cost-Accuracy Pareto Frontier):** Does `spot-advisor` achieve lower expected cost per solved task ($\mathbb{E}[\text{cost}]$) and 50–100× lower frontier input tokens than both frontier-only loops and full-transcript 1-turn advisors?
- **RQ3 (Ablations & Effort × I/O Budget Sweep):** What is the isolated impact of (a) packet compression & linter, (b) deterministic evidence flags (`--snippet`, `--diff`, `--error-tail`) vs. SLM prose only, (c) deterministic escalation triggers + pre-flight plan, (d) `Verdict / Do / Verify / Risk`, and (e) `effort ∈ {low, medium, high}` × visible cap (`120w`, `300w`, uncapped)?
- **RQ4 (Failure Taxonomy):** What fraction of residual failures stem from missed escalation (`E1`), lossy evidence (`E2`), wrong advisor verdict (`E3`), executor patch failure (`E4`), or budget/truncation limits (`E5`)?

---

## 5. Phased Milestones (Phase 0 → Phase 4, arXiv-Eligible)

### Phase 0 — Rebrand, Genericize & Research Scaffold *(Current Milestone)*
- Rename `codex-advisor` → **`spot-advisor`** across GitHub repo, metadata, topics, and docs.
- Lead [`README.md`](README.md) with the bolded 90/10 problem statement and remove unverified marketing claims.
- Make [`docs/install.md`](docs/install.md) host-agnostic and move Codex-specific `config.toml` setup into [`docs/codex-setup.md`](docs/codex-setup.md).
- Commit pre-registered [`docs/research-protocol.md`](docs/research-protocol.md), [`eval/telemetry_schema.json`](eval/telemetry_schema.json), [`paper/`](paper/README.md) LaTeX/BibTeX scaffold, and [`CITATION.cff`](CITATION.cff).
- **Exit criterion:** Anyone landing on the repo understands the problem, protocol, and arXiv research path in under 30 seconds while existing tests remain 100% green.

### Phase 1 — Calibrated Small I/O & Effort Engine
- Migrate skill to `skills/spot-advisor/` (`spot_advisor.py` with backward-compatible `ask_expert.py` shim; `SPOT_ADVISOR_*` env vars with legacy fallbacks).
- Implement 4-slot packet schema, local preflight linter, deterministic evidence extraction (`--snippet`, `--diff`, `--error-tail`), `2,500`-token text cap, and rolling Session Ledger.
- Switch output contract to `Verdict / Do / Verify / Risk`, default `--effort medium` with effort-scaled `max_output_tokens` headroom (`2048`/`4096`/`8192`), and structured JSON validation (`schema_ok`, `visible_budget_ok`, `truncated`).
- Make gateway transport universally OpenAI-compatible (`"system"` role, local token counting default, OpenRouter/OpenAI/Anthropic/Codex/Claude CLI support).
- Ship deterministic escalation-trigger templates (`AGENTS.md` / `CLAUDE.md`) and immutable JSONL telemetry emission matching [`eval/telemetry_schema.json`](eval/telemetry_schema.json).
- Expand offline `pytest` coverage across every linter rule, evidence extractor, effort ceiling, ledger rollup, schema parser, and transport fallback.
- **Exit criterion:** 100% of calls enforce safe thinking headroom and strict visible/input bounds across providers; bloated packets fail locally at zero token cost.

### Phase 2 — arXiv-Grade Evaluation, Effort Sweep & Ablations
- Build `eval/` task runners and frozen instance manifests (stratified **SWE-bench Verified** subset `N >= 50` and/or **Terminal-Bench**, plus `15–25` curated hard-fork diagnostic tasks).
- Run all 5 arms (`A1` Small Solo, `A2` Compute-Matched Best-of-N, `A3` Frontier Solo, `A4` Full-Transcript Advisor, `T1` `spot-advisor`) plus RQ3 ablations and the Effort × I/O Budget Pareto Sweep across at least 2 small/fast executors (local `7B–27B` + fast cloud).
- Compute paired McNemar's tests ($\alpha = 0.05$) and bootstrap 95% CIs (`B = 10,000`), classify failures (`E1–E5`), and script automatic LaTeX table & figure generation from `eval/results/`.
- Publish verified metrics in [`README.md`](README.md) and ship `--summary` local session receipts.
- **Exit criterion:** Auditable, statistically tested results linking every table cell to committed `eval/results/` JSONL logs.

### Phase 3 — Frictionless Adoption
- Package one-command CLI & skill installer (`uvx spot-advisor` / `pipx` + `spot-advisor install --host claude|codex|cursor|agents`).
- Ship optional thin, strictly tool-free MCP server (`spot_advise`) enforcing the exact same linter, evidence flags, effort policy, and token bounds for GUI agents (Cursor, Windsurf, Claude Desktop).
- **Exit criterion:** Any developer installs and runs their first spot consultation in under 60 seconds.

### Phase 4 — arXiv Submission & Reproducibility Release (`cs.SE` / `cs.AI`)
- Populate [`paper/main.tex`](paper/main.tex) directly from `eval/results/` artifacts; write Failure Taxonomy, Limitations, and Threats to Validity.
- Audit zero fabricated or hand-edited metrics, add full author affiliation/email, compile self-contained `pdflatex` + `.bbl` tarball with vector figures.
- Tag a frozen GitHub release matching the preprint, update [`CITATION.cff`](CITATION.cff) and [`README.md`](README.md) with the arXiv ID, secure arXiv endorsement (if required as first-time `cs.SE`/`cs.AI` submitter), and submit.
- **Exit criterion:** Clean compilation of the arXiv source bundle (`pdflatex` + `bibtex` zero unresolved refs) and live preprint linked to the frozen code release.
