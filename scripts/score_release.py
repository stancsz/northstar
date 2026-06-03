#!/usr/bin/env python3
"""
Layer 6 / REPORT & COMPLY — consolidate defects and compute the release
readiness score from every prior artifact.

Readiness = 100 * (0.30*coverage + 0.30*defect_health
                    + 0.25*ai_stability + 0.15*compliance)
Any critical defect forces recommendation = 'hold' regardless of score.

Inputs (in run-dir): 01_requirements.json, 02_testcases.json, 03_results.json,
05_evaluations.json (optional), compliance.json (optional checklist results).

Usage:
    python score_release.py <run-dir>
"""
import argparse, os
from _common import load, save, info, SEVERITY_WEIGHT

W = {"coverage": 0.30, "defects": 0.30, "stability": 0.25, "compliance": 0.15}

def opt(path):
    return load(path) if os.path.exists(path) else None

def severity_for(req):
    return {"critical": "critical", "high": "high"}.get(
        (req or {}).get("risk"), "medium")

def consolidate(rd):
    reqs = {r["id"]: r for r in load(f"{rd}/01_requirements.json")["requirements"]}
    tc = {c["id"]: c for c in load(f"{rd}/02_testcases.json")["cases"]}
    res = load(f"{rd}/03_results.json")["results"]
    ev = opt(f"{rd}/05_evaluations.json") or {}
    defects, n = [], 0

    def add(title, sev, rids, cid, kind, repro, evid):
        nonlocal n
        n += 1
        defects.append({"id": f"DEF-{n:03d}", "title": title, "severity": sev,
                        "requirement_ids": rids, "case_id": cid, "kind": kind,
                        "reproduction": repro, "evidence": str(evid)[:500]})

    for r in res:
        if r["status"] in ("fail", "error"):
            c = tc.get(r["case_id"], {})
            rids = c.get("requirement_ids", [])
            sev = severity_for(reqs.get(rids[0]) if rids else None)
            add(f"{c.get('title', r['case_id'])} — {r['status']}", sev, rids,
                r["case_id"], "functional" if r["status"] == "fail" else "performance",
                c.get("steps", []), r.get("assertion_detail", ""))

    for e in ev.get("evaluations", []):
        c = tc.get(e["case_id"], {})
        cons = e.get("consistency", {})
        flags = [f for s in e["samples"] for f in s.get("safety_flags", [])]
        halluc = [h for s in e["samples"] for h in s.get("hallucinations", [])]
        if cons.get("pass_rate", 1) < 1.0:
            kind = "safety" if flags else ("hallucination" if halluc else "consistency")
            sev = "high" if flags else ("high" if cons.get("pass_rate", 1) < 0.5 else "medium")
            add(f"AI output unreliable: {c.get('title', e['case_id'])} "
                f"(pass_rate {cons.get('pass_rate')})", sev, c.get("requirement_ids", []),
                e["case_id"], kind, c.get("steps", []),
                {"safety_flags": flags, "hallucinations": halluc})

    for adv in ev.get("adversarial", []):
        if adv["outcome"] == "breached":
            add(f"Adversarial breach: {adv['owasp']}", "critical", [], adv["case_id"],
                "safety", ["see adversarial.py probe"], adv["evidence"])

    for tr in ev.get("agent_traces", []):
        if not tr.get("goal_completed") or tr.get("unsafe_tool_calls"):
            sev = "critical" if tr.get("unsafe_tool_calls") else "high"
            add(f"Agent failure at step {tr.get('failing_step')}", sev, [], tr["case_id"],
                "safety", ["replay agent trace"],
                {"unsafe": tr.get("unsafe_tool_calls"), "deviations": tr.get("deviations")})

    comp = opt(f"{rd}/compliance.json")
    if comp:
        for chk in comp.get("checks", []):
            if not chk.get("passed"):
                add(f"Compliance: {chk.get('name')}", chk.get("severity", "high"),
                    [], None, "compliance", [chk.get("how_to_verify", "")], chk.get("detail", ""))

    save({"defects": defects}, f"{rd}/defects.json")
    return defects, reqs, res, ev, comp

def score(rd):
    defects, reqs, res, ev, comp = consolidate(rd)

    executed = {r["case_id"] for r in res if r["status"] not in ("skipped",)}
    tc = load(f"{rd}/02_testcases.json")["cases"]
    covered = {rid for c in tc if c["id"] in executed for rid in c.get("requirement_ids", [])}
    coverage = len(covered & set(reqs)) / len(reqs) if reqs else 1.0

    penalty = sum(SEVERITY_WEIGHT[d["severity"]] for d in defects)
    defect_health = max(0.0, 1.0 - penalty / max(len(res), 1))

    evals = ev.get("evaluations", [])
    stability = (sum(e["consistency"]["pass_rate"] for e in evals) / len(evals)) if evals else 1.0

    if comp:
        chs = comp.get("checks", [])
        compliance = (sum(1 for c in chs if c.get("passed")) / len(chs)) if chs else 1.0
        comp_detail = f"{sum(1 for c in chs if c.get('passed'))}/{len(chs)} checks passed"
    else:
        compliance, comp_detail = 1.0, "no compliance checklist supplied"

    total = round(100 * (W["coverage"]*coverage + W["defects"]*defect_health +
                         W["stability"]*stability + W["compliance"]*compliance), 1)
    has_critical = any(d["severity"] == "critical" for d in defects)
    rec = "hold" if (has_critical or total < 70) else ("ship" if total >= 85 else "ship_with_caveats")

    readiness = {"score": total, "recommendation": rec,
        "components": {
            "coverage":   {"weight": W["coverage"], "value": round(coverage, 3),
                           "detail": f"{len(covered & set(reqs))}/{len(reqs)} requirements executed"},
            "defects":    {"weight": W["defects"], "value": round(defect_health, 3),
                           "detail": _sev_breakdown(defects)},
            "stability":  {"weight": W["stability"], "value": round(stability, 3),
                           "detail": f"mean AI pass-rate across {len(evals)} AI cases"},
            "compliance": {"weight": W["compliance"], "value": round(compliance, 3),
                           "detail": comp_detail}},
        "blocking": (["critical defect present — blocks ship"] if has_critical else [])}
    save(readiness, f"{rd}/readiness.json")
    info(f"Defects: {len(defects)} ({_sev_breakdown(defects)})")
    info(f"RELEASE READINESS: {total}/100  ->  {rec.upper()}")

def _sev_breakdown(defects):
    return ", ".join(f"{s}={sum(1 for d in defects if d['severity']==s)}"
                     for s in ("critical", "high", "medium", "low"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); a = ap.parse_args()
    score(a.run_dir)

if __name__ == "__main__":
    main()
