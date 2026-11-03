"""Formal Goal review results are validated before a review task completes.

The real A2A request handler, task store and task updater run over an owned
synthetic native process.  No model, network, live port or production state
is used: every fixture lives in this folder's scratch area.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import (Message, Part, Role, SendMessageConfiguration,
                       SendMessageRequest, TaskState)

AGENT = Path(__file__).resolve().parent


def _stack_root() -> Path:
    """Locate the real a2a-stack root that owns the autonomy package."""
    for parent in (AGENT, *AGENT.parents):
        if (parent / "autonomy" / "runner.py").is_file():
            return parent
        nested = parent / "a2a-stack"
        if (nested / "autonomy" / "runner.py").is_file():
            return nested
    raise RuntimeError("cannot locate the a2a-stack root that owns autonomy/runner.py")


STACK_ROOT = _stack_root()


def _prioritize(directories):
    """Force a deterministic relative import order for the given directories.

    This folder comes first so its own service.py and stacks.py win over the
    readonly originals, then the durable task store, the runtime helper and
    the autonomy package.
    """
    wanted = [str(Path(d).resolve()) for d in directories]
    rest = [entry for entry in sys.path
            if entry and Path(entry).resolve() not in {Path(w) for w in wanted}]
    sys.path[:] = wanted + rest


_prioritize((AGENT, STACK_ROOT / "agent", STACK_ROOT / "runtime", STACK_ROOT))

import service  # noqa: E402 - the real host service module
import stacks  # noqa: E402 - the real trusted assignment registry
import task_store  # noqa: E402 - the real durable task store
from autonomy import manager as manager_module  # noqa: E402
from autonomy import runner as goal_runner  # noqa: E402

# The private driver injects SCRATCH/ROOT for the candidate folder; a direct
# run of this file falls back to a sibling scratch directory of its own.  The
# extended-length Windows prefix keeps the deep fixture paths below MAX_PATH.
FIXTURES = globals().get("SCRATCH") or (
    Path("\\\\?\\" + str(AGENT / "fixtures" / "formal-review-result"))
    if os.name == "nt" else AGENT / "fixtures" / "formal-review-result")

# The exact final result of the closed production incident: a successful native
# exit that carries progress prose instead of a formal review.
PROSE_ONLY_RESULT = ("Let me look for an archived copy of the baseline cart "
                     "test file to byte-compare original assertions.")


class FormalReviewResultTests(unittest.IsolatedAsyncioTestCase):
    """A Goal-bound candidate reviewer must return a typed formal review."""

    async def asyncSetUp(self):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=FIXTURES)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "w"
        self.state = self.root / "h"
        self.workspace.mkdir()
        self.workspace.joinpath("source.py").write_text("value=1\n", encoding="utf-8")
        for attribute, value in (("REPO_ROOT", self.workspace),
                                  ("STATE_ROOT", self.state),
                                  ("JOBS_DIR", self.state / "jobs"),
                                  ("TASKS_DIR", self.state / "tasks")):
            patcher = mock.patch.object(service, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.goal = "g-" + "d" * 32
        self.goal_dir = self.state / "autonomy" / "goals" / self.goal
        self.goal_dir.mkdir(parents=True)
        (self.goal_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        self.spec = {"id": self.goal, "workspace": str(self.workspace),
                     "goal": "Formal review fixture",
                     "acceptance": ["Fixture proof"], "write_paths": ["source.py"],
                     "baseline": {"source.py": None}, "checks": [],
                     "state_root": str(self.state), "goal_state_dir": str(self.goal_dir)}
        self.goal_dir.joinpath("spec.json").write_text(json.dumps(self.spec), encoding="utf-8")
        self.goal_state = self.goal_dir / "state.json"
        self.goal_state.write_text(json.dumps(
            {"id": self.goal, "status": "RUNNING", "session_id": None,
             "recovery_count": 0}), encoding="utf-8")
        self.goal_state_before = self.goal_state.read_bytes()

        self.handlers = {}

        def handler(**kwargs):
            actual = DefaultRequestHandler(**kwargs)
            self.handlers[kwargs["agent_card"].name] = actual
            return actual

        with mock.patch.dict(sys.modules, {"stacks": stacks, "task_store": task_store,
                                           "autonomy.manager": manager_module}), \
             mock.patch.object(service, "DefaultRequestHandler", side_effect=handler):
            self.app, _card = service.build_app()
            self.registry = self.app.state.stack_manager
            self.manager = self.app.state.goal_manager
            self.stack = self.registry.create_stack(
                {"workspace": str(self.workspace), "goal": "Fixture", "goal_id": self.goal,
                 "roles": [{"id": "coder", "profile": "coder"},
                           {"id": "review", "profile": "reviewer"}]})
            detailed = self.registry._detail(self.registry.get_stack(self.stack["stack_id"]))
            for role in detailed["roles"]:
                self.registry.role_app_factory(
                    detailed, role,
                    self.registry.loader_for(self.stack["stack_id"], role["id"]))
        self.review_handler = next(h for name, h in self.handlers.items() if "/review/reviewer" in name)
        self.coder_handler = next(h for name, h in self.handlers.items() if "/coder/coder" in name)
        self.root_handler = self.handlers["northstar-claude-code"]

        goal_runner.review_helpers.ROOT = self.workspace
        manifest = goal_runner.review_helpers.candidate(["source.py"])
        self.candidate = manifest["candidate"]
        self.registry.stamp_candidate(self.goal, self.candidate)

    async def asyncTearDown(self):
        for handler in self.handlers.values():
            await handler.task_store.close()

    # -- fixtures ---------------------------------------------------------- #
    def assignment(self, role, **kwargs):
        payload = {"role_id": role, "task": "Controlled formal review fixture",
                   "write_paths": ["source.py"] if role == "coder" else [],
                   "acceptance": list(self.spec["acceptance"])}
        payload.update(kwargs)
        return self.registry.create_assignment(self.stack["stack_id"], payload)

    def review(self, **overrides):
        value = {"candidate": self.candidate, "verdict": "READY",
                 "evidence": ["controlled fixture evidence"]}
        value.update(overrides)
        return json.dumps(value)

    def native_argv(self, result_text):
        payload = self.root / "native-result.json"
        payload.write_text(json.dumps({"type": "result", "subtype": "success",
                                       "is_error": False, "result": result_text}),
                           encoding="utf-8")
        source = "import sys;sys.stdout.write(open(%r,encoding='utf-8').read())" % str(payload)
        return [sys.executable, "-u", "-c", source]

    async def submit(self, handler, job_name, result_text):
        request = SendMessageRequest(
            message=Message(message_id=uuid.uuid4().hex, role=Role.ROLE_USER,
                            parts=[Part(text=json.dumps({"job": job_name}))]),
            configuration=SendMessageConfiguration(return_immediately=False))
        with mock.patch.object(service, "_build_claude_argv", return_value=self.native_argv(result_text)):
            return await handler.on_message_send(request, ServerCallContext())

    def terminal_receipt(self, task_id):
        return json.loads((self.state / "tasks" / task_id / "terminal.json").read_text(encoding="utf-8"))

    def assert_goal_untouched(self):
        self.assertEqual(self.goal_state.read_bytes(), self.goal_state_before)
        self.assertEqual(json.loads(self.goal_state.read_text(encoding="utf-8"))["status"], "RUNNING")

    # -- the incident: prose is not a formal review ------------------------ #
    async def test_progress_prose_is_not_published_as_a_completed_review(self):
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        self.assertEqual(len(response.artifacts), 0, "an invalid review artifact was published")
        self.assertEqual(self.terminal_receipt(response.id)["state"], "TASK_STATE_FAILED")
        self.assert_goal_untouched()

    async def test_failure_message_never_echoes_the_invalid_result(self):
        secret = "sk-ant-api03-fixture-credential-value"
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"],
                                     f"{PROSE_ONLY_RESULT} {secret}")
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        message = response.status.message.parts[0].text
        self.assertNotIn(secret, message)
        self.assertNotIn(PROSE_ONLY_RESULT, message)
        self.assertIn("NEW review Task", message)
        self.assertIn("SAME running Goal", message)
        self.assertIn(self.goal, message)

    # -- valid formal reviews stay completed -------------------------------- #
    async def test_ready_review_completes_and_publishes_the_review(self):
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], self.review())
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(len(response.artifacts), 1)
        published = response.artifacts[0].parts[0].text
        self.assertEqual(goal_runner.parse_object(published)["verdict"], "READY")
        self.assertEqual(self.terminal_receipt(response.id)["state"], "TASK_STATE_COMPLETED")

    async def test_negative_and_unverified_verdicts_are_completed_reviews(self):
        for verdict in ("NOT READY", "NOT_READY", "UNVERIFIED"):
            with self.subTest(verdict=verdict):
                assignment = self.assignment("review", candidate=self.candidate)
                response = await self.submit(self.review_handler, assignment["job_name"],
                                             self.review(verdict=verdict))
                self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
                published = response.artifacts[0].parts[0].text
                self.assertEqual(goal_runner.parse_object(published)["verdict"], verdict)
                self.assertEqual(self.terminal_receipt(response.id)["state"], "TASK_STATE_COMPLETED")

    async def test_fenced_review_inside_prose_completes(self):
        payload = self.review()
        text = ("I reviewed the frozen candidate.\n\n```json\n" + payload + "\n```\n\n"
                "That is my complete review.")
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], text)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        published = response.artifacts[0].parts[0].text
        self.assertEqual(goal_runner.parse_object(published)["candidate"], self.candidate)

    # -- invalid formal reviews fail the current task ----------------------- #
    async def test_wrong_candidate_review_fails(self):
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"],
                                     self.review(candidate="0" * 64))
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        self.assertEqual(len(response.artifacts), 0)
        self.assertEqual(self.terminal_receipt(response.id)["state"], "TASK_STATE_FAILED")
        self.assert_goal_untouched()

    async def test_missing_verdict_review_fails(self):
        payload = json.dumps({"candidate": self.candidate, "evidence": ["no verdict"]})
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], payload)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        self.assertEqual(len(response.artifacts), 0)

    async def test_missing_or_blank_evidence_review_fails(self):
        for evidence in ([], ["   "], "not-a-list", None):
            with self.subTest(evidence=evidence):
                assignment = self.assignment("review", candidate=self.candidate)
                response = await self.submit(self.review_handler, assignment["job_name"],
                                             self.review(evidence=evidence))
                self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
                self.assertEqual(len(response.artifacts), 0)

    async def test_ambiguous_review_json_fails(self):
        payload = self.review()
        ambiguous = (payload + "\n" + json.dumps({"verdict": "NOT READY"}) + "\n")
        fenced = ("```json\n" + payload + "\n```\n```json\n"
                  + json.dumps({"verdict": "NOT READY"}) + "\n```\n")
        for text in (ambiguous, fenced):
            with self.subTest(text=text[:40]):
                assignment = self.assignment("review", candidate=self.candidate)
                response = await self.submit(self.review_handler, assignment["job_name"], text)
                self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
                self.assertEqual(len(response.artifacts), 0)

    # -- the failed task cannot be the Goal's review evidence --------------- #
    async def test_failed_review_task_is_refused_by_goal_acceptance(self):
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        facts = await self.manager.task_reader(self.stack["stack_id"], "review", response.id)
        self.assertEqual(facts["status"]["state"], "TASK_STATE_FAILED")
        frozen = self.manager.freeze(self.goal, ["source.py"])
        proposal = {"status": "complete", "summary": "Fixture",
                    "candidate_manifest": frozen["manifest_path"],
                    "review": {"stack_id": self.stack["stack_id"], "role_id": "review",
                               "task_id": response.id}, "blocker": None}
        with self.assertRaisesRegex(ValueError, "Review task not completed"):
            await self.manager.completion(self.goal, {"operation": "prepare", "proposal": proposal})
        self.assert_goal_untouched()

    async def test_a_new_review_assignment_stays_admissible_after_a_failure(self):
        assignment = self.assignment("review", candidate=self.candidate)
        response = await self.submit(self.review_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)
        fresh = self.assignment("review", candidate=self.candidate)
        self.assertNotEqual(fresh["assignment_id"], assignment["assignment_id"])
        record = json.loads(self.registry._assignment_file(
            self.stack["stack_id"], fresh["assignment_id"]).read_text(encoding="utf-8"))
        self.assertEqual(record["candidate"], self.candidate)
        self.assertIsNone(record["task_id"])
        self.assert_goal_untouched()

    # -- unchanged jobs ----------------------------------------------------- #
    async def test_coder_result_stays_freeform(self):
        assignment = self.assignment("coder")
        response = await self.submit(self.coder_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(len(response.artifacts), 1)

    async def test_component_reviewer_without_candidate_stays_freeform(self):
        assignment = self.assignment("review")
        response = await self.submit(self.review_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(len(response.artifacts), 1)

    async def test_legacy_registered_job_stays_freeform(self):
        self.workspace.joinpath("prompt.txt").write_text("fixture prompt\n", encoding="utf-8")
        jobs = self.state / "jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        jobs.joinpath("legacy.json").write_text(json.dumps(
            {"mode": "claude", "cwd": ".", "prompt_file": "prompt.txt", "tools": ["Read"]}),
            encoding="utf-8")
        response = await self.submit(self.root_handler, "legacy", PROSE_ONLY_RESULT)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual(len(response.artifacts), 1)

    # -- the trusted contract itself ---------------------------------------- #
    def test_contract_is_bound_only_for_goal_candidate_reviewers(self):
        review = self.assignment("review", candidate=self.candidate)
        config = self.registry.loader_for(self.stack["stack_id"], "review")(
            review["job_name"], "contract-task")
        self.assertEqual(config["formal_review"]["candidate"], self.candidate)
        self.assertEqual(config["formal_review"]["goal_id"], self.goal)

        component = self.assignment("review")
        component_config = self.registry.loader_for(self.stack["stack_id"], "review")(
            component["job_name"], "component-task")
        self.assertNotIn("formal_review", component_config)

        coder = self.assignment("coder")
        coder_config = self.registry.loader_for(self.stack["stack_id"], "coder")(
            coder["job_name"], "coder-task")
        self.assertNotIn("formal_review", coder_config)

    async def test_real_stack_loader_delivers_the_contract_to_the_executor(self):
        """The bound job config comes from the real StackManager loader."""
        assignment = self.assignment("review", candidate=self.candidate)
        executor = self.review_handler.agent_executor
        seen = []
        original = executor._job_loader

        def loader(name, task_id):
            config = original(name, task_id)
            seen.append(config)
            return config

        executor._job_loader = loader
        try:
            response = await self.submit(self.review_handler, assignment["job_name"], PROSE_ONLY_RESULT)
        finally:
            executor._job_loader = original
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["formal_review"]["candidate"], self.candidate)
        self.assertEqual(seen[0]["formal_review"]["goal_id"], self.goal)
        self.assertEqual(response.status.state, TaskState.TASK_STATE_FAILED)


FLAG = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"


def claude_config(**overrides):
    """A minimal trusted Claude job config, as the service would load it."""
    config = {"name": "fixture", "mode": "claude", "cwd": ".", "timeout_seconds": None,
              "prompt_path": Path("prompt.txt"), "max_turns": None, "tools": ["Read"],
              "allowed_tools": ["Read"], "permission_mode": "acceptEdits"}
    config.update(overrides)
    return config


class ClaudeChildSettingsTests(unittest.TestCase):
    """The service pins the flag for Claude children only."""

    def settings_env(self, argv):
        """The env map carried by the child-only --settings argument."""
        self.assertIn("--settings", argv)
        payload = json.loads(argv[argv.index("--settings") + 1])
        self.assertEqual(payload, {"env": {FLAG: "0"}})
        return payload["env"]

    def test_claude_argv_carries_the_child_only_settings_override(self):
        with mock.patch.object(service, "resolve_claude_exe", return_value="claude.exe"):
            argv = service._build_claude_argv(claude_config())
        self.settings_env(argv)

    def test_claude_argv_preserves_every_other_field(self):
        with mock.patch.object(service, "resolve_claude_exe", return_value="claude.exe"):
            argv = service._build_claude_argv(claude_config(max_turns=3,
                                                           tools=["Read", "Glob"],
                                                           allowed_tools=["Read", "Glob"]))
        self.assertEqual(argv[0], "claude.exe")
        self.assertEqual(argv[argv.index("--max-turns") + 1], "3")
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob")
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,Glob")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")

    def test_claude_child_environment_carries_the_flag_without_mutating_the_parent(self):
        for parent_value in (None, "parent-sentinel-value"):
            with self.subTest(parent_value=parent_value):
                with mock.patch.dict(os.environ):
                    if parent_value is None:
                        os.environ.pop(FLAG, None)
                    else:
                        os.environ[FLAG] = parent_value
                    env = service._child_env(True)
                    self.assertEqual(env[FLAG], "0")
                    # The parent keeps exactly the state it had before.
                    self.assertEqual(FLAG in os.environ, parent_value is not None)
                    self.assertEqual(os.environ.get(FLAG), parent_value)

    def test_check_child_environment_is_not_forced(self):
        parent_value = os.environ.get(FLAG, "<ABSENT>")
        env = service._child_env(False)
        # A check child is never forced: it keeps exactly the inherited value.
        self.assertEqual(env.get(FLAG, "<ABSENT>"), parent_value)
        self.assertEqual(os.environ.get(FLAG, "<ABSENT>"), parent_value)

    def test_run_job_hands_the_pinned_environment_to_the_claude_child(self):
        """The real execution path builds the child environment, not a copy."""
        FIXTURES.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=FIXTURES) as scratch:
            root = Path(scratch)
            prompt = root / "prompt.txt"
            prompt.write_text("fixture prompt\n", encoding="utf-8")
            captured = {}

            def popen(argv, **kwargs):
                captured["argv"] = list(argv)
                captured["env"] = kwargs.get("env")
                raise OSError("synthetic launch stop")

            config = claude_config(cwd=str(root), prompt_path=prompt)
            updater = mock.Mock()
            updater.task_id = "bg-wait-fixture"
            with mock.patch.object(service, "TASKS_DIR", root / "tasks"), \
                 mock.patch.object(service.subprocess, "Popen", side_effect=popen):
                with self.assertRaises(OSError):
                    asyncio.run(service.RegisteredJobExecutor._run_job(
                        service.RegisteredJobExecutor.__new__(service.RegisteredJobExecutor),
                        config, service._ActiveJob(), updater))
        self.assertEqual(captured["env"][FLAG], "0")
        self.assertEqual(captured["env"]["CLAUDE_CODE_RETRY_WATCHDOG"], "1")
        self.settings_env(captured["argv"])


if __name__ == "__main__":
    unittest.main()
