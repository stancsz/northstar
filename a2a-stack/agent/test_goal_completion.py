"""Real SDK productive admission/finalization races; controlled jobs and isolated SQLite."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import uuid

from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.database_task_store import DatabaseTaskStore
from a2a.types import SendMessageRequest, SendMessageConfiguration, Message, Role, Part, Task, TaskStatus, TaskState, Artifact

AGENT = Path(__file__).resolve().parent
STACK = AGENT.parent
for directory in (AGENT, STACK):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
import service
import stacks
import task_store
from autonomy import manager as manager_module
from autonomy import runner as goal_runner
SCRATCH = STACK.parent / "tmp/a2a-stack/goal-completion-tests"


class SDKBoundaryTests(unittest.IsolatedAsyncioTestCase):
    def coverage_criteria(self):
        criteria = [f"Immutable fixture acceptance criterion {number}." for number in range(1, 9)]
        self.spec["acceptance"] = criteria
        self.directory.joinpath("spec.json").write_text(json.dumps(self.spec), encoding="utf-8")
        return criteria

    async def test_formal_review_rejects_paraphrased_or_missing_acceptance_before_writes(self):
        criteria = self.coverage_criteria()
        stack_dir = self.registry.stacks_dir / self.stack["stack_id"]
        before = {str(p.relative_to(stack_dir)): p.read_bytes() for p in stack_dir.rglob("*") if p.is_file()}
        epoch = self.registry.goal_generation(self.goal)
        for acceptance in (["Paraphrased fixture behavior is correct."], criteria[:-1]):
            with self.subTest(acceptance=acceptance):
                with self.assertRaisesRegex(ValueError, "copy.*Goal.acceptance"):
                    self.assignment("review", candidate=self.frozen["candidate"], acceptance=acceptance)
                self.assertEqual({str(p.relative_to(stack_dir)): p.read_bytes() for p in stack_dir.rglob("*") if p.is_file()}, before)
                self.assertEqual(self.registry.goal_generation(self.goal), epoch)
                self.assertEqual(json.loads((self.directory / "state.json").read_text())["status"], "RUNNING")
                self.assertEqual(self.started, 0)
        corrected = self.assignment("review", candidate=self.frozen["candidate"], acceptance=criteria)
        record = json.loads(self.registry._assignment_file(self.stack["stack_id"], corrected["assignment_id"]).read_text())
        self.assertEqual(record["acceptance"], criteria)
        self.assertEqual(self.registry.goal_generation(self.goal), epoch)

    async def test_formal_review_accepts_canonical_acceptance_superset(self):
        criteria = self.coverage_criteria()
        epoch = self.registry.goal_generation(self.goal)
        acceptance = criteria + ["Additional component-specific fixture evidence."]
        assigned = self.assignment("review", candidate=self.frozen["candidate"], acceptance=acceptance)
        record = json.loads(self.registry._assignment_file(self.stack["stack_id"], assigned["assignment_id"]).read_text())
        self.assertEqual(record["acceptance"], acceptance)
        self.assertEqual(record["candidate"], self.frozen["candidate"])
        self.assertEqual(record["freeze_id"], epoch["freeze"]["id"])
        self.assertEqual(self.registry.goal_generation(self.goal), epoch)
        self.assertEqual(json.loads((self.directory / "state.json").read_text())["status"], "RUNNING")

        # Component review without a frozen candidate and productive work retain
        # their existing scoped acceptance contracts.
        component = self.assignment("review", acceptance=["Component-only fixture evidence."])
        coder = self.assignment("coder", acceptance=["Scoped implementation fixture evidence."])
        for assignment in (component, coder):
            self.assertTrue(self.registry._assignment_file(self.stack["stack_id"], assignment["assignment_id"]).is_file())

    async def asyncSetUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace, self.state = self.root / "w", self.root / "h"
        self.workspace.mkdir()
        self.workspace.joinpath("source.py").write_text("value=1\n")
        self.stacks, self.manager_module = stacks, manager_module
        self.store_module, self.service, self.runner = task_store, service, goal_runner
        for attribute, value in (("REPO_ROOT", self.workspace), ("STATE_ROOT", self.state), ("TASKS_DIR", self.state / "tasks")):
            patcher = mock.patch.object(self.service, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.handlers = {}
        def handler(**kwargs):
            actual = DefaultRequestHandler(**kwargs)
            self.handlers[kwargs["agent_card"].name] = actual
            return actual
        with mock.patch.dict(sys.modules, {"stacks": self.stacks, "task_store": self.store_module,
                                          "autonomy.manager": self.manager_module}), \
             mock.patch.object(self.service, "DefaultRequestHandler", side_effect=handler):
            self.app, _ = self.service.build_app()
            self.registry = self.app.state.stack_manager
            self.manager = self.app.state.goal_manager
            self.goal = "g-" + "d" * 32
            self.directory = self.state / "autonomy/goals" / self.goal
            self.directory.mkdir(parents=True)
            self.spec = {"id": self.goal, "workspace": str(self.workspace), "goal": "SDK fixture",
                "acceptance": ["Fixture proof"], "write_paths": ["source.py"], "baseline": {"source.py": None},
                "checks": [{"id": "fixture", "argv": [sys.executable, "-c", "print('fixture')"], "cwd": str(self.workspace)}],
                "state_root": str(self.state), "goal_state_dir": str(self.directory)}
            self.directory.joinpath("spec.json").write_text(json.dumps(self.spec))
            self.journal = self.runner.Journal(self.directory, self.spec)
            self.journal.record("fixture", session_id="same-session")
            self.stack = self.registry.create_stack({"workspace": str(self.workspace), "goal": "Fixture",
                "goal_id": self.goal, "roles": [{"id": "coder", "profile": "coder"}, {"id": "review", "profile": "reviewer"}]})
            detailed = self.registry._detail(self.registry.get_stack(self.stack["stack_id"]))
            for role in detailed["roles"]:
                self.registry.role_app_factory(detailed, role, self.registry.loader_for(self.stack["stack_id"], role["id"]))
        self.coder_handler = next(h for name, h in self.handlers.items() if "/coder/coder" in name)
        self.review_handler = next(h for name, h in self.handlers.items() if "/review/reviewer" in name)
        self.executor = self.coder_handler.agent_executor
        self.started = 0
        self.finish_work = asyncio.Event()
        async def controlled_job(executor, config, entry, updater):
            self.started += 1
            await self.finish_work.wait()
            return True, "Controlled fixture artifact"
        self.executor._run_job = types.MethodType(controlled_job, self.executor)
        # Seed a completed earlier producer through the real registry/store.
        old = self.assignment("coder")
        self.registry._load_assignment(self.stack["stack_id"], "coder", old["job_name"], "old-producer")
        await self.coder_handler.task_store.save(Task(id="old-producer", context_id="old-context",
            status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED), artifacts=[Artifact(artifact_id="old", parts=[Part(text="old fixture")])]), ServerCallContext())
        if hasattr(self.manager, "freeze_quiescent"):
            self.frozen = await self.manager.freeze_quiescent(self.goal, ["source.py"])
        else:
            self.frozen = self.manager.freeze(self.goal, ["source.py"])
        review = self.assignment("review", candidate=self.frozen["candidate"])
        self.registry._load_assignment(self.stack["stack_id"], "review", review["job_name"], "ready-review")
        await self.review_handler.task_store.save(Task(id="ready-review", context_id="review-context",
            status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED), artifacts=[Artifact(artifact_id="review",
                parts=[Part(text=json.dumps({"candidate": self.frozen["candidate"], "verdict": "READY", "evidence": ["controlled source review"]}))])]), ServerCallContext())
        self.proposal = {"status": "complete", "summary": "Fixture", "candidate_manifest": self.frozen["manifest_path"],
            "review": {"stack_id": self.stack["stack_id"], "role_id": "review", "task_id": "ready-review"}, "blocker": None}
        self.pending = []

    def assignment(self, role, **kwargs):
        return self.registry.create_assignment(self.stack["stack_id"], {"role_id": role, "task": "Controlled SDK fixture",
            "write_paths": ["source.py"] if role == "coder" else [], "acceptance": self.spec["acceptance"], **kwargs})

    async def asyncTearDown(self):
        self.finish_work.set()
        for task in self.pending:
            if not task.done(): task.cancel()
        await asyncio.gather(*self.pending, return_exceptions=True)
        for handler in self.handlers.values(): await handler.task_store.close()

    async def commit(self):
        if hasattr(self.manager, "completion"):
            prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
            if prepared["status"] != "ready": return prepared
            checks = [{"id": "fixture", "exit_code": 0, "output": "controlled"}]
            self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
            return await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
                "ticket": prepared["ticket"], "checks": checks})
    async def fresh_review(self):
        self.frozen = await self.manager.freeze_quiescent(self.goal, ["source.py"])
        assignment = self.assignment("review", candidate=self.frozen["candidate"])
        tid = "review-" + uuid.uuid4().hex
        self.registry._load_assignment(self.stack["stack_id"], "review", assignment["job_name"], tid)
        await self.review_handler.task_store.save(Task(id=tid, context_id="fresh-review",
            status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED), artifacts=[Artifact(artifact_id="ready",
                parts=[Part(text=json.dumps({"candidate": self.frozen["candidate"], "verdict": "READY", "evidence": ["fresh generation review"]}))])]), ServerCallContext())
        self.proposal.update(candidate_manifest=self.frozen["manifest_path"],
            review={"stack_id": self.stack["stack_id"], "role_id": "review", "task_id": tid})

    def request(self, assignment):
        return SendMessageRequest(message=Message(message_id=uuid.uuid4().hex, role=Role.ROLE_USER,
            parts=[Part(text=json.dumps({"job": assignment["job_name"]}))]), configuration=SendMessageConfiguration(return_immediately=False))

    async def test_sdk_submitted_persisted_then_commit_wins_loader_rejects(self):
        late = self.assignment("coder")
        persisted, paused, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        real_save, real_execute = DatabaseTaskStore.save, self.executor.execute
        async def save(store, task, context):
            await real_save(store, task, context)
            if task.status.state == TaskState.TASK_STATE_SUBMITTED: persisted.set()
        async def execute(context, queue):
            class QueueProxy:
                async def enqueue_event(self, event):
                    await queue.enqueue_event(event)
                    if isinstance(event, Task) and event.status.state == TaskState.TASK_STATE_SUBMITTED:
                        await persisted.wait()
                        paused.set()
                        await release.wait()
                def __getattr__(self, name): return getattr(queue, name)
            await real_execute(context, QueueProxy())
        request = SendMessageRequest(message=Message(message_id=uuid.uuid4().hex, role=Role.ROLE_USER,
            parts=[Part(text=json.dumps({"job": late["job_name"]}))]), configuration=SendMessageConfiguration(return_immediately=False))
        with mock.patch.object(DatabaseTaskStore, "save", save), mock.patch.object(self.executor, "execute", execute):
            task = asyncio.create_task(self.coder_handler.on_message_send(request, ServerCallContext()))
            self.pending.append(task)
            waiting = asyncio.create_task(paused.wait())
            done, _ = await asyncio.wait({task, waiting}, return_when=asyncio.FIRST_COMPLETED)
            if task in done and not paused.is_set():
                waiting.cancel()
                await task
                self.fail("SDK request ended before controlled enqueue boundary")
            result = await self.commit()
            self.assertEqual(result["status"], "complete")
            release.set()
            self.finish_work.set()
            response = await task
        self.assertEqual(response.status.state, TaskState.TASK_STATE_REJECTED)
        self.assertEqual(self.started, 0)
        saved = await self.coder_handler.task_store.get(response.id, ServerCallContext())
        self.assertEqual(saved.status.state, TaskState.TASK_STATE_REJECTED)

    async def test_sdk_binding_wins_queued_task_blocks_completion(self):
        late = self.assignment("coder")
        bound = asyncio.Event()
        original_loader = self.executor._job_loader
        def loader(name, tid):
            result = original_loader(name, tid)
            bound.set()
            return result
        self.executor._job_loader = loader
        await self.executor._semaphore.acquire()
        request = SendMessageRequest(message=Message(message_id=uuid.uuid4().hex, role=Role.ROLE_USER,
            parts=[Part(text=json.dumps({"job": late["job_name"]}))]), configuration=SendMessageConfiguration(return_immediately=False))
        task = asyncio.create_task(self.coder_handler.on_message_send(request, ServerCallContext()))
        self.pending.append(task)
        try:
            await bound.wait()
            result = await self.commit()
            self.assertNotEqual(result["status"], "complete")
            self.assertEqual(self.started, 0)
        finally:
            self.executor._semaphore.release()
            self.finish_work.set()
            await task

    async def test_normal_completion_and_idempotent_commit(self):
        prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        checks = [{"id": "fixture", "exit_code": 0, "output": "controlled"}]
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        payload = {"operation": "commit", "proposal": self.proposal, "ticket": prepared["ticket"], "checks": checks}
        accepted = await self.manager.completion(self.goal, payload)
        repeated = await self.manager.completion(self.goal, payload)
        self.assertEqual(accepted, repeated)
        self.assertEqual(accepted["status"], "complete")
        with self.assertRaises(ValueError): self.assignment("coder")

    async def test_finished_new_producer_invalidates_old_review_even_without_edits(self):
        late = self.assignment("coder")
        task = asyncio.create_task(self.coder_handler.on_message_send(self.request(late), ServerCallContext()))
        self.pending.append(task)
        # Wait only on the fixture's real executor entry, not an elapsed clock.
        while not self.started: await asyncio.sleep(0)
        self.assertEqual((await self.commit())["status"], "wait")
        with self.assertRaises(ValueError): self.assignment("review", candidate=self.frozen["candidate"])
        self.finish_work.set()
        response = await task
        self.assertEqual(response.status.state, TaskState.TASK_STATE_COMPLETED)
        self.assertEqual((await self.commit())["status"], "refresh")
        await self.fresh_review()
        self.assertEqual((await self.commit())["status"], "complete")

    async def test_generation_change_after_prepare_invalidates_check_ticket(self):
        prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        late = self.assignment("coder")
        self.registry._load_assignment(self.stack["stack_id"], "coder", late["job_name"], "failed-attempt")
        await self.coder_handler.task_store.save(Task(id="failed-attempt", context_id="failed",
            status=TaskStatus(state=TaskState.TASK_STATE_FAILED)), ServerCallContext())
        checks = [{"id": "fixture", "exit_code": 0, "output": "old-generation"}]
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        rejected = await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
            "ticket": prepared["ticket"], "checks": checks})
        self.assertEqual(rejected["status"], "refresh")
        await self.fresh_review()
        # A new generation cannot use the old check ticket even after new review.
        stale = await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
            "ticket": prepared["ticket"], "checks": checks})
        self.assertEqual(stale["status"], "refresh")
        self.assertEqual((await self.commit())["status"], "complete")

    async def test_terminal_task_with_live_native_identity_still_blocks(self):
        late = self.assignment("coder")
        tid = "terminal-native"
        self.registry._load_assignment(self.stack["stack_id"], "coder", late["job_name"], tid)
        await self.coder_handler.task_store.save(Task(id=tid, context_id="terminal",
            status=TaskStatus(state=TaskState.TASK_STATE_CANCELED)), ServerCallContext())
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            self.manager_module.runtime.atomic_json(self.state / "tasks" / tid / "process.json", {
                "pid": child.pid, "process_token": self.service.runner.process_token(child.pid)})
            result = await self.commit()
            self.assertEqual(result["status"], "wait")
            self.assertIn("native identity", result["reason"])
        finally:
            child.kill()
            child.wait()
        await self.fresh_review()
        self.assertEqual((await self.commit())["status"], "complete")
        original = await self.coder_handler.task_store.get(tid, ServerCallContext())
        self.assertEqual(original.status.state, TaskState.TASK_STATE_CANCELED)

    async def test_failed_epoch_publish_cannot_grant_write_capability(self):
        late = self.assignment("coder")
        original = self.stacks._atomic_json
        def fail_epoch(path, value):
            if path.name == "producer-generation.json": raise PermissionError("synthetic epoch write failure")
            original(path, value)
        with mock.patch.object(self.stacks, "_atomic_json", side_effect=fail_epoch):
            response = await self.coder_handler.on_message_send(self.request(late), ServerCallContext())
        self.assertEqual(response.status.state, TaskState.TASK_STATE_REJECTED)
        self.assertEqual(self.started, 0)
        self.assertEqual(self.registry.goal_generation(self.goal)["generation"], 1)
        self.assertEqual((await self.commit())["status"], "complete")

    async def test_epoch_advance_then_binding_failure_requires_fresh_evidence_not_reservation(self):
        late = self.assignment("coder")
        original = self.stacks._atomic_json
        def fail_binding(path, value):
            if path.name == late["job_name"] + ".json" and value.get("task_id"):
                raise PermissionError("synthetic binding publish failure")
            original(path, value)
        with mock.patch.object(self.stacks, "_atomic_json", side_effect=fail_binding):
            response = await self.coder_handler.on_message_send(self.request(late), ServerCallContext())
        self.assertEqual(response.status.state, TaskState.TASK_STATE_REJECTED)
        self.assertEqual(self.started, 0)
        self.assertEqual(self.registry.goal_generation(self.goal)["generation"], 2)
        self.assertEqual((await self.commit())["status"], "refresh")
        await self.fresh_review()
        self.assertEqual((await self.commit())["status"], "complete")
        saved = await self.coder_handler.task_store.get(response.id, ServerCallContext())
        self.assertEqual(saved.status.state, TaskState.TASK_STATE_REJECTED)

    async def test_cancel_marker_refuses_commit_and_new_write(self):
        (self.directory / "cancel.request").touch()
        with self.assertRaises(ValueError): await self.commit()
        with self.assertRaises(ValueError): self.assignment("coder")
        self.assertNotEqual(json.loads((self.directory / "state.json").read_text())["status"], "COMPLETE")

    async def test_actual_native_harness_checks_then_host_commits_no_direct_complete(self):
        loop = asyncio.get_running_loop()
        owner = self
        from google.protobuf.json_format import MessageToDict
        async def review_facts():
            generation, records, facts = await owner.manager._producer_facts(owner.goal, owner.proposal["review"])
            stack = owner.registry.get_stack(owner.stack["stack_id"])
            stack["all_goal_producers"] = [{"stack_id": r["stack"]["stack_id"], "goal_id": owner.goal,
                "profile": "coder", "role_id": r["assignment"]["role_id"], "task_id": r["assignment"]["task_id"],
                "task": facts[(r["stack"]["stack_id"], r["assignment"]["role_id"], r["assignment"]["task_id"])]}
                for r in records if r["profile"] == "coder" and r["assignment"].get("task_id")]
            ref = owner.proposal["review"]
            return facts[(ref["stack_id"], ref["role_id"], ref["task_id"])], stack
        class Backend(self.runner.NativeBackend):
            def owner(self, feedback): return owner.proposal
            def _host_completion(self, payload):
                return asyncio.run_coroutine_threadsafe(owner.manager.completion(owner.goal, payload), loop).result()
            def fetch_review(self, reference):
                return asyncio.run_coroutine_threadsafe(review_facts(), loop).result()
        backend = Backend(self.spec, self.journal)
        with mock.patch.object(self.journal, "record", wraps=self.journal.record) as record:
            result = await asyncio.to_thread(self.runner.run_goal, self.spec, self.journal, backend)
        self.assertEqual(result, 0)
        self.assertEqual(self.journal.state["status"], "COMPLETE")
        self.assertEqual(self.journal.state["session_id"], "same-session")
        self.assertTrue(self.journal.state["accepted_receipt"]["accepted"])
        self.assertFalse(any(call.kwargs.get("status") == "COMPLETE" for call in record.call_args_list))

    async def test_admission_during_async_status_reads_is_rechecked_before_commit(self):
        original = self.manager.task_reader
        admitted = []
        async def reader(sid, rid, tid):
            value = await original(sid, rid, tid)
            if rid == "review" and not admitted:
                late = self.assignment("coder")
                self.registry._load_assignment(self.stack["stack_id"], "coder", late["job_name"], "late-status-read")
                admitted.append(True)
                await self.coder_handler.task_store.save(Task(id="late-status-read", context_id="failed",
                    status=TaskStatus(state=TaskState.TASK_STATE_FAILED)), ServerCallContext())
            return value
        self.manager.task_reader = reader
        result = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        self.assertEqual(result["status"], "wait")
        self.assertIn("admission changed", result["reason"])
        self.manager.task_reader = original
        await self.fresh_review()
        self.assertEqual((await self.commit())["status"], "complete")

    async def test_late_check_failure_and_changed_files_cannot_commit(self):
        prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        checks = [{"id": "fixture", "exit_code": 1, "output": "failing"}]
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        with self.assertRaises(ValueError):
            await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
                "ticket": prepared["ticket"], "checks": checks})
        (self.workspace / "source.py").write_text("value=2\n")
        checks[0]["exit_code"] = 0
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        with self.assertRaises(ValueError):
            await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
                "ticket": prepared["ticket"], "checks": checks})

    async def test_native_identity_access_error_is_not_false_absence(self):
        kernel = types.SimpleNamespace(OpenProcess=mock.Mock(return_value=0), WaitForSingleObject=mock.Mock(),
            GetProcessTimes=mock.Mock(), CloseHandle=mock.Mock())
        with mock.patch.object(self.service.ctypes, "WinDLL", return_value=kernel), \
             mock.patch.object(self.service.ctypes, "get_last_error", return_value=5):
            with self.assertRaises(PermissionError): self.service.productive_process_matches(12345, "0000000000000001")
        with mock.patch.object(self.service.ctypes, "WinDLL", return_value=kernel), \
             mock.patch.object(self.service.ctypes, "get_last_error", return_value=87):
            self.assertFalse(self.service.productive_process_matches(12345, "0000000000000001"))

    async def test_host_restart_invalidates_ticket_without_resetting_goal_session(self):
        prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        self.manager.completion_tickets.clear()
        checks = [{"id": "fixture", "exit_code": 0, "output": "controlled"}]
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        result = await self.manager.completion(self.goal, {"operation": "commit", "proposal": self.proposal,
            "ticket": prepared["ticket"], "checks": checks})
        self.assertEqual(result["status"], "refresh")
        self.assertEqual(json.loads((self.directory / "state.json").read_text())["session_id"], "same-session")
        self.assertEqual((await self.commit())["status"], "complete")

    async def test_ambiguous_commit_response_retries_without_overwriting_complete(self):
        prepared = await self.manager.completion(self.goal, {"operation": "prepare", "proposal": self.proposal})
        checks = [{"id": "fixture", "exit_code": 0, "output": "controlled"}]
        self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
        loop, owner, requests = asyncio.get_running_loop(), self, []
        class Backend(self.runner.NativeBackend):
            def _host_completion(self, payload):
                value = asyncio.run_coroutine_threadsafe(owner.manager.completion(owner.goal, payload), loop).result()
                requests.append(True)
                if len(requests) == 1: raise ConnectionError("synthetic lost response after durable commit")
                return value
        backend = Backend(self.spec, self.journal)
        with mock.patch.object(self.journal, "record", wraps=self.journal.record) as record:
            result = await asyncio.to_thread(backend.commit_completion, self.proposal, prepared["ticket"], checks)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(requests), 2)
        self.assertEqual(json.loads((self.directory / "state.json").read_text())["status"], "COMPLETE")
        self.assertEqual(record.call_count, 0)

    async def test_internal_control_route_commits_through_isolated_asgi(self):
        import httpx
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://unit.invalid") as client:
            response = await client.post("/control/goals/" + self.goal + "/complete",
                json={"operation": "prepare", "proposal": self.proposal})
            self.assertEqual(response.status_code, 200)
            prepared = response.json()
            self.assertEqual(prepared["status"], "ready")
            checks = [{"id": "fixture", "exit_code": 0, "output": "controlled"}]
            self.manager_module.runtime.atomic_json(self.directory / "checks.json", checks)
            response = await client.post("/control/goals/" + self.goal + "/complete",
                json={"operation": "commit", "proposal": self.proposal, "ticket": prepared["ticket"], "checks": checks})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "complete")

if __name__ == "__main__": unittest.main()
