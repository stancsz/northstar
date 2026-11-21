"""Summarize a checkpoint pilot without treating missing usage as zero."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from report import estimate, read_json, sum_known

ARMS = ("luna_only", "luna_advice", "astra_takeover")


def executor_receipts(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    latest = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        latest[row["attempt_id"]] = row
    return list(latest.values())


def summarize_pilot(root: Path) -> list[dict]:
    rows = []
    for manifest in sorted(root.glob("*/checkpoint-summary.json")):
        case = manifest.parent
        prefix = executor_receipts(case / "prefix.jsonl")
        for arm in read_json(manifest)["order"]:
            folder = case / arm
            path = folder / "result.json"
            if not path.is_file():
                continue
            result = read_json(path)
            receipts = prefix + executor_receipts(folder / "attempts.jsonl")
            receipts.extend(attempt for consultation in result["consultations"]
                            for attempt in consultation["attempts"] if attempt["dispatch_possible"])
            usage = [receipt.get("usage") or {} for receipt in receipts]
            by_model = {}
            for receipt, counts in zip(receipts, usage):
                model = receipt.get("model") or "unattributed"
                by_model.setdefault(model, []).append(counts)
            rows.append({
                "task": case.name, "arm": arm, "accepted": result["accepted"],
                "input_tokens": sum_known(item.get("input_tokens") for item in usage) if usage else None,
                "output_tokens": sum_known(item.get("output_tokens") for item in usage) if usage else None,
                "api_equivalent_usd": sum_known(
                    estimate(receipt) if receipt.get("usage") else None for receipt in receipts
                ) if receipts else None,
                "observed_usage_attempts": sum(
                    item.get("input_tokens") is not None and item.get("output_tokens") is not None
                    for item in usage
                ),
                "attempts": len(receipts),
                "usage_by_model": {
                    model: {
                        "input_tokens": sum_known(item.get("input_tokens") for item in counts),
                        "output_tokens": sum_known(item.get("output_tokens") for item in counts),
                        "attempts": len(counts),
                    }
                    for model, counts in sorted(by_model.items())
                },
                "advisor_statuses": [call["status"] for call in result["consultations"]],
            })
    return rows


def matched_summary(rows: list[dict], planned: tuple[str, ...] = ()) -> dict:
    by_task = {}
    for row in rows:
        by_task.setdefault(row["task"], {})[row["arm"]] = row
    complete = {
        task: arms for task, arms in by_task.items()
        if all(arm in arms and type(arms[arm]["accepted"]) is bool for arm in ARMS)
    }
    totals = {}
    for arm in ARMS:
        cohort = [arms[arm] for arms in complete.values()]
        accepted = sum(row["accepted"] for row in cohort)
        tokens = sum_known(sum_known([row["input_tokens"], row["output_tokens"]]) for row in cohort)
        cost = sum_known(row["api_equivalent_usd"] for row in cohort)
        frontier_tokens = []
        for row in cohort:
            usage = row["usage_by_model"]
            if "unattributed" in usage:
                frontier_tokens.append(None)
                continue
            astra = usage.get("gpt-6.2-astra", {"input_tokens": 0, "output_tokens": 0})
            frontier_tokens.append(sum_known([astra["input_tokens"], astra["output_tokens"]]))
        frontier = sum_known(frontier_tokens)
        totals[arm] = {
            "accepted": accepted,
            "total_tokens_per_verified_task": tokens / accepted if accepted and tokens is not None else None,
            "astra_tokens_per_verified_task": frontier / accepted if accepted and frontier is not None else None,
            "api_equivalent_usd_per_verified_task": cost / accepted if accepted and cost is not None else None,
        }
    return {
        "complete_tasks": sorted(complete),
        "incomplete_tasks_with_results": sorted(by_task.keys() - complete.keys()),
        "planned_tasks_without_results": sorted(set(planned) - by_task.keys()),
        "arms": totals,
        "advice_only_passes": sum(arms["luna_advice"]["accepted"] and not arms["luna_only"]["accepted"]
                                  for arms in complete.values()),
        "luna_only_passes_against_advice": sum(arms["luna_only"]["accepted"] and not arms["luna_advice"]["accepted"]
                                              for arms in complete.values()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--matched", action="store_true", help="Report only complete three-arm comparisons.")
    args = parser.parse_args()
    rows = summarize_pilot(args.run)
    plan = args.run / "pilot-plan.json"
    planned = tuple(read_json(plan)["cases"]) if plan.is_file() else ()
    if args.matched:
        summary = matched_summary(rows, planned)
        dispositions = {
            path.parent.name: read_json(path)
            for path in sorted(args.run.glob("*/result.json"))
        }
        summary["prefix_dispositions"] = dispositions
        summary["planned_tasks_without_results"] = [
            task for task in summary["planned_tasks_without_results"] if task not in dispositions
        ]
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(rows, indent=2))
