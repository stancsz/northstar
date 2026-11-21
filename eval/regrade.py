"""Re-run the independent verifier on immutable pilot artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run import ARMS, ROOT, dump, ensure_image, grade, source_digest
from suites import browser_tasks, pilot_diagnostics, swe_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--swe-source", type=Path, default=ROOT / "eval/runs/swe-bench-pro-source")
    args = parser.parse_args()
    source = args.pilot.resolve()
    target = args.output.resolve()
    if target == source or not target.is_relative_to(ROOT / "eval/runs") or target == ROOT / "eval/runs":
        parser.error("Regrade output must be a distinct run under eval/runs/.")
    original = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if original["stage"] != "pilot":
        parser.error("Regrading with revised verification is limited to pilot artifacts.")
    cases = {task.id: task for task in [*pilot_diagnostics(), *browser_tasks(pilot=True),
                                        *swe_tasks(args.swe_source.resolve(), "pilot")]}
    manifest = {**original, "regraded_from": source.name, "grader_source_sha256": source_digest()}
    target.mkdir(parents=True, exist_ok=True)
    manifest_file = target / "manifest.json"
    if manifest_file.exists():
        if json.loads(manifest_file.read_text(encoding="utf-8")) != manifest:
            parser.error("This regrade directory has a different manifest.")
    else:
        dump(manifest_file, manifest)

    for entry in manifest["tasks"]:
        task = cases[entry["task_id"]]
        ensure_image(task)
        for arm in ARMS:
            arm_source = source / task.id / arm
            if not (arm_source / "result.json").is_file():
                continue
            folder = target / task.id / arm
            folder.mkdir(parents=True, exist_ok=True)
            result_file = folder / "result.json"
            if result_file.exists():
                continue
            row = json.loads((arm_source / "result.json").read_text(encoding="utf-8"))
            artifact = "browser-state.json" if task.browser else "model.patch" if task.upstream else "workspace.tar"
            patch = (arm_source / artifact).read_bytes()
            if hashlib.sha256(patch).hexdigest() != row["artifact_sha256"]:
                raise ValueError(f"Artifact hash differs from the original receipt: {task.id} / {arm}")
            accepted, verdict = grade(task, arm_source / "work", patch, folder)
            dump(result_file, {**row, "accepted": accepted, "verdict": verdict})
            print(f"{task.id} / {arm}: {row['verdict']} -> {verdict}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
