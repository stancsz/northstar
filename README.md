# Spot Advisor

> **Frontier models are too expensive—and hit rate limits too fast—to waste on reading files, running tests, and routine edits. Fast, cheap, or local models fly through the grunt work, but get stuck in loops on the 10% of hard decisions that actually require frontier intelligence.**
>
> **To get 100 tokens of frontier judgment at a hard coding fork today, you either pay for 100,000+ tokens of frontier context churn—or watch a fast, cheap model spin in circles.**
>
> **`spot-advisor` decouples execution from judgment: your fast executor owns 100% of tools, file reads, edits, and tests, and calls a frontier advisor only at the sticking point—compact evidence packet in, concise structured verdict out, 1 turn.**

[Roadmap](ROADMAP.md) · [Install & Setup](docs/install.md) · [Research Protocol](docs/research-protocol.md) · [Advisor Skill](skills/advisor/SKILL.md) · [Paper](paper/README.md) · [License](LICENSE)

---

## Why Existing Approaches Waste Tokens

| Approach | Who Owns Tools & File Reads? | What Crosses to the Frontier Model? | Where It Breaks |
| :--- | :--- | :--- | :--- |
| **Continuous Frontier Loop** | Frontier model | Growing raw history + full files + logs every turn | Burns ~90% of frontier tokens on `grep`, routine edits, and test retries. |
| **Fast / Cheap Executor Alone** | Fast / local model (`7B–27B`, Haiku, `gpt-6-luna`) | Nothing | Flies through grunt work, then spins in trial-and-error loops on the hard ~10%. |
| **Native Subagent / Full-Transcript Advisor** | Subagent or executor | Full multi-turn tool loop or entire raw conversation transcript | Still pays tens of thousands of frontier tokens—plus **context rot** from noisy logs. |
| **`spot-advisor`** | **Fast executor (100%)** | **1 compact structured packet + bounded code/error evidence** | **1-turn, tool-free frontier judgment only at verified bottlenecks.** |

---

## How It Works

1. **Fast executor absorbs all local work:** File discovery, reads, edits, builds, and test runs stay on your cheap cloud or local executor (`Qwen`, `Haiku`, `gpt-6-luna`, Ollama/vLLM, etc.).
2. **At a genuine decision fork, send a compact packet:**
   - **Blocker / Decision:** 1 sentence on what blocks the next turn.
   - **Verified Facts & Evidence:** 3–5 concrete bullets + bounded snippet/error (no raw stack dumps or full files).
   - **Tried & Constraints:** 1 bullet ruling out dead ends.
   - **1 Sharp Question:** Specific enough to change the very next edit.
3. **Advisor returns a 1-turn, tool-free structured reply:**
   - Current skill returns `Verdict / Next / Prompt / Risk` (`<= 120–150` words).
   - **Phase 1 target ([Roadmap](ROADMAP.md)):** Tightens to `Verdict / Do / Verify / Risk` (`150–400` visible words) with deterministic `--snippet`/`--diff`/`--error-tail` evidence flags, a local preflight linter, rolling `--session-file` ledger, and `--effort medium` default with safe thinking-token headroom.

---

## Host-Agnostic Architecture & Transports (`--transport`)

`spot-advisor` works across **Claude Code**, **Codex CLI**, **Cursor**, **OpenCode**, and local/open-weight agent harnesses via [`skills/advisor/scripts/ask_expert.py`](skills/advisor/scripts/ask_expert.py):

- `--transport auto` *(default)*: Uses Direct Codex (`~/.codex/auth.json`) for text consults when signed in, routes `--image` screenshots or custom models through an OpenAI-compatible gateway (`EXPERTS_BASE_URL`), and falls back to local `claude -p`.
- `--transport codex`: Direct Codex subscription (`gpt-6.2-astra`, `gpt-6.2-sol`, `gpt-6-luna`).
- `--transport gateway`: Any OpenAI-compatible `/v1` endpoint (OpenRouter, LiteLLM, Subroute, vLLM) with optional `--image` UI checks.
- `--transport claude`: Local Claude Code CLI (`claude -p --no-session-persistence --tools ""`).

See [Install & Setup](docs/install.md) for skill installation and [Codex Setup Appendix](docs/codex-setup.md) for optional Codex CLI/Desktop configuration notes.

---

## Benchmarking & arXiv Paper

All performance, cost-savings, and token-efficiency claims for `spot-advisor` will be established through our pre-registered empirical evaluation rather than unverified estimates:

- **Research Design & Baselines:** [Research Protocol](docs/research-protocol.md) (`RQ1–RQ4`, 5 experimental arms including full-transcript advisor and compute-matched Best-of-N controls, plus an Effort × I/O Budget Pareto Sweep).
- **Evaluation Harness & Telemetry Schema:** [`eval/README.md`](eval/README.md) & [`eval/telemetry_schema.json`](eval/telemetry_schema.json).
- **Manuscript Scaffold (`cs.SE` / `cs.AI`):** [`paper/README.md`](paper/README.md) & [`paper/main.tex`](paper/main.tex).

---

## Verify Locally

Run the offline regression suite:

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_advisor.py
```
