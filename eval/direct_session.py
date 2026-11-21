"""Run both executor arms against the existing direct Codex subscription route."""

from __future__ import annotations

import importlib.util
import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request
from uuid import uuid4


CALLER = Path(__file__).resolve().parent.parent / "skills/advisor/scripts/ask_expert.py"
SPEC = importlib.util.spec_from_file_location("spot_advisor_transport", CALLER)
transport = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transport)


class ExecutorError(RuntimeError):
    pass


class DirectSession:
    def __init__(self, path: Path):
        raw_token, account = transport.read_codex_credentials()
        self.headers = {
            "Authorization": f"Bearer {raw_token}", "ChatGPT-Account-ID": account,
            "User-Agent": "OpenAI-Codex/0.154.0", "Content-Type": "application/json", "Accept": "text/event-stream",
        }
        self.journal = path
        self.attempts = []
        self.reroutes = []

    def record(self, event: str, receipt: dict) -> None:
        row = {"event": event, "timestamp_utc": datetime.now(timezone.utc).isoformat(), **receipt}
        with self.journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def request(self, model: str, effort: str, messages: list, tools: list[dict], deadline: float) -> dict:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Executor wall-clock limit reached.")
        payload = {
            "model": model, "instructions": "Execute the assigned benchmark task strictly within the supplied tools.",
            "input": messages, "stream": True, "store": False, "reasoning": {"effort": effort},
            "tools": [{"type": "function", "name": tool["name"], "description": tool["description"],
                       "parameters": tool["inputSchema"]} for tool in tools],
            "include": ["reasoning.encrypted_content"],
        }
        request = Request(transport.CODEX_API_BASE_URL + "/responses", headers=self.headers,
                          data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST")
        receipt = {"attempt_id": uuid4().hex, "requested_model": model, "reasoning_effort": effort}
        self.record("dispatched", receipt)
        terminal = None
        status = "unavailable"
        started = time.monotonic()
        try:
            with transport.urlopen(request, timeout=min(90, remaining)) as stream:
                for event in transport.codex_stream_events(stream):
                    if event.get("type") in {"response.completed", "response.incomplete", "response.failed", "error"}:
                        terminal = event.get("response") or {}
                        status = event["type"].removeprefix("response.")
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError("Executor wall-clock limit reached while receiving a response.")
        except HTTPError as exc:
            status = "rate_limited" if exc.code == 429 else "http_error"
            raise ExecutorError(f"Direct Codex executor returned HTTP {exc.code}.") from exc
        except (URLError, OSError) as exc:
            raise ExecutorError(f"Direct Codex executor transport failed ({type(exc).__name__}).") from exc
        finally:
            terminal = terminal or {}
            usage = transport.normalized_usage({"usage": terminal.get("usage")})
            receipt.update(model=terminal.get("model"), request_id=terminal.get("id"), status=status,
                           usage=usage, elapsed_seconds=round(time.monotonic() - started, 3))
            self.record("finished", receipt)
            self.attempts.append(receipt)
        if status != "completed":
            raise ExecutorError(f"Direct Codex executor response ended with status {status}.")
        if terminal.get("model") != model:
            self.reroutes.append({"fromModel": model, "toModel": terminal.get("model")})
            raise ExecutorError("Direct Codex returned a different executor model.")
        return terminal

    def run(self, model: str, effort: str, prompt: str, tools: list[dict], handle, timeout: float) -> dict:
        return self.continue_run(model, effort, [{"role": "user", "content": prompt}], tools, handle, timeout)

    def continue_run(self, model: str, effort: str, messages: list[dict], tools: list[dict],
                     handle, timeout: float, *, stop_after_batch=None) -> dict:
        """Continue from complete conversation items without modifying the supplied checkpoint."""
        deadline = time.monotonic() + timeout
        messages = deepcopy(messages)
        for _ in range(101):
            terminal = self.request(model, effort, messages, tools, deadline)
            output = terminal.get("output", [])
            calls = [item for item in output if item.get("type") == "function_call"]
            if not calls:
                return {"turn_id": terminal.get("id"), "status": "completed"}
            messages.extend(output)
            for call in calls:
                try:
                    arguments = json.loads(call["arguments"])
                except (KeyError, ValueError):
                    arguments = {}
                result = handle({"tool": call.get("name"), "arguments": arguments if isinstance(arguments, dict) else {}})
                messages.append({"type": "function_call_output", "call_id": call["call_id"],
                                 "output": json.dumps(result, ensure_ascii=False)})
            if stop_after_batch is not None and stop_after_batch():
                return {"turn_id": terminal.get("id"), "status": "checkpoint", "messages": messages}
        raise TimeoutError("Executor reached the request limit.")

    def usage(self) -> dict:
        result = {}
        for key in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "reasoning_output_tokens"):
            counts = [row["usage"][key] for row in self.attempts]
            result[key] = sum(counts) if counts and all(value is not None for value in counts) else None
        return result
