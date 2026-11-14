import importlib.util
import base64
import hashlib
import io
from pathlib import Path
import sys
import json
import subprocess
import os
import threading
from urllib.error import HTTPError, URLError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).parents[1]
CALLER = ROOT / "skills" / "advisor-council" / "scripts" / "ask_expert.py"
TOKEN_COUNT_SUFFIX = "/responses/input_tokens"
CODEX_RESPONSES_SUFFIX = "/backend-api/codex/responses"


def codex_event_stream(events):
    lines = []
    for event in events:
        if isinstance(event, str):
            lines.append(f"data: {event}\n\n")
        else:
            lines.append(f"data: {json.dumps(event, ensure_ascii=False)}\n\n")
    return io.BytesIO("".join(lines).encode("utf-8"))


def codex_completed_event(model="gpt-6.1-terra", *, usage=None):
    return {"type": "response.completed", "response": {
        "status": "completed", "id": "resp-codex-test", "model": model,
        "usage": usage or {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20},
    }}


def write_codex_auth_file(tmp_path, monkeypatch, access_token="codex-test-token"):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(json.dumps({"tokens": {
        "access_token": access_token, "account_id": "codex-test-account",
    }}), encoding="utf-8")
    monkeypatch.setenv("CODEX_AUTH_FILE", str(auth_file))
    return auth_file


def with_token_counter(handler, count=16, observed=None):
    """Stub the route's exact-count endpoint while preserving a provider handler."""
    def route(request, **kwargs):
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            if observed is not None:
                observed.append(json.loads(request.data))
            return io.StringIO(json.dumps({"object": "response.input_tokens", "input_tokens": count}))
        return handler(request, **kwargs)
    return route


def load_caller():
    spec = importlib.util.spec_from_file_location("codex_advisor_caller", CALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


@pytest.mark.parametrize("value,kind,expected", [
    ("fixture-user-key", 1, "fixture-user-key"), ("", 1, None),
    ("   ", 1, None), ("fixture-user-key", 2, None), (None, 1, None),
])
def test_windows_user_key_reads_only_a_nonempty_string(monkeypatch, value, kind, expected):
    caller = load_caller()
    registry = SimpleNamespace(HKEY_CURRENT_USER=object(), REG_SZ=1,
        OpenKey=lambda *a: io.StringIO(), QueryValueEx=lambda *a: (value, kind))
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(caller.sys, "platform", "win32")
    assert caller.windows_user_api_key() == expected


def test_unconfigured_windows_user_key_is_optional(monkeypatch):
    caller = load_caller()
    def missing(*args):
        raise FileNotFoundError("No configured value")
    registry = SimpleNamespace(HKEY_CURRENT_USER=object(), REG_SZ=1, OpenKey=missing)
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(caller.sys, "platform", "win32")
    assert caller.windows_user_api_key() is None
    monkeypatch.setattr(caller.sys, "platform", "linux")
    registry.OpenKey = lambda *a: pytest.fail("Registry must not be read off Windows")
    assert caller.windows_user_api_key() is None


@pytest.mark.parametrize("url,expected,windows_reads", [
    ("http://127.0.0.1:4040/v1", "user-key", 1),
    ("http://LOCALHOST:4040/v1/", "user-key", 1),
    ("http://[::1]:4040/v1", "user-key", 1),
    ("http://localhost/v1", None, 0), ("https://localhost:4040/v1", None, 0),
    ("http://example.com:4040/v1", None, 0), ("http://192.168.1.2:4040/v1", None, 0),
    ("http://user@localhost:4040/v1", None, 0),
])
def test_local_key_fallback_uses_endpoint_credentials_without_leaking(monkeypatch, url, expected, windows_reads):
    caller = load_caller()
    monkeypatch.delenv("EXPERTS_API_KEY", raising=False)
    calls = []
    monkeypatch.setattr(caller, "windows_user_api_key", lambda: calls.append(1) or "user-key")
    assert caller.expert_api_key(url) == expected
    assert len(calls) == windows_reads


@pytest.mark.parametrize("key", ["process-key", ""])
def test_explicit_process_key_wins_over_user_configuration(monkeypatch, key):
    caller = load_caller()
    monkeypatch.setenv("EXPERTS_API_KEY", key)
    monkeypatch.setattr(caller, "windows_user_api_key", lambda: pytest.fail("Must use process env"))
    assert caller.expert_api_key("http://localhost:4040/v1") == (key or None)


@pytest.mark.parametrize("with_image", [False, True])
def test_bearer_key_is_sent_for_consultation(monkeypatch, with_image):
    caller = load_caller()
    monkeypatch.delenv("EXPERTS_API_KEY", raising=False)
    monkeypatch.setattr(caller, "windows_user_api_key", lambda: "fixture-user-key")
    requests = []
    def upstream(request, **kwargs):
        requests.append(request)
        assert request.get_header("Authorization") == "Bearer fixture-user-key"
        assert request.full_url.endswith("/chat/completions")
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": "Verdict: received."}}]}))
    count_requests = []
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream, observed=count_requests))
    image_parts = []
    if with_image:
        image_parts, _ = caller.prepare_images([ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png"])
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1,
        image_parts=image_parts)
    result = caller.consult(args, [{"role": "user", "content": "Inspect."}])
    assert len(requests) == 1
    assert len(count_requests) == 1
    assert count_requests[0]["model"] == "gpt-6.1-terra"
    blocks = json.loads(requests[0].data)["messages"][0]["content"]
    if with_image:
        assert any(block.get("type") == "image_url" for block in blocks)
    else:
        assert isinstance(blocks, str)
    assert "fixture-user-key" not in json.dumps(result)


def test_missing_base_url_stops_before_request(monkeypatch):
    caller = load_caller()
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: pytest.fail("Unconfigured base URL must not send a request"))
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="EXPERTS_BASE_URL"):
        caller.consult(args, [{"role": "user", "content": "Inspect."}])


def test_direct_codex_streams_completion_and_reports_provider_usage(tmp_path, monkeypatch):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    requests = []

    def upstream(request, **kwargs):
        requests.append(request)
        return codex_event_stream([
            {"type": "response.output_text.delta", "delta": "Verdict: use Codex.\nNext: test.\nRisk: none"},
            codex_completed_event(),
        ])

    monkeypatch.setattr(caller, "urlopen", upstream)
    args = SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=1)
    result = caller.consult_codex(args, [
        {"role": "developer", "content": caller.ADVISOR_INSTRUCTION},
        {"role": "user", "content": "Check Unicode input: Calgary 雪."},
    ], fallback_reason="gateway unavailable")

    assert len(requests) == 1
    request = requests[0]
    assert request.full_url.endswith(CODEX_RESPONSES_SUFFIX)
    assert request.get_header("Authorization") == "Bearer codex-test-token"
    assert next(value for key, value in request.header_items() if key.lower() == "chatgpt-account-id") == "codex-test-account"
    payload = json.loads(request.data)
    assert payload["model"] == "gpt-6.1-terra"
    assert payload["stream"] is True and payload["store"] is False
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["input"][-1]["content"] == "Check Unicode input: Calgary 雪."
    assert len(request.data) <= caller.MAX_CODEX_REQUEST_BYTES
    assert result["transport"] == "codex"
    assert result["fallback_reason"] == "gateway unavailable"
    assert result["requested_model"] == result["model"] == "gpt-6.1-terra"
    assert result["request_id"] == "resp-codex-test"
    assert result["input_tokens"] == 12
    assert result["usage"]["total_tokens"] == 20
    assert "codex-test-token" not in json.dumps(result)


def test_direct_codex_enforces_complete_utf8_request_byte_limit(tmp_path, monkeypatch):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: pytest.fail("Oversized request reached Codex"))
    args = SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="bytes; the limit is 24,000"):
        caller.consult_codex(args, [{"role": "user", "content": "😀" * 6_000}])


def test_direct_codex_requires_supported_models_and_login(tmp_path, monkeypatch):
    caller = load_caller()
    monkeypatch.setenv("CODEX_AUTH_FILE", str(tmp_path / "missing-auth.json"))
    args = SimpleNamespace(model="gemini-3.8-flash-low", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="only gpt-6.1-terra and gpt-6.1-sol"):
        caller.consult_codex(args, [{"role": "user", "content": "A synthetic packet."}])
    args.model = "gpt-6.1-terra"
    with pytest.raises(RuntimeError, match="codex login"):
        caller.consult_codex(args, [{"role": "user", "content": "A synthetic packet."}])


def test_direct_codex_auth_error_redacts_credentials(tmp_path, monkeypatch):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch, access_token="sensitive-codex-token")

    def upstream(request, **kwargs):
        body = b"sensitive-codex-token codex-test-account"
        raise HTTPError(request.full_url, 401, "unauthorized", {}, io.BytesIO(body))

    monkeypatch.setattr(caller, "urlopen", upstream)
    with pytest.raises(RuntimeError, match="authentication was rejected") as failure:
        caller.consult_codex(SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=1), [
            {"role": "user", "content": "A synthetic packet."},
        ])
    assert "sensitive-codex-token" not in str(failure.value)
    assert "codex-test-account" not in str(failure.value)


@pytest.mark.parametrize("events,match", [
    (["not-json"], "malformed streaming event"),
    ([{"type": "response.output_text.delta", "delta": "incomplete"}], "without a completed response"),
    ([{"type": "response.incomplete"}], "failed or was incomplete"),
    ([{"type": "response.output_text.delta", "delta": "advice"},
      codex_completed_event(model="gpt-6.1-sol")], "expected requested model"),
    ([{"type": "response.output_text.delta", "delta": "advice"},
      codex_completed_event(usage={"input_tokens": True, "output_tokens": 1, "total_tokens": 2})],
     "valid provider usage"),
])
def test_direct_codex_rejects_malformed_or_invalid_streams(tmp_path, monkeypatch, events, match):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: codex_event_stream(events))
    with pytest.raises(RuntimeError, match=match):
        caller.consult_codex(SimpleNamespace(model="gpt-6.1-terra", timeout_seconds=1), [
            {"role": "user", "content": "A synthetic packet."},
        ])


@pytest.mark.parametrize("connection_error", [URLError("connection refused"), TimeoutError("preflight timed out")])
def test_auto_falls_back_to_codex_on_gateway_preflight_connection_failure(
        tmp_path, monkeypatch, capsys, connection_error):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "A synthetic packet.",
        "--base-url", "http://127.0.0.1:1/v1"])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            raise connection_error
        return codex_event_stream([
            {"type": "response.output_text.delta", "delta": "Verdict: use Codex.\nNext: test.\nRisk: none"},
            codex_completed_event(),
        ])

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["transport"] == "codex"
    expected_reason = "connection refused" if isinstance(connection_error, URLError) else "preflight timed out"
    assert expected_reason in result["fallback_reason"]
    assert requests == ["http://127.0.0.1:1/v1/responses/input_tokens",
                        f"https://chatgpt.com{CODEX_RESPONSES_SUFFIX}"]


def test_auto_does_not_fall_back_after_gateway_inference_starts(monkeypatch, capsys):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "A synthetic packet.",
        "--base-url", "http://127.0.0.1:4040/v1"])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            return io.StringIO(json.dumps({"input_tokens": 12}))
        raise URLError("inference connection lost")

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable"
    assert "inference connection lost" in result["error"]
    assert requests == ["http://127.0.0.1:4040/v1/responses/input_tokens",
                        "http://127.0.0.1:4040/v1/chat/completions"]


def test_gateway_http_error_does_not_trigger_automatic_codex_fallback(monkeypatch, capsys):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "A synthetic packet.",
        "--base-url", "http://127.0.0.1:4040/v1"])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        raise HTTPError(request.full_url, 503, "service unavailable", {}, io.BytesIO(b"gateway error"))

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable"
    assert "HTTP 503" in result["error"]
    assert requests == ["http://127.0.0.1:4040/v1/responses/input_tokens"]


def test_auto_malformed_gateway_count_does_not_trigger_codex_fallback(monkeypatch, capsys):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "A synthetic packet.",
        "--base-url", "http://127.0.0.1:4040/v1"])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        return io.StringIO(json.dumps({"input_tokens": True}))

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable"
    assert "valid input_tokens" in result["error"]
    assert requests == ["http://127.0.0.1:4040/v1/responses/input_tokens"]


def test_explicit_transport_and_unsupported_direct_mode(monkeypatch):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--transport", "codex",
        "--complexity", "complex", "--question", "A synthetic packet."])
    with pytest.raises(SystemExit, match="require the Advisor gateway"):
        caller.main()

    monkeypatch.setattr(sys, "argv", [str(CALLER), "--transport", "gateway",
        "--question", "A synthetic packet."])
    args = caller.parse_args()
    assert args.transport == "gateway"


def test_explicit_gateway_does_not_fall_back_when_gateway_is_missing(monkeypatch, capsys):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--transport", "gateway",
        "--question", "A synthetic packet.", "--base-url", ""])
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: pytest.fail("Missing gateway sent a request"))
    assert caller.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable"
    assert "EXPERTS_BASE_URL" in result["error"]


def test_explicit_codex_skips_gateway_and_reports_no_fallback(tmp_path, monkeypatch, capsys):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--transport", "codex",
        "--question", "A synthetic packet.", "--base-url", "http://127.0.0.1:4040/v1"])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        return codex_event_stream([
            {"type": "response.output_text.delta", "delta": "Verdict: direct.\nNext: verify.\nRisk: none"},
            codex_completed_event(),
        ])

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["transport"] == "codex"
    assert result["fallback_reason"] is None
    assert requests == [f"https://chatgpt.com{CODEX_RESPONSES_SUFFIX}"]


def test_auto_without_gateway_url_uses_direct_codex(tmp_path, monkeypatch, capsys):
    caller = load_caller()
    write_codex_auth_file(tmp_path, monkeypatch)
    monkeypatch.delenv("EXPERTS_BASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "A synthetic packet.",
        "--base-url", ""])
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        return codex_event_stream([
            {"type": "response.output_text.delta", "delta": "Verdict: direct.\nNext: verify.\nRisk: none"},
            codex_completed_event(),
        ])

    monkeypatch.setattr(caller, "urlopen", upstream)
    assert caller.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["transport"] == "codex"
    assert "base URL is not configured" in result["fallback_reason"]
    assert requests == [f"https://chatgpt.com{CODEX_RESPONSES_SUFFIX}"]


def test_request_token_count_boundary_and_adversarial_unicode(monkeypatch):
    caller = load_caller()
    calls, count_requests = [], []
    counts = iter([caller.MAX_INPUT_TOKENS, caller.MAX_INPUT_TOKENS + 1, caller.MAX_INPUT_TOKENS + 1])
    def upstream(request, **kwargs):
        calls.append(json.loads(request.data))
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": "ok"}}]}))
    def count_handler(request, **kwargs):
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            count_requests.append(json.loads(request.data))
            return io.StringIO(json.dumps({"input_tokens": next(counts)}))
        return upstream(request, **kwargs)
    monkeypatch.setattr(caller, "urlopen", count_handler)
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1)
    exact = "x" * 40_000
    result = caller.call_model(args, "gpt-6.1-terra", [{"role": "user", "content": exact}])
    assert result["advice"] == "ok"
    assert result["input_tokens"] == caller.MAX_INPUT_TOKENS
    assert calls[-1]["model"] == "gpt-6.1-terra"
    assert calls[-1]["reasoning_effort"] == "low"
    with pytest.raises(RuntimeError, match="32,000.*no model request was sent"):
        caller.call_model(args, "gpt-6.1-terra", [{"role": "user", "content": exact + "x"}])
    with pytest.raises(RuntimeError, match="32,000.*no model request was sent"):
        caller.call_model(args, "gpt-6.1-terra", [{"role": "user", "content": "界" * 10_000}])
    assert len(calls) == 1
    assert len(count_requests) == 3
    assert count_requests[-1]["input"][0]["content"] == "界" * 10_000


def test_oversized_multimessage_request_stops_before_network(monkeypatch):
    caller = load_caller()
    count_requests = []
    def counter(request, **kwargs):
        count_requests.append(json.loads(request.data))
        return io.StringIO(json.dumps({"input_tokens": caller.MAX_INPUT_TOKENS + 1}))
    monkeypatch.setattr(caller, "urlopen", counter)
    args = SimpleNamespace(base_url="http://localhost:4040/v1", timeout_seconds=1)
    messages = [{"role": "developer", "content": "a" * 20_000},
                {"role": "user", "content": "b" * 15_000}]
    with pytest.raises(RuntimeError, match="no model request was sent"):
        caller.call_model(args, "gpt-6.1-terra", messages)
    assert count_requests[0]["input"] == messages


@pytest.mark.parametrize("count_body", [{}, {"input_tokens": True}, {"input_tokens": -1}])
def test_invalid_token_count_stops_before_model_submission(monkeypatch, count_body):
    caller = load_caller()
    requests = []

    def upstream(request, **kwargs):
        requests.append(request.full_url)
        return io.StringIO(json.dumps(count_body))

    monkeypatch.setattr(caller, "urlopen", upstream)
    args = SimpleNamespace(base_url="http://localhost:4040/v1", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="valid input_tokens.*no model request was sent"):
        caller.call_model(args, "gpt-6.1-terra", [{"role": "user", "content": "question"}])
    assert requests == ["http://localhost:4040/v1/responses/input_tokens"]


def test_image_consultation_remains_attached(monkeypatch):
    caller = load_caller()
    sent, count_requests = [], []
    def upstream(request, **kwargs):
        sent.append(json.loads(request.data))
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}))
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream, count=23, observed=count_requests))
    parts, _ = caller.prepare_images([ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png"])
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1, image_parts=parts)
    caller.consult(args, [{"role":"user","content":"Inspect."}])
    assert sent[0]["reasoning_effort"] == "low"
    assert sent[0]["messages"][0]["content"][-1] == parts[-1]
    assert count_requests[0]["model"] == "gpt-6.1-terra"
    assert count_requests[0]["input"][0]["content"][-1]["type"] == "input_image"
    assert count_requests[0]["input"][0]["content"][-1]["detail"] == "high"
    assert sent[0]["model"] == "gpt-6.1-terra"
    assert len(sent) == 1


@pytest.mark.parametrize(("count", "submitted"), [
    (32_000, True), (32_001, False),
])
def test_image_input_token_limit_boundary(count, submitted, monkeypatch):
    caller = load_caller()
    sent, counted = [], []

    def upstream(request, **kwargs):
        body = json.loads(request.data)
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            counted.append(body)
            return io.StringIO(json.dumps({"input_tokens": count}))
        sent.append(body)
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": "ok"}}]}))

    monkeypatch.setattr(caller, "urlopen", upstream)
    parts, _ = caller.prepare_images([ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png"])
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1",
        timeout_seconds=1, image_parts=parts)
    if submitted:
        result = caller.consult(args, [{"role": "user", "content": "Inspect this view."}])
        assert result["input_tokens"] == 32_000
    else:
        with pytest.raises(RuntimeError, match="no model request was sent"):
            caller.consult(args, [{"role": "user", "content": "Inspect this view."}])
    assert len(counted) == 1
    assert counted[0]["input"][-1]["content"][-1]["type"] == "input_image"
    assert len(sent) == int(submitted)


def test_malformed_and_oversized_images_are_rejected_before_submission(tmp_path, monkeypatch):
    caller = load_caller()
    image = tmp_path / "view.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"truncated")
    monkeypatch.setattr(caller, "urlopen", lambda *a, **k: pytest.fail("Invalid image reached network"))
    with pytest.raises(ValueError, match="malformed or truncated"):
        caller.prepare_images([image])
    image.write_bytes((ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png").read_bytes())
    monkeypatch.setattr(caller, "MAX_IMAGE_BYTES", 16)
    with pytest.raises(ValueError, match="no larger"):
        caller.prepare_images([image])


def test_truncated_jpeg_is_rejected_before_submission(tmp_path, monkeypatch):
    from PIL import Image

    caller = load_caller()
    image = tmp_path / "truncated.jpg"
    source = tmp_path / "source.jpg"
    Image.new("RGB", (8, 8), "red").save(source, format="JPEG")
    image.write_bytes(source.read_bytes().rstrip(b"\xff\xd9"))
    monkeypatch.setattr(caller, "urlopen", lambda *a, **k: pytest.fail("Truncated JPEG reached network"))
    with pytest.raises(ValueError, match="malformed or truncated"):
        caller.prepare_images([image])


def test_reader_followup_uses_bounded_shared_call_path(source_repo, monkeypatch):
    caller, reader = load_caller(), load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    monkeypatch.setattr(reader, "run_pi", lambda *a, **kw: {"status": "ok", "evidence": evidence()})
    requests = []
    def upstream(request, **kwargs):
        body = json.loads(request.data)
        requests.append(body)
        answer = ('{"read":"What does source say?"}' if len(requests) == 1 else
                  '{"advice":"Verdict: Source checked.\\nNext: Verify runtime.\\nRisk: none"}')
        return io.StringIO(json.dumps({"model": body["model"], "choices": [{
            "finish_reason": "stop", "message": {"content": answer}}]}))
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream))
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1,
        image_parts=[], reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "packet", caller.consult, "instruction")
    assert result["status"] == "ok", result
    assert len(requests) == 2
    assert all(request["model"] == "gpt-6.1-terra" and request["reasoning_effort"] == "low" for request in requests)
    assert "retries = 0" in requests[1]["messages"][-1]["content"]


def test_oversized_actual_reader_followup_stops_before_second_request(source_repo, monkeypatch):
    caller, reader = load_caller(), load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    monkeypatch.setattr(reader, "MAX_EXPERT_CONTEXT_CHARS", 40_000)
    monkeypatch.setattr(reader, "run_pi", lambda *a, **kw: {"status": "ok", "evidence": evidence()})
    requests, token_counts = [], iter([16, caller.MAX_INPUT_TOKENS + 1])
    def upstream(request, **kwargs):
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            return io.StringIO(json.dumps({"input_tokens": next(token_counts)}))
        requests.append(json.loads(request.data))
        assert len(requests) == 1
        answer = '{"read":"What does source say?"}'
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": answer}}]}))
    monkeypatch.setattr(caller, "urlopen", upstream)
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1,
        image_parts=[], reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "p" * 28_500, caller.consult, "instruction")
    assert result["status"] == "unavailable"
    assert "32,000" in result["error"]
    assert len(requests) == 1


@pytest.mark.parametrize("status", [401, 502])
def test_auth_error_is_actionable_redacted_and_never_retried(monkeypatch, status):
    caller = load_caller()
    monkeypatch.setenv("EXPERTS_API_KEY", "fixture-secret")
    requests = []
    def upstream(request, **kwargs):
        requests.append(request)
        raise caller.HTTPError(request.full_url, status, "failed", {}, io.BytesIO(b"fixture-secret"))
    monkeypatch.setattr(caller, "urlopen", upstream)
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1)
    with pytest.raises(RuntimeError) as error:
        caller.consult(args, [])
    assert len(requests) == 1
    assert "fixture-secret" not in str(error.value)
    assert f"HTTP {status}" in str(error.value)
    if status == 401:
        assert "EXPERTS_API_KEY" in str(error.value)
        assert "no model request was sent" in str(error.value)


def test_redirect_does_not_forward_an_advisor_credential(monkeypatch):
    caller = load_caller()
    monkeypatch.setenv("EXPERTS_API_KEY", "fixture-secret")
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(self.path)
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(302)
            self.send_header("Location", "/redirected")
            self.end_headers()

        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        args = SimpleNamespace(model="gpt-6.1-terra", base_url=f"http://127.0.0.1:{server.server_port}/v1",
            timeout_seconds=1)
        with pytest.raises(RuntimeError, match="HTTP 302"):
            caller.consult(args, [])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert requests == ["/v1/responses/input_tokens"]


def test_packaged_caller_reconfigures_legacy_windows_stdout_to_utf8():
    caller = load_caller()
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")

    caller.configure_utf8_stdout(stream)
    stream.write("Astra 建议 ✅")
    stream.flush()

    assert raw.getvalue() == "Astra 建议 ✅".encode("utf-8")


def load_reader():
    spec = importlib.util.spec_from_file_location("expert_reader", CALLER.with_name("expert_reader.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("retries = 0\n", encoding="utf-8")
    (repo / "src" / "auth.json").write_text('{"private":true}', encoding="utf-8")
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    (repo / "src" / "untracked.py").write_text("not approved", encoding="utf-8")
    return repo


def evidence():
    return json.dumps({"findings": [{"file": "src/app.py", "line": 1,
        "quote": "retries = 0", "fact": "Retries are disabled in source."}],
        "unknowns": "Runtime behavior not verified."})


def test_snapshot_limits_authority_and_keeps_current_edits(source_repo, tmp_path):
    reader = load_reader()
    (source_repo / "src" / "app.py").write_text("retries = 1\n", encoding="utf-8")
    snapshot = tmp_path / "snapshot"
    result = reader.snapshot_sources(source_repo, ["src"], snapshot)
    assert list(result["files"]) == ["src/app.py"]
    assert result["excluded_files"] == 1
    assert (snapshot / "src/app.py").read_text() == "retries = 1\n"
    with pytest.raises(ValueError, match="escapes"):
        reader.snapshot_sources(source_repo, [".."], tmp_path / "bad")


@pytest.mark.parametrize("mutation", ["escape", "invented_quote", "wrong_line", "oversized", "multiline_quote"])
def test_reader_rejects_unverifiable_evidence(source_repo, mutation):
    reader = load_reader()
    data = json.loads(evidence())
    if mutation == "escape":
        data["findings"][0]["file"] = "../outside.py"
    elif mutation == "invented_quote":
        data["findings"][0]["quote"] = "retries = 9"
    elif mutation == "wrong_line":
        data["findings"][0]["line"] = 999
    elif mutation == "multiline_quote":
        data["findings"][0]["quote"] = "retries = 0\nnext_line"
    else:
        data["unknowns"] = "x" * 2001
    with pytest.raises(ValueError):
        reader.validate_evidence(json.dumps(data), source_repo)


def test_reader_accepts_only_a_single_json_fence_without_relaxing_citations(source_repo):
    reader = load_reader()
    wrapped = "```json\n" + evidence() + "\n```"
    assert json.loads(reader.validate_evidence(wrapped, source_repo)) == json.loads(evidence())
    for bad in ("Explanation\n" + wrapped, wrapped + "\nMore prose",
                wrapped + "\n" + wrapped, wrapped.replace("retries = 0", "retries = 9")):
        with pytest.raises(ValueError):
            reader.validate_evidence(bad, source_repo)


@pytest.mark.parametrize("decision,worker_ok,expected_calls,status", [
    ('{"read":"What is the retry setting?"}', True, 2, "ok"),
    ('{"read":"What is the retry setting?"}', False, 1, "unavailable"),
    ('{"advice":"Verdict: Enough.\\nNext: Verify.\\nRisk: none"}', True, 1, "ok"),
    ('not JSON', True, 1, "unavailable"),
    ('{"read":"question", "advice":"ambiguous"}', True, 1, "unavailable"),
])
def test_expert_controls_read_without_vendor_specific_history_or_retries(
        source_repo, monkeypatch, decision, worker_ok, expected_calls, status):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    calls, questions = [], []
    def consult(args, messages):
        calls.append(messages)
        return {"advice": decision if len(calls) == 1 else '{"advice":"Verdict: Inspect deployment.\\nNext: Test.\\nRisk: none"}',
                "usage": {"total_tokens": 50}}
    def pi(package, snapshot, question, model, **kwargs):
        if kwargs.get("preflight"):
            return {"status": "ok"}
        questions.append(question)
        return {"status": "ok" if worker_ok else "unavailable", "evidence": evidence()}
    monkeypatch.setattr(reader, "run_pi", pi)
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "Selected-route hypothesis: broken retries.", consult, "Be concise.")
    assert result["status"] == status
    assert len(calls) == expected_calls
    assert len(result["expert_calls"]) == expected_calls
    assert all(q == "What is the retry setting?" for q in questions)
    if expected_calls == 2:
        assert "retries = 0" in calls[1][-1]["content"]
        assert "advice" in result
    if status == "unavailable":
        assert "advice" not in result


def test_bad_reader_citation_stops_before_paid_followup(source_repo, monkeypatch):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    monkeypatch.setattr(reader, "run_pi", lambda *a, **kw: {"status": "ok"} if kw else {
        "status": "ok", "evidence": evidence().replace("retries = 0", "retries = 8")})
    calls = []
    def consult(*args):
        calls.append(args)
        return {"advice": '{"read":"Inspect retries"}', "usage": {"total_tokens": 10}}
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "packet", consult, "instruction")
    assert result["status"] == "unavailable"
    assert len(calls) == 1
    assert result["expert_calls"][0]["usage"]["total_tokens"] == 10


def test_incomplete_expert_is_not_advice(monkeypatch):
    caller = load_caller()
    body = {"choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}
    monkeypatch.setattr(caller, "urlopen", with_token_counter(lambda *a, **k: io.StringIO(json.dumps(body))))
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="completed"):
        caller.consult(args, [])


def test_council_calls_selected_models_and_keeps_primary_verdict(monkeypatch):
    caller = load_caller()
    requests = []
    def upstream(request, **kwargs):
        body = json.loads(request.data)
        requests.append(body)
        answer = "Council concern: check the timeout." if len(requests) == 1 else (
            "Own verdict: Keep the bounded route.\n"
            "Independent review: Agree on timeout evidence, but no broad rewrite.\n"
            "Next: Probe cancellation.\nRisk: orphaned work."
        )
        return io.StringIO(json.dumps({"model": body["model"], "usage": {"total_tokens": 9},
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}]}))
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream))
    args = SimpleNamespace(model="gpt-6.1-terra", council_model="gemini-3.8-flash-low",
                           base_url="http://localhost:4040/v1", timeout_seconds=1)
    result = caller.consult_council(args, "Original decision packet.")
    assert [request["model"] for request in requests] == ["gemini-3.8-flash-low", "gpt-6.1-terra"]
    assert "Original decision packet." in requests[0]["messages"][-1]["content"]
    assert "Council concern" not in requests[0]["messages"][-1]["content"]
    assert "Council concern" in requests[1]["messages"][-1]["content"]
    assert "Own verdict" in requests[1]["messages"][0]["content"]
    assert len(result["council"]) == 2
    assert result["council"][0]["usage"]["total_tokens"] == 9


def test_council_stops_if_review_model_does_not_complete(monkeypatch):
    caller = load_caller()
    calls = []
    def upstream(request, **kwargs):
        calls.append(json.loads(request.data)["model"])
        return io.StringIO(json.dumps({"choices": [{"finish_reason": "length",
            "message": {"content": "partial"}}]}))
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream))
    args = SimpleNamespace(model="gpt-6.1-terra", council_model="gemini-3.8-flash-low",
                           base_url="http://localhost:4040/v1", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="completed"):
        caller.consult_council(args, "Original decision packet.")
    assert calls == ["gemini-3.8-flash-low"]


def test_council_retains_review_usage_if_primary_fails(monkeypatch):
    caller = load_caller()
    calls = []
    def upstream(request, **kwargs):
        model = json.loads(request.data)["model"]
        calls.append(model)
        finish = "stop" if len(calls) == 1 else "length"
        return io.StringIO(json.dumps({"model": model, "usage": {"total_tokens": 17},
            "choices": [{"finish_reason": finish, "message": {"content": "review"}}]}))
    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream))
    args = SimpleNamespace(model="gpt-6.1-terra", council_model="gemini-3.8-flash-low",
                           base_url="http://localhost:4040/v1", timeout_seconds=1)
    result = caller.consult_council(args, "Original decision packet.")
    assert result["status"] == "unavailable"
    assert "advice" not in result
    assert result["council"][0]["usage"]["total_tokens"] == 17
    assert calls == ["gemini-3.8-flash-low", "gpt-6.1-terra"]


@pytest.mark.parametrize("batches,expected_expert,expected_pi", [
    ([["q1", "q2", "q3"]], 2, 3),
    ([["q1"], ["q2", "q3"]], 3, 3),
    ([["q1"], ["q2"]], 3, 2),
])
def test_total_three_expert_three_pi_budget(source_repo, monkeypatch, batches, expected_expert, expected_pi):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    questions, calls = [], []
    def pi(package, snapshot, question, model, **kwargs):
        if not kwargs.get("preflight"):
            questions.append(question)
        return {"status": "ok", "evidence": evidence()}
    monkeypatch.setattr(reader, "run_pi", pi)
    def consult(args, messages):
        index = len(calls)
        calls.append(messages)
        answer = json.dumps({"read": batches[index]}) if index < len(batches) else "Verdict: enough.\nNext: Test.\nRisk: none"
        return {"advice": answer, "usage": {"total_tokens": 10}}
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "packet", consult, "final")
    assert result["status"] == "ok"
    assert len(calls) == expected_expert
    assert len(questions) == expected_pi


@pytest.mark.parametrize("batch", [["q"] * 2, ["q1", "q2", "q3", "q4"], []])
def test_invalid_or_repeat_batch_spends_no_pi_calls(source_repo, monkeypatch, batch):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    def pi(*args, **kwargs):
        assert kwargs.get("preflight"), "no inference allowed for invalid batch"
        return {"status": "ok"}
    monkeypatch.setattr(reader, "run_pi", pi)
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "packet", lambda *a: {"advice": json.dumps({"read": batch})}, "final")
    assert result["status"] == "unavailable"
    assert len(result["expert_calls"]) == 1


def test_preflight_failure_does_not_spend_expert_tokens(source_repo, monkeypatch):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    monkeypatch.setattr(reader, "run_pi", lambda *a, **kw: {"status": "unavailable"})
    def consult(*args):
        pytest.fail("Expert should not be called")
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra")
    result = reader.run_with_reader(args, "packet", consult, "instruction")
    assert result["status"] == "unavailable"
    assert result["expert_calls"] == []


@pytest.mark.parametrize("finish,content,exit_code", [
    ("stop", "Astra 建议 ✅", 0), ("length", "Astra 建议 ✅", 1),
    ("stop", "", 1), ("invalid_json", "", 1),
])
def test_real_cli_unicode_and_incomplete_response_boundary(finish, content, exit_code):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            if self.path.endswith(TOKEN_COUNT_SUFFIX):
                body = {"object": "response.input_tokens", "input_tokens": 9}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
                return
            body = {"choices": [{"finish_reason": finish, "message": {"content": content}}],
                    "model": "test-stub", "usage": {"total_tokens": 1}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"not JSON" if finish == "invalid_json" else
                             json.dumps(body, ensure_ascii=False).encode("utf-8"))
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    environment = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    environment.pop("EXPERTS_API_KEY", None)
    try:
        result = subprocess.run([sys.executable, str(CALLER), "--question", "test",
            "--base-url", f"http://127.0.0.1:{server.server_port}/v1"],
            env=environment, capture_output=True, timeout=10)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result.returncode == exit_code
    receipt = json.loads(result.stdout.decode("utf-8"))
    if exit_code == 0:
        assert receipt["advice"] == content
    else:
        assert receipt["status"] == "unavailable"
        assert "advice" not in receipt


def test_cli_image_input_reaches_stub_with_image_payload(tmp_path):
    sent, counted = [], []
    image = tmp_path / "view.png"
    data = (ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png").read_bytes()
    image.write_bytes(data)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            if self.path.endswith(TOKEN_COUNT_SUFFIX):
                counted.append(payload)
                response = {"object": "response.input_tokens", "input_tokens": 321}
            else:
                sent.append(payload)
                response = {"usage": {"total_tokens": 7}, "choices": [{"finish_reason": "stop",
                    "message": {"content": "Verdict: inspected.\nNext: verify.\nRisk: none"}}]}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    environment = dict(os.environ)
    environment.pop("EXPERTS_API_KEY", None)
    try:
        result = subprocess.run([sys.executable, "-B", str(CALLER), "--question", "Inspect both views.",
            "--image", str(image), "--image", str(image),
            "--base-url", f"http://127.0.0.1:{server.server_port}/v1"],
            env=environment, capture_output=True, timeout=10)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result.returncode == 0, result.stderr
    assert len(sent) == 1
    assert len(counted) == 1 and counted[0]["model"] == "gpt-6.1-terra"
    counted_images = counted[0]["input"][-1]["content"]
    assert [block["type"] for block in counted_images] == [
        "input_text", "input_text", "input_image", "input_text", "input_image"]
    assert json.loads(result.stdout)["input_tokens"] == 321
    assert sent[0]["model"] == "gpt-6.1-terra"
    assert sent[0]["reasoning_effort"] == "low"
    blocks = sent[0]["messages"][-1]["content"]
    assert blocks[0] == {"type": "text", "text": "Inspect both views."}
    images = [block["image_url"] for block in blocks if block["type"] == "image_url"]
    assert len(images) == 2
    assert all(base64.b64decode(item["url"].split(",", 1)[1]) == data for item in images)
    assert all(item["detail"] == "high" for item in images)
    receipt = json.loads(result.stdout)
    assert len(receipt["images"]) == 2
    assert receipt["images"][0]["sha256"] == hashlib.sha256(data).hexdigest()
    assert b"base64," not in result.stdout
    assert receipt["usage"]["total_tokens"] == 7


@pytest.mark.parametrize("bad", ["invalid", "missing", "oversized", "too_many", "total_bytes"])
def test_image_preflight_stops_before_provider(tmp_path, monkeypatch, bad):
    caller = load_caller()
    image = tmp_path / "view.png"
    image.write_bytes((ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png").read_bytes())
    paths = [image]
    if bad == "invalid":
        image.write_text("not an image")
    elif bad == "missing":
        paths = [tmp_path / "missing.png"]
    elif bad == "oversized":
        monkeypatch.setattr(caller, "MAX_IMAGE_BYTES", 4)
    elif bad == "too_many":
        paths *= caller.MAX_IMAGES + 1
    else:
        monkeypatch.setattr(caller, "MAX_TOTAL_IMAGE_BYTES", image.stat().st_size)
        paths *= 2
    monkeypatch.setattr(caller, "parse_args", lambda: SimpleNamespace(
        model="gpt-6.1-terra", question="Inspect", input_file=None, timeout_seconds=1,
        reader_scope=[], reader_root=None, image=paths, image_detail="high"))
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: pytest.fail("Invalid image spent a provider call"))
    assert caller.main() == 1


def test_reader_image_followup_uses_bounded_shared_call_path(
        source_repo, monkeypatch):
    caller, reader = load_caller(), load_reader()
    parts, _ = caller.prepare_images([ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png"])
    requests, questions = [], []
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)

    def pi(package, snapshot, question, model, **kwargs):
        if not kwargs.get("preflight"):
            questions.append(question)
            assert not list(snapshot.rglob("*.png"))
        return {"status": "ok", "evidence": evidence()}

    monkeypatch.setattr(reader, "run_pi", pi)
    detailed_advice = "Verdict: Visible defect.\nNext: " + "Specific repair. " * 120 + "\nRisk: none"

    def upstream(request, **kwargs):
        requests.append(json.loads(request.data))
        answer = json.dumps({"read": ["What does the approved source say about retries?"]}) if len(requests) == 1 else json.dumps({"advice": detailed_advice})
        return io.StringIO(json.dumps({"model": "fixture", "usage": {"total_tokens": 1},
            "choices": [{"finish_reason": "stop", "message": {"content": answer}}]}))

    monkeypatch.setattr(caller, "urlopen", with_token_counter(upstream))
    args = SimpleNamespace(model="gpt-6.1-terra", base_url="http://localhost:4040/v1", timeout_seconds=1,
        reader_root=source_repo, reader_scope=["src"], reader_model="gpt-6.1-terra", image_parts=parts)
    result = reader.run_with_reader(args, "Inspect the screenshot and check source if needed.",
                                    caller.consult, caller.VISUAL_INSTRUCTION)
    assert result["status"] == "ok"
    assert result["advice"] == detailed_advice
    assert len(requests) == 2 and len(questions) == 1
    for request in requests:
        blocks = request["messages"][-1]["content"]
        assert blocks[-1] == parts[-1]
        assert request["reasoning_effort"] == "low"
        assert request["messages"][0]["content"].count("One JSON object only") == 1
    assert "retries = 0" in requests[1]["messages"][-1]["content"][0]["text"]


def test_attaching_images_preserves_original_user_blocks():
    caller = load_caller()
    messages = [{"role": "user", "content": [{"type": "text", "text": "original"}]}]
    parts = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,fixture", "detail": "high"}}]
    attached = caller.with_images(messages, parts)
    assert attached[0]["content"] == [*messages[0]["content"], *parts]
    assert len(messages[0]["content"]) == 1


def test_caller_accepts_exact_model_names(monkeypatch):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--model", "gpt-6.1-terra",
                                       "--council-model", "gemini-3.8-flash-low", "--question", "test"])
    args = caller.parse_args()
    assert args.model == "gpt-6.1-terra"
    assert args.council_model == "gemini-3.8-flash-low"


def test_removed_council_shortcut_is_not_a_model_selection(monkeypatch):
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--council", "--question", "test"])
    with pytest.raises(SystemExit):
        caller.parse_args()


@pytest.mark.parametrize(("model", "council_model", "sonnet_model"), [
    ("gpt-6.1-terra", "gpt-6.1-terra", "Claude Sonnet 5.5 Medium"),
    ("gpt-6.1-terra", "gemini-3.8-flash-low", "gemini-3.8-flash-low"),
])
def test_council_requires_distinct_configured_routes(monkeypatch, model, council_model, sonnet_model):
    caller = load_caller()
    argv = [str(CALLER), "--model", model, "--question", "test"]
    if council_model:
        argv.extend(["--council-model", council_model])
    argv.extend(["--complexity", "very-complex", "--sonnet-model", sonnet_model])
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit, match="must differ"):
        caller.main()


def test_advisor_defaults_follow_requested_council(monkeypatch):
    for key in ("NORTHSTAR_ADVISOR_MODEL", "NORTHSTAR_COUNCIL_MODEL", "NORTHSTAR_SONNET_MODEL"):
        monkeypatch.delenv(key, raising=False)
    caller = load_caller()
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--question", "test"])
    args = caller.parse_args()
    assert args.model == "gpt-6.1-terra"
    assert args.council_model == "gemini-3.8-flash-low"
    assert args.sonnet_model == "Claude Sonnet 5.5 Medium"
    assert args.reader_model == "gpt-6.1-terra"


def test_very_complex_tier_calls_gemini_and_sonnet_then_terra(monkeypatch, capsys):
    caller = load_caller()
    requests, counts = [], []

    def upstream(request, **kwargs):
        payload = json.loads(request.data)
        requests.append(payload)
        return io.StringIO(json.dumps({"model": payload["model"], "usage": {"total_tokens": 1},
            "choices": [{"finish_reason": "stop", "message": {"content": "Review."}}]}))

    def routed(request, **kwargs):
        if request.full_url.endswith(TOKEN_COUNT_SUFFIX):
            counts.append(json.loads(request.data))
            return io.StringIO(json.dumps({"input_tokens": 10}))
        return upstream(request, **kwargs)

    monkeypatch.setattr(caller, "urlopen", routed)
    monkeypatch.setattr(sys, "argv", [str(CALLER), "--complexity", "very-complex",
        "--question", "Decide carefully.", "--base-url", "http://localhost:4040/v1"])
    assert caller.main() == 0
    assert [request["model"] for request in requests] == [
        "gemini-3.8-flash-low", "Claude Sonnet 5.5 Medium", "gpt-6.1-terra"]
    expected_models = ["gemini-3.8-flash-low", "Claude Sonnet 5.5 Medium", "gpt-6.1-terra"]
    assert [item["model"] for item in counts] == expected_models
    assert [item["model"] for item in requests] == expected_models
    assert all(request["reasoning_effort"] == "low" for request in requests)
    receipt = json.loads(capsys.readouterr().out)
    assert receipt.get("status", "ok") == "ok"
    assert len(receipt["council"]) == 3
