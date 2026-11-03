"""Unit tests for trusted per-job MCP configuration and allowed_tools.

These are pure configuration tests: nothing here launches a server, a Claude
process, or an MCP server.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

AGENT_DIR = Path(__file__).resolve().parent
STACK_ROOT = AGENT_DIR.parent
REPO_ROOT = STACK_ROOT.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(STACK_ROOT / "runtime") not in sys.path:
    sys.path.insert(0, str(STACK_ROOT / "runtime"))

import service  # noqa: E402  imports the real A2A SDK

FIXTURE_ROOT = REPO_ROOT / "tmp" / "a2a-stack" / "config-tests"
MCP_FIXTURE = FIXTURE_ROOT / "mcp-config.json"
PROMPT_FIXTURE = FIXTURE_ROOT / "prompt.txt"


def _write_fixtures() -> None:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    MCP_FIXTURE.write_text('{"mcpServers": {}}\n', encoding="utf-8")
    PROMPT_FIXTURE.write_text("hello\n", encoding="utf-8")


class JobConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _write_fixtures()

    def _job(self, **overrides) -> dict:
        data = {
            "mode": "claude",
            "prompt_file": str(PROMPT_FIXTURE.relative_to(REPO_ROOT)).replace("\\", "/"),
            "tools": ["Read", "Edit"],
            "timeout_seconds": 30,
            "max_turns": 5,
        }
        data.update(overrides)
        return data

    def _argv(self, config: dict) -> list[str]:
        with mock.patch.object(service, "resolve_claude_exe", return_value="claude.exe"):
            return service._build_claude_argv(config)

    # -- happy paths --------------------------------------------------------- #
    def test_mcp_config_and_allowed_tools_reach_argv(self) -> None:
        rel_mcp = str(MCP_FIXTURE.relative_to(REPO_ROOT)).replace("\\", "/")
        config = service.validate_job(
            self._job(mcp_config=rel_mcp, allowed_tools=["Read", "MCPtoolname"]), "mcpjob"
        )

        self.assertEqual(config["mcp_config"], MCP_FIXTURE)
        self.assertEqual(config["allowed_tools"], ["Read", "MCPtoolname"])

        argv = self._argv(config)
        self.assertIn("--mcp-config", argv)
        self.assertEqual(argv[argv.index("--mcp-config") + 1], str(MCP_FIXTURE))
        self.assertIn("--strict-mcp-config", argv)
        self.assertIn("--allowedTools", argv)
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,MCPtoolname")
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Edit")

    def test_default_without_mcp_is_unchanged(self) -> None:
        config = service.validate_job(self._job(), "plainjob")

        self.assertNotIn("mcp_config", config)
        self.assertEqual(config["allowed_tools"], config["tools"])

        argv = self._argv(config)
        self.assertNotIn("--mcp-config", argv)
        self.assertNotIn("--strict-mcp-config", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Edit")
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,Edit")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertNotIn("--max-budget", argv)

    # -- rejection paths ----------------------------------------------------- #
    def test_mcp_config_outside_workspace_rejected(self) -> None:
        outside = Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "system32" / "drivers" / "etc" / "hosts"
        with self.assertRaises(service.JobFailed):
            service.validate_job(self._job(mcp_config=str(outside)), "escapejob")

    def test_missing_mcp_config_rejected(self) -> None:
        rel_missing = str((FIXTURE_ROOT / "missing-config.json").relative_to(REPO_ROOT)).replace("\\", "/")
        with self.assertRaises(service.JobFailed):
            service.validate_job(self._job(mcp_config=rel_missing), "missingjob")

    def test_non_string_mcp_config_rejected(self) -> None:
        for bad in (123, {"path": "x"}, ["x"], True):
            with self.subTest(bad=bad):
                with self.assertRaises(service.JobFailed):
                    service.validate_job(self._job(mcp_config=bad), "badtypejob")

    def test_work_is_uncapped_by_default_under_latest_user_instruction(self) -> None:
        data = self._job()
        data.pop('max_turns')
        data.pop('timeout_seconds')
        config = service.validate_job(data, 'uncapped')
        self.assertIsNone(config['max_turns'])
        self.assertIsNone(config['timeout_seconds'])
        argv = self._argv(config)
        self.assertNotIn('--max-turns', argv)
        self.assertNotIn('--max-budget-usd', argv)

    def test_explicit_large_operational_limits_have_no_arbitrary_ceiling(self) -> None:
        config = service.validate_job(self._job(max_turns=100000, timeout_seconds=1000000), 'explicit')
        self.assertEqual(config['max_turns'], 100000)
        self.assertEqual(config['timeout_seconds'], 1000000)
        self.assertEqual(self._argv(config)[self._argv(config).index('--max-turns') + 1], '100000')

    def test_invalid_explicit_operational_values_are_rejected(self) -> None:
        for field in ('max_turns', 'timeout_seconds'):
            for value in (-1, 0, True, '3'):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(service.JobFailed):
                        service.validate_job(self._job(**{field: value}), 'invalid')

    def test_invalid_allowed_tools_rejected(self) -> None:
        for bad in ("Read", 5, ["Read", 7], {"Read": True}):
            with self.subTest(bad=bad):
                with self.assertRaises(service.JobFailed):
                    service.validate_job(self._job(allowed_tools=bad), "badtoolsjob")


if __name__ == "__main__":
    unittest.main()
