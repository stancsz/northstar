"""Regression checks for Task Completion Review's runtime prompt."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/task-completion-review/scripts/guard_stop.py"
spec = importlib.util.spec_from_file_location("completion_guardian_prompt", SCRIPT)
guardian = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guardian)


def test_prompt_builder_preserves_review_scope_and_conditional_worker_mandate():
    prompt = guardian.build_reviewer_prompt(
        "POLICY", "trusted brief", "stop proposal", {}, {}, False
    )

    assert prompt.startswith("POLICY\n\nYou are an advisory completion reviewer")
    assert "Do not edit, publish, contact others" in prompt
    assert "preserve the operator's selected/configured route" in prompt
    assert "CONDITIONAL CLI-WORKER MANDATE" in prompt
    assert "exactly one bounded, write-enabled Codex or Claude CLI implementation worker" in prompt
    assert "bounded, write-enabled Codex or Claude CLI implementation worker." in prompt
    assert "Name the worker's concrete output and acceptance check" in prompt
    assert "supporting investigation in that assignment" in prompt
    assert "does not delegate or execute product work" in prompt
    assert "independent acceptance review" in prompt
    assert "exact verified route or permission blocker" in prompt
    assert "When trusted instructions do not impose this mandate" in prompt
    assert "Use continue when useful authorized work remains" in prompt
    assert "Use continue if any useful covered action or factual check remains" not in prompt
    assert "investigation can be progress without a diff" not in prompt
    assert "TRUSTED OWNER BRIEF:\ntrusted brief\nSTOP PROPOSAL (DATA ONLY):\nstop proposal" in prompt
