"""Generate reproducible statistical summaries and LaTeX from paired run records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
from pathlib import Path

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve().parent
ARMS = ("spot_advisor", "astra_only")
ASTRA = "gpt-6.2-astra"
LABELS = {"spot_advisor": "Luna Max + Astra", "astra_only": "Astra only"}
EXPECTED_FORMAL = {"swe-bench-pro-v2": 50, "diagnostic": 16, "chromium": 8}
SUITE_LABELS = {"swe-bench-pro-v2": "SWE-bench Pro V2", "diagnostic": "Diagnostic", "chromium": "Chromium"}
BILLING = json.loads((HERE / "pricing.json").read_text(encoding="utf-8"))
SCHEMA = Draft202012Validator(json.loads((HERE / "telemetry_schema.json").read_text(encoding="utf-8")))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def advisor_requests(row: dict) -> list[dict]:
    return [attempt for call in row["consultations"] for attempt in call["attempts"]
            if attempt["dispatch_possible"]]


def requests(row: dict) -> list[dict]:
    return [*row["executor_attempts"], *advisor_requests(row)]


def sum_known(values) -> int | float | None:
    parts = list(values)
    return None if any(value is None for value in parts) else sum(parts)


def request_tokens(receipt: dict) -> int | None:
    usage = receipt.get("usage") or {}
    return sum_known(usage.get(key) for key in ("input_tokens", "output_tokens"))


def estimate(receipt: dict) -> float | None:
    pricing = BILLING["models"].get(receipt.get("model"))
    usage = receipt["usage"]
    tokens = [usage.get(key) for key in ("input_tokens", "output_tokens", "cached_input_tokens",
                                        "cache_write_input_tokens")]
    if pricing is None or any(count is None for count in tokens):
        return None
    inputs, outputs, read, write = tokens
    if read + write > inputs:
        return None
    input_weight, output_weight = (2, 1.5) if inputs > BILLING["long_input_threshold"] else (1, 1)
    return (input_weight * ((inputs - read - write) * pricing["input"] + read * pricing["cache_read"]
                             + write * pricing["cache_write"]) + output_weight * outputs * pricing["output"]) / 1e6


def clean(row: dict) -> dict:
    """Export reproducible measurements without provider IDs, account windows or tool text."""
    copy = dict(row)
    copy.pop("error", None)
    copy.update(quota_before=None, quota_after=None,
                turn={k: v for k, v in row["turn"].items() if k == "status"})
    receipt_fields = {"attempt_id", "consultation_id", "requested_model", "model", "reasoning_effort", "status", "usage",
                      "elapsed_seconds", "dispatch_possible", "estimated_input_tokens", "transport"}
    def public_attempt(attempt: dict) -> dict:
        return {k: v for k, v in attempt.items() if k in receipt_fields}
    copy["executor_attempts"] = [public_attempt(a) for a in row["executor_attempts"]]
    copy["consultations"] = [{**c, "attempts": [public_attempt(a) for a in c["attempts"]]}
                             for c in row["consultations"]]
    copy["tool_events"] = [
        {key: event[key] for key in ("tool", "elapsed_seconds", "browser_action", "ok") if key in event}
        for event in row["tool_events"]
    ]
    return copy


def load_pairs(folder: Path) -> tuple[dict, list, list]:
    manifest = read_json(folder / "manifest.json")
    if manifest["stage"] == "formal" and "exclusions" not in manifest:
        marked = []
        for item in read_json(HERE / "formal-exclusions.json"):
            markers = [folder / item["task_id"] / arm / "exclusion.json" for arm in ARMS]
            if any(p.exists() for p in markers):
                for arm, path in zip(ARMS, markers):
                    row = read_json(path)
                    if (row.get("task_id"), row.get("arm"), row.get("status")) != (
                            item["task_id"], arm, "excluded_before_execution"):
                        raise ValueError("An exclusion marker differs from the registered disposition.")
                marked.append(item)
        if marked:
            manifest["exclusions"] = marked
    if len({t["task_id"] for t in manifest["tasks"]}) != len(manifest["tasks"]):
        raise ValueError("The run manifest contains duplicate tasks.")
    exported = folder / "evidence.jsonl"
    published = {}
    if exported.is_file():
        for line in exported.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            receipt = json.loads(line)
            key = (receipt["task_id"], receipt["arm"])
            if key in published:
                raise ValueError(f"Duplicate exported record: {key}")
            published[key] = receipt
    rows, pairs = [], []
    for task in manifest["tasks"]:
        outcomes = {}
        for arm in ARMS:
            path = folder / task["task_id"] / arm / "result.json"
            receipt = published.pop((task["task_id"], arm), None)
            if path.is_file():
                row = read_json(path)
            elif receipt is not None:
                row = receipt
            else:
                continue
            SCHEMA.validate(row)
            if (row["schema_version"] != 2 or row["task_id"] != task["task_id"] or row["arm"] != arm
                    or row["stage"] != manifest["stage"] or row["suite"] != task["suite"]
                    or row["seed"] != manifest["seed"] or row["git_commit"] != manifest["git_commit"]
                    or row["source_sha256"] != manifest["source_sha256"]
                    or row["executor_model"] != manifest["settings"][arm][0]
                    or row["executor_effort"] != manifest["settings"][arm][1]):
                raise ValueError(f"Run record differs from the pinned manifest: {path}")
            if (row["advisor_model"] != (ASTRA if arm == "spot_advisor" else None)
                    or any(a["requested_model"] != row["executor_model"] or a["reasoning_effort"] != row["executor_effort"]
                    for a in row["executor_attempts"])
                    or any(a["requested_model"] != ASTRA or a["reasoning_effort"] != "medium"
                           or arm != "spot_advisor" for a in advisor_requests(row))):
                raise ValueError(f"Attempt differs from the pinned workflow: {path}")
            for attempt in requests(row):
                counts = (attempt.get("usage") or {}).values()
                if any(value is not None and (type(value) is not int or value < 0) for value in counts):
                    raise ValueError(f"Invalid token count in {path}")
            if type(row["accepted"]) is not bool or row["agent_seconds"] < 0:
                raise ValueError(f"Invalid outcome in {path}")
            outcomes[arm] = row
            rows.append(row)
        if len(outcomes) == 2:
            pairs.append((outcomes[ARMS[0]], outcomes[ARMS[1]]))
    if published:
        raise ValueError("The exported records include tasks or arms outside the manifest.")
    return manifest, rows, pairs


def fully_observed(row: dict) -> bool:
    receipts = requests(row)
    return (
        not row["reroutes"] and row["verdict"] not in {"infrastructure_error", "model_rerouted"} and bool(receipts)
        and bool(row["executor_attempts"]) and all(request_tokens(r) is not None for r in receipts)
        and all(r.get("model") == r["requested_model"] for r in receipts)
    )


def frontier_tokens(row: dict) -> int | None:
    receipts = requests(row)
    # A missing resolved model or dispatch receipt prevents attribution.
    if not fully_observed(row):
        return None
    return sum_known(request_tokens(r) for r in receipts if r["model"] == ASTRA)


def per_success(values: list, passed: int) -> float | None:
    total = sum_known(values)
    return total / passed if total is not None and passed else None


def summarize(rows: list[dict]) -> dict:
    passes = sum(row["accepted"] for row in rows)
    all_tokens = [sum_known(request_tokens(r) for r in requests(row)) if fully_observed(row) else None
                  for row in rows]
    costs = [sum_known(estimate(r) for r in requests(row)) if fully_observed(row) else None for row in rows]
    latencies = [row["agent_seconds"] for row in rows]
    advice = [call for row in rows for call in row["consultations"]]
    adopted = [call for call in advice if call["status"] == "ok" and call["advice_applied"] is True]
    return {
        "n": len(rows), "accepted": passes, "astra_tokens_per_accepted": per_success(
            [frontier_tokens(row) for row in rows], passes,
        ),
        "total_tokens_per_accepted": per_success(all_tokens, passes),
        "api_equivalent_usd_per_accepted": per_success(costs, passes),
        "median_agent_seconds": statistics.median(latencies) if latencies else None,
        "p95_agent_seconds": percentile(latencies, 0.95) if latencies else None,
        "consultation_triggers": len(advice), "advice_applied": len(adopted),
        "consultations": sum(len(advisor_requests(row)) for row in rows),
        "tasks_with_consultation": sum(bool(advisor_requests(row)) for row in rows),
        "usable_advice": sum(call["status"] == "ok" for call in advice),
        "triggers_without_dispatch": sum(not any(a["dispatch_possible"] for a in call["attempts"]) for call in advice),
        "advice_applied_and_next_check_passed": sum(call["next_check_passed"] is True for call in adopted),
        "usage_complete": sum(fully_observed(row) for row in rows),
    }


def percentile(numbers: list, quantile: float) -> float:
    ordered = sorted(numbers)
    position = quantile * (len(ordered) - 1)
    first = int(position)
    last = min(len(ordered) - 1, first + 1)
    return ordered[first] + (ordered[last] - ordered[first]) * (position - first)


def wilson(count: int, n: int) -> tuple[float, float]:
    # Bonferroni adjustment for the two discordant-proportion intervals.
    z = 2.2414027276
    proportion = count / n
    scale = 1 + z**2 / n
    center = (proportion + z**2 / (2 * n)) / scale
    radius = z * math.sqrt((proportion * (1 - proportion) + z**2 / (4 * n)) / n) / scale
    return max(0, center - radius), min(1, center + radius)


def acceptance_effect(pairs: list) -> dict:
    wins = sum(a["accepted"] and not b["accepted"] for a, b in pairs)
    losses = sum(b["accepted"] and not a["accepted"] for a, b in pairs)
    n = len(pairs)
    lo_a, hi_a = wilson(wins, n)
    lo_b, hi_b = wilson(losses, n)
    count = wins + losses
    pvalue = min(1., 2. * sum(math.comb(count, i) for i in range(min(wins, losses) + 1)) / 2**count)
    return {"difference": (wins - losses) / n, "difference_ci95": [lo_a - hi_b, hi_a - lo_b],
            "wins": wins, "losses": losses, "exact_mcnemar_p": pvalue}


def effects(pairs: list, seed: int) -> dict:
    n = len(pairs)
    result = {**acceptance_effect(pairs), "astra_ratio_ci95": None}
    points = [(a["accepted"], b["accepted"], frontier_tokens(a), frontier_tokens(b)) for a, b in pairs]
    if all(a is not None and b is not None for _, _, a, b in points):
        bootstrap = []
        rng = random.Random(seed)
        for _ in range(10_000):
            sa, sb, ta, tb = map(sum, zip(*rng.choices(points, k=n)))
            if sa and sb and tb:
                bootstrap.append((ta / sa) / (tb / sb))
        if len(bootstrap) == 10_000:
            result["astra_ratio_ci95"] = [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)]
    return result


def join_accepts(call: dict, revision: str) -> bool:
    return call["status"] == "ok" and call["revision"] == revision


def replay(pairs: list, independent_seconds: float) -> list[dict]:
    """Model an explicitly supplied independent-work interval using observed advisor durations."""
    return [
        {"task_id": a["task_id"], "consultation": call["number"], "observed_advisor_seconds": call["elapsed_seconds"],
         "scenario_independent_seconds": independent_seconds,
         "scenario_overlap_seconds": min(independent_seconds, call["elapsed_seconds"]),
         "accept_at_original_revision": join_accepts(call, call["revision"]),
         "accept_after_revision_change": join_accepts(
             call, hashlib.sha256((call["revision"] + ":changed").encode()).hexdigest(),
         )}
        for a, _ in pairs for call in a["consultations"] if call["status"] == "ok"
    ]


def display(number, digits: int = 0) -> str:
    return "--" if number is None else f"{number:,.{digits}f}"


def crossover(spot_passes, baseline_passes, spot_frontier, spot_luna, baseline_frontier):
    """Relative Luna weight at equal weighted tokens per timely verified patch."""
    if not spot_passes or not baseline_passes or not spot_luna:
        return None
    return (baseline_frontier * spot_passes / baseline_passes - spot_frontier) / spot_luna


def received_capacity(rows: list[dict]) -> dict:
    observed = {ASTRA: 0, "gpt-6-luna": 0}
    missing = 0
    for row in rows:
        for receipt in requests(row):
            model = receipt.get("model")
            count = request_tokens(receipt)
            if model in observed and model == receipt["requested_model"] and count is not None:
                observed[model] += count
            else:
                missing += 1
    return {"astra_tokens": observed[ASTRA], "luna_tokens": observed["gpt-6-luna"],
            "unattributed_requests": missing}


def deployment_analysis(pairs: list, seed: int, deadlines: list, target: float, weight: float) -> dict:
    """Retrospectively score all spend, including late runs, against verified wall time."""
    terms = []
    for spot, baseline in pairs:
        frontier = frontier_tokens(spot)
        luna = (sum(request_tokens(a) for a in spot["executor_attempts"]) if frontier is not None else None)
        terms.append((frontier, luna, frontier_tokens(baseline)))
    totals = [sum_known(values) for values in zip(*terms)] if terms else [None] * 3
    received = {arm: received_capacity([pair[i] for pair in pairs]) for i, arm in enumerate(ARMS)}
    known_spend = [received[arm]["astra_tokens"] + weight * received[arm]["luna_tokens"] for arm in ARMS]
    windows = []
    for deadline in [*deadlines, None]:
        on_time = [(a["accepted"] and (deadline is None or a["wall_seconds"] <= deadline),
                    b["accepted"] and (deadline is None or b["wall_seconds"] <= deadline)) for a, b in pairs]
        passes = [sum(col) for col in zip(*on_time)] if pairs else [0, 0]
        spot, base = passes
        frontier, luna, baseline = totals
        window = {"deadline_seconds": deadline, "timely_passes": dict(zip(ARMS, passes)),
                  "meets_observed_target": {arm: bool(pairs) and n / len(pairs) >= target
                                            for arm, n in zip(ARMS, passes)},
                  "frontier_per_timely_spot": per_success([frontier], spot),
                  "luna_per_timely_spot": per_success([luna], spot),
                  "frontier_per_timely_baseline": per_success([baseline], base),
                  "crossover": None, "crossover_ci95": None, "bootstrap_defined": 0,
                  "weighted_spot_per_timely": None, "unknown_balance_at_equality": None}
        if spot and frontier is not None and luna is not None:
            window["weighted_spot_per_timely"] = (frontier + weight * luna) / spot
        if all(t is not None for t in totals):
            window["crossover"] = crossover(spot, base, frontier, luna, baseline)
        if spot and base and any(received[arm]["unattributed_requests"] for arm in ARMS):
            # U_T - (s_T/s_B) U_B at equality, without assigning zero to a lost receipt.
            window["unknown_balance_at_equality"] = known_spend[1] * spot / base - known_spend[0]
        if window["crossover"] is not None:
            rng = random.Random(seed)
            samples = [(*success, *counts) for success, counts in zip(on_time, terms)]
            estimates = []
            for _ in range(10_000):
                selected = rng.choices(samples, k=len(samples))
                value = crossover(*map(sum, zip(*selected)))
                if value is not None:
                    estimates.append(value)
            window["bootstrap_defined"] = len(estimates)
            if len(estimates) == 10_000:
                window["crossover_ci95"] = [percentile(estimates, q) for q in (0.025, 0.975)]
        windows.append(window)
    return {"pairs": len(pairs), "target": target, "relative_luna_weight": weight, "received": received,
            "acceptance": acceptance_effect(pairs) if pairs else None, "windows": windows}


def deployment_latex(report: dict) -> str:
    decision = report["deployment"]
    n = decision["pairs"]
    lines = [r"\begin{tabular}{lrrrr}", r"\toprule",
             r"Verified by & Luna + Astra & Astra only & Break-even $w$ & Paired 95\% interval \\", r"\midrule"]
    for window in decision["windows"]:
        seconds = window["deadline_seconds"]
        label = f"{seconds:g} s" if seconds is not None else "Any time"
        left, right = (window["timely_passes"][arm] for arm in ARMS)
        ci = window["crossover_ci95"]
        interval = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci is not None else "--"
        lines.append(f"{label} & {left}/{n} & {right}/{n} & {display(window['crossover'], 3)} & {interval} "
                     + r"\\")
    return "\n".join([*lines, r"\bottomrule", r"\end{tabular}"]) + "\n"


def deployment_plot(report: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    study = report["deployment"]
    windows = study["windows"]
    figure, axes = plt.subplots(1, len(windows), figsize=(max(4, 2.1 * len(windows)), 2.45),
                                squeeze=False, sharey=True, layout="constrained")
    for ax, window in zip(axes[0], windows):
        frontier = window["frontier_per_timely_spot"]
        luna = window["luna_per_timely_spot"]
        baseline = window["frontier_per_timely_baseline"]
        if baseline is not None:
            ax.axhline(baseline / 1000, color="#9b451d", linestyle="--", linewidth=1.6)
        if frontier is not None and luna is not None:
            ax.plot([0, 1], [frontier / 1000, (frontier + luna) / 1000], color="#115672", linewidth=2)
        else:
            message = ("No timely Luna pass" if not window["timely_passes"][ARMS[0]] else "Usage incomplete")
            ax.text(.5, .77, message, transform=ax.transAxes, ha="center", fontsize=8)
        crossing = window["crossover"]
        if crossing is not None and 0 <= crossing <= 1:
            ax.plot(crossing, baseline / 1000, "o", color="#282828", ms=4)
        d = window["deadline_seconds"]
        eligible = [arm for arm in ARMS if window["meets_observed_target"][arm]]
        qualifies = {(): "neither", (ARMS[0],): "Luna + Astra", (ARMS[1],): "Astra only", ARMS: "both"}[tuple(eligible)]
        title = f"{d:g} s" if d is not None else "Any time"
        ax.set_title(f"{title}\n{study['target']:.0%} target: {qualifies}", fontsize=8.5)
        ax.set(xlim=(0, 1), ylim=(0, None), xticks=[0, .5, 1])
        ax.tick_params(labelsize=8)
        ax.grid(axis="y", alpha=.18)
    axes[0][0].set_ylabel("Weighted tokens / timely pass (k)", fontsize=8)
    figure.supxlabel("Weight of a Luna token relative to one Astra token", fontsize=9)
    handles = [plt.Line2D([], [], color="#115672", label=LABELS[ARMS[0]]),
               plt.Line2D([], [], color="#9b451d", linestyle="--", label=LABELS[ARMS[1]])]
    figure.legend(handles=handles, loc="outside upper center", ncols=2, frameon=False, fontsize=8)
    figure.savefig(output, metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)


def latex(metrics: dict) -> str:
    lines = [r"\begin{tabular}{llrrrrr}", r"\toprule",
             r"Suite & Arm & Pass & Usage$^*$ & Astra/pass & Total/pass & Agent s \\ ", r"\midrule"]
    for suite, data in metrics["suites"].items():
        for index, arm in enumerate(ARMS):
            item = data[arm]
            name = SUITE_LABELS[suite] if index == 0 else ""
            lines.append(
                f"{name} & {LABELS[arm]} & {item['accepted']}/{item['n']} & {item['usage_complete']}/{item['n']} & "
                f"{display(item['astra_tokens_per_accepted'])} & {display(item['total_tokens_per_accepted'])} & "
                f"{display(item['median_agent_seconds'], 1)} " + r"\\"
            )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    if metrics["suites"]:
        counts = [
            f"{SUITE_LABELS[suite]} {group[ARMS[0]]['tasks_with_consultation']}/{group[ARMS[0]]['n']}"
            for suite, group in metrics["suites"].items()
        ]
        lines.append("\n\n" + r"\footnotesize $^*$Runs with complete, attributable token usage. "
                     + "A consultation was dispatched on these treatment runs (" + ", ".join(counts) + ").")
    if metrics["formal_complete"]:
        effect = metrics["primary_effect"]
        ci = effect["difference_ci95"]
        ratio = effect["astra_ratio_ci95"]
        lines.append(f"\n\nPrimary pass-rate difference: {100 * effect['difference']:.1f} pp "
                     f"(paired 95\\% interval [{100 * ci[0]:.1f}, {100 * ci[1]:.1f}] pp).")
        if ratio:
            lines.append(f"Astra token ratio per accepted task: paired 95\\% interval [{ratio[0]:.3f}, {ratio[1]:.3f}].")
    return "\n".join(lines) + "\n"


def coding_findings(report: dict, public_pairs: list) -> tuple[str, str]:
    public = report["suites"].get("swe-bench-pro-v2")
    if not public:
        return "This build contains no paired public coding tasks.", ""
    spot, baseline = (public[arm] for arm in ARMS)
    n = spot["n"]
    headline = (f"On {n} paired public issues, the independent grader accepted {spot['accepted']} patches "
                f"with Luna and optional Astra advice and {baseline['accepted']} with Astra alone.")
    both = [(a, b) for a, b in public_pairs if a["accepted"] and b["accepted"]]
    if both:
        faster = sum(b["wall_seconds"] < a["wall_seconds"] for a, b in both)
        if faster == len(both):
            headline += (f" On all {len(both)} issues that both workflows passed, the Astra run took less "
                         "time from setup through final grading.")
        else:
            headline += f" Astra took less time on {faster} of the {len(both)} issues that both workflows passed."
    headline += f" Luna called the advisor on {spot['tasks_with_consultation']} of the {n} public issues."
    if min(spot["usage_complete"], baseline["usage_complete"]) < n:
        headline += (f" Complete token receipts cover {spot['usage_complete']}/{n} and "
                     f"{baseline['usage_complete']}/{n} runs, respectively. "
                     "Missing receipts leave the primary resource comparison unresolved.")
    else:
        headline += (f" Median agent time was {display(spot['median_agent_seconds'])} and "
                     f"{display(baseline['median_agent_seconds'])} seconds, respectively.")
    detail = (f"The executor reached {spot['consultation_triggers']} eligible checkpoints and dispatched "
              f"{spot['consultations']} advisor calls across {spot['tasks_with_consultation']} of the {n} tasks. "
              f"The executor reported applying {spot['advice_applied']} usable replies. "
              f"The next recorded check passed after {spot['advice_applied_and_next_check_passed']} of them.")
    skipped = spot["triggers_without_dispatch"]
    if skipped:
        detail += f" {skipped} eligible checkpoint{'s' if skipped != 1 else ''} ended before dispatch."
    if spot["consultations"] == 0:
        detail += " These tasks measure executor substitution without any delivered advice."
    incomplete = [[p[i] for p in public_pairs if p[i]["verdict"] == "incomplete_turn"] for i in range(2)]
    if any(incomplete):
        luna, astra = incomplete
        detail += (f" Execution ended without a completed final turn on {len(luna)} Luna runs "
                   f"and {len(astra)} Astra runs. The recovered patches still passed grading in "
                   f"{sum(r['accepted'] for r in luna)} and {sum(r['accepted'] for r in astra)} "
                   "of those runs, respectively.")
    return headline, detail


def paired_interpretation(report: dict, pairs: list) -> str:
    decision = report["deployment"]
    if not pairs:
        return ""
    n = len(pairs)
    e = decision["acceptance"]
    both = sum(a["accepted"] and b["accepted"] for a, b in pairs)
    neither = n - both - e["wins"] - e["losses"]
    lo, hi = e["difference_ci95"]
    return (
        f"Both workflows passed on {both} issues. Of the discordant pairs, {e['wins']} favored the "
        f"Luna workflow and {e['losses']} favored Astra. Neither passed in {neither}. "
        f"The Luna-workflow minus Astra-only pass-rate difference was {100*e['difference']:+.1f} percentage "
        f"points (paired 95\\% interval [{100*lo:.1f}, {100*hi:.1f}], "
        f"exact two-sided McNemar $p={e['exact_mcnemar_p']:.3g}$)."
    )


def decision_interpretation(report: dict) -> str:
    study = report["deployment"]
    if not study["pairs"]:
        return "A deployment comparison requires paired public coding tasks."
    sentences = []
    for window in study["windows"][:-1]:
        names = [LABELS[arm] for arm in ARMS if window["meets_observed_target"][arm]]
        who = " and ".join(names) if names else "neither workflow"
        sentences.append(f"At {window['deadline_seconds']:g} seconds, {who} met the observed "
                         f"{study['target']:.0%} service target.".replace("%", r"\%"))
    any_time = study["windows"][-1]["crossover"]
    if any_time is not None and 0 <= any_time <= 1:
        sentences.append(f"With the deadline removed, the two point estimates cross at a Luna-token "
                         f"weight of {any_time:.3f}. Lower weights favor Luna with the advisor available. "
                         f"Higher weights favor Astra execution.")
    elif any_time is None:
        sentences.append("The records do not identify a break-even weight for this cohort.")
    else:
        winner = "Luna with optional advice" if any_time > 1 else "Astra only"
        sentences.append(f"Across weights from zero to one, {winner} has the lower unrestricted point estimate.")
    return " ".join(sentences)


def missing_usage_latex(report: dict) -> str:
    study = report["deployment"]
    candidates = [w for w in study["windows"] if w["unknown_balance_at_equality"] is not None]
    if not candidates:
        return ""
    finite = [w for w in candidates if w["deadline_seconds"] is not None]
    window = finite[-1] if finite else candidates[-1]
    count = window["timely_passes"]
    d = window["deadline_seconds"]
    deadline = f"at {d:g} seconds" if d is not None else "with an unrestricted deadline"
    left, right = (study["received"][arm]["unattributed_requests"] for arm in ARMS)
    balance = f"{window['unknown_balance_at_equality']:,.0f}".replace(",", "{,}")
    conclusion = ("Without an upper bound on the missing usage, both rankings remain possible here."
                  if left and right else "The missing capacity must be evaluated against this threshold.")
    return (r"\paragraph{What the missing receipts would have to change.} "
            f"There were {left} unattributed dispatched requests in the Luna workflow and {right} in the Astra "
            f"workflow. At the illustrative weight $w={study['relative_luna_weight']:g}$, let $U_T,U_B$ be the "
            "total weighted capacity missing from the respective receipt sums. "
            f"Using every attributable receipt, {deadline} the Luna workflow uses less weighted capacity per "
            f"timely patch when $U_T-({count[ARMS[0]]}/{count[ARMS[1]]})U_B < {balance}$ "
            f"(threshold rounded to the nearest token). {conclusion}")


def plot(metrics: dict, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    suites = metrics["suites"]
    panel_count = max(1, len(suites))
    figure, axes = plt.subplots(1, panel_count, squeeze=False, figsize=(6, 2.25), layout="constrained",
                                sharey=True)
    if not suites:
        axes[0][0].text(0.5, 0.5, "No paired observations", ha="center", va="center",
                        transform=axes[0][0].transAxes)
    for axis, (suite, summary) in zip(axes[0], suites.items()):
        for arm, color, marker in (("spot_advisor", "#105f84", "o"), ("astra_only", "#a24625", "s")):
            row = summary[arm]
            value = row["astra_tokens_per_accepted"]
            if value is not None and row["n"]:
                axis.scatter(value, row["accepted"] / row["n"], color=color, marker=marker, s=40,
                             label=LABELS[arm], zorder=3)
        axis.set_title(f"{SUITE_LABELS[suite]}\n{summary[ARMS[0]]['n']} task pairs", fontsize=9)
        axis.set_xscale("symlog", linthresh=1)
        axis.set_xlim(left=-0.15)
        axis.grid(alpha=0.2)
    axes[0][0].set_ylim(-0.06, 1.07)
    axes[0][0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0][0].set_ylabel("Acceptance")
    handles = [plt.Line2D([], [], linestyle="", color=color, marker=marker, label=LABELS[arm])
               for arm, color, marker in (("spot_advisor", "#105f84", "o"), ("astra_only", "#a24625", "s"))]
    figure.legend(handles=handles, loc="outside upper center", ncols=2, frameon=False, fontsize=8)
    figure.supxlabel("Astra tokens per accepted task", fontsize=9)
    figure.savefig(output, metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)


def write_report(run: Path, output: Path, independent_seconds=0., deadlines=(300, 900),
                 target=0.8, weight=0.10) -> dict:
    manifest, rows, pairs = load_pairs(run)
    suites = {}
    for suite in EXPECTED_FORMAL:
        group = [(a, b) for a, b in pairs if a["suite"] == suite]
        if group:
            suites[suite] = {arm: summarize([pair[index] for pair in group]) for index, arm in enumerate(ARMS)}
    primary_pairs = [pair for pair in pairs if pair[0]["suite"] == "swe-bench-pro-v2"]
    all_usage = bool(rows) and all(fully_observed(row) for row in rows)
    all_pairs = len(manifest["tasks"]) == len(pairs) and len(rows) == 2 * len(pairs)
    pinned = read_json(HERE / "swe_tasks.json")
    # A completed accounting of attempted and excluded pairs can support a descriptive paper
    # even when the originally registered, fully attributable comparison is unavailable.
    public_ids = {t["id"] for t in pinned["formal"]}
    registered = {e["task_id"] for e in read_json(HERE / "formal-exclusions.json")}
    exclusions = {e["task_id"] for e in manifest.get("exclusions", [])}
    recorded_ids = {r["task_id"] for r in rows}
    if not exclusions.issubset(registered) or exclusions & recorded_ids:
        raise ValueError("Pre-dispatch exclusions conflict with the registered IDs or observed arms.")
    planned = {t["task_id"] for t in manifest["tasks"]}
    suite_counts = {s: sum(t["suite"] == s for t in manifest["tasks"]) for s in EXPECTED_FORMAL}
    disposition_complete = (
        manifest["stage"] == "formal" and suite_counts == EXPECTED_FORMAL
        and manifest["swe_revision"] == pinned["revision"] and manifest["seed"] == pinned["seed"]
        and manifest["settings"] == {ARMS[0]: ["gpt-6-luna", "max"], ARMS[1]: [ASTRA, "medium"]}
        and {t["task_id"] for t in manifest["tasks"] if t["suite"] == "swe-bench-pro-v2"} == public_ids
        and ({a["task_id"] for a, _ in pairs} | exclusions) == planned
        and len(rows) == 2 * len(pairs))
    formal = disposition_complete and all_pairs and all_usage
    primary = effects(primary_pairs, manifest["seed"]) if formal else None
    if primary is not None:
        interval = primary["astra_ratio_ci95"]
        primary["supports_joint_claim"] = bool(
            interval and interval[1] < 1 and primary["difference_ci95"][0] > -0.10
        )
    report = {"stage": manifest["stage"], "source_sha256": manifest["source_sha256"],
              "requested_pairs": len(manifest["tasks"]), "completed_pairs": len(pairs),
              "formal_complete": formal, "suites": suites, "primary_effect": primary,
              "completed_arms": len(rows), "all_usage_observed": all_usage,
              "deployment": deployment_analysis(primary_pairs, manifest["seed"], deadlines, target, weight),
              "grader_source_sha256": manifest.get("grader_source_sha256", manifest["source_sha256"])}
    if exclusions or disposition_complete:
        report.update(disposition_complete=disposition_complete, excluded_before_dispatch=sorted(exclusions))
    evidence = "".join(json.dumps(clean(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    report["evidence_sha256"] = hashlib.sha256(evidence.encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    if manifest["stage"] == "pilot":
        label = "exploratory pilot"
    elif formal:
        label = "completed formal study"
    elif disposition_complete and exclusions:
        label = "completed collection with reported exclusions"
    elif all_pairs:
        label = "formal study with incomplete evidence"
    else:
        label = "interim formal snapshot"
    headline, detail = coding_findings(report, primary_pairs)
    artifacts = [("metrics.json", json.dumps(report, indent=2, sort_keys=True) + "\n"),
                 ("evidence.jsonl", evidence), ("results.tex", latex(report)),
                 ("study.tex", (r"\def\StudyStage{" + label + "}\n"
                                r"\def\StudyPairs{" + str(len(pairs)) + "}\n"
                                r"\def\StudyPlanned{" + str(len(manifest["tasks"])) + "}\n"
                                r"\def\EvidenceID{" + report["evidence_sha256"][:12] + "}\n")),
                 ("coding-headline.tex", headline + "\n"), ("coding-detail.tex", detail + "\n"),
                 ("paired.tex", paired_interpretation(report, primary_pairs) + "\n"),
                 ("deployment.tex", deployment_latex(report)),
                 ("interpretation.tex", decision_interpretation(report) + "\n"),
                 ("missing-usage.tex", missing_usage_latex(report) + "\n"),
                 ("async-replay.json", json.dumps(replay(pairs, independent_seconds), indent=2) + "\n")]
    for name, content in artifacts:
        (output / name).write_text(content, encoding="utf-8", newline="\n")
    if output.resolve() != run.resolve():
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                              encoding="utf-8", newline="\n")
    plot(report, output / "outcomes.pdf")
    deployment_plot(report, output / "deployment.pdf")
    print(f"{report['completed_pairs']}/{report['requested_pairs']} paired tasks. Formal complete: {formal}.")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--independent-seconds", type=float, default=0.)
    parser.add_argument("--deadline-seconds", type=float, action="append", help="Verified-return deadline, repeatable.")
    parser.add_argument("--service-target", type=float, default=0.8, help="Required fraction of verified timely patches.")
    parser.add_argument("--luna-weight", type=float, default=0.1, help="Resource weight per Luna token in Astra units.")
    args = parser.parse_args()
    deadlines = sorted(set(args.deadline_seconds or (300, 900)))
    if not math.isfinite(args.independent_seconds) or args.independent_seconds < 0:
        parser.error("--independent-seconds must be finite and nonnegative.")
    if (not 0 < args.service_target <= 1 or not math.isfinite(args.luna_weight) or args.luna_weight < 0
            or any(not math.isfinite(d) or d <= 0 for d in deadlines)):
        parser.error("Specify a service fraction in (0,1], a finite nonnegative weight, and positive finite deadlines.")
    write_report(args.run, args.output, args.independent_seconds, deadlines, args.service_target, args.luna_weight)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
