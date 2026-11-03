"""MCP facade over the official-SDK A2A host worker (a2a-stack/agent/service.py).

Exposes legacy task tools and dynamic stack control over streamable HTTP.
Calls use the fixed A2A_URL upstream; task payloads use the official SDK.
Assignment text and scope are data; callers cannot supply upstream URLs,
executables, model overrides or arbitrary CLI configuration.
"""

from __future__ import annotations

import contextlib
import inspect
import json
import os
import re
import uuid
from urllib.parse import urlsplit, urlunsplit

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.types import (CancelTaskRequest, GetTaskRequest, ListTasksRequest, Message,
                       Part, Role, SendMessageConfiguration, SendMessageRequest)
from google.protobuf.json_format import MessageToDict, ParseDict
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

UPSTREAM = os.environ.get("A2A_URL", "http://127.0.0.1:18890")
TIMEOUT = 15.0
PROTOCOL_VERSION = "1.0"
INTERFACE_KEYS = ("supportedInterfaces", "supported_interfaces",
                  "additionalInterfaces", "additional_interfaces")

mcp = MCPServer("northstar-a2a", instructions=(
    "人通过 set_goal 设置当前目标，通过 get_goal_report 查看结果并决定下一条 Goal。"
    "执行过程由主 Agent 动态选择模板和 A2A 团队，自主修复、重试和验收；"
    "普通错误及中间 api_retry 不能成为人工救场或整个 Goal 停止的默认理由，不自设费用/轮数/总时长上限。"
    "完成当前 Goal 后报告并等待新指令。只有 harness 启动且已持有 IMMUTABLE GOAL SPEC 的执行主 Agent 使用动态 stack/task 工具和"
    "freeze_goal_candidate，在原 goal_id 内继续，不调用 set_goal/stop_goal/resume_goal。"
    "保留原始验收、作用范围及发布/交易/凭据限制；只有程序核实的真实外部依赖才请求人工。"
))
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
STACK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _to_upstream(url: str, upstream: str = UPSTREAM) -> str:
    """Rewrite scheme/netloc of an advertised URL, preserving the exact path."""
    target, upstream_parts = urlsplit(url), urlsplit(upstream)
    return urlunsplit(
        (upstream_parts.scheme, upstream_parts.netloc, target.path, target.query, target.fragment))


def _agent_base(stack_id: str | None = None, role_id: str | None = None) -> str:
    if stack_id is None and role_id is None:
        return UPSTREAM
    if stack_id is None or role_id is None:
        raise ValueError("stack_id and role_id must be provided together")
    for label, value in (("stack_id", stack_id), ("role_id", role_id)):
        if not isinstance(value, str) or not STACK_ID_RE.fullmatch(value):
            raise ValueError(f"{label} must contain 1-80 ASCII letters, digits, '_' or '-'")
    return f"{UPSTREAM.rstrip('/')}/stacks/{stack_id}/agents/{role_id}"


def _role_roster(value: list[dict] | None) -> list[dict] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("roles must be an array")
    roles = []
    for role in value:
        if not isinstance(role, dict):
            raise ValueError("each role must be an object")
        role_id, profile = role.get("id"), role.get("profile")
        if not isinstance(role_id, str) or not STACK_ID_RE.fullmatch(role_id):
            raise ValueError("role id must contain 1-80 ASCII letters, digits, '_' or '-'")
        if not isinstance(profile, str) or not profile:
            raise ValueError("role profile is required")
        # Do not forward caller-supplied URLs, commands, model names, or other role fields.
        roles.append({"id": role_id, "profile": profile})
    return roles


def _to_dict(value) -> dict:
    """Render a protocol object as protobuf JSON; never fabricate success."""
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        value = next((i for i in value if hasattr(i, "DESCRIPTOR")), None)
    if value is None or not hasattr(value, "DESCRIPTOR"):
        raise RuntimeError(f"upstream returned an unsupported payload: {type(value)!r}")
    return MessageToDict(value)


async def _load_card(http: httpx.AsyncClient, agent_base: str | None = None):
    """Resolve the upstream card, validate JSONRPC 1.0, retarget the URLs."""
    upstream = agent_base or UPSTREAM
    card = await A2ACardResolver(http, upstream).get_agent_card()
    data = MessageToDict(card)
    versions = [data.get("protocolVersion") or data.get("protocol_version")]
    bindings = []
    for key in INTERFACE_KEYS:
        for interface in data.get(key) or []:
            if not isinstance(interface, dict):
                continue
            versions.append(
                interface.get("protocolVersion") or interface.get("protocol_version"))
            binding = interface.get("protocolBinding") or interface.get("protocol_binding")
            if binding:
                bindings.append(str(binding).replace("_", "").replace("-", "").upper())
    for version in versions:
        if version and str(version) != PROTOCOL_VERSION:
            raise RuntimeError(f"unsupported A2A protocol version: {version}")
    if bindings and "JSONRPC" not in bindings:
        raise RuntimeError("upstream card does not advertise a JSONRPC transport")
    out = dict(data)
    for key in INTERFACE_KEYS:
        items = out.get(key)
        if isinstance(items, list):
            out[key] = [{**i, "url": _to_upstream(i["url"], upstream)}
                        if isinstance(i, dict) and isinstance(i.get("url"), str) else i
                        for i in items]
    if isinstance(out.get("url"), str):
        out["url"] = _to_upstream(out["url"], upstream)
    retargeted = type(card)()
    ParseDict(out, retargeted, ignore_unknown_fields=True)
    return retargeted


@contextlib.asynccontextmanager
async def _client(agent_base: str | None = None):
    """Yield an upstream A2A client, always closing it afterwards."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as http:
        card = await _load_card(http, agent_base)
        client = create_client(
            card, client_config=ClientConfig(
                streaming=False, polling=False, httpx_client=http,
                supported_protocol_bindings=["JSONRPC"]))
        if inspect.isawaitable(client):
            client = await client
        try:
            yield client
        finally:
            closer = getattr(client, "close", None)
            if closer is not None:
                result = closer()
                if inspect.isawaitable(result):
                    await result


async def _first_response(stream) -> dict:
    """Return the first streamed response that carries a task id."""
    iterator = stream
    if inspect.isawaitable(iterator):
        iterator = await iterator
    latest: dict = {}
    async with contextlib.aclosing(iterator) as events:
        async for event in events:
            payload = _to_dict(event)
            latest = payload
            task = payload.get("task")
            task_id = task.get("id") if isinstance(task, dict) else payload.get("id")
            if task_id:
                return payload
    if not latest:
        raise RuntimeError("upstream returned no A2A response")
    return latest


@mcp.tool(annotations=READ_ONLY)
async def discover_agent(stack_id: str | None = None, role_id: str | None = None) -> dict:
    """Return the configured root agent card or one selected stack role card."""
    agent_base = _agent_base(stack_id, role_id)
    async with httpx.AsyncClient(timeout=TIMEOUT) as http:
        card = await _load_card(http, agent_base)
    return {"upstream": agent_base, "agent_card": MessageToDict(card)}


@mcp.tool()
async def submit_job(job_name: str, stack_id: str | None = None, role_id: str | None = None) -> dict:
    """Submit a registered local job by name and return the resulting A2A task."""
    job = (job_name or "").strip()
    if not job:
        raise ValueError("job_name is required")
    agent_base = _agent_base(stack_id, role_id)
    request = SendMessageRequest(
        message=Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=json.dumps({"job": job}))],
        ),
        configuration=SendMessageConfiguration(return_immediately=True),
    )
    async with _client(agent_base) as client:
        return await _first_response(client.send_message(request))


@mcp.tool(annotations=READ_ONLY)
async def get_task(task_id: str, stack_id: str | None = None, role_id: str | None = None) -> dict:
    """Fetch one A2A task by id."""
    task_id = (task_id or "").strip()
    if not task_id:
        raise ValueError("task_id is required")
    agent_base = _agent_base(stack_id, role_id)
    async with _client(agent_base) as client:
        return _to_dict(await client.get_task(GetTaskRequest(id=task_id)))


@mcp.tool()
async def cancel_task(task_id: str, stack_id: str | None = None, role_id: str | None = None) -> dict:
    """Cancel one A2A task by id."""
    task_id = (task_id or "").strip()
    if not task_id:
        raise ValueError("task_id is required")
    agent_base = _agent_base(stack_id, role_id)
    async with _client(agent_base) as client:
        return _to_dict(await client.cancel_task(CancelTaskRequest(id=task_id)))


@mcp.tool(annotations=READ_ONLY)
async def list_tasks(stack_id: str | None = None, role_id: str | None = None) -> dict:
    """List tasks for the root agent or a selected stack role."""
    agent_base = _agent_base(stack_id, role_id)
    async with _client(agent_base) as client:
        return _to_dict(await client.list_tasks(ListTasksRequest(include_artifacts=True)))


async def _control_request(method: str, path: str, body: dict | None = None) -> dict:
    """Proxy one fixed host control endpoint; MCP arguments never choose a URL."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as http:
        response = await http.request(method, f"{UPSTREAM.rstrip('/')}{path}", json=body)
        response.raise_for_status()
        value = response.json()
    if not isinstance(value, dict):
        raise RuntimeError("host control endpoint returned a non-object payload")
    return value


@mcp.tool(annotations=READ_ONLY)
async def list_templates() -> dict:
    """List available stack templates and trusted role profiles."""
    return await _control_request("GET", "/control/templates")


@mcp.tool()
async def create_stack(workspace: str, goal: str, template_name: str | None = None,
                       roles: list[dict] | None = None, name: str | None = None,
                       goal_id: str | None = None) -> dict:
    """Create a dynamic stack from a template or explicit role roster."""
    body = {"workspace": workspace, "goal": goal}
    optional = {"template_name": template_name, "roles": _role_roster(roles), "name": name, "goal_id": goal_id}
    body.update({key: value for key, value in optional.items() if value is not None})
    return await _control_request("POST", "/control/stacks", body)


@mcp.tool(annotations=READ_ONLY)
async def list_stacks() -> dict:
    """List persisted dynamic stacks."""
    return await _control_request("GET", "/control/stacks")


@mcp.tool(annotations=READ_ONLY)
async def get_stack(stack_id: str) -> dict:
    """Return one stack, including roles, endpoint URLs, and assignment bindings."""
    _agent_base(stack_id, "validation-role")
    return await _control_request("GET", f"/control/stacks/{stack_id}")


@mcp.tool()
async def create_assignment(stack_id: str, role_id: str, task: str, write_paths: list[str],
                            acceptance: list[str], candidate: str | None = None,
                            assignment_id: str | None = None,
                            depends_on: list[dict] | None = None) -> dict:
    """Create one scoped assignment for a role in a stack."""
    _agent_base(stack_id, role_id)
    body = {"role_id": role_id, "task": task, "write_paths": write_paths, "acceptance": acceptance}
    optional = {"candidate": candidate, "assignment_id": assignment_id, "depends_on": depends_on}
    body.update({key: value for key, value in optional.items() if value is not None})
    return await _control_request("POST", f"/control/stacks/{stack_id}/assignments", body)


def _goal_path(goal_id: str) -> str:
    if not isinstance(goal_id, str) or not re.fullmatch(r"g-[a-f0-9]{32}", goal_id):
        raise ValueError("invalid autonomous goal ID")
    return f"/control/goals/{goal_id}"


@mcp.tool(annotations=READ_ONLY)
async def list_goal_checks() -> dict:
    """List owner-registered host checks; callers cannot supply commands."""
    return await _control_request("GET", "/control/goals/checks")


@mcp.tool()
async def set_goal(workspace: str, goal: str, acceptance: list[str],
                                write_paths: list[str], check_ids: list[str] | None = None,
                                constraints: list[str] | None = None,
                                required_inputs: list[str] | None = None,
                                user_gates: list[str] | None = None) -> dict:
    """Start a persistent main agent that chooses and operates its own A2A team."""
    body = {"workspace": workspace, "goal": goal, "acceptance": acceptance, "write_paths": write_paths}
    body.update({key: value for key, value in {
        "check_ids": check_ids, "constraints": constraints,
        "required_inputs": required_inputs, "user_gates": user_gates}.items() if value is not None})
    return await _control_request("POST", "/control/goals", body)


@mcp.tool(annotations=READ_ONLY)
async def list_goals() -> dict:
    """Inspect goals without intervening in their running agent loops."""
    return await _control_request("GET", "/control/goals")


@mcp.tool(annotations=READ_ONLY)
async def get_goal_report(goal_id: str) -> dict:
    """Read persistent progress, recovery and final acceptance evidence."""
    return await _control_request("GET", _goal_path(goal_id) + "/report")


@mcp.tool()
async def stop_goal(goal_id: str) -> dict:
    """Explicitly cancel this goal and its associated A2A assignments."""
    return await _control_request("POST", _goal_path(goal_id) + "/cancel")


@mcp.tool()
async def resume_goal(goal_id: str) -> dict:
    """Resume the same goal after explicit cancellation or resolved user dependency."""
    return await _control_request("POST", _goal_path(goal_id) + "/resume")


@mcp.tool()
async def freeze_goal_candidate(goal_id: str, files: list[str]) -> dict:
    """Compute actual file hashes and save a candidate in this goal's own artifact directory."""
    return await _control_request("POST", _goal_path(goal_id) + "/candidate", {"files": files})


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=18892,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=["127.0.0.1:*", "localhost:*", "mcp-gateway:*"],
            allowed_origins=["http://127.0.0.1:*", "http://localhost:*"],
        ),
    )


if __name__ == "__main__":
    main()
