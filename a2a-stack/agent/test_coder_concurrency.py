"""Execute actual build_app/execute AST with fake I/O and controlled jobs only."""
import argparse
import ast
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SERVICE = HERE / "service.py"


def assembly(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in ("RegisteredJobExecutor", "_ActiveJob", "build_app")]
    handlers, receipts = [], []
    class App:
        def __init__(self, **kwargs): self.state = SimpleNamespace()
    class Handler:
        def __init__(self, **kwargs): handlers.append(kwargs["agent_executor"])
    class StackManager:
        def __init__(self, state_root, workspace, factory):
            stack = {"stack_id": "fixture-team"}
            for role_id in ("coder-a", "coder-b"):
                factory(stack, {"id": role_id, "profile": "coder", "agent_url": "http://127.0.0.1/fixture"},
                        lambda name, task_id: {"name": name})
        def routes(self): return []
    class Goals:
        def __init__(self, *args): pass
        def routes(self): return []
    class Updater:
        def __init__(self, *args): pass
        async def start_work(self): pass
        async def add_artifact(self, **kwargs): pass
        async def complete(self): pass
        async def reject(self, **kwargs): pass
        async def failed(self, **kwargs): pass
        async def cancel(self): pass
        def new_agent_message(self, value): return value
    def card():
        skill = SimpleNamespace(tags=[], ClearField=lambda field: None)
        return SimpleNamespace(skills=[skill], supported_interfaces=[SimpleNamespace(url="")])
    namespace = {"asyncio": asyncio, "asynccontextmanager": asynccontextmanager, "json": json,
        "AgentExecutor": object, "TaskUpdater": Updater, "Task": lambda **kwargs: kwargs,
        "TaskStatus": lambda **kwargs: kwargs, "TaskState": SimpleNamespace(TASK_STATE_SUBMITTED="SUBMITTED"),
        "Part": lambda **kwargs: kwargs, "JobRejected": type("JobRejected", (Exception,), {}),
        "JobFailed": type("JobFailed", (Exception,), {}), "load_job": lambda name: {"name": name},
        "runner": SimpleNamespace(atomic_json=lambda path, value: receipts.append(value), now=lambda: "fixture-time"),
        "TASKS_DIR": HERE / "unused-no-write", "STATE_ROOT": HERE / "unused-no-write", "REPO_ROOT": HERE,
        "DefaultRequestHandler": Handler, "build_agent_card": card, "RPC_URL": "/fixture",
        "create_agent_card_routes": lambda card: [], "create_jsonrpc_routes": lambda *args, **kwargs: []}
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *selected], type_ignores=[])), str(path), "exec"), namespace)
    modules = {"starlette.applications": SimpleNamespace(Starlette=App), "stacks": SimpleNamespace(StackManager=StackManager),
        "task_store": SimpleNamespace(create_task_store=lambda *args: object()), "autonomy.manager": SimpleNamespace(GoalManager=Goals)}
    with patch.dict("sys.modules", modules): namespace["build_app"]()
    return handlers, receipts


class FakeQueue:
    async def enqueue_event(self, value): pass


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.executors, self.receipts = assembly(SERVICE)
        self.serial = 0

    def schedule(self, executor, entered, release, attempted):
        self.serial += 1
        task_id = "fixture-" + str(self.serial)
        context = SimpleNamespace(task_id=task_id, context_id="context-" + task_id, message=None,
            get_user_input=lambda: json.dumps({"job": task_id}))
        # One fake runner per executor handles all jobs, routing by config name.
        if not hasattr(executor, "fixture_events"):
            executor.fixture_events = {}
            async def job(owner, config, entry, updater):
                started, finish = owner.fixture_events[config["name"]]
                started.set()
                await finish.wait()
                return True, "fixture artifact"
            executor._run_job = MethodType(job, executor)
        executor.fixture_events[task_id] = (entered, release)
        async def invoke():
            attempted.set()
            await executor.execute(context, FakeQueue())
        return asyncio.create_task(invoke())

    async def pair(self, first_executor, second_executor, concurrent):
        first_entered, second_entered = asyncio.Event(), asyncio.Event()
        first_release, second_release = asyncio.Event(), asyncio.Event()
        first_attempted, second_attempted = asyncio.Event(), asyncio.Event()
        first = self.schedule(first_executor, first_entered, first_release, first_attempted)
        await first_entered.wait()
        second = self.schedule(second_executor, second_entered, second_release, second_attempted)
        try:
            await second_attempted.wait()
            # All fake awaits before the controlled job return synchronously;
            # second now either waits on the actual semaphore or its job gate.
            self.assertEqual(second_entered.is_set(), concurrent)
            if not concurrent:
                first_release.set()
                await first
                await second_entered.wait()
        finally:
            first_release.set()
            second_release.set()
            await asyncio.gather(first, second)

    async def test_distinct_coders_execute_concurrently_from_build_app(self):
        root, coder_a, coder_b = self.executors
        await self.pair(coder_a, coder_b, concurrent=True)
        self.assertIsNot(coder_a._semaphore, coder_b._semaphore)
        self.assertIsNot(root._semaphore, coder_a._semaphore)

    async def test_same_role_still_serializes(self):
        await self.pair(self.executors[1], self.executors[1], concurrent=False)

    async def test_legacy_root_still_serializes(self):
        root = self.executors[0]
        self.assertEqual(root._semaphore._value, 1)
        await self.pair(root, root, concurrent=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", type=Path, default=SERVICE)
    args = parser.parse_args()
    SERVICE = args.service
    unittest.main(argv=["test_coder_concurrency"], verbosity=2)
