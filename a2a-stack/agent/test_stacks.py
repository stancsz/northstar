"""Dynamic stack and assignment routing tests; no A2A server or worker is launched."""
from __future__ import annotations

import json
import threading
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from stacks import BASE_URL, StackManager

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "tmp" / "a2a-stack" / "dynamic-build"


def role_factory(calls):
    def factory(stack, role, loader):
        calls.append((stack["stack_id"], role["id"]))

        async def card(_request: Request):
            return JSONResponse({"name": role["agent_name"],
                                 "stack_id": stack["stack_id"], "role_id": role["id"]})

        async def rpc(request: Request):
            payload = await request.json()
            try:
                config = loader(payload["job_name"], payload["task_id"])
                response = {"mode": config["mode"], "cwd": str(config["cwd"]),
                            "prompt_path": str(config["prompt_path"]), "tools": config["tools"],
                            "allowed_tools": config["allowed_tools"],
                            "permission_mode": config["permission_mode"],
                            "max_turns": config["max_turns"], "timeout_seconds": config["timeout_seconds"]}
                return JSONResponse(response)
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=409)

        return Starlette(routes=[
            Route("/.well-known/agent-card.json", card, methods=["GET"]),
            Route("/a2a/jsonrpc", rpc, methods=["POST"]),
        ])
    return factory


class DynamicStackTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.state = self.root / "state"
        self.factory_calls = []
        self.manager = StackManager(self.state, self.workspace, role_factory(self.factory_calls))
        self.client = TestClient(Starlette(routes=self.manager.routes()))

    def tearDown(self):
        self.temp.cleanup()

    def post_stack(self, body):
        return self.client.post("/control/stacks", json={"workspace": str(self.workspace), **body})

    def test_templates_custom_roster_unique_instances_and_cards(self):
        templates = self.client.get("/control/templates").json()
        self.assertEqual({item["name"] for item in templates["templates"]}, {"code-review", "research-brief"})
        self.assertEqual(templates["profiles"]["coder"]["tools"], ["Read", "Glob", "Edit", "Write", "Bash"])
        self.assertEqual(templates["profiles"]["reviewer"], {"tools": ["Read", "Glob"], "permission_mode": "default"})
        created = self.post_stack({"template_name": "code-review", "goal": "Review one scoped change", "name": "Review run"})
        self.assertEqual(created.status_code, 201, created.text)
        stack = created.json()
        self.assertTrue(stack["stack_id"].startswith("s-"))
        self.assertEqual([role["id"] for role in stack["roles"]], ["coder", "reviewer"])
        coder, reviewer = stack["roles"]
        self.assertEqual(coder["agent_url"], f"{BASE_URL}/stacks/{stack['stack_id']}/agents/coder")
        self.assertEqual(coder["card_url"], f"{BASE_URL}/stacks/{stack['stack_id']}/agents/coder/.well-known/agent-card.json")

        card1 = self.client.get(f"/stacks/{stack['stack_id']}/agents/coder/.well-known/agent-card.json").json()
        card2 = self.client.get(f"/stacks/{stack['stack_id']}/agents/reviewer/.well-known/agent-card.json").json()
        self.assertNotEqual(card1["name"], card2["name"])
        self.assertEqual(self.factory_calls, [(stack["stack_id"], "coder"), (stack["stack_id"], "reviewer")])
        self.client.get(f"/stacks/{stack['stack_id']}/agents/coder/.well-known/agent-card.json")
        self.assertEqual(len(self.factory_calls), 2, "role app must be cached per stack/role")

        same_name = self.post_stack({"template_name": "code-review", "goal": "A separate run", "name": "Review run"}).json()
        same_name_card = self.client.get(f"/stacks/{same_name['stack_id']}/agents/coder/.well-known/agent-card.json").json()
        self.assertNotEqual(card1["name"], same_name_card["name"], "stack identity must distinguish role cards")

        custom = self.post_stack({"goal": "Research this question", "roles": [{"id": "analyst", "profile": "researcher"}]})
        self.assertEqual(custom.status_code, 201, custom.text)
        self.assertNotEqual(custom.json()["stack_id"], stack["stack_id"])
        self.client.get(f"/stacks/{custom.json()['stack_id']}/agents/analyst/.well-known/agent-card.json")
        self.assertIn((custom.json()["stack_id"], "analyst"), self.factory_calls)
        self.assertEqual(len(self.client.get("/control/stacks").json()["stacks"]), 3)

    def test_assignment_scope_loader_binding_and_detail_persistence(self):
        stack = self.post_stack({"template_name": "code-review", "goal": "Review candidate"}).json()
        stack_id = stack["stack_id"]
        assignment_response = self.client.post(f"/control/stacks/{stack_id}/assignments", json={
            "role_id": "coder", "task": "Fix the parser edge case", "write_paths": ["src/parser.py"],
            "acceptance": ["Handle empty input"], "candidate": "tree-abc",
            "depends_on": [{"assignment_id": "a-upstream", "role_id": "researcher"}],
        })
        self.assertEqual(assignment_response.status_code, 201, assignment_response.text)
        assignment = assignment_response.json()
        self.assertEqual(assignment["job_name"], assignment["assignment_id"])
        app_url = f"/stacks/{stack_id}/agents/coder/a2a/jsonrpc"
        loaded = self.client.post(app_url, json={"job_name": assignment["job_name"], "task_id": "task-original"})
        self.assertEqual(loaded.status_code, 200, loaded.text)
        config = loaded.json()
        self.assertEqual(config["mode"], "claude")
        self.assertEqual(config["cwd"], str(self.workspace))
        self.assertEqual(config["tools"], ["Read", "Glob", "Edit", "Write", "Bash"])
        self.assertEqual(config["allowed_tools"], config["tools"])
        self.assertEqual(config["permission_mode"], "acceptEdits")
        self.assertIsNone(config["max_turns"])
        self.assertIsNone(config["timeout_seconds"])
        prompt = Path(config["prompt_path"]).read_text(encoding="utf-8")
        for expected in ("Fix the parser edge case", "src/parser.py", "Handle empty input", "tree-abc", str(self.workspace)):
            self.assertIn(expected, prompt)
        self.assertIn("not an OS-level sandbox", prompt)

        loader = self.manager.loader_for(stack_id, "coder")
        with self.assertRaisesRegex(ValueError, "original task ID task-original"):
            loader(assignment["job_name"], "task-other")
        with self.assertRaisesRegex(ValueError, "original task ID task-original"):
            loader(assignment["job_name"], "task-original")
        detail = self.client.get(f"/control/stacks/{stack_id}").json()
        self.assertEqual(detail["roles"][0]["assignments"][0]["task_id"], "task-original")
        reloaded = StackManager(self.state, self.workspace, role_factory([]))
        persisted = TestClient(Starlette(routes=reloaded.routes())).get(f"/control/stacks/{stack_id}").json()
        self.assertEqual(persisted["roles"][0]["assignments"][0]["task_id"], "task-original")

    def test_readonly_scope_outside_workspace_and_cross_role_rejected(self):
        stack = self.post_stack({"template_name": "code-review", "goal": "Review candidate"}).json()
        stack_id = stack["stack_id"]
        reviewer = self.client.post(f"/control/stacks/{stack_id}/assignments", json={
            "role_id": "reviewer", "task": "Inspect only", "write_paths": ["src/file.py"],
        })
        self.assertEqual(reviewer.status_code, 400)
        outside = self.client.post(f"/control/stacks/{stack_id}/assignments", json={
            "role_id": "coder", "task": "Escape attempt", "write_paths": ["../../outside.txt"],
        })
        self.assertEqual(outside.status_code, 400)
        wrong_workspace = self.post_stack({"goal": "bad", "roles": [{"id": "coder", "profile": "coder"}],
                                           "workspace": str(self.root)})
        self.assertEqual(wrong_workspace.status_code, 400)
        assignment = self.client.post(f"/control/stacks/{stack_id}/assignments", json={
            "role_id": "coder", "task": "Scoped", "write_paths": ["src/file.py"],
        }).json()
        with self.assertRaisesRegex(ValueError, "cross-role"):
            self.manager.loader_for(stack_id, "reviewer")(assignment["job_name"], "task-x")

    def test_completion_contract_applies_to_every_role_profile(self):
        stack = self.post_stack({"goal": "Contract fixture", "roles": [
            {"id": "coder", "profile": "coder"},
            {"id": "reviewer", "profile": "reviewer"},
            {"id": "analyst", "profile": "researcher"},
        ]}).json()
        stack_id = stack["stack_id"]
        for index, role_id in enumerate(["coder", "reviewer", "analyst"]):
            response = self.client.post(f"/control/stacks/{stack_id}/assignments", json={
                "role_id": role_id, "task": f"Scoped task {index}",
                "write_paths": ["src/file.py"] if role_id == "coder" else [],
                "acceptance": [f"Criterion {index}"],
            })
            self.assertEqual(response.status_code, 201, response.text)
            assignment = response.json()
            loaded = self.client.post(
                f"/stacks/{stack_id}/agents/{role_id}/a2a/jsonrpc",
                json={"job_name": assignment["job_name"], "task_id": f"task-{index}"})
            self.assertEqual(loaded.status_code, 200, loaded.text)
            config = loaded.json()
            self.assertIsNone(config["max_turns"])
            self.assertIsNone(config["timeout_seconds"])
            prompt = Path(config["prompt_path"]).read_text(encoding="utf-8")
            for expected in ("Completion condition and ownership:",
                             "acceptance criteria above are satisfied",
                             "repair or retry it within this assignment",
                             "Do not turn one or two errors into a global stop",
                             "no budget, turn, or runtime ceiling",
                             "return the evidence",
                             "control back to the main agent",
                             "Do not take over the entire stack goal",
                             "self-assign unrelated work",
                             "main agent chooses the template"):
                self.assertIn(expected, prompt, f"{role_id} prompt missing: {expected}")

    def test_unknown_stack_role_and_invalid_roster(self):
        self.assertEqual(self.client.get("/control/stacks/s-missing").status_code, 404)
        self.assertEqual(self.client.get("/stacks/s-missing/agents/coder/.well-known/agent-card.json").status_code, 404)
        duplicate = self.post_stack({"goal": "bad", "roles": [
            {"id": "coder", "profile": "coder"}, {"id": "coder", "profile": "reviewer"},
        ]})
        self.assertEqual(duplicate.status_code, 400)

    def test_concurrent_assignment_create_and_task_claim_are_serialized(self):
        stack = self.post_stack({"goal": "Concurrency fixture", "roles": [{"id": "coder", "profile": "coder"}]}).json()
        stack_id = stack["stack_id"]

        def create(task):
            barrier.wait()
            try:
                return ("created", self.manager.create_assignment(stack_id, {
                    "assignment_id": "a-shared", "role_id": "coder", "task": task,
                    "write_paths": ["src/target.py"],
                }))
            except ValueError as exc:
                return ("rejected", str(exc))

        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            created = list(pool.map(create, ["winner-one", "winner-two"]))
        self.assertEqual(sum(kind == "created" for kind, _ in created), 1)
        self.assertEqual(sum(kind == "rejected" for kind, _ in created), 1)
        prompt = (self.state / "stacks" / stack_id / "prompts" / "a-shared.txt").read_text(encoding="utf-8")
        self.assertNotEqual("winner-one" in prompt, "winner-two" in prompt)

        assignment = self.manager.create_assignment(stack_id, {
            "assignment_id": "a-claim", "role_id": "coder", "task": "Claim once",
            "write_paths": ["src/target.py"],
        })
        claim_barrier = threading.Barrier(2)

        def claim(task_id):
            claim_barrier.wait()
            try:
                config = self.manager.loader_for(stack_id, "coder")(assignment["job_name"], task_id)
                return ("loaded", task_id, config)
            except ValueError as exc:
                return ("rejected", task_id, str(exc))

        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(claim, ["task-one", "task-two"]))
        self.assertEqual(sum(result[0] == "loaded" for result in claims), 1)
        rejected = next(result for result in claims if result[0] == "rejected")
        accepted = next(result for result in claims if result[0] == "loaded")
        self.assertIn(accepted[1], rejected[2])
        stored = json.loads((self.state / "stacks" / stack_id / "assignments" / "a-claim.json").read_text())
        self.assertEqual(stored["task_id"], accepted[1])


if __name__ == "__main__":
    unittest.main()
