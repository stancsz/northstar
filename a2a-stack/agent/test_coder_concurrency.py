"""Execute actual build_app/execute AST with fake I/O and controlled jobs only."""
import argparse
import ast
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SERVICE = HERE / "service.py"
# The scratch root must be the repository's own ignored tmp tree.  The
# executor publishes its terminal receipt straight onto disk under TASKS_DIR,
# bypassing runner.atomic_json, so a TASKS_DIR inside the repository would
# leave residue in the owner's working tree and void the start/end status
# comparison that binds an independent review to a candidate tree.
ROOT = HERE.parents[1]
SCRATCH = ROOT / "tmp" / "a2a-stack" / "coder-concurrency"
# A token unique to this lane, so its receipts can be told apart from any
# other lane's by content alone.
LANE_TOKEN = "coder-fixture-" + os.urandom(4).hex()
# The git query is bounded, so a wedged git cannot hang the lane.
GIT_TIMEOUT = 30


def git_ignored_directories():
    """The directories git ignores, so the guard never misses a visible one.

    The prune set is derived from git rather than from a hand-maintained name
    list, because a name list is broader than git's own ignore rules: this
    repository ignores the repository-root tmp/ but not a nested tmp/, and it
    does not ignore node_modules at all.  Pruning a directory git does NOT
    ignore would hide a receipt that would still show up in git status.

    Git collapses an ignored directory to a single entry, so a directory is
    pruned only while everything beneath it stays invisible to git.  As soon
    as a git-visible file appears under it, git reports the specific entries
    instead of the collapsed one and the directory is scanned again.

    If git cannot be consulted the prune set is empty, which scans MORE of
    the tree and therefore cannot hide a receipt.
    """
    try:
        listing = subprocess.run(
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"],
            cwd=ROOT, capture_output=True, text=True, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return set()
    if listing.returncode != 0:
        return set()
    ignored = set()
    for entry in listing.stdout.split("\0"):
        if not entry:
            continue
        path = (ROOT / entry.rstrip("/")).resolve()
        ignored.add(path)
    return ignored


def assembly(path, scratch):
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
        def __init__(self, *args, **kwargs): pass
        def routes(self): return []
    class Updater:
        def __init__(self, *args, **kwargs): pass
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
        "TASKS_DIR": scratch / "tasks", "STATE_ROOT": scratch, "REPO_ROOT": HERE,
        "DefaultRequestHandler": Handler, "build_agent_card": card, "RPC_URL": "/fixture",
        "productive_process_matches": lambda *args: False, "create_agent_card_routes": lambda card: [], "create_jsonrpc_routes": lambda *args, **kwargs: []}
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *selected], type_ignores=[])), str(path), "exec"), namespace)
    modules = {"starlette.applications": SimpleNamespace(Starlette=App), "stacks": SimpleNamespace(StackManager=StackManager),
        "task_store": SimpleNamespace(create_task_store=lambda *args: object(), _process_matches=lambda *args: False), "autonomy.manager": SimpleNamespace(GoalManager=Goals)}
    with patch.dict("sys.modules", modules): namespace["build_app"]()
    return handlers, receipts


class FakeQueue:
    async def enqueue_event(self, value): pass


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    # The counter is shared by every test in the class, so no two publishes
    # can carry the same task id.  The executor publishes its receipt by an
    # EXCLUSIVE link, so a receipt that already exists makes the publish a
    # no-op: a repeated id would let an earlier publish mask a later one,
    # and the guard could not observe its own publish.
    serial = 0

    @classmethod
    def receipts_written_by_this_lane(cls):
        """Terminal receipts in the repository tree that this lane published.

        The receipts are identified by CONTENT, not by when they appeared: a
        receipt is this lane's when its task id carries this lane's prefix.
        A tree snapshot would instead attribute any receipt that appeared
        while the lane ran to this lane, including one an unrelated
        concurrent writer left behind.

        The walk covers the whole repository, because a regression could point
        TASKS_DIR at any part of it.  Only the directories GIT IGNORES are
        pruned: they cannot affect the working tree that binds an independent
        review.  A nested tmp/, .wrangler/ or node_modules/ is not ignored by
        git and is therefore scanned.

        The lane's own scratch root is excluded unconditionally.  It is where
        the receipts are SUPPOSED to land, and it is excluded by name rather
        than by git's opinion, so the guard still holds when git cannot be
        consulted at all.
        """
        ignored = git_ignored_directories()
        found = []
        for dirpath, dirnames, filenames in os.walk(ROOT):
            kept = []
            for name in dirnames:
                path = (Path(dirpath) / name).resolve()
                if path in ignored or name == ".git":
                    continue
                kept.append(name)
            dirnames[:] = kept
            if "terminal.json" not in filenames:
                continue
            path = Path(dirpath) / "terminal.json"
            if path.is_relative_to(SCRATCH):
                continue
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            task_id = receipt.get("task_id") if isinstance(receipt, dict) else None
            if isinstance(task_id, str) and task_id.startswith(cls.task_prefix()):
                found.append(str(path))
        return sorted(found)

    @staticmethod
    def task_prefix():
        """The task-id prefix this lane's receipts carry."""
        return LANE_TOKEN + "-"

    async def asyncSetUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.executors, self.receipts = assembly(SERVICE, Path(self.temp.name))
        self.prefix = LANE_TOKEN

    def schedule(self, executor, entered, release, attempted):
        ConcurrencyTests.serial += 1
        task_id = f"{self.prefix}-{ConcurrencyTests.serial}"
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

    async def test_terminal_receipt_is_published_inside_the_scratch_root(self):
        # The executor publishes its terminal receipt straight onto disk
        # under TASKS_DIR, bypassing runner.atomic_json, so the fixture's
        # interception cannot redirect it.  If TASKS_DIR were inside the
        # repository the lane would leave receipt files in the owner's
        # working tree, and the start/end status comparison that binds an
        # independent review to a candidate tree would then be void.
        root = self.executors[0]
        await self.pair(root, root, concurrent=False)
        strays = self.receipts_written_by_this_lane()
        self.assertEqual(strays, [],
                         f"the lane wrote receipts into the repository tree: {strays}")
        scratch = Path(self.temp.name).resolve()
        published = sorted(scratch.rglob("terminal.json"))
        self.assertTrue(published, "the executor published no terminal receipt")
        for receipt in published:
            self.assertTrue(receipt.resolve().is_relative_to(scratch), receipt)
        self.assertEqual(self.receipts, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", type=Path, default=SERVICE)
    args = parser.parse_args()
    SERVICE = args.service
    unittest.main(argv=["test_coder_concurrency"], verbosity=2)
