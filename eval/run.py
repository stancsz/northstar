"""Run two matched arms on a Codex subscription and retain per-task receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from codex_server import CodexServer, cli_command
from direct_session import DirectSession, ExecutorError
from sandbox import Sandbox, SandboxError, checked, docker
from suites import BROWSER_IMAGE, SWE_REVISION, Task, browser_tasks, pilot_diagnostics, swe_tasks


ROOT = Path(__file__).resolve().parent.parent
FORMAL_EXCLUSIONS = {e["task_id"]: e for e in json.loads((ROOT / "eval/formal-exclusions.json").read_bytes())}
ADVISOR = ROOT / "skills/advisor/scripts/ask_expert.py"
LUNA = "gpt-6-luna"
ASTRA = "gpt-6.2-astra"
ARMS = {"spot_advisor": (LUNA, "max"), "astra_only": (ASTRA, "medium")}
DEFAULT_SEED = 20261120
TOOLS = [
    {
        "name": "run_command",
        "description": "Run a shell command inside the task's isolated repository and return its output.",
        "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}},
                        "required": ["command"], "additionalProperties": False},
    },
    {
        "name": "verify_checkpoint",
        "description": "Run the task's public check. If you received guidance, say whether you applied it.",
        "inputSchema": {"type": "object", "properties": {"advice_applied": {"type": "boolean"},
                        "command": {"type": "string", "description": "Optional public test command for coding tasks."}},
                        "additionalProperties": False},
    },
]
BROWSER_TOOL = {
    "name": "browser_action",
    "description": "Observe Chromium or act on a visible control by its exact label. Selections use option text.",
    "inputSchema": {
        "type": "object", "properties": {
            "action": {"enum": ["observe", "click", "fill", "select"]},
            "label": {"type": "string"}, "value": {"type": "string"},
        }, "required": ["action"], "additionalProperties": False,
    },
}


def dump(path: Path, value) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp",
                                     mode="w", encoding="utf-8", delete=False) as journal:
        temporary = Path(journal.name)
        try:
            json.dump(value, journal, ensure_ascii=False, indent=2, sort_keys=True)
            journal.write("\n")
            journal.flush()
            os.fsync(journal.fileno())
        except BaseException:
            journal.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        if path.exists():
            raise FileExistsError(path)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def response(message: str, success: bool = True) -> dict:
    return {"success": success, "contentItems": [{"type": "inputText", "text": message}]}


def output_text(result: subprocess.CompletedProcess, size: int) -> str:
    merged = (result.stdout + b"\n" + result.stderr).decode("utf-8", errors="replace").strip()
    if len(merged) <= size:
        return merged
    return "(tail)\n" + merged[-size:]


class TaskExecution:
    def __init__(self, task: Task, arm: str, workspace: Sandbox, folder: Path, deadline: float,
                 *, tool_limit: int = 100):
        self.task = task
        self.arm = arm
        self.workspace = workspace
        self.folder = folder
        self.deadline = deadline
        self.tools = 0
        self.tool_limit = tool_limit
        self.last_failure = None
        self.last_outcome = ""
        self.consultations: list[dict] = []
        self.checkpoints: list[dict] = []
        self.events: list[dict] = []

    def remaining(self, cap: float = 60) -> float:
        seconds = min(cap, self.deadline - time.monotonic())
        if seconds <= 0:
            raise TimeoutError("Task reached its wall-clock limit.")
        return seconds

    def revision(self) -> str:
        if self.task.browser:
            content = self.browser_state()
        else:
            content = self.workspace.patch() if self.task.upstream else self.workspace.archive()
        return hashlib.sha256(content).hexdigest()

    def browser_state(self) -> bytes:
        result = self.workspace.exec("python -B browser_driver.py state", timeout=self.remaining(12))
        if result.returncode:
            checked(result)
        return result.stdout

    def consult(self, reason: str, evidence: str, revision: str) -> str:
        number = len(self.consultations) + 1
        state = {
            "task_id": self.task.id, "revision": revision, "phase": "Public verification failed.",
            "goal": self.task.goal[:450], "constraints": list(self.task.constraints),
            "acceptance": [self.task.acceptance],
            "evidence": [evidence[-700:]], "last_advice_outcome": self.last_outcome,
        }
        state_path = self.folder / f"consultation-{number}.json"
        dump(state_path, state)
        args = [
            sys.executable, "-B", str(self.folder.parent.parent / "advisor-frozen.py"),
            "--transport", "codex", "--model", ASTRA,
            "--protocol", "v2", "--effort", "medium", "--state-file", str(state_path),
            "--session-file", str(self.folder / "advisor-session.json"),
            "--trigger", reason, "--timeout-seconds", str(max(1, self.remaining(55) - 1)),
            "--question", "Given these observed results, what one change and verification should the executor try?",
        ]
        started = time.monotonic()
        result = {}
        try:
            completed = subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace",
                                       timeout=self.remaining(60), check=False)
            result = json.loads(completed.stdout)
        except (subprocess.TimeoutExpired, ValueError):
            journal = self.folder / "advisor-session.json.attempts.jsonl"
            attempts = {}
            if journal.is_file():
                for line in journal.read_text(encoding="utf-8").splitlines():
                    event = json.loads(line)
                    if event["round"] == number:
                        attempts[event["attempt_id"]] = event
            result = {"status": "unavailable", "attempts": list(attempts.values())}
        row = {
            "number": number, "trigger": reason, "revision": revision, "attempts": result.get("attempts", []),
            "status": result.get("status", "unavailable"), "packet_chars": result.get("packet_chars"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "advice_applied": None, "next_check_passed": None,
        }
        self.consultations.append(row)
        guidance = result.get("advice_fields")
        if row["status"] == "ok" and isinstance(guidance, dict) and self.revision() == revision:
            return "\n\nAdvisor guidance to check against the task evidence:\n" + "\n".join(
                f"{key.capitalize()}: {value}" for key, value in guidance.items()
            )
        return ""

    def verify(self, advice_applied: bool | None = None, command: str | None = None) -> tuple[str, bool]:
        if self.task.browser:
            state = json.loads(self.browser_state())
            passed = browser_accepted(self.task, state)
            code = int(not passed)
            text = ("The requested changes are confirmed." if passed else
                    "The confirmed records still differ from the requested final state.")
        else:
            check = self.workspace.exec(command or self.task.public_check, timeout=self.remaining())
            text = output_text(check, 1_400) or "(no output)"
            code = check.returncode
            passed = code == 0
        if self.consultations and self.consultations[-1]["next_check_passed"] is None:
            previous = self.consultations[-1]
            previous["advice_applied"] = advice_applied
            previous["next_check_passed"] = passed
            self.last_outcome = f"The next check {'passed' if passed else 'failed'} (exit {code})."
        check_identity = "browser_state" if self.task.browser else (command or self.task.public_check).strip()
        failure = None if passed else check_identity
        reason = None
        if not passed and code == self.task.conflict_exit:
            reason = "conflicting_evidence"
        elif failure is not None and failure == self.last_failure:
            reason = "two_failed_checks"
        self.last_failure = failure
        revision = self.revision()
        self.checkpoints.append({"revision": revision, "passed": passed, "exit_code": code,
                                 "trigger": reason, "output_sha256": hashlib.sha256(text.encode()).hexdigest()})
        rendered = f"Public check exit {code}\n{text}"
        if (self.arm == "spot_advisor" and reason and len(self.consultations) < 3
                and all(call["revision"] != revision for call in self.consultations)):
            rendered += self.consult(reason, rendered, revision)
            self.last_failure = None
        return rendered, passed

    def handle(self, call: dict) -> dict:
        self.tools += 1
        if self.tools > self.tool_limit:
            raise TimeoutError("Task reached its tool-call limit.")
        tool = call.get("tool")
        arguments = call.get("arguments") or {}
        started = time.monotonic()
        try:
            if tool == "run_command" and self.task.browser is None:
                command = arguments.get("command")
                if not isinstance(command, str) or not command.strip() or len(command) > 16_000:
                    return response("Provide a nonempty command under 16,000 characters.", False)
                finished = self.workspace.exec(command, timeout=self.remaining())
                text = f"Exit {finished.returncode}\n{output_text(finished, 6_000)}"
                return response(text, finished.returncode == 0)
            if tool == "browser_action" and self.task.browser:
                action, label, value = (arguments.get(key) for key in ("action", "label", "value"))
                if action not in ("observe", "click", "fill", "select"):
                    return response("Use a visible browser action.", False)
                parts = ["python", "-B", "browser_driver.py", action]
                if action != "observe":
                    if not isinstance(label, str) or not label or len(label) > 200:
                        return response("Supply an exact nonempty control label.", False)
                    parts.append("--label=" + label)
                if action in ("fill", "select"):
                    if not isinstance(value, str) or len(value) > 500:
                        return response("Supply the desired text or option under 500 characters.", False)
                    parts.append("--value=" + value)
                result = self.workspace.exec(shlex.join(parts), timeout=self.remaining(20))
                self.events.append({"browser_action": action, "label": label, "value": value,
                                    "output": output_text(result, 4_000), "ok": result.returncode == 0})
                return response(output_text(result, 4_000), result.returncode == 0)
            if tool == "verify_checkpoint":
                applied = arguments.get("advice_applied")
                command = arguments.get("command")
                if command is not None and (not isinstance(command, str) or len(command) > 16_000):
                    return response("Supply a public check command under 16,000 characters.", False)
                text, passed = self.verify(applied if isinstance(applied, bool) else None, command)
                return response(text, passed)
            return response("Unknown tool.", False)
        except subprocess.TimeoutExpired:
            return response("The isolated command reached its time limit.", False)
        finally:
            self.events.append({"tool": tool, "elapsed_seconds": round(time.monotonic() - started, 3)})


def prepare_inputs(folder: Path, task: Task) -> Path:
    work = folder / "work"
    work.mkdir()
    for name, content in task.inputs.items():
        destination = work / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
    return work


def browser_accepted(task: Task, state: dict) -> bool:
    return state.get("records") == task.browser["expected"]


def start_browser(sandbox: Sandbox) -> None:
    checked(docker("exec", "-d", sandbox.container, "/bin/sh", "-c",
                   "exec chromedriver --port=9515 >/tmp/chromedriver.log 2>&1"))
    checked(sandbox.exec("python -B browser_driver.py start", timeout=45))


def grade(task: Task, work: Path, patch: bytes, folder: Path) -> tuple[bool, str]:
    if task.browser:
        accepted = browser_accepted(task, json.loads(patch))
        return accepted, "passed" if accepted else "verifier_failed"
    with Sandbox(task.image) as verifier:
        if task.upstream:
            verifier.initial(task, work)
            if patch and verifier.exec("git apply --binary -", data=patch).returncode:
                return False, "patch_rejected"
            source = task.upstream.parents[2]
            tests = subprocess.check_output([
                "git", "-C", str(source), "-c", "core.autocrlf=false", "-c", "core.eol=lf",
                "archive", "--format=tar", SWE_REVISION, f"v2/tasks/{task.id}/tests",
            ])
            checked(verifier.exec("mkdir -p /tests && tar -xf - --strip-components=4 -C /tests", data=tests))
            result = verifier.exec("/bin/bash /tests/test.sh", timeout=task.timeout)
            reward = verifier.exec("cat /logs/verifier/reward.txt")
            (folder / "verifier.log").write_text(output_text(result, 12_000), encoding="utf-8")
            if reward.returncode or reward.stdout.strip() not in (b"0", b"0.0", b"1", b"1.0"):
                raise SandboxError("The upstream verifier did not produce a binary reward.")
            success = result.returncode == 0 and reward.returncode == 0 and reward.stdout.strip() in (b"1", b"1.0")
        else:
            verifier.restore_fresh_work(patch)
            grader_file = folder / "grader.py"
            grader_file.write_text(task.grader, encoding="utf-8", newline="\n")
            verifier.copy(grader_file, "/spot-advisor-grader.py")
            result = verifier.exec("PYTHONPATH=/work python -B /spot-advisor-grader.py")
            success = result.returncode == 0
        (folder / "verifier.log").write_text(output_text(result, 12_000), encoding="utf-8")
        return success, "passed" if success else "verifier_failed"


def source_digest() -> str:
    here = Path(__file__).parent
    sources = ("browser.Dockerfile", "browser_driver.py", "browser_fixture.html", "codex_server.py",
               "diagnostic_cases.py", "direct_session.py", "formal-exclusions.json", "run.py",
               "sandbox.py", "suites.py", "swe_tasks.json")
    paths = [ADVISOR, *(here / name for name in sources)]
    digest = hashlib.sha256()
    for path in sorted(paths):
        text = path.read_bytes().replace(b"\r\n", b"\n")
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + text + b"\0")
    return digest.hexdigest()


def run_arm(task: Task, arm: str, folder: Path, stage: str, seed: int, commit: str, code: str) -> dict:
    folder.mkdir(parents=True, exist_ok=False)
    work = prepare_inputs(folder, task)
    started = time.monotonic()
    model, effort = ARMS[arm]
    stamp = utc_now()
    error = None
    turn = {}
    patch = None
    agent_seconds = None
    quota_before = quota_after = subscription = None
    execution = None
    usage = {"input_tokens": None, "output_tokens": None}
    executor = DirectSession(folder / "executor-attempts.jsonl")
    with Sandbox(task.image) as sandbox:
        sandbox.initial(task, work)
        if task.browser:
            start_browser(sandbox)
        with CodexServer(folder / "server") as server:
            subscription = server.subscription()
            quota_before = server.quota()
            agent_started = time.monotonic()
            execution = TaskExecution(task, arm, sandbox, folder, agent_started + task.timeout)
            try:
                initial, _ = execution.verify()
                directions = (
                    "Use browser_action to observe and operate the local fixture. Confirm updates in the live page."
                    if task.browser else
                    "Use run_command for file inspection and edits. Run public tests with verify_checkpoint "
                    "and provide the test command. Use the same command when retrying a test. "
                    "Leave the finished patch in the workspace."
                )
                prompt = (
                    "Complete this benchmark task using the supplied tools. "
                    + directions + " The final grader runs independently.\n\n"
                    f"Task: {task.goal}\n"
                    "Constraints:\n" + "\n".join(f"- {rule}" for rule in task.constraints) +
                    f"\nAcceptance: {task.acceptance}\n\nThe initial check reported:\n{initial}"
                )
                tools = [BROWSER_TOOL, TOOLS[1]] if task.browser else TOOLS
                turn = executor.run(model, effort, prompt, tools, execution.handle, execution.remaining(task.timeout))
            except (TimeoutError, ExecutorError, subprocess.TimeoutExpired) as exc:
                error = str(exc)[:500]
            usage = executor.usage()
            agent_seconds = round(time.monotonic() - agent_started, 3)
            quota_after = server.quota()
        if task.browser:
            patch = checked(sandbox.exec("python -B browser_driver.py state", timeout=15)).encode()
            artifact = "browser-state.json"
        elif task.upstream:
            patch = sandbox.patch()
            artifact = "model.patch"
        else:
            patch = sandbox.archive()
            artifact = "workspace.tar"
        (folder / artifact).write_bytes(patch)

    try:
        accepted, verdict = grade(task, work, patch, folder)
    except (SandboxError, subprocess.TimeoutExpired) as exc:
        accepted, verdict = False, "infrastructure_error"
        error = str(exc)[:500]
    if executor.reroutes:
        verdict = "model_rerouted"
    elif not turn and verdict != "infrastructure_error":
        verdict = "incomplete_turn"
    return {
        "schema_version": 2, "run_id": folder.parent.parent.name, "task_id": task.id, "suite": task.suite,
        "stage": stage, "arm": arm, "seed": seed, "git_commit": commit, "source_sha256": code,
        "timestamp_utc": stamp, "subscription": subscription, "executor_model": model,
        "executor_effort": effort, "executor_usage": usage, "advisor_model": ASTRA if arm == "spot_advisor" else None,
        "quota_before": quota_before, "quota_after": quota_after, "turn": turn, "reroutes": executor.reroutes,
        "executor_transport": "codex_subscription_responses", "executor_attempts": executor.attempts,
        "error": error, "wall_seconds": round(time.monotonic() - started, 3),
        "agent_seconds": agent_seconds, "accepted": accepted, "verdict": verdict,
        "consultations": execution.consultations, "checkpoints": execution.checkpoints, "tool_events": execution.events,
        "artifact_sha256": hashlib.sha256(patch).hexdigest(),
    }


def ensure_image(task: Task) -> None:
    present = docker("image", "inspect", task.image)
    if present.returncode:
        if task.image == BROWSER_IMAGE:
            checked(docker("build", "--platform=linux/amd64", "--tag", BROWSER_IMAGE, "-", timeout=600,
                           data=(ROOT / "eval/browser.Dockerfile").read_bytes()))
        else:
            checked(docker("pull", "--platform=linux/amd64", task.image, timeout=600))


def run_pair(task: Task, pair: dict, folder: Path, stage: str, seed: int, commit: str, code: str,
             stop: threading.Event) -> None:
    if stop.is_set():
        return
    if task.id in FORMAL_EXCLUSIONS:
        print(f"{task.id}: excluded before execution", flush=True)
        return
    ensure_image(task)
    for arm in pair["arms"]:
        if stop.is_set():
            return
        arm_folder = folder / task.id / arm
        result_file = arm_folder / "result.json"
        if result_file.is_file():
            continue
        if arm_folder.exists():
            # A partially written trial may have reached the provider. Preserve it rather than charging twice.
            raise RuntimeError(f"An interrupted trial needs its journal reconciled: {arm_folder}")
        print(f"Running {task.id} / {arm}", flush=True)
        row = run_arm(task, arm, arm_folder, stage, seed, commit, code)
        dump(result_file, row)
        print(f"{task.id} / {arm}: {row['verdict']} | accepted={row['accepted']} | "
              f"{row['agent_seconds']} s | {len(row['consultations'])} consultation(s)", flush=True)
        if any(attempt["status"] == "rate_limited" for attempt in row["executor_attempts"]):
            stop.set()
            raise ExecutorError("Codex subscription returned HTTP 429. Retained the attempt and stopped launching tasks.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["pilot", "formal"], default="pilot")
    parser.add_argument("--case", action="append", help="Run only the specified task ID (repeatable).")
    parser.add_argument("--output", type=Path, required=True, help="New or resumable run directory under eval/runs/.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of independent task pairs to run concurrently (1–4).")
    parser.add_argument("--swe-source", type=Path, default=ROOT / "eval/runs/swe-bench-pro-source")
    parser.add_argument("--suite", choices=("swe", "diagnostic", "browser"),
                        help="Optional suite slice, for integration and local debugging.")
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        parser.error("--workers must be between 1 and 4.")
    tasks = []
    if args.suite in (None, "diagnostic"):
        from suites import diagnostic_tasks
        tasks += pilot_diagnostics() if args.stage == "pilot" else diagnostic_tasks()
    if args.suite in (None, "browser"):
        tasks += browser_tasks(pilot=args.stage == "pilot")
    if args.suite in (None, "swe"):
        tasks += swe_tasks(args.swe_source.resolve(), args.stage)
    if args.case:
        selected = set(args.case)
        tasks = [task for task in tasks if task.id in selected]
        if {task.id for task in tasks} != selected:
            parser.error("Some --case IDs are absent from this stage.")
    folder = args.output.resolve()
    if not folder.is_relative_to(ROOT / "eval/runs") or folder == ROOT / "eval/runs":
        parser.error("--output must be a named directory under eval/runs/.")
    folder.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    code = source_digest()
    rng = random.Random(args.seed)
    plan = []
    for task in tasks:
        arms = list(ARMS)
        rng.shuffle(arms)
        plan.append({"task_id": task.id, "suite": task.suite, "arms": arms, "image": task.image})
    manifest = {"stage": args.stage, "seed": args.seed, "source_sha256": code, "git_commit": commit,
                "workers": args.workers, "swe_revision": SWE_REVISION,
                "codex_cli": subprocess.check_output([*cli_command(), "--version"], text=True).strip(),
                "settings": {arm: list(pair) for arm, pair in ARMS.items()}, "tasks": plan}
    listed = {task.id for task in tasks}
    exclusions = [e for task_id, e in FORMAL_EXCLUSIONS.items() if task_id in listed]
    if exclusions:
        manifest["exclusions"] = exclusions
    manifest_file = folder / "manifest.json"
    if manifest_file.is_file():
        if json.loads(manifest_file.read_text(encoding="utf-8")) != manifest:
            parser.error("This run was frozen with a different manifest. Choose a new output directory.")
    else:
        dump(manifest_file, manifest)
    frozen = folder / "advisor-frozen.py"
    if not frozen.exists():
        with frozen.open("xb") as stream:
            stream.write(ADVISOR.read_bytes())
    elif frozen.read_bytes() != ADVISOR.read_bytes():
        parser.error("The run's frozen advisor differs from the recorded code.")

    stop = threading.Event()
    errors = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        trials = {pool.submit(run_pair, task, pair, folder, args.stage, args.seed, commit, code, stop): task.id
                  for task, pair in zip(tasks, plan)}
        for completed in as_completed(trials):
            try:
                completed.result()
            except (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
                errors.append(trials[completed])
                print(f"{trials[completed]}: {exc}", file=sys.stderr, flush=True)
    if errors:
        print(f"{len(errors)} task pair(s) encountered an execution or infrastructure error.", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
