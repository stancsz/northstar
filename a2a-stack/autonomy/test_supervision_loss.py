"""Regression tests for loss of a goal's supervisor watcher.

A watcher that dies with an unhandled exception used to end silently: no host
event recorded the loss, state.json kept saying RUNNING, and the goal report
told the user the agent was autonomously executing with no manual rescue
needed, while nothing was supervising the goal and nothing could relaunch its
controller.

These tests are offline: no model, provider, HTTP or live host calls.
"""
from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import json
import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


STACK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("supervision_loss_manager", STACK / "autonomy/manager.py")
manager_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager_module)
SCRATCH = Path(__file__).resolve().parents[2] / "tmp/review-uncommitted-20261104/supervision-worker"


class FakeProcess:
    def __init__(self):
        self.pid = 4242
        self.code = 1

    def wait(self):
        return self.code

    def poll(self):
        return self.code

    def kill(self):
        self.code = 1


class FakeJob:
    def assign(self, process):
        pass

    def close(self):
        pass


class SupervisionLossTests(unittest.IsolatedAsyncioTestCase):
    """The watcher must not die silently, and the report must not lie."""

    async def asyncSetUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.state_root = self.root / "host-state"
        self.state_root.mkdir()
        self.manager = manager_module.GoalManager(self.state_root, self.workspace)
        self._hold_process_boundaries()
        # This manager's watchers live on this test's event loop, so it is
        # closed from this loop rather than from a separate one.
        self.addCleanup(self._close_manager)
        self.goal_id = "g-" + "d" * 32
        self.directory = self.manager._dir(self.goal_id)
        self.directory.mkdir(parents=True)
        self.state_path = self.directory / "state.json"
        self.spec_path = self.directory / "spec.json"
        self.journal_path = self.directory / "host-events.jsonl"
        self.real_atomic = manager_module.runtime.atomic_json
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "RUNNING", "session_id": None, "recovery_count": 0})
        self.real_atomic(self.spec_path, {
            "id": self.goal_id, "workspace": str(self.workspace),
            "goal": "Supervise this goal", "acceptance": ["stays supervised"], "checks": []})

    def events(self):
        if not self.journal_path.exists():
            return []
        return [json.loads(line) for line in
                self.journal_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    async def _close_manager(self):
        self.manager.closing = True
        watchers = list(self.manager.watchers.values())
        for watcher in watchers:
            watcher.cancel()
        for watcher in watchers:
            try:
                await watcher
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

    def _hold_process_boundaries(self):
        """Keep the controller's process boundary fake for the whole test.

        A watcher is a background task: its body runs on a later event-loop
        turn, so a patch scoped to the call that started it is already gone
        by the time the watcher reaches `subprocess.Popen`.  The watcher then
        spawns a real controller that inherits `runner-stderr.log`, and the
        temporary directory cannot be removed while that child holds the
        handle.  Holding the boundary for the whole test keeps the watcher
        from ever leaving this process.
        """
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(manager_module.runtime, "Job", FakeJob))
        stack.enter_context(patch.object(manager_module.subprocess, "Popen",
                                         side_effect=lambda *a, **k: FakeProcess()))
        stack.enter_context(patch.object(manager_module.runtime, "process_token",
                                         return_value="fixture-token"))
        self.addCleanup(stack.close)

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    async def test_assignment_failure_keeps_live_controller_owned_for_cancel(self):
        class LiveProcess(FakeProcess):
            def __init__(self):
                super().__init__()
                self.code = None

        class FailingJob(FakeJob):
            def assign(self, process):
                raise OSError("injected assignment failure")

        process = LiveProcess()
        with patch.object(manager_module.runtime, "Job", FailingJob), \
                patch.object(manager_module.subprocess, "Popen", return_value=process):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)
            self.assertIs(self.manager.processes[self.goal_id][0], process)
            self.assertIsNone(process.poll())
            await self.manager.cancel(self.goal_id)
            await asyncio.wait_for(self.manager.cancel_watchers[self.goal_id], timeout=3)
        self.assertIsNotNone(process.poll())
        self.assertNotIn(self.goal_id, self.manager.processes)
        self.assertEqual(self.state()["status"], "CANCELED")

    async def run_watcher_with_publish_failure(self, error):
        """Run a watcher whose recovery publish fails once, then recovers."""
        real_atomic = self.real_atomic
        fault = {"active": True}

        def atomic(path, value):
            if path == self.state_path and value.get("status") == "RECOVERING" and fault["active"]:
                fault["active"] = False
                raise error
            return real_atomic(path, value)

        with patch.object(manager_module.runtime, "Job", FakeJob), \
                patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FakeProcess()), \
                patch.object(manager_module.runtime, "process_token", return_value="fixture-token"), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            for _ in range(100):
                await asyncio.sleep(.02)
                if self.state().get("host_restart_count", 0) > 0:
                    break
            await self.manager.cancel(self.goal_id)
            cleanup = self.manager.cancel_watchers[self.goal_id]
            await asyncio.wait_for(cleanup, timeout=5)
            return task

    async def run_uncertain_wait_failure(self, error):
        """A launched controller exists, but host wait cannot establish outcome."""
        class FailedWaitProcess(FakeProcess):
            def wait(self):
                raise error

        with patch.object(manager_module.subprocess, "Popen",
                          side_effect=lambda *a, **k: FailedWaitProcess()):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

    async def test_watcher_loss_records_a_host_event(self):
        denied = OSError("synthetic transient write error")
        await self.run_watcher_with_publish_failure(denied)
        names = [event["event"] for event in self.events()]
        self.assertIn("host_snapshot_recovery", names)

    async def test_watcher_loss_does_not_leave_the_goal_claiming_autonomous_progress(self):
        denied = OSError("synthetic transient write error")
        await self.run_watcher_with_publish_failure(denied)

        for _ in range(100):
            await asyncio.sleep(.02)
            if self.state().get("status") == "CANCELED":
                break
        report = self.manager.report(self.goal_id)
        self.assertFalse(report["supervision_lost"])
        self.assertEqual(report["status"], "CANCELED")
        self.assertFalse(report["controller_running"])

    async def test_watcher_loss_marks_the_goal_unsupervised_in_persisted_state(self):
        disk_full = OSError(28, "temporary disk error")
        await self.run_watcher_with_publish_failure(disk_full)

        for _ in range(100):
            await asyncio.sleep(.02)
            if self.state().get("status") == "CANCELED":
                break
        state = self.state()
        self.assertEqual(state["status"], "CANCELED")
        self.assertEqual(state["id"], self.goal_id)

    async def test_report_detects_loss_even_when_the_state_write_also_failed(self):
        """Uncertain execution is reported even if its first state write fails."""
        real_atomic = self.real_atomic
        failed = {"active": True}

        def atomic(path, value):
            if path == self.state_path and value.get("host_suspended") and failed["active"]:
                failed["active"] = False
                raise OSError(28, "temporary disk error")
            return real_atomic(path, value)

        class FailedWait(FakeProcess):
            def wait(inner_self):
                raise OSError("uncertain host wait failure")

        with patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FailedWait()), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            await asyncio.wait_for(task, timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertTrue(report["supervision_lost"])
        self.assertEqual(report["status"], "NEEDS_USER")
        self.assertEqual(report["blocker"]["kind"], "host_outcome_uncertain")
        self.assertNotIn("自主执行，无需手动救场", report["next_user_action"])

    async def test_explicit_resume_clears_the_supervision_loss(self):
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "NEEDS_USER", "session_id": None,
            "recovery_count": 0, "supervision_lost": True,
            "supervision_lost_reason": "fixture"})
        resumed = await self.manager.resume(self.goal_id)

        self.assertEqual(resumed["state"]["status"], "RUNNING")
        self.assertNotIn("supervision_lost", resumed["state"])

    async def test_normal_watcher_exit_is_not_a_supervision_loss(self):
        """A watcher that returns normally (terminal goal) is not a loss."""
        self.real_atomic(self.state_path, {"id": self.goal_id, "status": "COMPLETE"})

        with patch.object(manager_module.runtime, "Job", FakeJob), \
                patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FakeProcess()), \
                patch.object(manager_module.runtime, "process_token", return_value="fixture-token"):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            await asyncio.wait([task], timeout=15)

        self.assertTrue(task.done())
        self.assertIsNone(task.exception())
        self.assertNotIn("host_supervision_lost", [event["event"] for event in self.events()])
        report = self.manager.report(self.goal_id)
        self.assertFalse(report["supervision_lost"])
        self.assertEqual(report["status"], "COMPLETE")

    async def test_completed_goal_is_not_downgraded_when_its_watcher_dies(self):
        """A finished goal keeps its accepted result; nothing still needs supervising."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "COMPLETE", "session_id": None,
            "recovery_count": 0, "last_summary": "Accepted result"})

        report = self.manager.report(self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Accepted result")
        self.assertFalse(report["supervision_lost"])

    async def test_cancelled_watcher_is_not_a_supervision_loss(self):
        real_atomic = self.real_atomic
        fault = {"active": True}

        def atomic(path, value):
            if path == self.state_path and value.get("status") == "RECOVERING" and fault["active"]:
                fault["active"] = False
                real_atomic(path, value)
                raise asyncio.CancelledError()
            return real_atomic(path, value)

        with patch.object(manager_module.runtime, "Job", FakeJob), \
                patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FakeProcess()), \
                patch.object(manager_module.runtime, "process_token", return_value="fixture-token"), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            await asyncio.wait([task], timeout=15)

        self.assertTrue(task.done())
        self.assertTrue(task.cancelled())
        self.assertNotIn("host_supervision_lost", [event["event"] for event in self.events()])
        self.assertFalse(self.manager.report(self.goal_id)["supervision_lost"])

    async def test_a_loss_from_a_superseded_watcher_does_not_undo_a_resume(self):
        """A stale loss callback cannot undo a newer same-goal resume."""
        denied = PermissionError("synthetic non-recoverable access error")
        denied.winerror = 87
        await self.run_watcher_with_publish_failure(OSError("transient failure"))

        # A resume installs a fresh watcher for the goal.
        cleanup = self.manager.cancel_watchers[self.goal_id]
        await asyncio.wait_for(cleanup, timeout=3)
        await self.manager.resume(self.goal_id)

        # A loss belonging to a watcher that no longer owns the goal is
        # history, and must not be applied to the goal's current state.
        self.manager._record_supervision_loss(self.goal_id, _FailedWatcher())

        report = self.manager.report(self.goal_id)
        self.assertFalse(report["supervision_lost"],
                         "a superseded watcher's loss undid the owner's resume")
        self.assertEqual(report["status"], "RUNNING")

    async def test_a_completed_goal_is_not_downgraded_when_its_watcher_dies_with_an_exception(self):
        """A finished goal keeps its accepted result even if its watcher dies.

        The watcher must reach the publish failure, so the goal is completed
        AFTER the watcher has started rather than before it.
        """
        real_atomic = self.real_atomic
        fault = {"active": True}

        def atomic(path, value):
            if path == self.state_path and value.get("status") == "RECOVERING" and fault["active"]:
                # The goal completes before the publish is attempted, so the
                # recovery write fails once against an already-completed goal.
                fault["active"] = False
                real_atomic(path, {"id": self.goal_id, "status": "COMPLETE",
                                   "last_summary": "Accepted result"})
                raise OSError("temporary recovery publish failure")
            return real_atomic(path, value)

        with patch.object(manager_module.runtime, "Job", FakeJob), \
                patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FakeProcess()), \
                patch.object(manager_module.runtime, "process_token", return_value="fixture-token"), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            await asyncio.wait([task], timeout=15)

        self.assertTrue(task.done())
        self.assertIsNone(task.exception())
        report = self.manager.report(self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Accepted result")
        self.assertFalse(report["supervision_lost"],
                         "a completed goal was downgraded by a watcher that died afterwards")

    async def test_the_report_states_that_supervision_was_lost_and_why(self):
        """Legacy persisted loss reports never claim external dependency."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "NEEDS_USER", "session_id": None,
            "recovery_count": 0, "supervision_lost": True,
            "supervision_lost_reason": "OSError: prior supervisor stopped",
            "blocker": {"kind": "host_supervision_lost", "evidence": ["prior host loss"]}})

        report = self.manager.report(self.goal_id)
        self.assertTrue(report["supervision_lost"])
        self.assertEqual(report["status"], "NEEDS_USER")
        self.assertIn("supervision_lost_reason", report)
        self.assertIsNotNone(report["supervision_lost_reason"])
        self.assertNotEqual(report["next_user_action"],
                            "处理报告中的已核实外部依赖后，调用 resume_goal。",
                            "the report still claims a verified external dependency")
        self.assertIsNotNone(report["blocker"],
                             "a supervision-lost goal must name its own blocker")

    async def test_a_completed_goal_is_not_hidden_behind_a_stale_supervision_loss_flag(self):
        """An accepted result must not be hidden by a leftover loss flag.

        `NEEDS_USER` is itself in the terminal set, so the loss check cannot
        simply be short-circuited by any terminal status.  A goal that
        reached COMPLETE must keep its accepted result even if a supervision
        loss was recorded before it completed.
        """
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "COMPLETE", "session_id": None,
            "recovery_count": 0, "last_summary": "Accepted result",
            "supervision_lost": True, "supervision_lost_at": "2026-11-04T00:00:00+00:00"})

        report = self.manager.report(self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Accepted result")
        self.assertFalse(report["supervision_lost"])

    async def test_the_report_names_the_cause_even_when_the_durable_write_also_failed(self):
        """The report must not point at a reason it does not contain.

        When the durable loss write fails there is no persisted cause, so the
        report has to derive it from the live watcher.  Otherwise the action
        text tells the owner to handle a reason that is not in the report.
        """
        denied = PermissionError("synthetic non-recoverable access error")
        denied.winerror = 87
        real_atomic = self.real_atomic
        fault = {"active": True}

        def atomic(path, value):
            if path == self.state_path and value.get("host_suspended") and fault["active"]:
                fault["active"] = False
                raise OSError(28, "No space left on device")
            return real_atomic(path, value)

        class FailedWait(FakeProcess):
            def wait(inner_self):
                raise OSError("uncertain host wait failure")

        with patch.object(manager_module.subprocess, "Popen", side_effect=lambda *a, **k: FailedWait()), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            task = self.manager.watchers[self.goal_id]
            await asyncio.wait_for(task, timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertTrue(report["supervision_lost"])
        self.assertEqual(report["status"], "NEEDS_USER")
        self.assertEqual(report["blocker"]["kind"], "host_outcome_uncertain")
        self.assertIsNotNone(report["blocker"],
                             "a supervision-lost goal must name its own blocker")

    async def test_a_normal_needs_user_goal_keeps_the_external_dependency_guidance(self):
        """The supervision-loss copy must not leak onto ordinary blockers."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "NEEDS_USER", "session_id": None,
            "recovery_count": 0, "blocker": {"kind": "missing_external_input",
                                             "message": "Owner must supply a document",
                                             "evidence": ["document is unavailable"]}})

        report = self.manager.report(self.goal_id)
        self.assertFalse(report["supervision_lost"])
        self.assertEqual(report["status"], "NEEDS_USER")
        self.assertEqual(report["next_user_action"], "处理报告中的已核实外部依赖后，调用 resume_goal。")

    async def test_the_loss_is_recorded_even_when_the_state_file_cannot_be_read(self):
        """An ordinary read error retries until state becomes readable."""
        denied = OSError("synthetic transient state read error")
        real_read = manager_module.GoalManager._read
        state_path = self.state_path

        attempts = {"count": 0}

        def unreadable(self, path, default=None):
            if path == state_path and attempts["count"] == 0:
                attempts["count"] += 1
                raise denied
            return real_read(self, path, default)

        with patch.object(manager_module.GoalManager, "_read", unreadable):
            self.manager._launch(self.goal_id)
            watcher = self.manager.watchers[self.goal_id]
            for _ in range(100):
                await asyncio.sleep(.02)
                if self.manager.processes.get(self.goal_id):
                    break
            self.assertFalse(watcher.done())
            self.assertIn("host_recovery", [event["event"] for event in self.events()])
            await self.manager.cancel(self.goal_id)

        report = self.manager.report(self.goal_id)
        self.assertFalse(report["supervision_lost"])
        self.assertEqual(report["goal_id"], self.goal_id)

    async def test_controller_side_failure_is_not_replayed_when_outcome_is_uncertain(self):
        """`last_error` is shared with the controller and with `resume`.

        The report must name the cause of the supervision loss, not a stale
        controller error that would send the owner after the wrong problem.
        """
        starts = []
        class FailedWait(FakeProcess):
            def wait(inner_self):
                raise OSError("uncertain controller wait failure")

        with patch.object(manager_module.subprocess, "Popen",
                          side_effect=lambda *a, **k: (starts.append(1) or FailedWait())):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

        self.assertEqual(starts, [1], "uncertain controller execution was replayed")
        self.assertEqual(self.state()["id"], self.goal_id)

    async def test_a_stale_last_error_does_not_become_the_loss_reason(self):
        """A controller error left in `last_error` is not the host's cause."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "RUNNING", "session_id": None,
            "recovery_count": 0, "last_error": "controller: native worker crashed with boom"})

        starts = []
        class FailedWait(FakeProcess):
            def wait(inner_self):
                raise OSError("synthetic post-launch wait failure")

        with patch.object(manager_module.subprocess, "Popen",
                          side_effect=lambda *a, **k: (starts.append(1) or FailedWait())):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertEqual(starts, [1])
        self.assertTrue(report["supervision_lost"])
        self.assertNotIn("native worker crashed", report["blocker"]["evidence"][0])
        self.assertEqual(report["blocker"]["kind"], "host_outcome_uncertain")

    async def test_transient_cleanup_state_write_error_is_retried(self):
        """A transient state-write error keeps the cleanup operation alive."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "CANCELING", "session_id": None,
            "recovery_count": 0, "unresolved_task_ids": ["task-1"]})

        fault = {"active": True}
        real_atomic = self.real_atomic

        def atomic(path, value):
            if path == self.state_path and value.get("status") == "CANCELED" and fault["active"]:
                fault["active"] = False
                raise OSError(28, "temporary disk error")
            return real_atomic(path, value)

        with patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch_cancel(self.goal_id)
            watcher = self.manager.cancel_watchers[self.goal_id]
            for _ in range(100):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        self.assertTrue(watcher.done())
        self.assertIsNone(watcher.exception())
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(self.state()["status"], "CANCELED")
        self.assertIn("host_cancel_recovery", [event["event"] for event in self.events()])

    async def test_a_goal_stuck_in_canceling_can_be_resumed_after_the_cleanup_dies(self):
        """A dead cleanup must not leave the owner with no working operation."""
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "CANCELING", "session_id": None,
            "recovery_count": 0, "cancel_lost": True,
            "cancel_lost_reason": "OSError: No space left on device"})

        resumed = await self.manager.resume(self.goal_id)
        self.assertEqual(resumed["state"]["status"], "RUNNING")
        self.assertNotIn("cancel_lost", resumed["state"])

    async def test_transient_watcher_publish_error_recovers_without_relaunch_or_resume(self):
        """A transient watcher fault recovers and the original goal completes."""
        fault = {"active": True}
        process_starts = []
        real_read = manager_module.GoalManager._read

        def read(manager, path, default=None):
            if path == self.state_path and fault["active"]:
                fault["active"] = False
                raise OSError(28, "temporary transient read error")
            return real_read(manager, path, default)

        def start(*_args, **_kwargs):
            process_starts.append(1)
            self.real_atomic(self.state_path, {
                **self.state(), "status": "COMPLETE", "last_summary": "Completed after recovery"})
            return FakeProcess()

        with patch.object(manager_module.subprocess, "Popen",
                          side_effect=start), \
                patch.object(manager_module.GoalManager, "_read", read):
            self.manager._launch(self.goal_id)
            watcher = self.manager.watchers[self.goal_id]
            await asyncio.wait_for(watcher, timeout=3)
        state = self.state()
        report = self.manager.report(self.goal_id)
        self.assertEqual(len(process_starts), 1)
        self.assertEqual(state["id"], self.goal_id)
        self.assertEqual(state["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Completed after recovery")
        self.assertFalse(report["supervision_lost"])
        self.assertIn("host_recovery", [event["event"] for event in self.events()])

    async def test_transient_cancel_cleanup_errors_retry_same_goal_until_canceled(self):
        """Cleanup errors do not demand resume and task cancellation is re-polled."""
        state = {"id": self.goal_id, "status": "CANCELING", "session_id": None,
                 "recovery_count": 9, "unresolved_task_ids": ["task-1"]}
        self.real_atomic(self.state_path, state)
        calls = {"count": 0}

        async def cancel_owned(_goal_id):
            calls["count"] += 1
            if calls["count"] == 1:
                raise OSError("temporary transport failure")
            return []

        with patch.object(self.manager, "_cancel_owned_tasks", side_effect=cancel_owned):
            self.manager._launch_cancel(self.goal_id)
            watcher = self.manager.cancel_watchers[self.goal_id]
            for _ in range(100):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        final = self.state()
        self.assertEqual(final["status"], "CANCELED")
        self.assertEqual(final["id"], self.goal_id)
        self.assertEqual(final["recovery_count"], 9)
        self.assertGreaterEqual(calls["count"], 2)
        self.assertTrue(watcher.done())
        self.assertIsNone(watcher.exception())
        self.assertNotIn("cancel_lost", final)

    async def test_cancel_owns_retries_after_initial_query_failure(self):
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "RUNNING", "session_id": None,
            "recovery_count": 4})
        calls = {"count": 0}

        async def cancel_owned(_goal_id):
            calls["count"] += 1
            if calls["count"] == 1:
                raise OSError("transient first query failure")
            return []

        with patch.object(self.manager, "_cancel_owned_tasks", side_effect=cancel_owned):
            result = await self.manager.cancel(self.goal_id)
            self.assertEqual(result["goal_id"], self.goal_id)
            self.assertTrue((self.directory / "cancel.request").exists())
            watcher = self.manager.cancel_watchers[self.goal_id]
            for _ in range(150):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        self.assertEqual(self.state()["status"], "CANCELED")
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(self.state()["recovery_count"], 4)
        self.assertGreaterEqual(calls["count"], 2)
        self.assertTrue(watcher.done())
        self.assertIsNone(watcher.exception())

    async def test_cancel_owns_retries_after_initial_state_publication_failure(self):
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "RUNNING", "session_id": None,
            "recovery_count": 6})
        real_atomic = self.real_atomic
        fault = {"active": True}
        polls = {"count": 0}

        async def cancel_owned(_goal_id):
            polls["count"] += 1
            return []

        def atomic(path, value):
            if path == self.state_path and value.get("status") == "CANCELED" and fault["active"]:
                fault["active"] = False
                raise OSError("transient first state publication failure")
            return real_atomic(path, value)

        with patch.object(self.manager, "_cancel_owned_tasks", side_effect=cancel_owned), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            await self.manager.cancel(self.goal_id)
            watcher = self.manager.cancel_watchers[self.goal_id]
            for _ in range(150):
                await asyncio.sleep(.02)
                try:
                    if self.state().get("status") == "CANCELED":
                        break
                except OSError:
                    continue

        final = self.state()
        self.assertEqual(final["status"], "CANCELED")
        self.assertEqual(final["id"], self.goal_id)
        self.assertEqual(final["recovery_count"], 6)
        self.assertGreaterEqual(polls["count"], 2)
        self.assertFalse(fault["active"])
        self.assertTrue(watcher.done())
        self.assertIsNone(watcher.exception())

    async def test_cancel_owns_cleanup_before_initial_canceling_write(self):
        self.real_atomic(self.state_path, {
            "id": self.goal_id, "status": "RUNNING", "session_id": None,
            "recovery_count": 11})
        real_atomic = self.real_atomic
        fault = {"active": True}
        calls = {"count": 0}

        async def cancel_owned(_goal_id):
            calls["count"] += 1
            return []

        def atomic(path, value):
            if (path == self.state_path and value.get("status") == "CANCELING"
                    and fault["active"]):
                fault["active"] = False
                raise OSError("transient initial CANCELING publication failure")
            return real_atomic(path, value)

        with patch.object(self.manager, "_cancel_owned_tasks", side_effect=cancel_owned), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            result = await self.manager.cancel(self.goal_id)
            self.assertEqual(result["goal_id"], self.goal_id)
            self.assertIn(self.goal_id, self.manager.cancel_watchers,
                          "cleanup ownership must precede the initial state write")
            watcher = self.manager.cancel_watchers[self.goal_id]
            for _ in range(150):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        final = self.state()
        self.assertFalse(fault["active"])
        self.assertEqual(final["status"], "CANCELED")
        self.assertEqual(final["id"], self.goal_id)
        self.assertEqual(final["recovery_count"], 11)
        self.assertTrue((self.directory / "cancel.request").exists())
        self.assertGreaterEqual(calls["count"], 1)
        self.assertTrue(watcher.done())
        self.assertIsNone(watcher.exception())

    async def test_controller_started_journal_failure_does_not_stop_existing_process(self):
        starts = []
        real_event = self.manager._event

        def event(goal_id, name, **fields):
            if name == "controller_started":
                raise OSError("temporary started-event journal failure")
            return real_event(goal_id, name, **fields)

        def start(*_args, **_kwargs):
            starts.append(1)
            self.real_atomic(self.state_path, {**self.state(), "status": "COMPLETE",
                                               "last_summary": "Completed despite start log failure"})
            return FakeProcess()

        with patch.object(manager_module.subprocess, "Popen", side_effect=start), \
                patch.object(self.manager, "_event", side_effect=event):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertEqual(starts, [1])
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Completed despite start log failure")
        self.assertFalse(report["supervision_lost"])

    async def test_controller_exited_journal_failure_preserves_completed_result(self):
        starts = []
        real_event = self.manager._event

        def event(goal_id, name, **fields):
            if name == "controller_exited":
                raise OSError("temporary exit-event journal failure")
            return real_event(goal_id, name, **fields)

        def start(*_args, **_kwargs):
            starts.append(1)
            self.real_atomic(self.state_path, {**self.state(), "status": "COMPLETE",
                                               "last_summary": "Completed before exit log failed"})
            return FakeProcess()

        with patch.object(manager_module.subprocess, "Popen", side_effect=start), \
                patch.object(self.manager, "_event", side_effect=event):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertEqual(starts, [1])
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Completed before exit log failed")
        self.assertFalse(report["supervision_lost"])
        self.assertFalse(report["controller_running"])

    async def test_transient_process_metadata_write_keeps_same_controller_supervised(self):
        launches = []
        fault = {"active": True}
        real_atomic = self.real_atomic

        def atomic(path, value):
            if path == self.directory / "process.json" and fault["active"]:
                fault["active"] = False
                raise OSError("one-shot process metadata write failure")
            return real_atomic(path, value)

        class CompletingProcess(FakeProcess):
            def __init__(inner_self):
                super().__init__()
                inner_self.finished = False

            def poll(inner_self):
                return inner_self.code if inner_self.finished else None

            def wait(inner_self):
                import time
                time.sleep(.35)
                self.real_atomic(self.state_path, {**self.state(), "status": "COMPLETE",
                                                   "last_summary": "Metadata recovered"})
                inner_self.finished = True
                return inner_self.code

        def start(*_args, **_kwargs):
            launches.append(1)
            return CompletingProcess()

        self.real_atomic(self.state_path, {**self.state(), "status": "RUNNING"})
        with patch.object(manager_module.subprocess, "Popen", side_effect=start), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(self.manager.watchers[self.goal_id], timeout=3)

        report = self.manager.report(self.goal_id)
        self.assertEqual(launches, [1])
        self.assertFalse(fault["active"])
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "Metadata recovered")
        self.assertFalse(report["supervision_lost"])

    async def test_cancel_intent_is_preserved_during_metadata_retry(self):
        fault = {"active": True}
        real_atomic = self.real_atomic
        launched = asyncio.Event()
        release = threading.Event()

        def atomic(path, value):
            if path == self.directory / "process.json" and fault["active"]:
                fault["active"] = False
                raise OSError("one-shot process metadata write failure")
            return real_atomic(path, value)

        class WaitingProcess(FakeProcess):
            def wait(inner_self):
                release.wait()
                return 1

            def __init__(inner_self):
                super().__init__()
                inner_self.code = None

            def poll(inner_self):
                return inner_self.code

        def start(*_args, **_kwargs):
            launched.set()
            return WaitingProcess()

        with patch.object(manager_module.subprocess, "Popen", side_effect=start), \
                patch.object(manager_module.runtime, "atomic_json", side_effect=atomic):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(launched.wait(), timeout=2)
            await asyncio.sleep(.15)
            self.assertFalse(fault["active"])
            self.assertTrue(self.manager.processes.get(self.goal_id))
            canceled = await self.manager.cancel(self.goal_id)
            self.assertTrue((self.directory / "cancel.request").exists())
            cleanup = self.manager.cancel_watchers[self.goal_id]
            release.set()
            for _ in range(100):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        self.assertEqual(canceled["goal_id"], self.goal_id)
        self.assertTrue((self.directory / "cancel.request").exists())
        self.assertEqual(self.state()["id"], self.goal_id)
        self.assertEqual(self.state()["status"], "CANCELED")
        self.assertTrue(cleanup.done())
        self.assertIsNone(cleanup.exception())

    async def test_one_shot_job_close_failure_keeps_cleanup_owner_and_terminates_process(self):
        close_calls = []
        process_holder = {}
        launched = asyncio.Event()

        class FlakyJob:
            def assign(self, process):
                pass

            def close(self):
                close_calls.append(1)
                if len(close_calls) == 1:
                    raise OSError("one-shot process job close failure")

        class LiveProcess(FakeProcess):
            def __init__(self):
                super().__init__()
                self.code = None
                self.terminated = False

            def poll(self):
                return self.code

            def wait(self):
                while self.code is None:
                    import time
                    time.sleep(.01)
                return self.code

            def kill(self):
                self.terminated = True
                self.code = 1

        def start(*_args, **_kwargs):
            process = LiveProcess()
            process_holder["proc"] = process
            launched.set()
            return process

        with patch.object(manager_module.runtime, "Job", FlakyJob), \
                patch.object(manager_module.subprocess, "Popen", side_effect=start):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(launched.wait(), timeout=2)
            await asyncio.sleep(.1)
            self.assertTrue(self.manager.processes.get(self.goal_id))

            canceled = await self.manager.cancel(self.goal_id)
            self.assertEqual(canceled["goal_id"], self.goal_id)
            self.assertIn(self.goal_id, self.manager.cancel_watchers)
            cleanup = self.manager.cancel_watchers[self.goal_id]
            for _ in range(150):
                await asyncio.sleep(.02)
                if self.state().get("status") == "CANCELED":
                    break

        final = self.state()
        self.assertGreaterEqual(len(close_calls), 2)
        self.assertTrue(process_holder["proc"].terminated)
        self.assertIsNone(self.manager.processes.get(self.goal_id))
        self.assertTrue((self.directory / "cancel.request").exists())
        self.assertEqual(final["status"], "CANCELED")
        self.assertEqual(final["id"], self.goal_id)
        self.assertTrue(cleanup.done())
        self.assertIsNone(cleanup.exception())

    async def test_transient_kill_and_wait_failures_block_canceled_until_exit_confirmed(self):
        launched = asyncio.Event()
        calls = {"kill": 0, "wait": 0}
        process_holder = {}

        class TrickyProcess(FakeProcess):
            def __init__(self):
                super().__init__()
                self.code = None
                self.terminated = False

            def poll(self):
                return self.code

            def kill(self):
                calls["kill"] += 1
                if calls["kill"] == 1:
                    raise OSError("first process kill attempt failed")
                self.terminated = True
                # Keep it live until wait succeeds, proving CANCELED is not
                # published merely because kill() returned.

            def wait(self):
                calls["wait"] += 1
                if calls["wait"] == 1:
                    raise OSError("first process wait attempt failed")
                self.code = 1
                return self.code

        class Job:
            def assign(self, _process):
                pass

            def close(self):
                pass

        def start(*_args, **_kwargs):
            process = TrickyProcess()
            process_holder["proc"] = process
            launched.set()
            return process

        with patch.object(manager_module.runtime, "Job", Job), \
                patch.object(manager_module.subprocess, "Popen", side_effect=start):
            self.manager._launch(self.goal_id)
            await asyncio.wait_for(launched.wait(), timeout=2)
            canceled = await self.manager.cancel(self.goal_id)
            cleanup = self.manager.cancel_watchers[self.goal_id]
            self.assertEqual(canceled["goal_id"], self.goal_id)
            await asyncio.sleep(.05)
            self.assertNotEqual(self.state()["status"], "CANCELED",
                                "cleanup published terminal status before process exit was confirmed")
            self.assertIs(self.manager.processes[self.goal_id][0], process_holder["proc"])
            await asyncio.wait_for(cleanup, timeout=4)

        final = self.state()
        self.assertGreaterEqual(calls["kill"], 2)
        self.assertGreaterEqual(calls["wait"], 2)
        self.assertTrue(process_holder["proc"].terminated)
        self.assertIsNotNone(process_holder["proc"].poll())
        self.assertIsNone(self.manager.processes.get(self.goal_id))
        self.assertTrue((self.directory / "cancel.request").exists())
        self.assertEqual(final["status"], "CANCELED")
        self.assertEqual(final["id"], self.goal_id)
        self.assertTrue(cleanup.done())
        self.assertIsNone(cleanup.exception())


class _FailedWatcher:
    """A finished watcher that owns an exception, for the superseded case."""

    def __init__(self):
        self._error = PermissionError("synthetic non-recoverable access error")
        self._error.winerror = 87

    def cancelled(self):
        return False

    def exception(self):
        return self._error


if __name__ == "__main__":
    unittest.main()
