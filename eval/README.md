# Paired evaluation

The runner drives the two Codex subscription arms through the same local tools. Model requests use the existing direct Responses transport. A separate App Server client reads plan and quota metadata. Docker holds task environments without credentials or outbound networking.

## Prepare

Use Python 3.11 or later, Docker with Linux containers, Git, and a Codex CLI session signed into ChatGPT. Install report dependencies with `python -m pip install jsonschema 'matplotlib>=3.8'`. From the repository root:

```powershell
git -c core.autocrlf=false clone --depth 1 --filter=blob:none --sparse https://github.com/scaleapi/SWE-bench_Pro-os.git eval/runs/swe-bench-pro-source
git -C eval/runs/swe-bench-pro-source sparse-checkout set v2
git -C eval/runs/swe-bench-pro-source rev-parse HEAD
```

Use the revision listed in [the task manifest](swe_tasks.json). If upstream has advanced, fetch that revision and check it out in the evaluation clone. Selected images are fetched on demand. The Chromium image is built locally from [browser.Dockerfile](browser.Dockerfile).

## Run and regenerate

```powershell
python -B eval/run.py --stage pilot --output eval/runs/pilot
python -B eval/report.py eval/runs/pilot --output eval/runs/pilot-report
python -B eval/run.py --stage formal --output eval/runs/formal
python -B eval/report.py eval/runs/formal --output eval/runs/formal-report
```

Use `--suite diagnostic` or `--suite browser` for a targeted integration run. `--workers` runs up to four independent pairs concurrently, with the two arms of each pair still executed in order. Concurrency is part of the frozen run manifest. A run skips completed arms when resumed. Inspect any interrupted trial's journal before choosing whether to repeat it. The journal preserves dispatches, provider errors and unsuccessful outcomes alongside completed work. Use `regrade.py` to apply revised pilot grading to existing artifacts without new model calls. For a finished study, export the sanitized `evidence.jsonl`, metrics, and manifest with the frozen revision.

The report emits LaTeX from the captured records. A complete formal study requires paired observations for all 50 public coding tasks, 16 diagnostics and eight browser scenarios, with verified model identity and token attribution. See the [research protocol](../docs/research-protocol.md) and [schema](telemetry_schema.json).
