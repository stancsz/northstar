"""Per-agent durable A2A task storage with automatic native-process recovery."""
from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from a2a.server.context import ServerCallContext
from a2a.server.tasks.database_task_store import DatabaseTaskStore
from a2a.types import ListTasksRequest, Message, Part, Role, Task, TaskState, TaskStatus

TASK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
ACTIVE_STATES = {TaskState.TASK_STATE_SUBMITTED, TaskState.TASK_STATE_WORKING}
TASK_STATE_NAMES = {
    TaskState.TASK_STATE_SUBMITTED: "TASK_STATE_SUBMITTED",
    TaskState.TASK_STATE_WORKING: "TASK_STATE_WORKING",
    TaskState.TASK_STATE_COMPLETED: "TASK_STATE_COMPLETED",
    TaskState.TASK_STATE_FAILED: "TASK_STATE_FAILED",
    TaskState.TASK_STATE_CANCELED: "TASK_STATE_CANCELED",
    TaskState.TASK_STATE_INPUT_REQUIRED: "TASK_STATE_INPUT_REQUIRED",
    TaskState.TASK_STATE_REJECTED: "TASK_STATE_REJECTED",
    TaskState.TASK_STATE_AUTH_REQUIRED: "TASK_STATE_AUTH_REQUIRED",
}
# The states the A2A protocol treats as terminal, by name.  A terminal task
# is the only one a receipt may describe.
TERMINAL_STATE_NAMES = {
    "TASK_STATE_COMPLETED", "TASK_STATE_FAILED",
    "TASK_STATE_CANCELED", "TASK_STATE_REJECTED",
}
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
        self._closing = False
        self._monitor_failures: dict[str, dict] = {}
        self._pending_receipts: dict[str, dict] = {}
        self._unrecovered_tasks: dict[str, dict] = {}
        # The context the recovery pass ran under, so a shutdown flush can
        # re-read the database before it publishes a pending receipt.
        self._context: ServerCallContext | None = None

    async def _recover_once(self, context: ServerCallContext) -> None:
        if self._recovered:
            return
        async with self._recovery_lock:
            if self._recovered:
                return
            await super().initialize()
            self._context = context
            page_token = None
            seen_tokens = set()
            while True:
                request = ListTasksRequest()
                if page_token:
                    request.page_token = page_token
                page = await super().list(request, context)
                for task in page.tasks:
                    state_name = TASK_STATE_NAMES.get(task.status.state)
                    if state_name in TERMINAL_STATE_NAMES:
                        # A host may have stopped after committing a terminal
                        # row but before its receipt reached disk. Reconcile
                        # that durable database state on restart; this only
                        # publishes evidence and never replays task side effects.
                        receipt = self._receipt_dir(task.id) / "terminal.json"
                        try:
                            existing = json.loads(receipt.read_text(encoding="utf-8"))
                        except (OSError, ValueError):
                            existing = None
                        if not isinstance(existing, dict) or existing.get("state") != state_name:
                            self._pending_receipts[task.id] = {
                                "task_id": task.id, "state": state_name}
                            try:
                                self._publish_receipt(task.id, state_name)
                            except OSError as error:
                                self._record_monitor_failure(task.id, error)
                        continue
                    if task.status.state not in ACTIVE_STATES:
                        continue
                    process_record = self._process_record(task.id)
                    alive = bool(process_record and _process_matches(
                        process_record["pid"], process_record["process_token"]))
                    # One task's failure must not end the recovery pass.  An
                    # unisolated commit failure would abort the pass before
                    # `self._recovered` is set, so every later call would
                    # re-enter recovery, re-raise the same error, and wedge
                    # the whole store.
                    try:
                        if alive:
                            # The task was ACTIVE in the snapshot taken when
                            # the pass started.  It may have finished since,
                            # and committing WORKING from that stale snapshot
                            # would move a finished task back into flight and
                            # retire its receipt.  The current state is
                            # re-read under the write lock, which also
                            # serializes this commit and the withdrawal
                            # against the executor's.
                            async with self._write_lock:
                                current = await super().get(task.id, context)
                                if current is None or current.status.state not in ACTIVE_STATES:
                                    continue
                                current.status.CopyFrom(
                                    _status_message(TaskState.TASK_STATE_WORKING, CONTINUED_MESSAGE))
                                await super().save(current, context)
                                # The task is in flight, so any receipt for it
                                # is stale: the executor may have published one
                                # before the host died, and the database now
                                # says the work is still running.  The receipt
                                # is withdrawn here rather than on the generic
                                # save path because this is the one place
                                # where the host has verified the native
                                # worker is alive and has re-committed the
                                # task as in flight.
                                self._withdraw_receipt(task.id)
                                self._watched_processes[task.id] = process_record
                        else:
                            # The task was ACTIVE in the snapshot taken when
                            # the pass started.  It may have finished since,
                            # and committing FAILED from that stale snapshot
                            # would overwrite a newer authoritative commit.
                            # The current state is re-read under the write
                            # lock, which also serializes this commit and its
                            # receipt against the executor's.
                            async with self._write_lock:
                                current = await super().get(task.id, context)
                                if current is None or current.status.state not in ACTIVE_STATES:
                                    continue
                                current.status.CopyFrom(
                                    _status_message(TaskState.TASK_STATE_FAILED, INTERRUPTED_MESSAGE))
                                await super().save(current, context)
                                self._pending_receipts[task.id] = {
                                    "task_id": task.id,
                                    "state": "TASK_STATE_FAILED",
                                    "recovery": "native_worker_not_alive_or_identity_mismatch",
                                }
                                # The state commit and the receipt write can
                                # fail separately.  An unisolated receipt
                                # failure would abort the whole recovery pass
                                # and skip every other task's recovery with it.
                                self._publish_receipt(task.id, "TASK_STATE_FAILED")
                    except Exception as error:  # noqa: BLE001 - one task must not end recovery
                        # The task was not recovered.  Keep it for a later
                        # attempt so it is not stranded reporting dead work
                        # as still in flight.
                        self._unrecovered_tasks[task.id] = {
                            "task_id": task.id,
                            "process_record": process_record,
                        }
                        self._record_monitor_failure(task.id, error)

                page_token = page.next_page_token or None
                if not page_token:
                    break
                if page_token in seen_tokens:
                    raise RuntimeError("task store returned a repeated recovery page token")
                seen_tokens.add(page_token)
            self._recovered = True
            if (self._watched_processes or self._pending_receipts
                    or self._unrecovered_tasks) and self._monitor_task is None:
                self._start_monitor(context)

    def _start_monitor(self, context: ServerCallContext) -> asyncio.Task | None:
        """Start one monitor unless shutdown has begun or one is still live."""
        if self._closing:
            return None
        if self._monitor_task is not None and not self._monitor_task.done():
            return self._monitor_task
        monitor = asyncio.create_task(self._monitor_processes(context))
        self._monitor_task = monitor
        monitor.add_done_callback(self._on_monitor_done)
        return monitor

    async def _monitor_processes(self, context: ServerCallContext) -> None:
        """Track only identity-matched in-flight processes discovered at startup."""
        while self._watched_processes or self._pending_receipts or self._unrecovered_tasks:
            await asyncio.sleep(1)
            # A receipt whose write failed during the recovery pass is
            # retried here.  Without this the receipt would never be
            # published, because its task is no longer watched.
            await self._retry_pending_receipts(context)
            await self._retry_unrecovered_tasks(context)
            for task_id, process in list(self._watched_processes.items()):
                if _process_matches(process["pid"], process["process_token"]):
                    continue
                # One task's failure must not strand the others.  The receipt
                # write is a separate step from the state commit, so it can
                # fail on its own; letting that escape would end the whole
                # monitor loop and leave every other watched task unreported.
                try:
                    await self._report_interrupted_task(task_id, context)
                except Exception as error:  # noqa: BLE001 - one task must not end the monitor
                    self._record_monitor_failure(task_id, error)
                    continue
                self._watched_processes.pop(task_id, None)

    async def _retry_unrecovered_tasks(self, context: ServerCallContext) -> None:
        """Retry the tasks whose recovery commit failed on an earlier pass.

        A task whose state commit failed is still active in the database, so
        without a retry it would keep reporting dead work as still in flight
        for the rest of the host's life.
        """
        for task_id, entry in list(self._unrecovered_tasks.items()):
            process_record = entry.get("process_record")
            try:
                # The commit and its receipt happen under the write lock, so
                # they cannot interleave with the executor's own commit and
                # leave a receipt describing a state the database does not
                # hold.
                async with self._write_lock:
                    task = await super().get(task_id, context)
                    if task is None:
                        self._unrecovered_tasks.pop(task_id, None)
                        continue
                    if task.status.state not in ACTIVE_STATES:
                        # Someone else finished it; it owns its own receipt.
                        self._unrecovered_tasks.pop(task_id, None)
                        continue
                    alive = bool(process_record and _process_matches(
                        process_record["pid"], process_record["process_token"]))
                    if alive:
                        task.status.CopyFrom(_status_message(TaskState.TASK_STATE_WORKING, CONTINUED_MESSAGE))
                        await super().save(task, context)
                        # The task is in flight, so any receipt for it is
                        # stale and must not claim a terminal outcome.  The
                        # receipt is withdrawn only here, where the host has
                        # verified the native worker is alive and the
                        # database has just been re-read under the write
                        # lock and still calls the task active.
                        self._withdraw_receipt(task_id)
                        self._watched_processes[task_id] = process_record
                    else:
                        task.status.CopyFrom(_status_message(TaskState.TASK_STATE_FAILED, INTERRUPTED_MESSAGE))
                        await super().save(task, context)
                        self._pending_receipts[task_id] = {
                            "task_id": task_id,
                            "state": "TASK_STATE_FAILED",
                            "recovery": "native_worker_not_alive_or_identity_mismatch",
                        }
                        self._publish_receipt(task_id, "TASK_STATE_FAILED")
            except Exception as error:  # noqa: BLE001 - one task must not end the monitor
                self._record_monitor_failure(task_id, error)
                continue
            self._unrecovered_tasks.pop(task_id, None)

    async def _retry_pending_receipts(self, context: ServerCallContext) -> None:
        """Publish receipts whose write failed on an earlier attempt.

        The database is re-read before the receipt is published, and the
        receipt records the state the database actually holds.  A pending
        receipt says the task was interrupted, but the task may since have
        been finished by its own executor; publishing the pending claim then
        would say FAILED for a task the database calls COMPLETED.
        """
        for task_id in list(self._pending_receipts):
            try:
                # The read and the publication happen under the write lock,
                # so no commit can land between them.  A read outside the
                # lock could be followed by a commit and then publish a
                # receipt describing the state that commit replaced.
                async with self._write_lock:
                    task = await super().get(task_id, context)
                    if task is None:
                        # The task is gone; there is no receipt to write.
                        self._pending_receipts.pop(task_id, None)
                        continue
                    state = TASK_STATE_NAMES.get(task.status.state)
                    if state not in TERMINAL_STATE_NAMES:
                        # The task is in flight again, so there is no terminal
                        # state to publish.  The receipt stays owed: the
                        # startup recovery pass will publish it if the task is
                        # later found dead.
                        continue
                    self._publish_receipt(task_id, state)
            except Exception as error:  # noqa: BLE001 - one receipt must not end the monitor
                self._record_monitor_failure(task_id, error)


    async def _report_interrupted_task(self, task_id: str, context: ServerCallContext) -> None:
        """Fail one interrupted task and publish its receipt.

        The state commit and the receipt write are separately retryable.  The
        receipt is published only after the FAILED state is committed, so a
        receipt is never visible for a task the database still calls active.
        When the receipt write fails the task stays watched and the pending
        receipt is retried on the next pass; the task is not dropped with no
        receipt.
        """
        async with self._write_lock:
            task = await super().get(task_id, context)
            if task is None:
                return
            if task.status.state in ACTIVE_STATES:
                task.status.CopyFrom(_status_message(TaskState.TASK_STATE_FAILED, INTERRUPTED_MESSAGE))
                await super().save(task, context)
                self._pending_receipts[task_id] = {
                    "task_id": task_id,
                    "state": "TASK_STATE_FAILED",
                    "recovery": "monitored_native_worker_exited_without_terminal_task_result",
                }
                self._publish_receipt(task_id, "TASK_STATE_FAILED")
                return
            if task_id not in self._pending_receipts:
                # The task was already finished by someone else; it owns its
                # own receipt and there is nothing for the monitor to publish.
                return
            # The task still owes a receipt, but it is no longer active, so
            # somebody else finished it.  The receipt must describe the
            # state the DATABASE holds, not the state this monitor was
            # going to commit: publishing FAILED here would claim an
            # interruption for a task the database calls COMPLETED, and
            # would send the owner after the wrong repair.
            state = TASK_STATE_NAMES.get(task.status.state)
            if state not in TERMINAL_STATE_NAMES:
                # The task is in flight again, so there is no terminal state
                # to publish.  The receipt stays owed.
                return
            self._publish_receipt(task_id, state)

    def _publish_receipt(self, task_id: str, state: str | None = None) -> None:
        """Write one task's terminal receipt and clear its pending entry.

        `state` is the authoritative terminal state from the database.  The
        receipt's `state` field always mirrors it, so the receipt never
        contradicts the database: a receipt claiming FAILED for a task the
        database calls COMPLETED would send an agent after the wrong repair.

        The recovery evidence is kept only while the database agrees with it.
        The recovery field is the operational statement "this task was
        interrupted; create a continuation assignment instead of replaying
        it".  That instruction is only true while the task is still FAILED.
        Once a later commit has moved the task to another terminal state the
        interruption has been superseded, and keeping the field would leave a
        completed task carrying live-looking guidance to replay it.

        The receipt is MERGED into whatever is already there, not replaced:
        two writers publish this path, and a replacement would erase
        whichever record was written first.
        """
        receipt = self._receipt_dir(task_id) / "terminal.json"
        pending = self._pending_receipts.get(task_id) or {}
        try:
            existing = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = None
        merged = dict(existing) if isinstance(existing, dict) else {}
        merged.update(pending)
        merged["task_id"] = task_id
        authoritative = state or merged.get("state")
        merged["state"] = authoritative
        if authoritative != "TASK_STATE_FAILED":
            # The interruption evidence has been superseded by a later
            # authoritative commit; it stays in the host event history, not
            # in the receipt an agent reads to decide what to do next.
            merged.pop("recovery", None)
        _atomic_json(receipt, merged)
        self._pending_receipts.pop(task_id, None)

    def _record_monitor_failure(self, task_id: str, error: Exception) -> None:
        """Record that one watched task could not be reported, and keep going.

        The task stays watched so a later pass can retry it.  If the failure
        was in the receipt write the database state is already committed, so
        the next pass sees a non-active task and finishes the receipt.
        """
        self._monitor_failures[task_id] = {
            "task_id": task_id,
            "error_type": type(error).__name__,
            "error": str(error),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._write_monitor_failures()
        except Exception as failure:  # noqa: BLE001 - recording must not end the monitor
            # The recorder is the last trace of a silent loss, so it must not
            # be the thing that ends the monitor.
            print(f"task-store monitor failure record could not be written: "
                  f"{type(failure).__name__}: {failure}", file=sys.stderr, flush=True)

    def _write_monitor_failures(self) -> None:
        """Persist the monitor failure record so the loss is not silent.

        Every agent in a host shares one state root, so the record is a
        shared file.  It is merged rather than replaced: the last store to
        fail must not erase the failures the other stores recorded, which
        would make the loss silent again.
        """
        path = self.state_root / "control" / "task-store-monitor-failures.json"
        try:
            existing = {}
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(stored, dict) and isinstance(stored.get("failures"), list):
                    existing = {entry["task_id"]: entry for entry in stored["failures"]
                                if isinstance(entry, dict) and isinstance(entry.get("task_id"), str)}
            except (OSError, ValueError):
                existing = {}
            merged = dict(existing)
            merged.update(self._monitor_failures)
            _atomic_json(path, {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "failures": sorted(merged.values(), key=lambda entry: entry["task_id"]),
            })
        except OSError as error:
            # The failure record itself is the last trace of a silent loss, so
            # it cannot be allowed to fail silently.
            print(f"task-store monitor failure record could not be written: "
                  f"{type(error).__name__}: {error}", file=sys.stderr, flush=True)


    def _on_monitor_done(self, monitor: asyncio.Task) -> None:
        """Record monitor loss and rearm any outstanding autonomous work."""
        # A stale callback must not clear or replace a newer monitor.
        if self._monitor_task is not monitor:
            return
        self._monitor_task = None
        if monitor.cancelled():
            return
        error = monitor.exception()
        if error is not None:
            self._record_monitor_failure("*monitor*", error)
        if (not self._closing and (self._watched_processes
                                   or self._pending_receipts
                                   or self._unrecovered_tasks)
                and self._context is not None):
            self._start_monitor(self._context)

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
            # The terminal state of a task is final.  The SDK's legacy task
            # store is last-writer-wins with no terminal guard, so a stale
            # in-flight event arriving after the terminal commit could
            # otherwise move the row back to a non-terminal state -- which
            # would invalidate the receipt published for the terminal
            # commit and leave the owner with no truthful record of the
            # outcome.  The store refuses that regression, so a published
            # receipt always describes the state the database still holds.
            current = await super().get(task.id, context)
            if current is not None:
                current_state = TASK_STATE_NAMES.get(current.status.state)
                incoming = TASK_STATE_NAMES.get(task.status.state)
                if (current_state in TERMINAL_STATE_NAMES
                        and incoming not in TERMINAL_STATE_NAMES):
                    # The incoming commit is stale: the task already
                    # reached its terminal state.  Keeping the row terminal
                    # is the only write that does not contradict the
                    # receipt.  A terminal commit may still supersede
                    # another terminal commit; the last terminal writer
                    # wins, and the receipt is republished to match it.
                    return
            await super().save(task, context)
            state = TASK_STATE_NAMES.get(task.status.state)
            if state in TERMINAL_STATE_NAMES:
                # The receipt is published inside the same critical section
                # as the commit that made the task terminal, so the receipt
                # always describes the state the database actually holds.
                # A receipt published outside that section could describe a
                # state that a later commit has already superseded.
                try:
                    self._publish_receipt(task.id, state)
                except OSError as error:
                    # The commit landed, so the task IS terminal, but the
                    # receipt did not.  The failure must not escape into the
                    # caller's request path, and it must not vanish: the
                    # receipt is left pending so a later pass publishes it.
                    self._pending_receipts[task.id] = {
                        "task_id": task.id, "state": state}
                    self._record_monitor_failure(task.id, error)
                    self._start_monitor(context)

    def _withdraw_receipt(self, task_id: str) -> None:
        """Remove a receipt for a task the database calls in flight.

        A receipt may only be withdrawn while the database holds the task in
        an active state.  The check happens under the write lock, so no
        terminal commit can land between the check and the withdrawal.

        The withdrawal retires the receipt and the host's outstanding claim
        together, and it records the retirement in the monitor failure
        record's sibling file so the loss is never silent: the host's
        outstanding FAILED+recovery claim is evidence that the task was
        interrupted, and dropping it without a trace would lose the
        interruption record.
        """
        receipt = self._receipt_dir(task_id) / "terminal.json"
        try:
            existing = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = None
        pending = self._pending_receipts.get(task_id)
        try:
            receipt.unlink()
        except FileNotFoundError:
            # There is no receipt to retire, but the host may still owe a
            # claim for this task.  The claim is retired, not dropped: it
            # is recorded so the outstanding obligation is never lost
            # without a trace.
            self._pending_receipts.pop(task_id, None)
            if pending is not None:
                self._record_retired_receipt(task_id, {}, pending)
            return
        except OSError:
            # The receipt could not be withdrawn.  Leaving it in place is
            # better than raising into the caller's commit path, but the
            # contradiction must not be silent.
            self._record_monitor_failure(task_id, OSError(
                "the terminal receipt could not be withdrawn"))
            return
        retired = self._pending_receipts.pop(task_id, None)
        if isinstance(existing, dict) or retired is not None:
            self._record_retired_receipt(
                task_id, existing if isinstance(existing, dict) else {}, retired)

    def _record_retired_receipt(self, task_id: str, receipt: dict,
                                pending: dict | None) -> None:
        """Record a retired receipt so the retirement is never silent.

        A receipt that is withdrawn had claimed a terminal outcome for a
        task the database calls in flight.  The claim is retired, not
        deleted: the interruption evidence in it is a fact about what the
        host observed, and an operator reading the record later needs to see
        that the claim was made and why it was retired.
        """
        record = {
            "task_id": task_id,
            "retired_at": datetime.now(timezone.utc).isoformat(),
            "retired_state": receipt.get("state"),
            "retired_recovery": receipt.get("recovery"),
            "pending_state": (pending or {}).get("state"),
            "pending_recovery": (pending or {}).get("recovery"),
        }
        path = self.state_root / "control" / "task-store-retired-receipts.json"
        try:
            existing = {}
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(stored, dict) and isinstance(stored.get("retired"), list):
                    existing = {entry["task_id"]: entry for entry in stored["retired"]
                                if isinstance(entry, dict) and isinstance(entry.get("task_id"), str)}
            except (OSError, ValueError):
                existing = {}
            merged = dict(existing)
            merged[task_id] = record
            _atomic_json(path, {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "retired": sorted(merged.values(), key=lambda entry: entry["task_id"]),
            })
        except OSError as error:
            # The retirement record is the last trace of a retired claim, so
            # it cannot be allowed to fail silently.
            print(f"task-store retired receipt record could not be written: "
                  f"{type(error).__name__}: {error}", file=sys.stderr, flush=True)

    async def get(self, task_id: str, context: ServerCallContext) -> Task | None:
        await self._recover_once(context)
        async with self._write_lock:
            return await super().get(task_id, context)

    async def list(self, params: ListTasksRequest, context: ServerCallContext):
        await self._recover_once(context)
        return await super().list(params, context)

    async def delete(self, task_id: str, context: ServerCallContext) -> None:
        await self._recover_once(context)
        await super().delete(task_id, context)

    async def close(self) -> None:
        self._closing = True
        try:
            if self._monitor_task is not None:
                monitor = self._monitor_task
                monitor.cancel()
                await asyncio.gather(monitor, return_exceptions=True)
                # Let the done callback observe _closing and settle its reference.
                await asyncio.sleep(0)
                # Do not erase a newer task if an unexpected callback/re-entry
                # managed to install one during cancellation.
                if self._monitor_task is monitor:
                    self._monitor_task = None
            await self._flush_pending_receipts()
        finally:
            await self.engine.dispose()

    async def _flush_pending_receipts(self) -> None:
        """Publish receipts still pending at shutdown.

        A receipt whose write was still failing when the host stopped is
        the artifact consumers read, so dropping it would leave the task
        permanently unreported.

        The database is re-read first, for the same reason the monitor
        re-reads it: a pending receipt says the task was interrupted, but
        the task may have been finished by its own executor since, and
        publishing the stale receipt would claim the opposite.
        """
        for task_id in list(self._pending_receipts):
            try:
                # The read and the publication are serialized by the write
                # lock, for the same reason the monitor's retry is: a commit
                # landing between them would leave the receipt describing a
                # state the database no longer holds.
                async with self._write_lock:
                    state = None
                    if self._context is not None:
                        task = await super().get(task_id, self._context)
                        if task is None:
                            self._pending_receipts.pop(task_id, None)
                            continue
                        state = TASK_STATE_NAMES.get(task.status.state)
                        if state not in TERMINAL_STATE_NAMES:
                            continue
                    self._publish_receipt(task_id, state)
            except Exception as error:  # noqa: BLE001 - shutdown must continue
                self._record_monitor_failure(task_id, error)



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
