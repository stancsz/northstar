"""Host lifecycle supervision for autonomous goal agents, outside worker queues."""
from __future__ import annotations

import asyncio
import importlib.util
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

from starlette.responses import JSONResponse
from starlette.routing import Route

STACK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("goal_host_runtime", STACK / "runtime/runner.py")
runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runtime)
_scope_spec = importlib.util.spec_from_file_location(
    "goal_candidate_scope", STACK / "autonomy/candidate_scope.py")
candidate_scope = importlib.util.module_from_spec(_scope_spec)
_scope_spec.loader.exec_module(candidate_scope)
ID = re.compile(r"^g-[a-f0-9]{32}$")
TERMINAL = {"COMPLETE", "CANCELED", "NEEDS_USER"}


class GoalManager:
    def __init__(self, state_root: Path, workspace: Path):
        self.state_root = Path(state_root).resolve()
        self.workspace = Path(workspace).resolve()
        self.directory = self.state_root / "autonomy" / "goals"
        self.watchers = {}
        self.processes = {}
        self.cancel_watchers = {}
        self.closing = False

    def _dir(self, goal_id):
        if not isinstance(goal_id, str) or not ID.fullmatch(goal_id):
            raise ValueError("invalid autonomous goal ID")
        return self.directory / goal_id

    def _read(self, path, default=None):
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def _event(self, goal_id, event, **fields):
        with (self._dir(goal_id) / "host-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": event, "at": runtime.now(), **fields}) + "\n")

    def check_catalog(self):
        data = self._read(self.state_root / "trusted-checks.json", {})
        if not isinstance(data, dict):
            raise ValueError("trusted check registry must be an object")
        return data

    def _scope(self, paths):
        if not isinstance(paths, list) or any(not isinstance(p, str) or not p for p in paths):
            raise ValueError("write_paths must be an array of project paths")
        result = []
        for value in paths:
            path = (self.workspace / value).resolve()
            if not path.is_relative_to(self.workspace):
                raise ValueError("write path escapes workspace")
            result.append(path.relative_to(self.workspace).as_posix() or ".")
        return sorted(set(result))

    def _checks(self, names):
        if not isinstance(names, list) or any(not isinstance(n, str) for n in names):
            raise ValueError("check_ids must be an array of trusted check names")
        catalog, result = self.check_catalog(), []
        for name in names:
            item = catalog.get(name)
            if not isinstance(item, dict):
                raise ValueError(f"unknown trusted check: {name}")
            argv = item.get("argv")
            cwd = (self.workspace / item.get("cwd", ".")).resolve()
            if (not isinstance(argv, list) or not argv
                    or any(not isinstance(arg, str) or not arg for arg in argv)
                    or not cwd.is_relative_to(self.workspace)):
                raise ValueError(f"invalid trusted check definition: {name}")
            result.append({"id": name, "argv": list(argv), "cwd": str(cwd)})
        return result

    async def create(self, request):
        allowed = {"workspace", "goal", "acceptance", "write_paths", "check_ids", "constraints",
                   "required_inputs", "user_gates"}
        if not isinstance(request, dict) or set(request) - allowed:
            raise ValueError("unsupported goal fields; commands and CLI options are not accepted")
        if Path(request.get("workspace", "")).resolve() != self.workspace:
            raise ValueError("goal workspace must match configured workspace")
        goal, acceptance = request.get("goal"), request.get("acceptance")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal is required")
        if (not isinstance(acceptance, list) or not acceptance
                or any(not isinstance(a, str) or not a.strip() for a in acceptance)):
            raise ValueError("original acceptance criteria are required")
        constraints = request.get("constraints", [])
        if not isinstance(constraints, list) or any(not isinstance(c, str) for c in constraints):
            raise ValueError("constraints must be strings")
        goal_id = "g-" + uuid.uuid4().hex
        directory = self._dir(goal_id)
        required_inputs = request.get("required_inputs", [])
        user_gates = request.get("user_gates", [])
        if (not isinstance(required_inputs, list) or any(not isinstance(p, str) for p in required_inputs)
                or not isinstance(user_gates, list) or any(not isinstance(g, str) or not g for g in user_gates)):
            raise ValueError("required_inputs and user_gates must be explicit string arrays")
        inputs = []
        for value in required_inputs:
            path = (self.workspace / value).resolve()
            if not path.is_relative_to(self.workspace):
                raise ValueError("required input must be in the authorized workspace")
            inputs.append(str(path))
        scope = self._scope(request.get("write_paths", []))
        baseline = candidate_scope.baseline_snapshot(self.workspace, scope)
        spec = {"id": goal_id, "workspace": str(self.workspace), "goal": goal.strip(),
                "acceptance": [a.strip() for a in acceptance],
                "write_paths": scope, "baseline": baseline,
                "required_inputs": inputs, "user_gates": user_gates,
                "checks": self._checks(request.get("check_ids", [])), "constraints": constraints,
                "mcp_config": str(STACK / "mcp/client-config.json"),
                "owner_prompt": str(STACK / "prompts/autonomous-main.md"),
                "supervisor_prompt": str(STACK / "prompts/autonomous-recovery.md"),
                "state_root": str(self.state_root), "goal_state_dir": str(directory)}
        for key in ("mcp_config", "owner_prompt", "supervisor_prompt"):
            if not Path(spec[key]).is_file():
                raise ValueError(f"host setup is missing {key}")
        runtime.atomic_json(directory / "spec.json", spec)
        runtime.atomic_json(directory / "state.json", {
            "id": goal_id, "status": "RUNNING", "session_id": None, "recovery_count": 0})
        self._launch(goal_id)
        return self.get(goal_id)

    def get(self, goal_id):
        directory = self._dir(goal_id)
        spec = self._read(directory / "spec.json")
        if not spec:
            raise KeyError("unknown autonomous goal")
        state = self._read(directory / "state.json", {"status": "RECOVERING"})
        process = self.processes.get(goal_id)
        return {"goal_id": goal_id, "goal": spec["goal"], "state": state,
                "controller_running": bool(process and process[0].poll() is None),
                "spec_path": str(directory / "spec.json"), "state_dir": str(directory)}

    def list(self):
        if not self.directory.exists():
            return []
        return [self.get(path.name) for path in sorted(self.directory.iterdir())
                if path.is_dir() and ID.fullmatch(path.name) and (path / "spec.json").is_file()]

    def report(self, goal_id):
        record = self.get(goal_id)
        spec = self._read(self._dir(goal_id) / "spec.json")
        state = record["state"]
        status = state.get("status", "RECOVERING")
        actions = {"COMPLETE": "查看结果后，由你设置下一条 Goal。",
                   "RUNNING": "Agent 正在自主执行，无需手动救场。",
                   "RECOVERING": "Agent 正在自主诊断和恢复，无需手动重派。",
                   "NEEDS_USER": "处理报告中的已核实外部依赖后，调用 resume_goal。",
                   "CANCELED": "已按指令停止，可恢复同一 Goal 或设置新 Goal。",
                   "CANCELING": "正在清理本 Goal 的任务，系统会自动继续清理。"}
        return {"goal_id": goal_id, "goal": spec["goal"], "status": status,
                "summary": state.get("last_summary"), "acceptance": spec["acceptance"],
                "accepted_result": state.get("accepted_receipt"),
                "candidate": state.get("checked_candidate"),
                "recovery_count": state.get("recovery_count", 0),
                "host_restart_count": state.get("host_restart_count", 0),
                "session_reset_count": len(state.get("previous_session_ids", [])),
                "blocker": state.get("blocker") if status == "NEEDS_USER" else None,
                "next_user_action": actions.get(status, "查看进度。"),
                "controller_running": record["controller_running"], "evidence_dir": str(self._dir(goal_id))}

    def _launch(self, goal_id):
        if goal_id not in self.watchers or self.watchers[goal_id].done():
            self.watchers[goal_id] = asyncio.create_task(self._watch(goal_id))

    async def _watch(self, goal_id):
        directory = self._dir(goal_id)
        while not self.closing:
            state = self._read(directory / "state.json", {})
            if (directory / "cancel.request").exists() or state.get("status") in TERMINAL:
                return
            job, proc = runtime.Job(), None
            try:
                with (directory / "runner-stderr.log").open("a", encoding="utf-8") as err:
                    python = Path(sys.executable)
                    if python.name.lower() == "pythonw.exe":
                        python = python.with_name("python.exe")
                    proc = subprocess.Popen([
                        str(python), str(STACK / "autonomy/runner.py"),
                        "--spec", str(directory / "spec.json"), "--state-dir", str(directory)],
                        cwd=self.workspace, stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL, stderr=err,
                        creationflags=0x4 | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
                    job.assign(proc)
                    self.processes[goal_id] = (proc, job)
                    runtime.atomic_json(directory / "process.json", {
                        "pid": proc.pid, "process_token": runtime.process_token(proc.pid)})
                    self._event(goal_id, "controller_started", pid=proc.pid)
                    code = await asyncio.to_thread(proc.wait)
                    self._event(goal_id, "controller_exited", exit_code=code)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._event(goal_id, "host_recovery", error_type=type(exc).__name__)
            finally:
                job.close()
                if proc is not None and proc.poll() is None:
                    proc.kill()
                    await asyncio.to_thread(proc.wait)
                self.processes.pop(goal_id, None)
            if self.closing or (directory / "cancel.request").exists():
                return
            state = self._read(directory / "state.json", {})
            if state.get("status") in TERMINAL:
                return
            state.update(status="RECOVERING", host_restart_count=state.get("host_restart_count", 0) + 1)
            runtime.atomic_json(directory / "state.json", state)
            # Yield to other goals between real process-exit events; never a retry ceiling.
            await asyncio.sleep(.2)

    async def startup(self):
        for record in self.list():
            if (self._dir(record["goal_id"]) / "cancel.request").exists():
                self._launch_cancel(record["goal_id"])
                continue
            if record["state"].get("status") not in TERMINAL:
                self._launch(record["goal_id"])

    async def _cancel_owned_tasks(self, goal_id):
        """Cancel only assignments associated with this goal, over official A2A."""
        import httpx
        from a2a.client import A2ACardResolver, ClientConfig, create_client
        from a2a.types import CancelTaskRequest, GetTaskRequest, TaskState

        unresolved = []
        for path in (self.state_root / "stacks").glob("*/stack.json"):
            stack = self._read(path)
            if stack.get("goal_id") != goal_id:
                continue
            for role in stack["roles"]:
                assignments = [self._read(p) for p in (path.parent / "assignments").glob("*.json")]
                ids = [a["task_id"] for a in assignments if a.get("role_id") == role["id"] and a.get("task_id")]
                if not ids:
                    continue
                base = f"http://127.0.0.1:18890/stacks/{stack['stack_id']}/agents/{role['id']}"
                try:
                    async with httpx.AsyncClient(timeout=15) as http:
                        card = await A2ACardResolver(http, base).get_agent_card()
                        client = create_client(card, client_config=ClientConfig(
                            streaming=False, polling=False, httpx_client=http,
                            supported_protocol_bindings=["JSONRPC"]))
                        if inspect.isawaitable(client):
                            client = await client
                        try:
                            for task_id in ids:
                                task = await client.get_task(GetTaskRequest(id=task_id))
                                if task.status.state in (TaskState.TASK_STATE_SUBMITTED, TaskState.TASK_STATE_WORKING):
                                    await client.cancel_task(CancelTaskRequest(id=task_id))
                        finally:
                            close = getattr(client, "close", None)
                            if close:
                                result = close()
                                if inspect.isawaitable(result):
                                    await result
                except Exception:
                    unresolved.extend(ids)
        return unresolved

    def _launch_cancel(self, goal_id):
        if goal_id not in self.cancel_watchers or self.cancel_watchers[goal_id].done():
            self.cancel_watchers[goal_id] = asyncio.create_task(self._finish_cancel(goal_id))

    async def _finish_cancel(self, goal_id):
        while not self.closing:
            unresolved = await self._cancel_owned_tasks(goal_id)
            state = self._read(self._dir(goal_id) / "state.json", {})
            state.update(status="CANCELING" if unresolved else "CANCELED", unresolved_task_ids=unresolved)
            runtime.atomic_json(self._dir(goal_id) / "state.json", state)
            if not unresolved:
                return
            await asyncio.sleep(1)

    async def cancel(self, goal_id):
        record = self.get(goal_id)
        if record["state"].get("status") == "COMPLETE":
            return record
        directory = self._dir(goal_id)
        (directory / "cancel.request").write_text("explicit controller cancellation\n", encoding="utf-8")
        process = self.processes.get(goal_id)
        if process:
            process[1].close()
        watcher = self.watchers.get(goal_id)
        if watcher:
            await asyncio.gather(watcher, return_exceptions=True)
        unresolved = await self._cancel_owned_tasks(goal_id)
        state = self._read(directory / "state.json", {})
        state.update(status="CANCELING" if unresolved else "CANCELED", unresolved_task_ids=unresolved)
        runtime.atomic_json(directory / "state.json", state)
        if unresolved:
            self._launch_cancel(goal_id)
        return self.get(goal_id)

    async def resume(self, goal_id):
        record = self.get(goal_id)
        if record["controller_running"] or record["state"].get("status") == "COMPLETE":
            return record
        if record["state"].get("status") == "CANCELING":
            raise ValueError("Owned task cancellation is still recovering; resume after it finishes")
        directory = self._dir(goal_id)
        (directory / "cancel.request").unlink(missing_ok=True)
        state = record["state"]
        state.update(status="RUNNING", last_error="Controller explicitly resumed this same goal; re-check current evidence.")
        runtime.atomic_json(directory / "state.json", state)
        self._launch(goal_id)
        return self.get(goal_id)

    async def close(self):
        self.closing = True
        for _proc, job in list(self.processes.values()):
            job.close()
        await asyncio.gather(*self.watchers.values(), *self.cancel_watchers.values(), return_exceptions=True)

    def freeze(self, goal_id, files):
        directory = self._dir(goal_id)
        spec = self._read(directory / "spec.json")
        if not spec:
            raise KeyError("unknown autonomous goal")
        if not isinstance(files, list) or not files or any(not isinstance(p, str) for p in files):
            raise ValueError("files must name the actual candidate files")
        allowed = [(self.workspace / p).resolve() for p in spec["write_paths"]]
        names = []
        for value in files:
            path = (self.workspace / value).resolve()
            if (not path.is_relative_to(self.workspace)
                    or not (any(path == p or path.is_relative_to(p) for p in allowed)
                            or path.is_relative_to(directory / "artifacts"))):
                raise ValueError("candidate file outside immutable goal scope")
            names.append(path.relative_to(self.workspace).as_posix())
        # The requested list alone may omit a real scoped change, so the frozen
        # candidate always covers every scoped file that changed against the
        # immutable pre-Goal baseline.
        changes = candidate_scope.scope_changes(
            self.workspace, spec["write_paths"], spec.get("baseline", {}))
        deleted = sorted(name for name, digest in changes.items() if digest is None)
        if deleted:
            raise ValueError("Scoped file was deleted and cannot be represented in a candidate: "
                             + ", ".join(deleted))
        names = sorted(set(names) | set(changes))
        module_spec = importlib.util.spec_from_file_location("goal_freeze", STACK / "runtime/review.py")
        helper = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(helper)
        helper.ROOT = self.workspace
        manifest = helper.candidate(names)
        destination = directory / "artifacts" / f"candidate-{uuid.uuid4().hex}.json"
        runtime.atomic_json(destination, manifest)
        return {"goal_id": goal_id, "candidate": manifest["candidate"],
                "manifest_path": str(destination), "files": manifest["files"]}

    async def _api(self, request):
        try:
            goal_id = request.path_params.get("goal_id")
            operation = request.url.path.rsplit("/", 1)[-1]
            if request.method == "GET":
                if request.url.path.endswith("/checks"):
                    return JSONResponse({"checks": [{"id": name, "description": item.get("description", name)}
                                                    for name, item in self.check_catalog().items()]})
                if operation == "report":
                    return JSONResponse(self.report(goal_id))
                return JSONResponse(self.get(goal_id) if goal_id else {"goals": self.list()})
            if not goal_id:
                return JSONResponse(await self.create(await request.json()), status_code=201)
            if operation == "candidate":
                return JSONResponse(self.freeze(goal_id, (await request.json()).get("files")))
            return JSONResponse(await (self.cancel(goal_id) if operation == "cancel" else self.resume(goal_id)))
        except KeyError:
            return JSONResponse({"error": "unknown autonomous goal"}, status_code=404)
        except (ValueError, OSError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    def routes(self):
        return [Route("/control/goals/checks", self._api, methods=["GET"]),
                Route("/control/goals", self._api, methods=["GET", "POST"]),
                Route("/control/goals/{goal_id}", self._api, methods=["GET"]),
                Route("/control/goals/{goal_id}/report", self._api, methods=["GET"]),
                Route("/control/goals/{goal_id}/cancel", self._api, methods=["POST"]),
                Route("/control/goals/{goal_id}/resume", self._api, methods=["POST"]),
                Route("/control/goals/{goal_id}/candidate", self._api, methods=["POST"])]
