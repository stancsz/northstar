"""Local SQLite/process-fixture tests for durable A2A task storage."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import asyncio
import unittest
from pathlib import Path

from a2a.server.context import ServerCallContext
from a2a.types import Artifact, Part, Task, TaskState, TaskStatus

from task_store import INTERRUPTED_MESSAGE, create_task_store

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "a2a-stack" / "runtime"))
import runner  # noqa: E402


def make_task(task_id: str, state: int, artifact: bool = False) -> Task:
    task = Task(id=task_id, context_id=f"ctx-{task_id}", status=TaskStatus(state=state))
    if artifact:
        task.artifacts.append(Artifact(
            artifact_id="result-1", name="result", parts=[Part(text="durable artifact")]
        ))
    return task


class DurableTaskStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        scratch = ROOT / "tmp" / "a2a-stack" / "store-build"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.state_root = Path(self.tmp.name)
        self.context = ServerCallContext()

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_completed_artifact_survives_reopen_and_agent_databases_are_isolated(self):
        store = create_task_store(self.state_root, "stack-a/role-coder")
        await store.save(make_task("completed-1", TaskState.TASK_STATE_COMPLETED, artifact=True), self.context)
        await store.close()

        reopened = create_task_store(self.state_root, "stack-a/role-coder")
        saved = await reopened.get("completed-1", self.context)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(saved.artifacts[0].parts[0].text, "durable artifact")
        await reopened.close()

        other = create_task_store(self.state_root, "stack-a/role-reviewer")
        self.assertIsNone(await other.get("completed-1", self.context))
        await other.close()

    async def test_inflight_task_without_process_is_failed_and_receipt_is_written(self):
        store = create_task_store(self.state_root, "dead-agent")
        await store.save(make_task("dead-task", TaskState.TASK_STATE_SUBMITTED, artifact=True), self.context)
        await store.close()

        recovered = create_task_store(self.state_root, "dead-agent")
        task = await recovered.get("dead-task", self.context)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_FAILED)
        self.assertIn("continuation assignment", task.status.message.parts[0].text)
        self.assertEqual(task.artifacts[0].parts[0].text, "durable artifact")
        receipt = json.loads((self.state_root / "tasks" / "dead-task" / "terminal.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "TASK_STATE_FAILED")
        await recovered.close()

    async def test_live_identity_matched_process_remains_working(self):
        if os.name != "nt":
            self.skipTest("native process identity checks are Windows-specific")
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            token = runner.process_token(proc.pid)
            self.assertIsNotNone(token)
            task_dir = self.state_root / "tasks" / "live-task"
            task_dir.mkdir(parents=True)
            (task_dir / "process.json").write_text(json.dumps({"pid": proc.pid, "process_token": token}), encoding="utf-8")
            first = create_task_store(self.state_root, "live-agent")
            await first.save(make_task("live-task", TaskState.TASK_STATE_WORKING), self.context)
            await first.close()

            recovered = create_task_store(self.state_root, "live-agent")
            task = await recovered.get("live-task", self.context)
            self.assertEqual(task.status.state, TaskState.TASK_STATE_WORKING)
            self.assertIn("alive", task.status.message.parts[0].text)
            self.assertFalse((task_dir / "terminal.json").exists())
            proc.terminate()
            proc.wait(timeout=10)

            receipt_path = task_dir / "terminal.json"
            for _ in range(5):
                if receipt_path.exists():
                    break
                await asyncio.sleep(1)
            self.assertTrue(receipt_path.exists(), "background monitor did not write terminal receipt")
            failed = await recovered.get("live-task", self.context)
            self.assertEqual(failed.status.state, TaskState.TASK_STATE_FAILED)
            self.assertIn("continuation assignment", failed.status.message.parts[0].text)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["recovery"], "monitored_native_worker_exited_without_terminal_task_result")
            await recovered.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)

    async def test_recovery_runs_once_and_does_not_fail_new_active_tasks(self):
        store = create_task_store(self.state_root, "current-agent")
        await store.save(make_task("new-active", TaskState.TASK_STATE_WORKING), self.context)
        for _ in range(3):
            task = await store.get("new-active", self.context)
            self.assertEqual(task.status.state, TaskState.TASK_STATE_WORKING)
        self.assertFalse((self.state_root / "tasks" / "new-active" / "terminal.json").exists())
        await store.close()


if __name__ == "__main__":
    unittest.main()
