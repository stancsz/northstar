"""Offline host-manager regressions; no model, provider, HTTP, or live host calls."""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch


STACK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("autonomy_manager", STACK / "autonomy/manager.py")
manager_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager_module)
SCRATCH = STACK / "scratchtmp/a2a-stack/manager-tests"


class GoalManagerTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.state_root = self.root / "host-state"
        self.state_root.mkdir()
        self.manager = manager_module.GoalManager(self.state_root, self.workspace)
        self.addCleanup(lambda: asyncio.run(self.manager.close()))
        self.trusted = {
            "unit": {
                "description": "Run the approved local unit check",
                "argv": [sys.executable, "-B", "-c", "print('approved')"],
                "cwd": ".",
            }
        }
        (self.state_root / "trusted-checks.json").write_text(
            json.dumps(self.trusted), encoding="utf-8"
        )

    def request(self, **changes):
        request = {
            "workspace": str(self.workspace),
            "goal": "  Build the requested behavior  ",
            "acceptance": ["  Candidate passes the check  ", "Independent review approves it"],
            "write_paths": ["src", "notes.txt"],
            "check_ids": ["unit"],
            "constraints": ["Keep changes scoped"],
            "required_inputs": ["source.txt"],
            "user_gates": ["Human sets the next goal"],
        }
        request.update(changes)
        return request

    def create_without_launch(self, request):
        with patch.object(manager_module.GoalManager, "_launch", autospec=True) as launch:
            result = asyncio.run(self.manager.create(request))
        return result, launch

    def test_create_snapshots_goal_scope_checks_and_baseline(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.py").write_text("before = True\n", encoding="utf-8")
        (self.workspace / "notes.txt").write_text("baseline notes\n", encoding="utf-8")
        (self.workspace / "source.txt").write_text("required evidence\n", encoding="utf-8")
        request = self.request()

        result, launch = self.create_without_launch(request)
        spec_path = Path(result["spec_path"])
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

        self.assertRegex(result["goal_id"], r"^g-[a-f0-9]{32}$")
        self.assertEqual(spec["id"], result["goal_id"])
        self.assertEqual(spec["goal"], "Build the requested behavior")
        self.assertEqual(spec["acceptance"], ["Candidate passes the check", "Independent review approves it"])
        self.assertEqual(spec["workspace"], str(self.workspace))
        self.assertEqual(spec["write_paths"], ["notes.txt", "src"])
        self.assertEqual(spec["baseline"], {
            "notes.txt": hashlib.sha256((self.workspace / "notes.txt").read_bytes()).hexdigest(),
            "src/main.py": hashlib.sha256((self.workspace / "src/main.py").read_bytes()).hexdigest(),
        })
        self.assertEqual(spec["checks"], [{
            "id": "unit",
            "argv": list(self.trusted["unit"]["argv"]),
            "cwd": str(self.workspace),
        }])
        self.assertEqual(spec["required_inputs"], [str(self.workspace / "source.txt")])
        self.assertEqual(spec["user_gates"], ["Human sets the next goal"])
        self.assertEqual(spec["constraints"], ["Keep changes scoped"])
        self.assertEqual(result["state"]["status"], "RUNNING")
        self.assertIsNone(result["state"]["session_id"])
        launch.assert_called_once_with(self.manager, result["goal_id"])

        # Mutating caller-owned values after creation cannot rewrite the persisted goal.
        request["acceptance"].append("Injected criterion")
        request["write_paths"].append("outside")
        request["check_ids"].clear()
        self.trusted["unit"]["argv"][0] = "untrusted-command"
        self.assertEqual(json.loads(spec_path.read_text(encoding="utf-8")), spec)

    def test_rejects_raw_commands_out_of_scope_paths_and_unknown_checks(self):
        base = self.request()
        for field in ("command", "claude_args", "argv"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "commands and CLI options are not accepted"):
                    asyncio.run(self.manager.create({**base, field: ["claude", "--dangerously-skip-permissions"]}))
        with self.assertRaisesRegex(ValueError, "escapes workspace"):
            asyncio.run(self.manager.create(self.request(write_paths=["../outside.txt"])))
        with self.assertRaisesRegex(ValueError, "authorized workspace"):
            asyncio.run(self.manager.create(self.request(required_inputs=["../outside.txt"])))
        with self.assertRaisesRegex(ValueError, "unknown trusted check"):
            asyncio.run(self.manager.create(self.request(check_ids=["arbitrary shell"])) )
        self.assertEqual(self.manager.list(), [])

    def test_candidate_freeze_hashes_actual_file_and_enforces_goal_scope(self):
        (self.workspace / "src").mkdir()
        candidate = self.workspace / "src/feature.py"
        candidate.write_bytes(b"value = 41 + 1\n")
        outside = self.workspace / "unlisted.py"
        outside.write_text("outside goal scope\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))

        frozen = self.manager.freeze(result["goal_id"], ["src/feature.py"])
        manifest = json.loads(Path(frozen["manifest_path"]).read_text(encoding="utf-8"))
        expected_hash = hashlib.sha256(b"value = 41 + 1\n").hexdigest()
        self.assertEqual(frozen["candidate"], manifest["candidate"])
        self.assertEqual(manifest["files"], {"src/feature.py": expected_hash})
        candidate.write_bytes(b"value = 42\n")
        self.assertNotEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), manifest["files"]["src/feature.py"])
        with self.assertRaisesRegex(ValueError, "outside immutable goal scope"):
            self.manager.freeze(result["goal_id"], ["unlisted.py"])
        with self.assertRaisesRegex(ValueError, "outside immutable goal scope"):
            self.manager.freeze(result["goal_id"], ["../outside.py"])

    def test_freeze_covers_every_changed_scoped_file(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / "src/b.py").write_text("b = 0\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))
        (self.workspace / "src/a.py").write_text("a = 1\n", encoding="utf-8")
        (self.workspace / "src/b.py").write_text("b = 1\n", encoding="utf-8")

        frozen = self.manager.freeze(result["goal_id"], ["src/a.py"])

        self.assertEqual(set(frozen["files"]), {"src/a.py", "src/b.py"},
                         "a frozen candidate must cover every changed scoped file")
        manifest = json.loads(Path(frozen["manifest_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["files"], frozen["files"])
        self.assertEqual(frozen["candidate"], manifest["candidate"])

    def test_freeze_rejects_a_deleted_scoped_file(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/gone.py").write_text("remove me\n", encoding="utf-8")
        (self.workspace / "src/kept.py").write_text("keep me\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))
        (self.workspace / "src/gone.py").unlink()
        (self.workspace / "src/kept.py").write_text("changed\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "deleted") as raised:
            self.manager.freeze(result["goal_id"], ["src/kept.py"])

        self.assertIn("src/gone.py", str(raised.exception))
        self.assertTrue(str(raised.exception).strip())

    def test_freeze_rejects_an_entirely_deleted_scoped_directory(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / "src/b.py").write_text("b = 0\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))
        shutil.rmtree(self.workspace / "src")

        with self.assertRaisesRegex(ValueError, "deleted") as raised:
            self.manager.freeze(result["goal_id"], ["src/a.py"])

        message = str(raised.exception)
        self.assertIn("src/a.py", message)
        self.assertIn("src/b.py", message)

    def test_freeze_rejects_a_scoped_directory_replaced_by_a_file(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / "src/b.py").write_text("b = 0\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))
        shutil.rmtree(self.workspace / "src")
        (self.workspace / "src").write_text("now a regular file\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "deleted") as raised:
            self.manager.freeze(result["goal_id"], ["src"])

        message = str(raised.exception)
        self.assertIn("src/a.py", message)
        self.assertIn("src/b.py", message)

    def test_root_scope_freeze_covers_every_changed_workspace_file(self):
        (self.workspace / "a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / "b.py").write_text("b = 0\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["."]))
        (self.workspace / "a.py").write_text("a = 1\n", encoding="utf-8")
        (self.workspace / "b.py").write_text("b = 1\n", encoding="utf-8")

        frozen = self.manager.freeze(result["goal_id"], ["a.py"])

        self.assertEqual(set(frozen["files"]), {"a.py", "b.py"},
                         "a workspace-root scope must cover every changed project file")
        spec = json.loads(Path(result["spec_path"]).read_text(encoding="utf-8"))
        self.assertEqual(spec["write_paths"], ["."])
        self.assertEqual(sorted(spec["baseline"]), ["a.py", "b.py"])
        self.assertFalse(Path(result["state_dir"]).is_relative_to(self.workspace),
                         "operational goal state must stay outside the root-scoped workspace")

    def test_root_scope_freeze_detects_nested_and_hidden_path_changes(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src" / "a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / ".generated").mkdir()
        (self.workspace / ".generated" / "out.txt").write_text("out = 0\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["."]))
        (self.workspace / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
        (self.workspace / ".generated" / "out.txt").write_text("out = 1\n", encoding="utf-8")

        frozen = self.manager.freeze(result["goal_id"], ["src/a.py"])

        self.assertEqual(set(frozen["files"]), {".generated/out.txt", "src/a.py"},
                         "a workspace-root scope must not hide generated or nested path changes")

    def test_root_scope_freeze_rejects_a_deleted_workspace_file(self):
        (self.workspace / "a.py").write_text("a = 0\n", encoding="utf-8")
        (self.workspace / "gone.py").write_text("remove me\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["."]))
        (self.workspace / "gone.py").unlink()

        with self.assertRaisesRegex(ValueError, "deleted") as raised:
            self.manager.freeze(result["goal_id"], ["a.py"])

        self.assertIn("gone.py", str(raised.exception))

    def test_directory_scope_baseline_records_contained_original_hashes(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.py").write_text("original main\n", encoding="utf-8")
        (self.workspace / "src/nested").mkdir()
        (self.workspace / "src/nested/deep.py").write_text("original deep\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src"]))
        spec = json.loads(Path(result["spec_path"]).read_text(encoding="utf-8"))

        self.assertEqual(spec["baseline"], {
            "src/main.py": hashlib.sha256((self.workspace / "src/main.py").read_bytes()).hexdigest(),
            "src/nested/deep.py": hashlib.sha256((self.workspace / "src/nested/deep.py").read_bytes()).hexdigest(),
        })

    def test_unchanged_preexisting_file_is_not_goal_work(self):
        (self.workspace / "src").mkdir()
        (self.workspace / "src/legacy.py").write_text("legacy = 1\n", encoding="utf-8")
        result, _ = self.create_without_launch(self.request(write_paths=["src/legacy.py"]))

        frozen = self.manager.freeze(result["goal_id"], ["src/legacy.py"])

        self.assertEqual(set(frozen["files"]), {"src/legacy.py"})

    def test_exact_file_goal_path_keeps_working(self):
        (self.workspace / "notes.txt").write_text("baseline notes\n", encoding="utf-8")
        original = hashlib.sha256((self.workspace / "notes.txt").read_bytes()).hexdigest()
        result, _ = self.create_without_launch(self.request(write_paths=["notes.txt"]))
        spec = json.loads(Path(result["spec_path"]).read_text(encoding="utf-8"))
        (self.workspace / "notes.txt").write_text("changed notes\n", encoding="utf-8")
        changed = hashlib.sha256((self.workspace / "notes.txt").read_bytes()).hexdigest()

        frozen = self.manager.freeze(result["goal_id"], ["notes.txt"])

        self.assertEqual(spec["baseline"], {"notes.txt": original})
        self.assertEqual(set(frozen["files"]), {"notes.txt"})
        self.assertEqual(frozen["files"]["notes.txt"], changed)

    def test_complete_report_waits_for_human_to_set_next_goal(self):
        result, launch = self.create_without_launch(self.request())
        state_path = Path(result["state_dir"]) / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(status="COMPLETE", last_summary="All acceptance criteria passed")
        manager_module.runtime.atomic_json(state_path, state)

        report = self.manager.report(result["goal_id"])
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["summary"], "All acceptance criteria passed")
        self.assertEqual(report["next_user_action"], "查看结果后，由你设置下一条 Goal。")
        self.assertEqual(len(self.manager.list()), 1)
        launch.assert_called_once()

    @unittest.skipUnless(os.name == "nt", "requires real Windows suspended process and Job Object")
    def test_watch_restarts_real_fixture_process_then_stops_on_complete(self):
        goal_id = "g-" + "a" * 32
        goal_dir = self.manager._dir(goal_id)
        goal_dir.mkdir(parents=True)
        manager_module.runtime.atomic_json(goal_dir / "spec.json", {
            "id": goal_id,
            "workspace": str(self.workspace),
            "goal": "Recover the same goal after the runner exits",
            "acceptance": ["The fixture reaches COMPLETE after a restart"],
        })
        manager_module.runtime.atomic_json(goal_dir / "state.json", {
            "id": goal_id,
            "status": "RUNNING",
            "session_id": "native-session-preserved",
            "recovery_count": 0,
        })
        fixture = SCRATCH / "manager-restart-fixture.py"
        fixture.write_text(textwrap.dedent("""
            import json
            from pathlib import Path
            import sys

            goal_dir = Path(sys.argv[1])
            spec = json.loads((goal_dir / "spec.json").read_text(encoding="utf-8"))
            state_path = goal_dir / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            count_path = goal_dir / "fixture-starts.txt"
            count = int(count_path.read_text(encoding="utf-8")) + 1 if count_path.exists() else 1
            count_path.write_text(str(count), encoding="utf-8")
            with (goal_dir / "fixture-observations.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"goal_id": spec["id"], "session_id": state["session_id"]}) + "\\n")
            if count == 1:
                raise SystemExit(1)
            state["status"] = "COMPLETE"
            state["last_summary"] = "Fixture completed on automatic host restart"
            state_path.write_text(json.dumps(state), encoding="utf-8")
        """), encoding="utf-8")

        real_popen = subprocess.Popen
        starts = []

        def fixture_popen(original_argv, **kwargs):
            starts.append((original_argv, dict(kwargs)))
            fixture_argv = [sys.executable, "-B", str(fixture), str(goal_dir)]
            return real_popen(fixture_argv, **kwargs)

        real_job_factory = manager_module.runtime.Job
        owned_jobs = []

        class TrackedJob:
            def __init__(self):
                self.inner = real_job_factory()
                self.closed = False
                owned_jobs.append(self)

            def assign(self, process):
                return self.inner.assign(process)

            def close(self):
                self.inner.close()
                self.closed = True

        try:
            with patch.object(manager_module.subprocess, "Popen", side_effect=fixture_popen), \
                    patch.object(manager_module.runtime, "Job", TrackedJob):
                asyncio.run(asyncio.wait_for(self.manager._watch(goal_id), timeout=10))
        finally:
            fixture.unlink(missing_ok=True)

        final_state = json.loads((goal_dir / "state.json").read_text(encoding="utf-8"))
        observations = [json.loads(line) for line in
                        (goal_dir / "fixture-observations.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(starts), 2)
        self.assertEqual((goal_dir / "fixture-starts.txt").read_text(encoding="utf-8"), "2")
        self.assertEqual([entry["goal_id"] for entry in observations], [goal_id, goal_id])
        self.assertEqual([entry["session_id"] for entry in observations],
                         ["native-session-preserved", "native-session-preserved"])
        self.assertEqual(final_state["status"], "COMPLETE")
        self.assertEqual(final_state["session_id"], "native-session-preserved")
        self.assertEqual(final_state["host_restart_count"], 1)
        self.assertEqual(self.manager.processes, {})
        self.assertEqual(len(owned_jobs), 2)
        self.assertTrue(all(job.closed and job.inner.handle is None for job in owned_jobs))
        for _argv, kwargs in starts:
            self.assertEqual(kwargs["cwd"], self.workspace)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
            self.assertIsNotNone(kwargs["stderr"])
            self.assertTrue(kwargs["creationflags"] & 0x4)  # CREATE_SUSPENDED
            self.assertTrue(kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW)


if __name__ == "__main__":
    unittest.main()
