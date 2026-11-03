"""Local Windows fixture-process checks for receipts and native retry events."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

AGENT_DIR = Path(__file__).resolve().parent
STACK_ROOT = AGENT_DIR.parent
REPO_ROOT = STACK_ROOT.parent
SCRATCH = REPO_ROOT / "tmp" / "a2a-stack" / "retry-tests"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(STACK_ROOT / "runtime") not in sys.path:
    sys.path.insert(0, str(STACK_ROOT / "runtime"))

import service  # noqa: E402 - import the real Windows process lifecycle


@unittest.skipUnless(os.name == "nt", "uses Windows Job Object process cleanup")
class RetryReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.run_root = SCRATCH / uuid.uuid4().hex
        self.run_root.mkdir()
        self.prompt = self.run_root / "prompt.txt"
        self.prompt.write_text("fixture prompt\n", encoding="utf-8")
        self.tasks_dir = self.run_root / "tasks"
        self.previous_tasks_dir = service.TASKS_DIR
        service.TASKS_DIR = self.tasks_dir

    async def asyncTearDown(self):
        service.TASKS_DIR = self.previous_tasks_dir

    def config(self, name="fixture"):
        return {
            "name": name,
            "mode": "claude",
            "cwd": self.run_root,
            "prompt_path": self.prompt,
            "tools": ["Read"],
            "allowed_tools": ["Read"],
            "permission_mode": "acceptEdits",
            "max_turns": None,
            "timeout_seconds": None,
        }

    def fixture(self, source):
        return [sys.executable, "-u", "-c", source]

    def updater(self):
        return SimpleNamespace(task_id=str(uuid.uuid4()))

    def assert_process_exited(self, pid, entry):
        self.assertIsNotNone(entry.proc)
        self.assertEqual(entry.proc.pid, pid)
        self.assertIsNotNone(entry.proc.poll(), "owned fixture process has not exited")

    async def run_fixture(self, source, name="fixture"):
        updater = self.updater()
        entry = service._ActiveJob()
        with patch.object(service, "_build_claude_argv", return_value=self.fixture(source)):
            result = await service.RegisteredJobExecutor()._run_job(self.config(name), entry, updater)
        return updater.task_id, entry, result

    async def test_intermediate_api_retry_recovers_and_completes_receipt(self):
        source = (
            "import json,time; "
            "print(json.dumps({'type':'system','subtype':'api_retry'}),flush=True); "
            "time.sleep(0.15); "
            "print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'recovered-native-retry'}),flush=True)"
        )
        task_id, entry, (ok, text) = await self.run_fixture(source, "retry-success")
        task_dir = self.tasks_dir / task_id
        receipt = json.loads((task_dir / "receipt.json").read_text(encoding="utf-8"))
        events = [json.loads(line) for line in (task_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(ok)
        self.assertEqual(text, "recovered-native-retry")
        self.assertTrue(receipt["completed"])
        self.assertEqual(receipt["exit_code"], 0)
        self.assertTrue(any(event.get("subtype") == "api_retry" for event in events))
        process = json.loads((task_dir / "process.json").read_text(encoding="utf-8"))
        self.assert_process_exited(process["pid"], entry)

    async def test_final_native_model_error_is_logged_and_receipt_is_incomplete(self):
        source = "import json; print(json.dumps({'type':'result','subtype':'error_during_execution','is_error':True,'result':'API error: unrecognized_model'}),flush=True)"
        updater = self.updater()
        entry = service._ActiveJob()
        with patch.object(service, "_build_claude_argv", return_value=self.fixture(source)):
            with self.assertRaises(service.JobFailed):
                await service.RegisteredJobExecutor()._run_job(self.config("fatal-model"), entry, updater)
        task_dir = self.tasks_dir / updater.task_id
        receipt = json.loads((task_dir / "receipt.json").read_text(encoding="utf-8"))
        events = [json.loads(line) for line in (task_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertFalse(receipt["completed"])
        self.assertTrue(any(event.get("subtype") == "error_during_execution" and event.get("is_error") is True
                            for event in events))
        pid_record = json.loads((task_dir / "process.json").read_text(encoding="utf-8"))
        self.assert_process_exited(pid_record["pid"], entry)

    async def test_cancellation_writes_incomplete_receipt_and_reaps_process(self):
        source = "import time; print('fixture-running',flush=True); time.sleep(3600)"
        updater = self.updater()
        entry = service._ActiveJob()
        with patch.object(service, "_build_claude_argv", return_value=self.fixture(source)):
            task = asyncio.create_task(service.RegisteredJobExecutor()._run_job(self.config("cancel-fixture"), entry, updater))
            task_dir = self.tasks_dir / updater.task_id
            while not (task_dir / "process.json").exists():
                await asyncio.sleep(0.01)
            pid_record = json.loads((task_dir / "process.json").read_text(encoding="utf-8"))
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        receipt = json.loads((task_dir / "receipt.json").read_text(encoding="utf-8"))
        self.assertFalse(receipt["completed"])
        self.assert_process_exited(pid_record["pid"], entry)


if __name__ == "__main__":
    unittest.main()
