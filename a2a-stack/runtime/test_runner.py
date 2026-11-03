import json
import inspect
import os
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path

NORTHSTAR_ROOT = Path(__file__).resolve().parents[2]
TEST_CONTROL = NORTHSTAR_ROOT / "tmp" / "a2a-stack" / "runtime-tests" / "control"
os.environ["A2A_TEST_CONTROL_DIR"] = str(TEST_CONTROL)
import runner


class StreamDetectionTests(unittest.TestCase):
    def test_runtime_has_no_default_time_or_turn_ceiling(self):
        self.assertIsNone(inspect.signature(runner.broker).parameters["timeout"].default)
        self.assertIsNone(inspect.signature(runner.broker).parameters["max_turns"].default)
        run = runner.argument_parser().parse_args(["run", "--prompt-file", "task.md"])
        execute = runner.argument_parser().parse_args(["exec", "--", sys.executable, "-c", "print('ok')"])
        self.assertIsNone(run.timeout)
        self.assertIsNone(run.max_turns)
        self.assertIsNone(execute.timeout)
        command = runner.claude_command("claude.exe", "do one task", ["Read", "Write"])
        self.assertNotIn("--max-turns", command)
        self.assertNotIn("--max-budget-usd", command)
        limited = runner.claude_command("claude.exe", "fixture", ["Read"], max_turns=4)
        self.assertEqual(limited[limited.index("--max-turns") + 1], "4")

    def test_only_structured_events_abort(self):
        self.assertIsNone(runner.structured_abort('{"type":"assistant","text":"429 unrecognized_model"}'))
        self.assertIsNone(runner.structured_abort('{"type":"tool_result","content":"api_retry 429"}'))
        self.assertIsNone(runner.structured_abort('{"type":"error","error":{"message":"documentation discusses HTTP 429 but request succeeded"}}'))
        self.assertIsNone(runner.structured_abort('{"type":"result","subtype":"error_during_execution","is_error":true,"result":"The docs mention API error: unrecognized_model but this is quoted text"}'))
        self.assertIsNone(runner.structured_abort('{"type":"system","subtype":"api_retry"}'))
        self.assertIsNone(runner.structured_abort('{"type":"api_retry","error":{"code":429}}'))
        self.assertIsNone(runner.structured_abort('{"type":"system","status_code":429}'))
        self.assertIsNone(runner.structured_abort('{"type":"error","error":{"code":"unrecognized_model"}}'))
        self.assertEqual(runner.structured_abort('{"type":"result","error":{"code":"429"}}'), "429")
        self.assertIsNone(runner.structured_abort('{"type":"result","error":"quoted unrecognized_model text"}'))
        self.assertEqual(runner.structured_abort('{"type":"result","subtype":"error_during_execution","is_error":true,"result":"API error: unrecognized_model: bad model"}'), "unrecognized_model")
        self.assertEqual(runner.structured_abort('{"type":"result","subtype":"error_during_execution","is_error":true,"result":"API error: 429 rate limited"}'), "429")

    def test_event_receipts_omit_tool_payload_and_sanitize_handoff(self):
        event = runner.sanitized_event('{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Read","input":{"file_path":"secret.txt"}},{"type":"text","text":"private source"}]}}')
        self.assertEqual(event["tools"], [{"id":"t1", "name":"Read"}])
        encoded = json.dumps(event)
        self.assertNotIn("secret.txt", encoded)
        self.assertNotIn("private source", encoded)
        result = runner.sanitized_event('{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","is_error":true,"content":"private error body"}]}}')
        self.assertEqual(result["tool_results"], [{"tool_use_id": "t1", "is_error": True}])
        self.assertNotIn("private error body", json.dumps(result))
        handoff = runner.sanitized_event('{"type":"result","subtype":"success","num_turns":2,"result":"Done; email a@b.com with token=abc123 and sk-ant-abcdefghijk"}')
        self.assertIn("[REDACTED_EMAIL]", handoff["handoff"])
        self.assertIn("[REDACTED]", handoff["handoff"])
        self.assertIn("[REDACTED_TOKEN]", handoff["handoff"])

        filler = "Acceptance evidence line with no secrets. "
        body = (filler * 40)[:1200]
        embedded_token = "sk-ant-" + "q" * 24
        payload = f"{body} credential={embedded_token} tail END_OF_HANDOFF"
        self.assertGreater(len(payload), 800)
        event = runner.sanitized_event(json.dumps({"type": "result", "subtype": "success", "result": payload}))
        long_handoff = event["handoff"]
        self.assertTrue(long_handoff.rstrip().endswith("END_OF_HANDOFF"), "handoff marker was truncated")
        self.assertIn("credential=[REDACTED_TOKEN]", long_handoff)
        self.assertNotIn(embedded_token, long_handoff)
        self.assertNotIn(embedded_token, json.dumps(event))
        self.assertGreaterEqual(len(long_handoff), len(body))


@unittest.skipUnless(os.name == "nt", "Windows process lifecycle required")
class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.test_control = TEST_CONTROL / uuid.uuid4().hex
        os.environ["A2A_TEST_CONTROL_DIR"] = str(self.test_control)
        runner.CONTROL = self.test_control
        runner.STATE = self.test_control / "status.json"
        runner.LOCK = self.test_control / "owner.lock"
    def cli(self, *args, timeout=30):
        return subprocess.run([sys.executable, str(Path(runner.__file__)), *map(str, args)], cwd=runner.ROOT,
                              capture_output=True, text=True, timeout=timeout)

    def wait_status(self, wanted, seconds=10):
        end = time.time() + seconds
        while time.time() < end:
            status = json.loads(self.cli("status").stdout or "{}")
            if status.get("status") == wanted:
                return status
            time.sleep(.1)
        self.fail(f"status did not become {wanted}")

    def start_clean(self):
        self.cli("stop", "--wait", "1")
        self.owner_process = subprocess.Popen([sys.executable, str(Path(runner.__file__)), "serve"], cwd=runner.ROOT,
                                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.wait_status("running")

    def fixture_command(self, marker):
        script = "import subprocess,sys,time,json,os; c=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(sys.argv[1],'w').write(json.dumps([os.getpid(),c.pid])); time.sleep(60)"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.unlink(missing_ok=True)
        return [sys.executable, "-c", script, str(marker)]

    def stop_owner(self):
        self.cli("stop")
        if getattr(self, "owner_process", None): self.owner_process.wait(timeout=5)

    def assert_fixture_tree_dead(self, marker):
        self.assertTrue(marker.exists(), "fixture did not record both PIDs")
        for pid in json.loads(marker.read_text(encoding="utf-8")):
            self.assertIsNone(runner.process_token(pid), f"fixture PID {pid} survived Job cleanup")

    def test_duplicate_start_keeps_owner_and_exec_success(self):
        first = self.start_clean()
        second = json.loads(self.cli("start").stdout)
        self.assertEqual(first["pid"], second["pid"])
        cmd = self.cli("exec", "--", sys.executable, "-c", "print('fixture-ok')")
        self.assertEqual(cmd.returncode, 0, cmd.stderr)
        status = json.loads(self.cli("status").stdout)
        self.assertIsNone(status["last_worker"]["deadline_epoch"])
        self.assertNotIn("fixture-ok", Path(status["last_worker"]["stdout"]).read_text(encoding="utf-8"))
        self.assertEqual(self.cli("stop").returncode, 0)
        self.owner_process.wait(timeout=5)

    def test_timeout_kills_child_tree_and_recovers(self):
        self.start_clean()
        marker = TEST_CONTROL.parent / "timeout-tree.json"
        result = self.cli("exec", "--timeout", "2", "--", *self.fixture_command(marker), timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assert_fixture_tree_dead(marker)
        self.assertEqual(json.loads(self.cli("status").stdout)["status"], "running")
        self.assertEqual(self.cli("exec", "--", sys.executable, "-c", "print('recovered')").returncode, 0)
        self.stop_owner()

    def test_concurrent_status_reads_do_not_kill_owner(self):
        self.start_clean()
        import threading
        failures = []
        def reader():
            end = time.time() + 3
            while time.time() < end:
                result = self.cli("status")
                try: json.loads(result.stdout)
                except ValueError: failures.append(result.stdout)
        threads = [threading.Thread(target=reader) for _ in range(4)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertFalse(failures)
        self.assertEqual(json.loads(self.cli("status").stdout)["status"], "running")
        self.stop_owner()

    def test_broker_death_kills_child_tree_and_recovers(self):
        owner = self.start_clean()
        marker = TEST_CONTROL.parent / "death-tree.json"
        # A separate client blocks on the request. Kill only the recorded broker PID to verify Job close cleanup.
        import threading
        holder = {}
        thread = threading.Thread(target=lambda: holder.setdefault("r", self.cli("exec", "--timeout", "90", "--", *self.fixture_command(marker), timeout=100)))
        thread.start(); time.sleep(2)
        current = json.loads(self.cli("status").stdout)
        subprocess.run(["taskkill", "/F", "/PID", str(current["pid"])], capture_output=True)
        thread.join(15)
        if getattr(self, "owner_process", None): self.owner_process.wait(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertNotEqual(holder.get("r").returncode, 0)
        self.assert_fixture_tree_dead(marker)
        self.start_clean()
        self.stop_owner()


if __name__ == "__main__":
    unittest.main()
