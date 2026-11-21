"""Exercise the Claude Advisor baseline without a provider account."""

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def evaluation_modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "eval"))


def test_native_report_separates_billed_model_usage_and_preserves_missing_receipts(tmp_path):
    from product_pilot_report import summarize

    result = tmp_path / "result.json"
    result.write_text(json.dumps({"task": "sort", "arm": "claude_native", "accepted": True,
                                  "turn": {"status": "end_turn"}}), encoding="utf-8")
    receipt = tmp_path / "receipts.jsonl"
    counts = {"input_tokens": 100, "output_tokens": 10,
              "cache_read_input_tokens": 20, "cache_creation_input_tokens": 0}
    data = {"model": "claude-sonnet-5", "usage": {**counts, "iterations": [
        {"type": "advisor_message", "model": "claude-opus-5-5", **counts}]}}
    receipt.write_text(json.dumps(data) + "\n", encoding="utf-8")
    row = summarize(result)
    assert row["total_tokens"] == 260
    assert row["api_equivalent_usd"] == pytest.approx(0.000908)
    data["usage"].pop("iterations")
    receipt.write_text(json.dumps(data) + "\n", encoding="utf-8")
    row = summarize(result)
    assert row["total_tokens"] is None and row["api_equivalent_usd"] is None


def test_spot_report_handles_an_interruption_before_the_first_request(tmp_path):
    from product_pilot_report import summarize

    result = tmp_path / "result.json"
    result.write_text(json.dumps({"task": "sort", "arm": "spot_advisor", "accepted": False,
                                  "turn": {"status": "executor_interrupted"}, "consultations": []}),
                      encoding="utf-8")
    row = summarize(result)
    assert row["executor"] == {"input_tokens": None, "output_tokens": None}
    assert row["total_tokens"] is None and row["api_equivalent_usd"] is None
