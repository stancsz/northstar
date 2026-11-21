"""Verify that the configured Anthropic API account can invoke native Advisor."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def send_native(key: str, payload: dict, timeout: float) -> dict:
    request = Request("https://api.anthropic.com/v1/messages", data=json.dumps(payload).encode(),
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                               "anthropic-beta": "advisor-tool-2026-03-01",
                               "content-type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def main() -> int:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(json.dumps({"status": "missing_anthropic_api_key"}))
        return 2
    payload = {
        "model": "claude-sonnet-5",
        "max_tokens": 4096,
        "tools": [{
            "type": "advisor_20260301", "name": "advisor", "model": "claude-opus-5-5", "max_uses": 1,
        }],
        "messages": [{
            "role": "user",
            "content": (
                "Make one Advisor consultation before answering. Ask which unit test would best "
                "distinguish numeric sort from lexicographic sort for the list [2, 11, 1]. "
                "Then state the expected numeric order."
            ),
        }],
    }
    try:
        data = send_native(key, payload, 60)
    except HTTPError as exc:
        print(json.dumps({"status": "anthropic_http_error", "code": exc.code}))
        return 1
    except (URLError, TimeoutError):
        print(json.dumps({"status": "anthropic_transport_error"}))
        return 1
    blocks = [block["type"] for block in data.get("content", [])]
    iterations = data.get("usage", {}).get("iterations", [])
    consulted = "advisor_tool_result" in blocks and any(
        item.get("type") == "advisor_message" for item in iterations
    )
    print(json.dumps({"status": "consulted" if consulted else "consultation_unverified",
                      "stop_reason": data.get("stop_reason"), "block_types": blocks,
                      "usage_iteration_types": [item.get("type") for item in iterations]}))
    return 0 if consulted else 1


if __name__ == "__main__":
    raise SystemExit(main())
