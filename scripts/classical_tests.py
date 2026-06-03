#!/usr/bin/env python3
"""
Layer 2 / GENERATE (classical backbone) — mechanically expand a test model into
classical test cases so AI/rubric tests have a real foundation and coverage is
meaningful, not just plausible.

Techniques implemented: Equivalence Partitioning, Boundary Value Analysis,
Decision Tables, State Transition. See references/classical_techniques.md.

  model  : emit a _test_model.json skeleton from the requirement graph for you
           to fill in (variables, partitions, boundaries, decision rules).
  expand : read the filled _test_model.json, generate classical cases, and MERGE
           them into 02_testcases.json (tagged technique + source=classical).

Usage:
    python classical_tests.py model  <run-dir>/01_requirements.json --out <run-dir>/_test_model.json
    python classical_tests.py expand <run-dir>/_test_model.json --into <run-dir>/02_testcases.json
"""
import argparse, json, copy
from _common import load, save, info, die

# ---------- model scaffold ----------
def scaffold(graph_path, out):
    g = load(graph_path)
    models = []
    for r in g["requirements"]:
        models.append({
            "requirement_id": r["id"], "title": r["text"][:60],
            "variables": [{"name": "TODO_var", "type": "int", "min": 0, "max": 100,
                           "partitions": [
                               {"label": "valid_low", "valid": True, "range": [0, 50]},
                               {"label": "valid_high", "valid": True, "range": [51, 100]},
                               {"label": "invalid_neg", "valid": False, "range": [-100, -1]}],
                           "boundaries": [50]}],
            "decision_table": {"conditions": ["valid_low"],
                               "rules": [{"when": {"valid_low": True}, "expect": "TODO_outcome"},
                                         {"when": {"valid_low": False}, "expect": "TODO_other"}]},
            "target_template": {"kind": "manual", "arg_from": "TODO_var"},
            "states": None})
    save({"models": models}, out)
    info(f"Scaffolded {len(models)} model stubs -> {out}")
    info("Fill in variables/partitions/boundaries/rules (see references/classical_techniques.md), then `expand`.")

# ---------- helpers ----------
def mid(lo, hi):
    return lo + (hi - lo) // 2

def in_range(v, rng):
    return rng[0] <= v <= rng[1]

def partition_of(var, value):
    for p in var.get("partitions", []):
        if in_range(value, p["range"]):
            return p
    return None

def find_partition(models_vars, label):
    for v in models_vars:
        for p in v.get("partitions", []):
            if p["label"] == label:
                return v, p
    return None, None

def defaults(variables):
    d = {}
    for v in variables:
        valid = [p for p in v.get("partitions", []) if p.get("valid")]
        p = valid[0] if valid else (v.get("partitions") or [{"range": [v.get("min", 0)] * 2}])[0]
        d[v["name"]] = mid(*p["range"])
    return d

def rule_matches(values, variables, when):
    for cond, want in when.items():
        var, part = find_partition(variables, cond)
        if not var:
            return False
        actual = in_range(values.get(var["name"]), part["range"])
        if actual != want:
            return False
    return True

def expected_for(values, model):
    dt = model.get("decision_table") or {}
    for rule in dt.get("rules", []):
        if rule_matches(values, model["variables"], rule["when"]):
            tok = str(rule["expect"]).lower()
            return {"mode": "predicate",
                    "predicate": f"'{tok}' in str(result).lower()"}
    return {"mode": "predicate", "predicate": "result is not None",
            "exact": {"note": "no decision rule matched — refine rejection/validation check"}}

def build_target(template, values, variables):
    t = copy.deepcopy(template)
    kind = t.get("kind", "manual")
    if kind == "manual":
        t["_values"] = values
        return t
    decl_order = [v["name"] for v in variables if v["name"] in values]
    if kind == "python":
        if "args_from" in template:                       # explicit positional order
            t["args"] = [values[n] for n in template["args_from"] if n in values]
        elif "kwargs_from" in template:                   # var -> param name
            t["kwargs"] = {param: values[var] for var, param in template["kwargs_from"].items()
                           if var in values}
        elif "arg_from" in template:                      # single positional (legacy)
            t["args"] = [values[n] for n in decl_order]
    elif kind == "cli":
        for name, val in values.items():
            t["command"] = t.get("command", "").replace("{" + name + "}", str(val))
    elif kind == "http":
        ref = t.setdefault("request", {}).setdefault("body", {})
        def put(path, value):
            keys = path.split("."); cur = ref
            for k in keys[:-1]:
                cur = cur.setdefault(k, {})
            cur[keys[-1]] = value
        if template.get("body_path"):                     # single var -> one path
            put(template["body_path"], next(iter(values.values()), None))
        for var, path in (template.get("body_paths") or {}).items():  # var -> path
            if var in values:
                put(path, values[var])
    for k in ("arg_from", "args_from", "kwargs_from", "body_path", "body_paths"):
        t.pop(k, None)
    return t

# ---------- expansion ----------
def cartesian(levels):
    import itertools
    names = list(levels)
    return [dict(zip(names, combo)) for combo in itertools.product(*levels.values())]

def all_pairs(levels):
    """Greedy all-pairs (pairwise) generator. Covers every pair of values across
    every pair of parameters with far fewer cases than the full cartesian product."""
    names = list(levels)
    if len(names) < 2:
        return [{names[0]: v} for v in levels[names[0]]] if names else []
    # every (param_i=val_i, param_j=val_j) pair that must be covered
    uncovered = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for a in levels[names[i]]:
                for b in levels[names[j]]:
                    uncovered.add((i, a, j, b))
    tests = []
    while uncovered:
        i, a, j, b = next(iter(uncovered))
        test = {names[i]: a, names[j]: b}
        # greedily fill remaining params with the value covering most uncovered pairs
        for k in range(len(names)):
            if names[k] in test:
                continue
            best_val, best_gain = levels[names[k]][0], -1
            for cand in levels[names[k]]:
                gain = 0
                for assigned_idx, val in [(names.index(n), v) for n, v in test.items()]:
                    lo, hi = (assigned_idx, k) if assigned_idx < k else (k, assigned_idx)
                    lo_v, hi_v = (val, cand) if assigned_idx < k else (cand, val)
                    if (lo, lo_v, hi, hi_v) in uncovered:
                        gain += 1
                if gain > best_gain:
                    best_gain, best_val = gain, cand
            test[names[k]] = best_val
        # mark all pairs in this test covered
        idxs = [(names.index(n), v) for n, v in test.items()]
        for x in range(len(idxs)):
            for y in range(x + 1, len(idxs)):
                (i1, v1), (i2, v2) = idxs[x], idxs[y]
                lo, hi = (i1, i2) if i1 < i2 else (i2, i1)
                lo_v, hi_v = (v1, v2) if i1 < i2 else (v2, v1)
                uncovered.discard((lo, lo_v, hi, hi_v))
        tests.append(test)
    return tests

def expand_model(model):
    cases = []
    variables = model["variables"]
    base = defaults(variables)
    rid = model["requirement_id"]

    def add(values, technique, category, label):
        v = dict(base); v.update(values)
        cases.append({
            "requirement_ids": [rid], "category": category, "technique": technique,
            "source": "classical", "title": f"[{technique}] {model['title']} — {label}",
            "preconditions": [], "steps": [f"set {values} then exercise the feature"],
            "target": build_target(model["target_template"], v, variables),
            "expected": expected_for(v, model)})

    # Equivalence Partitioning — one representative per partition per variable
    for var in variables:
        for p in var.get("partitions", []):
            rep = mid(*p["range"])
            add({var["name"]: rep}, "equivalence",
                "positive" if p.get("valid") else "negative",
                f"{var['name']}={rep} ({p['label']})")

    # Boundary Value Analysis — b-1,b,b+1 plus min/max and just-outside
    for var in variables:
        pts = set()
        for b in var.get("boundaries", []):
            pts |= {b - 1, b, b + 1}
        if "min" in var:
            pts |= {var["min"], var["min"] - 1}
        if "max" in var:
            pts |= {var["max"], var["max"] + 1}
        for val in sorted(pts):
            part = partition_of(var, val)
            cat = "boundary" if (part and part.get("valid")) else "negative"
            add({var["name"]: val}, "boundary", cat, f"{var['name']}={val}")

    # Decision Table — one case per rule
    dt = model.get("decision_table") or {}
    for i, rule in enumerate(dt.get("rules", [])):
        values = dict(base)
        for cond, want in rule["when"].items():
            var, part = find_partition(variables, cond)
            if not var:
                continue
            if want:
                values[var["name"]] = mid(*part["range"])
            else:  # pick a value outside that partition
                other = next((p for p in var["partitions"] if p["label"] != cond), None)
                values[var["name"]] = mid(*(other["range"] if other else part["range"]))
        cat = "positive" if all(rule["when"].values()) else "negative"
        add({k: values[k] for k in (v["name"] for v in variables)},
            "decision_table", cat, f"rule {i+1} -> {rule['expect']}")

    # Combinatorial — for multi-variable requirements, cover variable interactions.
    # Default: pairwise (all-pairs) when >=2 variables. Override with
    # model["combinatorial"] in {"pairwise","all","none"}.
    mode = model.get("combinatorial", "pairwise" if len(variables) >= 2 else "none")
    if mode != "none" and len(variables) >= 2:
        levels = {v["name"]: [mid(*p["range"]) for p in v.get("partitions", [])]
                  for v in variables}
        combos = (cartesian(levels) if mode == "all" else all_pairs(levels))
        for combo in combos:
            cat = "positive" if all(
                (partition_of(next(v for v in variables if v["name"] == n), val) or {}).get("valid")
                for n, val in combo.items()) else "negative"
            label = ", ".join(f"{n}={v}" for n, v in combo.items())
            add(dict(combo), mode, cat, label)

    # State Transition
    st = model.get("states") or {}
    for tr in st.get("transitions", []):
        invalid = str(tr.get("to")).upper() == "INVALID"
        cases.append({
            "requirement_ids": [rid], "category": "negative" if invalid else "positive",
            "technique": "state_transition", "source": "classical",
            "title": f"[state_transition] {tr['from']} --{tr['event']}--> {tr['to']}",
            "preconditions": [f"system in state '{tr['from']}'"],
            "steps": [f"fire event '{tr['event']}'"],
            "target": {"kind": "manual", "_transition": tr},
            "expected": {"mode": "predicate",
                         "predicate": ("'reject' in str(result).lower() or 'invalid' in str(result).lower()"
                                       if invalid else f"'{tr['to']}'.lower() in str(result).lower()")}})
    return cases

def expand(model_path, into):
    m = load(model_path)
    if any("TODO" in json.dumps(mod) for mod in m["models"]):
        die("Test model still has TODO placeholders — fill them in before expanding.")
    suite = load(into)
    existing = suite.setdefault("cases", [])
    nums = [int(c["id"].split("-")[1]) for c in existing if c.get("id", "").startswith("TC-")]
    n = max(nums) if nums else 0
    seen = {json.dumps({"r": c.get("requirement_ids"), "tech": c.get("technique"),
                        "t": c.get("target")}, sort_keys=True, default=str) for c in existing}
    added, by_tech = 0, {}
    for mod in m["models"]:
        for c in expand_model(mod):
            key = json.dumps({"r": c["requirement_ids"], "tech": c["technique"],
                              "t": c["target"]}, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key); n += 1
            c = {"id": f"TC-{n:03d}", **c}
            existing.append(c); added += 1
            by_tech[c["technique"]] = by_tech.get(c["technique"], 0) + 1
    save(suite, into)
    info(f"Added {added} classical cases -> {into}")
    info("  by technique: " + ", ".join(f"{k}={v}" for k, v in sorted(by_tech.items())))
    info("Now layer AI rubric cases on top — only for requirements that now have classical coverage.")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("model"); s.add_argument("graph"); s.add_argument("--out", required=True)
    e = sub.add_parser("expand"); e.add_argument("model"); e.add_argument("--into", required=True)
    a = ap.parse_args()
    if a.cmd == "model": scaffold(a.graph, a.out)
    else: expand(a.model, a.into)

if __name__ == "__main__":
    main()
