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
    def __init__(self, state_root: Path, workspace: Path, registry=None, task_reader=None,
                 active_task=None, process_matches=None):
        self.state_root = Path(state_root).resolve()
        self.workspace = Path(workspace).resolve()
        self.directory = self.state_root / "autonomy" / "goals"
        self.watchers = {}
        self.processes = {}
        self.cancel_watchers = {}
        self.suspended_goals = {}
        self.closing = False
        self.registry, self.task_reader = registry, task_reader
        self.active_task, self.process_matches = active_task, process_matches
        self.completion_tickets = {}
        self.completion_validator = None

    def _dir(self, goal_id):
        if not isinstance(goal_id, str) or not ID.fullmatch(goal_id):
            raise ValueError("invalid autonomous goal ID")
        return self.directory / goal_id

    def _read(self, path, default=None):
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def _event(self, goal_id, event, **fields):
        with (self._dir(goal_id) / "host-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": event, "at": runtime.now(), **fields}) + "\n")

    def _lifecycle_event(self, goal_id, event, **fields):
        """Best-effort journal write; lifecycle logging cannot own the process."""
        try:
            self._event(goal_id, event, **fields)
        except OSError:
            pass

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
        for value in scope:
            path = (self.workspace / value).resolve()
            if path.is_relative_to(self.state_root) or self.state_root.is_relative_to(path):
                raise ValueError(
                    f"write path {value!r} and operational state root {str(self.state_root)!r} overlap; "
                    "choose explicit source paths outside the state root, or run the host against a "
                    "workspace whose state namespace lies outside it")
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
        try:
            state = self._read(directory / "state.json", {"status": "RECOVERING"})
        except (OSError, ValueError):
            # An unreadable state file must not make the goal unreportable:
            # the report is the only way the owner learns what happened.
            state = {"status": "RECOVERING"}
        if not isinstance(state, dict):
            state = {"status": "RECOVERING"}
        process = self.processes.get(goal_id)
        return {"goal_id": goal_id, "goal": spec["goal"], "state": state,
                "controller_running": bool(process and process[0].poll() is None),
                "spec_path": str(directory / "spec.json"), "state_dir": str(directory)}

    def list(self):
        if not self.directory.exists():
            return []
        return [self.get(path.name) for path in sorted(self.directory.iterdir())
                if path.is_dir() and ID.fullmatch(path.name) and (path / "spec.json").is_file()]

    def _controller_starts(self, goal_id):
        """Count recorded controller starts; None when the journal cannot be read.

        Only `controller_started` records count. A crash without a matching
        `controller_exited` record still counts as a start. The presence and
        content reads share one guarded edge, so a denied stat or read yields
        unknown metrics instead of aborting the ordinary report.
        """
        journal = self._dir(goal_id) / "host-events.jsonl"
        try:
            if not journal.exists():
                return 0
            lines = journal.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return 0
        except (OSError, ValueError):
            return None
        starts = 0
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                return None
            if not isinstance(record, dict) or not isinstance(record.get("event"), str):
                return None
            if record["event"] == "controller_started":
                starts += 1
        return starts

    def report(self, goal_id):
        record = self.get(goal_id)
        spec = self._read(self._dir(goal_id) / "spec.json")
        state = record["state"]
        starts = self._controller_starts(goal_id)
        status = state.get("status", "RECOVERING")
        actions = {"COMPLETE": "查看结果后，由你设置下一条 Goal。",
                   "RUNNING": "Agent 正在自主执行，无需手动救场。",
                   "RECOVERING": "Agent 正在自主诊断和恢复，无需手动重派。",
                   "NEEDS_USER": "处理报告中的已核实外部依赖后，调用 resume_goal。",
                   "CANCELED": "已按指令停止，可恢复同一 Goal 或设置新 Goal。",
                   "CANCELING": "正在清理本 Goal 的任务，系统会自动继续清理。"}
        supervision_lost = self._supervision_lost_state(goal_id, state)
        cancel_lost = bool(state.get("cancel_lost")) and status != "CANCELED"
        # `last_error` is a shared field also written by the controller and by
        # `resume()`, so it can name a stale or benign cause.  The loss has
        # its own reason field.
        loss_reason = state.get("supervision_lost_reason") if supervision_lost else None
        blocker = state.get("blocker") if status == "NEEDS_USER" else None
        if cancel_lost:
            # The cleanup stopped, so the goal is not being cleaned up and no
            # automatic continuation is happening.  Saying otherwise would be
            # the same deception the supervision loss fixed.
            status = "NEEDS_USER"
            actions["NEEDS_USER"] = ("本 Goal 的宿主清理已中断，Goal 停在 CANCELING。"
                                     "请先处理报告中的 cancel_lost 原因，再调用 resume_goal。")
            blocker = state.get("blocker") or {
                "kind": "host_cancel_lost",
                "message": ("The host cleanup for this goal stopped without "
                            "finishing; the goal is stuck in CANCELING."),
                "evidence": ([state["cancel_lost_reason"]] if state.get("cancel_lost_reason") else []),
            }
        if supervision_lost:
            status = "NEEDS_USER"
            suspended = bool(state.get("host_suspended") or goal_id in self.suspended_goals)
            actions["NEEDS_USER"] = (
                "控制器结果不确定，已暂停自动重放；请先核实外部结果。"
                if suspended else
                "本 Goal 的宿主监督已中断，Goal 未在自主执行。"
                "请先处理报告中的 supervision_lost 原因，再调用 resume_goal。")
            # The live watcher holds the exception that actually ended the
            # supervision, so it is the most direct cause available.  The
            # persisted reason is the fallback for the case where the durable
            # write failed, or where the loss was recorded for a watcher that
            # is no longer the goal's owner.
            live_reason = self._live_supervision_error(goal_id)
            if live_reason is not None:
                loss_reason = live_reason
            if blocker is None:
                if suspended:
                    blocker = {"kind": "host_outcome_uncertain",
                               "message": ("The controller may have performed external work; "
                                           "automatic replay is suspended to avoid duplication."),
                               "evidence": [loss_reason] if loss_reason else []}
                else:
                    blocker = {"kind": "host_supervision_lost",
                               "message": ("The host supervisor for this goal stopped without "
                                           "supervising it; the goal is not running autonomously."),
                               "evidence": [loss_reason] if loss_reason else []}
        return {"goal_id": goal_id, "goal": spec["goal"], "status": status,
                "summary": state.get("last_summary"), "acceptance": spec["acceptance"],
                "accepted_result": state.get("accepted_receipt"),
                "candidate": state.get("checked_candidate"),
                "recovery_count": state.get("recovery_count", 0),
                "host_restart_count": state.get("host_restart_count", 0),
                "controller_start_count": starts,
                "controller_restart_count": None if starts is None else max(0, starts - 1),
                "session_reset_count": len(state.get("previous_session_ids", [])),
                "blocker": blocker,
                "next_user_action": actions.get(status, "查看进度。"),
                "supervision_lost": supervision_lost,
                "supervision_lost_reason": loss_reason,
                "controller_running": record["controller_running"], "evidence_dir": str(self._dir(goal_id))}

    def _live_supervision_error(self, goal_id):
        """The sanitized cause of the current watcher's failure, if any.

        Used when the durable loss write failed, so the report can still name
        the cause instead of pointing the owner at an absent field.
        """
        watcher = self.watchers.get(goal_id)
        if watcher is None or not watcher.done() or watcher.cancelled():
            return None
        error = watcher.exception()
        if error is None:
            return None
        return runtime._safe_handoff(f"{type(error).__name__}: {error}")

    def _supervision_lost_state(self, goal_id, state):
        """True when the goal is not actually supervised right now.

        Derived from the live watcher task, not only from persisted state, so a
        report cannot claim autonomous execution after supervision died even if
        the durable state update failed too.
        """
        status = state.get("status")
        if status in ("COMPLETE", "CANCELED"):
            # The goal already reached its own outcome; a watcher that died
            # afterwards supervised nothing that still needed supervising, and
            # an accepted result must never be hidden behind a false blocker.
            return False
        if state.get("supervision_lost") or state.get("host_suspended"):
            return True
        if goal_id in self.suspended_goals:
            return True
        if status in TERMINAL:
            # The goal already stopped for its own reason.
            return False
        watcher = self.watchers.get(goal_id)
        if watcher is None or not watcher.done() or watcher.cancelled():
            return False
        return watcher.exception() is not None

    def _launch(self, goal_id):
        if goal_id not in self.watchers or self.watchers[goal_id].done():
            watcher = asyncio.create_task(self._watch(goal_id))
            self.watchers[goal_id] = watcher
            watcher.add_done_callback(
                lambda finished, goal_id=goal_id: self._record_supervision_loss(goal_id, finished))

    def _record_supervision_loss(self, goal_id, watcher):
        """Record that a goal's supervisor stopped without supervising anything.

        A watcher that finishes normally (terminal goal, explicit cancellation,
        host shutdown) is not a loss. A watcher that dies with an unhandled
        exception is: the goal would otherwise keep reporting RUNNING with
        nothing supervising it and nothing able to relaunch the controller.

        A loss that belongs to a watcher which has already been superseded is
        history, not the goal's current state: recording it would undo a
        resume that the owner just performed.
        """
        if self.closing or watcher.cancelled():
            return
        error = watcher.exception()
        if error is None:
            return
        if self.watchers.get(goal_id) is not watcher:
            # A newer watcher owns this goal now; this loss is already history.
            return
        directory = self._dir(goal_id)
        if (directory / "cancel.request").exists():
            return
        # This callback is the last thing that can record the loss, so it must
        # not itself die.  A corrupt or locked state file must not stop the
        # event and the durable update from being written.
        state = self._read_loss_state(directory)
        if state.get("status") in TERMINAL:
            return
        detail = runtime._safe_handoff(f"{type(error).__name__}: {error}")
        try:
            self._event(goal_id, "host_supervision_lost", error_type=type(error).__name__,
                        error=detail)
        except OSError:
            pass
        # The goal is no longer supervised. Say so durably instead of leaving
        # a RUNNING goal that claims autonomous progress nobody is delivering.
        # The update is MERGED into the on-disk state: a degraded read must
        # never be written back, or the goal's id and recovery count would be
        # destroyed along with the rest of its state.
        try:
            self._merge_state(directory, {
                "status": "NEEDS_USER", "supervision_lost": True,
                "supervision_lost_at": runtime.now(),
                "supervision_lost_reason": detail,
                "blocker": {
                    "kind": "host_supervision_lost",
                    "message": ("The host supervisor for this goal stopped without "
                                "supervising it; the goal is not running autonomously."),
                    "evidence": [detail],
                }})
        except OSError:
            pass

    def _read_loss_state(self, directory):
        """Read the goal's state for the loss callback, never raising.

        The loss callback is the only thing that can record that supervision
        ended, so a corrupt or locked state file must degrade to an empty
        state rather than kill the callback and lose the loss.

        The result is NOT safe to write back: a degraded read is empty, so
        writing it would replace the goal's real state with a five-field
        stub.  Callers must merge into the on-disk state instead.
        """
        try:
            state = self._read(directory / "state.json", {})
        except (OSError, ValueError):
            return {}
        return state if isinstance(state, dict) else {}

    def _merge_state(self, directory, changes, remove=()):
        """Merge changes into the goal's on-disk state, never dropping fields.

        A read-modify-write is used instead of writing the dict the caller
        happened to hold, because the caller's copy may be a degraded empty
        read: writing that back would destroy every field the read failed to
        return.

        `remove` names fields to delete, for the case where a merge must also
        clear a stale field rather than merely overwrite it.

        If the read itself fails, nothing is written.  A degraded read that
        is written back as a stub is worse than no durable update at all:
        the goal's id, recovery count and session history are exactly what
        the controller needs to make progress.  The caller keeps its event
        record, and the report still derives the loss from the live watcher.
        """
        path = directory / "state.json"
        try:
            current = self._read(path, {})
        except (OSError, ValueError):
            return None
        if not isinstance(current, dict):
            return None
        for field in remove:
            current.pop(field, None)
        current.update(changes)
        runtime.atomic_json(path, current)
        return current


    async def _watch(self, goal_id):
        directory = self._dir(goal_id)
        while not self.closing:
            job, proc = runtime.Job(), None
            try:
                state = self._read(directory / "state.json", {})
                if (directory / "cancel.request").exists() or state.get("status") in TERMINAL:
                    return
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
                    self.processes[goal_id] = (proc, job)
                    job.assign(proc)
                    process_record = {
                        "pid": proc.pid, "process_token": runtime.process_token(proc.pid)}
                    metadata_written = False
                    while proc.poll() is None and not metadata_written and not self.closing:
                        try:
                            runtime.atomic_json(directory / "process.json", process_record)
                            metadata_written = True
                        except OSError as exc:
                            self._lifecycle_event(
                                goal_id, "host_process_metadata_recovery",
                                error_type=type(exc).__name__)
                            await asyncio.sleep(.1)
                    # Continue supervising the same process even if it exits
                    # before metadata is published; proc.wait() and the
                    # terminal-state check below remain authoritative.
                    self._lifecycle_event(goal_id, "controller_started", pid=proc.pid)
                    code = await asyncio.to_thread(proc.wait)
                    self._lifecycle_event(goal_id, "controller_exited", exit_code=code)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # A transient host-side failure must not permanently orphan
                # this goal. Do not launch another controller until the
                # existing process boundary has been cleaned up and state can
                # be read again.
                try:
                    self._event(goal_id, "host_recovery", error_type=type(exc).__name__)
                except OSError:
                    pass
                if proc is not None:
                    # Once a controller may have run, its external effects
                    # are uncertain. Do not replay it automatically. Mark the
                    # same goal suspended; returning normally would make the
                    # report claim autonomous progress with no watcher.
                    detail = runtime._safe_handoff(f"{type(exc).__name__}: {exc}")
                    self.suspended_goals[goal_id] = detail
                    while not self.closing:
                        try:
                            merged = self._merge_state(directory, {
                                "status": "NEEDS_USER", "host_suspended": True,
                                "host_suspended_at": runtime.now(),
                                "host_suspended_reason": detail,
                                "blocker": {
                                    "kind": "host_outcome_uncertain",
                                    "message": ("The controller may have performed external work; "
                                                "automatic replay is suspended to avoid duplication."),
                                    "evidence": [detail],
                                }})
                            if merged is None:
                                raise OSError("goal state unreadable while recording uncertain outcome")
                            break
                        except OSError:
                            await asyncio.sleep(.2)
                    return
            finally:
                try:
                    job.close()
                except Exception as exc:
                    self._lifecycle_event(goal_id, "host_job_close_recovery",
                                          error_type=type(exc).__name__)
                if proc is not None and proc.poll() is not None:
                    self.processes.pop(goal_id, None)
            while True:
                if self.closing or (directory / "cancel.request").exists():
                    return
                try:
                    current = self._read(directory / "state.json", {})
                    if current.get("status") in TERMINAL:
                        return
                    current.update(status="RECOVERING",
                                   host_restart_count=current.get("host_restart_count", 0) + 1)
                    runtime.atomic_json(directory / "state.json", current)
                    break
                except OSError as exc:
                    if isinstance(exc, PermissionError) and getattr(exc, "winerror", None) not in (5, 32, 33):
                        raise
                    try:
                        fields = ({"winerror": exc.winerror} if isinstance(exc, PermissionError)
                                  and getattr(exc, "winerror", None) is not None
                                  else {"error_type": type(exc).__name__})
                        self._event(goal_id, "host_snapshot_recovery", **fields)
                    except OSError:
                        pass
                    await asyncio.sleep(.2)
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
            try:
                stack = self._read(path)
            except (OSError, ValueError):
                # A stack file that cannot be read must not end the cleanup:
                # the goal would stay in CANCELING forever with no way out.
                unresolved.append(f"unreadable_stack:{path.parent.name}")
                continue
            if not isinstance(stack, dict) or stack.get("goal_id") != goal_id:
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
            watcher = asyncio.create_task(self._finish_cancel(goal_id))
            self.cancel_watchers[goal_id] = watcher
            watcher.add_done_callback(
                lambda finished, goal_id=goal_id: self._record_cancel_loss(goal_id, finished))

    async def _terminate_controller(self, goal_id):
        """Keep ownership and retry until the registered controller is exited."""
        while not self.closing:
            registered = self.processes.get(goal_id)
            if registered is None:
                return True
            proc, job = registered
            try:
                if proc.poll() is not None:
                    try:
                        job.close()
                    except Exception:
                        pass
                    self.processes.pop(goal_id, None)
                    return True
                try:
                    job.close()
                except Exception:
                    pass
                if proc.poll() is None:
                    proc.kill()
                await asyncio.to_thread(proc.wait)
                if proc.poll() is not None:
                    self.processes.pop(goal_id, None)
                    return True
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                try:
                    self._event(goal_id, "host_process_termination_recovery",
                                error_type=type(exc).__name__)
                except OSError:
                    pass
            await asyncio.sleep(.2)
        return False

    def _record_cancel_loss(self, goal_id, watcher):
        """Record that a goal's cleanup watcher stopped without cleaning up.

        The same defect class as the supervision watcher: a background task
        whose exception is never observed ends the cleanup with no trace,
        leaving the goal stuck in CANCELING with the report promising an
        automatic continuation that has already stopped.
        """
        if self.closing or watcher.cancelled():
            return
        error = watcher.exception()
        if error is None:
            return
        if self.cancel_watchers.get(goal_id) is not watcher:
            return
        directory = self._dir(goal_id)
        detail = runtime._safe_handoff(f"{type(error).__name__}: {error}")
        try:
            self._event(goal_id, "host_cancel_lost", error_type=type(error).__name__,
                        error=detail)
        except OSError:
            pass
        try:
            state = self._read_loss_state(directory)
            if state.get("status") in ("COMPLETE", "CANCELED"):
                return
            self._merge_state(directory, {
                "status": "NEEDS_USER", "cancel_lost": True,
                "cancel_lost_at": runtime.now(), "cancel_lost_reason": detail,
                "blocker": {
                    "kind": "host_cancel_lost",
                    "message": ("The host cleanup for this goal stopped without "
                                "finishing; the goal is stuck in CANCELING."),
                    "evidence": [detail],
                }})
        except OSError:
            pass

    async def _finish_cancel(self, goal_id):
        while not self.closing:
            try:
                # Publish the canceling state under the already-installed
                # cleanup owner. A transient read/write error must not escape
                # the initial cancel() call and orphan durable cancel intent.
                state = self._merge_state(self._dir(goal_id), {"status": "CANCELING"})
                if state is None:
                    raise OSError("goal state unavailable while publishing cancellation")
                if not await self._terminate_controller(goal_id):
                    return
                unresolved = await self._cancel_owned_tasks(goal_id)
                # MERGED, not written from the dict that was read: a degraded read
                # must never be written back, or the cleanup would destroy the
                # goal's id and recovery count on its way to the terminal state.
                merged = self._merge_state(self._dir(goal_id), {
                    "status": "CANCELING" if unresolved else "CANCELED",
                    "unresolved_task_ids": unresolved})
                if merged is None:
                    raise OSError("goal state is unreadable; cancellation remains pending")
                if not unresolved:
                    return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                try:
                    self._event(goal_id, "host_cancel_recovery", error_type=type(exc).__name__)
                except OSError:
                    pass
            await asyncio.sleep(1)

    async def cancel(self, goal_id):
        record = self.get(goal_id)
        if record["state"].get("status") == "COMPLETE":
            return record
        directory = self._dir(goal_id)
        (directory / "cancel.request").write_text("explicit controller cancellation\n", encoding="utf-8")
        process = self.processes.get(goal_id)
        watcher = self.watchers.get(goal_id)
        # Install the retry owner before any fallible task query or state
        # publication. The cancel.request is durable intent and startup also
        # restores this owner after a host restart.
        self._launch_cancel(goal_id)
        if process:
            try:
                process[1].close()
            except Exception as exc:
                try:
                    self._event(goal_id, "host_job_close_recovery",
                                error_type=type(exc).__name__)
                except OSError:
                    pass
        if watcher and not watcher.done():
            watcher.cancel()
        return self.get(goal_id)

    async def resume(self, goal_id):
        record = self.get(goal_id)
        if record["controller_running"] or record["state"].get("status") == "COMPLETE":
            return record
        if record["state"].get("status") == "CANCELING":
            # A cleanup that is still running must be waited out.  A cleanup
            # that DIED is not still recovering: refusing the resume there
            # would leave the owner with no operation that works at all.
            if not record["state"].get("cancel_lost"):
                raise ValueError("Owned task cancellation is still recovering; resume after it finishes")
        directory = self._dir(goal_id)
        # The stale-loss fields are REMOVED, not just overwritten, so the
        # update is a merge with explicit deletions rather than a merge with
        # additions.  The state is read from the FILE again rather than from
        # the report's copy, because the report degrades to a stub when the
        # file cannot be read, and writing that stub back would destroy the
        # goal's id and recovery count.
        merged = self._merge_state(directory, {
            "status": "RUNNING",
            "last_error": ("Controller explicitly resumed this same goal; "
                           "re-check current evidence.")},
            remove=("supervision_lost", "supervision_lost_at",
                    "supervision_lost_reason", "cancel_lost",
                    "cancel_lost_at", "cancel_lost_reason", "host_suspended",
                    "host_suspended_at", "host_suspended_reason", "blocker"))
        if merged is None:
            # The state file could not be read, so it cannot be updated
            # without risking a truncation.  The goal stays as it was and the
            # owner is told, rather than being handed a stubbed goal.
            raise ValueError("Goal state could not be read; resume the goal again "
                             "once its state file is readable")
        (directory / "cancel.request").unlink(missing_ok=True)
        self.suspended_goals.pop(goal_id, None)
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

    async def _producer_facts(self, goal_id, review=None):
        if self.registry is None or self.task_reader is None or self.active_task is None:
            raise ValueError("Host productive-boundary wiring is unavailable; completion refused")
        with self.registry.boundary_lock:
            generation = self.registry.goal_generation(goal_id)["generation"]
            records = self.registry.goal_assignments(goal_id)
        facts = {}
        references = [(r["stack"]["stack_id"], r["assignment"]["role_id"], r["assignment"].get("task_id"))
                      for r in records if r["profile"] == "coder" and r["assignment"].get("task_id")]
        if review:
            references.append((review["stack_id"], review["role_id"], review["task_id"]))
        for reference in references:
            try:
                facts[reference] = await self.task_reader(*reference)
            except Exception:
                facts[reference] = {"id": reference[2], "status": {"state": "UNKNOWN"}}
        return generation, records, facts

    def _productive_quiescence(self, goal_id, generation, records, facts):
        # Entire function and final publish are synchronous under the SAME
        # registry lock as productive binding. No await crosses this boundary.
        if self.closing:
            return {"status": "wait", "reason": "Host is closing; retry after recovery"}
        self.registry.goal_active(goal_id)
        if self.registry.goal_generation(goal_id)["generation"] != generation:
            return {"status": "wait", "reason": "Producer admission changed during observation; retry current facts"}
        for record in records:
            assignment = record["assignment"]
            task_id = assignment.get("task_id")
            if record["profile"] != "coder" or not task_id:
                continue
            key = (record["stack"]["stack_id"], assignment["role_id"], task_id)
            if self.active_task(*key):
                return {"status": "wait", "reason": "Productive executor is queued or running", "task_id": task_id}
            path = self.state_root / "tasks" / task_id / "process.json"
            process = self._read(path, {})
            if process:
                if self.process_matches is None:
                    return {"status": "refresh", "reason": "Native identity reader unavailable; reconcile task"}
                if (type(process.get("pid")) is not int or not 0 < process["pid"] <= 0xffffffff
                        or not isinstance(process.get("process_token"), str)
                        or not re.fullmatch(r"[0-9a-f]{16}", process["process_token"])):
                    return {"status": "refresh", "reason": "Malformed native identity; reconcile original task"}
                if self.process_matches(process.get("pid"), process.get("process_token")):
                    return {"status": "wait", "reason": "Protocol terminal state still has a live native identity", "task_id": task_id}
            task = facts.get(key)
            if task is None:
                # A bound task lost before protocol persistence cannot later run
                # in this recovered host: no executor or native identity exists.
                # Preserve binding and write a separate truthful recovery receipt.
                runtime.atomic_json(self.state_root / "tasks" / task_id / "admission-recovery.json", {
                    "task_id": task_id, "reason": "no_protocol_task_executor_or_native_identity"})
                continue
            state = task.get("status", {}).get("state", "").upper()
            if state == "UNKNOWN":
                return {"status": "wait", "reason": "Protocol state unavailable; retry original task observation"}
            if state in ("SUBMITTED", "WORKING", "TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"):
                return {"status": "wait", "reason": "Productive task is pending; reconcile original task", "task_id": task_id}
            if state not in ("COMPLETED", "FAILED", "CANCELED", "REJECTED", "TASK_STATE_COMPLETED",
                             "TASK_STATE_FAILED", "TASK_STATE_CANCELED", "TASK_STATE_REJECTED"):
                return {"status": "refresh", "reason": "Productive task needs reconciliation", "task_id": task_id}
        return None

    async def freeze_quiescent(self, goal_id, files):
        generation, records, facts = await self._producer_facts(goal_id)
        with self.registry.boundary_lock:
            pending = self._productive_quiescence(goal_id, generation, records, facts)
            if pending:
                raise ValueError(pending["reason"] + "; retry freeze after original productive work finishes")
            frozen = self.freeze(goal_id, files)
            frozen["producer_epoch"] = self.registry.stamp_candidate(goal_id, frozen["candidate"])
            return frozen

    async def completion(self, goal_id, payload):
        existing = self._read(self._dir(goal_id) / "state.json", {})
        if existing.get("status") == "COMPLETE":
            receipt = existing.get("accepted_receipt", {})
            if payload.get("operation") == "commit" and receipt.get("completion_ticket") == payload.get("ticket"):
                return {"status": "complete", "state": existing}
            return {"status": "refresh", "reason": "Goal already complete; do not admit more work"}
        proposal = payload.get("proposal", {})
        reference = proposal.get("review")
        if not isinstance(reference, dict) or set(reference) != {"stack_id", "role_id", "task_id"}:
            raise ValueError("Actual review reference is required")
        generation, records, facts = await self._producer_facts(goal_id, reference)
        if self.completion_validator is None:
            helper_spec = importlib.util.spec_from_file_location("host_completion_validation", STACK / "autonomy/runner.py")
            self.completion_validator = importlib.util.module_from_spec(helper_spec)
            helper_spec.loader.exec_module(self.completion_validator)
        helper = self.completion_validator
        with self.registry.boundary_lock:
            pending = self._productive_quiescence(goal_id, generation, records, facts)
            if pending:
                return pending
            directory = self._dir(goal_id)
            spec = self._read(directory / "spec.json")
            manifest = helper.freeze_current(spec, directory, proposal.get("candidate_manifest"))
            epoch = self.registry.goal_generation(goal_id)
            stamp = epoch.get("freeze", {})
            review_assignment = next((r["assignment"] for r in records if
                r["stack"]["stack_id"] == reference["stack_id"] and r["assignment"].get("role_id") == reference["role_id"]
                and r["assignment"].get("task_id") == reference["task_id"]), {})
            if (stamp.get("candidate") != manifest["candidate"] or stamp.get("generation") != generation
                    or review_assignment.get("freeze_id") != stamp.get("id")
                    or review_assignment.get("producer_generation") != generation):
                return {"status": "refresh", "reason": "Fresh quiescent freeze and independent review required for current producer generation"}
            stack = self.registry.get_stack(reference["stack_id"])
            stack["all_goal_producers"] = [{"stack_id": r["stack"]["stack_id"], "goal_id": goal_id,
                "profile": "coder", "role_id": r["assignment"]["role_id"], "task_id": r["assignment"]["task_id"],
                "task": facts.get((r["stack"]["stack_id"], r["assignment"]["role_id"], r["assignment"]["task_id"])) or
                        {"id": r["assignment"]["task_id"], "status": {"state": "FAILED"}}}
                for r in records if r["profile"] == "coder" and r["assignment"].get("task_id")]
            review = facts.get((reference["stack_id"], reference["role_id"], reference["task_id"]))
            receipt = helper.validate_review(spec, reference, manifest, review or {}, stack)
            proof = {"generation": generation, "freeze_id": stamp["id"], "candidate": manifest["candidate"], "review": reference}
            if payload.get("operation") == "prepare":
                ticket = uuid.uuid4().hex
                self.completion_tickets[ticket] = proof
                return {"status": "ready", "ticket": ticket, **proof}
            if payload.get("operation") != "commit" or self.completion_tickets.get(payload.get("ticket")) != proof:
                return {"status": "refresh", "reason": "Prepared evidence changed or host restarted; repeat current checks/review"}
            checks = self._read(directory / "checks.json", [])
            if (checks != payload.get("checks") or [c.get("id") for c in checks] != [c["id"] for c in spec["checks"]]
                    or any(type(c.get("exit_code")) is not int or c["exit_code"] != 0 for c in checks)):
                raise ValueError("Actual immutable full check receipt is missing or failing")
            # Writer admission cannot interleave between this final fact/hash
            # check, draft retirement and durable COMPLETE publication.
            self.registry.retire_drafts(goal_id)
            state = self._read(directory / "state.json", {})
            state.update(status="COMPLETE", accepted_receipt={**receipt, **proof, "checks": checks,
                "completion_ticket": payload["ticket"]}, last_error=None, updated_at=runtime.now())
            runtime.atomic_json(directory / "state.json", state)
            self.completion_tickets.pop(payload["ticket"], None)
            return {"status": "complete", "state": state}

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
                return JSONResponse(await self.freeze_quiescent(goal_id, (await request.json()).get("files")))
            if operation == "complete":
                return JSONResponse(await self.completion(goal_id, await request.json()))
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
                Route("/control/goals/{goal_id}/candidate", self._api, methods=["POST"]),
                Route("/control/goals/{goal_id}/complete", self._api, methods=["POST"])]
