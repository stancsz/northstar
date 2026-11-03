"""Run a goal's immutable, host-selected checks against one frozen candidate."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

STACK = Path(__file__).resolve().parents[1]
_runtime_spec = importlib.util.spec_from_file_location("autonomy_checks_runtime", STACK / "runtime" / "runner.py")
runtime = importlib.util.module_from_spec(_runtime_spec)
_runtime_spec.loader.exec_module(runtime)
_review_spec = importlib.util.spec_from_file_location("autonomy_checks_review", STACK / "runtime" / "review.py")
review = importlib.util.module_from_spec(_review_spec)
_review_spec.loader.exec_module(review)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _workspace_candidate(workspace: Path, files):
    review.ROOT = workspace
    return review.candidate(files)


def _manifest_for(spec: dict, candidate_id: str, artifacts: Path):
    if not isinstance(candidate_id, str) or len(candidate_id) != 64 or any(c not in "0123456789abcdef" for c in candidate_id):
        raise ValueError("invalid candidate identity")
    for path in sorted(artifacts.glob("candidate-*.json")):
        resolved = path.resolve()
        if not resolved.is_relative_to(artifacts):
            continue
        try:
            manifest = _load_json(resolved)
            if isinstance(manifest, dict) and manifest.get("candidate") == candidate_id:
                workspace = Path(spec["workspace"]).resolve()
                if not isinstance(manifest.get("files"), dict):
                    raise ValueError("candidate manifest has no file hashes")
                current = _workspace_candidate(workspace, manifest["files"])
                if current != manifest:
                    raise ValueError("STALE candidate manifest; candidate files changed before checks")
                return manifest
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError("candidate manifest is unreadable or invalid") from exc
    raise ValueError("candidate manifest not found for requested identity")


def _safe_text(value):
    return runtime._safe_handoff(value)


def run_checks(spec_path: Path, candidate_id: str, output_path: Path) -> dict:
    spec_path = Path(spec_path).resolve()
    spec = _load_json(spec_path)
    if not isinstance(spec, dict):
        raise ValueError("goal spec must be an object")
    goal_id = spec.get("id")
    workspace = Path(spec.get("workspace", "")).resolve()
    state_dir = Path(spec.get("goal_state_dir", "")).resolve()
    artifacts = (state_dir / "artifacts").resolve()
    output_path = Path(output_path).resolve()
    if not isinstance(goal_id, str) or not goal_id:
        raise ValueError("goal spec has no goal ID")
    if not workspace.is_dir() or not state_dir.is_dir():
        raise ValueError("goal workspace or state directory is unavailable")
    if not output_path.is_relative_to(artifacts):
        raise ValueError("output must be inside the goal artifacts directory")

    report = {"goal_id": goal_id, "candidate": candidate_id,
              "checks_passed": False, "checks": []}
    try:
        manifest = _manifest_for(spec, candidate_id, artifacts)
        check_list = spec.get("checks")
        if not isinstance(check_list, list):
            raise ValueError("goal spec checks must be an array")
        for check in check_list:
            if (not isinstance(check, dict) or not isinstance(check.get("id"), str)
                    or not isinstance(check.get("argv"), list) or not check["argv"]
                    or any(not isinstance(arg, str) or not arg for arg in check["argv"])):
                raise ValueError("goal spec contains an invalid trusted check")
            cwd_value = Path(check.get("cwd", ""))
            cwd = (cwd_value if cwd_value.is_absolute() else workspace / cwd_value).resolve()
            if not cwd.is_relative_to(workspace) or not cwd.is_dir():
                raise ValueError(f"trusted check cwd is outside workspace or unavailable: {check['id']}")

        for check in check_list:
            # argv and cwd come only from the immutable host-created spec; no shell is involved.
            cwd_value = Path(check["cwd"])
            cwd = (cwd_value if cwd_value.is_absolute() else workspace / cwd_value).resolve()
            completed = subprocess.run(check["argv"], cwd=cwd, shell=False,
                                       capture_output=True, text=True, encoding="utf-8", errors="replace")
            report["checks"].append({
                "id": check["id"], "exit_code": completed.returncode,
                "output": _safe_text(completed.stdout + completed.stderr),
            })

        after = _workspace_candidate(workspace, manifest["files"])
        if after != manifest:
            report["error"] = "Candidate files changed during trusted checks; freeze and review the new candidate."
        else:
            report["checks_passed"] = all(item["exit_code"] == 0 for item in report["checks"])
    except Exception as exc:
        report["error"] = _safe_text(f"{type(exc).__name__}: {exc}")
    _atomic_json(output_path, report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_checks(args.spec, args.candidate, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(_safe_text(str(exc)))
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
