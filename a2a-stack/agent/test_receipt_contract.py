"""Regression tests for the terminal-receipt contract.

One file per task, `terminal.json`, is published by two writers:

  * the task store's recovery and monitor passes, which commit
    TASK_STATE_FAILED and then publish the receipt carrying the recovery
    evidence; and
  * the job executor's finally-hook, which publishes its own terminal state.

Both writers commit to the same database row, so the database has a single
authoritative terminal state and a single last writer.  The receipt must
agree with it.  A receipt claiming FAILED for a task the database calls
COMPLETED sends an agent after the wrong repair: the delivery owner reads
the receipt to decide whether to replay the work or to accept it.

The recovery evidence is the operational statement "this task was
interrupted; create a continuation assignment instead of replaying it".
That instruction is only true while the task is still FAILED, so the
evidence is retained only while the database agrees with it.

These tests are offline: no model, provider, HTTP or live host calls.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "a2a-stack" / "agent"))
sys.path.insert(0, str(ROOT / "a2a-stack" / "runtime"))
sys.path.insert(0, str(ROOT / "a2a-stack"))
import runner  # noqa: E402
import service as service_module  # noqa: E402
import task_store as task_store_module  # noqa: E402
from task_store import TASK_STATE_NAMES, create_task_store  # noqa: E402


def make_task(task_id: str, state: int) -> Task:
    return Task(id=task_id, context_id=f"ctx-{task_id}", status=TaskStatus(state=state))


class ReceiptContractTests(unittest.IsolatedAsyncioTestCase):
    """The receipt must describe the state the database actually holds."""

    async def asyncSetUp(self):
        scratch = ROOT / "tmp" / "review-uncommitted-20261104" / "receipt-worker"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.state_root = Path(self.tmp.name)
        self.context = ServerCallContext()
        self.stores = []
        self.previous_tasks_dir = service_module.TASKS_DIR
        service_module.TASKS_DIR = self.state_root / "tasks"
        self.addCleanup(self._restore)

    def _restore(self):
        service_module.TASKS_DIR = self.previous_tasks_dir

    async def asyncTearDown(self):
        for store in self.stores:
            try:
                await store.close()
            except Exception:  # noqa: BLE001 - every store must still be closed
                pass
        self.stores.clear()
        self.tmp.cleanup()

    def open_store(self, agent_key: str):
        store = create_task_store(self.state_root, agent_key)
        self.stores.append(store)
        return store

    def receipt(self, task_id: str) -> dict:
        path = self.state_root / "tasks" / task_id / "terminal.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def receipt_path(self, task_id: str) -> Path:
        return self.state_root / "tasks" / task_id / "terminal.json"

    # -- the store publishes the receipt ----------------------------------- #
    async def test_the_store_publishes_the_receipt_when_it_commits_a_terminal_state(self):
        """A terminal commit must leave a receipt behind.

        Without this the receipt exists only if the executor's finally-hook
        happens to run, and a task the host failed on its own would leave
        nothing for the owner to read.
        """
        store = self.open_store("publish-agent")
        task_id = "published"

        await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)

        self.assertTrue(self.receipt_path(task_id).exists(),
                        "the terminal commit left no receipt")
        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED")
        self.assertEqual(receipt["task_id"], task_id)

    async def test_idle_store_retries_transient_terminal_receipt_failure(self):
        store = self.open_store("idle-retry-agent")
        task_id = "idle-retry"
        original = task_store_module._atomic_json
        failed = False

        def fail_once(path, value):
            nonlocal failed
            if path.name == "terminal.json" and not failed:
                failed = True
                raise OSError(28, "transient receipt failure")
            return original(path, value)

        with patch.object(task_store_module, "_atomic_json", fail_once):
            await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        self.assertTrue(failed)
        deadline = asyncio.get_running_loop().time() + 5
        while not self.receipt_path(task_id).exists() and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.05)
        self.assertEqual(self.receipt(task_id)["state"], "TASK_STATE_COMPLETED")

    async def test_terminal_save_restarts_receipt_retry_after_monitor_has_exited(self):
        store = self.open_store("exited-monitor-agent")
        task_id = "exited-monitor"
        async def finished_monitor():
            return None

        store._monitor_task = asyncio.create_task(finished_monitor())
        await store._monitor_task
        original_atomic = task_store_module._atomic_json
        original_save = DatabaseTaskStore.save
        attempts = 0
        fail_once = True

        async def count_save(base_store, task, context):
            nonlocal attempts
            attempts += 1
            return await original_save(base_store, task, context)

        def fail_receipt_once(path, value):
            nonlocal fail_once
            if path.name == "terminal.json" and fail_once:
                fail_once = False
                raise OSError(28, "transient receipt failure")
            return original_atomic(path, value)

        with patch.object(DatabaseTaskStore, "save", count_save), \
                patch.object(task_store_module, "_atomic_json", fail_receipt_once):
            await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
            deadline = asyncio.get_running_loop().time() + 5
            while not self.receipt_path(task_id).exists() and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.05)

        self.assertEqual(attempts, 1, "receipt retry repeated the task's database side effect")
        self.assertEqual(self.receipt(task_id)["state"], "TASK_STATE_COMPLETED")
        task = await store.get(task_id, self.context)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_COMPLETED)

    async def test_failed_monitor_rearms_pending_receipt_without_another_save(self):
        """A crashed monitor must retry its receipt from the committed row."""
        store = self.open_store("crashed-monitor-agent")
        task_id = "crashed-monitor"
        original_atomic = task_store_module._atomic_json
        original_save = DatabaseTaskStore.save
        saves = 0
        fail_receipts = True

        async def count_save(base_store, task, context):
            nonlocal saves
            saves += 1
            return await original_save(base_store, task, context)

        def fault_receipts(path, value):
            if path.name == "terminal.json" and fail_receipts:
                raise OSError(28, "receipt filesystem fault")
            return original_atomic(path, value)

        with patch.object(DatabaseTaskStore, "save", count_save), \
                patch.object(task_store_module, "_atomic_json", fault_receipts):
            await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
            crashed = store._monitor_task
            self.assertIsNotNone(crashed, "terminal receipt failure did not arm monitor")
            with patch.object(store, "_retry_pending_receipts",
                              side_effect=RuntimeError("injected monitor crash")):
                await asyncio.gather(crashed, return_exceptions=True)
            await asyncio.sleep(0)
            self.assertIn(task_id, store._pending_receipts)
            fail_receipts = False

            deadline = asyncio.get_running_loop().time() + 5
            while (not self.receipt_path(task_id).exists()
                   and asyncio.get_running_loop().time() < deadline):
                await asyncio.sleep(0.02)

        self.assertTrue(self.receipt_path(task_id).exists(),
                        "monitor recovery did not publish its pending receipt")
        self.assertEqual(self.receipt(task_id)["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(saves, 1, "receipt recovery replayed the task database save")

    async def test_monitor_rearm_ignores_stale_callback_and_close_cancellation(self):
        store = self.open_store("monitor-lifecycle-agent")
        task_id = "lifecycle"
        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_COMPLETED"}

        async def blocked_monitor():
            await asyncio.Event().wait()

        active = asyncio.create_task(blocked_monitor())
        store._monitor_task = active
        active.add_done_callback(store._on_monitor_done)
        store._on_monitor_done(asyncio.create_task(asyncio.sleep(0)))
        await asyncio.sleep(0)
        self.assertIs(store._monitor_task, active,
                      "a stale completion callback replaced the active monitor")

        await store.close()
        self.assertIsNone(store._monitor_task)
        self.assertTrue(active.cancelled(), "close did not cancel the active monitor")
        self.assertTrue(store._closing)

    async def test_normal_monitor_exit_rearms_outstanding_work(self):
        store = self.open_store("normal-monitor-exit-agent")
        task_id = "normal-exit"
        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_COMPLETED"}

        async def normal_exit():
            return None

        monitor = asyncio.create_task(normal_exit())
        store._monitor_task = monitor
        monitor.add_done_callback(store._on_monitor_done)
        await monitor
        await asyncio.sleep(0)

        replacement = store._monitor_task
        self.assertIsNotNone(replacement,
                             "normal monitor exit stranded outstanding receipt work")
        self.assertIsNot(replacement, monitor,
                         "normal monitor exit did not start a replacement")
        await store.close()

    async def test_restart_reconciles_committed_terminal_state_without_replaying_work(self):
        task_id = "restart-receipt"
        first = self.open_store("restart-agent")
        original = task_store_module._atomic_json
        original_save = DatabaseTaskStore.save
        saves = 0

        async def count_save(base_store, task, context):
            nonlocal saves
            saves += 1
            return await original_save(base_store, task, context)

        def fail_receipt(path, value):
            if path.name == "terminal.json":
                raise OSError(28, "receipt unavailable through shutdown")
            return original(path, value)

        with patch.object(task_store_module, "_atomic_json", fail_receipt), \
                patch.object(DatabaseTaskStore, "save", count_save):
            await first.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
            await first.close()
        self.stores.remove(first)
        restarted = self.open_store("restart-agent")
        with patch.object(DatabaseTaskStore, "save", count_save):
            task = await restarted.get(task_id, self.context)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(self.receipt(task_id)["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(saves, 1, "restart receipt reconciliation repeated the task save")

    async def test_superseding_terminal_commit_replaces_failed_pending_receipt(self):
        store = self.open_store("supersede-pending-agent")
        task_id = "supersede-pending"
        original = task_store_module._atomic_json
        fail_once = True

        def fail_first(path, value):
            nonlocal fail_once
            if path.name == "terminal.json" and fail_once:
                fail_once = False
                raise OSError(28, "transient receipt failure")
            return original(path, value)

        with patch.object(task_store_module, "_atomic_json", fail_first):
            await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)
            self.assertIn(task_id, store._pending_receipts)
            await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        receipt = self.receipt(task_id)
        task = await store.get(task_id, self.context)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")
        self.assertNotIn("recovery", receipt)
        self.assertNotIn(task_id, store._pending_receipts)

    async def test_the_receipt_state_always_matches_the_database(self):
        """The receipt is a mirror of the authoritative state."""
        store = self.open_store("mirror-agent")
        task_id = "mirror"

        for state in (TaskState.TASK_STATE_FAILED, TaskState.TASK_STATE_COMPLETED):
            await store.save(make_task(task_id, state), self.context)
            task = await store.get(task_id, self.context)
            receipt = self.receipt(task_id)
            self.assertEqual(
                receipt["state"], TASK_STATE_NAMES.get(task.status.state),
                f"the receipt contradicts the database for {state}")

    async def test_a_non_terminal_commit_leaves_no_receipt(self):
        """An in-flight task has no terminal outcome to publish."""
        store = self.open_store("inflight-agent")
        task_id = "inflight"

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        self.assertFalse(self.receipt_path(task_id).exists(),
                         "a receipt was published for a task that is still in flight")

    # -- the recovery evidence ---------------------------------------------- #
    async def test_the_recovery_evidence_is_kept_while_the_task_is_failed(self):
        store = self.open_store("evidence-agent")
        task_id = "evidence"
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "monitored_native_worker_exited_without_terminal_task_result",
        }

        await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)

        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED")
        self.assertEqual(
            receipt.get("recovery"),
            "monitored_native_worker_exited_without_terminal_task_result",
            "the recovery evidence was dropped while the task is still FAILED")

    async def test_the_recovery_evidence_is_dropped_once_a_later_commit_supersedes_it(self):
        """A completed task must not carry live-looking replay guidance.

        The recovery field tells the owner to create a continuation
        assignment instead of replaying the task.  That is wrong advice for
        a task the database now calls COMPLETED, so the evidence is
        superseded history rather than an instruction.
        """
        store = self.open_store("superseded-agent")
        task_id = "superseded"
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "monitored_native_worker_exited_without_terminal_task_result",
        }
        store._publish_receipt(task_id, "TASK_STATE_FAILED")
        self.assertEqual(
            self.receipt(task_id).get("recovery"),
            "monitored_native_worker_exited_without_terminal_task_result")

        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)

        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")
        self.assertNotIn(
            "recovery", receipt,
            "a completed task still carries the instruction to replay it")

    # -- the executor's write ----------------------------------------------- #
    async def test_the_executors_write_does_not_overwrite_the_published_state(self):
        """The executor's opinion is local; the host's record is authority.

        The executor's finally-hook runs before the request handler has
        persisted the terminal event, so its write is provisional.  It must
        never overwrite a state the store has already published.
        """
        store = self.open_store("executor-agent")
        task_id = "executor"
        await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)

        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_COMPLETED")

        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED",
                         "the executor overwrote the published state")
        task = await store.get(task_id, self.context)
        self.assertEqual(receipt["state"],
                         TASK_STATE_NAMES.get(task.status.state),
                         "the receipt contradicts the database")

    async def test_the_executors_write_supplies_the_receipt_when_none_was_published(self):
        """The receipt must not be empty just because the store was not the writer."""
        task_id = "supplied"
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_COMPLETED")

        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(receipt["task_id"], task_id)

    async def test_the_executors_write_cannot_clobber_a_published_state(self):
        """The publish must be exclusive, not a read-modify-write.

        A read-modify-write reads the receipt, builds a new one and writes
        it.  If the store publishes between that read and that write, the
        executor's write lands last and overwrites the authoritative state
        with the executor's stale opinion.  The publish must therefore be
        exclusive: it wins only when there is no receipt yet.
        """
        store = self.open_store("clobber-agent")
        task_id = "clobber"

        # The store publishes the authoritative state first.
        store._publish_receipt(task_id, "TASK_STATE_COMPLETED")

        # The executor then writes its own provisional state.
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_FAILED")

        receipt = self.receipt(task_id)
        self.assertEqual(
            receipt["state"], "TASK_STATE_COMPLETED",
            "the executor's write clobbered the state the store published")

    async def test_the_executors_write_leaves_no_staging_residue(self):
        """A provisional receipt must not leave a temp file behind."""
        task_id = "residue"
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_COMPLETED")

        task_dir = self.state_root / "tasks" / task_id
        self.assertEqual(
            sorted(path.name for path in task_dir.iterdir()),
            ["terminal.json"],
            "the executor's publish left staging files behind")

    async def test_the_executors_write_does_not_revive_dropped_recovery_evidence(self):
        store = self.open_store("no-revive-agent")
        task_id = "no-revive"
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "native_worker_not_alive_or_identity_mismatch",
        }
        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        self.assertNotIn("recovery", self.receipt(task_id))

        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_FAILED")

        receipt = self.receipt(task_id)
        self.assertNotIn(
            "recovery", receipt,
            "the executor revived evidence the host had superseded")
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")

    # -- the deferred publication ------------------------------------------- #
    async def test_a_deferred_receipt_is_published_with_the_database_state(self):
        """A receipt whose write failed is retried against the live state.

        The pending receipt says the task was interrupted, but the task may
        since have been finished by its own executor.  Publishing the
        pending claim would say FAILED for a task the database calls
        COMPLETED.
        """
        store = self.open_store("deferred-agent")
        task_id = "deferred"
        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        self.assertTrue(self.receipt_path(task_id).exists())

        # The task is later failed by the host, and its receipt write fails.
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "monitored_native_worker_exited_without_terminal_task_result",
        }
        with patch.object(task_store_module, "_atomic_json",
                          side_effect=OSError(28, "No space left on device")):
            with self.assertRaises(OSError):
                store._publish_receipt(task_id, "TASK_STATE_FAILED")

        # The pending receipt is retried.  The database says COMPLETED, so
        # the published receipt must say COMPLETED.
        await store._retry_pending_receipts(self.context)

        receipt = self.receipt(task_id)
        task = await store.get(task_id, self.context)
        self.assertEqual(receipt["state"], TASK_STATE_NAMES.get(task.status.state),
                         "the retried receipt contradicts the database")
        self.assertNotIn("recovery", receipt,
                         "the retried receipt revived superseded evidence")

    async def test_a_deferred_receipt_is_not_published_for_a_task_in_flight(self):
        """An in-flight task has no terminal state to publish."""
        store = self.open_store("inflight-deferred-agent")
        task_id = "inflight-deferred"
        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "native_worker_not_alive_or_identity_mismatch",
        }
        await store._retry_pending_receipts(self.context)

        self.assertFalse(self.receipt_path(task_id).exists(),
                         "a receipt was published for a task that is still in flight")


class ReceiptWithdrawalTests(unittest.IsolatedAsyncioTestCase):
    """A terminal outcome is final, and its receipt is never destroyed.

    The SDK's legacy task store is last-writer-wins with no terminal guard,
    so a stale in-flight event can arrive after the terminal commit.  The
    store refuses that regression, so the database row stays terminal and
    the receipt published for the terminal commit survives.

    A receipt is withdrawn only where the host has verified the native
    worker is ALIVE and has re-committed the task as genuinely in flight.
    """

    async def asyncSetUp(self):
        scratch = ROOT / "tmp" / "a2a-stack" / "receipt-withdrawal"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.state_root = Path(self.tmp.name)
        self.context = ServerCallContext()
        self.stores = []
        self.previous_tasks_dir = service_module.TASKS_DIR
        service_module.TASKS_DIR = self.state_root / "tasks"
        self.addCleanup(self._restore)

    def _restore(self):
        service_module.TASKS_DIR = self.previous_tasks_dir

    async def asyncTearDown(self):
        for store in self.stores:
            try:
                await store.close()
            except Exception:  # noqa: BLE001
                pass
        self.stores.clear()
        self.tmp.cleanup()

    def open_store(self, agent_key: str):
        store = create_task_store(self.state_root, agent_key)
        self.stores.append(store)
        return store

    def receipt(self, task_id: str) -> dict:
        path = self.state_root / "tasks" / task_id / "terminal.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def receipt_path(self, task_id: str) -> Path:
        return self.state_root / "tasks" / task_id / "terminal.json"

    def retired(self, task_id: str) -> dict:
        path = self.state_root / "control" / "task-store-retired-receipts.json"
        stored = json.loads(path.read_text(encoding="utf-8"))
        for entry in stored["retired"]:
            if entry["task_id"] == task_id:
                return entry
        raise AssertionError(f"no retired receipt was recorded for {task_id}")

    async def test_a_terminal_task_does_not_return_to_in_flight(self):
        """The terminal state of a task is final.

        A stale in-flight event arriving after the terminal commit would
        otherwise move the row back into flight, which would invalidate the
        receipt published for that commit and leave the owner with no
        truthful record of the outcome.
        """
        store = self.open_store("monotonic-agent")
        task_id = "monotonic"

        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)
        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        task = await store.get(task_id, self.context)
        self.assertEqual(
            TASK_STATE_NAMES.get(task.status.state), "TASK_STATE_COMPLETED",
            "a stale in-flight commit moved a terminal task back into flight")
        self.assertTrue(self.receipt_path(task_id).exists(),
                        "the terminal receipt was destroyed by a stale in-flight commit")
        receipt = self.receipt(task_id)
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")
        self.assertEqual(
            receipt["state"], TASK_STATE_NAMES.get(task.status.state),
            "the receipt contradicts the database")

    async def test_a_terminal_receipt_survives_a_later_in_flight_save(self):
        """The authoritative receipt must never be deleted by an in-flight save.

        The receipt is the artifact the delivery owner reads.  A later
        in-flight save for the same task id is a stale event; it must not
        destroy the record of the outcome the database already holds.
        """
        store = self.open_store("survive-agent")
        task_id = "survives"

        await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)
        self.assertTrue(self.receipt_path(task_id).exists())

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        self.assertTrue(
            self.receipt_path(task_id).exists(),
            "a stale in-flight save destroyed the authoritative terminal receipt")
        receipt = self.receipt(task_id)
        task = await store.get(task_id, self.context)
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED")
        self.assertEqual(receipt["state"], TASK_STATE_NAMES.get(task.status.state))

    async def test_the_recovery_evidence_survives_a_later_in_flight_save(self):
        """The interruption evidence must not be destroyed by a stale save.

        The recovery evidence is the record that the host found the task
        interrupted.  An in-flight save cannot make that history untrue, so
        the evidence must remain readable.
        """
        store = self.open_store("evidence-agent")
        task_id = "evidence-survives"
        store._pending_receipts[task_id] = {
            "task_id": task_id, "state": "TASK_STATE_FAILED",
            "recovery": "native_worker_not_alive_or_identity_mismatch",
        }
        await store.save(make_task(task_id, TaskState.TASK_STATE_FAILED), self.context)
        self.assertEqual(
            self.receipt(task_id).get("recovery"),
            "native_worker_not_alive_or_identity_mismatch")

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        self.assertEqual(
            self.receipt(task_id).get("recovery"),
            "native_worker_not_alive_or_identity_mismatch",
            "a stale in-flight save destroyed the interruption evidence")

    async def test_the_executor_provisional_receipt_survives_a_stale_in_flight_save(self):
        """The window between the executor's write and the terminal commit.

        The executor publishes its receipt before the request handler has
        persisted the terminal task event.  A stale in-flight event in that
        window must not destroy the receipt: if the host dies there, the
        receipt is the only record of the outcome.
        """
        store = self.open_store("provisional-agent")
        task_id = "provisional"

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_FAILED")
        self.assertTrue(self.receipt_path(task_id).exists(),
                        "the executor did not write its provisional receipt")

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)

        self.assertTrue(
            self.receipt_path(task_id).exists(),
            "a stale in-flight save destroyed the executor's provisional receipt")

    async def test_the_monitor_does_not_publish_failed_for_a_task_the_database_finished(self):
        """A pending receipt must not outlive the state that justified it.

        The monitor owes a receipt for a task whose worker exited.  If the
        task's own executor finished it before the monitor published, the
        receipt must describe the state the DATABASE holds.  Publishing
        FAILED would claim an interruption for a task the database calls
        COMPLETED, and would send the owner after the wrong repair.
        """
        store = self.open_store("divergence-agent")
        task_id = "divergent"

        await store.save(make_task(task_id, TaskState.TASK_STATE_COMPLETED), self.context)

        # The monitor's earlier receipt write failed, so it still owes a
        # receipt and believes the task was interrupted.
        store._pending_receipts[task_id] = {
            "task_id": task_id,
            "state": "TASK_STATE_FAILED",
            "recovery": "monitored_native_worker_exited_without_terminal_task_result",
        }

        await store._report_interrupted_task(task_id, self.context)

        receipt = self.receipt(task_id)
        task = await store.get(task_id, self.context)
        self.assertEqual(
            receipt["state"], TASK_STATE_NAMES.get(task.status.state),
            "the receipt contradicts the database")
        self.assertEqual(receipt["state"], "TASK_STATE_COMPLETED")
        self.assertNotIn(
            "recovery", receipt,
            "the receipt carries interruption guidance for a completed task")

    async def test_the_recovery_pass_withdraws_the_receipt_of_a_live_task(self):
        """The recovery pass retires a receipt for a task it found alive.

        The host died between the executor's write and the terminal commit.
        The recovery pass finds the native worker alive, re-commits the task
        as working, and retires the receipt that now contradicts the
        database.  The retirement is recorded, so the host's claim is not
        lost without a trace.
        """
        store = self.open_store("recovery-agent")
        task_id = "recovered"

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_FAILED")

        # The native worker is still running, so the recovery pass takes its
        # alive branch and re-commits the task as working.
        worker = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"])
        def stop_worker():
            if worker.poll() is None:
                worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=10)
        self.addCleanup(stop_worker)
        task_dir = self.state_root / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "process.json").write_text(json.dumps({
            "pid": worker.pid,
            "process_token": runner.process_token(worker.pid),
        }), encoding="utf-8")

        # A fresh store over the same database is a host restart: its
        # recovery pass has not run yet, so it really does sweep the task.
        restarted = self.open_store("recovery-agent")
        await restarted._recover_once(self.context)

        self.assertFalse(
            self.receipt_path(task_id).exists(),
            "the recovery pass left a terminal receipt on a live task")

    async def test_a_retired_receipt_is_recorded_rather_than_silently_dropped(self):
        """A retired claim must leave a trace.

        The receipt the recovery pass retires had claimed a terminal outcome
        for a task the database calls in flight.  The claim is retired, not
        deleted: an operator reading the record later must be able to see
        that the claim was made and why it was retired.
        """
        store = self.open_store("retired-agent")
        task_id = "retired"

        await store.save(make_task(task_id, TaskState.TASK_STATE_WORKING), self.context)
        service_module.RegisteredJobExecutor()._write_terminal_receipt(
            task_id, "TASK_STATE_FAILED")

        worker = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"])
        def stop_worker():
            if worker.poll() is None:
                worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait(timeout=10)
        self.addCleanup(stop_worker)
        task_dir = self.state_root / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "process.json").write_text(json.dumps({
            "pid": worker.pid,
            "process_token": runner.process_token(worker.pid),
        }), encoding="utf-8")

        restarted = self.open_store("retired-agent")
        await restarted._recover_once(self.context)

        entry = self.retired(task_id)
        self.assertEqual(entry["retired_state"], "TASK_STATE_FAILED")
        self.assertIn("retired_at", entry)

    async def test_an_outstanding_claim_is_recorded_when_there_is_no_receipt_to_retire(self):
        """The host's outstanding claim must never be dropped without a trace.

        A claim can be outstanding while no receipt file exists, because the
        receipt write failed earlier.  Retiring the claim must still leave a
        record: the host observed an interruption, and that observation is
        history whether or not a receipt ever reached the disk.
        """
        store = self.open_store("claim-agent")
        task_id = "claim"
        store._pending_receipts[task_id] = {
            "task_id": task_id,
            "state": "TASK_STATE_FAILED",
            "recovery": "native_worker_not_alive_or_identity_mismatch",
        }

        store._withdraw_receipt(task_id)

        self.assertNotIn(task_id, store._pending_receipts,
                         "the outstanding claim was not retired")
        entry = self.retired(task_id)
        self.assertEqual(entry["pending_state"], "TASK_STATE_FAILED")
        self.assertEqual(
            entry["pending_recovery"], "native_worker_not_alive_or_identity_mismatch")


if __name__ == "__main__":
    unittest.main()
