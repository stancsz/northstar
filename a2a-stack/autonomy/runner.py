"""Persistent goal controller around the installed Claude native decision loop.

The host owns the process Job Object and immutable spec. This module never
dispatches work itself, acquires the worker lock, or imposes an execution budget.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STACK = Path(__file__).resolve().parents[1]
runtime = load_module("goal_runtime", STACK / "runtime/runner.py")
review_helpers = load_module("goal_review", STACK / "runtime/review.py")
candidate_scope = load_module("goal_candidate_scope", STACK / "autonomy/candidate_scope.py")
MCP_TOOLS = tuple("mcp__northstar_a2a__" + name for name in (
    "list_templates", "create_stack", "list_stacks", "get_stack", "discover_agent",
    "create_assignment", "submit_job", "get_task", "list_tasks", "cancel_task", "freeze_goal_candidate"))
USER_GOAL_MUTATIONS = tuple("mcp__northstar_a2a__" + name for name in ("set_goal", "stop_goal", "resume_goal"))
# The native print-background idle wait defaults to 600000ms.  The child is
# pinned to 0 so background work can finish without an idle-wait ceiling; the flag
# reaches the child both through the copied environment and through the
# child-only --settings override, which outranks a higher-precedence profile.
BG_WAIT_FLAG = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"
BG_WAIT_SETTINGS = json.dumps({"env": {BG_WAIT_FLAG: "0"}})
OWNER_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "status": {"enum": ["complete", "continue", "needs_user"]},
    "summary": {"type": "string"}, "candidate_manifest": {"type": ["string", "null"]},
    "review": {"anyOf": [{"type": "null"}, {"type": "object", "additionalProperties": False,
        "properties": {k: {"type": "string"} for k in ("stack_id", "role_id", "task_id")},
        "required": ["stack_id", "role_id", "task_id"]}]},
    "blocker": {"anyOf": [{"type": "null"}, {"type": "object", "additionalProperties": False,
        "properties": {"kind": {"type": "string"}, "message": {"type": "string"},
                       "evidence": {"type": "array", "items": {"type": "string"}},
                       "gate": {"type": ["string", "null"]}, "input_path": {"type": ["string", "null"]}},
        "required": ["kind", "message", "evidence"]}]}},
    "required": ["status", "summary", "candidate_manifest", "review", "blocker"]}
SUPERVISOR_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "classification": {"enum": ["recoverable", "external_dependency"]},
    "advice": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}},
    "recovery_action": {"enum": ["continue", "reset_session"]}},
    "required": ["classification", "advice", "evidence"]}


class Canceled(Exception):
    pass


class InfrastructureUnavailable(Exception):
    """Canonical capability failure; retry transport without a model supervisor."""


class OwnedSnapshotUnavailable(InfrastructureUnavailable):
    """Only a known Windows sharing/access failure writing this Journal's state."""
    def __init__(self, winerror):
        self.winerror = winerror
        super().__init__(f"Owned goal-state snapshot write unavailable (winerror={winerror})")


def configured_mcp_url(spec):
    config = json.loads(Path(spec["mcp_config"]).read_text(encoding="utf-8"))
    server = config["mcpServers"]["northstar_a2a"]
    if server.get("type") not in ("http", "streamable-http") or not isinstance(server.get("url"), str):
        raise ValueError("northstar_a2a requires a configured HTTP MCP URL")
    return server["url"]


def native_capability_receipt(event):
    required = set(MCP_TOOLS)
    tools = event.get("tools", [])
    present = {tool for tool in tools if isinstance(tool, str)} if isinstance(tools, list) else set()
    missing = sorted(required - present)
    servers = event.get("mcp_servers")
    connected = True
    if isinstance(servers, list):
        matching = [server for server in servers if isinstance(server, dict) and server.get("name") == "northstar_a2a"]
        connected = bool(matching) and all(server.get("status") == "connected" for server in matching)
    return {"ready": not missing and connected, "missing_tools": missing,
            "server_connected": connected, "required_tool_count": len(required)}


RESET_CATEGORIES = {"session_not_found", "session_corrupt", "invalid_session", "context_limit"}


class NativeFailure(ValueError):
    def __init__(self, channel, diagnostic, exit_code, subtype="unknown"):
        self.channel, self.diagnostic = channel, dict(diagnostic)
        super().__init__("Native process failed: " + json.dumps({"exit_code": exit_code,
            "subtype": subtype, **diagnostic}))


def reset_owner_session(journal, reason):
    previous = list(journal.state.get("previous_session_ids", []))
    session = journal.state.get("session_id")
    if session and session not in previous:
        previous.append(session)
    journal.record("owner_session_reset", session_id=None, previous_session_ids=previous,
                   session_reset_reason=reason)


def parse_object(value):
    if isinstance(value, dict):
        return value
    text = str(value).strip()
    try:
        result = json.loads(text)
    except ValueError:
        blocks = list(re.finditer(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)```", text, re.I))
        if len(blocks) != 1:
            raise ValueError("Expected exactly one unambiguous fenced JSON object")
        block = blocks[0]
        surrounding = text[:block.start()] + text[block.end():]
        # A second valid object outside the block is ambiguous even if prose
        # separates it. Never select whichever candidate happens to be first.
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", surrounding):
            try:
                other, _ = decoder.raw_decode(surrounding[match.start():])
            except ValueError:
                continue
            if isinstance(other, dict):
                raise ValueError("Multiple JSON objects in response")
        result = json.loads(block.group(1))
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def native_diagnostic(event):
    """Extract only standard categories/status numbers, never native payloads."""
    categories = {"429": "rate_limited", "529": "overloaded", "401": "authentication_required",
        "403": "permission_denied", "400": "invalid_request", "408": "transport_timeout",
        "unrecognized_model": "model_unavailable", "authentication_failed": "authentication_required",
        "invalid_api_key": "authentication_required", "context_length_exceeded": "context_limit",
        "overloaded_error": "overloaded", "rate_limit_error": "rate_limited",
        "api_error": "provider_error", "invalid_request_error": "invalid_request",
        "account_on_hold": "account_on_hold", "billing_error": "billing_error",
        "session_not_found": "session_not_found", "conversation_not_found": "session_not_found",
        "invalid_session": "invalid_session", "session_corrupt": "session_corrupt",
        "context_overflow": "context_limit", "context_window_exceeded": "context_limit",
        "prompt_too_long": "context_limit"}
    error = event.get("error")
    nested = error if isinstance(error, dict) else {}
    values = [nested.get(k) for k in ("code", "type", "status_code", "status")]
    if isinstance(error, str):
        values.append(error)
    values += [event.get(k) for k in ("code", "status_code", "http_status", "error_status")]
    # Some native final failures contain only an anchored canonical API code.
    match = re.match(r"^API error:\s*(\d{3}|unrecognized_model)(?:\b|$)",
                     str(event.get("result", "")), re.I)
    if match:
        values.append(match.group(1))
    if (event.get("type") == "result" and event.get("is_error") is True
            and re.match(r"^(?:Error:\s*)?Prompt is too long(?:\b|$)", str(event.get("result", "")), re.I)):
        values.append("prompt_too_long")
    result = {}
    for value in values:
        code = str(value).lower()
        if code.isdigit() and 100 <= int(code) <= 599:
            result["http_status"] = int(code)
            result["error_category"] = categories.get(code, "provider_error" if int(code) >= 500 else "http_error")
        elif code in categories:
            result.setdefault("error_category", categories[code])
    return result


def native_local_diagnostic(line):
    """Recognize canonical CLI-local failures without retaining stderr contents."""
    text = line.strip()
    if re.match(r"^(?:Error:\s*)?No conversation found with session ID(?:\s|:)", text, re.I):
        return {"error_category": "session_not_found"}
    if re.match(r"^(?:Error:\s*)?(?:Invalid session ID|Session data is corrupt)(?:\s|:|$)", text, re.I):
        return {"error_category": "invalid_session" if "invalid session" in text.lower() else "session_corrupt"}
    return {}


def within(path, root):
    return path.resolve().is_relative_to(root.resolve())


def claude_argv(spec, session_id=None, supervisor=False, executable=None):
    tools = "Read,Glob"
    argv = [executable or runtime.claude_executable(), "-p", "--verbose", "--output-format", "stream-json",
            "--json-schema", json.dumps(SUPERVISOR_SCHEMA if supervisor else OWNER_SCHEMA),
            "--permission-mode", "acceptEdits", "--tools", tools,
            "--allowedTools", tools if supervisor else tools + "," + ",".join(MCP_TOOLS),
            "--mcp-config", spec["mcp_config"], "--strict-mcp-config"]
    if session_id and not supervisor:
        argv += ["--resume", session_id]
    argv += ["--disallowedTools", ",".join(("Bash", "Edit", "Write", *USER_GOAL_MUTATIONS,
                                         *(MCP_TOOLS if supervisor else ())))]
    argv += ["--settings", BG_WAIT_SETTINGS]
    return argv


class Journal:
    def __init__(self, directory, spec):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / "state.json"
        self.state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "id": spec["id"], "status": "RUNNING", "session_id": None, "recovery_count": 0}
        # Bind resumptions to the same immutable goal, scope and checks.
        import hashlib
        digest = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        if self.state.get("spec_digest", digest) != digest:
            raise ValueError("Immutable goal spec changed")
        self.state["spec_digest"] = digest
        self.record("attached", runner_pid=os.getpid())

    def record(self, event, **fields):
        self.state.update(fields, updated_at=runtime.now())
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"event": event, "at": self.state["updated_at"], **fields}) + "\n")
        try:
            runtime.atomic_json(self.directory / "state.json", self.state)
        except PermissionError as exc:
            if getattr(exc, "winerror", None) in (5, 32, 33):
                raise OwnedSnapshotUnavailable(exc.winerror) from exc
            raise

    def cancel_check(self):
        if (self.directory / "cancel.request").exists():
            raise Canceled()


class NativeBackend:
    def __init__(self, spec, journal, mcp_probe=None):
        self.spec, self.journal = spec, journal
        self.mcp_probe = mcp_probe or self.probe_mcp

    async def probe_mcp(self):
        from mcp import Client
        async with Client(configured_mcp_url(self.spec)) as client:
            result = await client.list_tools()
            return {tool.name for tool in result.tools}

    def wait_for_mcp(self):
        """No owner/model is started until configured transport proves tools ready."""
        async def wait():
            attempt = 0
            required = {name.removeprefix("mcp__northstar_a2a__") for name in MCP_TOOLS}
            while True:
                self.journal.cancel_check()
                attempt += 1
                task = asyncio.create_task(self.mcp_probe())
                names, category = set(), "transport_unavailable"
                try:
                    while not task.done():
                        self.journal.cancel_check()
                        await asyncio.wait({task}, timeout=.2)
                    names = set(task.result())
                    category = "missing_tools"
                except Canceled:
                    raise
                except Exception:
                    # SDK exceptions can contain headers/URLs; persist no raw payload.
                    pass
                finally:
                    if not task.done():
                        task.cancel()
                        await asyncio.gather(task, return_exceptions=True)
                missing = sorted(required - names)
                if not missing:
                    receipt = {"ready_at": runtime.now(), "attempts": attempt,
                               "required_tools": sorted(required), "source": "configured_mcp_sdk_list_tools"}
                    self.journal.record("infrastructure_ready", status="RUNNING",
                        infrastructure_wait=None, infrastructure_receipt=receipt)
                    return receipt
                self.journal.record("infrastructure_wait", status="RECOVERING",
                    infrastructure_wait={"at": runtime.now(), "attempt": attempt, "category": category,
                                         "missing_tools": missing})
                # Bounded backoff cadence; neither attempts nor total wait is capped.
                delay = min(.25 * attempt, 5.0)
                until = asyncio.get_running_loop().time() + delay
                while asyncio.get_running_loop().time() < until:
                    self.journal.cancel_check()
                    await asyncio.sleep(min(.2, max(0, until - asyncio.get_running_loop().time())))
        return asyncio.run(wait())

    def process(self, argv, prompt=None, channel="owner"):
        """Pump both pipes without a deadline; inherited host Job owns children."""
        self.journal.cancel_check()
        env = os.environ.copy()
        env["CLAUDE_CODE_RETRY_WATCHDOG"] = "1"
        if channel in ("owner", "supervisor"):
            # Child-only: the parent environment is never mutated, and a plain
            # check command keeps exactly the environment it had before.
            env[BG_WAIT_FLAG] = "0"
        job = runtime.Job() if os.name == "nt" else None
        proc = None
        try:
            proc = subprocess.Popen(argv, cwd=self.spec["workspace"], env=env, shell=False,
                stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                errors="replace", creationflags=(subprocess.CREATE_NO_WINDOW | 0x00000004) if job else 0)
            if job:
                job.assign(proc)  # Assign suspended child before any code or grandchild executes.
        except BaseException:
            if job:
                job.close()
            if proc and proc.poll() is None:
                proc.kill()
                proc.wait()
            raise
        try:
            failures = dict(self.journal.state.get("native_failures", {}))
            failures.pop(channel, None)
            self.journal.record("process_observations_reset", native_failures=failures)
            self.journal.record("process_started", **{channel + "_pid": proc.pid})
            messages = queue.Queue()
            def pump(pipe, source):
                try:
                    for line in pipe:
                        messages.put((source, line))
                finally:
                    pipe.close()
                    messages.put((source, None))
            for pipe, source in ((proc.stdout, "stdout"), (proc.stderr, "stderr")):
                threading.Thread(target=pump, args=(pipe, source), daemon=True).start()
            # Writing stdin in a thread also keeps cancellation responsive for large prompts.
            def feed():
                try:
                    proc.stdin.write(prompt)
                    proc.stdin.close()
                except (OSError, ValueError):
                    pass
            if prompt is not None:
                threading.Thread(target=feed, daemon=True).start()
            final, output, ended, diagnostic = None, [], 0, {}
            with (self.journal.directory / (channel + ".jsonl")).open("a", encoding="utf-8") as log:
                while ended < 2 or proc.poll() is None:
                    self.journal.cancel_check()
                    try:
                        source, line = messages.get(timeout=.2)
                    except queue.Empty:
                        continue
                    if line is None:
                        ended += 1
                        continue
                    if prompt is None:
                        output.append(runtime._safe_handoff(line))
                        continue
                    metadata = runtime.sanitized_event(line)
                    # Result text can contain tool payloads: keep it in memory only.
                    metadata.pop("handoff", None)
                    if source == "stderr":
                        observed = native_local_diagnostic(line)
                        if observed:
                            diagnostic = observed
                            metadata.update(observed)
                    log.write(json.dumps({"source": source, **metadata}) + "\n")
                    log.flush()
                    if source == "stdout":
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(event, dict):
                            continue
                        observed = native_diagnostic(event)
                        if observed:
                            # Intermediate recovery notices cannot invalidate a
                            # resumable owner context; only a final result can.
                            if event.get("type") == "result" or observed.get("error_category") not in RESET_CATEGORIES:
                                diagnostic = observed
                            metadata.update(observed)
                        if channel == "owner" and event.get("type") == "system" and event.get("subtype") == "init":
                            if isinstance(event.get("session_id"), str):
                                self.journal.record("session_initialized", session_id=event["session_id"])
                            receipt = native_capability_receipt(event)
                            self.journal.record("native_capability_checked", native_capability_receipt={
                                "at": runtime.now(), **receipt})
                            if not receipt["ready"]:
                                raise InfrastructureUnavailable("Native owner initialized without required MCP capabilities")
                        if event.get("type") == "result":
                            final = event
                    self.journal.record("native_event", last_native_event=metadata)
            code = proc.wait()
            self.journal.record("process_finished", native_exitcode=code, **{channel + "_pid": None})
            if prompt is None:
                return {"exit_code": code, "output": "".join(output)}
            if code != 0 or not final or final.get("is_error"):
                # Native result text may quote prompts/tool results; never persist it.
                diagnostic.update(native_diagnostic(final or {}))
                # Authentication escalation requires structured native metadata,
                # never an owner's prose or an API code quoted in result text.
                structured = {k: v for k, v in (final or {}).items() if k != "result"}
                verified = native_diagnostic(structured)
                if verified and final and final.get("is_error") is True:
                    failures[channel] = {**verified, "source": "native_metadata", "terminal": True}
                    self.journal.record("native_failure_observed", native_failures=failures)
                subtype = (final or {}).get("subtype")
                if subtype not in ("success", "error_during_execution", "error_max_turns", "error_max_budget_usd", "error_max_structured_output_retries"):
                    subtype = "unknown"
                raise NativeFailure(channel, diagnostic, code, subtype)
            return parse_object(final.get("structured_output") or final.get("result"))
        finally:
            if job:
                job.close()  # Includes all native/check grandchildren on cancellation or error.
            if proc.poll() is None:
                # The parent additionally closes the complete inherited Windows Job.
                proc.kill()
            proc.wait()
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                if pipe:
                    pipe.close()

    def owner(self, feedback):
        self.wait_for_mcp()
        prompt = Path(self.spec["owner_prompt"]).read_text(encoding="utf-8")
        prompt += "\nIMMUTABLE GOAL SPEC:\n" + json.dumps(self.spec) + "\nCURRENT FACTS / RECOVERY:\n" + feedback
        return self.process(claude_argv(self.spec, self.journal.state.get("session_id")), prompt)

    def _host_completion(self, payload):
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        request = Request("http://127.0.0.1:18890/control/goals/" + self.spec["id"] + "/complete",
            data=json.dumps(payload).encode("utf-8"), headers={"content-type": "application/json"}, method="POST")
        try:
            with urlopen(request) as response:
                return json.load(response)
        except HTTPError as error:
            if 400 <= error.code < 500:
                detail = json.loads(error.read().decode("utf-8"))
                return {"status": "refresh", "reason": runtime._safe_handoff(detail.get("error", "Host rejected completion evidence"))}
            raise

    def _completion(self, payload):
        while True:
            self.journal.cancel_check()
            try:
                result = self._host_completion(payload)
            except Exception:
                result = {"status": "wait", "reason": "Host completion transport unavailable"}
            if result.get("status") in ("ready", "complete"):
                return result
            if result.get("status") != "wait":
                raise InfrastructureUnavailable("Completion evidence refresh required: " + runtime._safe_handoff(result.get("reason", "Reconcile current candidate")))
            # Do not overwrite state.json after an ambiguously completed host
            # commit. Keep waits auditable without clobbering host COMPLETE.
            with (self.journal.directory / "events.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps({"event": "completion_wait", "at": runtime.now(),
                    "reason": runtime._safe_handoff(result.get("reason", "Pending productive work"))}) + "\n")
            time.sleep(.2)

    def prepare_completion(self, proposal):
        return self._completion({"operation": "prepare", "proposal": proposal})["ticket"]

    def commit_completion(self, proposal, ticket, checks):
        return self._completion({"operation": "commit", "proposal": proposal, "ticket": ticket, "checks": checks})

    def supervisor(self, facts):
        prompt = Path(self.spec["supervisor_prompt"]).read_text(encoding="utf-8")
        prompt += "\nREADONLY DIAGNOSIS. No tools beyond Read/Glob.\n" + json.dumps({"spec": self.spec, "facts": facts})
        return self.process(claude_argv(self.spec, supervisor=True), prompt, "supervisor")

    def check(self, check):
        cwd = Path(check["cwd"]).resolve()
        if not within(cwd, Path(self.spec["workspace"])):
            raise ValueError("Check cwd escapes workspace")
        original = self.spec
        self.spec = {**original, "workspace": str(cwd)}
        try:
            return self.process(check["argv"], channel="check")
        finally:
            self.spec = original

    def fetch_review(self, reference):
        async def fetch():
            from mcp import Client
            async with Client("http://127.0.0.1:18892/mcp") as client:
                async def call(name, args):
                    result = await client.call_tool(name, args)
                    if result.is_error:
                        raise ValueError("MCP review fetch failed")
                    data = getattr(result, "structured_content", None)
                    if data is not None:
                        return data
                    return parse_object("".join(p.text for p in result.content if getattr(p, "type", None) == "text"))
                task = await call("get_task", reference)
                stack = await call("get_stack", {"stack_id": reference["stack_id"]})
                producers = []
                listed = await call("list_stacks", {})
                goal_stacks = listed.get("stacks", [])
                if not any(item.get("stack_id") == stack["stack_id"] for item in goal_stacks):
                    goal_stacks.append(stack)
                for owned in goal_stacks:
                    if owned.get("goal_id") != self.spec["id"]:
                        continue
                    roles = {role["id"]: role.get("profile") for role in owned.get("roles", [])}
                    for assignment in bound_assignments(self.spec, owned["stack_id"]):
                        role_id = assignment.get("role_id")
                        task_id = assignment.get("bound_task_id", assignment.get("task_id"))
                        if task_id and roles.get(role_id) == "coder":
                            try:
                                actual = await call("get_task", {"stack_id": owned["stack_id"], "role_id": role_id, "task_id": task_id})
                            except Exception:
                                # Unknown task status cannot prove that a writer has
                                # stopped. Reconcile it rather than racing acceptance.
                                actual = {"id": task_id, "status": {"state": "UNKNOWN"}}
                            producers.append({"stack_id": owned["stack_id"], "goal_id": owned["goal_id"],
                                "profile": roles[role_id], "role_id": role_id, "task_id": task_id, "task": actual})
                # Never trust a remotely supplied internal receipt list.
                stack["_producer_tasks"] = producers
                stack["all_goal_producers"] = producers
                return task, stack
        return asyncio.run(fetch())


def freeze_current(spec, directory, manifest_path):
    workspace = Path(spec["workspace"]).resolve()
    path = Path(manifest_path)
    if not path.is_absolute():
        path = workspace / path
    if not (within(path, workspace) or within(path, directory)):
        raise ValueError("Manifest outside workspace/state")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    allowed = [(workspace / p).resolve() for p in spec["write_paths"]]
    for name in manifest["files"]:
        file = (workspace / name).resolve()
        if not (any(file == p or within(file, p) for p in allowed) or within(file, directory / "artifacts")):
            raise ValueError("Reviewed file outside explicit goal scope: " + name)
    # A candidate that lists only part of the scope would hide a real scoped
    # change from review, so coverage is checked against the immutable baseline.
    candidate_scope.validate_scope_coverage(
        workspace, spec["write_paths"], spec.get("baseline", {}), manifest["files"])
    # Existing helper owns canonical hashing and stale-candidate rules.
    review_helpers.ROOT = workspace
    if review_helpers.candidate(manifest["files"]) != manifest:
        raise ValueError("STALE candidate manifest")
    return manifest


def review_artifacts(task):
    for artifact in task.get("artifacts", []):
        for part in artifact.get("parts", []):
            try:
                value = part.get("data") if isinstance(part.get("data"), dict) else part.get("text", "")
                yield parse_object(value)
            except (ValueError, TypeError):
                continue


def bound_assignments(spec, stack_id):
    base = Path(spec["state_root"]) / "stacks"
    stack_dir = base / stack_id
    if not within(stack_dir, base):
        raise ValueError("Invalid stack identity")
    return [json.loads(path.read_text(encoding="utf-8")) for path in (stack_dir / "assignments").glob("*.json")]


def producer_receipts(spec, reference, manifest, stack, assignments):
    workspace = Path(spec["workspace"]).resolve()
    # The changed set comes from the scope versus the immutable baseline, not
    # from the manifest's listed entries; a file omitted from the manifest must
    # not escape the provenance rule.
    changes = candidate_scope.scope_changes(
        workspace, spec["write_paths"], spec.get("baseline", {}))
    changed = set(changes)
    receipts, covered = [], set()
    tasks = stack.get("all_goal_producers", stack.get("_producer_tasks", []))
    owned_assignments = []
    for item in tasks:
        owner_stack = item.get("stack_id", reference["stack_id"])
        if item.get("goal_id", stack.get("goal_id")) != spec["id"]:
            raise ValueError("Producer belongs to another goal")
        state = item.get("task", {}).get("status", {}).get("state", "").upper()
        if state in ("SUBMITTED", "WORKING", "TASK_STATE_SUBMITTED", "TASK_STATE_WORKING", "UNKNOWN"):
            raise ValueError("Owned coder task still active or unresolved: " + str(item.get("task_id")))
        for assignment in bound_assignments(spec, owner_stack):
            if (assignment.get("role_id") == item.get("role_id")
                    and assignment.get("bound_task_id", assignment.get("task_id")) == item.get("task_id")):
                owned_assignments.append((assignment, item, owner_stack))
    roles = {role["id"]: role.get("profile") for role in stack.get("roles", [])}
    for assignment, item, owner_stack in owned_assignments:
        role_id = assignment.get("role_id")
        task_id = assignment.get("bound_task_id", assignment.get("task_id"))
        profile = item.get("profile", roles.get(role_id))
        if (not task_id or profile != "coder" or (owner_stack == reference["stack_id"] and role_id == reference["role_id"])
                or assignment.get("stack_id") != owner_stack):
            continue
        actual = item.get("task", {})
        if (actual.get("id") != task_id or actual.get("status", {}).get("state", "").upper()
                not in ("COMPLETED", "TASK_STATE_COMPLETED") or not actual.get("artifacts")):
            continue
        paths = [(workspace / name).resolve() for name in assignment.get("write_paths", [])]
        contributed = {name for name in changed if any((workspace / name).resolve() == p
            or within(workspace / name, p) for p in paths)}
        if contributed:
            covered.update(contributed)
            receipts.append({"stack_id": owner_stack, "role_id": role_id, "task_id": task_id, "files": sorted(contributed)})
    if changed - covered:
        raise ValueError("Changed candidate lacks completed bound coder provenance: " + ", ".join(sorted(changed - covered)))
    return receipts


def validate_review(spec, reference, manifest, task, stack):
    if stack.get("goal_id") != spec["id"]:
        raise ValueError("Review stack belongs to another goal")
    if task.get("id") != reference["task_id"]:
        raise ValueError("Review task identity mismatch")
    state = task.get("status", {}).get("state", "").upper()
    if state not in ("COMPLETED", "TASK_STATE_COMPLETED"):
        raise ValueError("Review task not completed: " + state)
    role = next((r for r in stack.get("roles", []) if r["id"] == reference["role_id"]), None)
    if not role or role.get("profile") != "reviewer" or stack.get("stack_id") != reference["stack_id"]:
        raise ValueError("Independent reviewer role required")
    assignments = bound_assignments(spec, reference["stack_id"])
    producers = producer_receipts(spec, reference, manifest, stack, assignments)
    matches = []
    for assignment in assignments:
        if assignment.get("bound_task_id", assignment.get("task_id")) == reference["task_id"] and assignment.get("role_id") == reference["role_id"]:
            matches.append(assignment)
    if len(matches) != 1:
        raise ValueError("Actual bound review assignment missing or ambiguous")
    assignment = matches[0]
    if (assignment.get("stack_id") != reference["stack_id"]
            or assignment.get("candidate") != manifest["candidate"] or assignment.get("write_paths") != []
            or not set(spec["acceptance"]).issubset(assignment.get("acceptance", []))):
        raise ValueError("Review assignment does not cover immutable acceptance/candidate")
    for artifact in review_artifacts(task):
        if (artifact.get("candidate") == manifest["candidate"] and artifact.get("verdict") == "READY"
                and isinstance(artifact.get("evidence"), list) and artifact["evidence"]
                and all(isinstance(item, str) and item.strip() for item in artifact["evidence"])):
            author = ",".join(item["stack_id"] + "/" + item["role_id"] + "/" + item["task_id"] for item in producers) or "baseline:" + spec["id"]
            receipt = review_helpers.accept(manifest, {**artifact,
                "reviewer": reference["role_id"] + "/" + reference["task_id"], "author": author})
            return {**receipt, "producers": producers, "author": author}
    raise ValueError("Actual task has no candidate-bound READY evidence")


def verified_auth(observation):
    return (isinstance(observation, dict) and observation.get("source") == "native_metadata"
        and observation.get("terminal") is True and (observation.get("http_status") in (401, 403)
        or observation.get("error_category") in ("authentication_required", "account_on_hold", "billing_error")))


def external_blocker(proposal, diagnosis, spec=None, observations=None):
    blocker = proposal.get("blocker") or {}
    def evidence(value):
        return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)
    if not (diagnosis.get("classification") == "external_dependency"
            and bool(blocker.get("message")) and evidence(blocker.get("evidence"))
            and evidence(diagnosis.get("evidence"))):
        return False
    spec = spec or {}
    kind = blocker.get("kind")
    if kind == "credentials":
        return verified_auth((observations or {}).get("owner"))
    if kind in ("missing_authority", "irreversible_owner_decision"):
        return bool(blocker.get("gate")) and blocker["gate"] in spec.get("user_gates", [])
    if kind == "missing_external_input":
        path = blocker.get("input_path")
        return (isinstance(path, str) and Path(path).is_absolute() and path in spec.get("required_inputs", [])
            and path in blocker["evidence"] and not Path(path).exists())
    return False


def run_goal(spec, journal, backend, pause=time.sleep):
    feedback = json.dumps({"resume_state": journal.state})
    while True:
        proposal = {}
        try:
            journal.cancel_check()
            journal.record("owner_turn", status="RUNNING")
            proposal = backend.owner(feedback)
            if isinstance(proposal.get("summary"), str):
                journal.record("owner_summary", last_summary=runtime._safe_handoff(proposal["summary"]))
            if proposal.get("status") not in ("complete", "continue", "needs_user"):
                raise ValueError("Invalid owner structured status; return required JSON schema")
            if proposal["status"] == "continue":
                feedback = json.dumps({"previous": proposal, "instruction": "Continue original goal from actual task states; do not duplicate active assignments."})
                continue
            if proposal["status"] == "needs_user":
                raise ValueError("Owner proposed blocker; independent classification required")
            reference = proposal["review"]
            if not isinstance(reference, dict):
                raise ValueError("Candidate review reference required")
            ticket = backend.prepare_completion(proposal)
            manifest = freeze_current(spec, journal.directory, proposal["candidate_manifest"])
            task, stack = backend.fetch_review(reference)
            receipt = validate_review(spec, reference, manifest, task, stack)
            journal.record("review_verified", checked_candidate=manifest, review={**reference, **receipt})
            checks = []
            for check in spec["checks"]:
                journal.cancel_check()
                result = backend.check(check)
                result = {"id": check["id"], **result}
                checks.append(result)
                runtime.atomic_json(journal.directory / "checks.json", checks)
                journal.record("check_finished", checks=checks)
                if result["exit_code"] != 0:
                    raise ValueError("Check failed: " + json.dumps(result))
            if freeze_current(spec, journal.directory, proposal["candidate_manifest"]) != manifest:
                raise ValueError("Candidate changed during checks")
            journal.cancel_check()
            committed = backend.commit_completion(proposal, ticket, checks)
            state = committed.get("state", {})
            if (committed.get("status") != "complete" or state.get("status") != "COMPLETE"
                    or state.get("id") != spec["id"] or (state.get("accepted_receipt") or {}).get("accepted") is not True):
                raise ValueError("Host did not durably accept this Goal")
            journal.state = state
            return 0
        except Canceled:
            journal.record("canceled", status="CANCELED")
            return 0
        except Exception as exc:
            error = runtime._safe_handoff(f"{type(exc).__name__}: {exc}")
            journal.record("recovering", status="RECOVERING", last_error=error,
                           recovery_count=journal.state["recovery_count"] + 1)
            if isinstance(exc, InfrastructureUnavailable):
                # The native owner process has ended; A2A workers are untouched.
                # Re-enter SDK preflight and resume this same goal/session.
                feedback = json.dumps({"infrastructure_recovery": error, "state": journal.state,
                    "instruction": "Resume original goal from persisted task bindings; reconcile active workers before assigning."})
                journal.record("infrastructure_reconnect", status="RECOVERING",
                    infrastructure_reconnect_at=runtime.now())
                continue
            if (isinstance(exc, NativeFailure) and exc.channel == "owner"
                    and exc.diagnostic.get("error_category") in RESET_CATEGORIES):
                reset_owner_session(journal, exc.diagnostic["error_category"])
            facts = {"error": error, "state": journal.state, "proposal": proposal}
            try:
                diagnosis = backend.supervisor(facts)
                if diagnosis.get("recovery_action") == "reset_session":
                    reset_owner_session(journal, "independent_supervisor_recovery")
                if proposal.get("status") == "needs_user" and external_blocker(proposal, diagnosis, spec, journal.state.get("native_failures")):
                    journal.record("external_dependency", status="NEEDS_USER", blocker=proposal["blocker"], diagnosis=diagnosis)
                    return 0
                feedback = json.dumps({**facts, "supervisor": diagnosis, "instruction": "Repair the causal failure, reconcile active work, and continue the SAME goal and session."})
            except Canceled:
                journal.record("canceled", status="CANCELED")
                return 0
            except Exception as supervisor_error:
                observations = journal.state.get("native_failures", {})
                if verified_auth(observations.get("owner")) and verified_auth(observations.get("supervisor")):
                    journal.record("verified_native_auth_blocker", status="NEEDS_USER", blocker={
                        "kind": "credentials", "message": "Owner and independent supervisor native contexts require account action.",
                        "evidence": ["Verified terminal native authentication metadata in both contexts"]}, native_failures=observations)
                    return 0
                feedback = json.dumps({**facts, "supervisor_error": runtime._safe_handoff(str(supervisor_error))})
                journal.record("supervisor_recovering", last_error=error + "; supervisor: " + runtime._safe_handoff(str(supervisor_error)))
            pause(.2)  # Responsive recovery pacing, never an iteration or duration cap.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.spec.is_absolute() or not args.state_dir.is_absolute():
        parser.error("spec and state-dir must be absolute")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    journal = Journal(args.state_dir, spec)
    if journal.state["status"] in ("COMPLETE", "CANCELED", "NEEDS_USER"):
        return 0
    try:
        return run_goal(spec, journal, NativeBackend(spec, journal))
    except Exception as exc:
        journal.record("runner_recovering", status="RECOVERING", last_error=runtime._safe_handoff(str(exc)))
        return 1  # Host relaunches the same immutable goal and persisted native session.


if __name__ == "__main__":
    raise SystemExit(main())
