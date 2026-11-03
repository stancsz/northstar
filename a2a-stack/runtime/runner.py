"""Small Windows-only, single-owner project workflow broker."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

if os.name == "nt":
    import msvcrt
    from ctypes import wintypes

STACK_ROOT = Path(__file__).resolve().parents[1]
NORTHSTAR_ROOT = STACK_ROOT.parent
ROOT = Path(os.environ.get("A2A_WORKSPACE", NORTHSTAR_ROOT)).resolve()
STATE_ROOT = NORTHSTAR_ROOT / "tmp" / "a2a-stack"
_TEST_CONTROL = os.environ.get("A2A_TEST_CONTROL_DIR")
if _TEST_CONTROL:
    CONTROL = Path(_TEST_CONTROL).resolve()
    if not CONTROL.is_relative_to((STATE_ROOT / "runtime-tests").resolve()):
        raise RuntimeError("A2A_TEST_CONTROL_DIR must be under tmp/a2a-stack/runtime-tests")
else:
    CONTROL = STATE_ROOT / "control"
STATE = CONTROL / "status.json"
LOCK = CONTROL / "owner.lock"
RUNS = (STATE_ROOT / "runtime-tests" / "runs") if _TEST_CONTROL else (STATE_ROOT / "runs")
POLL = 0.2


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    deadline = time.monotonic() + 1.0
    try:
        while True:
            try:
                os.replace(temp, path)
                return
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.025)
    finally:
        temp.unlink(missing_ok=True)


def process_token(pid: int):
    """Return a process creation FILETIME token; None if the PID is absent."""
    if os.name != "nt":
        return None
    k = ctypes.windll.kernel32
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    k.GetProcessTimes.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    h = k.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not h:
        return None
    class FT(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]
    created, exited, kernel, user = FT(), FT(), FT(), FT()
    try:
        if not k.GetProcessTimes(h, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        return f"{created.hi:08x}{created.lo:08x}"
    finally:
        k.CloseHandle(h)


class Job:
    """Kill-on-close Windows Job Object owned by broker process."""
    def __init__(self):
        k = ctypes.windll.kernel32
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        self.k = k
        self.handle = k.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError()
        class BasicLimit(ctypes.Structure):
            _fields_ = [("per_process", ctypes.c_longlong), ("per_job", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                        ("active", wintypes.DWORD), ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("sched", wintypes.DWORD)]
        class IoCounters(ctypes.Structure):
            _fields_ = [(x, ctypes.c_ulonglong) for x in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class ExtLimit(ctypes.Structure):
            _fields_ = [("basic", BasicLimit), ("io", IoCounters), ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        info = ExtLimit()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            k.CloseHandle(self.handle)
            raise ctypes.WinError()

    def assign(self, proc):
        if not self.k.AssignProcessToJobObject(self.handle, int(proc._handle)):
            proc.kill()
            raise ctypes.WinError()
        # Children must not execute until the Job Object owns their process handle.
        status = ctypes.windll.ntdll.NtResumeProcess
        status.argtypes = [wintypes.HANDLE]
        status.restype = ctypes.c_long
        result = status(int(proc._handle))
        if result < 0:
            self.k.TerminateJobObject(self.handle, 1)
            raise OSError(f"NtResumeProcess failed: 0x{result & 0xffffffff:08x}")

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None


def structured_abort(line: str):
    """Recognize actual stream event metadata, never incidental quoted text."""
    try:
        event = json.loads(line)
    except (ValueError, TypeError):
        return None
    if not isinstance(event, dict):
        return None
    typ = str(event.get("type", "")).lower()
    subtype = str(event.get("subtype", "")).lower()
    if (typ == "system" and subtype == "api_retry") or typ == "api_retry":
        # This is native transport recovery, not a terminal job result.
        return None
    if typ != "result":
        return None
    error = event.get("error")
    if isinstance(error, dict):
        code = str(error.get("code", "")).lower()
        if code == "unrecognized_model" or (code == "429" and typ == "result"):
            return code
    for key in ("status_code", "http_status", "code"):
        code = str(event.get(key, "")).lower()
        if code == "unrecognized_model" or (code == "429" and typ == "result"):
            return code
    # Claude emits execution failures as result events; require the native
    # error subtype/flag and an anchored canonical API error code.
    if typ == "result" and subtype == "error_during_execution" and event.get("is_error") is True:
        message = event.get("result")
        if isinstance(message, str):
            match = re.match(r"^API error:\s*(429|unrecognized_model)(?:\b|$)", message, re.IGNORECASE)
            if match:
                return match.group(1).lower()
    return None


def claude_executable(configured=None):
    if configured:
        return configured
    found = shutil.which("claude.exe")
    if found:
        return found
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidate = Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError("Claude CLI executable not found; pass --claude with its installed executable path")


def _safe_handoff(value):
    value = str(value)
    value = re.sub(r"(?i)\b(?:sk-ant-|sk-proj-|sk_|ghp_|github_pat_)[A-Za-z0-9_-]{8,}\b", "[REDACTED_TOKEN]", value)
    value = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED_EMAIL]", value, flags=re.I)
    value = re.sub(r'''(?i)(['"]?[\w.-]*(?:api[_ -]?key|token|password|secret)[\w.-]*['"]?\s*[:=]\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;}\]]+)''',
                   lambda match: match[1] + (match[2][0] + '[REDACTED]' + match[2][-1]
                       if match[2][0] in ('"', "'") and match[2][-1] == match[2][0] else '[REDACTED]'), value)
    value = re.sub(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED_TOKEN]", value)
    # Keep the whole sanitized result: truncation dropped real acceptance/handoff
    # evidence (including the trailing handoff marker) from otherwise successful jobs.
    return value


def sanitized_event(line: str):
    try:
        event = json.loads(line)
    except (ValueError, TypeError):
        return {"type": "unparsed", "characters": len(line)}
    if not isinstance(event, dict):
        return {"type": "non_object"}
    safe = {key: event[key] for key in ("type", "subtype", "is_error", "num_turns", "duration_ms", "duration_api_ms") if key in event}
    if event.get("type") == "system" and event.get("subtype") == "api_retry":
        for key in ("attempt", "max_retries", "retry_delay_ms", "error_status"):
            value = event.get(key)
            if value is None or (isinstance(value, int) and not isinstance(value, bool)):
                safe[key] = value
    error = event.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, (str, int)) and str(code).lower() in ("429", "unrecognized_model"):
            safe["error_code"] = str(code).lower()
    contents = event.get("content", [])
    message = event.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), list):
        contents = message["content"]
    for content in contents if isinstance(contents, list) else []:
        if isinstance(content, dict) and content.get("type") == "tool_use":
            safe.setdefault("tools", []).append({k: content[k] for k in ("name", "id") if isinstance(content.get(k), str)})
        elif isinstance(content, dict) and content.get("type") == "tool_result":
            safe.setdefault("tool_results", []).append({
                "tool_use_id": content.get("tool_use_id") if isinstance(content.get("tool_use_id"), str) else None,
                "is_error": content.get("is_error") is True,
            })
    if event.get("type") == "result" and isinstance(event.get("result"), str):
        safe["handoff"] = _safe_handoff(event["result"])
    return safe


def write_event(stream, kind, line):
    abort = structured_abort(line)
    event = sanitized_event(line)
    stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    stream.flush()
    return abort


def claude_command(executable, prompt, allowed=None, max_turns=None):
    command = [executable, "-p", "--output-format", "stream-json", "--verbose"]
    if max_turns is not None:
        command += ["--max-turns", str(max_turns)]
    if allowed:
        command += ["--allowedTools", ",".join(allowed)]
    command += ["--", prompt]
    return command


def broker(run_id, kind, command, prompt_file=None, timeout=None, max_turns=None, allowed=None, acquire_lock=True):
    CONTROL.mkdir(parents=True, exist_ok=True)
    lock_file = None
    if acquire_lock:
        lock_file = open(LOCK, "a+b")
        try:
            lock_file.seek(0)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print("another workflow owner holds the project lock", file=sys.stderr)
            return 3
    token = process_token(os.getpid())
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = run_dir / "stdout.jsonl", run_dir / "stderr.log"
    deadline = time.monotonic() + timeout if timeout is not None else None
    state = {"run_id": run_id, "pid": os.getpid(), "process_token": token, "root": str(ROOT), "kind": kind,
             "started_at": now(), "heartbeat_at": now(), "deadline_epoch": deadline, "status": "starting",
             "stdout": str(stdout_path), "stderr": str(stderr_path)}
    state_path = STATE if acquire_lock else CONTROL / f"worker-{run_id}.json"
    atomic_json(state_path, state)
    job = Job()
    proc = None
    reason = None
    code = None
    try:
        cmd = list(command)
        if kind == "claude":
            cmd = claude_command(cmd[0], Path(prompt_file).read_text(encoding="utf-8"), allowed, max_turns)
        env = os.environ.copy()
        creation = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 0x00000004  # CREATE_SUSPENDED
        proc = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                bufsize=1, creationflags=creation, env=env)
        job.assign(proc)
        state.update(status="running", child_pid=proc.pid, child_token=process_token(proc.pid), command=cmd[:1] if kind == "claude" else cmd)
        atomic_json(state_path, state)
        import threading
        abort_box = []
        def pump(pipe, path, channel):
            if channel == "stdout":
                with open(path, "w", encoding="utf-8") as out:
                    for line in iter(pipe.readline, ""):
                        abort = write_event(out, channel, line)
                        if abort and not abort_box:
                            abort_box.append(abort)
            else:
                count = sum(1 for _ in iter(pipe.readline, ""))
                atomic_json(Path(path), {"stderr_lines": count, "content": "omitted"})
            pipe.close()
        threads = [threading.Thread(target=pump, args=(proc.stdout, stdout_path, "stdout"), daemon=True),
                   threading.Thread(target=pump, args=(proc.stderr, stderr_path, "stderr"), daemon=True)]
        for thread in threads: thread.start()
        while proc.poll() is None:
            if (CONTROL / "stop.request").exists():
                reason = "stop_requested"
                job.close()
                break
            if abort_box:
                reason = abort_box[0]
                job.close()
                break
            if deadline is not None and time.monotonic() >= deadline:
                reason = "timeout"
                job.close()
                break
            state["heartbeat_at"] = now(); atomic_json(state_path, state)
            time.sleep(POLL)
        if proc.poll() is not None:
            code = proc.returncode
        for thread in threads: thread.join(timeout=2)
        if proc.poll() is None:
            proc.wait(timeout=5)
        code = proc.returncode
    except Exception as exc:
        reason = f"broker_error: {type(exc).__name__}: {exc}"
        if proc and proc.poll() is None: job.close()
    finally:
        job.close()
        state.update(status="finished", finished_at=now(), exit_code=code, stop_reason=reason)
        atomic_json(state_path, state)
        if lock_file:
            try: msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError: pass
            lock_file.close()
    return 0 if code == 0 and reason is None else 1


def live_status():
    try: state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError): return {"status": "stopped"}
    token = process_token(int(state.get("pid", 0)))
    if token is None or token != state.get("process_token"):
        return {**state, "status": "stale"}
    # The OS lock is authoritative; an extant PID alone is not ownership.
    f = open(LOCK, "a+b")
    try:
        f.seek(0)
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return {**state, "status": "stale"}
        except OSError:
            if state.get("current_worker"):
                worker_file = CONTROL / f"worker-{state['current_worker']['run_id']}.json"
                try:
                    worker = json.loads(worker_file.read_text(encoding="utf-8"))
                    if worker.get("pid") == state.get("pid") and worker.get("process_token") == state.get("process_token"):
                        state["active_worker"] = worker
                except (OSError, ValueError):
                    pass
            return state
    finally: f.close()


def owner_lock_held():
    f = open(LOCK, "a+b")
    try:
        f.seek(0)
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            return False
        except OSError:
            return True
    finally: f.close()


def argument_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action", required=True)
    sub.add_parser("start")
    sub.add_parser("serve")
    sub.add_parser("status")
    stop = sub.add_parser("stop"); stop.add_argument("--wait", type=float, default=20)
    run = sub.add_parser("run"); run.add_argument("--prompt-file", required=True); run.add_argument("--claude"); run.add_argument("--timeout", type=int); run.add_argument("--max-turns", type=int); run.add_argument("--allowed-tools", default="Read,Edit,Write,Bash")
    ex = sub.add_parser("exec"); ex.add_argument("--timeout", type=int); ex.add_argument("command", nargs=argparse.REMAINDER)
    return p


def main():
    if os.name != "nt":
        print("runner requires Windows", file=sys.stderr); return 2
    p = argument_parser()
    a = p.parse_args()
    if a.action == "status": print(json.dumps(live_status(), indent=2)); return 0
    if a.action in ("start", "serve"):
        existing = live_status()
        if existing.get("status") in ("starting", "running"):
            print(json.dumps(existing), flush=True)
            return 0
        end = time.time() + 10
        CONTROL.mkdir(parents=True, exist_ok=True)
        while owner_lock_held() and time.time() < end: time.sleep(.1)
        if owner_lock_held():
            print("owner lock remains held by a live or unresponsive process", file=sys.stderr); return 1
        # Keep this foreground process in the host's tracked session. Detached
        # children may be reclaimed when a Codex shell invocation exits.
        class Args: pass
        args = Args(); args.run_id = uuid.uuid4().hex
        return idle_broker(args)
    if a.action == "stop":
        state = live_status()
        if state.get("status") not in ("running", "starting"):
            print(json.dumps(state)); return 0
        pid = int(state["pid"])
        # Graceful stop is delivered by the broker control marker and observed by lifecycle loop.
        (CONTROL / "stop.request").write_text(state["run_id"], encoding="ascii")
        end = time.time() + a.wait
        while time.time() < end:
            if live_status().get("status") not in ("running", "starting") and not owner_lock_held(): return 0
            time.sleep(.2)
        print(f"owner PID {pid} did not stop; no unrelated process was terminated", file=sys.stderr); return 1
    if a.action == "run":
        tools = [x for x in a.allowed_tools.split(",") if x]
        return submit({"kind":"claude", "command":[claude_executable(a.claude)], "prompt_file":a.prompt_file, "timeout":a.timeout, "max_turns":a.max_turns, "allowed":tools})
    if a.action == "exec":
        command = a.command[1:] if a.command and a.command[0] == "--" else a.command
        if not command: p.error("exec requires -- <executable> [args...]")
        return submit({"kind":"exec", "command":command, "timeout":a.timeout})
    if a.action == "_broker":
        # Internal idle owner used to establish a persistent cross-shell lock.
        return idle_broker(a)
    return 2


def idle_broker(a):
    CONTROL.mkdir(parents=True, exist_ok=True)
    f = open(LOCK, "a+b"); f.seek(0)
    try: msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError: return 3
    (CONTROL / "stop.request").unlink(missing_ok=True)
    token = process_token(os.getpid())
    state = {"run_id": a.run_id, "pid": os.getpid(), "process_token": token,
             "root": str(ROOT), "kind": "idle", "started_at": now(), "heartbeat_at": now(), "status": "running"}
    atomic_json(STATE, state)
    print(json.dumps(state), flush=True)
    try:
        while not (CONTROL / "stop.request").exists():
            requests = sorted(CONTROL.glob("request-*.json"))
            if requests:
                reqfile = requests[0]
                try:
                    req = json.loads(reqfile.read_text(encoding="utf-8"))
                    state["current_worker"] = {"run_id": req["run_id"], "kind": req["kind"], "started_at": now()}
                    state["heartbeat_at"] = now(); atomic_json(STATE, state)
                    rc = broker(req["run_id"], req["kind"], req["command"], req.get("prompt_file"), req.get("timeout"), req.get("max_turns"), req.get("allowed"), acquire_lock=False)
                    try: state["last_worker"] = json.loads((CONTROL / f"worker-{req['run_id']}.json").read_text(encoding="utf-8"))
                    except (OSError, ValueError): pass
                    state.pop("current_worker", None)
                    (CONTROL / f"result-{req['run_id']}.json").write_text(json.dumps({"exit_code":rc}), encoding="utf-8")
                except Exception as exc:
                    (CONTROL / f"result-{req.get('run_id','bad')}.json").write_text(json.dumps({"error":str(exc)}), encoding="utf-8")
                reqfile.unlink(missing_ok=True)
                state.update(status="running", heartbeat_at=now()); atomic_json(STATE, state)
            state["heartbeat_at"] = now(); atomic_json(STATE, state); time.sleep(.2)
        (CONTROL / "stop.request").unlink(missing_ok=True)
        state.update(status="finished", finished_at=now()); atomic_json(STATE, state)
    finally:
        try: msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError: pass
        f.close()
    return 0


def submit(spec):
    state = live_status()
    if state.get("status") not in ("running", "starting"):
        print("no live project broker; start it first", file=sys.stderr); return 3
    run_id = uuid.uuid4().hex
    spec["run_id"] = run_id
    req = CONTROL / f"request-{run_id}.json"
    atomic_json(req, spec)
    result = CONTROL / f"result-{run_id}.json"
    timeout = spec.get("timeout")
    deadline = time.monotonic() + int(timeout) + 30 if timeout is not None else None
    while deadline is None or time.monotonic() < deadline:
        if result.exists():
            try: data = json.loads(result.read_text(encoding="utf-8"))
            finally: result.unlink(missing_ok=True)
            if "error" in data: print(data["error"], file=sys.stderr); return 1
            return int(data["exit_code"])
        if live_status().get("status") not in ("running", "starting"):
            break
        time.sleep(.2)
    print(f"broker ended or request timed out; inspect {req}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    # Internal broker args are parsed separately because public subcommands stay small.
    if len(sys.argv) > 1 and sys.argv[1] == "_broker":
        class Args: pass
        args = Args(); args.run_id = sys.argv[2]
        raise SystemExit(idle_broker(args))
    raise SystemExit(main())
