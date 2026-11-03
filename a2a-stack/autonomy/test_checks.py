"""Local subprocess fixtures for the trusted goal verifier backend."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import checks

ROOT = Path(__file__).resolve().parents[2]


class TrustedCheckTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "tmp" / "a2a-stack" / "check-build"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.base = Path(self.temp.name)
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()
        self.state = self.base / "goal"
        self.artifacts = self.state / "artifacts"
        self.artifacts.mkdir(parents=True)
        self.source = self.workspace / "source.txt"
        self.source.write_text("candidate baseline", encoding="utf-8")
        self.spec_path = self.state / "spec.json"
        self.output = self.artifacts / "verification.json"

    def tearDown(self):
        self.temp.cleanup()

    def write_spec(self, argv):
        manifest = checks._workspace_candidate(self.workspace, ["source.txt"])
        manifest_path = self.artifacts / "candidate-fixture.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        spec = {"id": "g-fixture", "workspace": str(self.workspace),
                "goal_state_dir": str(self.state),
                "checks": [{"id": "fixture", "argv": argv, "cwd": str(self.workspace)}]}
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        return manifest["candidate"]

    def command(self, code):
        return [sys.executable, "-c", code]

    def test_successful_check_writes_verification_artifact(self):
        candidate = self.write_spec(self.command("print('fixture passed')"))
        report = checks.run_checks(self.spec_path, candidate, self.output)
        self.assertTrue(report["checks_passed"])
        self.assertEqual(report["checks"][0]["exit_code"], 0)
        self.assertIn("fixture passed", report["checks"][0]["output"])
        self.assertEqual(json.loads(self.output.read_text(encoding="utf-8")), report)

    def test_failed_check_keeps_truthful_exit_code_without_failing_backend(self):
        candidate = self.write_spec(self.command("import sys; print('fixture failed'); sys.exit(7)"))
        report = checks.run_checks(self.spec_path, candidate, self.output)
        self.assertFalse(report["checks_passed"])
        self.assertEqual(report["checks"][0]["exit_code"], 7)
        self.assertIn("fixture failed", report["checks"][0]["output"])

    def test_stale_candidate_is_reported_without_running_command(self):
        marker = self.workspace / "ran.txt"
        candidate = self.write_spec(self.command(f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"))
        self.source.write_text("candidate changed after freeze", encoding="utf-8")
        report = checks.run_checks(self.spec_path, candidate, self.output)
        self.assertFalse(report["checks_passed"])
        self.assertIn("STALE", report["error"])
        self.assertEqual(report["checks"], [])
        self.assertFalse(marker.exists())

    def test_output_path_escape_is_rejected_before_execution(self):
        marker = self.workspace / "ran.txt"
        candidate = self.write_spec(self.command(f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"))
        with self.assertRaisesRegex(ValueError, "inside the goal artifacts"):
            checks.run_checks(self.spec_path, candidate, self.state / "escaped.json")
        self.assertFalse(marker.exists())

    def test_candidate_change_during_check_is_detected(self):
        candidate = self.write_spec(self.command(
            f"from pathlib import Path; Path({str(self.source)!r}).write_text('changed by fixture')"))
        report = checks.run_checks(self.spec_path, candidate, self.output)
        self.assertFalse(report["checks_passed"])
        self.assertIn("changed during trusted checks", report["error"])
        self.assertEqual(report["checks"][0]["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
