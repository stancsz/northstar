"""Interval scheduler for trusted delivery and supervisor jobs on an A2A MCP gateway."""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import signal
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from mcp.client import Client

STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
MCP_URL = os.environ.get("MCP_URL", "http://mcp-gateway:18892/mcp")
TERMINAL = {"TASK_STATE_COMPLETED", "TASK_STATE_FAILED", "TASK_STATE_CANCELED", "TASK_STATE_REJECTED"}
ACTIVE = {"TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"}
ROLE_LOCKS: dict[str, asyncio.Lock] = {}
ACTIVE_TASKS: set[asyncio.Task] = set()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_state(role: str) -> dict:
    path = STATE_DIR / f"{role}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Persisted role state is unreadable; reconciliation required") from exc
    if not isinstance(value, dict):
        raise ValueError("Persisted role state is not an object; reconciliation required")
    phase = value.get("phase")
    if phase not in {"submitting", "running", "terminal", "NEEDS_RECONCILIATION"}:
        raise ValueError("Persisted role phase is invalid; reconciliation required")
    if not isinstance(value.get("job_name"), str) or not value["job_name"]:
        raise ValueError("Persisted job name is invalid; reconciliation required")
    completed_jobs = value.get("completed_jobs", [])
    if not isinstance(completed_jobs, list) or any(not isinstance(name, str) or not name for name in completed_jobs):
        raise ValueError("Persisted completed-job history is invalid; reconciliation required")
    task_id = value.get("task_id")
    if task_id is not None and (not isinstance(task_id, str) or not task_id):
        raise ValueError("Persisted task ID is invalid; reconciliation required")
    if phase in {"running", "terminal"}:
        expected = ACTIVE if phase == "running" else TERMINAL
        if not task_id or not isinstance(value.get("job_name"), str) or value.get("status") not in expected:
            raise ValueError("Persisted task state is inconsistent; reconciliation required")
    if phase == "NEEDS_RECONCILIATION" and value.get("status") != "UNKNOWN":
        raise ValueError("Persisted reconciliation state is inconsistent")
    if phase == "submitting" and task_id:
        raise ValueError("Submitting state unexpectedly has a task ID; reconciliation required")
    return value


def save_state(role: str, state: dict) -> None:
    state["updated_at"] = utc_now()
    atomic_json(STATE_DIR / f"{role}.json", state)


def event(role: str, job_name: str, task_id: str | None, phase: str, status: str | None = None) -> None:
    record = {"at": utc_now(), "role": role, "job": job_name, "task_id": task_id,
              "phase": phase, "status": status}
    data = (json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(STATE_DIR / "events.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def decode(result):
    if result.is_error:
        raise RuntimeError("MCP tool returned an error")
    if result.structured_content is not None:
        return result.structured_content
    if not result.content or not getattr(result.content[0], "text", None):
        raise ValueError("MCP tool returned no structured payload")
    return json.loads(result.content[0].text)


def task_parts(value: dict) -> tuple[dict, str | None, str]:
    task = value.get("task", value)
    if not isinstance(task, dict):
        raise ValueError("A2A task payload is not an object")
    task_id = task.get("id")
    status_obj = task.get("status")
    status = status_obj.get("state") if isinstance(status_obj, dict) else None
    return task, task_id if isinstance(task_id, str) else None, status if isinstance(status, str) else ""


def result_summary(task: dict, task_id: str, status: str) -> dict:
    names = []
    artifacts = task.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
    for artifact in artifacts:
        if isinstance(artifact, dict) and isinstance(artifact.get("name"), str):
            names.append(artifact["name"][:160])
    return {"task_id": task_id, "status": status, "artifact_count": len(artifacts),
            "artifact_names": names[:20]}


def remember_delivery_terminal(state: dict, task: dict, task_id: str, status: str) -> None:
    """Persist the terminal task and consume this registered delivery-job name once."""
    job_name = state["job_name"]
    completed = state.setdefault("completed_jobs", [])
    if job_name not in completed:
        completed.append(job_name)
    state["last_result"] = {**result_summary(task, task_id, status), "job_name": job_name}


async def tick(role: str, configured_job: str) -> None:
    task = asyncio.current_task()
    if task is not None:
        ACTIVE_TASKS.add(task)
    try:
        await _tick(role, configured_job)
    finally:
        if task is not None:
            ACTIVE_TASKS.discard(task)


async def _tick(role: str, configured_job: str) -> None:
    lock = ROLE_LOCKS.setdefault(role, asyncio.Lock())
    async with lock:
        try:
            state = read_state(role)
        except ValueError:
            # Preserve the unreadable bytes; overwriting might erase evidence of an accepted task.
            event(role, configured_job, None, "NEEDS_RECONCILIATION", "UNKNOWN")
            return
        event(role, configured_job, state.get("task_id"), "triggered", state.get("status"))

        # A delivery job name represents one explicitly assigned increment. Its terminal
        # receipt is durable; repeated timer ticks only wake its owner until the name changes.
        if role == "delivery" and state.get("phase") == "terminal":
            completed = state.setdefault("completed_jobs", [])
            if state["job_name"] not in completed:
                completed.append(state["job_name"])
            if configured_job in state["completed_jobs"]:
                save_state(role, state)
                event(role, configured_job, state["task_id"], "terminal", state["status"])
                return

        # A durable submitting marker with no ID means the submit response may have been lost.
        if state.get("phase") == "submitting" and not state.get("task_id"):
            state["phase"] = "NEEDS_RECONCILIATION"
            state["status"] = "UNKNOWN"
            save_state(role, state)
            event(role, state.get("job_name", configured_job), None, state["phase"], state["status"])
            return

        old_id = state.get("task_id")
        if old_id:
            try:
                async with Client(MCP_URL) as client:
                    task, returned_id, status = task_parts(decode(await client.call_tool("get_task", {"task_id": old_id})))
            except Exception:
                state.update(phase="NEEDS_RECONCILIATION", status="UNKNOWN")
                save_state(role, state)
                event(role, state.get("job_name", configured_job), old_id, state["phase"], state["status"])
                return
            if returned_id != old_id or status not in ACTIVE | TERMINAL:
                state.update(phase="NEEDS_RECONCILIATION", status="UNKNOWN")
                save_state(role, state)
                event(role, state.get("job_name", configured_job), old_id, state["phase"], state["status"])
                return
            if status in ACTIVE or state.get("phase") != "terminal":
                state.update(task_id=old_id, status=status, phase="running" if status in ACTIVE else "terminal")
                if status in TERMINAL:
                    if role == "delivery":
                        remember_delivery_terminal(state, task, old_id, status)
                    else:
                        state["last_result"] = result_summary(task, old_id, status)
                save_state(role, state)
                event(role, state.get("job_name", configured_job), old_id, state["phase"], status)
                return
            # The prior scheduled tick already recorded this terminal result. Querying the same
            # ID succeeded again, so a later interval may now submit configured work.
            if role == "delivery":
                remember_delivery_terminal(state, task, old_id, status)
            else:
                state["last_result"] = result_summary(task, old_id, status)
            state["previous_job_name"] = state.get("job_name")
            state["task_id"] = None
            state["status"] = status
            state["phase"] = "idle"

        if state.get("phase") == "NEEDS_RECONCILIATION":
            save_state(role, state)
            event(role, state.get("job_name", configured_job), state.get("task_id"), state["phase"], state.get("status"))
            return

        # No task ID is safe to submit only when there was no ambiguous prior submission.
        state.update(job_name=configured_job, task_id=None, status="UNKNOWN", phase="submitting")
        save_state(role, state)
        event(role, configured_job, None, "submitting")
        submitted_id = None
        try:
            async with Client(MCP_URL) as client:
                submitted = decode(await client.call_tool("submit_job", {"job_name": configured_job}))
            task, submitted_id, status = task_parts(submitted)
            if not submitted_id or status not in ACTIVE | TERMINAL:
                raise ValueError("Submit response lacks a recognized task ID/status")
        except Exception:
            state.update(task_id=submitted_id, phase="NEEDS_RECONCILIATION", status="UNKNOWN")
            save_state(role, state)
            event(role, configured_job, submitted_id, state["phase"], state["status"])
            return
        state.update(task_id=submitted_id, status=status, phase="running" if status in ACTIVE else "terminal")
        if status in TERMINAL:
            if role == "delivery":
                remember_delivery_terminal(state, task, submitted_id, status)
            else:
                state["last_result"] = result_summary(task, submitted_id, status)
        save_state(role, state)
        event(role, configured_job, submitted_id, state["phase"], status)


def interval(name: str, default: int) -> float:
    value = float(os.environ.get(name, str(default)))
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


async def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    scheduler = AsyncIOScheduler(timezone=timezone.utc)
    roles = [
        ("delivery", os.environ.get("DELIVERY_JOB", "").strip(), interval("DELIVERY_INTERVAL_SECONDS", 3600)),
        ("supervisor", os.environ.get("SUPERVISOR_JOB", "").strip(), interval("SUPERVISOR_INTERVAL_SECONDS", 1800)),
    ]
    for role, job_name, seconds in roles:
        if job_name:
            scheduler.add_job(tick, "interval", seconds=seconds, id=role, args=[role, job_name],
                              max_instances=1, coalesce=True, misfire_grace_time=None)

    loop = asyncio.get_running_loop()
    stopping = asyncio.Event()
    def request_stop() -> None:
        stopping.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: loop.call_soon_threadsafe(request_stop))

    # IntervalTrigger's first occurrence is one interval after registration; no startup dispatch.
    scheduler.start()
    await stopping.wait()
    scheduler.pause()
    await asyncio.sleep(0)
    # Let already-started network transitions finish; their task IDs were persisted before submit.
    current = asyncio.current_task()
    active = {task for task in ACTIVE_TASKS if task is not current and not task.done()}
    if active:
        await asyncio.gather(*active, return_exceptions=True)
    scheduler.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
