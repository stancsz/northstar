"""Local A2A service that runs registered Claude Code jobs.

Endpoints (loopback only):
    GET  http://127.0.0.1:18890/.well-known/agent-card.json
    POST http://127.0.0.1:18890/a2a/jsonrpc

Trust model:
    The HTTP surface may only *name* a job.  The job definition itself lives in
    tmp/a2a-stack/jobs/<name>.json and is written by a trusted local owner.  A
    request can never supply a prompt, a shell command, an executable path or
    CLI flags.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

STACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(os.environ.get("A2A_WORKSPACE", STACK_ROOT.parent)).resolve()
STATE_ROOT = STACK_ROOT.parent / "tmp" / "a2a-stack"
RUNTIME_DIR = STACK_ROOT / "runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))
if str(STACK_ROOT) not in sys.path:
    sys.path.insert(0, str(STACK_ROOT))

import runner  # noqa: E402  existing lifecycle helper (Windows Job object, abort helpers)

from a2a.server.agent_execution import AgentExecutor, RequestContext  # noqa: E402
from a2a.server.request_handlers import DefaultRequestHandler  # noqa: E402
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes  # noqa: E402
from a2a.types import (  # noqa: E402
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Part,
    Task,
    TaskState,
    TaskStatus,
)

try:  # import layout differs slightly between SDK releases
    from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
except ImportError:  # pragma: no cover
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.server.tasks.task_updater import TaskUpdater

try:
    from a2a.server.events import EventQueue
except ImportError:  # pragma: no cover
    from a2a.server.events.event_queue import EventQueue

HOST = "127.0.0.1"
PORT = 18890
RPC_URL = "/a2a/jsonrpc"
CARD_URL = "/.well-known/agent-card.json"

JOBS_DIR = STATE_ROOT / "jobs"
TASKS_DIR = STATE_ROOT / "tasks"
LOCK_PATH = STATE_ROOT / "control" / "owner.lock"

JOB_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
PERMISSION_MODES = {"default", "acceptEdits", "plan"}

# CREATE_SUSPENDED (0x4) so the child can be attached to a Job object before it runs.
CREATION_FLAGS = 0x4 | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP


class JobRejected(Exception):
    """The request itself is not acceptable."""


class JobFailed(Exception):
    """The job could not be executed."""


# --------------------------------------------------------------------------- #
# Project owner lock
# --------------------------------------------------------------------------- #
class OwnerLock:
    """Exclusive OS lock over the project owner file, held for the whole lifetime."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fh = None

    def acquire(self) -> None:
        import msvcrt

        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "a+b")
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write(b"\0")
            fh.flush()
        fh.seek(0)
        try:
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            fh.close()
            raise SystemExit(
                f"another owner already holds {self.path}; refusing to start a second service"
            )
        self._fh = fh

    def release(self) -> None:
        if self._fh is None:
            return
        import msvcrt

        try:
            self._fh.seek(0)
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        finally:
            self._fh.close()
            self._fh = None


# --------------------------------------------------------------------------- #
# Job registry
# --------------------------------------------------------------------------- #
def _under_repo(relative: str) -> Path:
    candidate = (REPO_ROOT / relative).resolve()
    root = REPO_ROOT.resolve()
    if candidate != root and root not in candidate.parents:
        raise JobFailed(f"path '{relative}' escapes the repository")
    return candidate


def job_file(name: str) -> Path:
    if not isinstance(name, str) or not JOB_NAME_RE.match(name) or ".." in name:
        raise JobRejected("job name must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    return JOBS_DIR / f"{name}.json"


def validate_job(data: Any, name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise JobFailed(f"job '{name}' must be a JSON object")

    mode = data.get("mode")
    if mode not in ("claude", "check"):
        raise JobFailed(f"job '{name}' has unsupported mode {mode!r}")

    timeout = data.get("timeout_seconds")
    if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1):
        raise JobFailed(f"job '{name}' timeout_seconds must be a positive int when explicitly set")

    cwd = data.get("cwd", ".")
    if not isinstance(cwd, str):
        raise JobFailed(f"job '{name}' cwd must be a string")
    workdir = _under_repo(cwd)

    config: dict[str, Any] = {
        "name": name,
        "mode": mode,
        "timeout_seconds": timeout,
        "cwd": workdir,
    }

    if mode == "claude":
        prompt_file = data.get("prompt_file")
        if not isinstance(prompt_file, str) or not prompt_file:
            raise JobFailed(f"job '{name}' requires prompt_file")
        prompt_path = _under_repo(prompt_file)
        if not prompt_path.is_file():
            raise JobFailed(f"job '{name}' prompt_file '{prompt_file}' does not exist")
        config["prompt_path"] = prompt_path

        max_turns = data.get("max_turns")
        if max_turns is not None and (isinstance(max_turns, bool) or not isinstance(max_turns, int) or max_turns < 1):
            raise JobFailed(f"job '{name}' max_turns must be a positive int when explicitly set")
        config["max_turns"] = max_turns

        tools = data.get("tools", [])
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            raise JobFailed(f"job '{name}' tools must be a list of strings")
        config["tools"] = tools

        mcp_config = data.get("mcp_config")
        if mcp_config is not None:
            if not isinstance(mcp_config, str) or not mcp_config:
                raise JobFailed(f"job '{name}' mcp_config must be a string path")
            mcp_path = _under_repo(mcp_config)
            if not mcp_path.is_file():
                raise JobFailed(f"job '{name}' mcp_config '{mcp_config}' does not exist")
            config["mcp_config"] = mcp_path

        allowed_tools = data.get("allowed_tools")
        if allowed_tools is None:
            allowed_tools = tools
        if not isinstance(allowed_tools, list) or not all(isinstance(t, str) for t in allowed_tools):
            raise JobFailed(f"job '{name}' allowed_tools must be a list of strings")
        config["allowed_tools"] = allowed_tools

        permission_mode = data.get("permission_mode", "acceptEdits")
        if permission_mode not in PERMISSION_MODES:
            raise JobFailed(f"job '{name}' permission_mode must be one of {sorted(PERMISSION_MODES)}")
        config["permission_mode"] = permission_mode
    else:
        command = data.get("command")
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) for part in command)
        ):
            raise JobFailed(f"job '{name}' requires a non-empty command argv list")
        config["command"] = command

    return config


def load_job(name: str) -> dict[str, Any]:
    path = job_file(name)
    if not path.is_file():
        raise JobFailed(f"unknown job '{name}'")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise JobFailed(f"job '{name}' is not valid JSON: {exc.msg}") from exc
    return validate_job(data, name)


# --------------------------------------------------------------------------- #
# Claude executable resolution
# --------------------------------------------------------------------------- #
def resolve_claude_exe() -> str:
    return runner.claude_executable()


# --------------------------------------------------------------------------- #
# Process helpers
# --------------------------------------------------------------------------- #
def _resume_process(proc: subprocess.Popen) -> None:
    ntdll = ctypes.windll.ntdll
    ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = ntdll.NtResumeProcess(proc._handle)
    if status != 0:
        raise RuntimeError(f"NtResumeProcess failed with status {status}")


def _new_job_object():
    job_cls = getattr(runner, "Job", None)
    if job_cls is None:
        raise RuntimeError("runner.Job is unavailable")
    return job_cls()


def _assign_to_job(job: Any, proc: subprocess.Popen) -> None:
    job.assign(proc)


def _build_claude_argv(config: dict[str, Any]) -> list[str]:
    executable = resolve_claude_exe()
    argv = [
        executable,
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        config["permission_mode"],
    ]
    if config["max_turns"] is not None:
        argv += ["--max-turns", str(config["max_turns"])]
    argv += ["--tools", ",".join(config["tools"])]
    allowed_tools = config.get("allowed_tools", config["tools"])
    if allowed_tools:
        argv += ["--allowedTools", ",".join(allowed_tools)]
    if config.get("mcp_config") is not None:
        argv += ["--mcp-config", str(config["mcp_config"]), "--strict-mcp-config"]
    return argv


def _parse_claude_stream(lines: list[str]) -> tuple[str | None, str | None]:
    """Return (result_text, error_reason) from Claude Code streaming JSON events."""
    result_text: str | None = None
    error_reason: str | None = None
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        if event_type == "result":
            subtype = event.get("subtype")
            if event.get("is_error"):
                error_reason = str(event.get("result") or subtype or "claude reported an error")
            elif subtype and subtype != "success":
                error_reason = f"claude ended with result subtype '{subtype}'"
            else:
                value = event.get("result")
                result_text = value if isinstance(value, str) else json.dumps(value)
        elif event_type in ("error", "system_error") or event.get("is_error"):
            error_reason = str(event.get("message") or event.get("error") or event_type)
    return result_text, error_reason


# --------------------------------------------------------------------------- #
# Executor
# --------------------------------------------------------------------------- #
class _ActiveJob:
    def __init__(self) -> None:
        self.proc: subprocess.Popen | None = None
        self.job: Any = None
        self.job_object_assigned = False


class RegisteredJobExecutor(AgentExecutor):
    """Runs one registered job at a time; every job gets its own process tree."""

    def __init__(self, job_loader=None, semaphore=None) -> None:
        self._job_loader = job_loader or (lambda name, task_id: load_job(name))
        self._semaphore = semaphore if semaphore is not None else asyncio.Semaphore(1)
        self._active: dict[str, _ActiveJob] = {}

    # -- request parsing ---------------------------------------------------- #
    @staticmethod
    def _parse_request(context: RequestContext) -> str:
        text = context.get_user_input()
        if not isinstance(text, str) or not text.strip():
            raise JobRejected("request body must be JSON: {\"job\": \"<registered-job-name>\"}")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise JobRejected(f"request body must be JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise JobRejected('request body must be a JSON object such as {"job": "demo"}')
        name = payload.get("job")
        if not isinstance(name, str) or not name.strip():
            raise JobRejected('request body must contain a "job" name')
        return name.strip()

    # -- process lifecycle --------------------------------------------------- #
    async def _wait_for_exit(self, entry: _ActiveJob) -> int | None:
        """Wait for the process to actually exit, absorbing further cancellations."""
        proc = entry.proc
        if proc is None:
            return None
        while True:
            code = proc.poll()
            if code is not None:
                return code
            try:
                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                continue

    async def _terminate(self, entry: _ActiveJob) -> int | None:
        """Kill only this task's process tree and wait for its real exit."""
        proc = entry.proc
        if proc is None:
            return None
        if entry.job is not None:
            try:
                entry.job.close()
            except Exception:
                pass
            entry.job = None
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
        return await self._wait_for_exit(entry)

    # -- execution ----------------------------------------------------------- #
    async def _run_job(self, config, entry, updater):
        task_dir = TASKS_DIR / str(updater.task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        is_claude = config["mode"] == "claude"
        argv = _build_claude_argv(config) if is_claude else list(config["command"])
        stdin_text = config["prompt_path"].read_text(encoding="utf-8") if is_claude else ""
        env = dict(os.environ, PYTHONIOENCODING="utf-8", CLAUDE_CODE_RETRY_WATCHDOG="1")
        entry.job = runner.Job()
        result_event = None
        stderr_lines = 0
        completed = False
        try:
            entry.proc = subprocess.Popen(
                argv, cwd=config["cwd"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=CREATION_FLAGS, env=env)
            proc = entry.proc
            entry.job.assign(proc)
            runner.atomic_json(task_dir / "process.json", {
                "pid": proc.pid, "process_token": runner.process_token(proc.pid),
                "mode": config["mode"], "job": config["name"]})
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue()

            def pump(pipe, channel):
                try:
                    for raw in iter(pipe.readline, b""):
                        loop.call_soon_threadsafe(queue.put_nowait,
                            (channel, raw.decode("utf-8", "replace").rstrip("\r\n")))
                finally:
                    pipe.close()
                    loop.call_soon_threadsafe(queue.put_nowait, (channel, None))

            def feed():
                try:
                    proc.stdin.write(stdin_text.encode("utf-8"))
                    proc.stdin.flush()
                except (OSError, ValueError):
                    pass
                finally:
                    proc.stdin.close()

            for pipe, channel in ((proc.stdout, "stdout"), (proc.stderr, "stderr")):
                threading.Thread(target=pump, args=(pipe, channel), daemon=True).start()
            threading.Thread(target=feed, daemon=True).start()
            deadline = (time.monotonic() + config["timeout_seconds"]) if config["timeout_seconds"] is not None else None
            done = set()
            text = []
            result_event = None
            stderr_lines = 0
            with (task_dir / "events.jsonl").open("w", encoding="utf-8") as log:
                while len(done) < 2 or proc.poll() is None:
                    remaining = (deadline - time.monotonic()) if deadline is not None else .2
                    if remaining <= 0:
                        raise JobFailed(f"job timed out after {config['timeout_seconds']}s")
                    try:
                        channel, line = await asyncio.wait_for(queue.get(), min(.2, remaining))
                    except asyncio.TimeoutError:
                        continue
                    if line is None:
                        done.add(channel)
                        continue
                    if channel == "stderr":
                        stderr_lines += 1
                        continue
                    if is_claude:
                        safe = runner.sanitized_event(line)
                        if safe:
                            log.write(json.dumps(safe) + "\n")
                            log.flush()
                        reason = runner.structured_abort(line)
                        if reason:
                            raise JobFailed(f"Claude stopped on native terminal error: {reason}")
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if isinstance(event, dict) and event.get("type") == "result":
                            result_event = event
                    else:
                        if sum(map(len, text)) + len(line) > 64000:
                            raise JobFailed("check output exceeds 64000 characters")
                        text.append(line)
            code = await self._wait_for_exit(entry)
            if code != 0:
                raise JobFailed(f"process exited with code {code}; stderr body omitted")
            if is_claude:
                if not result_event or result_event.get("is_error") is not False or result_event.get("subtype") != "success":
                    raise JobFailed("Claude did not return a successful result event")
                result = result_event.get("result")
                if not isinstance(result, str) or not result:
                    raise JobFailed("Claude returned no result text")
                completed = True
                return True, runner._safe_handoff(result)
            completed = True
            return True, "\n".join(text)
        finally:
            code = await self._terminate(entry)
            runner.atomic_json(task_dir / "receipt.json", {
                "exit_code": code, "completed": completed,
                "stderr_lines": stderr_lines, "stderr_content": "omitted",
                "result_subtype": result_event.get("subtype") if result_event else None,
            })

    # -- AgentExecutor surface ---------------------------------------------- #
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        updater = TaskUpdater(event_queue, task_id, context_id)
        entry = _ActiveJob()
        self._active[task_id] = entry
        terminal_state = "TASK_STATE_FAILED"

        await event_queue.enqueue_event(
            Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                history=[context.message],
            )
        )

        try:
            try:
                name = self._parse_request(context)
                config = self._job_loader(name, task_id)
            except JobRejected as exc:
                await updater.reject(
                    message=updater.new_agent_message([Part(text=str(exc))])
                )
                terminal_state = "TASK_STATE_REJECTED"
                return
            except JobFailed as exc:
                await updater.failed(
                    message=updater.new_agent_message([Part(text=str(exc))])
                )
                return

            await self._semaphore.acquire()
            try:
                await updater.start_work()
                ok, text = await self._run_job(config, entry, updater)
            finally:
                self._semaphore.release()

            if ok:
                await updater.add_artifact(
                    parts=[Part(text=text)], name="result", last_chunk=True
                )
                await updater.complete()
                terminal_state = "TASK_STATE_COMPLETED"
            else:
                await updater.failed(
                    message=updater.new_agent_message([Part(text="job did not succeed")])
                )
        except JobFailed as exc:
            await updater.failed(
                message=updater.new_agent_message([Part(text=str(exc))])
            )
        except asyncio.CancelledError:
            terminal_state = "TASK_STATE_CANCELED"
            await self._terminate(entry)
            try:
                await updater.cancel()
            except Exception:
                pass
            raise
        finally:
            self._active.pop(task_id, None)
            runner.atomic_json(TASKS_DIR / str(task_id) / "terminal.json", {
                "task_id": task_id, "state": terminal_state,
                "finished_at": runner.now(),
            })

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        entry = self._active.get(context.task_id)
        if entry is None:
            return
        await self._terminate(entry)


# --------------------------------------------------------------------------- #
# App assembly
# --------------------------------------------------------------------------- #
def build_agent_card() -> AgentCard:
    return AgentCard(
        name="northstar-claude-code",
        description="Runs trusted, locally registered Claude Code jobs over the A2A protocol.",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="registered-jobs",
                name="Registered jobs",
                description="Execute a trusted local job by name and return its final result.",
                tags=["coding"],
            )
        ],
        supported_interfaces=[
            AgentInterface(
                url=f"http://{HOST}:{PORT}{RPC_URL}",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
    )


def build_app(executor: AgentExecutor | None = None):
    from starlette.applications import Starlette
    from stacks import StackManager
    from task_store import create_task_store
    from autonomy.manager import GoalManager

    card = build_agent_card()
    root_executor = executor or RegisteredJobExecutor()
    root_store = create_task_store(STATE_ROOT, "legacy-root")
    stores = [root_store]
    handler = DefaultRequestHandler(
        agent_executor=root_executor,
        task_store=root_store,
        agent_card=card,
    )
    routes = [
        *create_agent_card_routes(card),
        *create_jsonrpc_routes(handler, rpc_url=RPC_URL),
    ]

    def role_app_factory(stack, role, loader):
        def scoped_loader(name, task_id):
            try:
                return loader(name, task_id)
            except (ValueError, KeyError, OSError) as exc:
                raise JobRejected(str(exc)) from exc

        role_executor = RegisteredJobExecutor(
            job_loader=scoped_loader,
            semaphore=(getattr(root_executor, "_semaphore", None) if role["profile"] == "coder" else None),
        )
        role_card = build_agent_card()
        role_card.name = f"northstar/{stack['stack_id']}/{role['id']}/{role['profile']}"
        role_card.description = (
            "Trusted goal-check executor in a main-agent selected A2A stack."
            if role["profile"] == "verifier" else
            f"Independent {role['profile']} context in a main-agent selected A2A stack."
        )
        role_card.skills[0].id = role["profile"]
        role_card.skills[0].name = f"{role['profile']} assignments"
        role_card.skills[0].description = (
            "Run immutable owner-registered checks and report actual exit codes."
            if role["profile"] == "verifier" else
            f"Execute one scoped {role['profile']} assignment in a separate Claude Code context."
        )
        role_card.skills[0].ClearField("tags")
        role_card.skills[0].tags.append(role["profile"])
        role_card.supported_interfaces[0].url = role["agent_url"] + RPC_URL
        role_store = create_task_store(STATE_ROOT, f"stack:{stack['stack_id']}:role:{role['id']}")
        stores.append(role_store)
        role_handler = DefaultRequestHandler(
            agent_executor=role_executor,
            task_store=role_store,
            agent_card=role_card,
        )
        return Starlette(routes=[
            *create_agent_card_routes(role_card),
            *create_jsonrpc_routes(role_handler, rpc_url=RPC_URL),
        ])

    manager = StackManager(STATE_ROOT, REPO_ROOT, role_app_factory)
    goals = GoalManager(STATE_ROOT, REPO_ROOT)

    @asynccontextmanager
    async def lifespan(_app):
        await goals.startup()
        try:
            yield
        finally:
            await goals.close()
            for store in stores:
                await store.close()

    app = Starlette(routes=[*routes, *manager.routes(), *goals.routes()], lifespan=lifespan)
    app.state.stack_manager = manager
    app.state.goal_manager = goals
    return app, card


def main() -> None:
    # pythonw (per-user Scheduled Task) has no console streams. Uvicorn's
    # logging formatters still need a writable stream with isatty().
    if sys.stdout is None or sys.stderr is None:
        log_path = STATE_ROOT / "control" / "host-service.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        background_log = log_path.open("a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = background_log
        if sys.stderr is None:
            sys.stderr = background_log
    import uvicorn

    lock = OwnerLock(LOCK_PATH)
    lock.acquire()
    app, _card = build_app()
    print(
        f"a2a service pid={os.getpid()} listening on http://{HOST}:{PORT}{RPC_URL} "
        f"(agent card {CARD_URL})",
        flush=True,
    )
    try:
        uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    finally:
        lock.release()


if __name__ == "__main__":
    main()
