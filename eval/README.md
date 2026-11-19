# `spot-advisor` Evaluation Suite (`eval/`)

This directory houses the reproducible evaluation contract, schemas, and (in Phase 2) frozen task manifests, runners, and logged experimental results for the `spot-advisor` arXiv paper.

---

## Planned Directory Layout

- [`telemetry_schema.json`](telemetry_schema.json) — Canonical JSON Schema (`Draft 2020-12`) for every per-task and per-consultation telemetry record.
- `tasks/` *(Phase 2)* — Frozen benchmark manifests (exact SWE-bench Verified / Terminal-Bench instance IDs + curated diagnostic hard-fork tasks).
- `runners/` *(Phase 2)* — Automated harness executing all 5 experimental arms (`A1`–`A4`, `T1`) and RQ3 ablations/effort sweeps.
- `results/` *(Phase 2)* — Summarized, auditable artifacts, pinned `pricing.json`, and scripts generating LaTeX tables/figures for [`../paper/main.tex`](../paper/main.tex).
- `runs/` *(git-ignored)* — Raw scratch workspaces, sandbox logs, and intermediate trial artifacts.

---

## Immutable Logging Rules

1. **Every run emits a validated JSONL record** conforming to [`telemetry_schema.json`](telemetry_schema.json), including `git_commit`, `executor_model`, `advisor_model`, `reasoning_effort`, `seed`, and separated `visible_output` vs. `reasoning` token counts.
2. **Never hand-edit `eval/results/` or `paper/` tables.** All metrics reported in [`../README.md`](../README.md) and [`../paper/main.tex`](../paper/main.tex) must be produced programmatically from committed JSONL logs.
3. **Never confuse API token truncation with visible length.** Telemetry records explicitly track both `visible_output_tokens`, `reasoning_tokens`, and `truncated` (`finish_reason == "length"`).

See [Research Protocol](../docs/research-protocol.md) for pre-registered research questions (`RQ1–RQ4`), baselines, and statistical tests.
