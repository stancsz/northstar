"""Native Claude Advisor conversation driver for the diagnostic evaluator."""

from __future__ import annotations

import json


NATIVE_ADVISOR = {
    "type": "advisor_20260301", "name": "advisor", "model": "claude-opus-5-5", "max_uses": 1,
}


def run_native(send, prompt: str, tools: list[dict], handle, remaining, *, on_receipt=None) -> dict:
    """Run until Claude finishes, preserving server-side advisor blocks between requests."""
    native_tools = [
        {"name": tool["name"], "description": tool["description"], "input_schema": tool["inputSchema"]}
        for tool in tools
    ]
    messages = [{"role": "user", "content": prompt}]
    receipts = []
    for _ in range(101):
        response = send({
            "model": "claude-sonnet-5",
            "max_tokens": 4096,
            "messages": messages,
            "tools": [*native_tools, NATIVE_ADVISOR],
        }, remaining())
        blocks = response["content"]
        reason = response["stop_reason"]
        receipts.append({
            "response_id": response.get("id"),
            "model": response.get("model"),
            "usage": response.get("usage"),
            "stop_reason": reason,
            "block_types": [block["type"] for block in blocks],
        })
        if on_receipt is not None:
            on_receipt(receipts[-1])
        messages.append({"role": "assistant", "content": blocks})
        if reason == "pause_turn":
            continue
        if reason != "tool_use":
            return {"status": reason, "receipts": receipts}
        results = [
            {
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(handle({"tool": block["name"], "arguments": block["input"]}),
                                      ensure_ascii=False),
            }
            for block in blocks if block["type"] == "tool_use"
        ]
        if not results:
            raise ValueError("Claude requested a client tool without an invocation.")
        messages.append({"role": "user", "content": results})
    raise TimeoutError("Claude executor reached the request limit.")
