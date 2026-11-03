"""Dynamic, per-stack A2A role routing and trusted assignment configuration."""
from __future__ import annotations

import json
import os
import re
import tempfile
import sys
import threading
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

BASE_URL = "http://127.0.0.1:18890"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PROFILES = {
    "coder": {"tools": ["Read", "Glob", "Edit", "Write", "Bash"], "permission_mode": "acceptEdits"},
    "reviewer": {"tools": ["Read", "Glob"], "permission_mode": "default"},
    "researcher": {"tools": ["Read", "Glob"], "permission_mode": "default"},
    "audit": {"tools": ["Read", "Glob"], "permission_mode": "default"},
    "verifier": {"tools": [], "permission_mode": "default", "backend": "trusted-checks"},
}
TEMPLATES = {
    "code-review": [{"id": "coder", "profile": "coder"}, {"id": "reviewer", "profile": "reviewer"}],
    "research-brief": [{"id": "researcher", "profile": "researcher"}, {"id": "reviewer", "profile": "reviewer"}],
}
READ_ONLY_PROFILES = {"reviewer", "researcher", "audit", "verifier"}
COMPLETION_CONTRACT = (
    "Completion condition and ownership:",
    "- This assignment is complete when the acceptance criteria above are satisfied.",
    "- On a recoverable error (failing test, lint or import error, flaky tool), diagnose and repair or retry it within this assignment's scope, then report the fix and its evidence.",
    "- Do not turn one or two errors into a global stop for the stack: keep the failure scoped to this assignment and escalate it with evidence.",
    "- There is no budget, turn, or runtime ceiling on this assignment; do not end it early because of elapsed time, remaining effort, or perceived limits.",
    "- The same no-ceiling rule applies to any child CLI or helper you launch: do not add max-turns, max-budget, runtime-deadline or retry-count limits to a nested agent. Propagate the original scope and completion condition instead.",
    "- When the acceptance criteria are satisfied, return the evidence (changed paths, verification output, remaining gaps) and control back to the main agent.",
    "- The main agent owns independent candidate review and additional role dispatch. Finish this leaf after its required self-checks pass; report concrete concerns in the handoff. Additional testing must resolve an observed defect in this assignment, and optional review must not become a new nested QA chain that delays handoff.",
    "- Do not take over the entire stack goal and do not self-assign unrelated work.",
    "- The main agent chooses the template, the role roster, and the next assignments; report status so it can decide.",
)
_REGISTRY_LOCK = threading.RLock()


def _registry_locked(method):
    @wraps(method)
    def locked(*args, **kwargs):
        with _REGISTRY_LOCK:
            return method(*args, **kwargs)
    return locked


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class StackManager:
    def __init__(self, state_root: Path, workspace: Path, role_app_factory: Callable):
        self.state_root = Path(state_root).resolve()
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError("configured workspace must be an existing directory")
        self.role_app_factory = role_app_factory
        self._apps: dict[tuple[str, str], Any] = {}
        self.stacks_dir = self.state_root / "stacks"
        self.boundary_lock = _REGISTRY_LOCK

    def _stack_dir(self, stack_id: str) -> Path:
        if not isinstance(stack_id, str) or not ID_RE.fullmatch(stack_id):
            raise ValueError("invalid stack ID")
        return self.stacks_dir / stack_id

    def _stack_file(self, stack_id: str) -> Path:
        return self._stack_dir(stack_id) / "stack.json"

    def get_stack(self, stack_id: str) -> dict:
        try:
            data = json.loads(self._stack_file(stack_id).read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError("unknown stack") from exc
        if not isinstance(data, dict) or data.get("stack_id") != stack_id:
            raise ValueError("invalid persisted stack record")
        if not isinstance(data.get("workspace"), str) or not data["workspace"]:
            raise ValueError("invalid persisted workspace")
        workspace = Path(data["workspace"]).resolve()
        if workspace != self.workspace:
            raise ValueError("persisted stack workspace differs from configured workspace")
        roles = data.get("roles")
        if not isinstance(roles, list) or not roles:
            raise ValueError("invalid persisted role roster")
        ids = set()
        for role in roles:
            if (not isinstance(role, dict) or not isinstance(role.get("id"), str)
                    or not ID_RE.fullmatch(role["id"]) or role["id"] in ids
                    or not isinstance(role.get("profile"), str) or role.get("profile") not in PROFILES):
                raise ValueError("invalid persisted role roster")
            ids.add(role["id"])
        return data

    def _detail(self, stack: dict) -> dict:
        stack_id = stack["stack_id"]
        roles = []
        for role in stack["roles"]:
            base = f"{BASE_URL}/stacks/{stack_id}/agents/{role['id']}"
            assignments = []
            directory = self._stack_dir(stack_id) / "assignments"
            if directory.exists():
                for path in sorted(directory.glob("*.json")):
                    item = json.loads(path.read_text(encoding="utf-8"))
                    if item.get("role_id") == role["id"]:
                        assignments.append({
                            "assignment_id": item["assignment_id"], "job_name": item["assignment_id"],
                            "task_id": item.get("task_id"), "phase": item.get("phase", "assigned"),
                        })
            roles.append({"id": role["id"], "profile": role["profile"],
                          "agent_name": f"northstar/{stack_id}/{role['id']}/{role['profile']}",
                          "card_url": f"{base}/.well-known/agent-card.json",
                          "agent_url": base, "assignments": assignments})
        return {**stack, "roles": roles}

    def _canonical_workspace(self, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("workspace is required")
        requested = Path(value).resolve(strict=True)
        if not requested.is_dir() or requested != self.workspace:
            raise ValueError(f"workspace must be the configured workspace: {self.workspace}")
        return str(requested)

    @staticmethod
    def _validate_roles(roles: Any) -> list[dict]:
        if not isinstance(roles, list) or not roles:
            raise ValueError("roles must be a non-empty array")
        result = []
        seen = set()
        for role in roles:
            if not isinstance(role, dict):
                raise ValueError("each role must be an object")
            role_id, profile = role.get("id"), role.get("profile")
            if not isinstance(role_id, str) or not ID_RE.fullmatch(role_id):
                raise ValueError("role id must use safe ASCII letters, digits, '_' or '-'")
            if role_id in seen:
                raise ValueError(f"duplicate role id: {role_id}")
            if not isinstance(profile, str) or profile not in PROFILES:
                raise ValueError(f"unknown role profile: {profile}")
            seen.add(role_id)
            result.append({"id": role_id, "profile": profile})
        return result

    @_registry_locked
    def create_stack(self, payload: Any) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("stack request must be an object")
        workspace = self._canonical_workspace(payload.get("workspace"))
        goal = payload.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal is required")
        template = payload.get("template_name")
        if template is not None and (not isinstance(template, str) or template not in TEMPLATES):
            raise ValueError(f"unknown template: {template}")
        roles = self._validate_roles(payload["roles"]) if "roles" in payload else (
            [dict(role) for role in TEMPLATES[template]] if template else None
        )
        if roles is None:
            raise ValueError("choose a template_name or provide an explicit roles roster")
        name = payload.get("name", template or "custom")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        stack_id = f"s-{uuid.uuid4().hex}"
        goal_id = payload.get("goal_id")
        if goal_id is not None:
            if not isinstance(goal_id, str) or not re.fullmatch(r"g-[a-f0-9]{32}", goal_id):
                raise ValueError("invalid autonomous goal ID")
            if not (self.state_root / "autonomy" / "goals" / goal_id / "spec.json").is_file():
                raise ValueError("unknown autonomous goal")
        stack = {"stack_id": stack_id, "name": name.strip(), "template_name": template,
                 "workspace": workspace, "goal": goal.strip(), "roles": roles,
                 "created_at": self._now(), "goal_id": goal_id}
        _atomic_json(self._stack_file(stack_id), stack)
        return self._detail(stack)

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def list_stacks(self) -> list[dict]:
        if not self.stacks_dir.exists():
            return []
        return [self._detail(self.get_stack(path.parent.name))
                for path in sorted(self.stacks_dir.glob("*/stack.json"))]

    def _assignment_file(self, stack_id: str, assignment_id: str) -> Path:
        if not isinstance(assignment_id, str) or not ID_RE.fullmatch(assignment_id):
            raise ValueError("invalid assignment ID")
        return self._stack_dir(stack_id) / "assignments" / f"{assignment_id}.json"

    def goal_active(self, goal_id):
        directory = self.state_root / "autonomy" / "goals" / goal_id
        state = json.loads((directory / "state.json").read_text(encoding="utf-8"))
        if (directory / "cancel.request").exists() or state.get("status") not in ("RUNNING", "RECOVERING"):
            raise ValueError("Goal is not active; productive assignment was not admitted")

    def goal_generation(self, goal_id):
        path = self.state_root / "autonomy" / "goals" / goal_id / "producer-generation.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"generation": 0}

    def advance_generation(self, goal_id):
        # Called under registry lock, BEFORE binding can grant write tools.
        value = {"generation": self.goal_generation(goal_id)["generation"] + 1}
        _atomic_json(self.state_root / "autonomy" / "goals" / goal_id / "producer-generation.json", value)
        return value["generation"]

    def stamp_candidate(self, goal_id, candidate):
        value = self.goal_generation(goal_id)
        value["freeze"] = {"id": uuid.uuid4().hex, "candidate": candidate,
                           "generation": value["generation"]}
        _atomic_json(self.state_root / "autonomy" / "goals" / goal_id / "producer-generation.json", value)
        return value["freeze"]

    def current_review(self, goal_id, candidate, freeze_id=None):
        epoch = self.goal_generation(goal_id)
        stamp = epoch.get("freeze", {})
        if (stamp.get("candidate") != candidate or stamp.get("generation") != epoch["generation"]
                or (freeze_id is not None and freeze_id != stamp.get("id"))):
            raise ValueError("Candidate generation is stale; wait for productive work, freeze current files, then assign fresh review")
        return stamp

    def goal_assignments(self, goal_id):
        records = []
        for path in sorted(self.stacks_dir.glob("*/stack.json")):
            stack = self.get_stack(path.parent.name)
            if stack.get("goal_id") != goal_id:
                continue
            roles = {role["id"]: role["profile"] for role in stack["roles"]}
            for assignment_path in sorted((path.parent / "assignments").glob("*.json")):
                value = json.loads(assignment_path.read_text(encoding="utf-8"))
                records.append({"stack": stack, "profile": roles[value["role_id"]],
                                "path": assignment_path, "assignment": value})
        return records

    def retire_drafts(self, goal_id):
        # Retirement never changes a protocol Task: only unbound intent is
        # discharged. A submission paused before binding will reject later.
        for record in self.goal_assignments(goal_id):
            assignment = record["assignment"]
            if record["profile"] == "coder" and assignment.get("task_id") is None:
                assignment.update(phase="retired", retired_reason="goal_completed_before_productive_binding")
                _atomic_json(record["path"], assignment)

    def _scope_paths(self, value: Any, profile: str) -> list[str]:
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("write_paths must be an array of non-empty paths")
        if profile in READ_ONLY_PROFILES and value:
            raise ValueError(f"{profile} roles cannot receive write paths")
        result = set()
        for item in value:
            candidate = Path(item)
            if not candidate.is_absolute():
                candidate = self.workspace / candidate
            resolved = candidate.resolve()
            if resolved != self.workspace and self.workspace not in resolved.parents:
                raise ValueError(f"write path escapes configured workspace: {item}")
            result.add(resolved.relative_to(self.workspace).as_posix() or ".")
        return sorted(result)

    def _prompt(self, stack: dict, role: dict, assignment: dict) -> str:
        scope = assignment["write_paths"] or ["(read-only; no writes authorized)"]
        lines = [
            f"# {role['id']} assignment ({role['profile']})",
            f"Stack goal: {stack['goal']}",
            f"Assignment task: {assignment['task']}",
            f"Workspace: {stack['workspace']}",
            "Authorized write paths:", *(f"- {path}" for path in scope),
            "Acceptance criteria:", *(f"- {item}" for item in assignment["acceptance"] or ["Report evidence and remaining gaps."]),
        ]
        if assignment.get("candidate"):
            lines.append(f"Candidate: {assignment['candidate']}")
        if assignment["depends_on"]:
            lines.extend(["Dependency metadata (the stack owner controls ordering):",
                          json.dumps(assignment["depends_on"], ensure_ascii=False, sort_keys=True)])
        if role["profile"] in READ_ONLY_PROFILES:
            lines.append("This role is read-only. Do not edit or write files.")
        elif role["profile"] == "coder":
            lines.append("Write paths are assignment scope, not an OS-level sandbox. Keep changes within the listed paths and have the owner review the actual diff.")
        if role["profile"] == "reviewer":
            lines.append("Remain independent of the author. If you authored the candidate or cannot establish a separate author, report UNVERIFIED.")
        lines.extend(COMPLETION_CONTRACT)
        return "\n".join(lines) + "\n"

    @_registry_locked
    def create_assignment(self, stack_id: str, payload: Any) -> dict:
        stack = self.get_stack(stack_id)
        if not isinstance(payload, dict):
            raise ValueError("assignment request must be an object")
        role_id = payload.get("role_id")
        role = next((item for item in stack["roles"] if item["id"] == role_id), None)
        if role is None:
            raise ValueError("role_id is not in this stack")
        task = payload.get("task")
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task is required")
        write_paths = self._scope_paths(payload.get("write_paths", []), role["profile"])
        if stack.get("goal_id"):
            if role["profile"] == "coder":
                self.goal_active(stack["goal_id"])
            goal_dir = self.state_root / "autonomy" / "goals" / stack["goal_id"]
            goal_spec = json.loads((goal_dir / "spec.json").read_text(encoding="utf-8"))
            allowed = [(self.workspace / value).resolve() for value in goal_spec["write_paths"]]
            allowed += [goal_dir / "artifacts", goal_dir / "scratch"]
            for value in write_paths:
                path = (self.workspace / value).resolve()
                if not any(path == root or path.is_relative_to(root) for root in allowed):
                    raise ValueError("assignment exceeds immutable autonomous goal write scope")
        acceptance = payload.get("acceptance", [])
        if not isinstance(acceptance, list) or any(not isinstance(item, str) or not item.strip() for item in acceptance):
            raise ValueError("acceptance must be an array of non-empty strings")
        candidate = payload.get("candidate")
        if candidate is not None and not isinstance(candidate, str):
            raise ValueError("candidate must be a string")
        if role["profile"] == "verifier" and (
                not stack.get("goal_id") or not isinstance(candidate, str)
                or not re.fullmatch(r"[a-f0-9]{64}", candidate)):
            raise ValueError("verifier requires an autonomous goal and its frozen candidate hash")
        if stack.get("goal_id") and role["profile"] == "reviewer" and candidate:
            self.current_review(stack["goal_id"], candidate)
            if not set(goal_spec["acceptance"]).issubset(item.strip() for item in acceptance):
                raise ValueError("Formal Goal review must cover immutable acceptance; copy every original Goal.acceptance string verbatim, then add review-specific criteria")
        dependencies = payload.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not isinstance(item, dict) for item in dependencies):
            raise ValueError("depends_on must be an array of metadata objects")
        try:
            json.dumps(dependencies)
        except (TypeError, ValueError) as exc:
            raise ValueError("depends_on must be JSON data") from exc
        assignment_id = payload.get("assignment_id", f"a-{uuid.uuid4().hex}")
        path = self._assignment_file(stack_id, assignment_id)
        if path.exists():
            raise ValueError("assignment_id already exists in this stack")
        assignment = {"assignment_id": assignment_id, "stack_id": stack_id, "role_id": role_id,
                      "job_name": assignment_id, "task": task.strip(), "write_paths": write_paths,
                      "acceptance": [item.strip() for item in acceptance], "candidate": candidate,
                      "depends_on": dependencies, "task_id": None, "phase": "assigned",
                      "created_at": self._now()}
        if stack.get("goal_id"):
            epoch = self.goal_generation(stack["goal_id"])
            stamp = epoch.get("freeze", {})
            assignment["producer_generation"] = epoch["generation"]
            assignment["freeze_id"] = stamp.get("id") if stamp.get("candidate") == candidate else None
        stack_dir = self._stack_dir(stack_id)
        prompt_path = stack_dir / "prompts" / f"{assignment_id}.txt"
        _atomic_text(prompt_path, self._prompt(stack, role, assignment))
        assignment["prompt_path"] = str(prompt_path)
        _atomic_json(path, assignment)
        base = f"{BASE_URL}/stacks/{stack_id}/agents/{role_id}"
        return {"assignment_id": assignment_id, "job_name": assignment_id, "role_id": role_id,
                "stack_id": stack_id, "agent_url": f"{base}/a2a/jsonrpc",
                "card_url": f"{base}/.well-known/agent-card.json"}

    @_registry_locked
    def _load_assignment(self, stack_id: str, role_id: str, job_name: str, task_id: str) -> dict:
        stack = self.get_stack(stack_id)
        role = next((item for item in stack["roles"] if item["id"] == role_id), None)
        if role is None:
            raise ValueError("unknown stack role")
        path = self._assignment_file(stack_id, job_name)
        try:
            assignment = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError("unknown assignment for this role") from exc
        if assignment.get("stack_id") != stack_id or assignment.get("role_id") != role_id:
            raise ValueError("cross-role assignment access rejected")
        if assignment.get("assignment_id") != job_name:
            raise ValueError("assignment identity mismatch")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("A2A task ID is required")
        original = assignment.get("task_id")
        if original is not None:
            raise ValueError(f"assignment is already bound to original task ID {original}")
        if assignment.get("phase") == "retired":
            raise ValueError("Unsubmitted intent retired at Goal completion; create fresh scoped work only for an active Goal")
        prompt_path = Path(assignment.get("prompt_path", "")).resolve(strict=True)
        expected_prompt = (self._stack_dir(stack_id) / "prompts" / f"{job_name}.txt").resolve(strict=True)
        if prompt_path != expected_prompt or not prompt_path.is_file():
            raise ValueError("assignment prompt path is invalid")
        profile = PROFILES[role["profile"]]
        if stack.get("goal_id") and role["profile"] == "reviewer" and assignment.get("candidate"):
            self.current_review(stack["goal_id"], assignment["candidate"], assignment.get("freeze_id"))
        if stack.get("goal_id") and role["profile"] == "coder":
            self.goal_active(stack["goal_id"])
            assignment["producer_generation"] = self.advance_generation(stack["goal_id"])
        assignment.update(task_id=task_id, phase="bound", bound_at=self._now())
        _atomic_json(path, assignment)
        if role["profile"] == "verifier":
            goal_dir = self.state_root / "autonomy" / "goals" / stack["goal_id"]
            python = Path(sys.executable)
            if python.name.lower() == "pythonw.exe":
                python = python.with_name("python.exe")
            return {"name": job_name, "mode": "check", "cwd": self.workspace,
                    "timeout_seconds": None,
                    "command": [str(python), str(Path(__file__).resolve().parents[1] / "autonomy/checks.py"),
                                "--spec", str(goal_dir / "spec.json"),
                                "--candidate", assignment["candidate"],
                                "--output", str(goal_dir / "artifacts" / f"verification-{job_name}.json")]}
        return {"name": job_name, "mode": "claude", "cwd": self.workspace,
                "prompt_path": prompt_path, "tools": list(profile["tools"]),
                "allowed_tools": list(profile["tools"]), "permission_mode": profile["permission_mode"],
                "max_turns": None, "timeout_seconds": None}

    def loader_for(self, stack_id: str, role_id: str) -> Callable[[str, str], dict]:
        return lambda job_name, task_id: self._load_assignment(stack_id, role_id, job_name, task_id)

    async def _role_dispatcher(self, scope, receive, send) -> None:
        params = scope.get("path_params", {})
        try:
            stack = self.get_stack(params.get("stack_id"))
            role = next((item for item in stack["roles"] if item["id"] == params.get("role_id")), None)
            if role is None:
                raise KeyError("unknown role")
        except (KeyError, ValueError):
            await JSONResponse({"error": "unknown stack or role"}, status_code=404)(scope, receive, send)
            return
        key = (stack["stack_id"], role["id"])
        app = self._apps.get(key)
        if app is None:
            detailed = self._detail(stack)
            role_detail = next(item for item in detailed["roles"] if item["id"] == role["id"])
            app = self.role_app_factory(dict(detailed), dict(role_detail), self.loader_for(*key))
            self._apps[key] = app
        await app(scope, receive, send)

    async def _templates(self, _request: Request):
        return JSONResponse({"templates": [{"name": name, "roles": roles} for name, roles in TEMPLATES.items()],
                             "profiles": PROFILES})

    async def _create_stack(self, request: Request):
        try:
            return JSONResponse(self.create_stack(await request.json()), status_code=201)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    async def _list_stacks(self, _request: Request):
        return JSONResponse({"stacks": self.list_stacks()})

    async def _get_stack(self, request: Request):
        try:
            return JSONResponse(self._detail(self.get_stack(request.path_params["stack_id"])))
        except KeyError:
            return JSONResponse({"error": "unknown stack"}, status_code=404)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)

    async def _create_assignment(self, request: Request):
        try:
            data = self.create_assignment(request.path_params["stack_id"], await request.json())
            return JSONResponse(data, status_code=201)
        except KeyError:
            return JSONResponse({"error": "unknown stack"}, status_code=404)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    def routes(self):
        return [
            Route("/control/templates", self._templates, methods=["GET"]),
            Route("/control/stacks", self._list_stacks, methods=["GET"]),
            Route("/control/stacks", self._create_stack, methods=["POST"]),
            Route("/control/stacks/{stack_id}/assignments", self._create_assignment, methods=["POST"]),
            Route("/control/stacks/{stack_id}", self._get_stack, methods=["GET"]),
            Mount("/stacks/{stack_id}/agents/{role_id}", app=self._role_dispatcher),
        ]
