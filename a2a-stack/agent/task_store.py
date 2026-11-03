"""Per-agent durable A2A task storage with automatic native-process recovery."""
from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from a2a.server.context import ServerCallContext
from a2a.server.tasks.database_task_store import DatabaseTaskStore
from a2a.types import ListTasksRequest, Message, Part, Role, Task, TaskState, TaskStatus

TASK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
ACTIVE_STATES = {TaskState.TASK_STATE_SUBMITTED, TaskState.TASK_STATE_WORKING}
INTERRUPTED_MESSAGE = (
    "The native worker was not running when the host recovered this task. "
    "The task is marked failed; create a continuation assignment instead of replaying it."
)
CONTINUED_MESSAGE = "The original native worker process is alive and identity-matched; the host is monitoring it."


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _process_matches(pid: int, expected_token: str) -> bool:
    """Check both Windows process liveness and creation identity on one handle."""
    if os.name != "nt" or isinstance(pid, bool) or pid <= 0 or not expected_token:
        return False
    from ctypes import wintypes

    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_void_p, ctypes.c_void_p]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL

    handle = kernel.OpenProcess(0x00100000 | 0x1000, False, pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
    if not handle:
        return False

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    created, exited, kernel_time, user_time = FileTime(), FileTime(), FileTime(), FileTime()
    exit_code = wintypes.DWORD()
    try:
        if kernel.WaitForSingleObject(handle, 0) != 0x102:  # WAIT_TIMEOUT means still running
            return False
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value != 259:  # STILL_ACTIVE
            return False
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                      ctypes.byref(kernel_time), ctypes.byref(user_time)):
            return False
        token = f"{created.high:08x}{created.low:08x}"
        return token == expected_token
    finally:
        kernel.CloseHandle(handle)


def _status_message(state: int, text: str) -> TaskStatus:
    status = TaskStatus(state=state)
    status.timestamp.GetCurrentTime()
    status.message.CopyFrom(Message(role=Role.ROLE_AGENT, parts=[Part(text=text)]))
    return status


class RecoveringDatabaseTaskStore(DatabaseTaskStore):
    """Official SQLAlchemy TaskStore with one serialized startup recovery pass."""

    def __init__(self, engine, state_root: Path, agent_key: str):
        super().__init__(engine, owner_resolver=lambda _context: agent_key)
        self.state_root = Path(state_root).resolve()
        self.agent_key = agent_key
        self._recovery_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._recovered = False
        self._watched_processes: dict[str, dict] = {}
        self._monitor_task: asyncio.Task | None = None

    async def _recover_once(self, context: ServerCallContext) -> None:
        if self._recovered:
            return
        async with self._recovery_lock:
            if self._recovered:
                return
            await super().initialize()
            page_token = None
            seen_tokens = set()
            while True:
                request = ListTasksRequest()
                if page_token:
                    request.page_token = page_token
                page = await super().list(request, context)
                for task in page.tasks:
                    if task.status.state not in ACTIVE_STATES:
                        continue
                    process_record = self._process_record(task.id)
                    alive = bool(process_record and _process_matches(
                        process_record["pid"], process_record["process_token"]))
                    if alive:
                        task.status.CopyFrom(_status_message(TaskState.TASK_STATE_WORKING, CONTINUED_MESSAGE))
                        await super().save(task, context)
                        self._watched_processes[task.id] = process_record
                    else:
                        task.status.CopyFrom(_status_message(TaskState.TASK_STATE_FAILED, INTERRUPTED_MESSAGE))
                        _atomic_json(self._receipt_dir(task.id) / "terminal.json", {
                            "task_id": task.id,
                            "state": "TASK_STATE_FAILED",
                            "recovery": "native_worker_not_alive_or_identity_mismatch",
                        })
                        await super().save(task, context)
                page_token = page.next_page_token or None
                if not page_token:
                    break
                if page_token in seen_tokens:
                    raise RuntimeError("task store returned a repeated recovery page token")
                seen_tokens.add(page_token)
            self._recovered = True
            if self._watched_processes and self._monitor_task is None:
                self._monitor_task = asyncio.create_task(self._monitor_processes(context))

    async def _monitor_processes(self, context: ServerCallContext) -> None:
        """Track only identity-matched in-flight processes discovered at startup."""
        while self._watched_processes:
            await asyncio.sleep(1)
            for task_id, process in list(self._watched_processes.items()):
                if _process_matches(process["pid"], process["process_token"]):
                    continue
                async with self._write_lock:
                    task = await super().get(task_id, context)
                    if task is None or task.status.state not in ACTIVE_STATES:
                        self._watched_processes.pop(task_id, None)
                        continue
                    task.status.CopyFrom(_status_message(TaskState.TASK_STATE_FAILED, INTERRUPTED_MESSAGE))
                    _atomic_json(self._receipt_dir(task_id) / "terminal.json", {
                        "task_id": task_id,
                        "state": "TASK_STATE_FAILED",
                        "recovery": "monitored_native_worker_exited_without_terminal_task_result",
                    })
                    await super().save(task, context)
                    self._watched_processes.pop(task_id, None)

    def _task_dir(self, task_id: str) -> Path:
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            raise ValueError("persisted task ID is unsafe for host-state lookup")
        return self.state_root / "tasks" / task_id

    def _receipt_dir(self, task_id: str) -> Path:
        if isinstance(task_id, str) and TASK_ID_RE.fullmatch(task_id):
            return self.state_root / "tasks" / task_id
        safe_id = hashlib.sha256(str(task_id).encode("utf-8", errors="replace")).hexdigest()
        return self.state_root / "tasks" / "_invalid" / safe_id

    def _process_record(self, task_id: str) -> dict | None:
        try:
            value = json.loads((self._task_dir(task_id) / "process.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(value, dict):
            return None
        pid, token = value.get("pid"), value.get("process_token")
        if isinstance(pid, bool) or not isinstance(pid, int) or not isinstance(token, str) or not token:
            return None
        return {"pid": pid, "process_token": token}

    async def save(self, task: Task, context: ServerCallContext) -> None:
        await self._recover_once(context)
        async with self._write_lock:
            await super().save(task, context)

    async def get(self, task_id: str, context: ServerCallContext) -> Task | None:
        await self._recover_once(context)
        return await super().get(task_id, context)

    async def list(self, params: ListTasksRequest, context: ServerCallContext):
        await self._recover_once(context)
        return await super().list(params, context)

    async def delete(self, task_id: str, context: ServerCallContext) -> None:
        await self._recover_once(context)
        await super().delete(task_id, context)

    async def close(self) -> None:
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
            self._monitor_task = None
        await self.engine.dispose()


def create_task_store(state_root: Path, agent_key: str) -> RecoveringDatabaseTaskStore:
    """Create an official SQLite-backed task store isolated to one A2A agent key."""
    if not isinstance(agent_key, str) or not agent_key.strip():
        raise ValueError("agent_key is required")
    state_root = Path(state_root).resolve()
    digest = hashlib.sha256(agent_key.encode("utf-8")).hexdigest()
    database = state_root / "protocol" / f"{digest}.sqlite"
    database.parent.mkdir(parents=True, exist_ok=True)
    url = URL.create("sqlite+aiosqlite", database=str(database))
    engine = create_async_engine(url)
    return RecoveringDatabaseTaskStore(engine, state_root, agent_key)
