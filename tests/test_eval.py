"""Regressions for verification, paired accounting, and task sampling."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def eval_modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "eval"))


def test_resume_at_a_complete_tool_batch_without_replaying_tools(monkeypatch):
    from direct_session import DirectSession

    session = DirectSession.__new__(DirectSession)
    handled = []
    responses = iter([
        {"id": "prefix", "output": [
            {"type": "reasoning", "encrypted_content": "opaque"},
            {"type": "function_call", "call_id": "check", "name": "verify_checkpoint", "arguments": "{}"},
            {"type": "function_call", "call_id": "read", "name": "run_command", "arguments": "{}"},
        ]},
        {"id": "continued", "output": []},
    ])
    requests = []

    def request(model, effort, messages, tools, deadline):
        requests.append(list(messages))
        return next(responses)

    def handle(call):
        handled.append(call["tool"])
        return {"ok": False}

    monkeypatch.setattr(session, "request", request)
    prompt = [{"role": "user", "content": "Fix the task"}]
    state = session.continue_run("luna", "max", prompt, [], handle, 1,
                                 stop_after_batch=lambda: bool(handled))
    assert state["status"] == "checkpoint"
    assert state["messages"][1]["encrypted_content"] == "opaque"
    assert [item["call_id"] for item in state["messages"][-2:]] == ["check", "read"]
    assert len(prompt) == 1
    outcome = session.continue_run("luna", "max", state["messages"], [], handle, 1)
    assert outcome == {"turn_id": "continued", "status": "completed"}
    assert requests[1] == state["messages"]
    assert handled == ["verify_checkpoint", "run_command"]


def test_native_advisor_pause_preserves_server_blocks_and_executes_only_client_tools():
    from claude_native_session import run_native

    pending = {"type": "server_tool_use", "id": "advisor", "name": "advisor", "input": {}}
    advice = {"type": "advisor_tool_result", "tool_use_id": "advisor", "content": "example"}
    check = {"type": "tool_use", "id": "check", "name": "verify_checkpoint", "input": {}}
    responses = iter([
        {"content": [pending], "stop_reason": "pause_turn"},
        {"content": [advice, check], "stop_reason": "tool_use",
         "usage": {"iterations": [{"type": "advisor_message", "input_tokens": 10, "output_tokens": 5}]}},
        {"content": [], "stop_reason": "end_turn"},
    ])
    requests = []
    calls = []

    def send(payload, timeout):
        requests.append(list(payload["messages"]))
        return next(responses)

    def handle(call):
        calls.append(call)
        return {"ok": True}

    result = run_native(send, "Fix the task", [], handle, lambda: 10)
    assert requests[1][-1] == {"role": "assistant", "content": [pending]}
    assert requests[2][-2]["content"] == [advice, check]
    assert requests[2][-1]["content"][0]["tool_use_id"] == "check"
    assert calls == [{"tool": "verify_checkpoint", "arguments": {}}]
    assert result["receipts"][1]["usage"]["iterations"][0]["type"] == "advisor_message"
    assert result["status"] == "end_turn"


def test_formal_manifest_has_disjoint_pilot_and_stratified_holdout():
    manifest = json.loads((ROOT / "eval/swe_tasks.json").read_text(encoding="utf-8"))
    pilot = {row["id"] for row in manifest["pilot"]}
    formal = {row["id"] for row in manifest["formal"]}
    assert len(pilot) == 3 and len(formal) == 50
    assert pilot.isdisjoint(formal)
    assert len({row["repository"] for row in manifest["formal"]}) == 11
    assert {row["hard51"] for row in manifest["formal"]} == {True, False}


def test_confirmed_browser_state_allows_reading_saved_record():
    from run import browser_accepted
    from suites import browser_tasks

    task = browser_tasks(pilot=True)[0]
    requested = task.browser["selected_ids"][0]
    assert not browser_accepted(task, {"records": task.browser["initial"], "selected": requested, "preview": True})
    assert browser_accepted(task, {"records": task.browser["expected"], "selected": requested, "preview": False})


def test_sandbox_enforces_timeout_inside_container(monkeypatch):
    import sandbox

    observed = {}

    def capture(*args, timeout, data):
        observed.update(args=args, timeout=timeout, data=data)

    monkeypatch.setattr(sandbox, "docker", capture)
    workspace = sandbox.Sandbox("fixture")
    workspace.container = "test-container"
    workspace.exec("sleep 60", timeout=1.5)
    assert observed["args"][-7:] == ("timeout", "-k", "3", "2", "/bin/sh", "-c", "sleep 60")
    assert observed["timeout"] > 2


def test_repeated_check_triggers_even_if_output_changes(monkeypatch, tmp_path):
    from run import TaskExecution
    from suites import pilot_diagnostics

    class Workspace:
        def __init__(self):
            self.runs = 0

        def exec(self, command, timeout):
            self.runs += 1
            return subprocess.CompletedProcess(command, 1, f"Failed after {self.runs} seconds".encode(), b"")

    state = TaskExecution(pilot_diagnostics()[1], "spot_advisor", Workspace(), tmp_path, float("inf"))
    monkeypatch.setattr(state, "revision", lambda: "r1")
    seen = []
    monkeypatch.setattr(state, "consult", lambda reason, *_: seen.append(reason) or "\nAdvice")
    state.verify(command="python -m unittest")
    assert seen == []
    state.verify(command="python -m unittest")
    assert seen == ["two_failed_checks"]


def test_diagnostic_grader_rejects_the_starting_artifact(tmp_path):
    from suites import diagnostic_tasks, pilot_diagnostics

    cases = diagnostic_tasks()
    assert len(cases) == 16
    for task in [*cases, *pilot_diagnostics()]:
        folder = tmp_path / task.id
        folder.mkdir()
        for name, source in task.inputs.items():
            (folder / name).write_text(source, encoding="utf-8")
        for source in (task.inputs["check.py"], task.grader):
            checked = subprocess.run([sys.executable, "-B", "-c", source], cwd=folder, capture_output=True)
            assert checked.returncode != 0, task.id
            assert b"AssertionError" in checked.stderr or checked.returncode == 78, (
                task.id, checked.stderr.decode(errors="replace"),
            )


def _study_row(arm, accepted, tokens):
    model = "gpt-6.2-astra" if arm == "astra_only" else "gpt-6-luna"
    return {
        "arm": arm, "accepted": accepted, "agent_seconds": 1, "verdict": "passed" if accepted else "verifier_failed",
        "reroutes": [], "consultations": [],
        "executor_attempts": [{"model": model, "requested_model": model,
                               "usage": {"input_tokens": tokens, "output_tokens": 1,
                                         "cached_input_tokens": 0, "cache_write_input_tokens": 0}}],
    }


def test_report_counts_failed_runs_and_preserves_unknown_usage():
    from report import summarize

    success = _study_row("astra_only", True, 12)
    failure = _study_row("astra_only", False, 4)
    assert summarize([success, failure])["astra_tokens_per_accepted"] == 18
    failure["executor_attempts"][0]["usage"]["input_tokens"] = None
    assert summarize([success, failure])["astra_tokens_per_accepted"] is None
    assert summarize([_study_row("astra_only", False, 5)])["astra_tokens_per_accepted"] is None
    assert summarize([_study_row("spot_advisor", True, 5)])["astra_tokens_per_accepted"] == 0


def test_replay_uses_the_recorded_revision_and_duration():
    from report import replay

    advice = {"status": "ok", "revision": "a", "elapsed_seconds": 3.0, "number": 1}
    spot = {"task_id": "case", "consultations": [advice]}
    row = replay([(spot, {})], 2.0)[0]
    assert row["scenario_overlap_seconds"] == 2.0
    assert row["accept_at_original_revision"]
    assert not row["accept_after_revision_change"]


def test_deadline_crossover_charges_late_and_unsuccessful_attempts():
    from report import deployment_analysis

    def row(arm, passed, tokens, seconds):
        return {**_study_row(arm, passed, tokens - 1), "wall_seconds": seconds}

    pairs = [(row("spot_advisor", True, 600, 120), row("astra_only", True, 90, 60)),
             (row("spot_advisor", True, 300, 500), row("astra_only", False, 10, 75))]
    data = deployment_analysis(pairs, 12, [300], .8, .1)
    early, unlimited = data["windows"]
    assert early["timely_passes"] == {"spot_advisor": 1, "astra_only": 1}
    assert early["crossover"] == pytest.approx(100 / 900)
    assert early["weighted_spot_per_timely"] == pytest.approx(90)
    assert early["crossover_ci95"] is None
    assert unlimited["timely_passes"]["spot_advisor"] == 2
    assert unlimited["crossover"] == pytest.approx(200 / 900)
    assert unlimited["meets_observed_target"] == {"spot_advisor": True, "astra_only": False}
    assert data["acceptance"]["wins"] == 1 and data["acceptance"]["difference"] == .5
    del pairs[0][0]["executor_attempts"][0]["usage"]
    unknown = deployment_analysis(pairs, 12, [300], .8, .1)["windows"][0]
    assert unknown["timely_passes"] == early["timely_passes"]
    assert unknown["crossover"] is None and unknown["weighted_spot_per_timely"] is None
    assert unknown["frontier_per_timely_baseline"] == 100
    assert unknown["unknown_balance_at_equality"] == pytest.approx(70)


def test_local_rejection_is_counted_separately_from_a_dispatched_reply():
    from report import summarize

    row = _study_row("spot_advisor", True, 10)
    row["consultations"] = [{"attempts": [], "status": "unavailable", "advice_applied": True,
                             "next_check_passed": True}]
    data = summarize([row])
    assert data["consultation_triggers"] == data["triggers_without_dispatch"] == 1
    assert data["consultations"] == data["tasks_with_consultation"] == data["advice_applied"] == 0
