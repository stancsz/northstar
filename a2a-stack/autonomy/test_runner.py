"""Offline controller tests: no native model, service, or provider calls."""
import importlib.util
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

SPEC = importlib.util.spec_from_file_location("autonomous_runner", Path(__file__).with_name("runner.py"))
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
SCRATCH = Path(__file__).resolve().parents[2] / "tmp/a2a-stack/qa/council-review/runner-fix"


class Fixture(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.goal = self.root / "goal"
        self.spec = {"id": "goal", "workspace": str(self.root), "goal": "Implement tested change",
            "acceptance": ["Tests pass", "Exact candidate independently reviewed"], "write_paths": ["source.py"],
            "checks": [{"id": "unit", "argv": [sys.executable, "-c", "print('ok')"], "cwd": str(self.root)}],
            "mcp_config": str(self.root / "mcp.json"), "owner_prompt": str(self.root / "owner.txt"),
            "supervisor_prompt": str(self.root / "supervisor.txt"), "state_root": str(self.root / "host")}
        self.spec.update(baseline={"source.py": None}, required_inputs=[], user_gates=[])
        (self.root / "source.py").write_text("version = 1\n")
        runner.review_helpers.ROOT = self.root
        self.manifest = runner.review_helpers.candidate(["source.py"])
        self.manifest_path = self.root / "candidate.json"
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.reference = {"stack_id": "team", "role_id": "critic", "task_id": "qa-1"}
        self.assignments = self.root / "host/stacks/team/assignments"
        self.assignments.mkdir(parents=True)
        self.assignment = {"stack_id": "team", "role_id": "critic", "task_id": "qa-1",
            "candidate": self.manifest["candidate"], "write_paths": [], "acceptance": self.spec["acceptance"]}
        self.save_assignment()
        (self.assignments / "producer.json").write_text(json.dumps({"stack_id": "team", "role_id": "coder",
            "task_id": "code-1", "write_paths": ["source.py"]}))
        self.task = {"id": "qa-1", "status": {"state": "TASK_STATE_COMPLETED"}, "artifacts": [
            {"parts": [{"text": json.dumps({"candidate": self.manifest["candidate"], "verdict": "READY", "evidence": ["Inspected source.py and exact criteria"]})}]}]}
        self.stack = {"stack_id": "team", "goal_id": self.spec["id"],
            "roles": [{"id": "critic", "profile": "reviewer"}, {"id": "coder", "profile": "coder"}],
            "_producer_tasks": [{"role_id": "coder", "task_id": "code-1", "task": {
                "id": "code-1", "status": {"state": "TASK_STATE_COMPLETED"}, "artifacts": [{"parts": [{"text": "Implemented exact scoped source"}]}]}}]}

    def save_assignment(self):
        (self.assignments / "review.json").write_text(json.dumps(self.assignment))

    def proposal(self):
        return {"status": "complete", "summary": "Done", "candidate_manifest": str(self.manifest_path),
                "review": self.reference, "blocker": None}

    def validate(self):
        return runner.validate_review(self.spec, self.reference, self.manifest, self.task, self.stack)

    def test_actual_review_and_stale_candidate(self):
        self.assertTrue(self.validate()["accepted"])
        (self.root / "source.py").write_text("version = 2\n")
        with self.assertRaisesRegex(ValueError, "STALE"):
            runner.freeze_current(self.spec, self.goal, str(self.manifest_path))

    def test_forged_or_mismatched_review_rejected(self):
        for mutation in ("candidate", "scope", "criteria", "profile", "task", "pending", "artifact", "goal"):
            with self.subTest(mutation=mutation):
                # Each mutation is reversed after a genuine rejection.
                old_assignment = json.loads(json.dumps(self.assignment))
                old_task = json.loads(json.dumps(self.task))
                old_stack = json.loads(json.dumps(self.stack))
                if mutation == "candidate": self.assignment["candidate"] = "wrong"
                if mutation == "scope": self.assignment["write_paths"] = ["source.py"]
                if mutation == "criteria": self.assignment["acceptance"] = ["Tests pass"]
                if mutation == "profile": self.stack["roles"][0]["profile"] = "coder"
                if mutation == "task": self.task["id"] = "forged"
                if mutation == "pending": self.task["status"]["state"] = "TASK_STATE_WORKING"
                if mutation == "artifact": self.task["artifacts"] = []
                if mutation == "goal": self.stack["goal_id"] = "another-goal"
                self.save_assignment()
                with self.assertRaises(ValueError): self.validate()
                self.assignment, self.task, self.stack = old_assignment, old_task, old_stack
                self.save_assignment()

    def test_scope_and_postcheck_mutation_rejected(self):
        self.spec["write_paths"] = []
        with self.assertRaisesRegex(ValueError, "outside explicit"):
            runner.freeze_current(self.spec, self.goal, str(self.manifest_path))

    def test_session_resume_no_default_ceilings(self):
        argv = runner.claude_argv(self.spec, "same-native-session", executable="claude.exe")
        self.assertEqual(argv[argv.index("--resume") + 1], "same-native-session")
        self.assertNotIn("--max-turns", argv)
        self.assertNotIn("--max-budget-usd", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob")
        self.assertNotIn("Bash", argv[argv.index("--allowedTools") + 1].split(","))
        self.assertIn("Bash", argv[argv.index("--disallowedTools") + 1])
        for tool in runner.USER_GOAL_MUTATIONS:
            self.assertIn(tool, argv[argv.index("--disallowedTools") + 1].split(","))
        self.assertEqual(len(runner.MCP_TOOLS), 11)
        supervisor = runner.claude_argv(self.spec, "same-native-session", True, executable="claude.exe")
        self.assertNotIn("--resume", supervisor)
        self.assertEqual(supervisor[supervisor.index("--allowedTools") + 1], "Read,Glob")
        for tool in runner.USER_GOAL_MUTATIONS:
            self.assertIn(tool, supervisor[supervisor.index("--disallowedTools") + 1].split(","))
        journal = runner.Journal(self.goal, self.spec)
        journal.record("session_initialized", session_id="native-123")
        self.assertEqual(runner.Journal(self.goal, self.spec).state["session_id"], "native-123")
        self.spec["goal"] = "Different goal"
        with self.assertRaisesRegex(ValueError, "Immutable"):
            runner.Journal(self.goal, self.spec)

    def test_transient_then_check_failure_then_success(self):
        fixture = self
        class Fake:
            turns = 0
            checks = 0
            feedback = []
            def owner(self, feedback):
                self.turns += 1
                self.feedback.append(feedback)
                if self.turns == 1: raise OSError("429 temporary provider interruption")
                return fixture.proposal()
            def supervisor(self, facts):
                return {"classification": "recoverable", "advice": "Inspect causal failure; repair", "evidence": []}
            def fetch_review(self, reference): return fixture.task, fixture.stack
            def check(self, check):
                self.checks += 1
                return {"exit_code": 1 if self.checks == 1 else 0, "output": "actual fixture result"}
        backend = Fake()
        journal = runner.Journal(self.goal, self.spec)
        self.assertEqual(runner.run_goal(self.spec, journal, backend, lambda _: None), 0)
        self.assertEqual(backend.turns, 3)
        self.assertEqual(journal.state["status"], "COMPLETE")
        self.assertEqual(journal.state["recovery_count"], 2)
        self.assertIn("Check failed", backend.feedback[-1])
        self.assertEqual(journal.state["accepted_receipt"]["candidate"], self.manifest["candidate"])
        self.assertEqual(journal.state["last_summary"], "Done")

    def test_supervisor_failure_recovers_and_cancellation(self):
        fixture = self
        class Fake:
            turns = 0
            def owner(self, feedback):
                self.turns += 1
                if self.turns == 1: raise ValueError("Recoverable coding bug")
                (fixture.goal / "cancel.request").touch()
                return {"status": "continue"}
            def supervisor(self, facts): raise OSError("529")
        journal = runner.Journal(self.goal, self.spec)
        backend = Fake()
        self.assertEqual(runner.run_goal(self.spec, journal, backend, lambda _: None), 0)
        self.assertEqual(journal.state["status"], "CANCELED")
        self.assertEqual(backend.turns, 2)

    def test_check_mutation_requires_new_candidate_review(self):
        fixture = self
        class Fake:
            turns = 0
            diagnosed = None
            def owner(self, feedback):
                self.turns += 1
                if self.turns > 1:
                    (fixture.goal / "cancel.request").touch()
                    return {"status": "continue"}
                return fixture.proposal()
            def fetch_review(self, reference): return fixture.task, fixture.stack
            def check(self, check):
                (fixture.root / "source.py").write_text("changed during verification\n")
                return {"exit_code": 0, "output": "check passed but changed candidate"}
            def supervisor(self, facts):
                self.diagnosed = facts
                return {"classification": "recoverable", "advice": "Freeze and review changed files", "evidence": []}
        journal = runner.Journal(self.goal, self.spec)
        backend = Fake()
        runner.run_goal(self.spec, journal, backend, lambda _: None)
        self.assertIn("STALE", backend.diagnosed["error"])
        self.assertNotIn("accepted_receipt", journal.state)
        self.assertEqual(journal.state["status"], "CANCELED")

    def test_only_external_dependency_can_need_user(self):
        diagnosis = {"classification": "external_dependency", "evidence": ["Observed missing required authority"]}
        for kind in ("test_failure", "tool_error", "429", "bug", "pending"):
            self.assertFalse(runner.external_blocker({"blocker": {"kind": kind, "message": "blocked", "evidence": ["fact"]}}, diagnosis))
        self.assertFalse(runner.external_blocker({"blocker": {"kind": "credentials", "message": "missing", "evidence": []}}, diagnosis))
        credentials = {"blocker": {"kind": "credentials", "message": "missing", "evidence": ["AssertionError: ordinary failed check, allegedly needs login"]}}
        self.assertFalse(runner.external_blocker(credentials, diagnosis))
        observations = {"owner": {"source": "native_metadata", "terminal": True, "http_status": 401}}
        self.assertTrue(runner.external_blocker(credentials, diagnosis, self.spec, observations))
        proposal = {"blocker": {"kind": "missing_external_input", "message": "Owner must supply required document", "evidence": ["Required source document is unavailable"]}}
        self.assertFalse(runner.external_blocker(proposal, diagnosis, self.spec))
        missing_path = str(self.root / "required-source.txt")
        proposal["blocker"].update(input_path=missing_path, evidence=[missing_path])
        self.assertFalse(runner.external_blocker(proposal, diagnosis, self.spec))
        self.spec["required_inputs"] = [missing_path]
        self.assertTrue(runner.external_blocker(proposal, diagnosis, self.spec))
        self.assertFalse(runner.external_blocker(proposal, {"classification": "recoverable", "evidence": ["Can continue locally"]}))
        Path(missing_path).touch()
        self.assertFalse(runner.external_blocker(proposal, diagnosis, self.spec))
        gate = {"blocker": {"kind": "missing_authority", "gate": "publish", "message": "Owner decision", "evidence": ["Publication gate"]}}
        self.assertFalse(runner.external_blocker(gate, diagnosis, self.spec))
        self.spec["user_gates"] = ["publish"]
        self.assertTrue(runner.external_blocker(gate, diagnosis, self.spec))

    def test_bound_producer_required_for_changed_files(self):
        self.assertEqual(self.validate()["producers"][0]["task_id"], "code-1")
        self.stack["_producer_tasks"] = []
        with self.assertRaisesRegex(ValueError, "coder provenance"):
            self.validate()
        self.spec["baseline"] = dict(self.manifest["files"])
        receipt = self.validate()
        self.assertEqual(receipt["author"], "baseline:goal")
        self.assertEqual(receipt["producers"], [])

    def test_failed_first_producer_does_not_discard_continuation(self):
        self.stack["_producer_tasks"].insert(0, {"role_id": "coder", "task_id": "failed-first", "task": {
            "id": "failed-first", "status": {"state": "TASK_STATE_FAILED"}, "artifacts": []}})
        (self.assignments / "first.json").write_text(json.dumps({"stack_id": "team", "role_id": "coder",
            "task_id": "failed-first", "write_paths": ["source.py"]}))
        self.assertTrue(self.validate()["accepted"])

    def test_cross_stack_producer_and_pending_writer_guard(self):
        alternate = self.root / "host/stacks/code-team/assignments"
        alternate.mkdir(parents=True)
        (alternate / "writer.json").write_text(json.dumps({"stack_id": "code-team", "role_id": "worker",
            "task_id": "cross-stack-code", "write_paths": ["source.py"]}))
        self.stack["all_goal_producers"] = [{"stack_id": "code-team", "goal_id": "goal", "profile": "coder",
            "role_id": "worker", "task_id": "cross-stack-code", "task": {"id": "cross-stack-code",
                "status": {"state": "TASK_STATE_COMPLETED"}, "artifacts": [{"parts": [{"text": "Scoped change"}]}]}}]
        accepted = self.validate()
        self.assertEqual(accepted["producers"][0]["stack_id"], "code-team")
        self.assertIn("code-team/worker/cross-stack-code", accepted["author"])
        self.stack["all_goal_producers"].append({"stack_id": "code-team", "goal_id": "goal", "profile": "coder",
            "role_id": "other", "task_id": "pending-write", "task": {"id": "pending-write",
                "status": {"state": "TASK_STATE_WORKING"}}})
        with self.assertRaisesRegex(ValueError, "still active"):
            self.validate()

    def test_one_fenced_object_with_prose_and_ambiguous_objects(self):
        value = {"candidate": "exact", "verdict": "READY", "evidence": ["source inspected"]}
        artifact = "## Finding\nReviewed source.\n```json\n" + json.dumps(value) + "\n```\nReview complete."
        self.assertEqual(runner.parse_object(artifact), value)
        self.task["artifacts"][0]["parts"][0]["text"] = "## Finding\n```json\n" + json.dumps({"candidate": self.manifest["candidate"], "verdict": "READY", "evidence": ["exact review"]}) + "\n```\nDone."
        self.assertTrue(self.validate()["accepted"])
        for ambiguous in (artifact + '\n{"verdict":"NOT READY"}', artifact + '\n```json\n{"verdict":"NOT READY"}\n```', '{"a":1} {"a":2}', '```json\n[]\n```'):
            with self.subTest(ambiguous=ambiguous), self.assertRaises(ValueError):
                runner.parse_object(ambiguous)

    def test_safe_native_diagnostic_categories(self):
        self.assertEqual(runner.native_diagnostic({"type": "result", "result": "API error: 429 private payload sk-ant-secret"}),
                         {"http_status": 429, "error_category": "rate_limited"})
        self.assertEqual(runner.native_diagnostic({"error": {"type": "overloaded_error", "message": "private payload"}}),
                         {"error_category": "overloaded"})
        self.assertEqual(runner.native_diagnostic({"result": "Tool quoted API error: 401 credential"}), {})
        self.assertEqual(runner.native_diagnostic({"error": {"code": "unknown-secret-value"}}), {})
        journal = runner.Journal(self.goal, self.spec)
        backend = runner.NativeBackend(self.spec, journal)
        event = {"type": "result", "subtype": "error_during_execution", "is_error": True,
                 "result": "API error: 529 secret payload that must not persist"}
        script = "import sys,json; sys.stdin.read(); print(json.dumps(" + repr(event) + "))"
        with self.assertRaisesRegex(ValueError, "overloaded") as raised:
            backend.process([sys.executable, "-c", script], "fixture prompt")
        self.assertNotIn("secret payload", str(raised.exception))
        self.assertNotIn("secret payload", (self.goal / "events.jsonl").read_text())

    def test_both_native_contexts_auth_failure_escalates_from_metadata(self):
        journal = runner.Journal(self.goal, self.spec)
        native = runner.NativeBackend(self.spec, journal)
        event = {"type": "result", "subtype": "error_during_execution", "is_error": True,
                 "error": {"code": 401}, "result": "Secret account details"}
        script = "import sys,json; sys.stdin.read(); print(json.dumps(" + repr(event) + "))"
        class Fake:
            def owner(self, feedback):
                return native.process([sys.executable, "-c", script], "fixture", "owner")
            def supervisor(self, facts):
                return native.process([sys.executable, "-c", script], "fixture", "supervisor")
        runner.run_goal(self.spec, journal, Fake(), lambda _: None)
        self.assertEqual(journal.state["status"], "NEEDS_USER")
        self.assertEqual(journal.state["native_failures"]["owner"]["http_status"], 401)
        self.assertNotIn("Secret account details", (self.goal / "events.jsonl").read_text())

    def test_missing_native_session_resets_context_and_continues_same_goal(self):
        fixture = self
        journal = runner.Journal(self.goal, self.spec)
        journal.record("initial", session_id="missing-native-session")
        native = runner.NativeBackend(self.spec, journal)
        script = "import sys; sys.stdin.read(); print('No conversation found with session ID: missing-native-session', file=sys.stderr); sys.exit(1)"
        class Fake:
            turns = 0
            feedback = None
            def owner(self, feedback):
                self.turns += 1
                if self.turns == 1:
                    return native.process([sys.executable, "-c", script], "fixture", "owner")
                self.feedback = feedback
                fixture.assertIsNone(journal.state["session_id"])
                fixture.assertEqual(journal.state["id"], fixture.spec["id"])
                argv = runner.claude_argv(fixture.spec, journal.state["session_id"], executable="claude.exe")
                fixture.assertNotIn("--resume", argv)
                fixture.assertNotIn("--max-turns", argv)
                journal.record("session_initialized", session_id="fresh-native-context")
                return fixture.proposal()
            def supervisor(self, facts):
                return {"classification": "recoverable", "advice": "Reconcile existing stacks in fresh context", "evidence": []}
            def fetch_review(self, reference): return fixture.task, fixture.stack
            def check(self, check): return {"exit_code": 0, "output": "verified"}
        backend = Fake()
        runner.run_goal(self.spec, journal, backend, lambda _: None)
        self.assertEqual(journal.state["status"], "COMPLETE")
        self.assertEqual(journal.state["previous_session_ids"], ["missing-native-session"])
        self.assertIn("missing-native-session", backend.feedback)
        self.assertIn("session_not_found", backend.feedback)

    def test_supervisor_can_request_context_reset_after_turn(self):
        fixture = self
        journal = runner.Journal(self.goal, self.spec)
        journal.record("initial", session_id="stuck-context")
        class Fake:
            turns = 0
            def owner(self, feedback):
                self.turns += 1
                if self.turns == 1:
                    raise ValueError("Repeated invalid structured response")
                fixture.assertIsNone(journal.state["session_id"])
                (fixture.goal / "cancel.request").touch()
                return {"status": "continue"}
            def supervisor(self, facts):
                return {"classification": "recoverable", "advice": "Reset ended owner context", "evidence": [], "recovery_action": "reset_session"}
        runner.run_goal(self.spec, journal, Fake(), lambda _: None)
        self.assertEqual(journal.state["previous_session_ids"], ["stuck-context"])
        self.assertEqual(journal.state["status"], "CANCELED")

    def test_typed_context_overflow_is_safe_and_intermediate_retry_preserves_session(self):
        self.assertEqual(runner.native_diagnostic({"error": {"code": "context_length_exceeded"}}), {"error_category": "context_limit"})
        self.assertEqual(runner.native_diagnostic({"type": "result", "is_error": True, "result": "Prompt is too long"}), {"error_category": "context_limit"})
        journal = runner.Journal(self.goal, self.spec)
        journal.record("initial", session_id="healthy-native-context")
        backend = runner.NativeBackend(self.spec, journal)
        events = [{"type": "system", "subtype": "api_retry", "error": {"code": "context_length_exceeded"}},
                  {"type": "result", "structured_output": {"status": "continue"}}]
        script = "import sys,json; sys.stdin.read(); [print(json.dumps(e)) for e in " + repr(events) + "]"
        backend.process([sys.executable, "-c", script], "fixture", "owner")
        self.assertEqual(journal.state["session_id"], "healthy-native-context")
        self.assertNotIn("previous_session_ids", journal.state)

    @unittest.skipUnless(os.name == "nt", "Windows Job Object fixture")
    def test_cancel_closes_local_grandchild_tree(self):
        journal = runner.Journal(self.goal, self.spec)
        backend = runner.NativeBackend(self.spec, journal)
        marker = self.root / "grandchild.pid"
        script = ("import subprocess,sys,time,pathlib; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                  "pathlib.Path(" + repr(str(marker)) + ").write_text(str(p.pid)); time.sleep(60)")
        def cancel_after_spawn():
            for _ in range(500):
                if marker.exists():
                    (self.goal / "cancel.request").touch()
                    return
                time.sleep(.02)
        thread = threading.Thread(target=cancel_after_spawn, daemon=True)
        thread.start()
        with self.assertRaises(runner.Canceled):
            backend.process([sys.executable, "-c", script], "fixture")
        thread.join(1)
        pid = int(marker.read_text())
        for _ in range(50):
            if runner.runtime.process_token(pid) is None:
                break
            time.sleep(.02)
        self.assertIsNone(runner.runtime.process_token(pid), "Grandchild survived closed per-process Job")

    def test_real_local_check_and_native_stream_metadata(self):
        journal = runner.Journal(self.goal, self.spec)
        backend = runner.NativeBackend(self.spec, journal)
        result = backend.check(self.spec["checks"][0])
        self.assertEqual(result, {"exit_code": 0, "output": "ok\n"})
        events = [{"type": "system", "subtype": "init", "session_id": "fixture-native-session",
                   "tools": list(runner.MCP_TOOLS), "mcp_servers": [{"name": "northstar_a2a", "status": "connected"}]},
            {"type": "system", "subtype": "api_retry", "attempt": 1, "error_status": 429},
            {"type": "result", "result": "secret arbitrary payload", "structured_output": {"status": "continue"}}]
        script = "import sys,json; sys.stdin.read(); events=" + repr(events) + "; [print(json.dumps(e)) for e in events]"
        self.assertEqual(backend.process([sys.executable, "-c", script], "fixture prompt"), {"status": "continue"})
        self.assertEqual(journal.state["session_id"], "fixture-native-session")
        log = (self.goal / "owner.jsonl").read_text()
        self.assertIn("api_retry", log)
        self.assertNotIn("secret arbitrary payload", log)
        self.assertNotIn("CLAUDE_CODE_RETRY_WATCHDOG", os.environ)

    def test_mcp_preflight_unavailable_then_ready_preserves_session(self):
        journal = runner.Journal(self.goal, self.spec)
        journal.record("initial", session_id="original-session")
        names = {name.removeprefix("mcp__northstar_a2a__") for name in runner.MCP_TOOLS}
        attempts = []
        async def probe():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise ConnectionError("Bearer secret-payload must not persist")
            if len(attempts) == 2:
                return {"list_stacks"}
            return names
        backend = runner.NativeBackend(self.spec, journal, mcp_probe=probe)
        receipt = backend.wait_for_mcp()
        self.assertEqual(receipt["attempts"], 3)
        self.assertEqual(journal.state["status"], "RUNNING")
        self.assertIsNone(journal.state["infrastructure_wait"])
        self.assertEqual(journal.state["session_id"], "original-session")
        self.assertEqual(journal.state["id"], "goal")
        events = (self.goal / "events.jsonl").read_text()
        self.assertIn("infrastructure_wait", events)
        self.assertIn("infrastructure_ready", events)
        self.assertNotIn("secret-payload", events)
        self.assertNotIn("owner_pid", journal.state)

    def test_mcp_preflight_cancel_interrupts_pending_sdk_probe(self):
        journal = runner.Journal(self.goal, self.spec)
        canceled = []
        async def probe():
            (self.goal / "cancel.request").touch()
            try:
                await asyncio.Future()
            finally:
                canceled.append(True)
        backend = runner.NativeBackend(self.spec, journal, mcp_probe=probe)
        with self.assertRaises(runner.Canceled):
            backend.wait_for_mcp()
        self.assertEqual(canceled, [True])
        self.assertNotIn("owner_pid", journal.state)

    def test_native_init_missing_tools_reconnects_same_session_without_supervisor(self):
        fixture = self
        journal = runner.Journal(self.goal, self.spec)
        async def ready():
            return {name.removeprefix("mcp__northstar_a2a__") for name in runner.MCP_TOOLS}
        native = runner.NativeBackend(self.spec, journal, mcp_probe=ready)
        event = {"type": "system", "subtype": "init", "session_id": "same-native-session",
                 "tools": ["Read", "Glob"], "mcp_servers": [{"name": "northstar_a2a", "status": "failed"}]}
        script = "import sys,json; sys.stdin.read(); print(json.dumps(" + repr(event) + "), flush=True); import time; time.sleep(60)"
        class Fake:
            turns = 0
            def owner(self, feedback):
                native.wait_for_mcp()
                self.turns += 1
                if self.turns == 1:
                    return native.process([sys.executable, "-c", script], "fixture", "owner")
                fixture.assertEqual(journal.state["session_id"], "same-native-session")
                fixture.assertIn("infrastructure_recovery", feedback)
                return fixture.proposal()
            def supervisor(self, facts):
                fixture.fail("Canonical infrastructure recovery must not invoke a model supervisor")
            def fetch_review(self, reference): return fixture.task, fixture.stack
            def check(self, check): return {"exit_code": 0, "output": "verified"}
        backend = Fake()
        runner.run_goal(self.spec, journal, backend, lambda _: None)
        self.assertEqual(backend.turns, 2)
        self.assertEqual(journal.state["status"], "COMPLETE")
        self.assertEqual(journal.state["session_id"], "same-native-session")
        self.assertNotIn("previous_session_ids", journal.state)
        self.assertIn("infrastructure_reconnect", (self.goal / "events.jsonl").read_text())

    def test_native_capability_init_schema_and_configured_url(self):
        config = self.root / "mcp.json"
        config.write_text(json.dumps({"mcpServers": {"northstar_a2a": {"type": "http", "url": "http://127.0.0.1:19999/mcp"}}}))
        self.assertEqual(runner.configured_mcp_url(self.spec), "http://127.0.0.1:19999/mcp")
        event = {"tools": ["Read", "Glob", *runner.MCP_TOOLS], "mcp_servers": [{"name": "northstar_a2a", "status": "connected"}]}
        self.assertTrue(runner.native_capability_receipt(event)["ready"])
        event["mcp_servers"][0]["status"] = "failed"
        self.assertFalse(runner.native_capability_receipt(event)["ready"])
        event["mcp_servers"][0]["status"] = "connected"
        event["tools"].pop()
        self.assertFalse(runner.native_capability_receipt(event)["ready"])


if __name__ == "__main__":
    unittest.main()
