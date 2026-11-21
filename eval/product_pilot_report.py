"""Report completed product pilot arms from their persisted receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from checkpoint_report import executor_receipts
from report import estimate, read_json, sum_known

# Standard rates in USD per million, from the Claude Platform pricing table.
CLAUDE_PRICES = {
    "claude-sonnet-5": (2, 10, 0.20, 2.50, 4),
    "claude-opus-5-5": (4, 20, 0.20, 5, 8),
}


def claude_estimate(model: str | None, usage: dict) -> float | None:
    prices = CLAUDE_PRICES.get(model)
    inputs, outputs, reads, writes = (usage.get(field) for field in (
        "input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
    ))
    if prices is None or None in (inputs, outputs, reads, writes):
        return None
    creation = usage.get("cache_creation") or {}
    short = creation.get("ephemeral_5m_input_tokens", 0)
    long = creation.get("ephemeral_1h_input_tokens", 0)
    if short + long != writes:
        return None
    return sum(count * price for count, price in zip((inputs, outputs, reads, short, long), prices)) / 1e6


def token_totals(usage: list[dict], *, separate_cache: bool = False) -> dict:
    input_fields = ["input_tokens"]
    if separate_cache:
        input_fields.extend(["cache_read_input_tokens", "cache_creation_input_tokens"])
    return {
        "input_tokens": sum_known(sum_known(row.get(field) for field in input_fields) for row in usage),
        "output_tokens": sum_known(row.get("output_tokens") for row in usage),
    }


def summarize(path: Path) -> dict:
    result = read_json(path)
    folder = path.parent
    if result["arm"] == "claude_native":
        receipts = [json.loads(line) for line in (folder / "receipts.jsonl").read_text(encoding="utf-8").splitlines()]
        executor = [receipt.get("usage") or {} for receipt in receipts]
        advisor = [item for usage in executor for item in (usage.get("iterations") or [])
                   if item.get("type") == "advisor_message"]
        executor_totals = token_totals(executor, separate_cache=True)
        advisor_totals = token_totals(advisor, separate_cache=True)
        if not receipts:
            executor_totals = advisor_totals = {"input_tokens": None, "output_tokens": None}
        elif any(not isinstance(usage.get("iterations"), list) for usage in executor):
            advisor_totals = {"input_tokens": None, "output_tokens": None}
        cost = None
        if receipts and advisor_totals["input_tokens"] is not None:
            cost = sum_known([
                *(claude_estimate(receipt.get("model"), usage) for receipt, usage in zip(receipts, executor)),
                *(claude_estimate(item.get("model"), item) for item in advisor),
            ])
    else:
        executor = executor_receipts(folder / "executor-attempts.jsonl")
        advisor = [attempt for call in result["consultations"] for attempt in call["attempts"]
                   if attempt["dispatch_possible"]]
        executor_totals = token_totals([receipt.get("usage") or {} for receipt in executor])
        advisor_totals = token_totals([receipt.get("usage") or {} for receipt in advisor])
        if not executor:
            executor_totals = {"input_tokens": None, "output_tokens": None}
        cost = sum_known(estimate(receipt) if receipt.get("usage") else None
                         for receipt in executor + advisor) if executor else None
    usage_complete = result["turn"]["status"] in {"completed", "end_turn", "max_tokens"}
    return {
        "task": result["task"], "arm": result["arm"], "accepted": result["accepted"],
        "executor": executor_totals, "advisor": advisor_totals, "turn_status": result["turn"]["status"],
        "total_tokens": sum_known([*executor_totals.values(), *advisor_totals.values()]) if usage_complete else None,
        "api_equivalent_usd": cost if usage_complete else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    print(json.dumps([summarize(path) for path in sorted(args.run.glob("*/*/result.json"))], indent=2))
