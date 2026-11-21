"""Read Codex subscription metadata and quota windows via App Server."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import tomllib
from pathlib import Path


class CodexError(RuntimeError):
    pass


def cli_command() -> list[str]:
    binary = shutil.which("codex")
    if not binary:
        raise CodexError("codex is required on PATH.")
    path = Path(binary)
    if path.suffix.lower() in {".cmd", ".bat"}:
        script = path.parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        if script.is_file() and shutil.which("node"):
            return [shutil.which("node"), str(script)]
    return [binary]


def host_overrides() -> list[str]:
    args = ["--config", 'web_search="disabled"', "--config", "project_doc_max_bytes=0",
            "--config", "mcp_servers={}"]
    for feature in ("multi_agent", "multi_agent_v2", "hooks", "memories", "apps", "plugins", "shell_tool",
                    "unified_exec", "tool_suggest"):
        args.extend(("--disable", feature))
    config = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "config.toml"
    if config.is_file():
        with config.open("rb") as stream:
            mcp = tomllib.load(stream).get("mcp_servers", {})
        for name in mcp:
            if not re.fullmatch(r"[\w-]+", name, flags=re.ASCII):
                raise CodexError("Cannot safely override a nonstandard MCP server name.")
            args.extend(("--config", f"mcp_servers.{name}.enabled=false"))
    return args


class CodexServer:
    def __init__(self, cwd: Path):
        self.cwd = cwd.resolve()
        self.process = None
        self.log = None
        self.incoming = queue.Queue()
        self.sequence = 0

    def __enter__(self):
        self.cwd.mkdir(parents=True, exist_ok=True)
        self.log = (self.cwd / "app-server.stderr.log").open("w", encoding="utf-8")
        try:
            self.process = subprocess.Popen(
                [*cli_command(), "app-server", *host_overrides(), "--listen", "stdio://"],
                cwd=self.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                encoding="utf-8", errors="replace", bufsize=1,
            )
            threading.Thread(target=self._read_stdout, daemon=True).start()
            self.call("initialize", {
                "clientInfo": {"name": "spot-advisor-eval", "version": "2.0.0"},
                "capabilities": {"experimentalApi": True},
            })
            self._send({"method": "initialized"})
            config = self.call("config/read").get("config") or {}
            if any(server.get("enabled", True) for server in (config.get("mcp_servers") or {}).values()):
                raise CodexError("An inherited MCP server is enabled in the evaluation client.")
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        if self.process is not None:
            if self.process.stdin is not None:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            if self.process.stdout is not None:
                self.process.stdout.close()
        if self.log is not None:
            self.log.close()

    def _read_stdout(self) -> None:
        try:
            for line in self.process.stdout:
                self.incoming.put(json.loads(line))
        except (OSError, ValueError) as exc:
            self.incoming.put(CodexError(f"Invalid app-server stream: {type(exc).__name__}"))
        finally:
            self.incoming.put(CodexError("Codex App Server closed its output."))

    def _send(self, message: dict) -> None:
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
        except OSError as exc:
            raise CodexError("Codex App Server stopped accepting messages.") from exc

    def _receive(self, deadline: float) -> dict:
        try:
            message = self.incoming.get(timeout=max(0, deadline - time.monotonic()))
        except queue.Empty as exc:
            raise TimeoutError("Timed out waiting for Codex App Server.") from exc
        if isinstance(message, Exception):
            raise message
        return message

    def _event(self, message: dict) -> None:
        if "id" in message and "method" in message:
            self._send({"id": message["id"], "error": {"code": -32601, "message": "Read-only quota client"}})

    def call(self, method: str, params: dict | None = None, timeout: float = 25) -> dict:
        self.sequence += 1
        request_id = self.sequence
        self._send({"id": request_id, "method": method, "params": params or {}})
        deadline = time.monotonic() + timeout
        while True:
            message = self._receive(deadline)
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    error = message["error"]
                    raise CodexError(f"{method} returned RPC error {error.get('code')}: {error.get('message')}")
                return message["result"]
            self._event(message)

    def subscription(self) -> dict:
        result = self.call("account/read")
        account = result.get("account") or {}
        if account.get("type") != "chatgpt":
            raise CodexError("Evaluation requires an active ChatGPT subscription login.")
        return {"type": account["type"], "plan": account.get("planType")}

    def quota(self) -> dict | None:
        try:
            response = self.call("account/rateLimits/read", timeout=12)
        except (CodexError, TimeoutError):
            return None
        windows = response.get("rateLimitsByLimitId") or {}
        if not windows and response.get("rateLimits"):
            snapshot = response["rateLimits"]
            windows = {snapshot.get("limitId", "codex"): snapshot}
        return {key: {period: {field: (value.get(period) or {}).get(field)
                               for field in ("usedPercent", "resetsAt", "windowDurationMins")}
                      for period in ("primary", "secondary") if value.get(period)}
                for key, value in windows.items()}
