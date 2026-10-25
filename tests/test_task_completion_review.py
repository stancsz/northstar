"""Offline protocol/runner tests; these do not prove a live host resumed."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/task-completion-review/scripts/guard_stop.py"
spec = importlib.util.spec_from_file_location("completion_guardian", SCRIPT)
guardian = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guardian)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.delenv(guardian.CHILD_MARKER, raising=False)
    brief = tmp_path / "brief.md"
    brief.write_text("Deliver the corrected local artifact. Existing grant: choose and execute ordinary remedies. No publishing or new credentials.", encoding="utf-8")
    args = SimpleNamespace(brief=brief, repo=tmp_path, state_dir=tmp_path / "state",
                           review_budget=8, timeout=5, codex=sys.executable)
    event = {"hook_event_name": "Stop", "session_id": "test-session", "stop_hook_active": False,
             "last_assistant_message": "The source passes, but the package is old."}
    return args, event


def verdict(disposition="continue", evidence="Artifact hash A; package hash B", action="Produce and verify the current package"):
    return {"disposition": disposition, "reason": "The required outcome is reconciled against current evidence",
            "next_action": action if disposition in {"continue", "verified-wait"} else "",
            "evidence": evidence, "reopening_condition": "Next verified result" if disposition in {"blocked", "verified-wait"} else ""}


@pytest.mark.parametrize("disposition", ["complete", "blocked", "verified-wait", "user-stop"])
def test_terminal_dispositions_preserve_their_distinction(setup, disposition):
    args, event = setup
    output = guardian.review_stop(event, args, lambda *_: verdict(disposition))
    assert "decision" not in output
    assert f": {disposition}." in output["systemMessage"]
    if disposition != "complete":
        assert ": complete." not in output["systemMessage"]
    if disposition == "verified-wait":
        assert "Next check:" in output["systemMessage"]


def test_already_continued_and_new_investigation_continue_without_a_diff(setup):
    args, event = setup
    event["stop_hook_active"] = True
    for fact in ["A supported lookup locates the resource", "A minimal check narrows the failure", "A new fact excludes the earlier hypothesis"]:
        output = guardian.review_stop(event, args, lambda *_: verdict(evidence=fact))
        assert output["decision"] == "block"
    assert not list(args.repo.glob("*.py"))  # Progress did not require editing source.


def test_unchanged_evidence_gets_one_remedy_checkpoint_then_disclosed_suspension(setup):
    args, event = setup
    first = guardian.review_stop(event, args, lambda *_: verdict())
    second = guardian.review_stop(event, args, lambda *_: verdict())
    third = guardian.review_stop(event, args, lambda *_: verdict())
    assert first["decision"] == second["decision"] == "block"
    assert "different bounded authorized remedy" in second["reason"]
    assert "decision" not in third
    assert "no-progress suspension" in third["systemMessage"]
    assert "not a verified external dependency or completion" in third["systemMessage"]


def test_explicit_budget_does_not_certify_success_or_call_reviewer_again(setup):
    args, event = setup
    args.review_budget = 1
    assert guardian.review_stop(event, args, lambda *_: verdict())["decision"] == "block"
    output = guardian.review_stop(event, args, lambda *_: pytest.fail("Budget exhausted"))
    assert "guard-budget stop" in output["systemMessage"]
    assert "not certified complete" in output["systemMessage"]


def test_session_budgets_are_separate_and_recursion_or_interrupt_never_resumes(setup, monkeypatch):
    args, event = setup
    args.review_budget = 1
    guardian.review_stop(event, args, lambda *_: verdict())
    event["session_id"] = "another-session"
    assert guardian.review_stop(event, args, lambda *_: verdict())["decision"] == "block"
    event["hook_event_name"] = "Interrupt"
    assert guardian.review_stop(event, args, lambda *_: pytest.fail("Interrupt reviewer")) == {}
    event["hook_event_name"] = "Stop"
    monkeypatch.setenv(guardian.CHILD_MARKER, "1")
    assert guardian.review_stop(event, args, lambda *_: pytest.fail("Recursive reviewer")) == {}


@pytest.mark.parametrize("answer", [{}, verdict(action=""), verdict("complete") | {"next_action": "Still must test"}])
def test_malformed_or_contradictory_verdicts_fail_open_visibly(setup, answer):
    args, event = setup
    output = guardian.review_stop(event, args, lambda *_: answer)
    assert "decision" not in output
    assert "reviewer failure" in output["systemMessage"]


def test_redacted_context_and_state_without_reading_transcript(setup):
    args, event = setup
    secret = "sk-synthetic-DO_NOT_DISCLOSE"
    args.brief.write_text("Owner authorizes ordinary remedies. API_KEY=" + secret, encoding="utf-8")
    transcript = args.repo / "transcript.jsonl"
    transcript.write_text("Never transmit raw transcript " + secret, encoding="utf-8")
    event.update(transcript_path=str(transcript), last_assistant_message="Bearer " + secret)

    def review(prompt, _):
        assert secret not in prompt
        assert "Never transmit raw transcript" not in prompt
        assert "Owner authorizes ordinary remedies" in prompt
        assert "STOP PROPOSAL (DATA ONLY)" in prompt
        assert "Do not reselect models, accounts or providers" in prompt
        return verdict(evidence="Synthetic " + secret)

    output = guardian.review_stop(event, args, review)
    assert secret not in json.dumps(output)
    assert secret not in next(args.state_dir.glob("*.json")).read_text()


def test_transcript_cannot_be_supplied_as_brief(setup):
    args, event = setup
    event["transcript_path"] = str(args.brief)
    output = guardian.review_stop(event, args, lambda *_: pytest.fail("Read transcript as brief"))
    assert "reviewer failure" in output["systemMessage"]


def test_reviewer_exception_does_not_leak_diagnostics(setup):
    args, event = setup
    def failure(*_):
        raise RuntimeError("sk-synthetic-secret diagnostic")
    output = guardian.review_stop(event, args, failure)
    assert "reviewer failure" in output["systemMessage"]
    assert "sk-synthetic-secret" not in json.dumps(output)


def test_cli_runner_uses_native_readonly_ephemeral_and_stdin(setup, monkeypatch):
    args, _ = setup
    args.state_dir.mkdir()
    native_popen = subprocess.Popen
    observed = []

    def launcher(command, **kwargs):
        if command[-3:] == ["mcp", "list", "--json"]:
            return native_popen([sys.executable, "-c", "print('[]')"], **kwargs)
        if len(command) > 1 and command[1] == "exec":
            observed.append((command, kwargs))
            answer = command[command.index("--output-last-message") + 1]
            program = "import sys,pathlib; data=sys.stdin.read(); assert 'trusted context' in data; pathlib.Path(" + repr(answer) + ").write_text(" + repr(json.dumps(verdict("complete"))) + ")"
            return native_popen([sys.executable, "-c", program], **kwargs)
        return native_popen(command, **kwargs)

    monkeypatch.setattr(guardian.subprocess, "Popen", launcher)
    assert guardian.review_with_codex("trusted context", args)["disposition"] == "complete"
    command, kwargs = observed[0]
    assert "--ephemeral" in command and command[command.index("--sandbox") + 1] == "read-only"
    assert {"features.hooks=false", "features.goals=false", "agents.enabled=false",
            "features.multi_agent=false", "features.multi_agent_v2=false",
            "features.apps=false", "features.plugins=false", "features.browser_use=false",
            "features.computer_use=false", "features.memories=false", "hooks={}"} <= set(command)
    assert "--model" not in command and command[-1] == "-"
    assert not kwargs["shell"] and kwargs["env"][guardian.CHILD_MARKER] == "1"
    assert kwargs["stdout"] == kwargs["stderr"] == subprocess.DEVNULL
    if os.name == "nt":
        assert kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
    assert not list(args.state_dir.iterdir())


def process_running(pid):
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        status = Path(f"/proc/{pid}/stat")
        return not status.exists() or status.read_text().split()[2] != "Z"
    except ProcessLookupError:
        return False


def test_timeout_stops_owned_native_reviewer_and_descendant(setup, monkeypatch):
    args, event = setup
    args.timeout = 1
    pid_file = args.repo / "owned-child.pid"
    native_popen = subprocess.Popen
    owned = []

    def launcher(command, **kwargs):
        if command[-3:] == ["mcp", "list", "--json"]:
            return native_popen([sys.executable, "-c", "print('[]')"], **kwargs)
        if len(command) > 1 and command[1] == "exec":
            program = (
                "import subprocess,sys,time,pathlib; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],"
                "creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); "
                "pathlib.Path(" + repr(str(pid_file)) + ").write_text(str(child.pid)); time.sleep(30)"
            )
            process = native_popen([sys.executable, "-c", program], **kwargs)
            owned.append(process)
            return process
        return native_popen(command, **kwargs)

    monkeypatch.setattr(guardian.subprocess, "Popen", launcher)
    started = time.monotonic()
    output = guardian.review_stop(event, args)
    assert time.monotonic() - started < 12, "Timeout must include waiting for a child that never reads stdin"
    assert "reviewer timeout" in output["systemMessage"]
    assert owned[0].poll() is not None
    assert pid_file.exists(), "Descendant fixture must actually launch before timeout"
    child_pid = int(pid_file.read_text())
    deadline = time.monotonic() + 3
    while process_running(child_pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not process_running(child_pid)


@pytest.mark.parametrize("budget_args", [[], ["--review-budget", "0"], ["--review-budget", "-1"]])
def test_bad_hook_configuration_is_nonblocking_json_not_continuation_exit_two(setup, budget_args):
    args, event = setup
    command = [sys.executable, "-B", str(SCRIPT), "--brief", str(args.brief),
               "--repo", str(args.repo), "--state-dir", str(args.state_dir), *budget_args]
    result = subprocess.run(command, input=json.dumps(event), capture_output=True,
                            text=True, encoding="utf-8", shell=False, timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert result.returncode == 0, "Exit 2 would request an unintended Stop continuation"
    output = json.loads(result.stdout)
    assert "configuration failure" in output["systemMessage"]
    assert "decision" not in output and not result.stderr
    assert not args.state_dir.exists(), "Configuration failure must not start a reviewer"


def test_manual_help_remains_available():
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"],
                            capture_output=True, text=True, encoding="utf-8", shell=False,
                            timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert result.returncode == 0
    assert "--review-budget" in result.stdout and not result.stderr


def inventory_launcher(monkeypatch, inventories, observed):
    native_popen = subprocess.Popen
    replies = iter(inventories)

    def launcher(command, **kwargs):
        observed.append((command, kwargs))
        if command[-3:] == ["mcp", "list", "--json"]:
            response = next(replies)
            text = response if isinstance(response, str) else json.dumps(response)
            program = "import sys; sys.stdout.write(" + repr(text) + ")"
        elif command[1] == "exec":
            answer = command[command.index("--output-last-message") + 1]
            program = "import pathlib; pathlib.Path(" + repr(answer) + ").write_text(" + repr(json.dumps(verdict("complete"))) + ")"
        else:
            return native_popen(command, **kwargs)
        return native_popen([sys.executable, "-c", program], **kwargs)

    monkeypatch.setattr(guardian.subprocess, "Popen", launcher)


def test_effective_mcp_names_disabled_literally_and_values_never_forwarded(setup, monkeypatch):
    import tomllib
    args, event = setup
    names = ['server.with.dots', 'quote" . spaces; $(unsafe)', 'already-disabled']
    secret = "sk-synthetic-INVENTORY_ONLY"
    first = [{"name": name, "enabled": index < 2,
              "transport": {"env": {"API_KEY": secret}, "headers": {"Authorization": secret}}}
             for index, name in enumerate(names)]
    second = [{"name": name, "enabled": False} for name in names]
    observed = []
    inventory_launcher(monkeypatch, [first, second], observed)
    output = guardian.review_stop(event, args)
    assert ": complete." in output["systemMessage"]
    assert len(observed) == 3
    verify, review = observed[1][0], observed[2][0]
    override = 'mcp_servers={' + ','.join(json.dumps(name, ensure_ascii=False) + '={enabled=false}' for name in names[:2]) + '}'
    assert override in verify and override in review
    assert tomllib.loads(override) == {"mcp_servers": {name: {"enabled": False} for name in names[:2]}}
    assert not any(item.startswith('mcp_servers.') for item in verify + review)
    assert all(not kwargs["shell"] for _, kwargs in observed)
    assert secret not in json.dumps(review) + json.dumps(output)
    assert secret not in next(args.state_dir.glob("*.json")).read_text()
    for command, _ in observed[:2]:
        assert {"features.apps=false", "features.plugins=false", "features.hooks=false"} <= set(command)


@pytest.mark.parametrize("inventories", [
    [[{"name": "still-enabled", "enabled": True}], [{"name": "still-enabled", "enabled": True}]],
    [[{"name": "missing-on-verify", "enabled": True}], []],
    [[{"name": "duplicate", "enabled": True}, {"name": "duplicate", "enabled": False}]],
    [[{"name": "no-state"}]],
    [[{"name": "wrong-state", "enabled": "false"}]],
    [{"not": "an inventory"}],
    ["malformed sk-synthetic-INVENTORY_ONLY"],
])
def test_ambiguous_or_enabled_inventory_prevents_reviewer_without_leaking(setup, monkeypatch, inventories):
    args, event = setup
    observed = []
    inventory_launcher(monkeypatch, inventories, observed)
    output = guardian.review_stop(event, args)
    assert "containment failure" in output["systemMessage"]
    assert "decision" not in output and "sk-synthetic" not in json.dumps(output)
    assert not any(command[1] == "exec" for command, _ in observed)


def test_preflights_share_review_deadline_and_do_not_launch_model_after_timeout(setup, monkeypatch):
    args, event = setup
    args.timeout = 0.4
    native_popen = subprocess.Popen
    observed = []

    def launcher(command, **kwargs):
        if command[-3:] == ["mcp", "list", "--json"]:
            observed.append(command)
            return native_popen([sys.executable, "-c", "import time; time.sleep(.25); print('[]')"], **kwargs)
        assert len(command) < 2 or command[1] != "exec", "Deadline expired before model launch"
        return native_popen(command, **kwargs)

    monkeypatch.setattr(guardian.subprocess, "Popen", launcher)
    started = time.monotonic()
    output = guardian.review_stop(event, args)
    assert "reviewer timeout" in output["systemMessage"]
    assert len(observed) <= 2 and time.monotonic() - started < 3


@pytest.mark.parametrize("failure", ["reviewer-launch", "reviewer-exit", "missing-answer", "oversized-answer", "malformed-structured-answer", "invalid-verdict"])
def test_reviewer_phase_failures_are_distinguishable_without_raw_diagnostics(setup, monkeypatch, failure):
    args, event = setup
    secret = "sk-synthetic-PRIVATE_DIAGNOSTIC"

    def run(command, *unused, **kwargs):
        if command[-3:] == ["mcp", "list", "--json"]:
            return 0, "[]"
        if failure == "reviewer-launch":
            raise OSError(secret)
        if failure == "reviewer-exit":
            return 17, secret
        answer = Path(command[command.index("--output-last-message") + 1])
        if failure == "oversized-answer":
            answer.write_text(secret + "x" * 32001, encoding="utf-8")
        elif failure == "malformed-structured-answer":
            answer.write_text(secret, encoding="utf-8")
        elif failure == "invalid-verdict":
            answer.write_text(json.dumps({"private": secret}), encoding="utf-8")
        return 0, secret

    monkeypatch.setattr(guardian, "run_cli", run)
    output = guardian.review_stop(event, args)
    assert "reviewer failure [" + failure in output["systemMessage"]
    if failure == "reviewer-exit":
        assert "exit 17" in output["systemMessage"]
    assert "decision" not in output and secret not in json.dumps(output)
    assert "No completion verdict" in output["systemMessage"]


def test_unavailable_native_and_preflight_launch_have_distinct_safe_remedies(setup, monkeypatch):
    args, event = setup
    args.codex = str(args.repo / "missing-native.exe")
    output = guardian.review_stop(event, args)
    assert "reviewer failure [unavailable-native]" in output["systemMessage"]
    event["session_id"] = "preflight-failure"
    args.codex = sys.executable
    def failed_launch(*unused, **kwargs):
        raise OSError("sk-synthetic-PRIVATE_DIAGNOSTIC")
    monkeypatch.setattr(guardian, "run_cli", failed_launch)
    output = guardian.review_stop(event, args)
    assert "containment failure [preflight-launch]" in output["systemMessage"]
    assert "No reviewer launched" in output["systemMessage"]
    assert "sk-synthetic" not in json.dumps(output) and "decision" not in output


@pytest.mark.parametrize("selected", [None, "provider/reviewer-route"])
def test_model_selection_is_optional_exact_and_only_on_reviewer_exec(setup, monkeypatch, selected):
    args, event = setup
    args.model = selected
    observed = []
    inventory_launcher(monkeypatch, [[], []], observed)
    output = guardian.review_stop(event, args)
    assert ": complete." in output["systemMessage"]
    for command, _ in observed[:2]:
        assert "--model" not in command
    command = observed[2][0]
    assert command.count("--model") == (0 if selected is None else 1)
    if selected is not None:
        assert command[command.index("--model") + 1] == selected
    assert not any(item.startswith("model=") for item in command)
    assert not any(item in command for item in ["--profile", "--oss", "--local-provider"])


def test_selected_model_failure_never_retries_or_reselects(setup, monkeypatch):
    args, event = setup
    args.model = "provider/reviewer-route"
    observed = []
    def run(command, *unused, **kwargs):
        observed.append(command)
        return (0, "[]") if command[-3:] == ["mcp", "list", "--json"] else (1, "")
    monkeypatch.setattr(guardian, "run_cli", run)
    output = guardian.review_stop(event, args)
    assert "reviewer-exit (exit 1)" in output["systemMessage"]
    assert len(observed) == 3 and sum(command[1] == "exec" for command in observed) == 1
    assert "decision" not in output


@pytest.mark.parametrize("identifier", ["bad model", "model;$(unsafe)", "sk-synthetic-PRIVATE"])
def test_model_identifier_rejects_shell_fragments_and_secret_shapes(identifier):
    with pytest.raises(ValueError):
        guardian.model_identifier(identifier)


@pytest.mark.parametrize("identifier", ["default", "provider/model-id", "vendor/model:revision"])
def test_model_identifier_accepts_supported_route_shapes(identifier):
    assert guardian.model_identifier(identifier) == identifier


@pytest.fixture
def event_setup(setup):
    args, stop = setup
    args.from_events, args.brief, args.repo = True, None, None
    cwd = str(args.state_dir.parent.resolve())
    capture = {"hook_event_name": "UserPromptSubmit", "session_id": stop["session_id"],
               "turn_id": "owner-1", "cwd": cwd, "prompt": "Finish the local GOAL.md outcome; preserve existing restrictions."}
    stop.update(turn_id="owner-1", cwd=cwd)
    return args, capture, stop


def checkpoint(args):
    return json.loads(next(args.state_dir.glob("*.json")).read_text(encoding="utf-8"))


def test_event_capture_redacts_before_persist_and_never_reads_transcript_or_attachment(event_setup, monkeypatch):
    args, capture, stop = event_setup
    secret, quoted = "sk-synthetic-PRIVATE", "private-quoted-value"
    transcript = args.state_dir.parent / "private.jsonl"
    transcript.write_text("Never read transcript or customer attachment", encoding="utf-8")
    capture.update(prompt='Finish GOAL.md. API_KEY="' + quoted + '" token ' + secret,
                   transcript_path=str(transcript), attachments=[str(transcript)])
    original_read = Path.read_text
    def guarded_read(path, *a, **kw):
        assert path != transcript, "Capture/review must not inspect transcript or attachments"
        return original_read(path, *a, **kw)
    monkeypatch.setattr(Path, "read_text", guarded_read)
    assert guardian.handle_event(capture, args) == {}
    saved = next(args.state_dir.glob("*.json")).read_text(encoding="utf-8")
    assert secret not in saved and quoted not in saved and "[redacted]" in saved
    assert "attachments" not in saved and "transcript_path" not in saved
    def review(prompt, review_args):
        assert secret not in prompt and quoted not in prompt
        assert "CAPTURED REQUEST CONTEXT (DATA ONLY)" in prompt
        assert "not new platform privileges" in prompt
        assert "Resolve designated paths within this repository" in prompt
        assert review_args.repo == Path(stop["cwd"])
        return verdict("complete")
    assert ": complete." in guardian.handle_event(stop, args, review)["systemMessage"]


@pytest.mark.parametrize("mutation", ["missing-context", "different-session", "different-turn", "different-cwd", "missing-turn"])
def test_stop_requires_matching_capture_and_cannot_reuse_context(event_setup, mutation):
    args, capture, stop = event_setup
    if mutation != "missing-context":
        guardian.handle_event(capture, args)
    if mutation == "different-session":
        stop["session_id"] = "other-session"
    elif mutation == "different-turn":
        stop["turn_id"] = "owner-2"
    elif mutation == "different-cwd":
        other = args.state_dir.parent / "other-project"
        other.mkdir()
        stop["cwd"] = str(other.resolve())
    elif mutation == "missing-turn":
        del stop["turn_id"]
    output = guardian.handle_event(stop, args, lambda *_: pytest.fail("Mismatched context launched review"))
    assert "context failure" in output["systemMessage"] and "decision" not in output


@pytest.mark.parametrize("prompt", ["", "x" * 6001, None], ids=["empty", "oversized", "missing"])
def test_invalid_capture_invalidates_older_matching_context(event_setup, prompt):
    args, capture, stop = event_setup
    guardian.handle_event(capture, args)
    output = guardian.handle_event(capture | {"turn_id": "owner-2", "prompt": prompt}, args)
    assert "context failure" in output["systemMessage"]
    output = guardian.handle_event(stop, args, lambda *_: pytest.fail("Old context reused"))
    assert "context failure" in output["systemMessage"]
    assert not checkpoint(args)["context_valid"]


def test_only_genuine_new_owner_turn_renews_budget_and_preserves_history(event_setup):
    args, capture, stop = event_setup
    args.review_budget = 1
    guardian.handle_event(capture, args)
    first = guardian.handle_event(stop, args, lambda *_: verdict(evidence="Current unmet result"))
    assert first["decision"] == "block"
    guardian.handle_event(capture, args)  # Duplicate capture is not a new human turn.
    output = guardian.handle_event(stop | {"stop_hook_active": True}, args, lambda *_: pytest.fail("Budget reset"))
    assert "guard-budget stop" in output["systemMessage"]
    before = checkpoint(args)
    assert before["reviews"] == 1 and before["failure_counts"]["guard-budget"] == 1
    newer = capture | {"turn_id": "owner-2", "prompt": "Also keep the existing deployment restriction."}
    guardian.handle_event(newer, args)
    after = checkpoint(args)
    assert after["reviews"] == 0
    for field in ["last_evidence", "last_action", "failure_counts", "route_history", "evidence_hash"]:
        assert after[field] == before[field]
    assert after["event_context"]["original_request"] == capture["prompt"]
    assert after["event_context"]["current_request"] == newer["prompt"]
    def review(prompt, *_):
        assert "Current unmet result" in prompt and "guard-budget" in prompt
        assert newer["prompt"] in prompt and capture["prompt"] in prompt
        return verdict(evidence="New verified investigation")
    assert guardian.handle_event(stop | {"turn_id": "owner-2"}, args, review)["decision"] == "block"
    assert "context failure" in guardian.handle_event(capture, args)["systemMessage"]  # Old turn cannot reset again.


def test_event_failure_and_selected_route_survive_new_owner_request(event_setup):
    args, capture, stop = event_setup
    args.model = "provider/reviewer-route"
    guardian.handle_event(capture, args)
    def failed(*_):
        raise guardian.ReviewerError("reviewer-exit", 1)
    output = guardian.handle_event(stop, args, failed)
    assert "reviewer-exit" in output["systemMessage"]
    guardian.handle_event(capture | {"turn_id": "owner-2", "prompt": "Continue within the existing limits."}, args)
    saved = checkpoint(args)
    assert saved["reviews"] == 0 and saved["failure_counts"]["reviewer-exit"] == 1
    assert saved["route_history"][-1]["model"] == "provider/reviewer-route"


def test_event_context_is_bounded_and_original_request_survives(event_setup):
    args, capture, _ = event_setup
    for index in range(5):
        assert guardian.handle_event(capture | {"turn_id": f"owner-{index}", "prompt": f"Request {index}"}, args) == {}
    saved = checkpoint(args)["event_context"]
    assert saved["original_request"] == "Request 0"
    assert [item["request"] for item in saved["recent"]] == ["Request 3", "Request 4"]
    assert saved["omitted_requests"] == 2


def test_child_marker_and_interrupt_skip_both_event_capture_and_review(event_setup, monkeypatch):
    args, capture, stop = event_setup
    monkeypatch.setenv(guardian.CHILD_MARKER, "1")
    for event in [capture, stop]:
        assert guardian.handle_event(event, args, lambda *_: pytest.fail("Child reviewer")) == {}
    assert not args.state_dir.exists()
    monkeypatch.delenv(guardian.CHILD_MARKER)
    assert guardian.handle_event(stop | {"hook_event_name": "Interrupt"}, args) == {}
    assert not args.state_dir.exists()


def test_event_cli_capture_needs_no_direct_brief_or_repo(event_setup):
    args, capture, _ = event_setup
    command = [sys.executable, "-B", str(SCRIPT), "--from-events", "--state-dir", str(args.state_dir), "--review-budget", "3"]
    result = subprocess.run(command, input=json.dumps(capture), capture_output=True, text=True,
                            encoding="utf-8", shell=False, timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert result.returncode == 0 and json.loads(result.stdout) == {} and not result.stderr
    assert checkpoint(args)["event_context"]["turn_id"] == capture["turn_id"]
    result = subprocess.run(command + ["--repo", capture["cwd"]], input=json.dumps(capture),
                            capture_output=True, text=True, encoding="utf-8", shell=False, timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    assert result.returncode == 0 and "configuration failure" in json.loads(result.stdout)["systemMessage"]



def test_two_project_sessions_keep_request_and_artifact_context_isolated(event_setup):
    args, capture, stop = event_setup
    guardian.handle_event(capture, args)
    other = args.state_dir.parent / "second-project"
    other.mkdir()
    second_capture = capture | {"session_id": "second-session", "cwd": str(other.resolve()), "prompt": "Second project: inspect local result.md only."}
    assert guardian.handle_event(second_capture, args) == {}
    def first_review(prompt, review_args):
        assert capture["prompt"] in prompt and second_capture["prompt"] not in prompt
        assert review_args.repo == Path(capture["cwd"])
        return verdict("complete")
    assert ": complete." in guardian.handle_event(stop, args, first_review)["systemMessage"]
    def second_review(prompt, review_args):
        assert second_capture["prompt"] in prompt and capture["prompt"] not in prompt
        assert review_args.repo == other.resolve()
        return verdict("complete")
    second_stop = stop | {"session_id": "second-session", "cwd": str(other.resolve())}
    assert ": complete." in guardian.handle_event(second_stop, args, second_review)["systemMessage"]


def test_changed_text_under_same_turn_invalidates_capture_without_budget_reset(event_setup):
    args, capture, stop = event_setup
    guardian.handle_event(capture, args)
    guardian.handle_event(stop, args, lambda *_: verdict())
    output = guardian.handle_event(capture | {"prompt": "Different instruction with reused turn identity"}, args)
    assert "context failure [conflicting-turn]" in output["systemMessage"]
    assert checkpoint(args)["reviews"] == 1 and not checkpoint(args)["context_valid"]
