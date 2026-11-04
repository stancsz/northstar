"""Regression tests for the degraded-state-write-back defect.

The supervision-loss fix reads the goal's state through a helper that
degrades to an empty dict when the read fails, and then writes that dict
back.  On Windows a transient sharing violation on the read while the write
succeeds is reachable, and the write then replaces the goal's real state
with a five-field stub.

The consequence is not cosmetic.  The stub has no `id`, so the controller's
completion check can never pass; it has no `recovery_count`, so the
controller's own exception handler raises `KeyError` while trying to report
one.  The goal is wedged: it can neither complete nor be resumed.

Every path that updates the goal's state must therefore MERGE into the
on-disk state, and a path that cannot read the state must not write one.

These tests are offline: no model, provider, HTTP or live host calls.
"""
from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


STACK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("state_truncation_manager", STACK / "autonomy/manager.py")
manager_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager_module)
SCRATCH = STACK / "scratchtmp/a2a-stack/manager-tests"

# The fields a truncated state.json would destroy.  Each one has a specific
# consequence: `id` fails the controller's completion check, and
# `recovery_count` makes the controller's own error handler raise.
ESSENTIAL_FIELDS = ("id", "recovery_count", "session_id", "host_restart_count",
                    "previous_session_ids", "spec_digest", "last_summary")


class StateTruncationTests(unittest.IsolatedAsyncioTestCase):
    """A degraded read must never be written back over the real state."""

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
        self.addCleanup(self._close_manager)
        self.goal_id = "g-" + "e" * 32
        self.directory = self.manager._dir(self.goal_id)
        self.directory.mkdir(parents=True)
        self.state_path = self.directory / "state.json"
        self.spec_path = self.directory / "spec.json"
        self.real_atomic = manager_module.runtime.atomic_json
        self.real_atomic(self.state_path, self.real_state("RUNNING"))
        self.real_atomic(self.spec_path, {
            "id": self.goal_id, "workspace": str(self.workspace),
            "goal": "Do not truncate this goal", "acceptance": ["stays whole"],
            "checks": []})

    def real_state(self, status):
        return {
            "id": self.goal_id, "status": status, "session_id": "sess-1",
            "recovery_count": 7, "host_restart_count": 3,
            "previous_session_ids": ["sess-0"], "spec_digest": "digest-abc",
            "last_summary": "the accepted evidence",
            "unresolved_task_ids": [],
        }

    def state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    async def _close_manager(self):
        self.manager.closing = True
        tasks = []
        for watcher in (list(self.manager.watchers.values())
                        + list(self.manager.cancel_watchers.values())):
            if isinstance(watcher, asyncio.Task):
                watcher.cancel()
                tasks.append(watcher)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def unreadable_state(self, error):
        """Patch state.json reads so they fail, leaving the write working.

        This is the Windows sharing-violation shape: the read is denied and
        the write is allowed.  The point of the defect is exactly that
        asymmetry.
        """
        real_read = manager_module.GoalManager._read
        state_path = self.state_path

        def guarded(self, path, default=None):
            if path == state_path:
                raise error
            return real_read(self, path, default)

        return patch.object(manager_module.GoalManager, "_read", guarded)

    def assert_state_intact(self, context=""):
        after = self.state()
        destroyed = [field for field in ESSENTIAL_FIELDS if field not in after]
        self.assertEqual(destroyed, [],
                         f"the goal's state was truncated{context}: {destroyed} lost")

    # -- the supervision-loss callback ------------------------------------- #
    async def test_the_supervision_loss_does_not_truncate_the_state(self):
        """An unreadable state must not be overwritten with a stub.

        The durable update is refused rather than written from a degraded
        read, so the loss is not durably recorded in this case.  The report
        still derives it from the live watcher, and the host event still
        records it, so the loss is not silent.
        """
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32
        watcher = _DeadWatcher(OSError(28, "No space left on device"))
        self.manager.watchers[self.goal_id] = watcher

        with self.unreadable_state(denied):
            self.manager._record_supervision_loss(self.goal_id, watcher)

        self.assert_state_intact(" by the supervision-loss callback")
        report = self.manager.report(self.goal_id)
        self.assertTrue(report["supervision_lost"],
                        "the loss vanished because the state could not be read")
        self.assertEqual(report["status"], "NEEDS_USER")

    async def test_the_supervision_loss_records_the_loss_when_the_read_works(self):
        watcher = _DeadWatcher(OSError(28, "No space left on device"))
        self.manager.watchers[self.goal_id] = watcher

        self.manager._record_supervision_loss(self.goal_id, watcher)

        self.assert_state_intact(" by the supervision-loss callback")
        after = self.state()
        self.assertTrue(after["supervision_lost"])
        self.assertEqual(after["status"], "NEEDS_USER")

    # -- the cancel-loss callback ------------------------------------------ #
    async def test_the_cancel_loss_does_not_truncate_the_state(self):
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32
        watcher = _DeadWatcher(OSError(28, "No space left on device"))
        self.manager.cancel_watchers[self.goal_id] = watcher

        with self.unreadable_state(denied):
            self.manager._record_cancel_loss(self.goal_id, watcher)

        self.assert_state_intact(" by the cancel-loss callback")

    # -- the cleanup path --------------------------------------------------- #
    async def test_the_cleanup_does_not_truncate_the_state(self):
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32
        self.real_atomic(self.state_path, self.real_state("CANCELING"))

        async def unresolved(goal_id):
            return ["task-1"]

        with self.unreadable_state(denied), \
                patch.object(self.manager, "_cancel_owned_tasks", side_effect=unresolved):
            try:
                await asyncio.wait_for(self.manager._finish_cancel(self.goal_id), timeout=2.0)
            except asyncio.TimeoutError:
                pass

        self.assert_state_intact(" by the cleanup")

    # -- the explicit cancel ------------------------------------------------ #
    async def test_the_explicit_cancel_does_not_truncate_the_state(self):
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32

        async def unresolved(goal_id):
            return ["task-1"]

        with self.unreadable_state(denied), \
                patch.object(self.manager, "_cancel_owned_tasks", side_effect=unresolved):
            try:
                await asyncio.wait_for(self.manager.cancel(self.goal_id), timeout=5.0)
            except asyncio.TimeoutError:
                pass

        self.assert_state_intact(" by the explicit cancel")

    # -- the resume --------------------------------------------------------- #
    async def test_failed_resume_preserves_durable_cancellation_intent(self):
        self.real_atomic(self.state_path, self.real_state("NEEDS_USER"))
        cancel_request = self.directory / "cancel.request"
        cancel_request.write_text("explicit cancellation\n", encoding="utf-8")
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32
        with self.unreadable_state(denied):
            with self.assertRaises(ValueError):
                await self.manager.resume(self.goal_id)
        self.assertTrue(cancel_request.exists(), "failed resume discarded cancellation intent")

    async def test_the_resume_does_not_truncate_the_state(self):
        """The report degrades to a stub when the state file cannot be read.

        The resume must not write that stub back: the goal would lose its
        id, its recovery count and its session history, and the controller
        could then neither complete it nor recover it.
        """
        denied = PermissionError("synthetic sharing violation on read")
        denied.winerror = 32
        self.real_atomic(self.state_path, {
            **self.real_state("NEEDS_USER"),
            "supervision_lost": True,
            "supervision_lost_reason": "OSError: boom",
            "blocker": {"kind": "host_supervision_lost", "message": "m",
                        "evidence": ["OSError: boom"]},
        })

        with self.unreadable_state(denied):
            with self.assertRaises(ValueError):
                await self.manager.resume(self.goal_id)

        self.assert_state_intact(" by the resume")

    async def test_the_resume_clears_the_loss_fields_without_losing_the_rest(self):
        self.real_atomic(self.state_path, {
            **self.real_state("NEEDS_USER"),
            "supervision_lost": True,
            "supervision_lost_at": "2026-11-04T00:00:00+00:00",
            "supervision_lost_reason": "OSError: boom",
            "cancel_lost": True,
            "cancel_lost_reason": "OSError: boom",
            "blocker": {"kind": "host_supervision_lost", "message": "m",
                        "evidence": ["OSError: boom"]},
        })

        await self.manager.resume(self.goal_id)

        after = self.state()
        self.assertEqual(after["status"], "RUNNING")
        for field in ("supervision_lost", "supervision_lost_at",
                      "supervision_lost_reason", "cancel_lost",
                      "cancel_lost_reason", "blocker"):
            self.assertNotIn(field, after,
                             f"the resume left the stale field {field!r} behind")
        self.assert_state_intact(" by the resume")

    # -- the controller's own view ------------------------------------------ #
    async def test_the_goal_stays_completable_after_a_loss(self):
        """The whole point: a loss must not wedge the goal.

        The controller refuses to accept a completion whose state has no
        `id`, and its own error handler raises `KeyError` when the state
        has no `recovery_count`.  A truncated state therefore strands the
        goal permanently.
        """
        watcher = _DeadWatcher(OSError(28, "No space left on device"))
        self.manager.watchers[self.goal_id] = watcher
        self.manager._record_supervision_loss(self.goal_id, watcher)

        after = self.state()
        self.assertEqual(after.get("id"), self.goal_id,
                         "the controller could not match the goal to its spec")
        self.assertIsInstance(after.get("recovery_count"), int,
                              "the controller's error handler would raise KeyError")

        # The controller's completion check, as autonomy/runner.py applies it.
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        completed = {**after, "status": "COMPLETE",
                     "accepted_receipt": {"accepted": True}}
        accepted = (completed.get("status") == "COMPLETE"
                    and completed.get("id") == spec["id"]
                    and (completed.get("accepted_receipt") or {}).get("accepted") is True)
        self.assertTrue(accepted,
                        "the controller would refuse the completion after a loss")


class _DeadWatcher:
    """A finished watcher that owns an exception."""

    def __init__(self, error):
        self._error = error

    def done(self):
        return True

    def cancelled(self):
        return False

    def exception(self):
        return self._error


if __name__ == "__main__":
    unittest.main()
