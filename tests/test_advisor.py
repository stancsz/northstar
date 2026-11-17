"""Offline regressions for the simplified Advisor caller (skills/advisor/scripts/ask_expert.py)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest


ROOT = Path(__file__).resolve().parents[1]
CALLER = ROOT / "skills" / "advisor" / "scripts" / "ask_expert.py"

spec = importlib.util.spec_from_file_location("ask_expert", CALLER)
assert spec is not None and spec.loader is not None
ask_expert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ask_expert)


def _fake_response(payload: dict | str):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    buf = io.BytesIO(raw.encode("utf-8"))

    class _Resp:
        def __enter__(self):
            return buf

        def __exit__(self, *args):
            buf.close()

    return _Resp()


def test_instructions_enforce_four_line_turn_format():
    for label in ("Verdict:", "Next:", "Prompt:", "Risk:"):
        assert label in ask_expert.ADVISOR_INSTRUCTION
        assert label in ask_expert.VISUAL_INSTRUCTION
    assert ask_expert.MAX_PACKET_CHARS == 4_000


def test_read_packet_rejects_empty_and_bloated_packets(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n", encoding="utf-8")
    with pytest.raises(SystemExit, match="must not be empty"):
        ask_expert.read_packet(SimpleNamespace(question=None, input_file=empty_file))

    bloated = "x" * (ask_expert.MAX_PACKET_CHARS + 1)
    with pytest.raises(SystemExit, match="limit is 4000"):
        ask_expert.read_packet(SimpleNamespace(question=bloated, input_file=None))

    ok = ask_expert.read_packet(SimpleNamespace(question="  Decision: X\nQuestion: Y?  ", input_file=None))
    assert ok == "Decision: X\nQuestion: Y?"


def test_gateway_happy_path_and_token_limit(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=75.0):
        calls.append(req.full_url)
        if req.full_url.endswith("/responses/input_tokens"):
            return _fake_response({"input_tokens": 120})
        return _fake_response({
            "id": "req_123",
            "model": "gpt-6.1-terra",
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": "Verdict: Use a lock.\nNext: Add singleton.\nPrompt: Implement singleton.\nRisk: none"},
            }],
            "usage": {"prompt_tokens": 120, "completion_tokens": 25},
        })

    monkeypatch.setattr(ask_expert, "urlopen", fake_urlopen)
    monkeypatch.setenv("EXPERTS_API_KEY", "sk-secret-test")
    args = SimpleNamespace(base_url="http://127.0.0.1:4040/v1", timeout_seconds=10.0, image_parts=[])
    result = ask_expert.call_gateway(args, "gpt-6.1-terra", [{"role": "user", "content": "hi"}])

    assert calls == [
        "http://127.0.0.1:4040/v1/responses/input_tokens",
        "http://127.0.0.1:4040/v1/chat/completions",
    ]
    assert result["transport"] == "gateway"
    assert result["input_tokens"] == 120
    assert "Verdict:" in result["advice"]

    # Exceeding MAX_INPUT_TOKENS aborts before chat/completions
    calls.clear()
    monkeypatch.setattr(
        ask_expert,
        "urlopen",
        lambda req, timeout=75.0: _fake_response({"input_tokens": ask_expert.MAX_INPUT_TOKENS + 1}),
    )
    with pytest.raises(RuntimeError, match="no model request was sent"):
        ask_expert.call_gateway(args, "gpt-6.1-terra", [{"role": "user", "content": "hi"}])


def test_gateway_401_redacts_api_key(monkeypatch):
    def fake_urlopen(req, timeout=75.0):
        raise HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"bad key sk-secret-xyz"))

    monkeypatch.setattr(ask_expert, "urlopen", fake_urlopen)
    monkeypatch.setenv("EXPERTS_API_KEY", "sk-secret-xyz")
    args = SimpleNamespace(base_url="http://127.0.0.1:4040/v1", timeout_seconds=10.0, image_parts=[])
    with pytest.raises(RuntimeError, match="HTTP 401") as exc_info:
        ask_expert.call_gateway(args, "gpt-6.1-terra", [{"role": "user", "content": "hi"}])
    assert "sk-secret-xyz" not in str(exc_info.value)


def test_consult_codex_sse_stream(monkeypatch, tmp_path):
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"tokens": {"access_token": "tok-1", "account_id": "acc-1"}}), encoding="utf-8")
    monkeypatch.setenv("CODEX_AUTH_FILE", str(auth))

    sse = (
        'data: {"type":"response.output_text.delta","delta":"Verdict: Keep it simple.\\nNext: Run pytest.\\nPrompt: Run pytest now.\\nRisk: none"}\n\n'
        'data: {"type":"response.completed","response":{"id":"resp_1","model":"gpt-6.1-terra","status":"completed","usage":{"input_tokens":50,"output_tokens":20,"total_tokens":70}}}\n\n'
        "data: [DONE]\n\n"
    )
    monkeypatch.setattr(ask_expert, "urlopen", lambda req, timeout=75.0: _fake_response(sse))

    args = SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=10.0)
    res = ask_expert.consult_codex(args, [{"role": "user", "content": "hi"}], fallback_reason="gateway down")
    assert res["transport"] == "codex"
    assert res["fallback_reason"] == "gateway down"
    assert res["input_tokens"] == 50
    assert "Prompt:" in res["advice"]


def test_consult_claude_cli(monkeypatch):
    monkeypatch.setattr(ask_expert.shutil, "which", lambda name: "/usr/bin/claude" if name == "claude" else None)

    recorded = {}

    def fake_run(cmd, input, capture_output, text, encoding, timeout, check):
        recorded["cmd"] = cmd
        recorded["input"] = input
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "is_error": False,
                "result": "Verdict: Use a lock.\nNext: Add lock.\nPrompt: Add lock.\nRisk: none",
                "session_id": "sess_1",
                "usage": {"input_tokens": 40, "output_tokens": 15},
            }),
            stderr="",
        )

    monkeypatch.setattr(ask_expert.subprocess, "run", fake_run)
    args = SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=10.0)
    res = ask_expert.consult_claude(args, "SYS", "PKT")

    assert res["transport"] == "claude"
    assert res["model"] == "claude-cli-default"
    assert "--no-session-persistence" in recorded["cmd"]
    assert "--tools" in recorded["cmd"]
    assert recorded["input"] == "PKT"
    assert "Verdict:" in res["advice"]


def test_auto_transport_falls_back_to_claude_when_no_gateway_or_codex_auth(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("CODEX_AUTH_FILE", str(tmp_path / "missing-auth.json"))
    monkeypatch.setattr(ask_expert.shutil, "which", lambda name: "/usr/bin/claude" if name == "claude" else None)
    monkeypatch.setattr(
        ask_expert.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"is_error": False, "result": "Verdict: OK.\nNext: Go.\nPrompt: Go.\nRisk: none"}),
            stderr="",
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["ask_expert.py", "--question", "Decision: Test fallback?", "--base-url", ""],
    )
    rc = ask_expert.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["transport"] == "claude"
    assert out["fallback_reason"] is not None


def test_direct_cli_transports_reject_images(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["ask_expert.py", "--transport", "claude", "--question", "Check UI", "--image", "a.png"],
    )
    with pytest.raises(SystemExit, match="text packets only"):
        ask_expert.main()


def test_compact_packet_trims_whitespace_and_blank_runs():
    raw = "Line 1   \n\n\n\nLine 2\t\n\nLine 3"
    assert ask_expert.compact_packet(raw) == "Line 1\n\nLine 2\n\nLine 3"


def test_session_file_delta_context_and_round_budget(monkeypatch, capsys, tmp_path):
    session_file = tmp_path / "advisor-session.json"
    seen_packets = []

    def fake_claude(args, instruction, packet, fallback_reason=None):
        seen_packets.append(packet)
        return {
            "model": "claude-cli-default",
            "requested_model": args.model,
            "transport": "claude",
            "advice": f"Verdict: Round {len(seen_packets)} answer.\nNext: Step.\nPrompt: Do step.\nRisk: none",
            "advice_words": 10,
            "usage": {"input_tokens": 50, "output_tokens": 12},
            "request_id": f"s_{len(seen_packets)}",
            "elapsed_seconds": 0.1,
        }

    monkeypatch.setattr(ask_expert, "consult_claude", fake_claude)

    monkeypatch.setattr(
        sys,
        "argv",
        ["ask_expert.py", "--transport", "claude", "--session-file", str(session_file),
         "--max-rounds", "2", "--question", "Decision: R1 question?"],
    )
    assert ask_expert.main() == 0
    out1 = json.loads(capsys.readouterr().out)
    assert out1["round"] == 1
    assert out1["max_rounds"] == 2
    assert out1["cumulative_tokens"] == {"input_tokens": 50, "output_tokens": 12}

    monkeypatch.setattr(
        sys,
        "argv",
        ["ask_expert.py", "--transport", "claude", "--session-file", str(session_file),
         "--max-rounds", "2", "--question", "Delta: Ran step, saw X."],
    )
    assert ask_expert.main() == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["round"] == 2
    assert out2["cumulative_tokens"] == {"input_tokens": 100, "output_tokens": 24}
    assert seen_packets[1].startswith("Prior Verdict: Round 1 answer.\n\nDelta: Ran step, saw X.")

    monkeypatch.setattr(
        sys,
        "argv",
        ["ask_expert.py", "--transport", "claude", "--session-file", str(session_file),
         "--max-rounds", "2", "--question", "Should not run"],
    )
    assert ask_expert.main() == 1
    out3 = json.loads(capsys.readouterr().out)
    assert out3["status"] == "budget_exhausted"
    assert len(seen_packets) == 2
