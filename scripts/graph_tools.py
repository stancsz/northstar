#!/usr/bin/env python3
"""
Layer 1 / UNDERSTAND — validate and enrich the requirement graph that Claude
authored. Checks structural integrity (unique IDs, resolvable dependencies),
runs cheap ambiguity heuristics, and verifies the graph is a DAG.

This does NOT replace Claude's semantic analysis — Claude already wrote the
ambiguities/predicted_gaps using judgment. This catches mechanical mistakes and
adds heuristic flags Claude may have missed.

Usage:
    python graph_tools.py <run-dir>/01_requirements.json
"""
import argparse, re, sys
from _common import load, save, info, die

VAGUE = ["fast", "slow", "quickly", "easy", "intuitive", "robust", "scalable",
         "secure", "user-friendly", "appropriate", "reasonable", "etc", "and/or",
         "as needed", "if necessary", "high quality", "good"]

def cycle_check(reqs):
    graph = {r["id"]: r.get("depends_on", []) for r in reqs}
    state = {}  # 0=unvisited,1=in-stack,2=done
    cyc = []
    def dfs(n, stack):
        if state.get(n) == 1:
            cyc.append(stack[stack.index(n):] + [n]); return
        if state.get(n) == 2 or n not in graph:
            return
        state[n] = 1
        for m in graph[n]:
            dfs(m, stack + [n])
        state[n] = 2
    for n in graph:
        dfs(n, [])
    return cyc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    a = ap.parse_args()
    g = load(a.graph)
    reqs = g.get("requirements", [])
    if not reqs:
        die("Graph has no requirements.")

    ids = [r["id"] for r in reqs]
    errors = []
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"Duplicate requirement IDs: {sorted(dup)}")
    idset = set(ids)
    for r in reqs:
        for d in r.get("depends_on", []):
            if d not in idset:
                errors.append(f"{r['id']} depends_on unknown {d}")
    cyc = cycle_check(reqs)
    if cyc:
        errors.append(f"Dependency cycle: {' -> '.join(cyc[0])}")
    if errors:
        die("Graph invalid:\n  - " + "\n  - ".join(errors))

    # heuristic ambiguity flags Claude may not have caught
    existing = {a["requirement_id"] for a in g.get("ambiguities", [])}
    added = 0
    for r in reqs:
        low = r["text"].lower()
        hits = [w for w in VAGUE if re.search(rf"\b{re.escape(w)}\b", low)]
        if hits and r["id"] not in existing:
            g.setdefault("ambiguities", []).append(
                {"requirement_id": r["id"],
                 "issue": f"Vague term(s): {', '.join(hits)} — needs measurable criteria",
                 "kind": "ambiguity"})
            added += 1
        if not r.get("acceptance_criteria"):
            g.setdefault("ambiguities", []).append(
                {"requirement_id": r["id"],
                 "issue": "No acceptance criteria — untestable as written",
                 "kind": "missing_criteria"})
            added += 1

    save(g, a.graph)
    info(f"Graph valid. {len(reqs)} requirements, "
         f"{sum(1 for r in reqs if r.get('is_ai_feature'))} AI features.")
    info(f"Ambiguities: {len(g.get('ambiguities', []))} ({added} added by heuristics).")
    info(f"Predicted gaps: {len(g.get('predicted_gaps', []))}.")

if __name__ == "__main__":
    main()
