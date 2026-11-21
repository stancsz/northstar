"""Run either product against the same independent local diagnostic grader."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError, URLError

from claude_advisor_probe import send_native
from claude_native_session import run_native
from direct_session import DirectSession, ExecutorError
from run import ADVISOR, LUNA, TOOLS, TaskExecution, dump, grade, prepare_inputs
from sandbox import Sandbox
from suites import diagnostic_tasks


def main() -> None:
    cases = {task.id: task for task in diagnostic_tasks()}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=cases)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--arm", choices=("claude_native", "spot_advisor"), default="claude_native")
    args = parser.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if args.arm == "claude_native" and not key:
        parser.error("ANTHROPIC_API_KEY is required for native Advisor.")
    folder = args.output.resolve()
    if Path(__file__).resolve().parent / "runs" not in folder.parents:
        parser.error("Use an output directory under eval/runs/.")
    task = cases[args.case]
    frozen = folder / "advisor-frozen.py"
    advisor_digest = None
    if args.arm == "spot_advisor":
        source = ADVISOR.read_bytes()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            with frozen.open("xb") as destination:
                destination.write(source)
        except FileExistsError:
            if frozen.read_bytes() != source:
                parser.error("This run uses a different frozen Spot Advisor revision. Choose a new output directory.")
        advisor_digest = hashlib.sha256(source).hexdigest()
    folder = folder / task.id / args.arm
    folder.mkdir(parents=True, exist_ok=False)
    verified_task = replace(task, grader=task.inputs["check.py"] + "\n" + task.grader)
    dump(folder / "manifest.json", {
        "task": task.id, "arm": args.arm, "image": task.image,
        "tool_limit": 40, "executor_seconds": 240,
        "inputs_sha256": hashlib.sha256(json.dumps(task.inputs, sort_keys=True).encode()).hexdigest(),
        "grader_sha256": hashlib.sha256(verified_task.grader.encode()).hexdigest(),
        "spot_advisor_sha256": advisor_digest,
    })
    work = prepare_inputs(folder, task)
    with Sandbox(task.image) as sandbox, (folder / "receipts.jsonl").open("x", encoding="utf-8") as journal:
        sandbox.initial(task, work)
        execution = TaskExecution(task, args.arm, sandbox, folder, time.monotonic() + 240, tool_limit=40)

        def record(receipt):
            journal.write(json.dumps(receipt) + "\n")
            journal.flush()

        prompt = (
            f"{task.goal}\nConstraints: {task.constraints}\nAcceptance: {task.acceptance}\n"
            f"First run verify_checkpoint with {task.public_check!r}, then repair and verify."
        )
        try:
            if args.arm == "claude_native":
                turn = run_native(lambda payload, timeout: send_native(key, payload, timeout), prompt, TOOLS,
                                  execution.handle, execution.remaining, on_receipt=record)
            else:
                session = DirectSession(folder / "executor-attempts.jsonl")
                turn = session.run(LUNA, "max", prompt, TOOLS, execution.handle, execution.remaining(240))
        except HTTPError as exc:
            turn = {"status": "anthropic_http_error", "code": exc.code}
        except (URLError, TimeoutError, ExecutorError, subprocess.TimeoutExpired):
            turn = {"status": "executor_interrupted"}
        patch = sandbox.archive()
    (folder / "workspace.tar").write_bytes(patch)
    accepted, verdict = grade(verified_task, work, patch, folder)
    dump(folder / "result.json", {"task": task.id, "arm": args.arm, "accepted": accepted,
                                  "verdict": verdict, "turn": turn, "consultations": execution.consultations})


if __name__ == "__main__":
    main()
