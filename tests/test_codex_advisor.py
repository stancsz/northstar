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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).parents[1]
CALLER = ROOT / "skills" / "codex-advisor" / "scripts" / "ask_expert.py"


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
def test_expert_controls_read_without_luna_history_or_retries(
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
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="current")
    result = reader.run_with_reader(args, "Luna hypothesis: broken retries.", consult, "Be concise.")
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
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="current")
    result = reader.run_with_reader(args, "packet", consult, "instruction")
    assert result["status"] == "unavailable"
    assert len(calls) == 1
    assert result["expert_calls"][0]["usage"]["total_tokens"] == 10


def test_incomplete_expert_is_not_advice(monkeypatch):
    caller = load_caller()
    body = {"choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}
    monkeypatch.setattr(caller, "urlopen", lambda *a, **k: io.StringIO(json.dumps(body)))
    args = SimpleNamespace(model="sol", base_url="http://localhost:4040/v1", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="completed"):
        caller.consult(args, [])


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
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="current")
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
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="current")
    result = reader.run_with_reader(args, "packet", lambda *a: {"advice": json.dumps({"read": batch})}, "final")
    assert result["status"] == "unavailable"
    assert len(result["expert_calls"]) == 1


def test_preflight_failure_does_not_spend_expert_tokens(source_repo, monkeypatch):
    reader = load_reader()
    monkeypatch.setattr(reader, "pi_package", lambda: source_repo)
    monkeypatch.setattr(reader, "run_pi", lambda *a, **kw: {"status": "unavailable"})
    def consult(*args):
        pytest.fail("Expert should not be called")
    args = SimpleNamespace(reader_root=source_repo, reader_scope=["src"], reader_model="current")
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


def test_cli_delivers_actual_images_with_text_and_safe_receipts(tmp_path):
    sent = []
    image = tmp_path / "view.png"
    data = (ROOT / "docs/evals/assets/qa-suite/A-narrow-viewport.png").read_bytes()
    image.write_bytes(data)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            sent.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"model": "image-test-stub", "usage": {"total_tokens": 7},
                "choices": [{"finish_reason": "stop", "message": {
                    "content": "Verdict: fixture.\nNext: inspect.\nRisk: none"}}]}).encode())

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
    assert sent[0]["model"] == "codex-gpt-6.1-sol-advisor"
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
    image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
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
        model="sol", question="Inspect", input_file=None, timeout_seconds=1,
        reader_scope=[], reader_root=None, image=paths, image_detail="high"))
    monkeypatch.setattr(caller, "urlopen", lambda *a, **kw: pytest.fail("Invalid image spent a provider call"))
    assert caller.main() == 1


def test_reader_keeps_image_pixels_on_followup_and_dispatches_its_own_question(
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

    monkeypatch.setattr(caller, "urlopen", upstream)
    args = SimpleNamespace(model="sol", base_url="http://localhost:4040/v1", timeout_seconds=1,
        reader_root=source_repo, reader_scope=["src"], reader_model="current", image_parts=parts)
    result = reader.run_with_reader(args, "Inspect the screenshot and check source if needed.",
                                    caller.consult, caller.VISUAL_INSTRUCTION)
    assert result["status"] == "ok", result
    assert result["advice"] == detailed_advice
    assert len(requests) == 2 and len(questions) == 1
    for request in requests:
        blocks = request["messages"][-1]["content"]
        assert blocks[-1] == parts[-1]
        assert request["messages"][0]["content"].count("One JSON object only") == 1
    assert "retries = 0" in requests[1]["messages"][-1]["content"][0]["text"]


def test_attaching_images_preserves_original_user_blocks():
    caller = load_caller()
    messages = [{"role": "user", "content": [{"type": "text", "text": "original"}]}]
    parts = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,fixture", "detail": "high"}}]
    attached = caller.with_images(messages, parts)
    assert attached[0]["content"] == [*messages[0]["content"], *parts]
    assert len(messages[0]["content"]) == 1


def test_caller_rejects_astra_instead_of_spending_or_falling_back():
    result = subprocess.run([sys.executable, "-B", str(CALLER), "--model", "astra", "--question", "test"],
                            capture_output=True, timeout=10)
    assert result.returncode == 2
    assert b"invalid choice" in result.stderr
    assert load_caller().MODEL_ALIASES == {"sol": "codex-gpt-6.1-sol-advisor"}
