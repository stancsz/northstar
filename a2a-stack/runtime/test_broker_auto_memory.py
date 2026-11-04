"""Regression tests for the runtime broker's Claude child isolation.

The broker is the third Claude spawn site in the stack.  Native Claude
auto-memory writes land in the shared Claude project-memory directory, which is
outside a worker's private source write scope, so the flag is pinned child-only
here exactly as it is for the service and the autonomy owner/supervisor.
"""
import json
import os
import sys
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch

NORTHSTAR_ROOT = Path(__file__).resolve().parents[2]
TEST_CONTROL = NORTHSTAR_ROOT / "tmp" / "a2a-stack" / "runtime-tests" / "control"
os.environ["A2A_TEST_CONTROL_DIR"] = str(TEST_CONTROL)
import runner


class BrokerAutoMemoryIsolation(unittest.TestCase):
    def test_claude_command_carries_the_pinned_settings_payload(self):
        command = runner.claude_command("claude.exe", "do one task", ["Read"])
        self.assertIn("--settings", command)
        payload = json.loads(command[command.index("--settings") + 1])
        self.assertEqual(payload, {"env": {runner.AUTO_MEMORY_FLAG: "1"}})

    def test_claude_command_keeps_its_existing_arguments(self):
        command = runner.claude_command("claude.exe", "do one task", ["Read", "Write"], max_turns=4)
        self.assertEqual(command[0], "claude.exe")
        self.assertIn("--output-format", command)
        self.assertIn("stream-json", command)
        self.assertIn("--max-turns", command)
        self.assertEqual(command[command.index("--max-turns") + 1], "4")
        self.assertIn("--allowedTools", command)
        self.assertEqual(command[command.index("--allowedTools") + 1], "Read,Write")
        self.assertEqual(command[-2:], ["--", "do one task"])

    def test_claude_child_environment_pins_the_flag_without_mutating_the_parent(self):
        before = dict(os.environ)
        prompt = TEST_CONTROL.parent / "broker-prompt.md"
        prompt.write_text("do one task", encoding="utf-8")
        try:
            with patch.object(runner.subprocess, "Popen") as popen:
                popen.return_value.pid = 1234
                popen.return_value._handle = 0
                # The broker's pump threads read these pipes until EOF.  A
                # mocked pipe that never yields "" would leave them spinning
                # for the rest of the process, starving any later test that
                # depends on real file replacement.
                popen.return_value.poll.return_value = 0
                popen.return_value.stdout.readline.return_value = ""
                popen.return_value.stderr.readline.return_value = ""
                with patch.object(runner, "Job"):
                    try:
                        runner.broker("run-" + uuid.uuid4().hex, "claude", ["claude.exe"],
                                      prompt_file=prompt, acquire_lock=False)
                    except Exception:
                        pass
            self.assertTrue(popen.called)
            env = popen.call_args.kwargs["env"]
            self.assertEqual(env[runner.AUTO_MEMORY_FLAG], "1")
        finally:
            prompt.unlink(missing_ok=True)
        self.assertEqual(dict(os.environ), before)

    def test_exec_child_environment_does_not_pin_the_flag(self):
        before = dict(os.environ)
        with patch.object(runner.subprocess, "Popen") as popen:
            popen.return_value.pid = 1234
            popen.return_value._handle = 0
            # See the note in the claude-child test: the pump threads need EOF.
            popen.return_value.poll.return_value = 0
            popen.return_value.stdout.readline.return_value = ""
            popen.return_value.stderr.readline.return_value = ""
            with patch.object(runner, "Job"):
                try:
                    runner.broker("run-" + uuid.uuid4().hex, "exec", ["python", "-c", "print(1)"],
                                  acquire_lock=False)
                except Exception:
                    pass
        self.assertTrue(popen.called)
        env = popen.call_args.kwargs["env"]
        self.assertNotIn(runner.AUTO_MEMORY_FLAG, env)
        self.assertEqual(dict(os.environ), before)


if __name__ == "__main__":
    unittest.main()
