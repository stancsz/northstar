#!/usr/bin/env python3
"""
Layer 2 / GENERATE — two modes.

  scaffold : emit a 02_testcases.json skeleton from the requirement graph so
             Claude isn't authoring from a blank page. One positive + one
             negative + a boundary stub per requirement; a rubric stub per AI
             feature; an adversarial stub per AI feature with a user-facing
             surface. Claude then fills steps/targets/expected with judgment.

  validate : structural check of the finished 02_testcases.json — every case
             maps to a real requirement, rubric refs resolve, coverage report.

Usage:
    python generate_test_cases.py scaffold <run-dir>/01_requirements.json --out <run-dir>/02_testcases.json
    python generate_test_cases.py validate <run-dir>/02_testcases.json --graph <run-dir>/01_requirements.json
"""
import argparse, sys
from _common import load, save, info, die

def scaffold(graph_path, out):
    g = load(graph_path)
    cases, rubrics, n, rn = [], [], 0, 0
    for r in g["requirements"]:
        rid = r["id"]
        ai = r.get("is_ai_feature")
        base = {"requirement_ids": [rid],
                "preconditions": [], "steps": ["TODO: fill steps"],
                "target": {"kind": "manual"}}
        for cat in ("positive", "negative", "boundary"):
            n += 1
            c = dict(base)
            c.update({"id": f"TC-{n:03d}", "category": cat,
                      "title": f"TODO: {cat} case for {rid}"})
            if ai and cat == "positive":
                rn += 1
                rub_id = f"RUB-{rn:03d}"
                rubrics.append({
                    "id": rub_id, "for_requirement": rid,
                    "intent": f"TODO: what a valid response to {rid} must accomplish",
                    "semantic_accuracy": "TODO", "required_claims": [],
                    "prohibited_content": ["PII of other users", "claims outside policy"],
                    "format_constraints": [], "tone": "TODO", "pass_threshold": 0.8})
                c["expected"] = {"mode": "rubric", "rubric_id": rub_id}
            else:
                c["expected"] = {"mode": "exact",
                                 "exact": {"note": "TODO define exact/predicate check"}}
            cases.append(c)
        if ai:  # adversarial probe stub for user-facing AI
            n += 1
            cases.append({"id": f"TC-{n:03d}", "requirement_ids": [rid],
                          "category": "adversarial", "title": f"Prompt-injection probe for {rid}",
                          "preconditions": [], "steps": ["see adversarial.py for the probe pack"],
                          "target": {"kind": "manual"},
                          "expected": {"mode": "rubric", "rubric_id": "ADVERSARIAL"}})
    out_obj = {"run_for": graph_path, "cases": cases, "rubrics": rubrics}
    save(out_obj, out)
    info(f"Scaffolded {len(cases)} cases and {len(rubrics)} rubric stubs -> {out}")
    info("Now fill in every TODO using judgment, then run `validate`.")

def validate(tc_path, graph_path):
    tc = load(tc_path)
    cases = tc.get("cases", [])
    if not cases:
        die("No test cases.")
    rubric_ids = {r["id"] for r in tc.get("rubrics", [])} | {"ADVERSARIAL"}
    req_ids = set()
    if graph_path:
        req_ids = {r["id"] for r in load(graph_path)["requirements"]}

    errs, covered = [], set()
    seen = set()
    for c in cases:
        if c["id"] in seen:
            errs.append(f"Duplicate case id {c['id']}")
        seen.add(c["id"])
        for rid in c.get("requirement_ids", []):
            covered.add(rid)
            if req_ids and rid not in req_ids:
                errs.append(f"{c['id']} maps to unknown requirement {rid}")
        exp = c.get("expected", {})
        if exp.get("mode") == "rubric" and exp.get("rubric_id") not in rubric_ids:
            errs.append(f"{c['id']} references unknown rubric {exp.get('rubric_id')}")
        if "TODO" in str(c):
            errs.append(f"{c['id']} still contains a TODO placeholder")
    if errs:
        die("Test suite invalid:\n  - " + "\n  - ".join(errs))

    info(f"Valid. {len(cases)} cases across categories: " +
         ", ".join(f"{cat}={sum(1 for c in cases if c['category']==cat)}"
                   for cat in ("positive", "negative", "boundary", "error_recovery", "adversarial")))
    if req_ids:
        miss = sorted(req_ids - covered)
        cov = 100 * len(covered & req_ids) / len(req_ids)
        info(f"Requirement coverage: {cov:.0f}%  ({len(covered & req_ids)}/{len(req_ids)})")
        if miss:
            info(f"UNCOVERED requirements: {miss}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scaffold"); s.add_argument("graph"); s.add_argument("--out", required=True)
    v = sub.add_parser("validate"); v.add_argument("testcases"); v.add_argument("--graph", default=None)
    a = ap.parse_args()
    if a.cmd == "scaffold":
        scaffold(a.graph, a.out)
    else:
        validate(a.testcases, a.graph)

if __name__ == "__main__":
    main()
