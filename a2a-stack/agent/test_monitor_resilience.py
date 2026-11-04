"""Regression tests for the task-store recovery monitor's silent death.

The monitor that watches identity-matched native workers was created with
`asyncio.create_task` and had no done-callback, and nothing in the stack ever
called `.exception()` on it.  It also had no error isolation inside its loop,
so one failing receipt write ended the whole loop.  The consequences were:

  * the monitor died with no trace at all (the module has no logging), and
  * every task it was still watching was left unreported - one task's failed
    receipt write stranded all the others.

These tests pin the repaired behaviour: one task's failure must not end the
monitor, the failed receipt must be retried rather than dropped, and the
failure must be recorded durably instead of vanishing.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from a2a.server.context import ServerCallContext
from a2a.server.tasks.database_task_store import DatabaseTaskStore
from a2a.types import Task, TaskState, TaskStatus

from task_store import create_task_store

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "a2a-stack" / "runtime"))
sys.path.insert(0, str(ROOT / "a2a-stack"))
import runner  # noqa: E402


def make_task(task_id: str, state: int) -> Task:
    return Task(id=task_id, context_id=f"ctx-{task_id}", status=TaskStatus(state=state))


class FailingDatabaseSave:
    """Make one task's database save fail so recovery isolation can be probed."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.armed = False
        self.failures = 0

    def patch(self):
        original = DatabaseTaskStore.save
        gate = self

        async def failing_save(store, task, context):
            if gate.armed and task.id == gate.task_id:
                gate.failures += 1
                raise OSError(28, "No space left on device")
            await original(store, task, context)

        return patch.object(DatabaseTaskStore, "save", failing_save)


def spawn_idle():
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


class MonitorResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.name != "nt":
            self.skipTest("native process identity checks are Windows-specific")
        scratch = ROOT / "tmp" / "review-uncommitted-20261104" / "receipt-worker"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.state_root = Path(self.tmp.name)
        self.context = ServerCallContext()
        self.procs = []
        self.stores = []

    async def asyncTearDown(self):
        for store in self.stores:
            try:
                await store.close()
            except Exception:  # noqa: BLE001 - retain cleanup failure for unittest
                raise
        self.stores.clear()
        for proc in self.procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
        self.procs.clear()
        self.tmp.cleanup()

    def open_store(self, agent_key: str):
        store = create_task_store(self.state_root, agent_key)
        self.stores.append(store)
        return store

    async def test_close_disposes_engine_when_receipt_flush_raises(self):
        store = self.open_store("close-failure-agent")
        await store.save(make_task("close-failure", TaskState.TASK_STATE_COMPLETED), self.context)
        failure = RuntimeError("injected flush failure")
        with patch.object(store, "_flush_pending_receipts", side_effect=failure):
            with self.assertRaises(RuntimeError) as raised:
                await store.close()
        self.assertIs(raised.exception, failure)
        self.assertEqual(store.engine.pool.checkedout(), 0)
        self.stores.remove(store)
        database = next((self.state_root / "protocol").glob("*.sqlite"))
        database.unlink()
        self.assertFalse(database.exists())

    async def seed_watched_tasks(self, agent_key: str, task_ids: list[str]) -> None:
        """Create in-flight tasks whose native workers are alive and watched."""
        for task_id in task_ids:
            proc = spawn_idle()
            self.procs.append(proc)
            token = runner.process_token(proc.pid)
            task_dir = self.state_root / "tasks" / task_id
            task_dir.mkdir(parents=True)
            (task_dir / "process.json").write_text(
                json.dumps({"pid": proc.pid, "process_token": token}), encoding="utf-8")

        seeder = self.open_store(agent_key)
        for task_id in task_ids:
            await seeder.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)
        await seeder.close()
        self.stores.remove(seeder)

    async def wait_for(self, predicate, timeout: float = 20.0) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.1)
            if predicate():
                return True
        return False

    async def test_one_failed_receipt_write_does_not_orphan_the_other_watched_tasks(self):
        """The core defect: one task's failed receipt write stranded the rest."""
        task_ids = ["watched-a", "watched-b"]
        await self.seed_watched_tasks("orphan-agent", task_ids)

        store = self.open_store("orphan-agent")
        for task_id in task_ids:
            task = await store.get(task_id, self.context)
            self.assertEqual(task.status.state, TaskState.TASK_STATE_WORKING)

        monitor = store._monitor_task
        self.assertIsNotNone(monitor, "the monitor task was never created")

        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)
        import task_store as ts
        original_atomic = ts._atomic_json
        failed_once = {"done": False}

        def failing_atomic(path, value):
            if not failed_once["done"] and path.name == "terminal.json":
                failed_once["done"] = True
                raise OSError(28, "No space left on device")
            return original_atomic(path, value)

        ts._atomic_json = failing_atomic
        try:
            # Let the first failed write happen, then restore the real writer
            # so the monitor's next pass can prove recovery.
            self.assertTrue(await self.wait_for(lambda: failed_once["done"]),
                            "the injected receipt failure was not exercised")
            ts._atomic_json = original_atomic
            for task_id in task_ids:
                receipt = self.state_root / "tasks" / task_id / "terminal.json"
                self.assertTrue(
                    await self.wait_for(receipt.exists),
                    f"{task_id} never received its terminal receipt",
                )
        finally:
            ts._atomic_json = original_atomic

        # Every watched task must end up FAILED with a published receipt, even
        # though one receipt write failed.
        for task_id in task_ids:
            task = await store.get(task_id, self.context)
            self.assertEqual(
                task.status.state, TaskState.TASK_STATE_FAILED,
                f"{task_id} was left reporting dead work as still in flight",
            )
            receipt = json.loads(
                (self.state_root / "tasks" / task_id / "terminal.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["state"], "TASK_STATE_FAILED")

    async def test_the_monitor_survives_a_failed_receipt_write(self):
        """The monitor must not die, so it cannot take the other tasks with it."""
        task_ids = ["watched-a", "watched-b"]
        await self.seed_watched_tasks("survive-agent", task_ids)

        store = self.open_store("survive-agent")
        for task_id in task_ids:
            await store.get(task_id, self.context)
        monitor = store._monitor_task

        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)

        import task_store as ts
        original_atomic = ts._atomic_json
        failed_once = {"done": False}

        def failing_atomic(path, value):
            if not failed_once["done"] and path.name == "terminal.json":
                failed_once["done"] = True
                raise OSError(28, "No space left on device")
            return original_atomic(path, value)

        ts._atomic_json = failing_atomic
        try:
            self.assertTrue(
                await self.wait_for(lambda: all(
                    (self.state_root / "tasks" / t / "terminal.json").exists() for t in task_ids)),
                "the monitor did not finish reporting every watched task",
            )
        finally:
            ts._atomic_json = original_atomic

        self.assertFalse(
            monitor.done() and monitor.exception() is not None,
            "the monitor ended with an unhandled exception",
        )

    async def test_the_failed_receipt_is_retried_rather_than_dropped(self):
        """A task whose receipt write failed must still end up with a receipt."""
        task_id = "retry-me"
        await self.seed_watched_tasks("retry-agent", [task_id])

        store = self.open_store("retry-agent")
        await store.get(task_id, self.context)

        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)

        import task_store as ts
        original_atomic = ts._atomic_json
        failed_once = {"done": False}

        def failing_atomic(path, value):
            if not failed_once["done"] and path.name == "terminal.json":
                failed_once["done"] = True
                raise OSError(28, "No space left on device")
            return original_atomic(path, value)

        ts._atomic_json = failing_atomic
        try:
            receipt = self.state_root / "tasks" / task_id / "terminal.json"
            self.assertTrue(
                await self.wait_for(receipt.exists),
                "the receipt was never published after the transient failure",
            )
        finally:
            ts._atomic_json = original_atomic

        receipt = json.loads(
            (self.state_root / "tasks" / task_id / "terminal.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED")
        self.assertEqual(
            receipt["recovery"], "monitored_native_worker_exited_without_terminal_task_result")

    async def test_the_monitor_failure_is_recorded_durably(self):
        """The failure must leave a trace; the module has no logging to do it."""
        task_id = "recorded"
        await self.seed_watched_tasks("recorded-agent", [task_id])

        store = self.open_store("recorded-agent")
        await store.get(task_id, self.context)

        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)

        import task_store as ts
        original_atomic = ts._atomic_json
        failed_once = {"done": False}

        def failing_atomic(path, value):
            if not failed_once["done"] and path.name == "terminal.json":
                failed_once["done"] = True
                raise OSError(28, "No space left on device")
            return original_atomic(path, value)

        ts._atomic_json = failing_atomic
        try:
            record = self.state_root / "control" / "task-store-monitor-failures.json"
            self.assertTrue(
                await self.wait_for(record.exists),
                "the monitor failure was not recorded anywhere",
            )
        finally:
            ts._atomic_json = original_atomic

        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertTrue(payload["failures"], "the failure record is empty")
        failure = payload["failures"][0]
        self.assertEqual(failure["task_id"], task_id)
        self.assertEqual(failure["error_type"], "OSError")

    async def test_a_monitor_that_dies_is_still_recorded_by_the_backstop(self):
        """If the monitor ever dies with an exception it must not vanish."""
        import task_store as ts

        store = self.open_store("backstop-agent")
        store._record_monitor_failure("probe", OSError(28, "No space left on device"))
        record = self.state_root / "control" / "task-store-monitor-failures.json"
        self.assertTrue(record.exists())
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["failures"][0]["task_id"], "probe")

        # A cancelled monitor is not a failure.
        async def cancelled():
            raise asyncio.CancelledError()

        task = asyncio.create_task(cancelled())
        await asyncio.sleep(0)
        store._on_monitor_done(task)
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["failures"]), 1,
                         "a cancelled monitor must not be recorded as a failure")

    async def test_a_monitor_that_dies_with_an_exception_is_recorded(self):
        """The backstop's positive path: a monitor that died with an error.

        The cancelled case above proves only that a cancellation is ignored.
        This proves the callback actually records a monitor that died with a
        real exception, which is the whole purpose of the backstop.
        """
        store = self.open_store("backstop-positive-agent")

        async def dies():
            raise RuntimeError("monitor loop died")

        task = asyncio.create_task(dies())
        await asyncio.gather(task, return_exceptions=True)
        store._monitor_task = task
        store._on_monitor_done(task)

        record = self.state_root / "control" / "task-store-monitor-failures.json"
        self.assertTrue(record.exists(), "the dead monitor left no trace at all")
        payload = json.loads(record.read_text(encoding="utf-8"))
        recorded = [entry for entry in payload["failures"]
                    if entry["task_id"] == "*monitor*"]
        self.assertEqual(len(recorded), 1,
                         "a monitor that died with an exception was not recorded")
        self.assertEqual(recorded[0]["error_type"], "RuntimeError")
        self.assertIn("monitor loop died", recorded[0]["error"])

    async def test_one_agents_failure_record_does_not_erase_another_agents(self):
        """Every agent in a host shares one state root and one failure file.

        The last store to fail must not erase the failures the other stores
        recorded, or the loss becomes silent again.
        """
        first = self.open_store("role-a")
        second = self.open_store("role-b")

        first._record_monitor_failure("task-a", OSError(28, "No space left on device"))
        second._record_monitor_failure("task-b", OSError(28, "No space left on device"))

        record = self.state_root / "control" / "task-store-monitor-failures.json"
        payload = json.loads(record.read_text(encoding="utf-8"))
        recorded = {entry["task_id"] for entry in payload["failures"]}
        self.assertEqual(recorded, {"task-a", "task-b"},
                         "one agent's failure record erased another agent's")

    async def test_a_failed_startup_receipt_write_does_not_abort_recovery(self):
        """One task's failed receipt write must not skip the other tasks.

        The startup recovery pass is the first thing the store does, so an
        unisolated receipt failure there stranded every other task with it.
        """
        task_ids = ["recover-a", "recover-b"]
        await self.seed_watched_tasks("recover-agent", task_ids)

        # The workers must be gone before the recovery pass runs, otherwise
        # recovery keeps the tasks alive and never takes the receipt path.
        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)

        import task_store as ts
        original_atomic = ts._atomic_json
        failed_once = {"done": False}

        def failing_atomic(path, value):
            if not failed_once["done"] and path.name == "terminal.json":
                failed_once["done"] = True
                raise OSError(28, "No space left on device")
            return original_atomic(path, value)

        ts._atomic_json = failing_atomic
        try:
            store = self.open_store("recover-agent")
            # The recovery pass runs here; every task must be failed and
            # every task must end up with a receipt.
            for task_id in task_ids:
                task = await store.get(task_id, self.context)
                self.assertEqual(
                    task.status.state, TaskState.TASK_STATE_FAILED,
                    f"{task_id} was left reporting dead work as still in flight",
                )
            self.assertTrue(
                await self.wait_for(lambda: all(
                    (self.state_root / "tasks" / t / "terminal.json").exists() for t in task_ids)),
                "a task's receipt was permanently lost after the recovery pass",
            )
        finally:
            ts._atomic_json = original_atomic

    async def test_a_pending_receipt_is_published_at_shutdown(self):
        """A receipt still pending when the host stops must not be dropped."""
        store = self.open_store("shutdown-agent")
        store._pending_receipts["pending-task"] = {
            "task_id": "pending-task",
            "state": "TASK_STATE_FAILED",
            "recovery": "monitored_native_worker_exited_without_terminal_task_result",
        }
        await store.close()
        self.stores.remove(store)

        receipt = self.state_root / "tasks" / "pending-task" / "terminal.json"
        self.assertTrue(receipt.exists(),
                        "the pending receipt was dropped at shutdown")

    async def test_one_task_commit_failure_does_not_wedge_the_whole_store(self):
        """A failed state commit must not brick the store.

        When the recovery pass aborted on one task's commit failure, every
        later `get` re-entered recovery and re-raised, so even a healthy task
        could not be read at all.
        """
        task_ids = ["rec-a", "rec-b"]
        await self.seed_watched_tasks("bricked-agent", task_ids)

        # The workers must be gone before the recovery pass runs, otherwise
        # recovery keeps the tasks alive and never takes the commit path.
        for proc in self.procs:
            proc.terminate()
            proc.wait(timeout=10)

        store = self.open_store("bricked-agent")
        gate = FailingDatabaseSave("rec-a")
        with gate.patch():
            gate.armed = True
            # The first read triggers the recovery pass.  It must not raise:
            # one task's commit failure is isolated to that task.
            task = await store.get("rec-b", self.context)
            self.assertEqual(
                task.status.state, TaskState.TASK_STATE_FAILED,
                "the healthy task was stranded by the other task's commit failure",
            )
            self.assertGreaterEqual(gate.failures, 1,
                                    "the failing task's commit was never attempted")

        # The store must still be usable after the failure.
        task = await store.get("rec-b", self.context)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_FAILED)
        self.assertTrue(store._recovered,
                        "the store never completed its recovery pass")

        # The task whose commit failed must not be stranded reporting dead
        # work as still in flight: a later pass retries it.
        self.assertTrue(
            await self.wait_for_task_state(store, "rec-a", TaskState.TASK_STATE_FAILED),
            "the task whose commit failed was never recovered by a later pass",
        )

    async def wait_for_task_state(self, store, task_id: str, state: int,
                                 timeout: float = 30.0) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            task = await store.get(task_id, self.context)
            if task is not None and task.status.state == state:
                return True
            await asyncio.sleep(0.1)
        return False

    async def test_the_executors_receipt_does_not_erase_the_recovery_receipt(self):
        """Two writers, one path: the evidence of an interruption must survive.

        The executor publishes its own terminal state to the same file the
        recovery pass uses.  Whichever writes last, the recovery evidence
        must still be readable: it is the record that the task was
        interrupted and needs a continuation assignment.
        """
        import service as service_module

        store = self.open_store("collide-agent")
        task_id = "collide"
        store._pending_receipts[task_id] = {
            "task_id": task_id,
            "state": "TASK_STATE_FAILED",
            "recovery": "native_worker_not_alive_or_identity_mismatch",
        }
        store._publish_receipt(task_id)

        receipt_path = self.state_root / "tasks" / task_id / "terminal.json"
        self.assertTrue(receipt_path.exists())

        previous_tasks_dir = service_module.TASKS_DIR
        service_module.TASKS_DIR = self.state_root / "tasks"
        try:
            writer = getattr(service_module.RegisteredJobExecutor(),
                             "_write_terminal_receipt", None)
            if writer is not None:
                writer(task_id, "TASK_STATE_COMPLETED")
            else:
                # The shape the executor used before the merge existed: the
                # file was replaced wholesale.  This branch is what makes the
                # assertion below a genuine regression check rather than an
                # assertion about one particular implementation.
                runner.atomic_json(receipt_path, {
                    "task_id": task_id, "state": "TASK_STATE_COMPLETED",
                    "finished_at": runner.now()})
        finally:
            service_module.TASKS_DIR = previous_tasks_dir

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            receipt.get("recovery"), "native_worker_not_alive_or_identity_mismatch",
            "the executor's receipt erased the recovery evidence",
        )
        self.assertEqual(receipt["task_id"], task_id)


if __name__ == "__main__":
    unittest.main()
