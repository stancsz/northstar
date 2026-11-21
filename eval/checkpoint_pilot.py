"""Exercise three live continuations on benign local diagnostic tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import subprocess
import time
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from checkpoint import Checkpoint, repository_snapshot
from direct_session import DirectSession, ExecutorError
from run import ADVISOR, ASTRA, LUNA, TOOLS, TaskExecution, dump, grade, prepare_inputs
from sandbox import Sandbox, SandboxError
from suites import diagnostic_tasks, load_swe_instances, pilot_diagnostics

TOOL_ALLOWANCE = 40
EXECUTOR_SECONDS = 120


def run_case(task, folder: Path, seed: int, *, natural_trigger: bool, prefix_seconds: int,
             continuation_seconds: int) -> None:
    with ExitStack() as snapshots:
        run_continuations(task, folder, seed, natural_trigger=natural_trigger, snapshots=snapshots,
                          prefix_seconds=prefix_seconds, continuation_seconds=continuation_seconds)


def run_continuations(task, folder: Path, seed: int, *, natural_trigger: bool, snapshots: ExitStack,
                      prefix_seconds: int, continuation_seconds: int) -> None:
    folder.mkdir()
    work = prepare_inputs(folder, task)
    verified_task = task if task.upstream else replace(task, grader=task.inputs["check.py"] + "\n" + task.grader)
    artifact_name = "model.patch" if task.upstream else "workspace.tar"
    prefix = DirectSession(folder / "prefix.jsonl")
    with Sandbox(task.image) as sandbox:
        sandbox.initial(task, work)
        execution = TaskExecution(task, "luna_only", sandbox, folder,
                                  time.monotonic() + prefix_seconds, tool_limit=TOOL_ALLOWANCE)
        prompt = (
            f"{task.goal}\nConstraints: {task.constraints}\nAcceptance: {task.acceptance}\n"
            f"First run verify_checkpoint with {task.public_check!r}, then repair and verify."
        )

        def checkpoint_ready():
            if not execution.checkpoints:
                return False
            latest = execution.checkpoints[-1]
            return bool(latest["trigger"]) if natural_trigger else not latest["passed"]

        try:
            turn = prefix.continue_run(
                LUNA, "max", [{"role": "user", "content": prompt}], TOOLS, execution.handle, prefix_seconds,
                stop_after_batch=checkpoint_ready,
            )
        except (TimeoutError, ExecutorError, subprocess.TimeoutExpired) as exc:
            turn = {"status": "prefix_failed", "error": str(exc)}
        if turn["status"] != "checkpoint" or execution.tools == TOOL_ALLOWANCE:
            workspace = sandbox.patch() if task.upstream else sandbox.archive()
            (folder / artifact_name).write_bytes(workspace)
            accepted, verdict = grade(verified_task, work, workspace, folder)
            dump(folder / "result.json", {
                "status": "prefix_failed" if turn["status"] == "prefix_failed" else "no_checkpoint",
                "prefix_usage": prefix.usage(),
                "reason": "tool_allowance_exhausted" if execution.tools == TOOL_ALLOWANCE else "no_eligible_trigger",
                "error": turn.get("error"),
                "accepted": accepted, "verdict": verdict,
                "workspace_sha256": hashlib.sha256(workspace).hexdigest(),
            })
            return
        trigger = execution.checkpoints[-1]["trigger"] if natural_trigger else "manual"
        remaining_tools = TOOL_ALLOWANCE - execution.tools
        if task.upstream:
            checkpoint_image = snapshots.enter_context(repository_snapshot(sandbox))
            base_commit = sandbox.base_commit
            checkpoint = None
        else:
            checkpoint_image = task.image
            checkpoint = Checkpoint.capture(sandbox, turn, remaining_tools)
    if checkpoint is not None:
        (folder / "checkpoint-workspace.tar").write_bytes(checkpoint.workspace)
    message_path = folder / "checkpoint-messages.json"
    dump(message_path, turn["messages"])
    order = ["luna_only", "luna_advice", "astra_takeover"]
    random.Random(seed).shuffle(order)
    dump(folder / "checkpoint-summary.json", {
        "task": task.id, "order": order,
        "workspace_sha256": hashlib.sha256(checkpoint.workspace).hexdigest() if checkpoint else None,
        "checkpoint_image": checkpoint_image if task.upstream else None,
        "messages_sha256": hashlib.sha256(message_path.read_bytes()).hexdigest(),
        "grader_sha256": hashlib.sha256(verified_task.grader.encode()).hexdigest() if not task.upstream else None,
        "remaining_tools": remaining_tools, "prefix_usage": prefix.usage(),
        "trigger": trigger,
    })
    for arm in order:
        output = folder / arm
        output.mkdir()
        session = DirectSession(output / "attempts.jsonl")
        with Sandbox(checkpoint_image) as sandbox:
            if checkpoint is None:
                sandbox.initial(task, work)
                sandbox.base_commit = base_commit
                messages = deepcopy(turn["messages"])
            else:
                messages = checkpoint.restore(sandbox)
            execution = TaskExecution(task, arm, sandbox, output, time.monotonic() + 60,
                                      tool_limit=remaining_tools)
            if arm == "luna_advice":
                checks = {item["call_id"] for item in messages
                          if item.get("type") == "function_call" and item.get("name") == "verify_checkpoint"}
                evidence = next(
                    item["output"] for item in reversed(messages)
                    if item.get("type") == "function_call_output" and item["call_id"] in checks
                )
                advice = execution.consult(trigger, evidence, execution.revision())
                if advice.strip():
                    messages.append({"role": "user", "content": advice})
            if arm == "astra_takeover":
                # Astra receives visible evidence, not Luna's model-specific reasoning items.
                messages = [item for item in messages if item.get("type") != "reasoning"]
            model, effort = (ASTRA, "medium") if arm == "astra_takeover" else (LUNA, "max")
            execution.deadline = time.monotonic() + continuation_seconds
            try:
                outcome = session.continue_run(model, effort, messages, TOOLS, execution.handle,
                                               execution.remaining(continuation_seconds))
            except (TimeoutError, ExecutorError, subprocess.TimeoutExpired) as exc:
                outcome = {"status": "executor_failed", "error": str(exc)}
            patch = sandbox.patch() if task.upstream else sandbox.archive()
        (output / artifact_name).write_bytes(patch)
        verification_error = None
        try:
            accepted, verdict = grade(verified_task, work, patch, output)
        except (SandboxError, subprocess.SubprocessError) as exc:
            accepted, verdict = None, "verifier_infrastructure_error"
            verification_error = str(exc)
        dump(output / "result.json", {
            "arm": arm, "accepted": accepted, "verdict": verdict, "turn": outcome,
            "verification_error": verification_error,
            "usage": session.usage(), "consultations": execution.consultations,
            "executor_tools": min(execution.tools, execution.tool_limit),
            "workspace_sha256": hashlib.sha256(patch).hexdigest(),
        })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    pilots = pilot_diagnostics()
    cases = {task.id: task for task in [*pilots, *diagnostic_tasks()]}
    parser.add_argument("--output", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--limit", type=int, choices=range(1, len(pilots) + 1))
    selection.add_argument("--case", choices=cases, action="append")
    selection.add_argument("--public-qutebrowser", dest="public_case", action="store_const",
                           const="qutebrowser", help="Use the screened color-helper refactor.")
    selection.add_argument("--public-openlibrary", dest="public_case", action="store_const",
                           const="openlibrary", help="Use the screened ISBNdb import helper task.")
    selection.add_argument("--qutebrowser-process-replay", dest="public_case", action="store_const",
                           const="process_replay", help="Replay the 2.0 process cleanup regression case.")
    parser.add_argument("--natural-trigger", action="store_true",
                        help="Fork only on the skill's repeated-failure or conflicting-evidence trigger.")
    args = parser.parse_args()
    folder = args.output.resolve()
    private_runs = Path(__file__).resolve().parent / "runs"
    if private_runs not in folder.parents:
        parser.error("Use an output directory under eval/runs/ for model transcripts and workspaces.")
    folder.mkdir(parents=True)
    shutil.copyfile(ADVISOR, folder / "advisor-frozen.py")
    prefix_seconds = continuation_seconds = EXECUTOR_SECONDS
    if args.public_case:
        manifest = json.loads((Path(__file__).with_name("checkpoint_tasks.json")).read_text(encoding="utf-8"))
        prefix_seconds = manifest["prefix_seconds"]
        continuation_seconds = manifest["continuation_seconds"]
        screened = {
            "qutebrowser": (manifest["tasks"][0], "Consolidate color interpolation into `qtutils`",
                            "QT_QPA_PLATFORM=offscreen python -c 'from qutebrowser.utils.qtutils import interpolate_color'"),
            "openlibrary": (manifest["tasks"][2], "Add ISBNdb line parsing and non-book format detection",
                            "python -c 'import runpy; m = runpy.run_path(\"scripts/providers/isbndb.py\"); "
                            "assert all(name in m for name in (\"get_line\", \"is_nonbook\", \"NONBOOK\"))'"),
            "process_replay": (
                "instance_qutebrowser__qutebrowser-c09e1439f145c66ee3af574386e277dd2388d094-v2ef375ac784985212b1805e1d0431dc8f1b3c171",
                "Successful process data is retained indefinitely",
                "QT_QPA_PLATFORM=offscreen python -c 'from PyQt5.QtCore import QCoreApplication; "
                "from qutebrowser.misc.guiprocess import GUIProcess; app = QCoreApplication([]); "
                "assert GUIProcess(\"cleanup-check\")._cleanup_timer.interval() == 3600000'",
            ),
        }
        instance, title, public_check = screened[args.public_case]
        task, = load_swe_instances(private_runs / "swe-bench-pro-source", [instance])
        if title not in task.goal:
            parser.error("The public instance differs from the screened task.")
        selected = [replace(task, public_check=public_check)]
    else:
        selected = [cases[case] for case in dict.fromkeys(args.case)] if args.case else pilots[:args.limit]
    dump(folder / "pilot-plan.json", {
        "cases": [task.id for task in selected],
        "seed": 20261121,
        "tool_allowance": TOOL_ALLOWANCE,
        "prefix_seconds": prefix_seconds,
        "continuation_seconds": continuation_seconds,
        "purpose": {
            "process_replay": "Regression replay of a 2.0 consultation case.",
            None: "Diagnostic qualification.",
        }.get(args.public_case, "Public repository qualification."),
        "natural_trigger": args.natural_trigger,
    })
    for index, task in enumerate(selected):
        run_case(task, folder / task.id, 20261121 + index, natural_trigger=args.natural_trigger,
                 prefix_seconds=prefix_seconds, continuation_seconds=continuation_seconds)


if __name__ == "__main__":
    main()
